import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.staff_portal import (
	assign_consultation_request,
	review_consultation_request,
	triage_consultation_request,
)
from consultation_center.consultant_portal import (
	get_consultant_case_detail,
	get_consultant_cases,
)


class TestStaffPortalWorkflow(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.operations_user = cls._make_user(
			"rushd.operations.workflow@example.com",
			"Intake Coordinator",
		)
		cls.supervisor_user = cls._make_user(
			"rushd.supervisor.workflow@example.com",
			"Consultation Supervisor",
		)
		cls.beneficiary_user = cls._make_user(
			"rushd.beneficiary.workflow@example.com",
			"Beneficiary",
		)
		cls.consultant_user = cls._make_user(
			"rushd.consultant.workflow@example.com",
			"Consultant",
		)
		cls.service = frappe.get_doc(
			{
				"doctype": "Consultation Service",
				"service_name": "Rushd Staff Workflow Test",
				"service_code": "_RUSHD-STAFF-WORKFLOW",
				"duration_minutes": 60,
				"active": 1,
			}
		).insert(ignore_permissions=True)
		cls.beneficiary = frappe.get_doc(
			{
				"doctype": "Beneficiary",
				"beneficiary_name": "Staff Workflow Beneficiary",
				"portal_user": cls.beneficiary_user,
			}
		).insert(ignore_permissions=True)
		cls.consultant = frappe.get_doc(
			{
				"doctype": "Consultant",
				"consultant_name": "مستشار اختبار مسار العمل",
				"code": "_RUSHD-STAFF-WORKFLOW-CONSULTANT",
				"user": cls.consultant_user,
				"active": 1,
				"services": cls.service.name,
			}
		).insert(ignore_permissions=True)

	@staticmethod
	def _make_user(email, role):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Rushd Workflow Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		user.add_roles(role)
		return user.name

	@classmethod
	def _make_request(cls, workflow_state="Submitted"):
		frappe.set_user("Administrator")
		return frappe.get_doc(
			{
				"doctype": "Consultation Request",
				"beneficiary": cls.beneficiary.name,
				"requested_service": cls.service.name,
				"workflow_state": workflow_state,
				"source": "Portal",
				"summary": "Request used to verify the staff portal workflow.",
				"preferred_mode": "Either",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_operations_moves_complete_request_to_triage(self):
		request_doc = self._make_request()
		frappe.set_user(self.operations_user)

		review_consultation_request(
			request_name=request_doc.name,
			action="start_review",
			operations_note="Verified the required fields.",
		)
		review_consultation_request(
			request_name=request_doc.name,
			action="send_to_triage",
			operations_note="Ready for professional triage.",
		)

		request_doc.reload()
		self.assertEqual(request_doc.workflow_state, "Ready for Triage")
		self.assertEqual(request_doc.assigned_coordinator, self.operations_user)

	def test_supervisor_records_separate_internal_and_public_notes(self):
		request_doc = self._make_request("Ready for Triage")
		frappe.set_user(self.supervisor_user)

		triage_consultation_request(
			request_name=request_doc.name,
			decision="not_eligible",
			triage_note="Internal professional rationale.",
			beneficiary_note="هذه الخدمة لا تطابق احتياجك الحالي، وسنتواصل لشرح البدائل.",
		)

		request_doc.reload()
		self.assertEqual(request_doc.workflow_state, "Not Eligible")
		self.assertEqual(request_doc.eligibility_status, "Not Eligible")
		self.assertEqual(request_doc.triage_note, "Internal professional rationale.")
		self.assertNotEqual(request_doc.triage_note, request_doc.beneficiary_action_note)

	def test_beneficiary_cannot_call_staff_action(self):
		request_doc = self._make_request()
		frappe.set_user(self.beneficiary_user)

		with self.assertRaises(frappe.PermissionError):
			review_consultation_request(
				request_name=request_doc.name,
				action="start_review",
			)

	def test_supervisor_creates_and_assigns_case_once(self):
		request_doc = self._make_request("Eligible")
		frappe.set_user(self.supervisor_user)

		result = assign_consultation_request(
			request_name=request_doc.name,
			consultant=self.consultant.name,
			priority="High",
		)

		request_doc.reload()
		case_doc = frappe.get_doc("Consultation Case", result["case"])
		self.assertEqual(request_doc.workflow_state, "Converted to Case")
		self.assertEqual(request_doc.linked_case, case_doc.name)
		self.assertEqual(case_doc.primary_consultant, self.consultant.name)
		self.assertEqual(case_doc.case_status, "Assigned")
		self.assertEqual(case_doc.priority, "High")

		case_count = frappe.db.count(
			"Consultation Case",
			{"beneficiary": self.beneficiary.name, "service": self.service.name},
		)
		repeated = assign_consultation_request(
			request_name=request_doc.name,
			consultant=self.consultant.name,
			priority="High",
		)
		self.assertEqual(repeated["case"], case_doc.name)
		self.assertEqual(
			frappe.db.count(
				"Consultation Case",
				{"beneficiary": self.beneficiary.name, "service": self.service.name},
			),
			case_count,
		)

	def test_assigned_case_appears_only_in_consultant_portal_scope(self):
		request_doc = self._make_request("Eligible")
		frappe.set_user(self.supervisor_user)
		result = assign_consultation_request(
			request_name=request_doc.name,
			consultant=self.consultant.name,
		)

		frappe.set_user(self.consultant_user)
		cases = get_consultant_cases(self.consultant.name)
		self.assertIn(result["case"], [row.name for row in cases])
		detail = get_consultant_case_detail(self.consultant.name, result["case"])
		self.assertEqual(detail.beneficiary, self.beneficiary.name)

	def test_beneficiary_cannot_assign_case(self):
		request_doc = self._make_request("Eligible")
		frappe.set_user(self.beneficiary_user)

		with self.assertRaises(frappe.PermissionError):
			assign_consultation_request(
				request_name=request_doc.name,
				consultant=self.consultant.name,
			)
