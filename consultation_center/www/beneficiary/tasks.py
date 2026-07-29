from consultation_center.portal import build_portal_context, get_beneficiary_tasks

no_cache = 1


def get_context(context):
	beneficiary = build_portal_context(context, "tasks", "مهامي")
	context.tasks = get_beneficiary_tasks(beneficiary.name) if beneficiary else []
