from urllib.parse import urlencode

import frappe
from frappe.utils import add_days, format_date, format_datetime, get_datetime, now_datetime, nowdate

from consultation_center.staff import CONSULTANT_ACCESS, build_staff_context

CASE_STATUS = {
	"New": "جديدة",
	"Screening": "قيد الفرز",
	"Awaiting Assignment": "بانتظار الإسناد",
	"Assigned": "مسندة",
	"Awaiting Appointment": "بانتظار الموعد",
	"Active": "نشطة",
	"On Hold": "معلقة",
	"Awaiting Report": "بانتظار التقرير",
	"Under Supervisor Review": "تحت مراجعة المشرف",
	"Follow-up": "متابعة",
	"Ready to Close": "جاهزة للإغلاق",
	"Closed": "مغلقة",
	"Reopened": "أعيد فتحها",
	"Cancelled": "ملغاة",
}

PRIORITY_LABELS = {
	"Low": "منخفضة",
	"Normal": "عادية",
	"High": "عالية",
	"Urgent": "عاجلة",
}

APPOINTMENT_STATUS = {
	"Draft": "مسودة",
	"Pending Approval": "بانتظار الاعتماد",
	"Confirmed": "مؤكد",
	"Rescheduled": "أعيدت جدولته",
	"Completed": "مكتمل",
	"No Show": "لم يحضر",
	"Cancelled by Beneficiary": "ألغاه المستفيد",
	"Cancelled by Center": "ألغاه المركز",
	"Expired": "منتهي",
}

SESSION_STATUS = {
	"Draft": "مسودة",
	"Pending Review": "بانتظار المراجعة",
	"Approved": "معتمدة",
	"Returned": "معادة للتعديل",
	"Cancelled": "ملغاة",
}

PLAN_STATUS = {
	"Draft": "مسودة",
	"Pending Review": "بانتظار المراجعة",
	"Active": "معتمدة ونشطة",
	"Returned": "معادة للتعديل",
	"Completed": "مكتملة",
	"Archived": "مؤرشفة",
}

ASSESSMENT_STATUS = {
	"Assigned": "مطلوب",
	"In Progress": "محفوظ جزئيًا",
	"Submitted": "بانتظار المراجعة",
	"Reviewed": "تمت المراجعة",
	"Cancelled": "ملغى",
}

ASSESSMENT_TYPE = {
	"Baseline": "قبلي",
	"Follow-up": "متابعة",
	"Closing": "بعدي",
}

REFERRAL_STATUS = {
	"Draft": "مسودة",
	"Pending Approval": "بانتظار الاعتماد",
	"Approved": "معتمدة",
	"Returned": "معادة للاستكمال",
	"Sent": "أُرسلت",
	"In Progress": "قيد المتابعة",
	"Closed": "مغلقة",
	"Cancelled": "ملغاة",
}

SUPERVISION_STATUS = {
	"Draft": "مسودة",
	"Submitted": "مرسل",
	"In Review": "قيد المراجعة",
	"Answered": "تم الرد",
	"Closed": "مغلق",
	"Cancelled": "ملغى",
}

ESCALATION_STATUS = {
	"Open": "مفتوح",
	"Acknowledged": "تم الاطلاع",
	"Action In Progress": "الإجراء جارٍ",
	"Resolved": "تم الحل",
	"Closed": "مغلق",
	"Cancelled": "ملغى",
}

REFERRAL_TYPE = {"Internal": "داخلية", "External": "خارجية"}
SUPERVISION_TYPE = {
	"Case Guidance": "توجيه للحالة",
	"Documentation Review": "مراجعة توثيق",
	"Ethical Consultation": "استشارة مهنية وأخلاقية",
	"Referral Guidance": "توجيه إحالة",
	"Other": "أخرى",
}
ALERT_TYPE = {
	"Safeguarding": "حماية",
	"Urgent Deterioration": "تدهور عاجل",
	"Conflict of Interest": "تضارب مصالح",
	"Service Risk": "مخاطر تقديم الخدمة",
	"Other": "أخرى",
}
SEVERITY_LABELS = {"Moderate": "متوسطة", "High": "عالية", "Critical": "حرجة"}

ATTENDANCE_STATUS = {
	"Not Recorded": "لم يسجل",
	"Attended": "حضر",
	"No Show": "لم يحضر",
	"Late": "حضر متأخرًا",
}


