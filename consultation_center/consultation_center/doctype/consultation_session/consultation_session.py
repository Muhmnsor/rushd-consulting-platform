import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime, time_diff_in_seconds

REVIEW_ROLES = {"System Manager", "Center Director", "Consultation Supervisor"}


class ConsultationSession(Document):
	def before_insert(self):
		self.documented_by = self.documented_by or frappe.session.user
		self.documented_on = self.documented_on or now_datetime()

	def validate(self):
		self.validate_case_scope()
		self.validate_appointment_scope()
		self.set_duration()
		self.validate_status_transition()

	def validate_case_scope(self):
		case = frappe.db.get_value(
			"Consultation Case",
			self.case,
			["beneficiary", "service", "primary_consultant"],
			as_dict=True,
		)
		if not case:
			frappe.throw(_("Consultation case was not found"))
		if case.primary_consultant != self.consultant:
			frappe.throw(_("Session consultant must match the assigned case consultant"))
		if case.beneficiary != self.beneficiary or case.service != self.service:
			frappe.throw(_("Session details do not match the consultation case"))

	def validate_appointment_scope(self):
		if not self.appointment:
			return
		appointment = frappe.db.get_value(
			"Consultation Appointment",
			self.appointment,
			["case", "beneficiary", "consultant", "service"],
			as_dict=True,
		)
		if not appointment:
			frappe.throw(_("Consultation appointment was not found"))
		if (
			appointment.case != self.case
			or appointment.beneficiary != self.beneficiary
			or appointment.consultant != self.consultant
			or appointment.service != self.service
		):
			frappe.throw(_("Session details do not match the appointment"))

	def set_duration(self):
		if not self.actual_start or not self.actual_end:
			return
		start = get_datetime(self.actual_start)
		end = get_datetime(self.actual_end)
		if end <= start:
			frappe.throw(_("Session end must be after its start"))
		self.duration_minutes = int(time_diff_in_seconds(end, start) / 60)

	def validate_status_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Draft", "Pending Review"}:
				frappe.throw(_("A new session must start as a draft or pending review"))
			return

		if previous.status == "Approved":
			frappe.throw(_("An approved session cannot be edited; create a formal revision"))

		allowed = {
			"Draft": {"Draft", "Pending Review", "Cancelled"},
			"Pending Review": {"Pending Review", "Approved", "Returned", "Cancelled"},
			"Returned": {"Returned", "Draft", "Pending Review", "Cancelled"},
			"Cancelled": {"Cancelled"},
		}
		if self.status not in allowed.get(previous.status, {previous.status}):
			frappe.throw(_("Invalid session status transition"))

		if (
			self.status in {"Approved", "Returned"}
			and self.status != previous.status
		):
			roles = set(frappe.get_roles(frappe.session.user))
			if frappe.session.user != "Administrator" and not roles & REVIEW_ROLES:
				frappe.throw(
					_("Only a supervisor can review a session"),
					frappe.PermissionError,
				)
			if self.status == "Returned" and not (self.review_note or "").strip():
				frappe.throw(_("A return reason is required"))
			self.last_reviewed_by = frappe.session.user
			self.last_reviewed_on = now_datetime()

		if self.status == "Approved" and previous.status != "Approved":
			self.approved_by = frappe.session.user
			self.approved_on = now_datetime()

	def on_trash(self):
		frappe.throw(_("Session records cannot be deleted; cancel or revise the record instead"))
