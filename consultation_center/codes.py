import frappe


def generate_record_code(doctype: str, fieldname: str, prefix: str) -> str:
	"""Generate a short, readable, collision-safe code for operational records."""
	for _attempt in range(20):
		code = f"{prefix}-{frappe.generate_hash(length=6).upper()}"
		if not frappe.db.exists(doctype, {fieldname: code}):
			return code
	frappe.throw("تعذر إنشاء رمز فريد للسجل؛ أعد المحاولة")
