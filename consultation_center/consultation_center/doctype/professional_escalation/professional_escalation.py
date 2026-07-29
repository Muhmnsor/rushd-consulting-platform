import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

SUPERVISOR_ROLES = {"System Manager", "Center Director", "Consultation Supervisor"}


class ProfessionalEscalation(Document):
	def before_insert(self):
		self.reported_by = self.reported_by or frappe.session.user
		self.reported_on = self.reported_on or now_datetime()

	def validate(self):
		case = frappe.db.get_value(
			"Consultation Case",
			self.case,
			["beneficiary", "primary_consultant", "supervisor"],
			as_dict=True,
		)
		if not case:
			frappe.throw(_("Consultation case was not found"))
		if case.beneficiary != self.beneficiary:
			frappe.throw(_("Escalation beneficiary must match the consultation case"))
		if case.primary_consultant != self.consultant:
			frappe.throw(_("Escalation consultant must match the assigned case consultant"))
		if case.supervisor and self.assigned_supervisor != case.supervisor:
			frappe.throw(_("Escalation must be assigned to the case supervisor"))
		if not (self.alert_summary or "").strip():
			frappe.throw(_("Escalation summary is required"))
		if self.severity == "Critical" and not (self.immediate_action or "").strip():
			frappe.throw(_("Immediate action is required for a critical escalation"))
		self._validate_transition()

	def _validate_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status != "Open":
				frappe.throw(_("A new escalation must start as open"))
			return
		if previous.status in {"Closed", "Cancelled"}:
			frappe.throw(_("A closed escalation is immutable"))
		allowed = {
			"Open": {"Open", "Acknowledged", "Action In Progress", "Cancelled"},
			"Acknowledged": {"Acknowledged", "Action In Progress", "Resolved", "Cancelled"},
			"Action In Progress": {"Action In Progress", "Resolved", "Cancelled"},
			"Resolved": {"Resolved", "Closed"},
		}
		if self.status not in allowed.get(previous.status, {previous.status}):
			frappe.throw(_("Invalid escalation status transition"))
		if self.status != previous.status:
			_require_supervisor()
			self.last_action_by = frappe.session.user
			self.last_action_on = now_datetime()
			if self.status == "Resolved" and not (self.resolution_note or "").strip():
				frappe.throw(_("Resolution note is required"))

	def on_trash(self):
		frappe.throw(_("Escalations cannot be deleted; close or cancel them instead"))


def _require_supervisor():
	roles = set(frappe.get_roles(frappe.session.user))
	if frappe.session.user != "Administrator" and not roles & SUPERVISOR_ROLES:
		frappe.throw(_("Only a supervisor can update an escalation"), frappe.PermissionError)
