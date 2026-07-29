from consultation_center.staff import OPERATIONS_ACCESS, build_staff_context, get_operations_appointments

no_cache = 1


def get_context(context):
	build_staff_context(context, "operations-attendance", "إدارة الحضور", "operations", OPERATIONS_ACCESS)
	context.appointments = get_operations_appointments()
