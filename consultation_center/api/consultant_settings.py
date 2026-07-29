import frappe
from frappe.utils import cint, flt, get_datetime, strip_html_tags

from consultation_center.consultant_portal import get_current_consultant


@frappe.whitelist(methods=["POST"])
def save_professional_profile(
	specializations: str | None = None,
	languages: str | None = None,
	qualifications: str | None = None,
	experience_summary: str | None = None,
	licenses: str | None = None,
	suitable_groups: str | None = None,
	credential_expiry: str | None = None,
	development_requirements: str | None = None,
	events_platform_url: str | None = None,
):
	consultant = _require_consultant()
	doc = frappe.get_doc("Consultant", consultant.name)
	doc.specializations = _clean(specializations, 2000)
	doc.languages = _clean(languages, 1000)
	doc.qualifications = _clean(qualifications, 5000)
	doc.experience_summary = _clean(experience_summary, 5000)
	doc.licenses = _clean(licenses, 2000)
	doc.suitable_groups = _clean(suitable_groups, 2000)
	doc.credential_expiry = credential_expiry or None
	doc.development_requirements = _clean(development_requirements, 5000)
	doc.events_platform_url = _clean(events_platform_url, 500)
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "message": "تم حفظ الملف المهني"}


@frappe.whitelist(methods=["POST"])
def save_availability_rule(
	weekday: str,
	start_time: str,
	end_time: str,
	rule_name: str | None = None,
	slot_duration: int | str = 60,
	delivery_mode: str = "Both",
	capacity: int | str = 1,
	service: str | None = None,
	branch: str | None = None,
	effective_from: str | None = None,
	effective_to: str | None = None,
	active: int | str = 1,
):
	consultant = _require_consultant()
	if weekday not in {
		"Monday",
		"Tuesday",
		"Wednesday",
		"Thursday",
		"Friday",
		"Saturday",
		"Sunday",
	}:
		frappe.throw("اليوم غير صالح")
	if delivery_mode not in {"Online", "In Person", "Both"}:
		frappe.throw("طريقة التقديم غير صالحة")
	if not start_time or not end_time or str(start_time) >= str(end_time):
		frappe.throw("وقت النهاية يجب أن يكون بعد وقت البداية")
	if cint(slot_duration) < 15 or cint(slot_duration) > 240:
		frappe.throw("مدة الموعد يجب أن تكون بين 15 و240 دقيقة")
	if cint(capacity) < 1:
		frappe.throw("السعة يجب أن تكون جلسة واحدة على الأقل")
	if rule_name:
		doc = frappe.get_doc("Consultant Availability Rule", rule_name)
		if doc.consultant != consultant.name:
			frappe.throw("قاعدة التوفر خارج نطاقك", frappe.PermissionError)
	else:
		doc = frappe.new_doc("Consultant Availability Rule")
		doc.consultant = consultant.name
	doc.update(
		{
			"weekday": weekday,
			"start_time": start_time,
			"end_time": end_time,
			"slot_duration": cint(slot_duration),
			"delivery_mode": delivery_mode,
			"capacity": cint(capacity),
			"service": service or None,
			"branch": _clean(branch, 180),
			"effective_from": effective_from or None,
			"effective_to": effective_to or None,
			"active": cint(active),
		}
	)
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "message": "تم حفظ قاعدة التوفر"}


@frappe.whitelist(methods=["POST"])
def add_time_off(from_datetime: str, to_datetime: str, reason: str | None = None):
	consultant = _require_consultant()
	start = get_datetime(from_datetime)
	end = get_datetime(to_datetime)
	if end <= start:
		frappe.throw("نهاية فترة عدم التوفر يجب أن تكون بعد بدايتها")
	doc = frappe.get_doc(
		{
			"doctype": "Consultant Time Off",
			"consultant": consultant.name,
			"from_datetime": start,
			"to_datetime": end,
			"reason": _clean(reason, 1000),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "message": "تمت إضافة فترة عدم التوفر"}


@frappe.whitelist(methods=["POST"])
def update_capacity(
	maximum_daily_sessions: int | str,
	default_duration: int | str,
	buffer_before: int | str = 0,
	buffer_after: int | str = 0,
):
	consultant = _require_consultant()
	maximum = cint(maximum_daily_sessions)
	duration = cint(default_duration)
	if maximum < 1 or maximum > 20:
		frappe.throw("الحد اليومي يجب أن يكون بين جلسة واحدة و20 جلسة")
	if duration < 15 or duration > 240:
		frappe.throw("مدة الجلسة يجب أن تكون بين 15 و240 دقيقة")
	doc = frappe.get_doc("Consultant", consultant.name)
	doc.maximum_daily_sessions = maximum
	doc.default_duration = duration
	doc.buffer_before = max(0, cint(buffer_before))
	doc.buffer_after = max(0, cint(buffer_after))
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "message": "تم تحديث الطاقة الاستيعابية"}


def _require_consultant():
	consultant = get_current_consultant()
	if not consultant:
		frappe.throw("لا يوجد ملف مستشار نشط مرتبط بالحساب", frappe.PermissionError)
	return consultant


def _clean(value: str | None, limit: int) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > limit:
		frappe.throw("النص أطول من الحد المسموح")
	return value
