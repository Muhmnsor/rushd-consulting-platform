import frappe
from consultation_center.portal import build_portal_context

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "feedback", "التقييم والشكاوى")
	context.complaints = frappe.db.get_all("Complaint", filters={"complainant":context.portal_user}, fields=["name","complaint_type","status","priority","submitted_on","public_response"], order_by="submitted_on desc") if beneficiary else []
