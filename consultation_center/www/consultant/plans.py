import frappe

from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_cases,
	get_consultant_plans,
	get_plan_editor_context,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-plans", "الخطط الاستشارية")
	if not context.consultant:
		context.cases = []
		context.plans = []
		context.editor = None
		return
	context.cases = get_consultant_cases(context.consultant.name)
	context.plans = get_consultant_plans(context.consultant.name)
	context.editor = get_plan_editor_context(
		context.consultant.name,
		frappe.form_dict.get("case"),
		frappe.form_dict.get("plan"),
	)
