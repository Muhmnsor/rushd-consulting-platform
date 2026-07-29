from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_sessions,
	get_session_documentation_queue,
)

no_cache = 1


def get_context(context):
	build_consultant_context(
		context,
		"consultant-sessions",
		"سجل الجلسات",
	)
	if not context.consultant:
		context.sessions = []
		context.documentation_queue = []
		return
	context.sessions = get_consultant_sessions(context.consultant.name)
	context.documentation_queue = get_session_documentation_queue(context.consultant.name)
