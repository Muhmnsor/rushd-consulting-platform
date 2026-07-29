from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_supervisor_consultant_performance,
	get_supervisor_report,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-reports",
		"تقارير الإشراف والجودة",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.report = get_supervisor_report(context.staff_user)
	context.consultants = get_supervisor_consultant_performance(context.staff_user)
