from consultation_center.consultant_portal import (
	build_consultant_context,
	get_consultant_report,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-reports", "تقارير المستشار")
	context.report = (
		get_consultant_report(context.consultant.name)
		if context.consultant
		else {}
	)
