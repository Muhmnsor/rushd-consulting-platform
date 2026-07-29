import frappe

from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_assessment_context,
	get_consultant_cases,
	get_published_assessment_versions,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-assessments", "المقاييس والنتائج")
	if not context.consultant:
		context.cases = []
		context.versions = []
		context.editor = None
		return
	context.cases = get_consultant_cases(context.consultant.name)
	context.versions = get_published_assessment_versions()
	context.editor = get_consultant_assessment_context(
		context.consultant.name,
		frappe.form_dict.get("case"),
		frappe.form_dict.get("submission"),
	)
