import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_supervision_request_queue,
)

no_cache = 1


def get_context(context):
	build_staff_context(context, "supervisor-requests", "طلبات الإشراف", "supervisor", SUPERVISOR_ACCESS)
	context.requests = get_supervision_request_queue(context.staff_user)
	selected = frappe.form_dict.get("request")
	context.selected_request = (
		next((row for row in context.requests if row.name == selected), None)
		if selected
		else None
	)
