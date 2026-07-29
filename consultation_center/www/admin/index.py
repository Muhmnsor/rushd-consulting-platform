from consultation_center.admin_portal import (
	build_admin_context,
	get_admin_case_context,
	get_admin_dashboard,
)

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-dashboard", "مركز إدارة رُشد")
	context.dashboard = get_admin_dashboard()
	context.recent_cases = get_admin_case_context().cases[:6]
