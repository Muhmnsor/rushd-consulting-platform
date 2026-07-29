import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

SUPERVISOR_ROLES = {"System Manager", "Center Director", "Consultation Supervisor"}


class CaseReferral(Document):
	def before_insert(self):
		self.created_by = self.created_by or frappe.session.user
		self.created_on = self.created_on or now_datetime()

	def validate(self):
		self._validate_scope()
		self._validate_required_details()
		self._validate_transition()

	def _validate_scope(self):
		case = frappe.db.get_value(
			"Consultation Case",
			self.case,
			["beneficiary", "primary_consultant"],
			as_dict=True,
		)
		if not case:
			frappe.throw(_("Consultation case was not found"))
		if case.beneficiary != self.beneficiary:
			frappe.throw(_("Referral beneficiary must match the consultation case"))
		if case.primary_consultant != self.consultant:
			frappe.throw(_("Referral consultant must match the assigned case consultant"))

	def _validate_required_details(self):
		if self.status == "Pending Approval":
			if not (self.referral_reason or "").strip():
				frappe.throw(_("Referral reason is required before submission"))
			if not (self.permitted_information or "").strip():
				frappe.throw(_("Specify the information permitted for referral"))
			if self.referral_type == "External" and not self.consent_confirmed:
				frappe.throw(_("Beneficiary consent must be confirmed for an external referral"))
			if self.referral_type == "External" and not (self.target_organization or "").strip():
				frappe.throw(_("External referral organization is required"))

	def _validate_transition(self):
		previous = self.get_doc_before_save()
		if not previous:
			if self.status not in {"Draft", "Pending Approval"}:
				frappe.throw(_("A new referral must start as draft or pending approval"))
			return
		if previous.status in {"Closed", "Cancelled"}:
			frappe.throw(_("A closed referral is immutable"))
		allowed = {
			"Draft": {"Draft", "Pending Approval", "Cancelled"},
			"Pending Approval": {"Pending Approval", "Approved", "Returned", "Cancelled"},
			"Returned": {"Returned", "Draft", "Pending Approval", "Cancelled"},
			"Approved": {"Approved", "Sent", "Cancelled"},
			"Sent": {"Sent", "In Progress", "Closed", "Cancelled"},
			"In Progress": {"In Progress", "Closed", "Cancelled"},
		}
		if self.status not in allowed.get(previous.status, {previous.status}):
			frappe.throw(_("Invalid referral status transition"))
		if self.status in {"Approved", "Returned"} and self.status != previous.status:
			_require_supervisor()
			if self.status == "Returned" and not (self.supervisor_note or "").strip():
				frappe.throw(_("A return reason is required"))
			self.reviewed_by = frappe.session.user
			self.reviewed_on = now_datetime()
		if previous.status in {"Approved", "Sent", "In Progress"}:
			for fieldname in (
				"referral_type",
				"referral_reason",
				"target_organization",
				"target_service",
				"permitted_information",
				"consent_confirmed",
			):
				if self.has_value_changed(fieldname):
					frappe.throw(_("Approved referral scope cannot be changed"))

	def on_trash(self):
		frappe.throw(_("Referrals cannot be deleted; cancel them instead"))


def _require_supervisor():
	roles = set(frappe.get_roles(frappe.session.user))
	if frappe.session.user != "Administrator" and not roles & SUPERVISOR_ROLES:
		frappe.throw(_("Only a supervisor can review a referral"), frappe.PermissionError)
