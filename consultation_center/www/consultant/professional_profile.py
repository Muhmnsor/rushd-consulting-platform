from consultation_center.consultant_portal import build_consultant_context

no_cache = 1


def get_context(context):
	build_consultant_context(
		context,
		"consultant-professional-profile",
		"الملف المهني",
	)
