from urllib.parse import urlencode

import frappe
import frappe.sessions
from frappe.utils import format_date, getdate, nowdate, strip_html_tags

RELATIONSHIP_LABELS = {
	"Father": "الأب",
	"Mother": "الأم",
	"Legal Guardian": "ولي أمر قانوني",
	"Authorized Representative": "ممثل مفوض",
	"Other": "صلة أخرى",
}

AUTHORIZATION_LABELS = {
	"Pending": ("بانتظار المراجعة", "gold"),
	"Active": ("نشط", "green"),
	"Revoked": ("ملغي", "neutral"),
	"Expired": ("منتهي", "neutral"),
}


def require_guardian_login() -> str:
	user = frappe.session.user
	if user == "Guest":
		redirect_to = frappe.request.path if frappe.request else "/guardian"
		frappe.redirect(f"/login?{urlencode({'redirect-to': redirect_to})}")
	return user


def get_guardian_for_user(user: str | None = None):
	user = user or require_guardian_login()
	return frappe.db.get_value(
		"Guardian",
		{"portal_user": user, "status": "Active"},
		["name", "guardian_name", "mobile", "email"],
		as_dict=True,
	)


def build_guardian_context(context, active_nav: str, title: str):
	user = require_guardian_login()
	frappe.sessions.get_csrf_token()
	frappe.db.commit()
	guardian = get_guardian_for_user(user)
	display_name = (
		guardian.guardian_name
		if guardian
		else frappe.db.get_value("User", user, "full_name") or user
	)
	context.update(
		{
			"title": title,
			"no_cache": 1,
			"body_class": "rushd-portal-page rushd-guardian-page",
			"active_nav": active_nav,
			"portal_user": user,
			"display_name": display_name,
			"guardian": guardian,
		}
	)
	return guardian


def get_guardian_authorizations(guardian: str):
	rows = frappe.db.get_all(
		"Guardian Authorization",
		filters={"guardian": guardian},
		fields=[
			"name",
			"beneficiary",
			"relationship",
			"authorization_status",
			"effective_from",
			"effective_to",
			"can_view_profile",
			"can_view_requests",
			"can_view_case",
			"can_manage_appointments",
			"can_view_reports",
		],
		order_by="modified desc",
	)
	for row in rows:
		if (
			row.authorization_status == "Active"
			and row.effective_to
			and getdate(row.effective_to) < getdate(nowdate())
		):
			row.authorization_status = "Expired"

		row.beneficiary_profile = frappe.db.get_value(
			"Beneficiary",
			row.beneficiary,
			["beneficiary_name", "city", "status", "consent_status"],
			as_dict=True,
		)
		row.relationship_label = RELATIONSHIP_LABELS.get(row.relationship, row.relationship)
		row.status_label, row.status_tone = AUTHORIZATION_LABELS.get(
			row.authorization_status,
			(row.authorization_status, "neutral"),
		)
		row.effective_from_label = format_date(row.effective_from) if row.effective_from else "—"
		row.effective_to_label = format_date(row.effective_to) if row.effective_to else "مفتوح"
		row.scope_labels = _scope_labels(row)
		row.request_count = (
			frappe.db.count("Consultation Request", {"beneficiary": row.beneficiary})
			if row.can_view_requests and row.authorization_status == "Active"
			else 0
		)
	return rows


def get_guardian_consents(guardian: str):
	rows = frappe.db.get_all(
		"Consent Record",
		filters={"guardian": guardian, "consent_role": "Guardian"},
		fields=[
			"name",
			"consent_template",
			"consent_version",
			"beneficiary",
			"status",
			"granted_at",
		],
		order_by="modified desc",
	)
	for row in rows:
		row.template_title = frappe.db.get_value(
			"Consent Template",
			row.consent_template,
			"template_title",
		)
		version = frappe.db.get_value(
			"Consent Version",
			row.consent_version,
			["version_label", "title", "simplified_text", "full_text", "effective_from", "status"],
			as_dict=True,
		)
		row.version_label = version.version_label if version else "—"
		row.version_status = version.status if version else None
		row.title = version.title if version else row.template_title
		row.simplified_text = strip_html_tags(version.simplified_text or "") if version else ""
		row.full_text = strip_html_tags(version.full_text or "") if version else ""
		row.beneficiary_name = frappe.db.get_value(
			"Beneficiary",
			row.beneficiary,
			"beneficiary_name",
		)
		row.granted_at_label = format_date(row.granted_at) if row.granted_at else None
		row.status_label = {
			"Pending": "بانتظار الموافقة",
			"Granted": "تمت الموافقة",
			"Withdrawn": "مسحوبة",
			"Expired": "منتهية",
		}.get(row.status, row.status)
		row.status_tone = {
			"Pending": "gold",
			"Granted": "green",
			"Withdrawn": "neutral",
			"Expired": "neutral",
		}.get(row.status, "neutral")
	return rows


def _scope_labels(authorization) -> list[str]:
	labels = []
	if authorization.can_view_profile:
		labels.append("البيانات العامة")
	if authorization.can_view_requests:
		labels.append("الطلبات")
	if authorization.can_view_case:
		labels.append("حالة الخدمة")
	if authorization.can_manage_appointments:
		labels.append("المواعيد")
	if authorization.can_view_reports:
		labels.append("الملخصات المعتمدة")
	return labels
