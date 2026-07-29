import frappe

from consultation_center.admin_portal import build_admin_context, get_admin_assessments

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-assessments", "المقاييس والجودة")
	context.assessments = get_admin_assessments()
	context.open_wizard = frappe.form_dict.get("new") == "1"
