from consultation_center.admin_portal import build_admin_context, get_admin_dashboard

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-workflow", "سير العمل")
	context.dashboard = get_admin_dashboard()
