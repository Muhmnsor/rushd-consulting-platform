from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_request_counts,
	get_staff_requests,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-dashboard",
		"لوحة المشرف",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.counts = get_request_counts()
	context.requests = get_staff_requests(("Ready for Triage",), limit=8)

