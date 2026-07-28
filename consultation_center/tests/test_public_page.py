from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.setup.install import RUSHD_LOGO_URL, configure_site_identity
from consultation_center.website import (
	SETTINGS_DOCTYPE,
	ensure_rushd_website_settings,
	get_rushd_website_settings,
)
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

	def test_homepage_content_is_loaded_from_single_settings_doctype(self):
		ensure_rushd_website_settings()
		settings = get_rushd_website_settings()

		self.assertTrue(frappe.db.exists("DocType", SETTINGS_DOCTYPE))
		self.assertEqual(settings.hero_title, "نستمع إليك،")
		self.assertEqual(len(settings.journey_steps), 4)
		self.assertEqual(len(settings.faqs), 4)

		context = self._build_context("Guest", [])
		self.assertEqual(context.website.page_title, settings.page_title)
		self.assertEqual(context.title, settings.page_title)
		self.assertLessEqual(len(context.services), settings.services_limit)

	def test_seed_does_not_overwrite_editorial_changes(self):
		settings = frappe.get_single(SETTINGS_DOCTYPE)
		settings.hero_title = "عنوان تحريري محفوظ"
		settings.save(ignore_permissions=True)

		ensure_rushd_website_settings()

		self.assertEqual(
			frappe.db.get_single_value(SETTINGS_DOCTYPE, "hero_title"),
			"عنوان تحريري محفوظ",
		)

	def test_website_workspace_integration_is_shipped_by_the_app(self):
		script_path = Path(__file__).parents[1] / "public" / "js" / "rushd-rtl.js"
		script = script_path.read_text()

		self.assertIn("installWebsiteSettingsEntry", script)
		self.assertIn("/app/rushd-website-settings/Rushd%20Website%20Settings", script)

	def test_site_loading_screen_uses_rushd_logo(self):
		configure_site_identity()

		self.assertEqual(
			frappe.db.get_single_value("Website Settings", "splash_image"),
			RUSHD_LOGO_URL,
		)
		self.assertEqual(
			frappe.db.get_single_value("Website Settings", "favicon"),
			RUSHD_LOGO_URL,
		)

	def test_login_variants_have_explicit_rtl_layout(self):
		rtl_path = Path(__file__).parents[1] / "public" / "css" / "rushd-rtl.css"
		rtl_styles = rtl_path.read_text()

		for login_variant in (
			".for-login",
			".for-email-login",
			".for-forgot",
			".for-login-with-email-link",
			".for-signup",
		):
			self.assertIn(login_variant, rtl_styles)

		self.assertIn("direction: rtl !important;", rtl_styles)
		self.assertIn(".password-field .toggle-password", rtl_styles)
		self.assertIn("left: 9px !important;", rtl_styles)

	def _build_context(self, user, roles):
		frappe.set_user(user)
		self.addCleanup(frappe.set_user, "Administrator")
		with patch("consultation_center.www.index.frappe.get_roles", return_value=roles):
			context = frappe._dict()
			get_context(context)
		return context
