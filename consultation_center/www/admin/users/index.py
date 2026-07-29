import frappe

from consultation_center.admin_portal import build_admin_context, get_admin_users

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-settings", "المستخدمون")
	context.users_data = get_admin_users(frappe.form_dict.get("q"))
