from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_cases,
	get_consultant_counts,
	get_upcoming_appointments,
)

no_cache = 1


def get_context(context):
	build_consultant_context(
		context,
		"consultant-dashboard",
		"لوحة المستشار",
	)
	if not context.consultant:
		context.counts = {}
		context.cases = []
		context.appointments = []
		return

	context.counts = get_consultant_counts(context.consultant.name)
	context.cases = get_consultant_cases(context.consultant.name, limit=6)
	context.appointments = get_upcoming_appointments(context.consultant.name, limit=5)
