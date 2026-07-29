import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from consultation_center.api.guardian_portal import grant_guardian_consent


class TestGuardianConsent(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.guardian_user = cls._make_user("rushd.guardian.consent@example.com")
		cls.other_guardian_user = cls._make_user("rushd.guardian.consent.other@example.com")
		cls.beneficiary_user = cls._make_user(
			"rushd.guardian.consent.beneficiary@example.com",
			role="Beneficiary",
		)
		cls.beneficiary = frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": "Guardian Consent Beneficiary",
				"portal_user": cls.beneficiary_user,
			}
		).insert(ignore_permissions=True)
		cls.guardian = cls._make_guardian(cls.guardian_user, "Consent Guardian")
		cls.other_guardian = cls._make_guardian(
			cls.other_guardian_user,
			"Other Consent Guardian",
		)
		cls.authorization = frappe.get_doc(
			{
				"doctype": "Guardian Authorization",
				"guardian": cls.guardian.name,
				"beneficiary": cls.beneficiary.name,
				"relationship": "Legal Guardian",
				"authorization_status": "Active",
				"effective_from": nowdate(),
				"can_view_profile": 1,
			}
		).insert(ignore_permissions=True)
		cls.template = frappe.get_doc(
			{
				"doctype": "Consent Template",
				"template_code": "_RUSHD-CONSENT-TEST",
				"template_title": "Guardian Consent Test",
				"requires_guardian": 1,
			}
		).insert(ignore_permissions=True)
		cls.version = frappe.get_doc(
			{
				"doctype": "Consent Version",
				"consent_template": cls.template.name,
				"version_label": "1.0-test",
				"status": "Published",
				"effective_from": nowdate(),
				"title": "Guardian Consent Test Version",
				"simplified_text": "Simplified immutable consent text.",
				"full_text": "Full immutable consent text for test purposes.",
			}
		).insert(ignore_permissions=True)

	@staticmethod
	def _make_user(email, role="Guardian"):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Rushd Consent Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		user.add_roles(role)
		return user.name

	@staticmethod
	def _make_guardian(user, guardian_name):
		return frappe.get_doc(
			{
				"doctype": "Guardian",
				"guardian_name": guardian_name,
				"portal_user": user,
			}
		).insert(ignore_permissions=True)

	@classmethod
	def _make_consent(cls):
		frappe.set_user("Administrator")
		return frappe.get_doc(
			{
				"doctype": "Consent Record",
				"consent_template": cls.template.name,
				"consent_version": cls.version.name,
				"beneficiary": cls.beneficiary.name,
				"guardian": cls.guardian.name,
				"consent_role": "Guardian",
				"status": "Pending",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_guardian_can_grant_own_pending_consent(self):
		consent = self._make_consent()
		frappe.set_user(self.guardian_user)
		grant_guardian_consent(consent.name, confirmed=1)

		consent.reload()
		self.beneficiary.reload()
		self.assertEqual(consent.status, "Granted")
		self.assertEqual(consent.granted_by, self.guardian_user)
		self.assertEqual(self.beneficiary.consent_status, "Granted")
		self.assertEqual(consent.grant_method, "Web")

	def test_other_guardian_cannot_grant_consent(self):
		consent = self._make_consent()
		frappe.set_user(self.other_guardian_user)
		with self.assertRaises(frappe.PermissionError):
			grant_guardian_consent(consent.name, confirmed=1)

	def test_published_consent_text_cannot_be_edited(self):
		frappe.set_user("Administrator")
		version = frappe.get_doc("Consent Version", self.version.name)
		version.full_text = "Changed after publication"
		with self.assertRaises(frappe.ValidationError):
			version.save(ignore_permissions=True)
