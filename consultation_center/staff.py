from urllib.parse import urlencode

import frappe
import frappe.sessions
from frappe.utils import date_diff, format_date, format_datetime, getdate, nowdate

from consultation_center.portal import REQUEST_STATUS

ADMIN_ACCESS = {"System Manager", "Center Director"}
OPERATIONS_ACCESS = ADMIN_ACCESS | {"Case Coordinator", "Intake Coordinator", "Operations Officer"}
SUPERVISOR_ACCESS = ADMIN_ACCESS | {"Consultation Supervisor"}
CONSULTANT_ACCESS = ADMIN_ACCESS | {"Consultant"}

ROLE_LABELS = {
	"System Manager": "مسؤول النظام",
	"Center Director": "مدير المركز",
	"Consultation Supervisor": "مشرف مهني",
	"Case Coordinator": "منسق حالات",
	"Intake Coordinator": "منسق استقبال وفرز",
	"Operations Officer": "موظف تشغيل",
	"Consultant": "مستشار",
}


def require_staff_access(allowed_roles: set[str]) -> tuple[str, set[str]]:
	user = frappe.session.user
	if user == "Guest":
		redirect_to = frappe.request.path if frappe.request else "/operations"
		frappe.redirect(f"/login?{urlencode({'redirect-to': redirect_to})}")

	roles = set(frappe.get_roles(user))
	if user != "Administrator" and not roles & allowed_roles:
		frappe.throw("ليس لديك صلاحية للوصول إلى هذه الواجهة", frappe.PermissionError)
	return user, roles


def build_staff_context(
	context,
	active_nav: str,
	title: str,
	staff_section: str,
	allowed_roles: set[str],
):
	user, roles = require_staff_access(allowed_roles)
	frappe.sessions.get_csrf_token()
	frappe.db.commit()
	display_name = frappe.db.get_value("User", user, "full_name") or user
	role_label = next(
		(ROLE_LABELS[role] for role in ROLE_LABELS if role in roles),
		"فريق رُشد",
	)
	if user == "Administrator":
		role_label = "مسؤول النظام"

	context.update(
		{
			"title": title,
			"no_cache": 1,
			"body_class": "rushd-staff-page",
			"active_nav": active_nav,
			"staff_section": staff_section,
			"staff_user": user,
			"display_name": display_name,
			"role_label": role_label,
		}
	)


def get_request_counts() -> dict[str, int]:
	statuses = (
		"Submitted",
		"Under Completeness Review",
		"Awaiting Beneficiary Information",
		"Ready for Triage",
		"Eligible",
		"Not Eligible",
	)
	return {
		status: frappe.db.count("Consultation Request", {"workflow_state": status})
		for status in statuses
	}


