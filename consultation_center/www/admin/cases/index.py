import frappe

from consultation_center.admin_portal import build_admin_context, get_admin_case_context

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-cases", "الحالات والجلسات")
	data = get_admin_case_context(
		frappe.form_dict.get("case"),
		frappe.form_dict.get("q"),
	)
	context.cases = data.cases
	context.selected_case = data.selected_case
	context.search_query = frappe.form_dict.get("q") or ""
