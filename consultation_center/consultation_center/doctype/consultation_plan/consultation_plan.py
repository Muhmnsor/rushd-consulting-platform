import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

REVIEW_ROLES = {"System Manager", "Center Director", "Consultation Supervisor"}


class ConsultationPlan(Document):
	def before_insert(self):
		self.created_by = self.created_by or frappe.session.user
		self.created_on = self.created_on or now_datetime()

	def validate(self):
		self.validate_case_scope()
		self.validate_goals()
		self.validate_status_transition()

	def validate_case_scope(self):
		case = frappe.db.get_value(
			"Consultation Case",
			self.case,
			["beneficiary", "primary_consultant"],
			as_dict=True,
		)
		if not case:
			frappe.throw(_("Consultation case was not found"))
		if case.beneficiary != self.beneficiary:
			frappe.throw(_("Plan beneficiary must match the consultation case"))
		if case.primary_consultant != self.consultant:
			frappe.throw(_("Plan consultant must match the assigned case consultant"))

	def validate_goals(self):
		if self.status == "Pending Review" and not self.goals:
			frappe.throw(_("Add at least one goal before submitting the plan"))
		for goal in self.goals:
			if not (goal.goal_title or "").strip():
				frappe.throw(_("Every plan goal needs a title"))

	def validate_status_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Draft", "Pending Review"}:
				frappe.throw(_("A new plan must start as a draft or pending review"))
			return
		if previous.status in {"Active", "Completed", "Archived"}:
			frappe.throw(_("An active or closed plan cannot be edited; create a new version"))

		allowed = {
			"Draft": {"Draft", "Pending Review", "Archived"},
			"Pending Review": {"Pending Review", "Active", "Returned", "Archived"},
			"Returned": {"Returned", "Draft", "Pending Review", "Archived"},
		}
		if self.status not in allowed.get(previous.status, {previous.status}):
			frappe.throw(_("Invalid plan status transition"))

		if self.status in {"Active", "Returned"} and self.status != previous.status:
			roles = set(frappe.get_roles(frappe.session.user))
			if frappe.session.user != "Administrator" and not roles & REVIEW_ROLES:
				frappe.throw(_("Only a supervisor can review a plan"), frappe.PermissionError)
			if self.status == "Returned" and not (self.review_note or "").strip():
				frappe.throw(_("A return reason is required"))
			self.reviewed_by = frappe.session.user
			self.reviewed_on = now_datetime()
			if self.status == "Active":
				self.approved_by = frappe.session.user
				self.approved_on = now_datetime()

	def on_trash(self):
		frappe.throw(_("Plans cannot be deleted; archive the plan instead"))
