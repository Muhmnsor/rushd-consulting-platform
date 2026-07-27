import frappe
from frappe.model.document import Document

from consultation_center.user_roles import ensure_user_role


class Beneficiary(Document):
	def validate(self):
		if self.portal_user:
			linked_profile = frappe.db.get_value(
				"Beneficiary",
				{"portal_user": self.portal_user, "name": ["!=", self.name or ""]},
				"name",
			)
			if linked_profile:
				frappe.throw("Portal User is already linked to another beneficiary")

	def on_update(self):
		ensure_user_role(self.portal_user, "Beneficiary")
