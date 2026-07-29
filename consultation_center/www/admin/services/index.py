from consultation_center.admin_portal import build_admin_catalog_context
no_cache = 1
def get_context(context): build_admin_catalog_context(context, "services")
