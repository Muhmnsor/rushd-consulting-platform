import frappe
from frappe.utils import now_datetime, strip_html_tags

from consultation_center.staff import OPERATIONS_ACCESS, SUPERVISOR_ACCESS, require_staff_access


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


def _clean_note(value: str | None) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > 2000:
		frappe.throw("الملاحظة أطول من الحد المسموح")
	return value

