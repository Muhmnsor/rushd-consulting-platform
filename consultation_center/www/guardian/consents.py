from consultation_center.guardian_portal import build_guardian_context, get_guardian_consents

no_cache = 1


def get_context(context):
	guardian = build_guardian_context(context, "guardian-consents", "موافقات ولي الأمر")
	context.consents = get_guardian_consents(guardian.name) if guardian else []

