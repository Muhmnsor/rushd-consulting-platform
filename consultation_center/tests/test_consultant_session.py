from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from consultation_center.api.consultant_portal import (
	record_appointment_attendance,
	save_session_documentation,
)
from consultation_center.api.staff_portal import review_consultation_session
from consultation_center.consultation_center.doctype.consultation_appointment.consultation_appointment import (
	WEEKDAYS,
)


class TestConsultantSessionWorkflow(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.consultant_user = cls._make_user(
			"rushd.session.consultant@example.com",
			"Consultant",
		)
		cls.other_consultant_user = cls._make_user(
			"rushd.session.other@example.com",
			"Consultant",
		)
		cls.supervisor_user = cls._make_user(
			"rushd.session.supervisor@example.com",
			"Consultation Supervisor",
		)
		cls.beneficiary_user = cls._make_user(
			"rushd.session.beneficiary@example.com",
			"Beneficiary",
		)
		cls.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": "اختبار توثيق الجلسة",
				"service_code": "_RUSHD-SESSION-WORKFLOW",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)
		cls.beneficiary = frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": "مستفيد اختبار الجلسة",
				"portal_user": cls.beneficiary_user,
			}
		).insert(ignore_permissions=True)
		cls.consultant = cls._make_consultant(
			"_RUSHD-SESSION-CONSULTANT",
			cls.consultant_user,
		)
		cls.other_consultant = cls._make_consultant(
			"_RUSHD-SESSION-OTHER",
			cls.other_consultant_user,
		)
		cls.case = frappe.get_doc(
			{
				"doctype": "Consultation Case",
				"beneficiary": cls.beneficiary.name,
				"service": cls.service.name,
				"case_owner": cls.supervisor_user,
				"supervisor": cls.supervisor_user,
				"primary_consultant": cls.consultant.name,
				"case_status": "Active",
			}
		).insert(ignore_permissions=True)

		cls.appointment_counter = 0
		for weekday in WEEKDAYS:
			frappe.get_doc(
				{
					"doctype": "Consultant Availability Rule",
					"consultant": cls.consultant.name,
					"weekday": weekday,
					"start_time": "00:00:00",
					"end_time": "23:59:59",
					"service": cls.service.name,
					"active": 1,
				}
			).insert(ignore_permissions=True)

	@staticmethod
	def _make_user(email, role):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "اختبار جلسة رُشد",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		user.add_roles(role)
		return user.name

	@classmethod
	def _make_consultant(cls, code, user):
		return frappe.get_doc(
			{
				"doctype": "Consultant",
				"consultant_name": code,
				"code": code,
				"user": user,
				"active": 1,
				"services": cls.service.name,
			}
		).insert(ignore_permissions=True)

	@classmethod
	def _make_appointment(cls):
		frappe.set_user("Administrator")
		cls.appointment_counter += 1
		start = now_datetime() - timedelta(days=cls.appointment_counter, hours=2)
		start = start.replace(minute=0, second=0, microsecond=0)
		return frappe.get_doc(
			{
				"doctype": "Consultation Appointment",
				"case": cls.case.name,
				"beneficiary": cls.beneficiary.name,
				"consultant": cls.consultant.name,
				"service": cls.service.name,
				"start_datetime": start,
				"status": "Confirmed",
				"delivery_mode": "Online",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_consultant_records_attendance_and_submits_separate_summaries(self):
		appointment = self._make_appointment()
		frappe.set_user(self.consultant_user)
		record_appointment_attendance(appointment.name, "Attended")

		result = save_session_documentation(
			appointment=appointment.name,
			topic="تنظيم الأولويات",
			goals_addressed="تحديد هدف أسبوعي",
			interventions="تمرين ترتيب البدائل",
			professional_notes="<b>ملاحظة مهنية داخلية</b>",
			beneficiary_summary="اتفقنا على خطوة عملية للأسبوع القادم.",
			guardian_summary_allowed=0,
			guardian_summary="يجب ألا يحفظ هذا النص",
			next_action="متابعة تنفيذ الخطوة",
			submit_for_review=1,
		)

		session = frappe.get_doc("Consultation Session", result["name"])
		appointment.reload()
		self.assertEqual(session.status, "Pending Review")
		self.assertEqual(session.professional_notes, "ملاحظة مهنية داخلية")
		self.assertEqual(session.guardian_summary, "")
		self.assertNotEqual(session.professional_notes, session.beneficiary_summary)
		self.assertEqual(appointment.created_session, session.name)

	def test_other_roles_cannot_record_or_read_professional_session(self):
		appointment = self._make_appointment()
		frappe.set_user(self.other_consultant_user)
		with self.assertRaises(frappe.PermissionError):
			record_appointment_attendance(appointment.name, "Attended")

		frappe.set_user(self.beneficiary_user)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Consultation Session", pluck="name")
		with self.assertRaises(frappe.PermissionError):
			review_consultation_session(
				session_name="SESSION-NOT-ALLOWED",
				decision="approve",
			)

	def test_approved_session_is_immutable(self):
		appointment = self._make_appointment()
		frappe.set_user(self.consultant_user)
		record_appointment_attendance(appointment.name, "Late")
		result = save_session_documentation(
			appointment=appointment.name,
			topic="جلسة مكتملة",
			professional_notes="توثيق مهني",
			beneficiary_summary="ملخص مبسط",
			submit_for_review=1,
		)

		frappe.set_user(self.supervisor_user)
		self.case.reload()
		completed_before = self.case.completed_sessions or 0
		review_consultation_session(
			session_name=result["name"],
			decision="approve",
			review_note="التوثيق مكتمل والملخصات منفصلة.",
		)
		session = frappe.get_doc("Consultation Session", result["name"])
		self.case.reload()
		self.assertEqual(session.status, "Approved")
		self.assertEqual(session.approved_by, self.supervisor_user)
		self.assertEqual(session.last_reviewed_by, self.supervisor_user)
		self.assertEqual(self.case.completed_sessions, completed_before + 1)

		session.topic = "محاولة تعديل بعد الاعتماد"
		with self.assertRaises(frappe.ValidationError):
			session.save(ignore_permissions=True)

	def test_supervisor_return_requires_reason_and_consultant_can_resubmit(self):
		appointment = self._make_appointment()
		frappe.set_user(self.consultant_user)
		record_appointment_attendance(appointment.name, "Attended")
		result = save_session_documentation(
			appointment=appointment.name,
			topic="جلسة تحتاج استكمالًا",
			professional_notes="توثيق أولي",
			beneficiary_summary="ملخص أولي",
			submit_for_review=1,
		)

		frappe.set_user(self.supervisor_user)
		with self.assertRaises(frappe.ValidationError):
			review_consultation_session(
				session_name=result["name"],
				decision="return",
				review_note="",
			)
		review_consultation_session(
			session_name=result["name"],
			decision="return",
			review_note="وضح المتابعة المهنية بصورة أدق.",
		)

		frappe.set_user(self.consultant_user)
		resubmitted = save_session_documentation(
			appointment=appointment.name,
			session_name=result["name"],
			topic="جلسة مكتملة بعد الإعادة",
			professional_notes="توثيق مهني مستكمل",
			follow_up="متابعة الإجراء في الجلسة القادمة",
			beneficiary_summary="ملخص مبسط مستكمل",
			submit_for_review=1,
		)
		self.assertEqual(resubmitted["status"], "Pending Review")
