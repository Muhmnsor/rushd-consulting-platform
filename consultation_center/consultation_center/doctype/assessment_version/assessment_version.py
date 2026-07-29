import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

MANAGER_ROLES = {"System Manager", "Center Director", "Assessment Manager"}


class AssessmentVersion(Document):
	def before_insert(self):
		self.created_by = self.created_by or frappe.session.user
		self.created_on = self.created_on or now_datetime()

	def validate(self):
		self._validate_version()
		self._validate_questions()
		self._validate_transition()

	def _validate_version(self):
		if frappe.db.exists(
			"Assessment Version",
			{
				"assessment_template": self.assessment_template,
				"version_number": self.version_number,
				"name": ["!=", self.name],
			},
		):
			frappe.throw(_("This assessment version already exists"))

	def _validate_questions(self):
		if self.status == "Published" and not self.questions:
			frappe.throw(_("Add at least one question before publishing the assessment"))
		seen = set()
		for question in self.questions:
			question.question_code = (question.question_code or "").strip().upper()
			question.question_text = (question.question_text or "").strip()
			if not question.question_code or not question.question_text:
				frappe.throw(_("Every assessment question needs a code and text"))
			if question.question_code in seen:
				frappe.throw(_("Assessment question codes must be unique"))
			seen.add(question.question_code)
			if question.response_type in {"Scale", "Number"}:
				if question.maximum_value <= question.minimum_value:
					frappe.throw(_("Question maximum must be greater than its minimum"))

	def _validate_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Draft", "Published"}:
				frappe.throw(_("A new assessment version must start as draft or published"))
		elif previous.status == "Published":
			if self.status != "Archived":
				frappe.throw(_("A published assessment version is immutable"))
		elif previous.status == "Archived":
			frappe.throw(_("An archived assessment version is immutable"))
		elif self.status not in {"Draft", "Published", "Archived"}:
			frappe.throw(_("Invalid assessment version status transition"))

		if self.status == "Published" and (not previous or previous.status != "Published"):
			self._require_manager()
			self.published_by = frappe.session.user
			self.published_on = now_datetime()
		if self.status == "Archived" and (not previous or previous.status != "Archived"):
			self._require_manager()

	def _require_manager(self):
		roles = set(frappe.get_roles(frappe.session.user))
		if frappe.session.user != "Administrator" and not roles & MANAGER_ROLES:
			frappe.throw(_("Only an assessment manager can publish or archive a version"), frappe.PermissionError)

	def on_update(self):
		if self.status == "Published":
			frappe.db.set_value(
				"Assessment Template",
				self.assessment_template,
				"current_published_version",
				self.name,
				update_modified=False,
			)
		elif self.status == "Archived":
			current = frappe.db.get_value(
				"Assessment Template",
				self.assessment_template,
				"current_published_version",
			)
			if current == self.name:
				frappe.db.set_value(
					"Assessment Template",
					self.assessment_template,
					"current_published_version",
					None,
					update_modified=False,
				)

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("Only draft assessment versions can be deleted"))
