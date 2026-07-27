from urllib.parse import urlencode

import frappe
from frappe.utils import format_date, format_time, get_datetime, now_datetime


REQUEST_STATUS = {
	"Draft": {
		"label": "مسودة",
		"tone": "neutral",
		"next_step": "أكمل بيانات الطلب ثم أرسله إلى فريق الاستقبال.",
	},
	"Submitted": {
		"label": "تم استلام الطلب",
		"tone": "blue",
		"next_step": "سيبدأ فريق الاستقبال مراجعة اكتمال البيانات.",
	},
	"Under Completeness Review": {
		"label": "تحت مراجعة الاكتمال",
		"tone": "blue",
		"next_step": "لا يلزمك إجراء حاليًا، وسنبلغك إذا احتجنا معلومات إضافية.",
	},
	"Awaiting Beneficiary Information": {
		"label": "بانتظار استكمال البيانات",
		"tone": "gold",
		"next_step": "راجع الطلب وأكمل المعلومات التي طلبها فريق الاستقبال.",
	},
	"Eligible": {
		"label": "مؤهل للخدمة",
		"tone": "green",
		"next_step": "سيتم استكمال الموافقات ثم تجهيز الطلب للإسناد.",
	},
	"Not Eligible": {
		"label": "الخدمة غير مناسبة",
		"tone": "red",
		"next_step": "راجع التوضيح العام أو تواصل مع فريق الدعم لمعرفة البدائل.",
	},
	"Awaiting Consent": {
		"label": "بانتظار الموافقة",
		"tone": "gold",
		"next_step": "أكمل الموافقة المطلوبة للانتقال إلى الإسناد.",
	},
	"Ready for Assignment": {
		"label": "جاهز للإسناد",
		"tone": "green",
		"next_step": "يعمل الفريق على اختيار المستشار الأنسب والتواصل معك.",
	},
	"Converted to Case": {
		"label": "تحول إلى حالة نشطة",
		"tone": "green",
		"next_step": "يمكنك متابعة الموعد والخطوات القادمة من لوحة المستفيد.",
	},
	"Cancelled": {
		"label": "ملغي",
		"tone": "neutral",
		"next_step": "يمكنك تقديم طلب جديد عندما تحتاج إلى الخدمة.",
	},
}


def require_portal_login() -> str:
	user = frappe.session.user
	if user == "Guest":
		redirect_to = frappe.request.path if frappe.request else "/beneficiary"
		frappe.redirect(f"/login?{urlencode({'redirect-to': redirect_to})}")
	return user


def get_beneficiary_for_user(user: str | None = None):
	user = user or require_portal_login()
	return frappe.db.get_value(
		"Beneficiary",
		{"portal_user": user, "status": "Active"},
		[
			"name",
			"beneficiary_name",
			"mobile",
			"email",
			"city",
			"date_of_birth",
			"consent_status",
			"guardian_required",
		],
		as_dict=True,
	)


def build_portal_context(context, active_nav: str, title: str):
	user = require_portal_login()
	beneficiary = get_beneficiary_for_user(user)
	display_name = (
		beneficiary.beneficiary_name
		if beneficiary
		else frappe.db.get_value("User", user, "full_name") or user
	)

	context.update(
		{
			"title": title,
			"no_cache": 1,
			"body_class": "rushd-portal-page",
			"active_nav": active_nav,
			"portal_user": user,
			"display_name": display_name,
			"beneficiary": beneficiary,
		}
	)
	return beneficiary


def get_beneficiary_requests(beneficiary: str, limit: int | None = None):
	rows = frappe.db.get_all(
		"Consultation Request",
		filters={"beneficiary": beneficiary},
		fields=[
			"name",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"preferred_mode",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)
	for row in rows:
		row.service_name = (
			frappe.db.get_value("Consultation Service", row.requested_service, "service_name")
			or row.requested_service
		)
		status = REQUEST_STATUS.get(row.workflow_state, REQUEST_STATUS["Submitted"])
		row.status_label = status["label"]
		row.status_tone = status["tone"]
		row.next_step = status["next_step"]
		row.request_date_label = format_date(row.request_datetime) if row.request_datetime else "—"
	return rows


def get_next_appointment(beneficiary: str):
	row = frappe.db.get_value(
		"Consultation Appointment",
		{
			"beneficiary": beneficiary,
			"status": ["in", ["Pending Approval", "Confirmed", "Rescheduled"]],
			"start_datetime": [">=", now_datetime()],
		},
		["name", "start_datetime", "delivery_mode", "service", "status"],
		order_by="start_datetime asc",
		as_dict=True,
	)
	if not row:
		return None

	start = get_datetime(row.start_datetime)
	row.date_label = format_date(start)
	row.time_label = format_time(start, format="HH:mm")
	row.service_name = frappe.db.get_value("Consultation Service", row.service, "service_name")
	row.delivery_label = "عن بُعد" if row.delivery_mode == "Online" else "حضوري"
	return row


def calculate_profile_completion(beneficiary) -> int:
	if not beneficiary:
		return 0
	fields = ("beneficiary_name", "mobile", "email", "city", "date_of_birth")
	completed = sum(bool(beneficiary.get(field)) for field in fields)
	return round((completed / len(fields)) * 100)

