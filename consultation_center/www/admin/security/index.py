from consultation_center.admin_portal import build_admin_context, get_admin_security

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-settings", "الأمان")
	context.security = get_admin_security()
