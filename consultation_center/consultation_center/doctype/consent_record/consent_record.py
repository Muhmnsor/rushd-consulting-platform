import frappe
from frappe import _
from frappe.model.document import Document


class ConsentRecord(Document):
	def validate(self):
		version_template = frappe.db.get_value(
			"Consent Version",
			self.consent_version,
			"consent_template",
		)
		if version_template != self.consent_template:
			frappe.throw(_("Consent version does not belong to the selected template"))

		if self.consent_role == "Guardian" and not self.guardian:
			frappe.throw(_("Guardian is required for guardian consent"))
		if self.status == "Granted" and not self.granted_by:
			frappe.throw(_("Granted By is required for granted consent"))

		previous = self.get_doc_before_save()
		if previous and previous.status == "Granted" and self.status not in {"Granted", "Withdrawn"}:
			frappe.throw(_("Granted consent can only remain granted or be withdrawn"))

	def on_trash(self):
		frappe.throw(_("Consent records cannot be deleted; withdraw or expire the record instead"))
