import frappe
from frappe import _
from frappe.utils import cint, strip_html_tags

from consultation_center.portal import get_beneficiary_for_user, require_portal_login

ALLOWED_DELIVERY_MODES = {"Online", "In Person", "Either"}


@frappe.whitelist(methods=["POST"])
def save_consultation_request(
	requested_service: str,
	summary: str,
	preferred_mode: str,
	preferred_times: str | None = None,
	request_name: str | None = None,
	submit: int | str = 0,
	emergency_acknowledged: int | str = 0,
):
	"""Create or update a beneficiary-owned draft without trusting a client beneficiary id."""
	user = require_portal_login()
	beneficiary = get_beneficiary_for_user(user)
	if not beneficiary:
		frappe.throw(_("No active beneficiary profile is linked to this account"), frappe.PermissionError)

	service = frappe.db.get_value(
		"Consultation Service",
		{"name": requested_service, "active": 1},
		["name", "service_name"],
		as_dict=True,
	)
	if not service:
		frappe.throw(_("The selected consultation service is unavailable"))

	if preferred_mode not in ALLOWED_DELIVERY_MODES:
		frappe.throw(_("Invalid delivery mode"))

	summary = strip_html_tags(summary or "").strip()
	preferred_times = strip_html_tags(preferred_times or "").strip()
	should_submit = cint(submit) == 1

	if not summary:
		frappe.throw(_("Please describe what you would like help with"))
	if len(summary) > 2000:
		frappe.throw(_("The request description is too long"))
	if len(preferred_times) > 500:
		frappe.throw(_("The preferred times description is too long"))
	if should_submit and len(summary) < 20:
		frappe.throw(_("Please add a little more detail before submitting the request"))
	if should_submit and not cint(emergency_acknowledged):
		frappe.throw(_("Please confirm that this request is not an emergency"))

	if request_name:
		doc = frappe.get_doc("Consultation Request", request_name)
		if doc.beneficiary != beneficiary.name or doc.owner != user:
			frappe.throw(_("You are not permitted to update this request"), frappe.PermissionError)
		if doc.workflow_state != "Draft":
			frappe.throw(_("Only draft requests can be updated"))
	else:
		doc = frappe.new_doc("Consultation Request")
		doc.beneficiary = beneficiary.name
		doc.source = "Portal"

	doc.requested_service = service.name
	doc.summary = summary
	doc.preferred_mode = preferred_mode
	doc.preferred_times = preferred_times
	doc.workflow_state = "Submitted" if should_submit else "Draft"

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {
		"name": doc.name,
		"workflow_state": doc.workflow_state,
		"message": "تم إرسال طلبك بنجاح" if should_submit else "تم حفظ المسودة",
	}

