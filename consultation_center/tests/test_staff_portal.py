import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.staff_portal import (
	review_consultation_request,
	triage_consultation_request,
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

