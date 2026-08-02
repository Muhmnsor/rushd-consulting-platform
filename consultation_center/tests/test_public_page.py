from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.setup.install import RUSHD_LOGO_URL, configure_site_identity
from consultation_center.setup.services import DEFAULT_SERVICES, ensure_default_services
from consultation_center.website import (
	SETTINGS_DOCTYPE,
	TABLE_DEFAULTS,
	TEXT_DEFAULTS,
	ensure_rushd_website_settings,
	get_rushd_website_settings,
)
from consultation_center.www.index import (
	_get_portal_url,
	_get_public_consultants,
	_get_public_testimonials,
	_get_service_request_url,
	get_context,
)


class TestPublicPage(FrappeTestCase):
	def test_each_role_is_sent_to_its_own_portal(self):
		self.assertEqual(_get_portal_url("Administrator", set()), "/admin")
		self.assertEqual(_get_portal_url("director@example.com", {"Center Director"}), "/admin")
		self.assertEqual(
			_get_portal_url("supervisor@example.com", {"Consultation Supervisor"}),
			"/supervisor",
		)
		self.assertEqual(
			_get_portal_url("operations@example.com", {"Intake Coordinator"}),
			"/operations",
		)
		self.assertEqual(
			_get_portal_url("consultant@example.com", {"Consultant"}),
			"/consultant",
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
		self.assertTrue(
			all("redirect-to=" in service.request_url for service in guest_context.services)
		)
		self.assertTrue(
			all(service.request_label == "اطلب الخدمة الآن" for service in guest_context.services)
		)

		beneficiary_context = self._build_context(
			"beneficiary@example.com",
			["Beneficiary"],
		)
		self.assertTrue(beneficiary_context.can_request_consultation)
		self.assertEqual(beneficiary_context.request_url, "/beneficiary/requests/new")
		self.assertTrue(
			all(
				service.request_url.startswith("/beneficiary/requests/new?service=")
				for service in beneficiary_context.services
			)
		)
		self.assertEqual(beneficiary_context.header_action_label, "حسابي")
		self.assertEqual(beneficiary_context.header_action_url, "/beneficiary")

		admin_context = self._build_context(
			"Administrator",
			["System Manager", "Beneficiary"],
		)
		self.assertFalse(admin_context.can_request_consultation)
		self.assertEqual(admin_context.primary_action_url, "/admin")
		self.assertEqual(admin_context.header_action_label, "حسابي")
		self.assertEqual(admin_context.header_action_url, "/admin")
		self.assertTrue(
			all(service.request_label == "اطلب الخدمة الآن" for service in admin_context.services)
		)

	def test_service_request_action_preserves_selected_service_through_login(self):
		destination = "/beneficiary/requests/new?service=RUSHD-DIGITAL-BALANCE"
		self.assertEqual(
			_get_service_request_url("RUSHD-DIGITAL-BALANCE", True),
			destination,
		)
		self.assertEqual(
			_get_service_request_url("RUSHD-DIGITAL-BALANCE", False),
			"/login?redirect-to=%2Fbeneficiary%2Frequests%2Fnew%3Fservice%3DRUSHD-DIGITAL-BALANCE",
		)

		public_template = (Path(__file__).parents[1] / "www" / "index.html").read_text()
		request_template = (
			Path(__file__).parents[1] / "www" / "beneficiary" / "requests" / "new.html"
		).read_text()
		self.assertIn("rushd-service-card__action", public_template)
		self.assertIn("service.request_url", public_template)
		self.assertIn("service.name == selected_service", request_template)

	def test_every_public_navigation_anchor_has_a_target_section(self):
		template_path = Path(__file__).parents[1] / "www" / "index.html"
		template = template_path.read_text()

		for section in ("services", "consultants", "testimonials", "journey", "privacy", "faq"):
			self.assertIn(f'href="#{section}"', template)
			self.assertIn(f'id="{section}"', template)

	def test_homepage_content_is_loaded_from_single_settings_doctype(self):
		ensure_rushd_website_settings()
		settings = get_rushd_website_settings()

		self.assertTrue(frappe.db.exists("DocType", SETTINGS_DOCTYPE))
		self.assertEqual(settings.hero_title, "نستمع إليك،")
		self.assertEqual(settings.consultants_title, "مستشارون يستمعون قبل أن يوجّهوا")
		self.assertEqual(settings.testimonials_title, "كلمات شاركها مستفيدون سابقون")
		self.assertEqual(len(settings.journey_steps), 4)
		self.assertEqual(len(settings.faqs), 4)

		context = self._build_context("Guest", [])
		self.assertEqual(context.website.page_title, settings.page_title)
		self.assertEqual(context.title, settings.page_title)
		self.assertLessEqual(len(context.services), settings.services_limit)

	def test_only_approved_complete_consultant_profiles_are_public(self):
		suffix = frappe.generate_hash(length=8).upper()
		published_user = self._make_public_test_user(f"published-{suffix.lower()}@example.com")
		hidden_user = self._make_public_test_user(f"hidden-{suffix.lower()}@example.com")
		published = frappe.get_doc(
			{
				"doctype": "Consultant",
				"consultant_name": f"مستشار منشور {suffix}",
				"code": f"PUBLIC-{suffix}",
				"user": published_user,
				"active": 1,
				"show_on_website": 1,
				"public_title": "مستشار في الرفاه النفسي",
				"public_bio": "يقدم دعمًا مهنيًا يركز على بناء المهارات وفهم الاحتياج.",
				"specializations": "إدارة الضغوط، تطوير الذات",
			}
		).insert(ignore_permissions=True)
		hidden = frappe.get_doc(
			{
				"doctype": "Consultant",
				"consultant_name": f"مستشار غير منشور {suffix}",
				"code": f"HIDDEN-{suffix}",
				"user": hidden_user,
				"active": 1,
				"show_on_website": 0,
				"public_title": "مستشار",
				"public_bio": "نبذة غير مصرح بنشرها.",
			}
		).insert(ignore_permissions=True)

		result = _get_public_consultants(12)
		names = {row.name for row in result}
		self.assertIn(published.name, names)
		self.assertNotIn(hidden.name, names)
		public_row = next(row for row in result if row.name == published.name)
		self.assertEqual(public_row.specialty_tags, ["إدارة الضغوط", "تطوير الذات"])

	def test_only_consented_published_testimonials_are_public(self):
		suffix = frappe.generate_hash(length=8).upper()
		published = frappe.get_doc(
			{
				"doctype": "Rushd Testimonial",
				"quote": "ساعدتني الخطوات الواضحة على فهم ما أحتاج إليه.",
				"display_name": "مستفيد من رُشد",
				"service_label": "التوجيه الدراسي",
				"active": 1,
				"consent_confirmed": 1,
				"consent_date": frappe.utils.nowdate(),
				"source_reference": f"TEST-{suffix}",
				"sort_order": 1,
			}
		).insert(ignore_permissions=True)
		hidden = frappe.get_doc(
			{
				"doctype": "Rushd Testimonial",
				"quote": "هذا الرأي غير منشور.",
				"display_name": "مستفيد آخر",
				"active": 0,
				"consent_confirmed": 0,
			}
		).insert(ignore_permissions=True)

		result = _get_public_testimonials(12)
		names = {row.name for row in result}
		self.assertIn(published.name, names)
		self.assertNotIn(hidden.name, names)
		public_row = next(row for row in result if row.name == published.name)
		self.assertEqual(public_row.display_name, "مستفيد من رُشد")
		self.assertEqual(public_row.service_label, "التوجيه الدراسي")

	@staticmethod
	def _make_public_test_user(email):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "مستشار اختبار",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True).name

	def test_homepage_defaults_address_the_student_not_the_guardian(self):
		public_copy = " ".join(
			[
				TEXT_DEFAULTS["privacy_description"],
				*(row["description"] for row in TABLE_DEFAULTS["intro_promises"]),
				*(row["title"] for row in TABLE_DEFAULTS["privacy_items"]),
				*(row["question"] for row in TABLE_DEFAULTS["faqs"]),
			]
		)

		self.assertNotIn("ولي الأمر", public_copy)
		self.assertEqual(TEXT_DEFAULTS["guardian_label"], "فريق رُشد")

	def test_default_student_services_are_available(self):
		ensure_default_services()

		for service in DEFAULT_SERVICES:
			self.assertTrue(
				frappe.db.exists("Consultation Service", service["service_code"])
			)

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
		self.assertIn('"مساحات العمل المشتركة"', script)
		self.assertIn('"مساحاتي الخاصة"', script)
		self.assertIn("localizeWorkspaceSidebarSections", script)

	def test_advanced_permission_manager_uses_rushd_identity_and_arabic_copy(self):
		app_path = Path(__file__).parents[1]
		desk_script = (app_path / "public" / "js" / "rushd-rtl.js").read_text()
		rtl_styles = (app_path / "public" / "css" / "rushd-rtl.css").read_text()
		roles_page = (app_path / "www" / "admin" / "roles" / "index.html").read_text()

		self.assertIn("installPermissionManagerIdentity", desk_script)
		self.assertIn("applyRushdDeskBrand", desk_script)
		self.assertIn('"Role Permissions Manager": "مدير صلاحيات الأدوار"', desk_script)
		self.assertIn('"Frappe Framework": "منصة رُشد"', desk_script)
		self.assertIn("/assets/consultation_center/images/rushd-logo.svg", desk_script)
		self.assertIn("#page-permission-manager .rushd-permission-page-intro", rtl_styles)
		self.assertIn('href="/app/permission-manager"', roles_page)
		self.assertNotIn('href="/app/role-permission-manager"', roles_page)

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

	def test_arabic_font_does_not_flash_a_fallback_face(self):
		app_path = Path(__file__).parents[1]
		fonts_css = (app_path / "public" / "css" / "fonts.css").read_text()
		preloads = (
			app_path / "templates" / "includes" / "rushd_font_preload.html"
		).read_text()

		self.assertEqual(fonts_css.count("font-display: block"), 9)
		self.assertNotIn("font-display: swap", fonts_css)
		self.assertNotIn(".ttf')", fonts_css)
		self.assertIn("NotoKufiArabic-Regular.woff2", fonts_css)
		self.assertIn('rel="preload"', preloads)
		self.assertIn('type="font/woff2"', preloads)
		self.assertEqual(
			frappe.db.get_value("User", "Administrator", "full_name"),
			"مدير النظام",
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

	def test_user_profile_heatmap_is_contained_on_tablet_widths(self):
		rtl_path = Path(__file__).parents[1] / "public" / "css" / "rushd-rtl.css"
		rtl_styles = rtl_path.read_text()

		self.assertIn("#page-user-profile .performance-heatmap", rtl_styles)
		self.assertIn("overflow-x: auto;", rtl_styles)
		self.assertIn("@media (min-width: 768px) and (max-width: 1199px)", rtl_styles)

	def test_rushd_workspace_styles_match_the_actual_desk_route(self):
		rtl_path = Path(__file__).parents[1] / "public" / "css" / "rushd-rtl.css"
		script_path = Path(__file__).parents[1] / "public" / "js" / "rushd-rtl.js"
		rtl_styles = rtl_path.read_text()
		desk_script = script_path.read_text()

		self.assertIn("body[data-route='Workspaces/Rushd']", rtl_styles)
		self.assertIn("--rushd-admin-canvas: #f4f3ef;", rtl_styles)
		self.assertIn("--rushd-admin-accent: #0d9488;", rtl_styles)
		self.assertIn("background: var(--rushd-admin-accent-deep);", rtl_styles)
		self.assertIn(".rushd-ux-section-heading", rtl_styles)
		self.assertIn(".shortcut-widget-box", rtl_styles)
		self.assertIn(".quick-list-widget-box", rtl_styles)
		self.assertIn(".links-widget-box", rtl_styles)
		self.assertIn("decorateRushdWorkspace", desk_script)
		self.assertIn("ابدأ من المهمة التي تريد إنجازها", desk_script)
		self.assertIn("مسار الطلبات", desk_script)
		self.assertIn("التشغيل اليومي", desk_script)
		self.assertIn("قرارات تحتاج متابعة", desk_script)

	def _build_context(self, user, roles):
		frappe.set_user(user)
		self.addCleanup(frappe.set_user, "Administrator")
		with patch("consultation_center.www.index.frappe.get_roles", return_value=roles):
			context = frappe._dict()
			get_context(context)
		return context
