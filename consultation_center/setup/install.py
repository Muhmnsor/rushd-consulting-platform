import frappe
from frappe.translate import set_default_language

RUSHD_APP_NAME = "Rushd"
RUSHD_ARABIC_NAME = "رُشد"
RUSHD_BRAND_HTML = f'<span class="rushd-brand-wordmark">{RUSHD_ARABIC_NAME}</span>'

DESK_ROLES = [
	"Center Director",
	"Consultation Supervisor",
	"Consultant",
	"Case Coordinator",
	"Assessment Manager",
	"Quality Reviewer",
	"Auditor",
]

PORTAL_ROLES = [
	"Beneficiary",
	"Guardian",
]


def create_roles():
	for role_name in DESK_ROLES:
		_create_role(role_name, desk_access=1)

	for role_name in PORTAL_ROLES:
		_create_role(role_name, desk_access=0)


def _create_role(role_name, desk_access):
	if frappe.db.exists("Role", role_name):
		return
	role = frappe.new_doc("Role")
	role.role_name = role_name
	role.desk_access = desk_access
	role.insert(ignore_permissions=True)


def after_install():
	create_roles()
	configure_site_identity()


def after_migrate():
	"""Keep required roles and the Arabic-first identity after a migration."""
	create_roles()
	configure_site_identity()


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
		"favicon": "/assets/consultation_center/images/rushd-favicon.svg",
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

	frappe.clear_cache()