def build_consultant_context(context, active_nav: str, title: str):
	build_staff_context(
		context,
		active_nav,
		title,
		"consultant",
		CONSULTANT_ACCESS,
	)
	context.consultant = get_current_consultant()
	context.consultant_ready = bool(context.consultant)


def get_current_consultant():
	user = frappe.session.user
	if user in {"Guest", "Administrator"}:
		return None
	return frappe.db.get_value(
		"Consultant",
		{"user": user, "active": 1},
		[
			"name",
			"consultant_name",
			"branch",
			"specializations",
			"languages",
			"default_duration",
			"maximum_daily_sessions",
			"services",
			"qualifications",
			"experience_summary",
			"licenses",
			"suitable_groups",
			"credential_expiry",
			"professional_development_hours",
			"development_requirements",
			"events_platform_url",
		],
		as_dict=True,
	)


def get_consultant_cases(consultant: str, limit: int | None = None):
	rows = frappe.db.get_all(
		"Consultation Case",
		filters={"primary_consultant": consultant},
		fields=[
			"name",
			"beneficiary",
			"service",
			"case_status",
			"priority",
			"opened_on",
			"next_action",
			"next_action_due",
			"completed_sessions",
			"planned_sessions",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)
	for row in rows:
		_decorate_case(row)
	return rows


def get_consultant_case_detail(consultant: str, case_name: str | None):
	if not case_name:
		return None
	row = frappe.db.get_value(
		"Consultation Case",
		{"name": case_name, "primary_consultant": consultant},
		[
			"name",
			"beneficiary",
			"service",
			"case_status",
			"priority",
			"confidentiality_level",
			"opened_on",
			"goal_summary",
			"planned_sessions",
			"completed_sessions",
			"next_action",
			"next_action_due",
			"supervisor",
		],
		as_dict=True,
	)
	if not row:
		return None

	_decorate_case(row)
	row.beneficiary_profile = frappe.db.get_value(
		"Beneficiary",
		row.beneficiary,
		["beneficiary_name", "date_of_birth", "city", "preferred_language"],
		as_dict=True,
	)
	row.request_summary = (
		frappe.db.get_value("Consultation Request", {"linked_case": row.name}, "summary")
		or ""
	)
	return row


def get_upcoming_appointments(consultant: str, limit: int = 6):
	rows = frappe.db.get_all(
		"Consultation Appointment",
		filters={
			"consultant": consultant,
			"start_datetime": [">=", now_datetime()],
			"status": ["in", ["Draft", "Pending Approval", "Confirmed", "Rescheduled"]],
		},
		fields=[
			"name",
			"case",
			"beneficiary",
			"status",
			"start_datetime",
			"delivery_mode",
		],
		order_by="start_datetime asc",
		limit=limit,
	)
	for row in rows:
		row.beneficiary_name = (
			frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
			or row.beneficiary
		)
		row.status_label = APPOINTMENT_STATUS.get(row.status, row.status)
		row.start_label = format_datetime(row.start_datetime)
		row.mode_label = "عن بُعد" if row.delivery_mode == "Online" else "حضوري"
	return rows


def get_consultant_schedule(consultant: str, view: str = "upcoming"):
	today_start = get_datetime(f"{nowdate()} 00:00:00")
	if view == "past":
		filters = {
			"consultant": consultant,
			"start_datetime": [
				"between",
				[
					get_datetime(f"{add_days(nowdate(), -30)} 00:00:00"),
					today_start,
				],
			],
		}
		order_by = "start_datetime desc"
	else:
		filters = {
			"consultant": consultant,
			"start_datetime": [
				"between",
				[
					today_start,
					get_datetime(f"{add_days(nowdate(), 30)} 23:59:59"),
				],
			],
		}
		order_by = "start_datetime asc"

	rows = frappe.db.get_all(
		"Consultation Appointment",
		filters=filters,
		fields=[
			"name",
			"case",
			"beneficiary",
			"service",
			"status",
			"start_datetime",
			"end_datetime",
			"delivery_mode",
			"location",
			"meeting_provider",
			"attendance_status",
			"created_session",
		],
		order_by=order_by,
	)
	for row in rows:
		_decorate_appointment(row)
	return rows


def get_consultant_sessions(consultant: str):
	rows = frappe.db.get_all(
		"Consultation Session",
		filters={"consultant": consultant},
		fields=[
			"name",
			"appointment",
			"case",
			"beneficiary",
			"service",
			"status",
			"attendance_status",
			"actual_start",
			"duration_minutes",
			"topic",
			"modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		row.beneficiary_name = (
			frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
			or row.beneficiary
		)
		row.service_name = (
			frappe.db.get_value("Consultation Service", row.service, "service_name")
			or row.service
		)
		row.status_label = SESSION_STATUS.get(row.status, row.status)
		row.attendance_label = ATTENDANCE_STATUS.get(
			row.attendance_status,
			row.attendance_status,
		)
		row.start_label = (
			format_datetime(row.actual_start) if row.actual_start else "غير محدد"
		)
		row.editable = row.status in {"Draft", "Returned"}
	return rows


def get_session_documentation_queue(consultant: str):
	rows = frappe.db.get_all(
		"Consultation Appointment",
		filters={
			"consultant": consultant,
			"attendance_status": ["in", ["Attended", "Late"]],
		},
		fields=[
			"name",
			"case",
			"beneficiary",
			"service",
			"start_datetime",
			"attendance_status",
			"created_session",
		],
		order_by="start_datetime desc",
	)
	queue = []
	for row in rows:
		session = frappe.db.get_value(
			"Consultation Session",
			{"appointment": row.name},
			["name", "status"],
			as_dict=True,
		)
		if session and session.status not in {"Draft", "Returned"}:
			continue
		_decorate_appointment(row)
		row.session_name = session.name if session else ""
		row.session_status = session.status if session else ""
		row.session_status_label = (
			SESSION_STATUS.get(session.status, session.status)
			if session
			else "غير موثقة"
		)
		queue.append(row)
	return queue


def get_session_documentation_context(
	consultant: str,
	appointment_name: str | None,
	session_name: str | None,
):
	session = None
	if session_name:
		session = frappe.db.get_value(
			"Consultation Session",
			{"name": session_name, "consultant": consultant},
			[
				"name",
				"appointment",
				"case",
				"beneficiary",
				"service",
				"status",
				"actual_start",
				"actual_end",
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
			],
			as_dict=True,
		)
		if not session:
			return None
		appointment_name = session.appointment

	if not appointment_name:
		return None
	appointment = frappe.db.get_value(
		"Consultation Appointment",
		{"name": appointment_name, "consultant": consultant},
		[
			"name",
			"case",
			"beneficiary",
			"service",
			"start_datetime",
			"end_datetime",
			"attendance_status",
		],
		as_dict=True,
	)
	if not appointment or appointment.attendance_status not in {"Attended", "Late"}:
		return None

	appointment.beneficiary_name = (
		frappe.db.get_value("Beneficiary", appointment.beneficiary, "beneficiary_name")
		or appointment.beneficiary
	)
	appointment.service_name = (
		frappe.db.get_value("Consultation Service", appointment.service, "service_name")
		or appointment.service
	)
	appointment.start_label = format_datetime(appointment.start_datetime)
	appointment.attendance_label = ATTENDANCE_STATUS.get(
		appointment.attendance_status,
		appointment.attendance_status,
	)
	return {"appointment": appointment, "session": session}


def get_consultant_counts(consultant: str):
	active_states = [
		"Assigned",
		"Awaiting Appointment",
		"Active",
		"On Hold",
		"Awaiting Report",
		"Under Supervisor Review",
		"Follow-up",
	]
	return {
		"active_cases": frappe.db.count(
			"Consultation Case",
			{"primary_consultant": consultant, "case_status": ["in", active_states]},
		),
		"new_cases": frappe.db.count(
			"Consultation Case",
			{"primary_consultant": consultant, "case_status": "Assigned"},
		),
		"upcoming_appointments": frappe.db.count(
			"Consultation Appointment",
			{
				"consultant": consultant,
				"start_datetime": [">=", now_datetime()],
				"status": ["in", ["Draft", "Pending Approval", "Confirmed", "Rescheduled"]],
			},
		),
		"supervisor_review": frappe.db.count(
			"Consultation Case",
			{
				"primary_consultant": consultant,
				"case_status": "Under Supervisor Review",
			},
		),
		"documentation_due": frappe.db.count(
			"Consultation Appointment",
			{
				"consultant": consultant,
				"attendance_status": ["in", ["Attended", "Late"]],
				"created_session": ["is", "not set"],
			},
		)
		+ frappe.db.count(
			"Consultation Session",
			{"consultant": consultant, "status": ["in", ["Draft", "Returned"]]},
		),
		"assessments_due": frappe.db.count(
			"Assessment Submission",
			{"consultant": consultant, "status": "Submitted"},
		),
		"open_supervision": frappe.db.count(
			"Supervision Request",
			{
				"consultant": consultant,
				"status": ["in", ["Submitted", "In Review", "Answered"]],
			},
		),
		"open_escalations": frappe.db.count(
			"Professional Escalation",
			{
				"consultant": consultant,
				"status": ["in", ["Open", "Acknowledged", "Action In Progress"]],
			},
		),
	}


def get_consultant_plans(consultant: str):
	rows = frappe.db.get_all(
		"Consultation Plan",
		filters={"consultant": consultant},
		fields=[
			"name",
			"case",
			"beneficiary",
			"status",
			"plan_title",
			"review_date",
			"modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		row.beneficiary_name = (
			frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
			or row.beneficiary
		)
		row.status_label = PLAN_STATUS.get(row.status, row.status)
	return rows


def get_plan_editor_context(
	consultant: str,
	case_name: str | None,
	plan_name: str | None,
):
	plan = None
	if plan_name:
		plan = frappe.get_doc("Consultation Plan", plan_name)
		if plan.consultant != consultant:
			return None
		case_name = plan.case
	if not case_name:
		return None
	case = frappe.db.get_value(
		"Consultation Case",
		{"name": case_name, "primary_consultant": consultant},
		["name", "beneficiary", "service", "case_status"],
		as_dict=True,
	)
	if not case:
		return None
	if not plan:
		existing_name = frappe.db.get_value(
			"Consultation Plan",
			{
				"case": case.name,
				"status": ["in", ["Draft", "Returned", "Pending Review", "Active"]],
			},
			"name",
			order_by="modified desc",
		)
		plan = frappe.get_doc("Consultation Plan", existing_name) if existing_name else None
	case.beneficiary_name = (
		frappe.db.get_value("Beneficiary", case.beneficiary, "beneficiary_name")
		or case.beneficiary
	)
	case.service_name = (
		frappe.db.get_value("Consultation Service", case.service, "service_name")
		or case.service
	)
	tasks = (
		frappe.db.get_all(
			"Beneficiary Task",
			filters={"plan": plan.name},
			fields=["name", "task_title", "instructions", "due_date", "status"],
			order_by="due_date asc",
		)
		if plan and plan.status == "Active"
		else []
	)
	if plan:
		plan.status_label = PLAN_STATUS.get(plan.status, plan.status)
	task_statuses = {
		"Pending": "لم تبدأ",
		"In Progress": "قيد التنفيذ",
		"Completed": "مكتملة",
		"Cancelled": "ملغاة",
	}
	for task in tasks:
		task.status_label = task_statuses.get(task.status, task.status)
		task.due_date_label = format_date(task.due_date) if task.due_date else "دون تاريخ"
	return {"case": case, "plan": plan, "tasks": tasks}


def get_published_assessment_versions():
	rows = frappe.db.get_all(
		"Assessment Version",
		filters={"status": "Published"},
		fields=["name", "assessment_template", "version_number"],
		order_by="assessment_template asc, version_number desc",
	)
	for row in rows:
		template = frappe.db.get_value(
			"Assessment Template",
			{"name": row.assessment_template, "active": 1, "responder": "Beneficiary"},
			["template_title", "result_visibility"],
			as_dict=True,
		)
		if not template:
			row.disabled = True
			continue
		row.template_title = template.template_title
		row.result_visibility = template.result_visibility
	return [row for row in rows if not row.get("disabled")]


def get_consultant_assessment_context(
	consultant: str,
	case_name: str | None,
	submission_name: str | None,
):
	if not case_name and submission_name:
		case_name = frappe.db.get_value(
			"Assessment Submission",
			{"name": submission_name, "consultant": consultant},
			"case",
		)
	if not case_name:
		return None
	case = frappe.db.get_value(
		"Consultation Case",
		{"name": case_name, "primary_consultant": consultant},
		["name", "beneficiary", "service", "case_status"],
		as_dict=True,
	)
	if not case:
		return None
	_decorate_case(case)

	submissions = frappe.db.get_all(
		"Assessment Submission",
		filters={"case": case.name, "consultant": consultant},
		fields=[
			"name",
			"assessment_template",
			"assessment_version",
			"assessment_type",
			"status",
			"due_date",
			"percentage_score",
			"result_visible",
			"submitted_on",
			"reviewed_on",
			"modified",
		],
		order_by="modified desc",
	)
	for row in submissions:
		_decorate_assessment(row)

	selected = None
	if submission_name:
		selected = frappe.get_doc("Assessment Submission", submission_name)
		if selected.case != case.name or selected.consultant != consultant:
			return None
		_decorate_assessment(selected)

	comparison = [
		{
			"name": row.name,
			"title": row.template_title,
			"type_label": row.type_label,
			"score": round(row.percentage_score or 0, 1),
			"date_label": row.reviewed_on_label or row.submitted_on_label,
		}
		for row in reversed(submissions)
		if row.status in {"Submitted", "Reviewed"}
	]
	return {
		"case": case,
		"submissions": submissions,
		"selected": selected,
		"comparison": comparison,
	}


def _decorate_assessment(row):
	row.template_title = (
		frappe.db.get_value(
			"Assessment Template",
			row.assessment_template,
			"template_title",
		)
		or row.assessment_template
	)
	row.status_label = ASSESSMENT_STATUS.get(row.status, row.status)
	row.type_label = ASSESSMENT_TYPE.get(row.assessment_type, row.assessment_type)
	row.due_date_label = format_date(row.due_date) if row.due_date else "دون موعد محدد"
	row.submitted_on_label = (
		format_datetime(row.submitted_on) if row.get("submitted_on") else ""
	)
	row.reviewed_on_label = (
		format_datetime(row.reviewed_on) if row.get("reviewed_on") else ""
	)


def get_consultant_referrals(consultant: str, case_name: str | None = None):
	filters = {"consultant": consultant}
	if case_name:
		filters["case"] = case_name
	rows = frappe.db.get_all(
		"Case Referral",
		filters=filters,
		fields=[
			"name", "case", "beneficiary", "status", "priority", "referral_type",
			"target_organization", "target_service", "modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_professional_record(row, REFERRAL_STATUS)
	return rows


def get_consultant_supervision_requests(consultant: str):
	rows = frappe.db.get_all(
		"Supervision Request",
		filters={"consultant": consultant},
		fields=[
			"name", "case", "supervisor", "status", "priority", "request_type",
			"supervision_question", "supervisor_response", "required_action",
			"follow_up_date", "requested_on", "modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_professional_record(row, SUPERVISION_STATUS)
	return rows


def get_consultant_escalations(consultant: str):
	rows = frappe.db.get_all(
		"Professional Escalation",
		filters={"consultant": consultant},
		fields=[
			"name", "case", "beneficiary", "status", "severity", "alert_type",
			"alert_summary", "immediate_action", "supervisor_action",
			"resolution_note", "follow_up_date", "reported_on", "modified",
		],
		order_by="modified desc",
	)
	for row in rows:
		_decorate_professional_record(row, ESCALATION_STATUS)
	return rows


def _decorate_professional_record(row, statuses):
	row.status_label = statuses.get(row.status, row.status)
	row.priority_label = PRIORITY_LABELS.get(row.get("priority"), row.get("priority", ""))
	row.referral_type_label = REFERRAL_TYPE.get(
		row.get("referral_type"),
		row.get("referral_type", ""),
	)
	row.request_type_label = SUPERVISION_TYPE.get(
		row.get("request_type"),
		row.get("request_type", ""),
	)
	row.alert_type_label = ALERT_TYPE.get(row.get("alert_type"), row.get("alert_type", ""))
	row.severity_label = SEVERITY_LABELS.get(row.get("severity"), row.get("severity", ""))
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


def get_consultant_availability(consultant: str):
	rules = frappe.db.get_all(
		"Consultant Availability Rule",
		filters={"consultant": consultant},
		fields=[
			"name",
			"weekday",
			"active",
			"start_time",
			"end_time",
			"slot_duration",
			"service",
			"delivery_mode",
			"branch",
			"capacity",
			"effective_from",
			"effective_to",
		],
		order_by="weekday asc, start_time asc",
	)
	for row in rules:
		row.weekday_label = {
			"Monday": "الاثنين",
			"Tuesday": "الثلاثاء",
			"Wednesday": "الأربعاء",
			"Thursday": "الخميس",
			"Friday": "الجمعة",
			"Saturday": "السبت",
			"Sunday": "الأحد",
		}.get(row.weekday, row.weekday)
		row.mode_label = {
			"Online": "عن بُعد",
			"In Person": "حضوري",
			"Both": "حضوري وعن بُعد",
		}.get(row.delivery_mode, row.delivery_mode)
	time_off = frappe.db.get_all(
		"Consultant Time Off",
		filters={"consultant": consultant, "to_datetime": [">=", now_datetime()]},
		fields=["name", "from_datetime", "to_datetime", "reason", "approved_by"],
		order_by="from_datetime asc",
	)
	for row in time_off:
		row.from_label = format_datetime(row.from_datetime)
		row.to_label = format_datetime(row.to_datetime)
	return {"rules": rules, "time_off": time_off}


def get_consultant_report(consultant: str):
	cases = get_consultant_cases(consultant)
	appointments = frappe.db.get_all(
		"Consultation Appointment",
		filters={"consultant": consultant},
		fields=["name", "attendance_status"],
	)
	sessions = frappe.db.get_all(
		"Consultation Session",
		filters={"consultant": consultant},
		fields=["name", "status"],
	)
	assessments = frappe.db.get_all(
		"Assessment Submission",
		filters={"consultant": consultant, "status": "Reviewed"},
		fields=["percentage_score", "assessment_type"],
	)
	attended = sum(
		1 for row in appointments if row.attendance_status in {"Attended", "Late"}
	)
	no_show = sum(1 for row in appointments if row.attendance_status == "No Show")
	approved_sessions = sum(1 for row in sessions if row.status == "Approved")
	return {
		"cases": len(cases),
		"active_cases": sum(1 for row in cases if row.case_status != "Closed"),
		"sessions": len(sessions),
		"approved_sessions": approved_sessions,
		"documentation_rate": (
			round(approved_sessions / len(sessions) * 100) if sessions else 0
		),
		"appointments": len(appointments),
		"attended": attended,
		"no_show": no_show,
		"attendance_rate": (
			round(attended / (attended + no_show) * 100)
			if attended + no_show
			else 0
		),
		"reviewed_assessments": len(assessments),
		"average_assessment_score": (
			round(
				sum(row.percentage_score or 0 for row in assessments)
				/ len(assessments),
				1,
			)
			if assessments
			else 0
		),
		"open_referrals": frappe.db.count(
			"Case Referral",
			{
				"consultant": consultant,
				"status": ["not in", ["Closed", "Cancelled"]],
			},
		),
		"open_supervision": frappe.db.count(
			"Supervision Request",
			{
				"consultant": consultant,
				"status": ["not in", ["Closed", "Cancelled"]],
			},
		),
	}


def redirect_consultant_login():
	redirect_to = frappe.request.path if frappe.request else "/consultant"
	frappe.redirect(f"/login?{urlencode({'redirect-to': redirect_to})}")


def _decorate_case(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
		or row.beneficiary
	)
	row.service_name = (
		frappe.db.get_value("Consultation Service", row.service, "service_name")
		or row.service
	)
	row.status_label = CASE_STATUS.get(row.case_status, row.case_status)
	row.priority_label = PRIORITY_LABELS.get(row.priority, row.priority)
	row.opened_on_label = format_date(row.opened_on) if row.opened_on else "—"
	row.next_action_due_label = (
		format_date(row.next_action_due) if row.next_action_due else "غير محدد"
	)


def _decorate_appointment(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name")
		or row.beneficiary
	)
	row.service_name = (
		frappe.db.get_value("Consultation Service", row.service, "service_name")
		or row.service
	)
	row.status_label = APPOINTMENT_STATUS.get(row.get("status"), row.get("status", ""))
	row.attendance_label = ATTENDANCE_STATUS.get(
		row.get("attendance_status"),
		row.get("attendance_status", ""),
	)
	row.start_label = format_datetime(row.start_datetime)
	row.end_label = format_datetime(row.end_datetime) if row.get("end_datetime") else ""
	row.mode_label = "عن بُعد" if row.get("delivery_mode") == "Online" else "حضوري"
	row.can_record_attendance = bool(
		row.get("start_datetime")
		and get_datetime(row.start_datetime) <= now_datetime()
		and row.get("status")
		not in {"Cancelled by Beneficiary", "Cancelled by Center", "Expired"}
	)
	row.can_document = row.get("attendance_status") in {"Attended", "Late"}
