import frappe
from consultation_center.permissions import has_admin_app_access


def redirect_admin(target):
	if not has_admin_app_access():
		frappe.throw("ليس لديك صلاحية للوصول إلى إدارة رُشد", frappe.PermissionError)
	frappe.redirect(target)
