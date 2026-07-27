import frappe
from frappe.utils import strip_html_tags

no_cache = 1


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

	context.is_logged_in = frappe.session.user != "Guest"
	context.portal_url = _get_portal_url() if context.is_logged_in else "/login"
	context.portal_label = "الذهاب إلى بوابتي" if context.is_logged_in else "تسجيل الدخول"


def _get_portal_url():
	user = frappe.session.user
	if user == "Administrator":
		return "/app/rushd"
	roles = set(frappe.get_roles(user))
	if "Beneficiary" in roles:
		return "/beneficiary"
	if "Guardian" in roles:
		return "/guardian"
	if roles & {"Intake Coordinator", "Operations Officer", "Case Coordinator"}:
		return "/operations"
	if "Consultation Supervisor" in roles:
		return "/supervisor"
	return "/login"

