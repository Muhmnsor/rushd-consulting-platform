import frappe
from consultation_center.portal import build_portal_context

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "documents", "ملفاتي")
	context.documents = frappe.db.get_all("Case Document", filters={"beneficiary":beneficiary.name,"active":1,"visibility":["in",["Beneficiary","Beneficiary and Guardian"]]}, fields=["name","title","document_type","file","description","uploaded_on"], order_by="uploaded_on desc") if beneficiary else []
