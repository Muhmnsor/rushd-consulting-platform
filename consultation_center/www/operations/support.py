from consultation_center.staff import OPERATIONS_ACCESS, build_staff_context, get_operations_support

no_cache = 1


def get_context(context):
	build_staff_context(context, "operations-support", "خدمة المستفيد", "operations", OPERATIONS_ACCESS)
	context.tickets = get_operations_support()
