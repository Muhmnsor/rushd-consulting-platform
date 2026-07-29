from frappe.utils import date_diff, getdate, nowdate

from consultation_center.consultant_portal import build_consultant_context

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-development", "التطوير المهني")
	context.credential_days = (
		date_diff(getdate(context.consultant.credential_expiry), getdate(nowdate()))
		if context.consultant and context.consultant.credential_expiry
		else None
	)
