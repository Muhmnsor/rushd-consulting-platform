import frappe
from frappe.translate import set_default_language

from consultation_center.website import (
	ensure_rushd_website_settings,
	remove_legacy_settings_from_website_workspace,
)

RUSHD_ARABIC_NAME = "رُشد"
RUSHD_APP_NAME = RUSHD_ARABIC_NAME
RUSHD_LOGO_URL = "/assets/consultation_center/images/rushd-logo.svg"
RUSHD_BRAND_HTML = (
	f'<span class="rushd-brand-wordmark"><img class="rushd-brand-symbol" src="{RUSHD_LOGO_URL}" alt="">'
	f"<span>{RUSHD_ARABIC_NAME}</span></span>"
)

ADMIN_ROLES = [
	"Center Director",
]

STAFF_ROLES = [
	"Consultation Supervisor",
	"Consultant",
	"Case Coordinator",
	"Intake Coordinator",
	"Operations Officer",
	"Assessment Manager",
	"Quality Reviewer",
	"Auditor",
	"Content Manager",
]

PORTAL_ROLES = [
	"Beneficiary",
	"Guardian",
]


def create_roles():
	for role_name in ADMIN_ROLES:
		_create_role(role_name, desk_access=1)

	for role_name in STAFF_ROLES + PORTAL_ROLES:
		_create_role(role_name, desk_access=0)


def _create_role(role_name, desk_access):
	if frappe.db.exists("Role", role_name):
		frappe.db.set_value(
			"Role",
			role_name,
			"desk_access",
			desk_access,
			update_modified=False,
		)
		return
	role = frappe.new_doc("Role")
	role.role_name = role_name
	role.desk_access = desk_access
	role.insert(ignore_permissions=True)


def after_install():
	create_roles()
	configure_site_identity()
	ensure_rushd_website_settings()
	remove_legacy_settings_from_website_workspace()


def after_migrate():
	"""Keep required roles and the Arabic-first identity after a migration."""
	create_roles()
	configure_site_identity()
	ensure_rushd_website_settings()
	remove_legacy_settings_from_website_workspace()


def configure_site_identity():
	"""Apply Rushd branding and make Arabic/RTL the site-wide default."""
	system_settings = {
		"app_name": RUSHD_APP_NAME,
		"language": "ar",
	}
	website_settings = {
		"app_name": RUSHD_APP_NAME,
		"title_prefix": RUSHD_APP_NAME,
		"brand_html": RUSHD_BRAND_HTML,
		"footer_powered": RUSHD_ARABIC_NAME,
		"favicon": RUSHD_LOGO_URL,
		"splash_image": RUSHD_LOGO_URL,
		"home_page": "index",
		"disable_signup": 0,
		"show_footer_on_login": 0,
	}

	for fieldname, value in system_settings.items():
		frappe.db.set_single_value(
			"System Settings",
			fieldname,
			value,
			update_modified=False,
		)

	for fieldname, value in website_settings.items():
		frappe.db.set_single_value(
			"Website Settings",
			fieldname,
			value,
			update_modified=False,
		)

	set_default_language("ar")

	for user in ("Administrator", "Guest"):
		if frappe.db.exists("User", user):
			frappe.db.set_value(
				"User",
				user,
				"language",
				"ar",
				update_modified=False,
			)

	if frappe.db.exists("Workspace", "Rushd"):
		frappe.db.set_value(
			"Workspace",
			"Rushd",
			{
				"label": "Rushd",
				"title": "Rushd",
			},
			update_modified=False,
		)

	frappe.clear_cache()
