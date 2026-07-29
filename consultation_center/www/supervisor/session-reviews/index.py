import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_session_review_detail,
	get_session_reviews,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-session-reviews",
		"مراجعة الجلسات",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.sessions = get_session_reviews()
	selected_name = frappe.form_dict.get("session")
	if not selected_name and context.sessions:
		selected_name = context.sessions[0].name
	allowed_names = {row.name for row in context.sessions}
	context.selected_session = (
		get_session_review_detail(selected_name)
		if selected_name in allowed_names
		else None
	)
