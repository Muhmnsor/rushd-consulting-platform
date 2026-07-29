from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_cases,
	get_consultant_supervision_requests,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-supervision", "طلبات الإشراف")
	if not context.consultant:
		context.cases = []
		context.requests = []
		return
	context.cases = get_consultant_cases(context.consultant.name)
	context.requests = get_consultant_supervision_requests(context.consultant.name)
