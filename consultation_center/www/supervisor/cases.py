import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_supervised_case_detail,
	get_supervised_cases,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-cases",
		"الحالات تحت الإشراف",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.cases = get_supervised_cases(context.staff_user)
	context.selected_case = get_supervised_case_detail(
		frappe.form_dict.get("case"),
		context.cases,
	)
