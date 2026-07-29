import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

SUPERVISOR_ROLES = {"System Manager", "Center Director", "Consultation Supervisor"}


class SupervisionRequest(Document):
	def before_insert(self):
		self.requested_by = self.requested_by or frappe.session.user
		self.requested_on = self.requested_on or now_datetime()

	def validate(self):
		case = frappe.db.get_value(
			"Consultation Case",
			self.case,
			["primary_consultant", "supervisor"],
			as_dict=True,
		)
		if not case:
			frappe.throw(_("Consultation case was not found"))
		if case.primary_consultant != self.consultant:
			frappe.throw(_("Supervision request consultant must match the assigned case consultant"))
		if case.supervisor and self.supervisor != case.supervisor:
			frappe.throw(_("Supervision request must be assigned to the case supervisor"))
		if not (self.supervision_question or "").strip():
			frappe.throw(_("Supervision question is required"))
		self._validate_transition()

	def _validate_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Draft", "Submitted"}:
				frappe.throw(_("A new supervision request must start as draft or submitted"))
			return
		if previous.status in {"Closed", "Cancelled"}:
			frappe.throw(_("A closed supervision request is immutable"))
		allowed = {
			"Draft": {"Draft", "Submitted", "Cancelled"},
			"Submitted": {"Submitted", "In Review", "Answered", "Cancelled"},
			"In Review": {"In Review", "Answered", "Cancelled"},
			"Answered": {"Answered", "Closed"},
		}
		if self.status not in allowed.get(previous.status, {previous.status}):
			frappe.throw(_("Invalid supervision request status transition"))
		if self.status in {"In Review", "Answered"} and self.status != previous.status:
			_require_supervisor()
			if self.status == "Answered" and not (self.supervisor_response or "").strip():
				frappe.throw(_("Supervisor response is required"))
			self.responded_by = frappe.session.user
			self.responded_on = now_datetime()

	def on_trash(self):
		frappe.throw(_("Supervision requests cannot be deleted; cancel them instead"))


def _require_supervisor():
	roles = set(frappe.get_roles(frappe.session.user))
	if frappe.session.user != "Administrator" and not roles & SUPERVISOR_ROLES:
		frappe.throw(_("Only a supervisor can respond to a supervision request"), frappe.PermissionError)
