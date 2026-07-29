from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import check_password

from consultation_center.api.user_admin import (
	create_staff_user,
	set_user_password,
	update_security_settings,
	update_user_roles,
	update_user_status,
)


class TestUserPasswordAdministration(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		suffix = frappe.generate_hash(length=8).lower()
		self.manager = self._make_user(
			f"rushd.password.manager.{suffix}@example.com",
			"System Manager",
			"مدير كلمات المرور",
		)
		self.target = self._make_user(
			f"rushd.password.target.{suffix}@example.com",
			None,
			"مستخدم تجريبي",
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def _make_user(email, role, first_name):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"enabled": 1,
				"user_type": "System User" if role else "Website User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		if role:
			user.add_roles(role)
		return user.name

	def test_system_manager_sets_password_without_sending_email(self):
		frappe.set_user(self.manager)
		password = "Secure-Rushd!2026-A7"

		with patch("frappe.sendmail") as sendmail:
			result = set_user_password(self.target, password, logout_all_sessions=1)

		self.assertEqual(result["user"], self.target)
		self.assertEqual(check_password(self.target, password), self.target)
		sendmail.assert_not_called()
		self.assertEqual(
			frappe.db.get_value("User", self.target, "reset_password_key"),
			"",
		)
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{
					"reference_doctype": "User",
					"reference_name": self.target,
					"content": ["like", "%دون إرسال بريد إلكتروني%"],
				},
			)
		)

	def test_regular_user_cannot_set_another_password(self):
		frappe.set_user(self.target)
		with self.assertRaises(frappe.PermissionError):
			set_user_password(self.manager, "Secure-Rushd!2026-B8")

	def test_system_manager_cannot_change_administrator_password(self):
		frappe.set_user(self.manager)
		with self.assertRaises(frappe.PermissionError):
			set_user_password("Administrator", "Secure-Rushd!2026-C9")

	def test_admin_can_create_staff_and_manage_status_and_roles(self):
		frappe.set_user("Administrator")
		suffix = frappe.generate_hash(length=8).lower()
		email = f"rushd.new.staff.{suffix}@example.com"
		result = create_staff_user(
			full_name="موظف تشغيل جديد",
			email=email,
			username=f"rushd-{suffix}",
			roles=["Operations Officer"],
		)
		user = frappe.get_doc("User", result["user"])
		self.assertTrue(user.enabled)
		self.assertIn("Operations Officer", frappe.get_roles(user.name))

		update_user_roles(user.name, ["Case Coordinator", "Operations Officer"])
		self.assertIn("Case Coordinator", frappe.get_roles(user.name))

		update_user_status(user.name, 0)
		self.assertFalse(frappe.db.get_value("User", user.name, "enabled"))
		update_user_status(user.name, 1)
		self.assertTrue(frappe.db.get_value("User", user.name, "enabled"))

	def test_admin_can_update_security_policy_from_simplified_page(self):
		frappe.set_user("Administrator")
		update_security_settings(
			enable_password_policy=1,
			minimum_password_score=3,
			allow_consecutive_login_attempts=6,
			allow_login_after_fail=90,
			session_expiry="12:00",
			deny_multiple_sessions=1,
			allow_login_using_user_name=1,
			enable_two_factor_auth=0,
		)
		settings = frappe.get_single("System Settings")
		self.assertEqual(int(settings.minimum_password_score), 3)
		self.assertEqual(settings.allow_consecutive_login_attempts, 6)
		self.assertEqual(settings.session_expiry, "12:00")
		self.assertTrue(settings.deny_multiple_sessions)
