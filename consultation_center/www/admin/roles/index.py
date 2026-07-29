from consultation_center.admin_portal import build_admin_context, get_admin_roles

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-settings", "الأدوار والصلاحيات")
	context.roles = get_admin_roles()
