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


def _get_portal_url(user: str, roles: set[str]):
	if user == "Administrator":
		return "/app/rushd"
	if roles & ADMIN_PORTAL_ROLES:
		return "/app/rushd"
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
