import frappe

from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_case_detail,
	get_consultant_cases,
)

no_cache = 1


def get_context(context):
	build_consultant_context(
		context,
		"consultant-cases",
		"حالاتي",
	)
	if not context.consultant:
		context.cases = []
		context.selected_case = None
		return

	context.cases = get_consultant_cases(context.consultant.name)
	selected_name = frappe.form_dict.get("case")
	if not selected_name and context.cases:
		selected_name = context.cases[0].name
	context.selected_case = get_consultant_case_detail(
		context.consultant.name,
		selected_name,
	)
