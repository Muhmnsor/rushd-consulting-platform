import frappe
from consultation_center.portal import get_beneficiary_for_user, require_portal_login

no_cache = 1


def get_context(context):
	user = require_portal_login()
	context.title = "مركز الرسائل والدعم"
	context.display_name = frappe.db.get_value("User", user, "full_name") or user
	context.tickets = frappe.db.get_all("Support Ticket", filters={"requester":user}, fields=["name","subject","category","status","priority","public_response","opened_on"], order_by="opened_on desc")
	context.beneficiary = get_beneficiary_for_user(user)
