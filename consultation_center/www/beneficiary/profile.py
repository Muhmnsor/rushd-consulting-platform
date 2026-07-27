from consultation_center.portal import build_portal_context, calculate_profile_completion

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "profile", "بيانات المستفيد")
	context.profile_completion = calculate_profile_completion(beneficiary)

