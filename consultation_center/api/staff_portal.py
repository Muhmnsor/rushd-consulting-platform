import frappe
from frappe.utils import now_datetime, strip_html_tags

from consultation_center.staff import (
	OPERATIONS_ACCESS,
	SUPERVISOR_ACCESS,
	consultant_supports_service,
	require_staff_access,
)


@frappe.whitelist(methods=["POST"])
def review_consultation_request(
	request_name: str,
	action: str,
	operations_note: str | None = None,
	beneficiary_note: str | None = None,
):
	user, _roles = require_staff_access(OPERATIONS_ACCESS)
	doc = frappe.get_doc("Consultation Request", request_name)
	operations_note = _clean_note(operations_note)
	beneficiary_note = _clean_note(beneficiary_note)

	transitions = {
		"start_review": {
			"from": {"Submitted"},
			"to": "Under Completeness Review",
		},
		"request_information": {
			"from": {"Submitted", "Under Completeness Review"},
			"to": "Awaiting Beneficiary Information",
		},
		"send_to_triage": {
			"from": {"Under Completeness Review"},
			"to": "Ready for Triage",
		},
	}
	transition = transitions.get(action)
	if not transition:
		frappe.throw("إجراء مراجعة غير صالح")
	if doc.workflow_state not in transition["from"]:
		frappe.throw("لا يمكن تنفيذ هذا الإجراء من حالة الطلب الحالية")
	if action == "request_information" and not beneficiary_note:
		frappe.throw("اكتب للمستفيد البيانات المطلوب استكمالها")

	doc.workflow_state = transition["to"]
	doc.assigned_coordinator = user
	doc.operations_note = operations_note
	doc.beneficiary_action_note = (
		beneficiary_note if action == "request_information" else ""
	)
	doc.save(ignore_permissions=True)

	return {
		"name": doc.name,
		"workflow_state": doc.workflow_state,
		"message": {
			"start_review": "بدأت مراجعة الطلب",
			"request_information": "أعيد الطلب للمستفيد لاستكمال البيانات",
			"send_to_triage": "تم تحويل الطلب إلى طابور الفرز",
		}[action],
	}


@frappe.whitelist(methods=["POST"])
def triage_consultation_request(
	request_name: str,
	decision: str,
	triage_note: str | None = None,
	beneficiary_note: str | None = None,
):
	user, _roles = require_staff_access(SUPERVISOR_ACCESS)
	doc = frappe.get_doc("Consultation Request", request_name)
	if doc.workflow_state != "Ready for Triage":
		frappe.throw("لا يمكن فرز الطلب من حالته الحالية")

	triage_note = _clean_note(triage_note)
	beneficiary_note = _clean_note(beneficiary_note)
	decisions = {
		"eligible": ("Eligible", "Eligible", "Completed"),
		"not_eligible": ("Not Eligible", "Not Eligible", "Completed"),
		"request_information": ("Awaiting Beneficiary Information", "Pending", "In Progress"),
	}
	result = decisions.get(decision)
	if not result:
		frappe.throw("قرار الفرز غير صالح")
	if decision in {"not_eligible", "request_information"} and not beneficiary_note:
		frappe.throw("اكتب توضيحًا عامًا مناسبًا للمستفيد")

	doc.workflow_state, doc.eligibility_status, doc.screening_status = result
	doc.triage_note = triage_note
	doc.beneficiary_action_note = beneficiary_note
	doc.decision_by = user
	doc.decision_on = now_datetime()
	doc.rejection_reason = beneficiary_note if decision == "not_eligible" else ""
	doc.save(ignore_permissions=True)

	return {
		"name": doc.name,
		"workflow_state": doc.workflow_state,
		"message": {
			"eligible": "تم اعتماد ملاءمة الطلب للخدمة",
			"not_eligible": "تم حفظ قرار عدم ملاءمة الخدمة",
			"request_information": "أعيد الطلب لاستكمال المعلومات",
		}[decision],
	}


