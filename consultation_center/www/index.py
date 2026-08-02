import re
from urllib.parse import urlencode

import frappe
from frappe.utils import cint, strip_html_tags

from consultation_center.website import get_rushd_website_settings

no_cache = 1

REQUEST_PATH = "/beneficiary/requests/new"
ADMIN_PORTAL_ROLES = {"System Manager", "Center Director"}
OPERATIONS_PORTAL_ROLES = {"Intake Coordinator", "Operations Officer", "Case Coordinator"}


def get_context(context):
	context.website = get_rushd_website_settings()
	context.title = context.website.page_title
	context.description = context.website.meta_description
	context.no_cache = 1
	context.body_class = "rushd-public-page"
	services_limit = max(1, min(cint(context.website.services_limit), 12))
	context.services = frappe.db.get_all(
		"Consultation Service",
		filters={"active": 1},
		fields=["name", "service_name", "category", "description", "delivery_modes", "duration_minutes"],
		order_by="service_name asc",
		limit=services_limit,
	)
	for service in context.services:
		description = strip_html_tags(service.description or "").strip()
		service.description_text = (
			description[:180]
			if description
			else context.website.service_card_fallback
		)
		service.mode_label = {
			"Online": "عن بُعد",
			"In Person": "حضوري",
			"Both": "حضوري أو عن بُعد",
		}.get(service.delivery_modes, "حسب الخدمة")

	user = frappe.session.user
	roles = set() if user == "Guest" else set(frappe.get_roles(user))
	context.is_logged_in = user != "Guest"
	context.portal_url = _get_portal_url(user, roles) if context.is_logged_in else "/login"
	context.portal_label = "الذهاب إلى بوابتي" if context.is_logged_in else "تسجيل الدخول"
	context.can_request_consultation = (
		not context.is_logged_in or context.portal_url == "/beneficiary"
	)
	context.request_url = (
		REQUEST_PATH
		if context.is_logged_in
		else f"/login?redirect-to={REQUEST_PATH}"
	)
	context.header_action_url = context.portal_url if context.is_logged_in else context.request_url
	context.header_action_label = "حسابي" if context.is_logged_in else "اطلب استشارة"
	context.primary_action_url = (
		context.request_url if context.can_request_consultation else context.portal_url
	)
	context.primary_action_label = (
		"ابدأ طلب الاستشارة"
		if context.can_request_consultation
		else "الذهاب إلى بوابتي"
	)
	for service in context.services:
		service.request_url = (
			_get_service_request_url(service.name, context.is_logged_in)
			if context.can_request_consultation
			else context.portal_url
		)
		service.request_label = "اطلب الخدمة الآن"

	consultants_limit = max(1, min(cint(context.website.consultants_limit), 12))
	context.consultants = _get_public_consultants(consultants_limit)
	testimonials_limit = max(1, min(cint(context.website.testimonials_limit), 12))
	context.testimonials = _get_public_testimonials(testimonials_limit)


def _get_portal_url(user: str, roles: set[str]):
	if user == "Administrator":
		return "/admin"
	if roles & ADMIN_PORTAL_ROLES:
		return "/admin"
	if "Consultation Supervisor" in roles:
		return "/supervisor"
	if "Consultant" in roles:
		return "/consultant"
	if roles & OPERATIONS_PORTAL_ROLES:
		return "/operations"
	if "Beneficiary" in roles:
		return "/beneficiary"
	if "Guardian" in roles:
		return "/guardian"
	return "/"


def _get_service_request_url(service_name: str, is_logged_in: bool):
	destination = f"{REQUEST_PATH}?{urlencode({'service': service_name})}"
	if is_logged_in:
		return destination
	return f"/login?{urlencode({'redirect-to': destination})}"


def _get_public_consultants(limit: int):
	rows = frappe.db.get_all(
		"Consultant",
		filters={"active": 1, "show_on_website": 1},
		fields=[
			"name",
			"consultant_name",
			"user",
			"specializations",
			"public_title",
			"public_bio",
			"profile_image",
		],
		order_by="consultant_name asc",
		limit=max(1, min(cint(limit), 12)),
	)
	result = []
	for row in rows:
		title = strip_html_tags(row.public_title or "").strip()
		bio = strip_html_tags(row.public_bio or "").strip()
		if not title or not bio:
			continue
		image = row.profile_image or frappe.db.get_value("User", row.user, "user_image")
		row.profile_image_url = (
			image
			if image and (image.startswith("/files/") or image.startswith("/assets/"))
			else None
		)
		row.public_title = title[:140]
		row.public_bio = bio[:320]
		row.initials = "".join(
			part[0] for part in row.consultant_name.split()[:2] if part
		) or "ر"
		row.specialty_tags = [
			item.strip()
			for item in re.split(r"[,،\n]+", row.specializations or "")
			if item.strip()
		][:3]
		result.append(row)
	return result


def _get_public_testimonials(limit: int):
	rows = frappe.db.get_all(
		"Rushd Testimonial",
		filters={"active": 1, "consent_confirmed": 1},
		fields=["name", "quote", "display_name", "service_label"],
		order_by="sort_order asc, creation desc",
		limit=max(1, min(cint(limit), 12)),
	)
	result = []
	for row in rows:
		quote = strip_html_tags(row.quote or "").strip()
		if not quote:
			continue
		row.quote = quote[:600]
		row.display_name = strip_html_tags(row.display_name or "").strip()[:100] or "مستفيد من رُشد"
		row.service_label = strip_html_tags(row.service_label or "").strip()[:140]
		row.initial = row.display_name[0] if row.display_name else "ر"
		result.append(row)
	return result
