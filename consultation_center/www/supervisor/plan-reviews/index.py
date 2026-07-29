import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_plan_review_detail,
	get_plan_reviews,
)

no_cache = 1


def get_context(context):
	build_staff_context(context, "supervisor-plan-reviews", "مراجعة الخطط", "supervisor", SUPERVISOR_ACCESS)
	context.plans = get_plan_reviews()
	selected = frappe.form_dict.get("plan") or (context.plans[0].name if context.plans else None)
	context.selected_plan = get_plan_review_detail(selected) if selected in {row.name for row in context.plans} else None
