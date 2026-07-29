import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from consultation_center.assessments import is_question_applicable

REVIEW_ROLES = {"System Manager", "Center Director", "Consultation Supervisor", "Consultant"}


class AssessmentSubmission(Document):
	def before_insert(self):
		self.assigned_by = self.assigned_by or frappe.session.user
		self.assigned_on = self.assigned_on or now_datetime()

	def validate(self):
		self._validate_scope()
		self._validate_version()
		self._validate_responses()
		self._validate_transition()

	def _validate_scope(self):
		case = frappe.db.get_value(
			"Consultation Case",
			self.case,
			["beneficiary", "primary_consultant"],
			as_dict=True,
		)
		if not case:
			frappe.throw(_("Consultation case was not found"))
		if case.beneficiary != self.beneficiary:
			frappe.throw(_("Assessment beneficiary must match the consultation case"))
		if case.primary_consultant != self.consultant:
			frappe.throw(_("Assessment consultant must match the assigned case consultant"))

	def _validate_version(self):
		version = frappe.db.get_value(
			"Assessment Version",
			self.assessment_version,
			["assessment_template", "status"],
			as_dict=True,
		)
		if not version or version.assessment_template != self.assessment_template:
			frappe.throw(_("Assessment version does not match its template"))
		if self.is_new() and version.status != "Published":
			frappe.throw(_("Only a published assessment version can be assigned"))
		if not self.is_new() and version.status not in {"Published", "Archived"}:
			frappe.throw(_("Assigned assessment version is unavailable"))

	def _validate_responses(self):
		if self.status not in {"Submitted", "Reviewed"}:
			return
		version = frappe.get_doc("Assessment Version", self.assessment_version)
		answers = {row.question_code: row.answer_value for row in self.responses}
		for question in version.questions:
			if (
				question.required
				and is_question_applicable(question, answers)
				and not str(answers.get(question.question_code, "")).strip()
			):
				frappe.throw(_("Answer all required assessment questions before submitting"))

	def _validate_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Assigned", "In Progress"}:
				frappe.throw(_("A new assessment must start as assigned or in progress"))
			return
		if previous.status == "Reviewed":
			frappe.throw(_("A reviewed assessment is immutable"))
		allowed = {
			"Assigned": {"Assigned", "In Progress", "Submitted", "Cancelled"},
			"In Progress": {"In Progress", "Submitted", "Cancelled"},
			"Submitted": {"Submitted", "Reviewed", "Cancelled"},
			"Cancelled": {"Cancelled"},
		}
		if self.status not in allowed.get(previous.status, {previous.status}):
			frappe.throw(_("Invalid assessment submission status transition"))
		if self.status == "Reviewed" and self.status != previous.status:
			roles = set(frappe.get_roles(frappe.session.user))
			if frappe.session.user != "Administrator" and not roles & REVIEW_ROLES:
				frappe.throw(_("Only the assigned professional can review an assessment"), frappe.PermissionError)

	def on_trash(self):
		frappe.throw(_("Assessments cannot be deleted; cancel them instead"))
