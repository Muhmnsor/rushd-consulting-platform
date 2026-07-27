from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.www.index import _get_portal_url, get_context


class TestPublicPage(FrappeTestCase):
	def test_each_role_is_sent_to_its_own_portal(self):
		self.assertEqual(_get_portal_url("Administrator", set()), "/app/rushd")
		self.assertEqual(_get_portal_url("director@example.com", {"Center Director"}), "/app/rushd")
		self.assertEqual(
			_get_portal_url("supervisor@example.com", {"Consultation Supervisor"}),
			"/supervisor",
		)
		self.assertEqual(
			_get_portal_url("operations@example.com", {"Intake Coordinator"}),
			"/operations",
		)
		self.assertEqual(_get_portal_url("beneficiary@example.com", {"Beneficiary"}), "/beneficiary")
		self.assertEqual(_get_portal_url("guardian@example.com", {"Guardian"}), "/guardian")

	def test_staff_route_takes_priority_for_multi_role_users(self):
		self.assertEqual(
			_get_portal_url(
				"staff@example.com",
				{"Beneficiary", "Operations Officer"},
			),
			"/operations",
		)

	def test_request_action_is_only_shown_to_guests_and_beneficiaries(self):
		guest_context = self._build_context("Guest", [])
		self.assertTrue(guest_context.can_request_consultation)
		self.assertEqual(
			guest_context.request_url,
			"/login?redirect-to=/beneficiary/requests/new",
		)
		self.assertEqual(guest_context.header_action_label, "اطلب استشارة")
		self.assertEqual(guest_context.header_action_url, guest_context.request_url)

		beneficiary_context = self._build_context(
			"beneficiary@example.com",
			["Beneficiary"],
		)
		self.assertTrue(beneficiary_context.can_request_consultation)
		self.assertEqual(beneficiary_context.request_url, "/beneficiary/requests/new")
		self.assertEqual(beneficiary_context.header_action_label, "حسابي")
		self.assertEqual(beneficiary_context.header_action_url, "/beneficiary")

		admin_context = self._build_context(
			"Administrator",
			["System Manager", "Beneficiary"],
		)
		self.assertFalse(admin_context.can_request_consultation)
		self.assertEqual(admin_context.primary_action_url, "/app/rushd")
		self.assertEqual(admin_context.header_action_label, "حسابي")
		self.assertEqual(admin_context.header_action_url, "/app/rushd")

	def test_every_public_navigation_anchor_has_a_target_section(self):
		template_path = Path(__file__).parents[1] / "www" / "index.html"
		template = template_path.read_text()

		for section in ("services", "journey", "privacy", "faq"):
			self.assertIn(f'href="#{section}"', template)
			self.assertIn(f'id="{section}"', template)

	def _build_context(self, user, roles):
		frappe.set_user(user)
		self.addCleanup(frappe.set_user, "Administrator")
		with patch("consultation_center.www.index.frappe.get_roles", return_value=roles):
			context = frappe._dict()
			get_context(context)
		return context
