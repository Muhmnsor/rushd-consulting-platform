import frappe

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


def after_migrate():
	"""Keep required roles present after restoring or migrating a site."""
	create_roles()
