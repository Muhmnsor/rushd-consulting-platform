import frappe
from frappe.tests.utils import FrappeTestCase


class TestRushdRecordIsolation(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

		cls.beneficiary_user = cls._make_user("rushd.beneficiary@example.com", "Website User")
		cls.other_beneficiary_user = cls._make_user(
			"rushd.other.beneficiary@example.com",
			"Website User",
		)
		cls.guardian_user = cls._make_user("rushd.guardian@example.com", "Website User")
		cls.consultant_user = cls._make_user("rushd.consultant@example.com", "System User")
		cls.other_consultant_user = cls._make_user(
			"rushd.other.consultant@example.com",
			"System User",
		)

		cls.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": "Rushd Permission Test",
				"service_code": "_RUSHD-PERMISSION-TEST",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)

		cls.beneficiary = frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": "Rushd Test Beneficiary",
				"portal_user": cls.beneficiary_user,
			}
		).insert(ignore_permissions=True)
		cls.other_beneficiary = frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": "Rushd Other Beneficiary",
				"portal_user": cls.other_beneficiary_user,
			}
		).insert(ignore_permissions=True)

		cls.guardian = frappe.get_doc(
			{
				"doctype": "Guardian",
				"guardian_name": "Rushd Test Guardian",
				"portal_user": cls.guardian_user,
			}
		).insert(ignore_permissions=True)
		cls.authorization = frappe.get_doc(
			{
				"doctype": "Guardian Authorization",
				"guardian": cls.guardian.name,
				"beneficiary": cls.beneficiary.name,
				"relationship": "Legal Guardian",
				"authorization_status": "Active",
				"can_view_profile": 1,
				"can_view_requests": 1,
				"can_view_case": 1,
				"can_manage_appointments": 1,
			}
		).insert(ignore_permissions=True)

		cls.consultant = cls._make_consultant(
			"_RUSHD-CONSULTANT",
			cls.consultant_user,
		)
		cls.other_consultant = cls._make_consultant(
			"_RUSHD-OTHER-CONSULTANT",
			cls.other_consultant_user,
		)
		cls.case = cls._make_case(cls.beneficiary.name, cls.consultant.name)
		cls.other_case = cls._make_case(
			cls.other_beneficiary.name,
			cls.other_consultant.name,
		)

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		super().tearDownClass()

	@staticmethod
	def _make_user(email, user_type):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Rushd Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": user_type,
			}
		).insert(ignore_permissions=True).name

	@staticmethod
	def _make_consultant(code, user):
		return frappe.get_doc(
			{
				"doctype": "Consultant",
				"consultant_name": code,
				"code": code,
				"user": user,
				"active": 1,
			}
		).insert(ignore_permissions=True)

	@classmethod
	def _make_case(cls, beneficiary, consultant):
		return frappe.get_doc(
			{
				"doctype": "Consultation Case",
				"beneficiary": beneficiary,
				"service": cls.service.name,
				"case_owner": "Administrator",
				"primary_consultant": consultant,
				"case_status": "Assigned",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_beneficiary_sees_only_own_records(self):
		frappe.set_user(self.beneficiary_user)

		self.assertEqual(
			frappe.get_list("Beneficiary", pluck="name"),
			[self.beneficiary.name],
		)
		self.assertEqual(
			frappe.get_list("Consultation Case", pluck="name"),
			[self.case.name],
		)
		self.assertFalse(
			frappe.get_doc("Consultation Case", self.other_case.name).has_permission(
				"read",
				user=self.beneficiary_user,
			)
		)

	def test_guardian_scope_does_not_expose_other_beneficiaries(self):
		frappe.set_user(self.guardian_user)

		self.assertEqual(
			frappe.get_list("Beneficiary", pluck="name"),
			[self.beneficiary.name],
		)
		self.assertEqual(
			frappe.get_list("Consultation Case", pluck="name"),
			[self.case.name],
		)

	def test_consultant_sees_only_assigned_case(self):
		frappe.set_user(self.consultant_user)

		self.assertEqual(
			frappe.get_list("Consultation Case", pluck="name"),
			[self.case.name],
		)
		self.assertEqual(
			frappe.get_list("Beneficiary", pluck="name"),
			[self.beneficiary.name],
		)
