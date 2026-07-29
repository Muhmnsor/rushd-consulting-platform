import frappe

from consultation_center.portal import (
	build_portal_context,
	get_beneficiary_assessment_detail,
	get_beneficiary_assessments,
)

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "assessments", "المقاييس والنماذج")
	context.assessments = (
		get_beneficiary_assessments(beneficiary.name) if beneficiary else []
	)
	context.selected_assessment = (
		get_beneficiary_assessment_detail(
			beneficiary.name,
			frappe.form_dict.get("assessment"),
		)
		if beneficiary
		else None
	)
