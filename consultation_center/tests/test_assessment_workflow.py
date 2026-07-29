import json

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.assessment_portal import (
	assign_assessment,
	review_assessment,
	save_assessment_responses,
)
from consultation_center.portal import (
	get_beneficiary_assessment_detail,
	get_beneficiary_assessments,
)


class TestAssessmentWorkflow(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.consultant_user = cls._make_user(
			"rushd.assessment.consultant@example.com",
			"Consultant",
		)
		cls.other_consultant_user = cls._make_user(
			"rushd.assessment.other-consultant@example.com",
			"Consultant",
		)
		cls.beneficiary_user = cls._make_user(
			"rushd.assessment.beneficiary@example.com",
			"Beneficiary",
		)
		cls.other_beneficiary_user = cls._make_user(
			"rushd.assessment.other-beneficiary@example.com",
			"Beneficiary",
		)
		cls.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": "اختبار المقاييس",
				"service_code": "_RUSHD-ASSESSMENT-WORKFLOW",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)
		cls.beneficiary = cls._make_beneficiary(
			"مستفيد اختبار المقاييس",
			cls.beneficiary_user,
		)
		cls.other_beneficiary = cls._make_beneficiary(
			"مستفيد آخر للمقاييس",
			cls.other_beneficiary_user,
		)
		cls.consultant = cls._make_consultant(
			"_RUSHD-ASSESSMENT-CONSULTANT",
			cls.consultant_user,
		)
		cls.other_consultant = cls._make_consultant(
			"_RUSHD-ASSESSMENT-OTHER",
			cls.other_consultant_user,
		)
		cls.template, cls.version = cls._make_template_and_version(
			"_RUSHD-ASSESSMENT",
			"مقياس متابعة الاختبار",
			"After Professional Review",
		)

	@staticmethod
	def _make_user(email, role):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "اختبار مقياس رُشد",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		user.add_roles(role)
		return user.name

	@staticmethod
	def _make_beneficiary(name, user):
		return frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": name,
				"portal_user": user,
			}
		).insert(ignore_permissions=True)

	@classmethod
	def _make_consultant(cls, code, user):
		return frappe.get_doc(
			{
				"doctype": "Consultant",
				"consultant_name": code,
				"code": code,
				"user": user,
				"active": 1,
				"services": cls.service.name,
			}
		).insert(ignore_permissions=True)

	@classmethod
	def _make_template_and_version(cls, code, title, visibility):
		template = frappe.get_doc(
			{
				"doctype": "Assessment Template",
				"template_title": title,
				"template_code": code,
				"responder": "Beneficiary",
				"result_visibility": visibility,
				"active": 1,
			}
		).insert(ignore_permissions=True)
		version = frappe.get_doc(
			{
				"doctype": "Assessment Version",
				"assessment_template": template.name,
				"version_number": 1,
				"status": "Published",
				"instructions": "أجب وفق وضعك الحالي.",
				"questions": [
					{
						"question_code": "Q1",
						"question_text": "أستطيع ترتيب أولوياتي",
						"response_type": "Scale",
						"minimum_value": 1,
						"maximum_value": 5,
						"required": 1,
					},
					{
						"question_code": "Q2",
						"question_text": "أجد صعوبة في بدء المهام",
						"response_type": "Scale",
						"minimum_value": 1,
						"maximum_value": 5,
						"reverse_scored": 1,
						"required": 1,
					},
					{
						"question_code": "Q3",
						"question_text": "حددت خطوة عملية",
						"response_type": "Yes/No",
						"minimum_value": 0,
						"maximum_value": 1,
						"required": 1,
					},
				],
			}
		).insert(ignore_permissions=True)
		template.reload()
		return template, version

	@classmethod
	def _make_case(cls):
		frappe.set_user("Administrator")
		return frappe.get_doc(
			{
				"doctype": "Consultation Case",
				"beneficiary": cls.beneficiary.name,
				"service": cls.service.name,
				"case_owner": "Administrator",
				"primary_consultant": cls.consultant.name,
				"case_status": "Active",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_full_assessment_flow_keeps_internal_interpretation_private(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		assigned = assign_assessment(
			case=case.name,
			assessment_version=self.version.name,
			assessment_type="Baseline",
			due_date="2026-08-20",
		)

		frappe.set_user(self.beneficiary_user)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Assessment Submission", pluck="name")
		self.assertIn(
			assigned["name"],
			[row.name for row in get_beneficiary_assessments(self.beneficiary.name)],
		)
		submitted = save_assessment_responses(
			submission_name=assigned["name"],
			responses=json.dumps(
				[
					{"question_code": "Q1", "answer_value": "5"},
					{"question_code": "Q2", "answer_value": "1"},
					{"question_code": "Q3", "answer_value": "1"},
				]
			),
			submit=1,
		)
		self.assertEqual(submitted["status"], "Submitted")

		frappe.set_user(self.consultant_user)
		review_assessment(
			submission_name=assigned["name"],
			professional_interpretation="<b>تفسير مهني داخلي</b>",
			beneficiary_result_summary="<p>يوضح المؤشر تقدمًا في تنظيم الأولويات.</p>",
			publish_result=1,
		)
		doc = frappe.get_doc("Assessment Submission", assigned["name"])
		self.assertEqual(doc.percentage_score, 100)
		self.assertEqual(doc.professional_interpretation, "تفسير مهني داخلي")
		self.assertEqual(doc.beneficiary_result_summary, "يوضح المؤشر تقدمًا في تنظيم الأولويات.")

		frappe.set_user(self.beneficiary_user)
		detail = get_beneficiary_assessment_detail(
			self.beneficiary.name,
			assigned["name"],
		)
		self.assertTrue(detail["result_visible"])
		self.assertEqual(detail["percentage_score"], 100)
		self.assertNotIn("professional_interpretation", detail)

	def test_other_consultant_and_beneficiary_cannot_access_assignment(self):
		case = self._make_case()
		frappe.set_user(self.other_consultant_user)
		with self.assertRaises(frappe.PermissionError):
			assign_assessment(
				case=case.name,
				assessment_version=self.version.name,
			)

		frappe.set_user(self.consultant_user)
		assigned = assign_assessment(
			case=case.name,
			assessment_version=self.version.name,
			assessment_type="Follow-up",
		)
		frappe.set_user(self.other_beneficiary_user)
		with self.assertRaises(frappe.PermissionError):
			save_assessment_responses(
				submission_name=assigned["name"],
				responses="[]",
			)

	def test_result_policy_can_prevent_publication(self):
		frappe.set_user("Administrator")
		_, hidden_version = self._make_template_and_version(
			"_RUSHD-ASSESSMENT-HIDDEN",
			"مقياس داخلي",
			"Never",
		)
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		assigned = assign_assessment(
			case=case.name,
			assessment_version=hidden_version.name,
			assessment_type="Closing",
		)
		frappe.set_user(self.beneficiary_user)
		save_assessment_responses(
			submission_name=assigned["name"],
			responses=json.dumps(
				[
					{"question_code": "Q1", "answer_value": "3"},
					{"question_code": "Q2", "answer_value": "3"},
					{"question_code": "Q3", "answer_value": "1"},
				]
			),
			submit=1,
		)
		frappe.set_user(self.consultant_user)
		with self.assertRaises(frappe.ValidationError):
			review_assessment(
				submission_name=assigned["name"],
				beneficiary_result_summary="ملخص لا تسمح السياسة بنشره.",
				publish_result=1,
			)

	def test_weighted_dimensions_excluded_option_and_safety_escalation(self):
		frappe.set_user("Administrator")
		template = frappe.get_doc(
			{
				"doctype": "Assessment Template",
				"template_title": "أداة متابعة وسلامة للاختبار",
				"template_code": f"_RUSHD-SAFE-{frappe.generate_hash(length=6).upper()}",
				"instrument_kind": "Safety Screener",
				"responder": "Beneficiary",
				"result_visibility": "After Professional Review",
				"active": 1,
			}
		).insert(ignore_permissions=True)
		version = frappe.get_doc(
			{
				"doctype": "Assessment Version",
				"assessment_template": template.name,
				"version_number": 1,
				"status": "Published",
				"scoring_method": "Percentage",
				"minimum_answered_percent": 100,
				"interpretation_rules_json": json.dumps(
					[
						{
							"minimum_age": 0,
							"maximum_age": 120,
							"minimum_score": 80,
							"maximum_score": 100,
							"label": "تقدم مرتفع يحتاج مراجعة مهنية",
						}
					],
					ensure_ascii=False,
				),
				"questions": [
					{
						"question_code": "W1",
						"question_text": "أستطيع التعامل مع الضغوط",
						"dimension": "إدارة الضغوط",
						"response_type": "Likert Agreement",
						"minimum_value": 1,
						"maximum_value": 5,
						"weight": 2,
						"required": 1,
					},
					{
						"question_code": "W2",
						"question_text": "كيف تصف تقدمك؟",
						"dimension": "إدارة الضغوط",
						"response_type": "Single Select",
						"options_json": json.dumps(
							[
								{"value": "GOOD", "label": "تقدم واضح", "score": 5},
								{"value": "NA", "label": "غير منطبق", "excluded": 1},
							],
							ensure_ascii=False,
						),
						"required": 1,
					},
					{
						"question_code": "SAFE1",
						"question_text": "هل تحتاج مساعدة عاجلة الآن؟",
						"response_type": "Yes/No",
						"is_safety_item": 1,
						"critical_values_json": '["1"]',
						"critical_action": "التواصل الفوري والتحقق من السلامة.",
						"required": 1,
					},
				],
			}
		).insert(ignore_permissions=True)
		case = self._make_case()
		frappe.db.set_value("Beneficiary", self.beneficiary.name, "date_of_birth", "2008-01-01")

		frappe.set_user(self.consultant_user)
		assigned = assign_assessment(case=case.name, assessment_version=version.name)
		frappe.set_user(self.beneficiary_user)
		save_assessment_responses(
			submission_name=assigned["name"],
			responses=[
				{"question_code": "W1", "answer_value": "5"},
				{"question_code": "W2", "answer_value": "GOOD"},
				{"question_code": "SAFE1", "answer_value": "1"},
			],
			submit=1,
		)

		submission = frappe.get_doc("Assessment Submission", assigned["name"])
		self.assertEqual(submission.percentage_score, 100)
		self.assertEqual(submission.scored_count, 2)
		self.assertTrue(submission.safety_alert_triggered)
		self.assertEqual(submission.interpretation_band, "تقدم مرتفع يحتاج مراجعة مهنية")
		self.assertTrue(submission.professional_escalation)
		self.assertIn("إدارة الضغوط", json.loads(submission.dimension_scores_json))
		escalation = frappe.get_doc(
			"Professional Escalation",
			submission.professional_escalation,
		)
		self.assertEqual(escalation.source_assessment, submission.name)
		self.assertEqual(escalation.severity, "Critical")

	def test_published_version_is_immutable(self):
		frappe.set_user("Administrator")
		version = frappe.get_doc("Assessment Version", self.version.name)
		version.instructions = "محاولة تعديل نسخة منشورة"
		with self.assertRaises(frappe.ValidationError):
			version.save(ignore_permissions=True)