def get_staff_requests(states: tuple[str, ...] | list[str], limit: int | None = None):
	rows = frappe.db.get_all(
		"Consultation Request",
		filters={"workflow_state": ["in", states]},
		fields=[
			"name",
			"beneficiary",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"assigned_coordinator",
			"urgency",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)
	for row in rows:
		_decorate_request(row)
	return rows


def get_staff_request_detail(request_name: str | None):
	if not request_name:
		return None
	row = frappe.db.get_value(
		"Consultation Request",
		request_name,
		[
			"name",
			"beneficiary",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"source",
			"urgency",
			"summary",
			"preferred_mode",
			"preferred_times",
			"eligibility_status",
			"screening_status",
			"assigned_coordinator",
			"operations_note",
			"beneficiary_action_note",
			"triage_note",
			"decision_by",
			"decision_on",
			"rejection_reason",
		],
		as_dict=True,
	)
	if not row:
		return None

	_decorate_request(row)
	beneficiary = frappe.db.get_value(
		"Beneficiary",
		row.beneficiary,
		[
			"beneficiary_name",
			"date_of_birth",
			"city",
			"mobile",
			"email",
			"guardian_required",
			"consent_status",
		],
		as_dict=True,
	)
	if beneficiary:
		beneficiary.age = (
			int(date_diff(nowdate(), beneficiary.date_of_birth) / 365.25)
			if beneficiary.date_of_birth
			else None
		)
		beneficiary.date_of_birth_label = (
			format_date(getdate(beneficiary.date_of_birth)) if beneficiary.date_of_birth else "غير مسجل"
		)
	row.beneficiary_profile = beneficiary
	return row


def get_assignment_requests():
	rows = frappe.db.get_all(
		"Consultation Request",
		filters={
			"workflow_state": ["in", ["Eligible", "Ready for Assignment"]],
			"linked_case": ["is", "not set"],
		},
		fields=[
			"name",
			"beneficiary",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"urgency",
			"modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_request(row)
		beneficiary = frappe.db.get_value(
			"Beneficiary",
			row.beneficiary,
			["guardian_required", "consent_status"],
			as_dict=True,
		)
		row.assignment_blocked = bool(
			beneficiary
			and beneficiary.guardian_required
			and beneficiary.consent_status != "Granted"
		)
		row.assignment_block_reason = (
			"يلزم اعتماد موافقة ولي الأمر قبل الإسناد"
			if row.assignment_blocked
			else ""
		)
	return rows


def get_active_consultants(service: str | None = None):
	rows = frappe.db.get_all(
		"Consultant",
		filters={"active": 1},
		fields=[
			"name",
			"consultant_name",
			"branch",
			"specializations",
			"services",
			"maximum_daily_sessions",
		],
		order_by="consultant_name asc",
	)
	for row in rows:
		row.active_cases = frappe.db.count(
			"Consultation Case",
			{
				"primary_consultant": row.name,
				"case_status": [
					"in",
					[
						"Assigned",
						"Awaiting Appointment",
						"Active",
						"On Hold",
						"Awaiting Report",
						"Under Supervisor Review",
						"Follow-up",
					],
				],
			},
		)
		row.compatible = consultant_supports_service(row.services, service)
	return rows


def consultant_supports_service(services: str | None, service: str | None) -> bool:
	if not service or not services:
		return True
	configured_services = {
		item.strip()
		for item in services.replace("\n", ",").split(",")
		if item.strip()
	}
	return not configured_services or service in configured_services


def get_session_reviews(states: tuple[str, ...] = ("Pending Review",)):
	rows = frappe.db.get_all(
		"Consultation Session",
		filters={"status": ["in", list(states)]},
		fields=[
			"name",
			"appointment",
			"case",
			"beneficiary",
			"consultant",
			"service",
			"status",
			"actual_start",
			"duration_minutes",
			"topic",
			"submitted_on",
			"modified",
		],
		order_by="submitted_on asc, modified asc",
	)
	for row in rows:
		_decorate_session_review(row)
	return rows


def get_session_review_detail(session_name: str | None):
	if not session_name:
		return None
	row = frappe.db.get_value(
		"Consultation Session",
		session_name,
		[
			"name",
			"appointment",
			"case",
			"beneficiary",
			"consultant",
			"service",
			"status",
			"actual_start",
			"actual_end",
			"duration_minutes",
			"attendance_status",
			"topic",
			"goals_addressed",
			"interventions",
			"professional_notes",
			"follow_up",
			"beneficiary_summary",
			"guardian_summary_allowed",
			"guardian_summary",
			"next_action",
			"next_action_due",
			"documented_by",
			"documented_on",
			"submitted_on",
			"review_note",
		],
		as_dict=True,
	)
	if not row:
		return None
	_decorate_session_review(row)
	row.beneficiary_profile = frappe.db.get_value(
		"Beneficiary",
		row.beneficiary,
		["beneficiary_name", "city", "date_of_birth"],
		as_dict=True,
	)
	return row


def _decorate_session_review(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
		or row.beneficiary
	)
	row.consultant_name = (
		frappe.db.get_value("Consultant", row.consultant, "consultant_name")
		or row.consultant
	)
	row.service_name = (
		frappe.db.get_value("Consultation Service", row.service, "service_name")
		or row.service
	)
	row.actual_start_label = (
		format_datetime(row.actual_start) if row.actual_start else "غير محدد"
	)
	row.submitted_on_label = (
		format_datetime(row.submitted_on) if row.submitted_on else "غير محدد"
	)


def get_plan_reviews():
	rows = frappe.db.get_all(
		"Consultation Plan",
		filters={"status": "Pending Review"},
		fields=[
			"name",
			"case",
			"beneficiary",
			"consultant",
			"plan_title",
			"submitted_on",
			"modified",
		],
		order_by="submitted_on asc, modified asc",
	)
	for row in rows:
		_decorate_plan_review(row)
	return rows


def get_plan_review_detail(plan_name: str | None):
	if not plan_name:
		return None
	doc = frappe.get_doc("Consultation Plan", plan_name)
	if doc.status != "Pending Review":
		return None
	_decorate_plan_review(doc)
	return doc


def get_assessment_oversight():
	rows = frappe.db.get_all(
		"Assessment Submission",
		filters={"status": ["in", ["Submitted", "Reviewed"]]},
		fields=[
			"name",
			"case",
			"beneficiary",
			"consultant",
			"assessment_template",
			"assessment_type",
			"status",
			"percentage_score",
			"submitted_on",
			"reviewed_on",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_assessment_oversight(row)
	return rows


def get_assessment_oversight_detail(submission_name: str | None):
	if not submission_name:
		return None
	doc = frappe.get_doc("Assessment Submission", submission_name)
	_decorate_assessment_oversight(doc)
	return doc


def _decorate_assessment_oversight(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
		or row.beneficiary
	)
	row.consultant_name = (
		frappe.db.get_value("Consultant", row.consultant, "consultant_name")
		or row.consultant
	)
	row.template_title = (
		frappe.db.get_value(
			"Assessment Template",
			row.assessment_template,
			"template_title",
		)
		or row.assessment_template
	)
	row.status_label = {
		"Submitted": "بانتظار مراجعة المستشار",
		"Reviewed": "تمت المراجعة",
	}.get(row.status, row.status)
	row.type_label = {
		"Baseline": "قبلي",
		"Follow-up": "متابعة",
		"Closing": "بعدي",
	}.get(row.assessment_type, row.assessment_type)


def get_referral_review_queue(user: str):
	filters = {"status": ["in", ["Pending Approval", "Approved", "Returned", "Sent", "In Progress"]]}
	if user != "Administrator" and not set(frappe.get_roles(user)) & ADMIN_ACCESS:
		case_names = frappe.db.get_all(
			"Consultation Case",
			filters={"supervisor": user},
			pluck="name",
		)
		filters["case"] = ["in", case_names or [""]]
	rows = frappe.db.get_all(
		"Case Referral",
		filters=filters,
		fields=[
			"name", "case", "beneficiary", "consultant", "status", "priority",
			"referral_type", "target_organization", "modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_professional_queue(row, {
			"Pending Approval": "بانتظار الاعتماد", "Approved": "معتمدة",
			"Returned": "معادة", "Sent": "أُرسلت", "In Progress": "قيد المتابعة",
		})
	return rows


def get_supervision_request_queue(user: str):
	filters = {"status": ["in", ["Submitted", "In Review", "Answered"]]}
	if user != "Administrator" and not set(frappe.get_roles(user)) & ADMIN_ACCESS:
		filters["supervisor"] = user
	rows = frappe.db.get_all(
		"Supervision Request",
		filters=filters,
		fields=[
			"name", "case", "consultant", "supervisor", "status", "priority",
			"request_type", "supervision_question", "supervisor_response",
			"required_action", "follow_up_date", "requested_on", "modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_professional_queue(row, {
			"Submitted": "جديد", "In Review": "قيد المراجعة", "Answered": "تم الرد",
		})
	return rows


def get_escalation_queue(user: str):
	filters = {"status": ["in", ["Open", "Acknowledged", "Action In Progress", "Resolved"]]}
	if user != "Administrator" and not set(frappe.get_roles(user)) & ADMIN_ACCESS:
		filters["assigned_supervisor"] = user
	rows = frappe.db.get_all(
		"Professional Escalation",
		filters=filters,
		fields=[
			"name", "case", "beneficiary", "consultant", "assigned_supervisor",
			"status", "severity", "alert_type", "alert_summary", "immediate_action",
			"supervisor_action", "resolution_note", "follow_up_date", "reported_on",
			"modified",
		],
		order_by="modified desc",
	)
	rows.sort(
		key=lambda row: {
			"Critical": 0,
			"High": 1,
			"Moderate": 2,
		}.get(row.severity, 3)
	)
	for row in rows:
		_decorate_professional_queue(row, {
			"Open": "مفتوح", "Acknowledged": "تم الاطلاع",
			"Action In Progress": "الإجراء جارٍ", "Resolved": "تم الحل",
		})
	return rows


def _decorate_professional_queue(row, statuses):
	row.status_label = statuses.get(row.status, row.status)
	row.priority_label = {
		"Low": "منخفضة", "Normal": "عادية", "High": "عالية", "Urgent": "عاجلة",
	}.get(row.get("priority"), row.get("priority", ""))
	row.referral_type_label = {
		"Internal": "داخلية", "External": "خارجية",
	}.get(row.get("referral_type"), row.get("referral_type", ""))
	row.request_type_label = {
		"Case Guidance": "توجيه للحالة",
		"Documentation Review": "مراجعة توثيق",
		"Ethical Consultation": "استشارة مهنية وأخلاقية",
		"Referral Guidance": "توجيه إحالة",
		"Other": "أخرى",
	}.get(row.get("request_type"), row.get("request_type", ""))
	row.alert_type_label = {
		"Safeguarding": "حماية",
		"Urgent Deterioration": "تدهور عاجل",
		"Conflict of Interest": "تضارب مصالح",
		"Service Risk": "مخاطر تقديم الخدمة",
		"Other": "أخرى",
	}.get(row.get("alert_type"), row.get("alert_type", ""))
	row.severity_label = {
		"Moderate": "متوسطة", "High": "عالية", "Critical": "حرجة",
	}.get(row.get("severity"), row.get("severity", ""))
	row.consultant_name = (
		frappe.db.get_value("Consultant", row.consultant, "consultant_name")
		or row.consultant
	)
	if row.get("beneficiary"):
		row.beneficiary_name = (
			frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
			or row.beneficiary
		)
	row.date_label = (
		format_datetime(row.get("requested_on") or row.get("reported_on"))
		if row.get("requested_on") or row.get("reported_on")
		else ""
	)


def get_supervised_cases(user: str):
	filters = {
		"case_status": [
			"in",
			[
				"Assigned",
				"Awaiting Appointment",
				"Active",
				"On Hold",
				"Awaiting Report",
				"Under Supervisor Review",
				"Follow-up",
				"Ready to Close",
			],
		],
	}
	if user != "Administrator" and not set(frappe.get_roles(user)) & ADMIN_ACCESS:
		filters["supervisor"] = user
	rows = frappe.db.get_all(
		"Consultation Case",
		filters=filters,
		fields=[
			"name",
			"beneficiary",
			"service",
			"primary_consultant",
			"case_status",
			"priority",
			"opened_on",
			"completed_sessions",
			"planned_sessions",
			"next_action",
			"next_action_due",
			"modified",
		],
		order_by="priority desc, modified desc",
	)
	for row in rows:
		_decorate_supervised_case(row)
	return rows


def get_supervised_case_detail(case_name: str | None, supervised_cases):
	if not case_name or case_name not in {row.name for row in supervised_cases}:
		return None
	case = frappe.get_doc("Consultation Case", case_name)
	_decorate_supervised_case(case)
	case.sessions = frappe.db.get_all(
		"Consultation Session",
		filters={"case": case.name},
		fields=[
			"name",
			"status",
			"actual_start",
			"topic",
			"submitted_on",
			"review_note",
		],
		order_by="actual_start desc",
		limit=8,
	)
	for row in case.sessions:
		row.status_label = {
			"Draft": "مسودة",
			"Pending Review": "بانتظار المراجعة",
			"Approved": "معتمدة",
			"Returned": "معادة للتعديل",
			"Cancelled": "ملغاة",
		}.get(row.status, row.status)
		row.date_label = format_datetime(row.actual_start) if row.actual_start else "غير محدد"
	case.plans = frappe.db.get_all(
		"Consultation Plan",
		filters={"case": case.name},
		fields=["name", "plan_title", "status", "review_date", "review_note"],
		order_by="modified desc",
		limit=5,
	)
	case.assessments = frappe.db.get_all(
		"Assessment Submission",
		filters={"case": case.name},
		fields=[
			"name",
			"assessment_type",
			"status",
			"percentage_score",
			"submitted_on",
		],
		order_by="modified desc",
		limit=8,
	)
	case.referrals = frappe.db.get_all(
		"Case Referral",
		filters={"case": case.name},
		fields=["name", "referral_type", "status", "priority", "target_organization"],
		order_by="modified desc",
		limit=8,
	)
	case.supervision_requests = frappe.db.get_all(
		"Supervision Request",
		filters={"case": case.name},
		fields=["name", "request_type", "status", "priority", "supervision_question"],
		order_by="modified desc",
		limit=8,
	)
	case.escalations = frappe.db.get_all(
		"Professional Escalation",
		filters={"case": case.name},
		fields=["name", "alert_type", "status", "severity", "alert_summary"],
		order_by="modified desc",
		limit=8,
	)
	return case


def get_supervisor_consultant_performance(user: str):
	cases = get_supervised_cases(user)
	consultant_names = sorted({row.primary_consultant for row in cases if row.primary_consultant})
	rows = []
	for consultant_name in consultant_names:
		consultant = frappe.db.get_value(
			"Consultant",
			consultant_name,
			[
				"name",
				"consultant_name",
				"branch",
				"maximum_daily_sessions",
				"specializations",
			],
			as_dict=True,
		)
		if not consultant:
			continue
		consultant.active_cases = sum(
			1 for row in cases if row.primary_consultant == consultant.name
		)
		consultant.sessions = frappe.db.count(
			"Consultation Session",
			{"consultant": consultant.name},
		)
		consultant.approved_sessions = frappe.db.count(
			"Consultation Session",
			{"consultant": consultant.name, "status": "Approved"},
		)
		consultant.pending_documentation = frappe.db.count(
			"Consultation Session",
			{"consultant": consultant.name, "status": ["in", ["Draft", "Returned"]]},
		)
		consultant.attended_appointments = frappe.db.count(
			"Consultation Appointment",
			{"consultant": consultant.name, "attendance_status": ["in", ["Attended", "Late"]]},
		)
		consultant.no_show_appointments = frappe.db.count(
			"Consultation Appointment",
			{"consultant": consultant.name, "attendance_status": "No Show"},
		)
		consultant.documentation_rate = (
			round(consultant.approved_sessions / consultant.sessions * 100)
			if consultant.sessions
			else 0
		)
		rows.append(consultant)
	return rows


def get_supervisor_report(user: str):
	cases = get_supervised_cases(user)
	case_names = [row.name for row in cases]
	consultants = get_supervisor_consultant_performance(user)
	return {
		"active_cases": len(cases),
		"priority_cases": sum(1 for row in cases if row.priority in {"High", "Urgent"}),
		"stalled_cases": sum(
			1 for row in cases if row.case_status in {"On Hold", "Awaiting Report"}
		),
		"sessions": frappe.db.count(
			"Consultation Session",
			{"case": ["in", case_names or [""]]},
		),
		"pending_reviews": frappe.db.count(
			"Consultation Session",
			{"case": ["in", case_names or [""]], "status": "Pending Review"},
		),
		"open_referrals": frappe.db.count(
			"Case Referral",
			{
				"case": ["in", case_names or [""]],
				"status": ["not in", ["Closed", "Cancelled"]],
			},
		),
		"open_escalations": frappe.db.count(
			"Professional Escalation",
			{
				"case": ["in", case_names or [""]],
				"status": ["not in", ["Resolved", "Closed", "Cancelled"]],
			},
		),
		"consultants": len(consultants),
		"average_documentation_rate": (
			round(sum(row.documentation_rate for row in consultants) / len(consultants))
			if consultants
			else 0
		),
	}


def _decorate_supervised_case(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
		or row.beneficiary
	)
	row.service_name = (
		frappe.db.get_value("Consultation Service", row.service, "service_name")
		or row.service
	)
	row.consultant_name = (
		frappe.db.get_value("Consultant", row.primary_consultant, "consultant_name")
		if row.primary_consultant
		else "غير مسندة"
	)
	row.status_label = {
		"Assigned": "مسندة",
		"Awaiting Appointment": "بانتظار الموعد",
		"Active": "نشطة",
		"On Hold": "معلقة",
		"Awaiting Report": "بانتظار التقرير",
		"Under Supervisor Review": "تحت مراجعة المشرف",
		"Follow-up": "متابعة",
		"Ready to Close": "جاهزة للإغلاق",
	}.get(row.case_status, row.case_status)
	row.priority_label = {
		"Low": "منخفضة",
		"Normal": "عادية",
		"High": "عالية",
		"Urgent": "عاجلة",
	}.get(row.priority, row.priority)
	row.progress_percent = (
		min(100, round((row.completed_sessions or 0) / row.planned_sessions * 100))
		if row.planned_sessions
		else 0
	)
	row.last_session = frappe.db.get_value(
		"Consultation Session",
		{"case": row.name},
		"actual_start",
		order_by="actual_start desc",
	)
	row.last_session_label = (
		format_datetime(row.last_session) if row.last_session else "لا توجد جلسة"
	)
	row.missing_items = (
		frappe.db.count(
			"Consultation Session",
			{"case": row.name, "status": ["in", ["Draft", "Returned"]]},
		)
		+ frappe.db.count(
			"Supervision Request",
			{"case": row.name, "status": ["in", ["Submitted", "In Review"]]},
		)
		+ frappe.db.count(
			"Professional Escalation",
			{
				"case": row.name,
				"status": ["in", ["Open", "Acknowledged", "Action In Progress"]],
			},
		)
	)


def get_operations_appointments():
	rows = frappe.db.get_all(
		"Consultation Appointment",
		fields=[
			"name",
			"beneficiary",
			"consultant",
			"service",
			"status",
			"start_datetime",
			"end_datetime",
			"delivery_mode",
			"location",
			"attendance_status",
			"confirmation_status",
			"cancellation_reason",
			"created_session",
		],
		order_by="start_datetime desc",
		limit=120,
	)
	for row in rows:
		row.beneficiary_name = frappe.db.get_value(
			"Beneficiary", row.beneficiary, "beneficiary_name"
		) or row.beneficiary
		row.consultant_name = frappe.db.get_value(
			"Consultant", row.consultant, "consultant_name"
		) or row.consultant
		row.service_name = frappe.db.get_value(
			"Consultation Service", row.service, "service_name"
		) or row.service
		row.start_label = format_datetime(row.start_datetime)
		row.mode_label = {
			"Online": "عن بُعد",
			"In Person": "حضوري",
			"Hybrid": "هجين",
		}.get(row.delivery_mode, row.delivery_mode)
		row.attendance_label = {
			"Not Recorded": "لم يسجل",
			"Attended": "حاضر",
			"Late": "متأخر",
			"No Show": "غائب",
			"Excused": "معتذر",
		}.get(row.attendance_status, row.attendance_status)
	return rows


def get_operations_waitlist():
	rows = frappe.db.get_all(
		"Consultation Request",
		filters={
			"workflow_state": ["in", ["Eligible", "Ready for Assignment"]],
			"linked_case": ["is", "not set"],
		},
		fields=[
			"name",
			"beneficiary",
			"requested_service",
			"urgency",
			"request_datetime",
			"preferred_times",
			"preferred_mode",
			"assigned_coordinator",
		],
		order_by="urgency desc, request_datetime asc",
	)
	for row in rows:
		_decorate_request(row)
	return rows


def get_operations_support():
	return frappe.db.get_all(
		"Support Ticket",
		fields=["name", "subject", "status", "priority", "requester", "opened_on", "modified"],
		order_by="modified desc",
		limit=80,
	)


def get_referral_directory():
	referrals = frappe.db.get_all(
		"Case Referral",
		filters={
			"referral_type": "External",
			"target_organization": ["is", "set"],
		},
		fields=[
			"target_organization",
			"organization_contact",
			"status",
			"modified",
		],
		order_by="modified desc",
	)
	organizations = {}
	for row in referrals:
		current = organizations.setdefault(
			row.target_organization,
			{
				"name": row.target_organization,
				"contact": row.organization_contact,
				"referrals": 0,
				"closed": 0,
				"last_update": row.modified,
			},
		)
		current["referrals"] += 1
		current["closed"] += int(row.status == "Closed")
	return list(organizations.values())


def _decorate_plan_review(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
		or row.beneficiary
	)
	row.consultant_name = (
		frappe.db.get_value("Consultant", row.consultant, "consultant_name")
		or row.consultant
	)
	row.submitted_on_label = (
		format_datetime(row.submitted_on) if row.submitted_on else "غير محدد"
	)


def _decorate_request(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name") or row.beneficiary
	)
	row.service_name = (
		frappe.db.get_value("Consultation Service", row.requested_service, "service_name")
		or row.requested_service
	)
	status = REQUEST_STATUS.get(row.workflow_state, REQUEST_STATUS["Submitted"])
	row.status_label = status["label"]
	row.status_tone = status["tone"]
	row.next_step = status["next_step"]
	row.request_date_label = format_date(row.request_datetime) if row.request_datetime else "—"
	row.mode_label = {
		"Online": "عن بُعد",
		"In Person": "حضوري",
		"Either": "لا فرق",
	}.get(row.get("preferred_mode"), "غير محدد")
