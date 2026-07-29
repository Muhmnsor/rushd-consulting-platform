import frappe
from frappe.utils import cint, now_datetime, strip_html_tags

from consultation_center.consultant_portal import get_current_consultant
from consultation_center.staff import SUPERVISOR_ACCESS, require_staff_access


@frappe.whitelist(methods=["POST"])
def save_case_referral(
	case: str,
	referral_name: str | None = None,
	referral_type: str = "Internal",
	priority: str = "Normal",
	referral_reason: str | None = None,
	target_service: str | None = None,
	target_organization: str | None = None,
	organization_contact: str | None = None,
	permitted_information: str | None = None,
	consent_confirmed: int | str = 0,
	submit_for_approval: int | str = 0,
):
	consultant = _require_consultant()
	case_doc = _consultant_case(case, consultant.name)
	if referral_type not in {"Internal", "External"}:
		frappe.throw("نوع الإحالة غير صالح")
	if priority not in {"Low", "Normal", "High", "Urgent"}:
		frappe.throw("أولوية الإحالة غير صالحة")

	if referral_name:
		doc = frappe.get_doc("Case Referral", referral_name)
		if doc.case != case_doc.name or doc.consultant != consultant.name:
			frappe.throw("لا يمكنك تعديل هذه الإحالة", frappe.PermissionError)
		if doc.status not in {"Draft", "Returned"}:
			frappe.throw("الإحالة في حالة لا تسمح بالتعديل")
	else:
		doc = frappe.new_doc("Case Referral")
		doc.case = case_doc.name
		doc.beneficiary = case_doc.beneficiary
		doc.consultant = consultant.name

	doc.referral_type = referral_type
	doc.priority = priority
	doc.referral_reason = _clean(referral_reason, 5000, "سبب الإحالة")
	doc.target_service = target_service or None
	doc.target_organization = _clean(target_organization, 180, "الجهة المستهدفة")
	doc.organization_contact = _clean(organization_contact, 1000, "بيانات تواصل الجهة")
	doc.permitted_information = _clean(
		permitted_information,
		3000,
		"البيانات المسموح بمشاركتها",
	)
	doc.consent_confirmed = cint(consent_confirmed)
	doc.status = "Pending Approval" if cint(submit_for_approval) else "Draft"
	doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"status": doc.status,
		"message": "تم إرسال الإحالة للمشرف" if doc.status == "Pending Approval" else "تم حفظ مسودة الإحالة",
	}


@frappe.whitelist(methods=["POST"])
def review_case_referral(
	referral_name: str,
	decision: str,
	supervisor_note: str | None = None,
):
	user, roles = require_staff_access(SUPERVISOR_ACCESS)
	if decision not in {"approve", "return"}:
		frappe.throw("قرار الإحالة غير صالح")
	doc = frappe.get_doc("Case Referral", referral_name)
	_require_assigned_supervisor(doc.case, user, roles)
	if doc.status != "Pending Approval":
		frappe.throw("لا يمكن مراجعة الإحالة من حالتها الحالية")
	doc.supervisor_note = _clean(supervisor_note, 3000, "ملاحظة المشرف")
	doc.status = "Approved" if decision == "approve" else "Returned"
	doc.save(ignore_permissions=True)
	if decision == "approve":
		_set_case_next_action(doc.case, "تنفيذ الإحالة المعتمدة")
	return {
		"name": doc.name,
		"status": doc.status,
		"message": "تم اعتماد الإحالة" if decision == "approve" else "أعيدت الإحالة للاستكمال",
	}


