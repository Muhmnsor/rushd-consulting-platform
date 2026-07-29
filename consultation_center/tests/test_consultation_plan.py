import json

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.plan_portal import (
	create_beneficiary_task,
	review_consultation_plan,
	save_consultation_plan,
	update_own_task,
)
from consultation_center.portal import (
	get_active_beneficiary_plan,
	get_beneficiary_tasks,
)


class TestConsultationPlanWorkflow(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.consultant_user = cls._make_user(
			"rushd.plan.consultant@example.com",
			"Consultant",
		)
		cls.other_consultant_user = cls._make_user(
			"rushd.plan.other-consultant@example.com",
			"Consultant",
		)
		cls.supervisor_user = cls._make_user(
			"rushd.plan.supervisor@example.com",
			"Consultation Supervisor",
		)
		cls.beneficiary_user = cls._make_user(
			"rushd.plan.beneficiary@example.com",
			"Beneficiary",
		)
		cls.other_beneficiary_user = cls._make_user(
			"rushd.plan.other-beneficiary@example.com",
			"Beneficiary",
		)
		cls.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": "اختبار الخطة الاستشارية",
				"service_code": "_RUSHD-PLAN-WORKFLOW",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)
		cls.beneficiary = cls._make_beneficiary(
			"مستفيد اختبار الخطة",
			cls.beneficiary_user,
		)
		cls.other_beneficiary = cls._make_beneficiary(
			"مستفيد آخر لاختبار الخصوصية",
			cls.other_beneficiary_user,
		)
		cls.consultant = cls._make_consultant(
			"_RUSHD-PLAN-CONSULTANT",
			cls.consultant_user,
		)
		cls.other_consultant = cls._make_consultant(
			"_RUSHD-PLAN-OTHER-CONSULTANT",
			cls.other_consultant_user,
		)

	@staticmethod
	def _make_user(email, role):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "اختبار خطة رُشد",
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
	def _make_case(cls, beneficiary=None, consultant=None):
		frappe.set_user("Administrator")
		return frappe.get_doc(
			{
				"doctype": "Consultation Case",
				"beneficiary": beneficiary or cls.beneficiary.name,
				"service": cls.service.name,
				"case_owner": cls.supervisor_user,
				"supervisor": cls.supervisor_user,
				"primary_consultant": consultant or cls.consultant.name,
				"case_status": "Active",
			}
		).insert(ignore_permissions=True)

	@staticmethod
	def _goals():
		return json.dumps(
			[
				{
					"goal_title": "تنظيم الأولويات الأسبوعية",
					"indicator": "عدد الأولويات المنجزة",
					"baseline_value": "1",
					"target_value": "4",
					"beneficiary_visible": 1,
				},
				{
					"goal_title": "ملاحظة مهنية داخلية",
					"indicator": "تقدير المستشار",
					"beneficiary_visible": 0,
				},
			]
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_plan_is_reviewed_before_it_becomes_visible_to_beneficiary(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		result = save_consultation_plan(
			case=case.name,
			plan_title="خطة تنظيم الأولويات",
			plan_summary="خطة عملية موزعة على خطوات أسبوعية.",
			expected_sessions=4,
			goals=self._goals(),
			submit_for_review=1,
		)
		self.assertEqual(result["status"], "Pending Review")

		frappe.set_user(self.beneficiary_user)
		self.assertNotIn(
			result["name"],
			frappe.get_list("Consultation Plan", pluck="name"),
		)

		frappe.set_user(self.supervisor_user)
		approved = review_consultation_plan(
			plan_name=result["name"],
			decision="approve",
			review_note="الخطة واضحة وقابلة للقياس.",
		)
		self.assertEqual(approved["status"], "Active")

		frappe.set_user(self.beneficiary_user)
		plan = get_active_beneficiary_plan(self.beneficiary.name)
		self.assertEqual(plan.name, result["name"])
		self.assertEqual(len(plan.visible_goals), 1)
		self.assertEqual(plan.visible_goals[0].goal_title, "تنظيم الأولويات الأسبوعية")

	def test_return_requires_reason_and_consultant_can_resubmit(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		result = save_consultation_plan(
			case=case.name,
			plan_title="خطة أولية",
			goals=self._goals(),
			submit_for_review=1,
		)

		frappe.set_user(self.supervisor_user)
		with self.assertRaises(frappe.ValidationError):
			review_consultation_plan(
				plan_name=result["name"],
				decision="return",
				review_note="",
			)
		review_consultation_plan(
			plan_name=result["name"],
			decision="return",
			review_note="أضف تاريخ المراجعة ووضح المؤشر.",
		)

		frappe.set_user(self.consultant_user)
		resubmitted = save_consultation_plan(
			case=case.name,
			plan_name=result["name"],
			plan_title="خطة مستكملة",
			review_date="2026-08-30",
			goals=self._goals(),
			submit_for_review=1,
		)
		self.assertEqual(resubmitted["status"], "Pending Review")

	def test_other_consultant_cannot_edit_plan_for_unassigned_case(self):
		case = self._make_case()
		frappe.set_user(self.other_consultant_user)
		with self.assertRaises(frappe.PermissionError):
			save_consultation_plan(
				case=case.name,
				plan_title="خطة غير مصرح بها",
				goals=self._goals(),
			)

	def test_beneficiary_updates_only_own_task(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		plan_result = save_consultation_plan(
			case=case.name,
			plan_title="خطة بمهام متابعة",
			goals=self._goals(),
			submit_for_review=1,
		)
		frappe.set_user(self.supervisor_user)
		review_consultation_plan(
			plan_name=plan_result["name"],
			decision="approve",
		)

		frappe.set_user(self.consultant_user)
		task_result = create_beneficiary_task(
			plan_name=plan_result["name"],
			task_title="كتابة أربع أولويات",
			instructions="دوّن الأولويات ثم حدّث حالة المهمة.",
			due_date="2026-08-15",
		)

		frappe.set_user(self.beneficiary_user)
		updated = update_own_task(
			task_name=task_result["name"],
			status="Completed",
			beneficiary_note="<b>تم إنجاز المهمة</b>",
		)
		self.assertEqual(updated["status"], "Completed")
		task = frappe.get_doc("Beneficiary Task", task_result["name"])
		self.assertEqual(task.beneficiary_note, "تم إنجاز المهمة")
		self.assertIsNotNone(task.completed_on)
		self.assertEqual(
			[row.name for row in get_beneficiary_tasks(self.beneficiary.name)],
			[task.name],
		)

		frappe.set_user(self.other_beneficiary_user)
		self.assertEqual(get_beneficiary_tasks(self.other_beneficiary.name), [])
		with self.assertRaises(frappe.PermissionError):
			update_own_task(
				task_name=task.name,
				status="In Progress",
			)
