import frappe

from consultation_center.permissions import has_admin_app_access

no_cache = 1

ROUTES = {
	"": "/app/rushd",
	"users": "/app/user",
	"roles": "/app/role",
	"consultants": "/app/consultant",
	"services": "/app/consultation-service",
	"forms": "/app/doctype",
	"assessments": "/app/assessment-template",
	"consents": "/app/consent-template",
	"website": "/app/rushd-website-settings/Rushd%20Website%20Settings",
	"announcements": "/app/internal-announcement",
	"resources": "/app/resource-content",
	"message-templates": "/app/notification",
	"complaints": "/app/complaint",
	"reports/operations": "/supervisor/reports",
	"reports/impact": "/app/assessment-submission",
	"audit": "/app/version",
	"privacy": "/app/consent-record",
	"integrations": "/app/integrations",
	"settings": "/app/rushd",
	"security": "/app/system-health-report",
}


def get_context(context):
	if not has_admin_app_access():
		frappe.throw("ليس لديك صلاحية للوصول إلى إدارة رُشد", frappe.PermissionError)
	path = (frappe.form_dict.get("admin_path") or "").strip("/")
	frappe.redirect(ROUTES.get(path, "/app/rushd"))
