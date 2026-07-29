import frappe
from frappe.utils import nowdate
from consultation_center.portal import require_portal_login

no_cache = 1


def get_context(context):
	user = require_portal_login()
	roles = set(frappe.get_roles(user))
	audiences = ["All"] + [role for role in ("Beneficiary","Guardian","Consultant","Consultation Supervisor","Operations") if role in roles]
	context.title = "مكتبة المحتوى الداخلي"
	context.display_name = frappe.db.get_value("User", user, "full_name") or user
	context.resources = frappe.db.get_all("Resource Content", filters={"active":1,"audience":["in",audiences]}, fields=["title","content_type","summary","content","external_url","attachment"], order_by="modified desc")
	announcements = frappe.db.get_all("Internal Announcement", filters={"active":1,"audience":["in",audiences]}, fields=["title","priority","summary","content","mandatory_read","start_date","end_date"], order_by="priority desc, modified desc")
	today = nowdate()
	context.announcements = [
		row for row in announcements
		if (not row.start_date or str(row.start_date) <= today)
		and (not row.end_date or str(row.end_date) >= today)
	]
