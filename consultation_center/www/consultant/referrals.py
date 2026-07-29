import frappe

from consultation_center.consultant_portal import (
	REFERRAL_STATUS,
	build_consultant_context,
	get_consultant_cases,
	get_consultant_referrals,
)

no_cache = 1


def get_context(context):
	build_consultant_context(context, "consultant-referrals", "الإحالات")
	if not context.consultant:
		context.cases = []
		context.selected_case = None
		context.referrals = []
		context.selected_referral = None
		return
	context.cases = get_consultant_cases(context.consultant.name)
	context.services = frappe.db.get_all(
		"Consultation Service",
		filters={"active": 1},
		fields=["name", "service_name"],
		order_by="service_name asc",
	)
	case_name = frappe.form_dict.get("case")
	context.selected_case = next(
		(row for row in context.cases if row.name == case_name),
		None,
	)
	context.referrals = get_consultant_referrals(context.consultant.name, case_name)
	context.selected_referral = None
	referral_name = frappe.form_dict.get("referral")
	if referral_name:
		doc = frappe.get_doc("Case Referral", referral_name)
		if doc.consultant == context.consultant.name:
			doc.status_label = REFERRAL_STATUS.get(doc.status, doc.status)
			context.selected_referral = doc
			if not context.selected_case:
				context.selected_case = next(
					(row for row in context.cases if row.name == doc.case),
					None,
				)