@frappe.whitelist(methods=["POST"])
def assign_consultation_request(
	request_name: str,
	consultant: str,
	priority: str = "Normal",
):
	user, _roles = require_staff_access(SUPERVISOR_ACCESS)
	if priority not in {"Low", "Normal", "High", "Urgent"}:
		frappe.throw("أولوية الحالة غير صالحة")

	# Locking the request prevents two supervisors from creating duplicate cases.
	frappe.db.sql(
		"select name from `tabConsultation Request` where name = %s for update",
		(request_name,),
	)
	request_doc = frappe.get_doc("Consultation Request", request_name)
	if request_doc.linked_case:
		existing_case = frappe.get_doc("Consultation Case", request_doc.linked_case)
		if existing_case.primary_consultant == consultant:
			return {
				"case": existing_case.name,
				"message": "الطلب مسند بالفعل إلى هذا المستشار",
			}
		frappe.throw("تم تحويل هذا الطلب إلى حالة من قبل")
	if request_doc.workflow_state not in {"Eligible", "Ready for Assignment"}:
		frappe.throw("لا يمكن إسناد الطلب من حالته الحالية")

	beneficiary = frappe.db.get_value(
		"Beneficiary",
		request_doc.beneficiary,
		["guardian_required", "consent_status"],
		as_dict=True,
	)
	if (
		beneficiary
		and beneficiary.guardian_required
		and beneficiary.consent_status != "Granted"
	):
		frappe.throw("يلزم اعتماد موافقة ولي الأمر قبل إسناد الحالة")

	consultant_doc = frappe.get_doc("Consultant", consultant)
	if not consultant_doc.active:
		frappe.throw("المستشار المحدد غير نشط")
	if not consultant_supports_service(
		consultant_doc.services,
		request_doc.requested_service,
	):
		frappe.throw("المستشار المحدد غير مرتبط بالخدمة المطلوبة")

	case_doc = frappe.get_doc(
		{
			"doctype": "Consultation Case",
			"beneficiary": request_doc.beneficiary,
			"service": request_doc.requested_service,
			"case_status": "Assigned",
			"priority": priority,
			"case_owner": request_doc.assigned_coordinator or user,
			"supervisor": user,
			"primary_consultant": consultant_doc.name,
			"next_action": "تنسيق الموعد الأول مع المستفيد",
		}
	).insert(ignore_permissions=True)

	request_doc.workflow_state = "Converted to Case"
	request_doc.linked_case = case_doc.name
	request_doc.save(ignore_permissions=True)

	return {
		"case": case_doc.name,
		"consultant": consultant_doc.consultant_name,
		"message": "تم إنشاء الحالة وإسنادها للمستشار",
	}


@frappe.whitelist(methods=["POST"])
def review_consultation_session(
	session_name: str,
	decision: str,
	review_note: str | None = None,
):
	user, _roles = require_staff_access(SUPERVISOR_ACCESS)
	if decision not in {"approve", "return"}:
		frappe.throw("قرار مراجعة الجلسة غير صالح")

	session = frappe.get_doc("Consultation Session", session_name)
	if session.status != "Pending Review":
		frappe.throw("لا يمكن مراجعة الجلسة من حالتها الحالية")

	review_note = _clean_note(review_note)
	if decision == "return" and not review_note:
		frappe.throw("اكتب سبب إعادة الجلسة للمستشار")

	session.review_note = review_note
	session.status = "Approved" if decision == "approve" else "Returned"
	session.save(ignore_permissions=True)

	if decision == "approve":
		case_doc = frappe.get_doc("Consultation Case", session.case)
		case_doc.completed_sessions = (case_doc.completed_sessions or 0) + 1
		case_doc.next_action = session.next_action or case_doc.next_action
		case_doc.next_action_due = session.next_action_due or case_doc.next_action_due
		if case_doc.case_status in {
			"Assigned",
			"Awaiting Appointment",
			"Awaiting Report",
			"Under Supervisor Review",
		}:
			case_doc.case_status = "Active"
		case_doc.save(ignore_permissions=True)

	return {
		"name": session.name,
		"status": session.status,
		"reviewed_by": user,
		"message": (
			"تم اعتماد الجلسة وتحديث تقدم الحالة"
			if decision == "approve"
			else "أعيدت الجلسة للمستشار لاستكمالها"
		),
	}


def _clean_note(value: str | None) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > 2000:
		frappe.throw("الملاحظة أطول من الحد المسموح")
	return value
