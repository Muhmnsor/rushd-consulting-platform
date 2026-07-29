import frappe
from frappe.utils import get_datetime

from consultation_center.consultant_portal import (
	build_consultant_context,
	get_session_documentation_context,
)

no_cache = 1


def get_context(context):
	build_consultant_context(
		context,
		"consultant-sessions",
		"توثيق الجلسة",
	)
	context.documentation = (
		get_session_documentation_context(
			context.consultant.name,
			frappe.form_dict.get("appointment"),
			frappe.form_dict.get("session"),
		)
		if context.consultant
		else None
	)
	if not context.documentation:
		return

	session = context.documentation["session"]
	appointment = context.documentation["appointment"]
	start = session.actual_start if session and session.actual_start else appointment.start_datetime
	end = session.actual_end if session and session.actual_end else appointment.end_datetime
	context.actual_start_value = (
		get_datetime(start).strftime("%Y-%m-%dT%H:%M") if start else ""
	)
	context.actual_end_value = (
		get_datetime(end).strftime("%Y-%m-%dT%H:%M") if end else ""
	)
