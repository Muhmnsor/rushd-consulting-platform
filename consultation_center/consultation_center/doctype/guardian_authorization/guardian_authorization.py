import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class GuardianAuthorization(Document):
	def validate(self):
		self._validate_dates()
		self._validate_scope()
		self._validate_duplicate_active_authorization()

	def _validate_dates(self):
		if self.effective_from and self.effective_to:
			if getdate(self.effective_to) < getdate(self.effective_from):
				frappe.throw(_("Effective To cannot be before Effective From"))

		if self.authorization_status == "Active" and self.effective_to:
			if getdate(self.effective_to) < getdate(nowdate()):
				self.authorization_status = "Expired"

	def _validate_scope(self):
		scope_fields = (
			"can_view_profile",
			"can_view_requests",
			"can_view_case",
			"can_manage_appointments",
			"can_view_reports",
		)
		if self.authorization_status == "Active" and not any(self.get(field) for field in scope_fields):
			frappe.throw(_("Select at least one authorization scope"))

	def _validate_duplicate_active_authorization(self):
		if self.authorization_status != "Active":
			return

		existing = frappe.db.exists(
			"Guardian Authorization",
			{
				"guardian": self.guardian,
				"beneficiary": self.beneficiary,
				"authorization_status": "Active",
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(_("An active authorization already exists for this guardian and beneficiary"))