@frappe.whitelist(methods=["POST"])
def update_case_referral(
	referral_name: str,
	action: str,
	follow_up_note: str | None = None,
	outcome: str | None = None,
):
	consultant = _require_consultant()
	doc = frappe.get_doc("Case Referral", referral_name)
	if doc.consultant != consultant.name:
		frappe.throw("لا يمكنك تحديث هذه الإحالة", frappe.PermissionError)
	status_by_action = {"mark_sent": "Sent", "start_follow_up": "In Progress", "close": "Closed"}
	if action not in status_by_action:
		frappe.throw("إجراء الإحالة غير صالح")
	doc.follow_up_note = _clean(follow_up_note, 4000, "ملاحظة المتابعة")
	doc.outcome = _clean(outcome, 4000, "نتيجة الإحالة")
	if action == "close" and not doc.outcome:
		frappe.throw("اكتب نتيجة الإحالة قبل إغلاقها")
	doc.status = status_by_action[action]
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status, "message": "تم تحديث الإحالة"}


@frappe.whitelist(methods=["POST"])
def create_supervision_request(
	case: str,
	request_type: str,
	supervision_question: str,
	priority: str = "Normal",
	preferred_datetime: str | None = None,
):
	consultant = _require_consultant()
	case_doc = _consultant_case(case, consultant.name)
	if not case_doc.supervisor:
		frappe.throw("لا يوجد مشرف معين لهذه الحالة")
	if request_type not in {
		"Case Guidance",
		"Documentation Review",
		"Ethical Consultation",
		"Referral Guidance",
		"Other",
	}:
		frappe.throw("نوع طلب الإشراف غير صالح")
	if priority not in {"Normal", "High", "Urgent"}:
		frappe.throw("أولوية طلب الإشراف غير صالحة")
	doc = frappe.get_doc(
		{
			"doctype": "Supervision Request",
			"case": case_doc.name,
			"consultant": consultant.name,
			"supervisor": case_doc.supervisor,
			"request_type": request_type,
			"supervision_question": _clean(supervision_question, 5000, "سؤال الإشراف"),
			"priority": priority,
			"preferred_datetime": preferred_datetime or None,
			"status": "Submitted",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "message": "تم إرسال طلب الإشراف"}


@frappe.whitelist(methods=["POST"])
def respond_supervision_request(
	request_name: str,
	action: str,
	supervisor_response: str | None = None,
	required_action: str | None = None,
	follow_up_date: str | None = None,
):
	user, roles = require_staff_access(SUPERVISOR_ACCESS)
	doc = frappe.get_doc("Supervision Request", request_name)
	_require_direct_supervisor(doc.supervisor, user, roles)
	if action not in {"start_review", "answer"}:
		frappe.throw("إجراء طلب الإشراف غير صالح")
	if doc.status not in {"Submitted", "In Review"}:
		frappe.throw("طلب الإشراف في حالة لا تسمح بهذا الإجراء")
	doc.supervisor_response = _clean(supervisor_response, 5000, "رد المشرف")
	doc.required_action = _clean(required_action, 4000, "الإجراء المطلوب")
	doc.follow_up_date = follow_up_date or None
	doc.status = "In Review" if action == "start_review" else "Answered"
	doc.save(ignore_permissions=True)
	if action == "answer" and doc.required_action:
		_set_case_next_action(doc.case, doc.required_action[:180])
	return {"name": doc.name, "status": doc.status, "message": "تم تحديث طلب الإشراف"}


@frappe.whitelist(methods=["POST"])
def close_supervision_request(request_name: str):
	consultant = _require_consultant()
	doc = frappe.get_doc("Supervision Request", request_name)
	if doc.consultant != consultant.name:
		frappe.throw("لا يمكنك إغلاق هذا الطلب", frappe.PermissionError)
	if doc.status != "Answered":
		frappe.throw("لا يمكن إغلاق الطلب قبل رد المشرف")
	doc.status = "Closed"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status, "message": "تم إغلاق طلب الإشراف"}


