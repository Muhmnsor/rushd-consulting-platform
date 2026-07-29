import json
from pathlib import Path

import frappe
from frappe.exceptions import Redirect
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from consultation_center.api.admin_portal import (
	create_assessment,
	onboard_beneficiary,
	onboard_consultant,
)
from consultation_center.api.admin_records import (
	delete_admin_record,
	get_admin_record,
	get_resource_ui_schema,
	save_admin_record,
)
from consultation_center.staff import get_staff_display_name


class TestAdminPortal(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		suffix = frappe.generate_hash(length=8).upper()
		self.suffix = suffix
		self.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": f"خدمة اختبار الإدارة {suffix}",
				"service_code": f"_ADMIN-{suffix}",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_admin_routes_use_task_pages_instead_of_desk_redirects(self):
		app_path = Path(frappe.get_app_path("consultation_center"))
		hooks = (app_path / "hooks.py").read_text()
		admin_page = (app_path / "www" / "admin" / "index.py").read_text()
		staff_template = (app_path / "templates" / "rushd_staff.html").read_text()

		self.assertNotIn('{"from_route": "/admin"', hooks)
		self.assertIn("build_admin_context", admin_page)
		self.assertNotIn('redirect_admin("/app/rushd")', admin_page)
		self.assertIn("<small>{{ display_name }}</small>", staff_template)
		for page in (
			"users",
			"roles",
			"security",
			"services",
			"consents",
			"forms",
			"website",
			"announcements",
			"resources",
			"message-templates",
			"privacy",
			"audit",
			"complaints",
			"integrations",
		):
			page_source = (app_path / "www" / "admin" / page / "index.py").read_text()
			self.assertTrue(
				"build_admin_context" in page_source
				or "build_admin_catalog_context" in page_source
			)
			self.assertNotIn("redirect_admin", page_source)

	def test_generic_administrator_title_is_not_used_as_person_name(self):
		username = f"account-{self.suffix.lower()}"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"{username}@example.com",
				"first_name": "مدير النظام",
				"username": username,
				"enabled": 1,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(get_staff_display_name(user.name), username)

	def test_onboard_beneficiary_can_create_initial_request(self):
		result = onboard_beneficiary(
			beneficiary_name=f"مستفيد الإدارة {self.suffix}",
			mobile="0500000000",
			service=self.service.name,
			urgency="High",
			summary="طلب أنشئ من معالج الإدارة المبسّط.",
		)

		beneficiary = frappe.get_doc("Beneficiary", result["name"])
		request = frappe.get_doc("Consultation Request", result["request"])
		self.assertEqual(beneficiary.beneficiary_name, f"مستفيد الإدارة {self.suffix}")
		self.assertEqual(request.beneficiary, beneficiary.name)
		self.assertEqual(request.requested_service, self.service.name)
		self.assertEqual(request.workflow_state, "Submitted")

	def test_onboard_consultant_connects_account_service_and_availability(self):
		email = f"admin.consultant.{self.suffix.lower()}@example.com"
		result = onboard_consultant(
			consultant_name=f"مستشار الإدارة {self.suffix}",
			email=email,
			services=[self.service.name],
			maximum_daily_sessions=5,
			weekday="Sunday",
			start_time="09:00",
			end_time="14:00",
		)

		consultant = frappe.get_doc("Consultant", result["name"])
		self.assertTrue(consultant.code.startswith("CONS-"))
		self.assertEqual(consultant.user, email)
		self.assertIn(self.service.name, consultant.services)
		self.assertEqual(consultant.maximum_daily_sessions, 5)
		self.assertTrue(
			frappe.db.exists(
				"Consultant Availability Rule",
				{"consultant": consultant.name, "weekday": "Sunday"},
			)
		)

	def test_create_assessment_builds_first_version_and_questions(self):
		result = create_assessment(
			template_title=f"مقياس الإدارة {self.suffix}",
			category="اختبار",
			questions=[
				{
					"question_code": "Q1",
					"question_text": "كيف تقيّم شعورك اليوم؟",
					"response_type": "Scale",
					"minimum_value": 0,
					"maximum_value": 5,
				}
			],
		)

		version = frappe.get_doc("Assessment Version", result["version"])
		self.assertTrue(result["name"].startswith("ASM-"))
		self.assertEqual(version.assessment_template, result["name"])
		self.assertEqual(version.status, "Draft")
		self.assertEqual(len(version.questions), 1)
		self.assertEqual(version.questions[0].question_text, "كيف تقيّم شعورك اليوم؟")

	def test_create_assessment_keeps_methodology_scoring_and_option_rules(self):
		result = create_assessment(
			template_title=f"أداة شاملة {self.suffix}",
			template_code=f"_METHOD-{self.suffix}",
			instrument_kind="Outcome Measure",
			intended_use="متابعة التغير في المهارات دون تشخيص.",
			validation_status="Content Reviewed",
			responder="Guardian",
			timeframe="خلال الأسبوعين الماضيين",
			scoring_method="Average",
			minimum_answered_percent=75,
			missing_answer_policy="Exclude Missing",
			interpretation_rules="13-17 | 0-49 | يحتاج متابعة\n13-17 | 50-100 | تقدم ملحوظ",
			questions=[
				{
					"question_code": "D1",
					"question_text": "يبدأ المهام دون تذكير متكرر",
					"dimension": "المبادرة",
					"response_type": "Parent/Proxy Item",
					"weight": 2,
					"options": "دائمًا | 4\nأحيانًا | 2\nغير متأكد | | مستبعد",
				}
			],
		)

		template = frappe.get_doc("Assessment Template", result["name"])
		version = frappe.get_doc("Assessment Version", result["version"])
		self.assertEqual(template.instrument_kind, "Outcome Measure")
		self.assertEqual(template.validation_status, "Content Reviewed")
		self.assertEqual(version.scoring_method, "Average")
		self.assertEqual(version.minimum_answered_percent, 75)
		self.assertEqual(
			json.loads(version.interpretation_rules_json)[1]["label"],
			"تقدم ملحوظ",
		)
		self.assertEqual(version.questions[0].dimension, "المبادرة")
		options = json.loads(version.questions[0].options_json)
		self.assertEqual(options[0]["score"], 4)
		self.assertTrue(options[2]["excluded"])

	def test_catalog_can_create_edit_and_delete_announcement(self):
		title = f"إعلان تشغيل {self.suffix}"
		created = save_admin_record(
			"announcements",
			{
				"title": title,
				"audience": "Operations",
				"priority": "High",
				"active": 1,
				"summary": "تعليمات تشغيلية لاختبار الواجهة الجديدة.",
				"content": "تفاصيل الإعلان",
			},
		)
		self.assertTrue(frappe.db.exists("Internal Announcement", created["name"]))

		record = get_admin_record("announcements", created["name"])
		self.assertEqual(record["values"]["audience"], "Operations")
		save_admin_record(
			"announcements",
			{
				"title": title,
				"audience": "Operations",
				"priority": "Urgent",
				"active": 0,
				"summary": "تم تحديث التعليمات من الواجهة المبسطة.",
				"content": "",
			},
			name=created["name"],
		)
		updated = frappe.get_doc("Internal Announcement", created["name"])
		self.assertEqual(updated.priority, "Urgent")
		self.assertFalse(updated.active)

		delete_admin_record("announcements", created["name"])
		self.assertFalse(frappe.db.exists("Internal Announcement", created["name"]))

	def test_catalog_can_update_and_delete_unlinked_service(self):
		result = save_admin_record(
			"services",
			{
				"service_name": f"خدمة عمليات {self.suffix}",
				"active": 1,
				"duration_minutes": 45,
				"delivery_modes": "Both",
			},
		)
		self.assertTrue(result["name"].startswith("SRV-"))
		save_admin_record(
			"services",
			{
				"service_name": f"خدمة عمليات {self.suffix}",
				"service_code": result["name"],
				"active": 1,
				"duration_minutes": 75,
				"delivery_modes": "Online",
			},
			name=result["name"],
		)
		self.assertEqual(
			frappe.db.get_value("Consultation Service", result["name"], "duration_minutes"),
			75,
		)
		delete_admin_record("services", result["name"])
		self.assertFalse(frappe.db.exists("Consultation Service", result["name"]))

	def test_consent_template_code_is_generated_automatically(self):
		result = save_admin_record(
			"consents",
			{
				"template_title": f"نموذج تلقائي {self.suffix}",
				"consent_scope": "General",
				"active": 1,
				"requires_beneficiary": 1,
			},
		)
		self.assertTrue(result["name"].startswith("CONSENT-"))
		delete_admin_record("consents", result["name"])

	def test_sensitive_catalogs_do_not_offer_hard_delete(self):
		privacy = get_resource_ui_schema("privacy")
		complaints = get_resource_ui_schema("complaints")
		self.assertTrue(privacy.can_edit)
		self.assertFalse(privacy.can_create)
		self.assertFalse(privacy.can_delete)
		self.assertFalse(complaints.can_delete)
		with self.assertRaises(frappe.ValidationError):
			delete_admin_record("complaints", "COMP-NOT-REAL")

	def test_privacy_action_withdraws_consent_and_keeps_audit_record(self):
		beneficiary = frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": f"مستفيد موافقة {self.suffix}",
			}
		).insert(ignore_permissions=True)
		template = frappe.get_doc(
			{
				"doctype": "Consent Template",
				"template_code": f"_PRIVACY-{self.suffix}",
				"template_title": f"موافقة خصوصية {self.suffix}",
			}
		).insert(ignore_permissions=True)
		version = frappe.get_doc(
			{
				"doctype": "Consent Version",
				"consent_template": template.name,
				"version_label": f"1-{self.suffix}",
				"status": "Draft",
				"effective_from": nowdate(),
				"title": "نسخة اختبار",
				"simplified_text": "نص مبسط للاختبار.",
				"full_text": "نص كامل للاختبار.",
			}
		).insert(ignore_permissions=True)
		consent = frappe.get_doc(
			{
				"doctype": "Consent Record",
				"consent_template": template.name,
				"consent_version": version.name,
				"beneficiary": beneficiary.name,
				"consent_role": "Beneficiary",
				"status": "Pending",
			}
		).insert(ignore_permissions=True)

		save_admin_record(
			"privacy",
			{
				"status": "Withdrawn",
				"withdrawal_reason": "طلب المستفيد سحب الموافقة.",
			},
			name=consent.name,
		)
		consent.reload()
		self.assertEqual(consent.status, "Withdrawn")
		self.assertEqual(consent.withdrawal_reason, "طلب المستفيد سحب الموافقة.")
		self.assertTrue(consent.withdrawn_at)
		with self.assertRaises(frappe.ValidationError):
			delete_admin_record("privacy", consent.name)

	def test_complaint_can_be_created_and_resolved_but_not_deleted(self):
		created = save_admin_record(
			"complaints",
			{
				"complaint_type": "Service Feedback",
				"confidentiality": "Standard",
				"priority": "Normal",
				"status": "Submitted",
				"details": "بلاغ تجريبي للتحقق من مسار المعالجة الجديد.",
			},
		)
		save_admin_record(
			"complaints",
			{
				"complaint_type": "Service Feedback",
				"confidentiality": "Standard",
				"priority": "Normal",
				"status": "Resolved",
				"details": "بلاغ تجريبي للتحقق من مسار المعالجة الجديد.",
				"action_taken": "تمت مراجعة الحالة.",
				"public_response": "تمت معالجة البلاغ وإبلاغ صاحبه.",
			},
			name=created["name"],
		)
		self.assertEqual(
			frappe.db.get_value("Complaint", created["name"], "status"),
			"Resolved",
		)
		with self.assertRaises(frappe.ValidationError):
			delete_admin_record("complaints", created["name"])

	def test_catalog_rejects_invalid_select_values(self):
		with self.assertRaises(frappe.ValidationError):
			save_admin_record(
				"announcements",
				{
					"title": f"إعلان غير صالح {self.suffix}",
					"audience": "Unknown Audience",
					"summary": "يجب ألا يُحفظ.",
				},
			)

	def test_non_admin_cannot_use_admin_onboarding(self):
		frappe.set_user("Guest")
		with self.assertRaises(Redirect):
			onboard_beneficiary(beneficiary_name="مستفيد غير مصرح")
