from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_cases,
	get_consultant_escalations,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-alerts", "التنبيهات المهنية")
	if not context.consultant:
		context.cases = []
		context.escalations = []
		return
	context.cases = get_consultant_cases(context.consultant.name)
	context.escalations = get_consultant_escalations(context.consultant.name)
