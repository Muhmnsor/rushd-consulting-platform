import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_assessment_oversight,
	get_assessment_oversight_detail,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-assessments",
		"متابعة المقاييس",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.assessments = get_assessment_oversight()
	context.selected_assessment = get_assessment_oversight_detail(
		frappe.form_dict.get("assessment")
	)
