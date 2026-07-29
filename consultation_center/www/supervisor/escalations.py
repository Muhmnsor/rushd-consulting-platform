import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_escalation_queue,
)

no_cache = 1


def get_context(context):
	build_staff_context(context, "supervisor-escalations", "التصعيدات المهنية", "supervisor", SUPERVISOR_ACCESS)
	context.escalations = get_escalation_queue(context.staff_user)
	selected = frappe.form_dict.get("escalation")
	context.selected_escalation = (
		next((row for row in context.escalations if row.name == selected), None)
		if selected
		else None
	)
