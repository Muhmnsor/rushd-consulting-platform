import frappe

from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_schedule,
)

no_cache = 1


def get_context(context):
	build_consultant_context(
		context,
		"consultant-calendar",
		"جدول المواعيد",
	)
	context.view = frappe.form_dict.get("view") or "upcoming"
	if context.view not in {"upcoming", "past"}:
		context.view = "upcoming"
	context.appointments = (
		get_consultant_schedule(context.consultant.name, context.view)
		if context.consultant
		else []
	)
