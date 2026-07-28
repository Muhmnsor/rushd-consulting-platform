import csv
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.desk.desktop import get_desktop_page
from frappe.tests.utils import FrappeTestCase

from consultation_center.boot import add_rushd_display_translations
from consultation_center.permissions import has_admin_app_access


APP_ROOT = Path(__file__).parents[1]
WORKSPACE_PATH = (
	APP_ROOT
	/ "consultation_center"
	/ "workspace"
	/ "rushd"
	/ "rushd.json"
)


class TestRushdWorkspace(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")

	def test_workspace_blocks_have_matching_widgets(self):
		workspace = json.loads(WORKSPACE_PATH.read_text())
		content = json.loads(workspace["content"])

		self.assertEqual(workspace["name"], "Rushd")
		self.assertEqual(workspace["title"], "Rushd")
		self.assertEqual(workspace["label"], "Rushd")

		shortcut_names = {item["label"] for item in workspace["shortcuts"]}
		quick_list_names = {item["label"] for item in workspace["quick_lists"]}
		card_names = {
			item["label"]
			for item in workspace["links"]
			if item["type"] == "Card Break"
		}

		for block in content:
			data = block["data"]
			if block["type"] == "shortcut":
				self.assertIn(data["shortcut_name"], shortcut_names)
			elif block["type"] == "quick_list":
				self.assertIn(data["quick_list_name"], quick_list_names)
			elif block["type"] == "card":
				self.assertIn(data["card_name"], card_names)

	def test_workspace_filters_and_destinations_are_valid(self):
		workspace = json.loads(WORKSPACE_PATH.read_text())

		for shortcut in workspace["shortcuts"]:
			if shortcut["type"] == "URL":
				self.assertTrue(shortcut["url"].startswith("/"))
				continue

			self.assertTrue(frappe.db.exists("DocType", shortcut["link_to"]))
			filters = json.loads(shortcut.get("stats_filter") or "{}")
			frappe.db.count(shortcut["link_to"], filters=filters)

		for quick_list in workspace["quick_lists"]:
			self.assertTrue(frappe.db.exists("DocType", quick_list["document_type"]))
			frappe.db.get_all(
				quick_list["document_type"],
				filters=json.loads(quick_list["quick_list_filter"]),
				limit=1,
			)

	def test_live_workspace_payload_contains_operational_sections(self):
		payload = get_desktop_page(
			json.dumps(
				{
					"name": "Rushd",
					"title": "Rushd",
					"public": 1,
				}
			)
		)

		self.assertGreaterEqual(len(payload["shortcuts"]["items"]), 11)
		self.assertGreaterEqual(len(payload["cards"]["items"]), 5)
		self.assertEqual(len(payload["quick_lists"]["items"]), 2)

	def test_administration_app_is_separate_from_role_portals(self):
		self.assertTrue(has_admin_app_access())

		frappe.set_user("beneficiary@example.com")
		with patch("consultation_center.permissions._roles", return_value={"Beneficiary"}):
			self.assertFalse(has_admin_app_access())

	def test_bootinfo_includes_arabic_labels_for_raw_doctype_list_values(self):
		bootinfo = frappe._dict()
		with (
			patch("consultation_center.boot.get_user_lang", return_value="ar"),
			patch(
				"consultation_center.boot.frappe.get_all",
				return_value=[
					frappe._dict(name="Guardian", module="Consultation Center"),
				],
			),
			patch(
				"consultation_center.boot._",
				side_effect={
					"Guardian": "ولي الأمر أو الممثل",
					"Consultation Center": "إدارة رُشد",
				}.get,
			),
		):
			add_rushd_display_translations(bootinfo)

		self.assertEqual(
			bootinfo.rushd_display_translations,
			{
				"Consultation Center": "إدارة رُشد",
				"Guardian": "ولي الأمر أو الممثل",
			},
		)

	def test_attached_page_english_chrome_has_arabic_translations(self):
		required = {
			"About",
			"Apps",
			"Add Row",
			"Alerts and Notifications",
			"Are you sure you want to log out?",
			"Back to Login",
			"Begin typing for results.",
			"Build",
			"Clear Cache",
			"Clear all filters",
			"Components to build your app",
			"Create Blogger",
			"Create Entry",
			"Create a {0} Account",
			"Delete",
			"Documents",
			"Duplicate",
			"Deleted Documents",
			"Edit",
			"Email",
			"Email Address",
			"Events",
			"Filter By",
			"Forgot Password",
			"Forgot Password?",
			"Frappe Support",
			"Get started",
			"Help",
			"Hide",
			"Hide Saved",
			"ID",
			"Integrations",
			"Import Data",
			"Keyboard Shortcuts",
			"Last Updated On",
			"List View",
			"Login",
			"Login to {0}",
			"Login with Email Link",
			"Login with Frappe Cloud",
			"Login with LDAP",
			"Login with {0}",
			"Log out",
			"Models",
			"My Profile",
			"My Settings",
			"Navigate to main content",
			"New",
			"No New notifications",
			"No Data to Show",
			"No Upcoming Events",
			"No activities to show",
			"No new notifications",
			"Nothing New",
			"Notifications",
			"Personal",
			"Public",
			"Rank",
			"Monthly Rank",
			"Recent Activity",
			"Reload",
			"Reports & Masters",
			"Reset Password",
			"Rushd",
			"Save Filter",
			"Send login link",
			"Session Defaults",
			"Show",
			"Show More Activity",
			"Sign Up",
			"Sign up",
			"Tags",
			"Toggle Full Width",
			"Toggle Section: {0}",
			"Toggle Theme",
			"Tools",
			"Type Distribution",
			"Users",
			"Verification Code",
			"View Website",
			"Website",
			"What's New",
			"You have unseen notifications",
			"Your Shortcuts",
			"or",
		}
		with (APP_ROOT / "translations" / "ar.csv").open(newline="") as translations_file:
			translated = {row[0] for row in csv.reader(translations_file) if row}

		self.assertTrue(required <= translated)

	def test_admin_shell_localizes_hardcoded_and_dynamic_frappe_text(self):
		rtl_script = (APP_ROOT / "public" / "js" / "rushd-rtl.js").read_text()

		for source_text in (
			"Begin typing for results.",
			"Clear all filters",
			"Grid Empty State",
			"Reports & Masters",
			"Search or type a command ({0})",
			"Toggle Section: {0}",
		):
			self.assertIn(source_text, rtl_script)

		self.assertIn("MutationObserver", rtl_script)
		self.assertIn("FIELD_VALUE_TRANSLATIONS", rtl_script)
		self.assertIn("INLINE_TRANSLATIONS", rtl_script)
		self.assertIn("installDeskBackButton", rtl_script)
		self.assertIn("navigateDeskBack", rtl_script)
		self.assertIn("separatorIndex", rtl_script)
		self.assertIn("rushd_display_translations", rtl_script)
		self.assertIn("website_theme", rtl_script)
		self.assertIn("frappe._messages", rtl_script)
