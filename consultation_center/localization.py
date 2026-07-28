import frappe


def force_arabic_for_guests():
	"""Keep public Rushd pages Arabic regardless of the browser language header."""
	if frappe.session.user == "Guest":
		frappe.local.lang = "ar"
