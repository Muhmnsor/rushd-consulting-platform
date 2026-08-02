import frappe

ADMIN_PORTAL_ROLES = {"System Manager", "Center Director"}
COMPLETED_SETUP_LEGACY_ROUTES = {
	"/app",
	"/app/",
	"/desk",
	"/desk/",
	"/app/setup-wizard",
	"/desk/setup-wizard",
}


def force_arabic_for_guests():
	"""Keep public Rushd pages Arabic regardless of the browser language header."""
	if frappe.session.user == "Guest":
		frappe.local.lang = "ar"
		return

	request = getattr(frappe.local, "request", None)
	path = getattr(request, "path", "")
	if should_redirect_completed_admin_setup(
		user=frappe.session.user,
		roles=set(frappe.get_roles(frappe.session.user)),
		path=path,
		setup_complete=frappe.is_setup_complete(),
	):
		frappe.redirect("/admin")


def should_redirect_completed_admin_setup(
	user: str,
	roles: set[str],
	path: str,
	setup_complete: bool,
) -> bool:
	"""Send completed administrator setup routes to the simplified Rushd portal."""
	return bool(
		setup_complete
		and path in COMPLETED_SETUP_LEGACY_ROUTES
		and (user == "Administrator" or roles & ADMIN_PORTAL_ROLES)
	)
