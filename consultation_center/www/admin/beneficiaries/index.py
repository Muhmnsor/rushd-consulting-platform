import frappe

from consultation_center.admin_portal import (
	build_admin_context,
	get_admin_beneficiaries,
	get_admin_services,
)

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-beneficiaries", "إدارة المستفيدين")
	context.beneficiaries = get_admin_beneficiaries()
	context.services = get_admin_services()
	context.open_wizard = frappe.form_dict.get("new") == "1"
