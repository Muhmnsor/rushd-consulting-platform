from consultation_center.staff import (
	OPERATIONS_ACCESS,
	build_staff_context,
	get_request_counts,
	get_staff_requests,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"operations-dashboard",
		"لوحة الاستقبال والتشغيل",
		"operations",
		OPERATIONS_ACCESS,
	)
	context.counts = get_request_counts()
	context.requests = get_staff_requests(
		(
			"Submitted",
			"Under Completeness Review",
			"Awaiting Beneficiary Information",
		),
		limit=6,
	)

