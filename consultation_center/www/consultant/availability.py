from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_availability,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-availability", "التوفر والطاقة")
	context.availability = (
		get_consultant_availability(context.consultant.name)
		if context.consultant
		else {"rules": [], "time_off": []}
	)
