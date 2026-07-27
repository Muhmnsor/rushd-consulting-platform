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

