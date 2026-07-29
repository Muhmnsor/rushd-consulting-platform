from consultation_center.admin_portal import build_admin_context

no_cache = 1


def get_context(context):
	build_admin_context(context, "admin-settings", "تهيئة المنصة")
