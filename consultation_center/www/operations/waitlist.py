from consultation_center.staff import OPERATIONS_ACCESS, build_staff_context, get_operations_waitlist

no_cache = 1


def get_context(context):
	build_staff_context(context, "operations-waitlist", "قائمة الانتظار", "operations", OPERATIONS_ACCESS)
	context.requests = get_operations_waitlist()
