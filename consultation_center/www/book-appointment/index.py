import frappe
from frappe import _

from consultation_center.permissions import authorized_beneficiaries

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to book an appointment"), frappe.PermissionError)

	beneficiaries = frappe.db.get_all(
		"Beneficiary",
		filters={"portal_user": frappe.session.user},
		pluck="name",
	)
	is_guardian = False
	if not beneficiaries:
		beneficiaries = authorized_beneficiaries(
			frappe.session.user,
			"can_manage_appointments",
		)
		is_guardian = bool(beneficiaries)

	if not beneficiaries:
		frappe.throw(
			_("No beneficiary profile or active guardian authorization is linked to your account"),
			frappe.PermissionError,
		)

	cases = frappe.db.get_all(
		"Consultation Case",
		filters={
			"beneficiary": ["in", beneficiaries],
			"case_status": ["in", ["Assigned", "Awaiting Appointment", "Active", "On Hold"]],
			"primary_consultant": ["is", "set"],
		},
		fields=["name", "beneficiary", "service", "primary_consultant", "case_status"],
	)

	for case in cases:
		case["beneficiary_name"] = frappe.db.get_value(
			"Beneficiary",
			case.beneficiary,
			"beneficiary_name",
		)
		case["service_name"] = frappe.db.get_value("Consultation Service", case.service, "service_name")
		case["consultant_name"] = frappe.db.get_value("Consultant", case.primary_consultant, "consultant_name")

	context.cases = cases
	context.is_guardian = is_guardian
	context.title = _("Book an Appointment")
