import frappe

from consultation_center.staff import (
	OPERATIONS_ACCESS,
	build_staff_context,
	get_staff_request_detail,
	get_staff_requests,
)

no_cache = 1

OPERATIONS_STATES = (
	"Submitted",
	"Under Completeness Review",
	"Awaiting Beneficiary Information",
	"Ready for Triage",
)


def get_context(context):
	build_staff_context(
		context,
		"operations-requests",
		"إدارة طلبات الخدمة",
		"operations",
		OPERATIONS_ACCESS,
	)
	context.requests = get_staff_requests(OPERATIONS_STATES)
	selected_name = frappe.form_dict.get("request")
	if not selected_name and context.requests:
		selected_name = context.requests[0].name
	context.selected_request = get_staff_request_detail(selected_name)
	context.action_type = "operations"

