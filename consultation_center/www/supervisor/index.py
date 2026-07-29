import frappe

from consultation_center.staff import (
	SUPERVISOR_ACCESS,
	build_staff_context,
	get_escalation_queue,
	get_referral_review_queue,
	get_request_counts,
	get_staff_requests,
	get_supervision_request_queue,
)

no_cache = 1


def get_context(context):
	build_staff_context(
		context,
		"supervisor-dashboard",
		"لوحة المشرف",
		"supervisor",
		SUPERVISOR_ACCESS,
	)
	context.counts = get_request_counts()
	context.requests = get_staff_requests(("Ready for Triage",), limit=8)
	context.pending_session_reviews = frappe.db.count(
		"Consultation Session",
		{"status": "Pending Review"},
	)
	context.submitted_assessments = frappe.db.count(
		"Assessment Submission",
		{"status": "Submitted"},
	)
	context.pending_referrals = len(
		[
			row
			for row in get_referral_review_queue(context.staff_user)
			if row.status == "Pending Approval"
		]
	)
	context.pending_supervision_requests = len(
		[
			row
			for row in get_supervision_request_queue(context.staff_user)
			if row.status in {"Submitted", "In Review"}
		]
	)
	escalations = get_escalation_queue(context.staff_user)
	context.open_escalations = len(
		[row for row in escalations if row.status != "Resolved"]
	)
	context.critical_escalations = len(
		[
			row
			for row in escalations
			if row.severity == "Critical" and row.status != "Resolved"
		]
	)
