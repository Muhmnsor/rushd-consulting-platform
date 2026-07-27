from consultation_center.portal import build_portal_context, get_beneficiary_requests

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "requests", "طلباتي")
	context.requests = get_beneficiary_requests(beneficiary.name) if beneficiary else []

