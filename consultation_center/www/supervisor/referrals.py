import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_referral_review_queue,
)

no_cache = 1


def get_context(context):
	build_staff_context(context, "supervisor-referrals", "مراجعة الإحالات", "supervisor", SUPERVISOR_ACCESS)
	context.referrals = get_referral_review_queue(context.staff_user)
	selected = frappe.form_dict.get("referral")
	context.selected_referral = (
		frappe.get_doc("Case Referral", selected)
		if selected and selected in {row.name for row in context.referrals}
		else None
	)
	if context.selected_referral:
		context.selected_referral.referral_type_label = {
			"Internal": "داخلية",
			"External": "خارجية",
		}.get(
			context.selected_referral.referral_type,
			context.selected_referral.referral_type,
		)
