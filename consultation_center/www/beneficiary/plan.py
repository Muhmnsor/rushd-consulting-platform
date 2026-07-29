from consultation_center.portal import build_portal_context, get_active_beneficiary_plan

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "plan", "خطتي الاستشارية")
	context.plan = get_active_beneficiary_plan(beneficiary.name) if beneficiary else None
