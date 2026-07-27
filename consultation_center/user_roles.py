import frappe


def ensure_user_role(user_name: str | None, role: str) -> None:
	"""Attach a Rushd role when a domain profile is linked to a user."""
	if not user_name or user_name in {"Administrator", "Guest"}:
		return

	user = frappe.get_doc("User", user_name)
	if role in {row.role for row in user.roles}:
		return

	user.flags.ignore_permissions = True
	user.add_roles(role)
