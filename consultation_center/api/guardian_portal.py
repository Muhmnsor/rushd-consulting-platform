import frappe
from frappe.utils import (
	cint,
	getdate,
	now_datetime,
	nowdate,
	strip_html_tags,
	validate_email_address,
	validate_phone_number,
)

from consultation_center.guardian_portal import get_guardian_for_user, require_guardian_login
from consultation_center.permissions import authorized_beneficiaries


@frappe.whitelist(methods=["POST"])
def update_guardian_profile(guardian_name: str, mobile: str, email: str):
	user = require_guardian_login()
	guardian = get_guardian_for_user(user)
	if not guardian:
		frappe.throw("لا يوجد ملف ولي أمر نشط مرتبط بالحساب", frappe.PermissionError)

	guardian_name = strip_html_tags(guardian_name or "").strip()
	mobile = strip_html_tags(mobile or "").strip()
	email = strip_html_tags(email or "").strip()
	if not guardian_name or len(guardian_name) > 140:
		frappe.throw("أدخل اسمًا صحيحًا")
	if mobile and not validate_phone_number(mobile):
		frappe.throw("أدخل رقم جوال صحيحًا")
	if email and not validate_email_address(email):
		frappe.throw("أدخل بريدًا إلكترونيًا صحيحًا")

	doc = frappe.get_doc("Guardian", guardian.name)
	if doc.portal_user != user:
		frappe.throw("لا يمكنك تعديل هذا الملف", frappe.PermissionError)
	doc.guardian_name = guardian_name
	doc.mobile = mobile
	doc.email = email
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "message": "تم تحديث بيانات ولي الأمر"}


@frappe.whitelist(methods=["POST"])
def grant_guardian_consent(consent_record: str, confirmed: int | str = 0):
	user = require_guardian_login()
	guardian = get_guardian_for_user(user)
	if not guardian or not cint(confirmed):
		frappe.throw("يلزم تأكيد قراءة الموافقة", frappe.PermissionError)

	doc = frappe.get_doc("Consent Record", consent_record)
	if doc.guardian != guardian.name or doc.consent_role != "Guardian":
		frappe.throw("لا يمكنك الموافقة على هذا السجل", frappe.PermissionError)
	if doc.beneficiary not in authorized_beneficiaries(user, "can_view_profile"):
		frappe.throw("تفويض الوصول غير نشط", frappe.PermissionError)
	if doc.status != "Pending":
		frappe.throw("سجل الموافقة ليس بانتظار الإجراء")

	version = frappe.db.get_value(
		"Consent Version",
		doc.consent_version,
		["status", "effective_from"],
		as_dict=True,
	)
	if not version or version.status != "Published":
		frappe.throw("نسخة الموافقة غير منشورة")
	if version.effective_from and getdate(version.effective_from) > getdate(nowdate()):
		frappe.throw("نسخة الموافقة لم تدخل حيز التطبيق بعد")

	doc.status = "Granted"
	doc.granted_by = user
	doc.granted_at = now_datetime()
	doc.grant_method = "Web"
	doc.save(ignore_permissions=True)
	frappe.db.set_value(
		"Beneficiary",
		doc.beneficiary,
		"consent_status",
		"Granted",
		update_modified=False,
	)
	return {"name": doc.name, "message": "تم تسجيل موافقتك بنجاح"}
