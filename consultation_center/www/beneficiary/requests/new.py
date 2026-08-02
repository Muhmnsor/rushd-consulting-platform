import frappe

from consultation_center.portal import build_portal_context

no_cache = 1


def get_context(context):
	build_portal_context(context, "requests", "طلب استشارة جديد")
	context.services = frappe.db.get_all(
		"Consultation Service",
		filters={"active": 1},
		fields=["name", "service_name", "description", "delivery_modes"],
		order_by="service_name asc",
	)
	requested_service = frappe.form_dict.get("service")
	context.selected_service = (
		requested_service
		if requested_service and any(service.name == requested_service for service in context.services)
		else None
	)
