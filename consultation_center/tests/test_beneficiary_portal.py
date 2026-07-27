import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.beneficiary_portal import (
	save_consultation_request,
	update_beneficiary_profile,
)


class TestBeneficiaryPortal(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": "Rushd Portal Test",
				"service_code": "_RUSHD-PORTAL-TEST",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)
		cls.user = cls._make_user("rushd.portal.owner@example.com")
		cls.other_user = cls._make_user("rushd.portal.other@example.com")
		cls.user_without_profile = cls._make_user("rushd.portal.no-profile@example.com")
		cls.beneficiary = cls._make_beneficiary(cls.user, "Portal Owner")
		cls.other_beneficiary = cls._make_beneficiary(cls.other_user, "Portal Other")

	@staticmethod
	def _make_user(email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Rushd Portal Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		user.add_roles("Beneficiary")
		return user.name

	@staticmethod
	def _make_beneficiary(user, beneficiary_name):
		return frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": beneficiary_name,
				"portal_user": user,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_submitted_request_is_bound_to_signed_in_beneficiary(self):
		frappe.set_user(self.user)
		result = save_consultation_request(
			requested_service=self.service.name,
			summary="أحتاج إلى مساعدة في ترتيب أهدافي الدراسية خلال هذا الفصل.",
			preferred_mode="Either",
			preferred_times="مساءً",
			submit=1,
			emergency_acknowledged=1,
		)

		request_doc = frappe.get_doc("Consultation Request", result["name"])
		self.assertEqual(request_doc.beneficiary, self.beneficiary.name)
		self.assertEqual(request_doc.owner, self.user)
		self.assertEqual(request_doc.workflow_state, "Submitted")

	def test_user_cannot_update_another_beneficiary_draft(self):
		frappe.set_user(self.other_user)
		other_request = save_consultation_request(
			requested_service=self.service.name,
			summary="هذه مسودة تخص المستفيد الآخر فقط.",
			preferred_mode="Online",
		)

		frappe.set_user(self.user)
		with self.assertRaises(frappe.PermissionError):
			save_consultation_request(
				requested_service=self.service.name,
				summary="محاولة تعديل طلب لا يخص المستخدم الحالي.",
				preferred_mode="Online",
				request_name=other_request["name"],
			)

	def test_user_without_profile_cannot_create_request(self):
		frappe.set_user(self.user_without_profile)
		with self.assertRaises(frappe.PermissionError):
			save_consultation_request(
				requested_service=self.service.name,
				summary="لا يجب إنشاء هذا الطلب دون ملف مستفيد.",
				preferred_mode="Either",
			)

	def test_profile_update_is_bound_to_signed_in_beneficiary(self):
		frappe.set_user(self.user)
		update_beneficiary_profile(
			beneficiary_name="Portal Owner Updated",
			mobile="0501234567",
			email="rushd.portal.owner@example.com",
			city="Riyadh",
			date_of_birth="2001-02-03",
			preferred_language="Arabic",
		)

		self.beneficiary.reload()
		self.other_beneficiary.reload()
		self.assertEqual(self.beneficiary.beneficiary_name, "Portal Owner Updated")
		self.assertEqual(self.beneficiary.city, "Riyadh")
		self.assertEqual(self.other_beneficiary.beneficiary_name, "Portal Other")

