import frappe

from consultation_center.admin_portal import (
	build_admin_context,
	get_admin_consultants,
	get_admin_services,
	get_admin_supervisors,
)

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-consultants", "إدارة المستشارين")
	context.consultants = get_admin_consultants()
	context.services = get_admin_services()
	context.supervisors = get_admin_supervisors()
	context.open_wizard = frappe.form_dict.get("new") == "1"
