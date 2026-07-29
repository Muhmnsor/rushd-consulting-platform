import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from consultation_center.assessments import (
	SUPPORTED_RESPONSE_TYPES,
	parse_json_list,
	question_options,
)

MANAGER_ROLES = {"System Manager", "Center Director", "Assessment Manager"}


class AssessmentVersion(Document):
	def before_insert(self):
		self.created_by = self.created_by or frappe.session.user
		self.created_on = self.created_on or now_datetime()

	def validate(self):
		self._validate_version()
		self._validate_interpretation_rules()
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
			if question.response_type not in SUPPORTED_RESPONSE_TYPES:
				frappe.throw(f"نوع إجابة السؤال {question.question_code} غير مدعوم")
			if question.condition_question_code:
				question.condition_question_code = question.condition_question_code.strip().upper()
				if question.condition_question_code not in seen:
					frappe.throw(
						f"شرط السؤال {question.question_code} يجب أن يشير إلى سؤال سابق"
					)
			seen.add(question.question_code)
			if question.response_type in {
				"Scale",
				"Likert Agreement",
				"Frequency",
				"Frequency Scale",
				"Intensity",
				"Intensity Scale",
				"Difficulty",
				"Difficulty Scale",
				"Confidence",
				"Confidence Scale",
				"Numeric Rating",
				"Semantic Differential",
				"Number",
				"Goal Rating",
				"Matrix",
			}:
				if question.maximum_value <= question.minimum_value:
					frappe.throw(_("Question maximum must be greater than its minimum"))
			if frappe.utils.flt(question.weight) < 0:
				frappe.throw(f"وزن السؤال {question.question_code} لا يمكن أن يكون سالبًا")
			if question.response_type in {
				"Single Select",
				"Multi Select",
				"Ranking",
				"Scenario Based",
				"Parent/Proxy Item",
				"Observer Item",
			} and not question_options(question):
				frappe.throw(f"أضف خيارات للسؤال {question.question_code}")
			parse_json_list(question.critical_values_json, "القيم الحرجة")
			if question.is_safety_item:
				question.scored = 0
				if not question.critical_action:
					frappe.throw(f"حدد الإجراء الفوري لسؤال السلامة {question.question_code}")
			if question.response_type in {"Open Text", "Ranking"}:
				question.scored = 0

	def _validate_interpretation_rules(self):
		rules = parse_json_list(self.interpretation_rules_json, "قواعد تفسير النتائج")
		for index, rule in enumerate(rules, 1):
			if not isinstance(rule, dict):
				frappe.throw(f"قاعدة تفسير النتائج {index} غير صالحة")
			minimum_age = frappe.utils.cint(rule.get("minimum_age"))
			maximum_age = frappe.utils.cint(rule.get("maximum_age"))
			minimum_score = frappe.utils.flt(rule.get("minimum_score"))
			maximum_score = frappe.utils.flt(rule.get("maximum_score"))
			if (
				maximum_age < minimum_age
				or maximum_score < minimum_score
				or not str(rule.get("label") or "").strip()
			):
				frappe.throw(f"حدود قاعدة تفسير النتائج {index} غير صالحة")

	def _validate_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Draft", "Published"}:
				frappe.throw(_("A new assessment version must start as draft or published"))
		elif previous.status == "Published":
			if self.status != "Archived":
				frappe.throw(_("A published assessment version is immutable"))
			if self._published_content_changed(previous):
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

	def _published_content_changed(self, previous):
		fields = [
			"assessment_template",
			"version_number",
			"instructions",
			"timeframe",
			"scoring_method",
			"minimum_answered_percent",
			"missing_answer_policy",
			"interpretation_rules_json",
		]
		if any(self.get(field) != previous.get(field) for field in fields):
			return True
		question_fields = [
			"question_code",
			"question_text",
			"beneficiary_help",
			"dimension",
			"timeframe",
			"response_type",
			"required",
			"scored",
			"weight",
			"minimum_value",
			"maximum_value",
			"step_value",
			"reverse_scored",
			"left_anchor",
			"right_anchor",
			"options_json",
			"condition_question_code",
			"condition_operator",
			"condition_value",
			"is_safety_item",
			"critical_values_json",
			"critical_action",
		]
		current_questions = [
			tuple(question.get(field) for field in question_fields) for question in self.questions
		]
		previous_questions = [
			tuple(question.get(field) for field in question_fields) for question in previous.questions
		]
		return current_questions != previous_questions

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
