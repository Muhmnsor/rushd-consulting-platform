import frappe
from frappe.utils import strip_html_tags

no_cache = 1

REQUEST_PATH = "/beneficiary/requests/new"
ADMIN_PORTAL_ROLES = {"System Manager", "Center Director"}
OPERATIONS_PORTAL_ROLES = {"Intake Coordinator", "Operations Officer", "Case Coordinator"}


def get_context(context):
	context.title = "رُشد للاستشارات الشبابية"
	context.no_cache = 1
	context.body_class = "rushd-public-page"
	context.services = frappe.db.get_all(
		"Consultation Service",
		filters={"active": 1},
		fields=["name", "service_name", "category", "description", "delivery_modes", "duration_minutes"],
		order_by="service_name asc",
		limit=6,
	)
	for service in context.services:
		description = strip_html_tags(service.description or "").strip()
		service.description_text = (
			description[:180]
			if description
			else "خدمة استشارية مهنية تقدم ضمن رحلة واضحة تحافظ على خصوصيتك."
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
	if roles & OPERATIONS_PORTAL_ROLES:
		return "/operations"
	if "Beneficiary" in roles:
		return "/beneficiary"
	if "Guardian" in roles:
		return "/guardian"
	return "/"
