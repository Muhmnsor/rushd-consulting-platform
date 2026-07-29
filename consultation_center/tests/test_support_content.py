import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.support_portal import create_complaint, create_support_ticket


class TestSupportContent(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.user = cls._user("rushd.support.beneficiary@example.com", "Beneficiary")
		cls.other = cls._user("rushd.support.other@example.com", "Beneficiary")
		cls.beneficiary = frappe.get_doc({"doctype":"Beneficiary","beneficiary_name":"مستفيد الدعم","portal_user":cls.user}).insert(ignore_permissions=True)
		frappe.get_doc({"doctype":"Beneficiary","beneficiary_name":"مستفيد دعم آخر","portal_user":cls.other}).insert(ignore_permissions=True)

	@staticmethod
	def _user(email, role):
		user = frappe.get_doc({"doctype":"User","email":email,"first_name":"اختبار الدعم","enabled":1,"send_welcome_email":0,"user_type":"Website User"}).insert(ignore_permissions=True)
		user.add_roles(role)
		return user.name

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_beneficiary_creates_private_support_and_complaint(self):
		frappe.set_user(self.user)
		ticket = create_support_ticket("Access Issue","تعذر الدخول","<b>تظهر رسالة عند الدخول</b>")
		complaint = create_complaint("Confidential Complaint","<p>شكوى سرية عن الخدمة</p>")
		self.assertEqual(frappe.db.get_value("Support Ticket",ticket["name"],"description"),"تظهر رسالة عند الدخول")
		self.assertEqual(frappe.db.get_value("Complaint",complaint["name"],"confidentiality"),"Confidential")
		frappe.set_user(self.other)
		self.assertNotIn(ticket["name"], frappe.get_list("Support Ticket", pluck="name"))
		self.assertNotIn(complaint["name"], frappe.get_list("Complaint", pluck="name"))

	def test_resolution_requires_public_response_and_records_audit(self):
		frappe.set_user(self.user)
		result = create_complaint("Suggestion","اقتراح لتحسين تجربة الموعد")
		frappe.set_user("Administrator")
		doc = frappe.get_doc("Complaint", result["name"])
		doc.status = "Resolved"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		doc.reload()
		doc.status = "Resolved"
		doc.public_response = "شكرًا، تم اعتماد التحسين."
		doc.save(ignore_permissions=True)
		self.assertIsNotNone(doc.resolved_on)

	def test_published_content_is_managed_separately(self):
		frappe.set_user("Administrator")
		resource = frappe.get_doc({"doctype":"Resource Content","title":"دليل الاستعداد للجلسة","content_type":"Guide","audience":"Beneficiary","summary":"خطوات مبسطة قبل الموعد","active":1}).insert(ignore_permissions=True)
		announcement = frappe.get_doc({"doctype":"Internal Announcement","title":"تحديث أوقات الدعم","audience":"All","summary":"تم تحديث أوقات الاستجابة","active":1}).insert(ignore_permissions=True)
		self.assertTrue(resource.active)
		self.assertTrue(announcement.active)
