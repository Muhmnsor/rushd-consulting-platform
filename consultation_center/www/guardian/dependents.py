from consultation_center.guardian_portal import build_guardian_context, get_guardian_authorizations

no_cache = 1


def get_context(context):
	guardian = build_guardian_context(
		context,
		"guardian-dependents",
		"المستفيدون المرتبطون",
	)
	context.authorizations = get_guardian_authorizations(guardian.name) if guardian else []

