import frappe
from frappe.utils import strip_html_tags

from consultation_center.portal import get_beneficiary_for_user, require_portal_login


@frappe.whitelist(methods=["POST"])
def create_support_ticket(category: str, subject: str, description: str, priority: str = "Normal"):
	user = require_portal_login()
	if category not in {"Access Issue", "Appointment", "Data Update", "Account Closure", "Callback", "Other"}:
		frappe.throw("تصنيف الدعم غير صالح")
	beneficiary = get_beneficiary_for_user(user)
	doc = frappe.get_doc({"doctype":"Support Ticket","requester":user,"beneficiary":beneficiary.name if beneficiary else None,"category":category,"subject":_clean(subject,180),"description":_clean(description,5000),"priority":priority,"status":"New"})
	doc.insert(ignore_permissions=True)
	return {"name":doc.name,"message":"تم استلام طلب الدعم"}


@frappe.whitelist(methods=["POST"])
def create_complaint(complaint_type: str, details: str, priority: str = "Normal", confidentiality: str = "Confidential"):
	user = require_portal_login()
	if complaint_type not in {"Service Feedback", "Confidential Complaint", "Suggestion", "Change Consultant"}:
		frappe.throw("نوع البلاغ غير صالح")
	beneficiary = get_beneficiary_for_user(user)
	doc = frappe.get_doc({"doctype":"Complaint","complainant":user,"beneficiary":beneficiary.name if beneficiary else None,"complaint_type":complaint_type,"details":_clean(details,5000),"priority":priority,"confidentiality":confidentiality,"status":"Submitted"})
	doc.insert(ignore_permissions=True)
	return {"name":doc.name,"message":"تم استلام البلاغ بسرية"}


def _clean(value, limit):
	value = strip_html_tags(value or "").strip()
	if not value:
		frappe.throw("أكمل الحقل المطلوب")
	if len(value) > limit:
		frappe.throw("النص أطول من الحد المسموح")
	return value
