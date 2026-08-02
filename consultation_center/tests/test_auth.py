from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.auth import check_password
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.auth import sign_up
from consultation_center.localization import force_arabic_for_guests


class TestRushdSignUp(FrappeTestCase):
	def test_portal_logout_uses_post_request_instead_of_legacy_get_link(self):
		app_path = Path(frappe.get_app_path("consultation_center"))
		auth_script = (app_path / "public" / "js" / "rushd-auth.js").read_text()

		self.assertIn('method: "logout"', auth_script)
		self.assertIn("data-rushd-logout", auth_script)
		for template_name in (
			"rushd_portal.html",
			"rushd_staff.html",
			"rushd_guardian.html",
		):
			template = (app_path / "templates" / template_name).read_text()
			self.assertIn("data-rushd-logout", template)
			self.assertNotIn("cmd=web_logout", template)

	def test_guest_pages_are_rendered_in_arabic(self):
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.local.lang = "en"

		force_arabic_for_guests()

		self.assertEqual(frappe.local.lang, "ar")

	def test_authenticated_language_preference_is_preserved(self):
		frappe.set_user("Administrator")
		frappe.local.lang = "en"

		force_arabic_for_guests()

		self.assertEqual(frappe.local.lang, "en")

	def test_signup_creates_beneficiary_account_and_profile(self):
		email = f"rushd-signup-{frappe.generate_hash(length=8)}@example.com"
		password = "Rushd_Test_2026!"
		frappe.utils.set_request(path="/login")

		with patch(
			"frappe.core.doctype.user.user.is_signup_disabled",
			return_value=False,
		):
			result = sign_up(email, "مستفيد جديد", "/beneficiary", password)

		self.assertIn(result[0], (1, 2))
		self.assertTrue(frappe.db.exists("User", email))
		self.assertEqual(check_password(email, password), email)
		self.assertIn("Beneficiary", frappe.get_roles(email))

		beneficiary = frappe.db.get_value(
			"Beneficiary",
			{"portal_user": email},
			["beneficiary_name", "email", "status"],
			as_dict=True,
		)
		self.assertIsNotNone(beneficiary)
		self.assertEqual(beneficiary.beneficiary_name, "مستفيد جديد")
		self.assertEqual(beneficiary.email, email)
		self.assertEqual(beneficiary.status, "Active")
