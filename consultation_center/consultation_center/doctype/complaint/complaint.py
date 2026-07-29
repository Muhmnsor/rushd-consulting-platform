import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class Complaint(Document):
	def before_insert(self):
		self.complainant = self.complainant or frappe.session.user
		self.submitted_on = self.submitted_on or now_datetime()

	def validate(self):
		if not (self.details or "").strip():
			frappe.throw(_("Complaint details are required"))
		previous = self.get_doc_before_save()
		if previous and previous.status in {"Resolved", "Closed"} and self.status != previous.status:
			frappe.throw(_("A closed complaint is immutable"))
		if self.status == "Resolved" and not (self.public_response or "").strip():
			frappe.throw(_("A public response is required before resolving a complaint"))
		if previous and self.status in {"Resolved", "Closed"} and self.status != previous.status:
			self.resolved_on = now_datetime()

	def on_trash(self):
		frappe.throw(_("Complaints cannot be deleted; close them instead"))