@frappe.whitelist(methods=["POST"])
def create_professional_escalation(
	case: str,
	alert_type: str,
	severity: str,
	alert_summary: str,
	immediate_action: str | None = None,
	emergency_protocol_activated: int | str = 0,
):
	consultant = _require_consultant()
	case_doc = _consultant_case(case, consultant.name)
	if not case_doc.supervisor:
		frappe.throw("لا يوجد مشرف معين لهذه الحالة")
	if alert_type not in {
		"Safeguarding",
		"Urgent Deterioration",
		"Conflict of Interest",
		"Service Risk",
		"Other",
	}:
		frappe.throw("نوع التنبيه المهني غير صالح")
	if severity not in {"Moderate", "High", "Critical"}:
		frappe.throw("درجة التصعيد غير صالحة")
	doc = frappe.get_doc(
		{
			"doctype": "Professional Escalation",
			"case": case_doc.name,
			"beneficiary": case_doc.beneficiary,
			"consultant": consultant.name,
			"assigned_supervisor": case_doc.supervisor,
			"alert_type": alert_type,
			"severity": severity,
			"alert_summary": _clean(alert_summary, 5000, "ملخص التنبيه"),
			"immediate_action": _clean(immediate_action, 5000, "الإجراء الفوري"),
			"emergency_protocol_activated": cint(emergency_protocol_activated),
			"status": "Open",
		}
	)
	doc.insert(ignore_permissions=True)
	_set_case_next_action(case_doc.name, "متابعة التصعيد المهني")
	return {"name": doc.name, "message": "تم إشعار المشرف وفتح التصعيد"}


@frappe.whitelist(methods=["POST"])
def update_professional_escalation(
	escalation_name: str,
	action: str,
	supervisor_action: str | None = None,
	resolution_note: str | None = None,
	follow_up_date: str | None = None,
):
	user, roles = require_staff_access(SUPERVISOR_ACCESS)
	doc = frappe.get_doc("Professional Escalation", escalation_name)
	_require_direct_supervisor(doc.assigned_supervisor, user, roles)
	status_by_action = {
		"acknowledge": "Acknowledged",
		"start_action": "Action In Progress",
		"resolve": "Resolved",
		"close": "Closed",
	}
	if action not in status_by_action:
		frappe.throw("إجراء التصعيد غير صالح")
	doc.supervisor_action = _clean(supervisor_action, 5000, "إجراء المشرف")
	doc.resolution_note = _clean(resolution_note, 5000, "ملاحظة الحل")
	doc.follow_up_date = follow_up_date or None
	doc.status = status_by_action[action]
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status, "message": "تم تحديث التصعيد"}


def _require_consultant():
	consultant = get_current_consultant()
	if not consultant:
		frappe.throw("لا يوجد ملف مستشار نشط مرتبط بالحساب", frappe.PermissionError)
	return consultant


def _consultant_case(case_name: str, consultant: str):
	case = frappe.db.get_value(
		"Consultation Case",
		{"name": case_name, "primary_consultant": consultant},
		["name", "beneficiary", "supervisor"],
		as_dict=True,
	)
	if not case:
		frappe.throw("الحالة غير مسندة إلى هذا المستشار", frappe.PermissionError)
	return case


def _require_assigned_supervisor(case_name: str, user: str, roles: set[str]):
	supervisor = frappe.db.get_value("Consultation Case", case_name, "supervisor")
	_require_direct_supervisor(supervisor, user, roles)


def _require_direct_supervisor(supervisor: str | None, user: str, roles: set[str]):
	if (
		user != "Administrator"
		and not roles & {"System Manager", "Center Director"}
		and supervisor
		and supervisor != user
	):
		frappe.throw("هذا السجل ليس ضمن نطاق إشرافك", frappe.PermissionError)


def _set_case_next_action(case_name: str, action: str):
	frappe.db.set_value(
		"Consultation Case",
		case_name,
		"next_action",
		action,
		update_modified=False,
	)


def _clean(value: str | None, limit: int, label: str) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > limit:
		frappe.throw(f"{label} أطول من الحد المسموح")
	return value
