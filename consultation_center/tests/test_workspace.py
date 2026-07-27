import csv
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.desk.desktop import get_desktop_page
from frappe.tests.utils import FrappeTestCase

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
		self.assertEqual(workspace["title"], "لوحة إدارة رُشد")
		self.assertEqual(workspace["label"], "رُشد")

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
					"title": "لوحة إدارة رُشد",
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

	def test_attached_page_english_chrome_has_arabic_translations(self):
		required = {
			"About",
			"Apps",
			"Begin typing for results.",
			"Build",
			"Components to build your app",
			"Delete",
			"Documents",
			"Duplicate",
			"Edit",
			"Events",
			"Forgot Password",
			"Frappe Support",
			"Get started",
			"Help",
			"Hide",
			"Integrations",
			"Keyboard Shortcuts",
			"Login",
			"Log out",
			"My Profile",
			"My Settings",
			"Navigate to main content",
			"New",
			"No New notifications",
			"No Upcoming Events",
			"No new notifications",
			"Nothing New",
			"Notifications",
			"Personal",
			"Public",
			"Reload",
			"Reports & Masters",
			"Rushd",
			"Session Defaults",
			"Sign Up",
			"Toggle Full Width",
			"Toggle Theme",
			"Tools",
			"Users",
			"View Website",
			"Website",
			"What's New",
			"You have unseen notifications",
			"Your Shortcuts",
		}
		with (APP_ROOT / "translations" / "ar.csv").open(newline="") as translations_file:
			translated = {row[0] for row in csv.reader(translations_file) if row}

		self.assertTrue(required <= translated)
