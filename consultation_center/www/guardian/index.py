from consultation_center.guardian_portal import (
	build_guardian_context,
	get_guardian_authorizations,
	get_guardian_consents,
)

no_cache = 1


def get_context(context):
	guardian = build_guardian_context(context, "guardian-dashboard", "لوحة ولي الأمر")
	context.authorizations = get_guardian_authorizations(guardian.name) if guardian else []
	context.consents = get_guardian_consents(guardian.name) if guardian else []
	context.active_authorizations = [
		row for row in context.authorizations if row.authorization_status == "Active"
	]
	context.pending_consents = [row for row in context.consents if row.status == "Pending"]
	context.total_requests = sum(row.request_count for row in context.active_authorizations)

