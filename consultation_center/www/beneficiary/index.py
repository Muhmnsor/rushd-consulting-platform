from consultation_center.portal import (
	build_portal_context,
	calculate_profile_completion,
	get_beneficiary_requests,
	get_next_appointment,
)

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "dashboard", "لوحة المستفيد")
	if not beneficiary:
		context.requests = []
		context.next_appointment = None
		context.profile_completion = 0
		return

	context.requests = get_beneficiary_requests(beneficiary.name, limit=4)
	context.next_appointment = get_next_appointment(beneficiary.name)
	context.profile_completion = calculate_profile_completion(beneficiary)

