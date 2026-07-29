import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_active_consultants,
	get_assignment_requests,
	get_staff_request_detail,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-assignments",
		"توزيع الحالات",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.requests = get_assignment_requests()
	selected_name = frappe.form_dict.get("request")
	if not selected_name and context.requests:
		selected_name = context.requests[0].name

	allowed_names = {row.name for row in context.requests}
	context.selected_request = (
		get_staff_request_detail(selected_name)
		if selected_name in allowed_names
		else None
	)
	context.consultants = get_active_consultants(
		context.selected_request.requested_service
		if context.selected_request
		else None
	)
	context.priority_labels = {
		"Low": "منخفضة",
		"Normal": "عادية",
		"High": "عالية",
		"Urgent": "عاجلة",
	}
