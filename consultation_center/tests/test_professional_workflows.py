import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.professional_portal import (
	close_supervision_request,
	create_professional_escalation,
	create_supervision_request,
	respond_supervision_request,
	review_case_referral,
	save_case_referral,
	update_case_referral,
	update_professional_escalation,
)
from consultation_center.api.consultant_settings import (
	add_time_off,
	save_availability_rule,
	save_professional_profile,
	update_capacity,
)
from consultation_center.consultant_portal import get_current_consultant
from consultation_center.staff import get_supervised_cases
from consultation_center.www.consultant.professional_profile import get_context as get_profile_page_context


class TestProfessionalWorkflows(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.consultant_user = cls._make_user(
			"rushd.professional.consultant@example.com",
			"Consultant",
		)
		cls.other_consultant_user = cls._make_user(
			"rushd.professional.other-consultant@example.com",
			"Consultant",
		)
		cls.supervisor_user = cls._make_user(
			"rushd.professional.supervisor@example.com",
			"Consultation Supervisor",
		)
		cls.other_supervisor_user = cls._make_user(
			"rushd.professional.other-supervisor@example.com",
			"Consultation Supervisor",
		)
		cls.beneficiary_user = cls._make_user(
			"rushd.professional.beneficiary@example.com",
			"Beneficiary",
		)
		service_name = frappe.db.exists(
			"Consultation Service", {"service_code": "_RUSHD-PROFESSIONAL-WORKFLOW"}
		)
		cls.service = (
			frappe.get_doc("Consultation Service", service_name)
			if service_name
			else frappe.get_doc(
				{
					"doctype": "Consultation Service",
					"service_name": "اختبار التنسيق والإشراف",
					"service_code": "_RUSHD-PROFESSIONAL-WORKFLOW",
					"duration_minutes": 60,
					"active": 1,
				}
			).insert(ignore_permissions=True)
		)
		beneficiary_name = frappe.db.exists("Beneficiary", {"portal_user": cls.beneficiary_user})
		cls.beneficiary = (
			frappe.get_doc("Beneficiary", beneficiary_name)
			if beneficiary_name
			else frappe.get_doc(
				{
					"doctype": "Beneficiary",
					"beneficiary_name": "مستفيد اختبار التنسيق المهني",
					"portal_user": cls.beneficiary_user,
				}
			).insert(ignore_permissions=True)
		)
		cls.consultant = cls._make_consultant(
			"_RUSHD-PROFESSIONAL-CONSULTANT",
			cls.consultant_user,
		)
		cls.other_consultant = cls._make_consultant(
			"_RUSHD-PROFESSIONAL-OTHER",
			cls.other_consultant_user,
		)

	@staticmethod
	def _make_user(email, role):
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
			user.enabled = 1
			user.save(ignore_permissions=True)
			user.add_roles(role)
			return user.name
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "اختبار التنسيق المهني",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		user.add_roles(role)
		return user.name

	@classmethod
	def _make_consultant(cls, code, user):
		consultant_name = frappe.db.exists("Consultant", {"code": code})
		if consultant_name:
			doc = frappe.get_doc("Consultant", consultant_name)
			doc.update({"user": user, "active": 1, "services": cls.service.name})
			doc.save(ignore_permissions=True)
			return doc
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
	def _make_case(cls, supervisor=None):
		frappe.set_user("Administrator")
		return frappe.get_doc(
			{
				"doctype": "Consultation Case",
				"beneficiary": cls.beneficiary.name,
				"service": cls.service.name,
				"case_owner": supervisor or cls.supervisor_user,
				"supervisor": supervisor or cls.supervisor_user,
				"primary_consultant": cls.consultant.name,
				"case_status": "Active",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_external_referral_is_approved_and_followed_to_closure(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		referral = save_case_referral(
			case=case.name,
			referral_type="External",
			priority="High",
			referral_reason="<b>الحاجة إلى خدمة تخصصية مساندة</b>",
			target_organization="جهة تخصصية",
			organization_contact="هاتف الجهة",
			permitted_information="<p>الاسم وملخص سبب الإحالة فقط</p>",
			consent_confirmed=1,
			submit_for_approval=1,
		)
		self.assertEqual(referral["status"], "Pending Approval")

		frappe.set_user(self.supervisor_user)
		approved = review_case_referral(
			referral_name=referral["name"],
			decision="approve",
			supervisor_note="النطاق مناسب والموافقة مثبتة.",
		)
		self.assertEqual(approved["status"], "Approved")

		doc = frappe.get_doc("Case Referral", referral["name"])
		doc.permitted_information = "محاولة توسيع نطاق البيانات"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

		frappe.set_user(self.consultant_user)
		self.assertEqual(
			update_case_referral(
				referral_name=referral["name"],
				action="mark_sent",
				follow_up_note="تم إرسال الإحالة للجهة.",
			)["status"],
			"Sent",
		)
		self.assertEqual(
			update_case_referral(
				referral_name=referral["name"],
				action="start_follow_up",
				follow_up_note="تم تأكيد استلام الإحالة.",
			)["status"],
			"In Progress",
		)
		self.assertEqual(
			update_case_referral(
				referral_name=referral["name"],
				action="close",
				outcome="قُبل المستفيد وبدأت الخدمة المساندة.",
			)["status"],
			"Closed",
		)

	def test_external_referral_requires_consent_and_supervisor_scope(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		with self.assertRaises(frappe.ValidationError):
			save_case_referral(
				case=case.name,
				referral_type="External",
				referral_reason="إحالة خارجية",
				target_organization="جهة خارجية",
				permitted_information="ملخص الإحالة",
				submit_for_approval=1,
			)
		referral = save_case_referral(
			case=case.name,
			referral_type="Internal",
			referral_reason="تحويل إلى خدمة داخلية",
			target_service=self.service.name,
			permitted_information="بيانات الحالة الأساسية",
			submit_for_approval=1,
		)
		frappe.set_user(self.other_supervisor_user)
		with self.assertRaises(frappe.PermissionError):
			review_case_referral(
				referral_name=referral["name"],
				decision="approve",
			)

	def test_supervision_request_is_answered_by_assigned_supervisor(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		request = create_supervision_request(
			case=case.name,
			request_type="Ethical Consultation",
			supervision_question="<p>ما حدود المعلومات المناسبة للمشاركة؟</p>",
			priority="Urgent",
		)

		frappe.set_user(self.other_supervisor_user)
		with self.assertRaises(frappe.PermissionError):
			respond_supervision_request(
				request_name=request["name"],
				action="start_review",
			)

		frappe.set_user(self.supervisor_user)
		self.assertEqual(
			respond_supervision_request(
				request_name=request["name"],
				action="start_review",
			)["status"],
			"In Review",
		)
		self.assertEqual(
			respond_supervision_request(
				request_name=request["name"],
				action="answer",
				supervisor_response="<b>شارك الحد الأدنى اللازم فقط.</b>",
				required_action="توثيق نطاق المشاركة والموافقة.",
				follow_up_date="2026-08-15",
			)["status"],
			"Answered",
		)

		frappe.set_user(self.consultant_user)
		self.assertEqual(
			close_supervision_request(request_name=request["name"])["status"],
			"Closed",
		)
		doc = frappe.get_doc("Supervision Request", request["name"])
		self.assertEqual(doc.supervisor_response, "شارك الحد الأدنى اللازم فقط.")
		self.assertEqual(doc.responded_by, self.supervisor_user)

	def test_critical_escalation_requires_action_and_full_audit(self):
		case = self._make_case()
		frappe.set_user(self.consultant_user)
		with self.assertRaises(frappe.ValidationError):
			create_professional_escalation(
				case=case.name,
				alert_type="Safeguarding",
				severity="Critical",
				alert_summary="مؤشر حماية يستلزم تدخلاً عاجلاً.",
			)
		escalation = create_professional_escalation(
			case=case.name,
			alert_type="Safeguarding",
			severity="Critical",
			alert_summary="<b>مؤشر حماية يستلزم تدخلاً عاجلاً.</b>",
			immediate_action="تفعيل مسار الحماية وإبقاء التواصل متاحًا.",
			emergency_protocol_activated=1,
		)

		frappe.set_user(self.other_supervisor_user)
		with self.assertRaises(frappe.PermissionError):
			update_professional_escalation(
				escalation_name=escalation["name"],
				action="acknowledge",
			)

		frappe.set_user(self.supervisor_user)
		for action, expected in (
			("acknowledge", "Acknowledged"),
			("start_action", "Action In Progress"),
		):
			self.assertEqual(
				update_professional_escalation(
					escalation_name=escalation["name"],
					action=action,
					supervisor_action="تم التواصل وتفعيل الإجراء المتفق عليه.",
				)["status"],
				expected,
			)
		self.assertEqual(
			update_professional_escalation(
				escalation_name=escalation["name"],
				action="resolve",
				supervisor_action="اكتملت الاستجابة المهنية.",
				resolution_note="استقرت الحالة مع خطة متابعة يومية.",
				follow_up_date="2026-08-10",
			)["status"],
			"Resolved",
		)
		self.assertEqual(
			update_professional_escalation(
				escalation_name=escalation["name"],
				action="close",
				resolution_note="استقرت الحالة مع خطة متابعة يومية.",
			)["status"],
			"Closed",
		)
		doc = frappe.get_doc("Professional Escalation", escalation["name"])
		self.assertEqual(doc.reported_by, self.consultant_user)
		self.assertEqual(doc.last_action_by, self.supervisor_user)
		self.assertTrue(doc.emergency_protocol_activated)

	def test_records_are_private_and_supervisors_see_only_assigned_scope(self):
		case = self._make_case()
		other_case = self._make_case(self.other_supervisor_user)
		frappe.set_user(self.consultant_user)
		first = create_supervision_request(
			case=case.name,
			request_type="Case Guidance",
			supervision_question="طلب ضمن نطاق المشرف الأول.",
		)
		second = create_supervision_request(
			case=other_case.name,
			request_type="Case Guidance",
			supervision_question="طلب ضمن نطاق المشرف الآخر.",
		)

		frappe.set_user(self.supervisor_user)
		visible = frappe.get_list("Supervision Request", pluck="name")
		self.assertIn(first["name"], visible)
		self.assertNotIn(second["name"], visible)

		frappe.set_user(self.beneficiary_user)
		for doctype in (
			"Case Referral",
			"Supervision Request",
			"Professional Escalation",
		):
			with self.assertRaises(frappe.PermissionError):
				frappe.get_list(doctype, pluck="name")

		frappe.set_user(self.other_consultant_user)
		with self.assertRaises(frappe.PermissionError):
			close_supervision_request(request_name=first["name"])

	def test_consultant_updates_professional_profile_and_capacity(self):
		frappe.set_user(self.consultant_user)
		frappe.db.set_value(
			"Consultant",
			self.consultant.name,
			{"show_on_website": 1, "public_title": "", "public_bio": "", "profile_image": ""},
		)
		result = save_professional_profile(
			specializations="<b>الإرشاد الشبابي</b>\nالإرشاد الأسري",
			languages="العربية\nالإنجليزية",
			qualifications="ماجستير في الإرشاد\nدبلوم الإرشاد الأسري",
			experience_summary="خبرة في الاستشارات الفردية.",
			public_title="مستشار الإرشاد الشبابي",
			public_bio="خبرة مهنية في مساندة الشباب وبناء الخطط المناسبة.",
			profile_image="/files/consultant-profile.webp",
			licenses="اعتماد مهني تجريبي",
			suitable_groups="الشباب من 18 إلى 30 عامًا",
			credential_expiry="2027-08-30",
			development_requirements="استكمال عشر ساعات تطوير.",
			events_platform_url="https://events.example.com",
		)
		self.assertEqual(result["name"], self.consultant.name)
		self.assertTrue(result["requires_review"])
		update_capacity(
			maximum_daily_sessions=7,
			default_duration=50,
			buffer_before=10,
			buffer_after=5,
		)
		doc = frappe.get_doc("Consultant", self.consultant.name)
		self.assertEqual(doc.specializations, "الإرشاد الشبابي\nالإرشاد الأسري")
		self.assertEqual(doc.profile_image, "/files/consultant-profile.webp")
		self.assertEqual(doc.public_title, "مستشار الإرشاد الشبابي")
		self.assertFalse(doc.show_on_website)
		self.assertEqual(doc.maximum_daily_sessions, 7)
		self.assertEqual(doc.default_duration, 50)
		profile = get_current_consultant()
		self.assertEqual(profile.specialization_items, ["الإرشاد الشبابي", "الإرشاد الأسري"])
		self.assertEqual(profile.language_items, ["العربية", "الإنجليزية"])
		self.assertEqual(profile.qualification_items, ["ماجستير في الإرشاد", "دبلوم الإرشاد الأسري"])
		context = frappe._dict(boot=frappe._dict(lang="ar"))
		get_profile_page_context(context)
		html = frappe.render_template(
			"consultation_center/www/consultant/professional-profile.html",
			context,
		)
		self.assertIn("data-repeatable-field", html)
		self.assertIn("data-profile-image-file", html)
		self.assertIn("مستشار الإرشاد الشبابي", html)

	def test_consultant_manages_only_own_availability(self):
		frappe.set_user(self.consultant_user)
		rule = save_availability_rule(
			weekday="Sunday",
			start_time="09:00:00",
			end_time="13:00:00",
			slot_duration=50,
			delivery_mode="Both",
			capacity=1,
		)
		time_off = add_time_off(
			from_datetime="2027-09-01 09:00:00",
			to_datetime="2027-09-01 13:00:00",
			reason="<p>تطوير مهني</p>",
		)
		self.assertEqual(
			frappe.db.get_value("Consultant Availability Rule", rule["name"], "consultant"),
			self.consultant.name,
		)
		self.assertEqual(
			frappe.db.get_value("Consultant Time Off", time_off["name"], "reason"),
			"تطوير مهني",
		)
		frappe.set_user(self.other_consultant_user)
		with self.assertRaises(frappe.PermissionError):
			save_availability_rule(
				rule_name=rule["name"],
				weekday="Monday",
				start_time="10:00:00",
				end_time="12:00:00",
			)

	def test_supervisor_case_list_is_isolated_by_assignment(self):
		first = self._make_case(self.supervisor_user)
		second = self._make_case(self.other_supervisor_user)
		frappe.set_user(self.supervisor_user)
		visible = {row.name for row in get_supervised_cases(self.supervisor_user)}
		self.assertIn(first.name, visible)
		self.assertNotIn(second.name, visible)
