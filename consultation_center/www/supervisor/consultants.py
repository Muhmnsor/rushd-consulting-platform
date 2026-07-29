from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_supervisor_consultant_performance,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-consultants",
		"أداء المستشارين",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.consultants = get_supervisor_consultant_performance(context.staff_user)
