import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class SupportTicket(Document):
	def before_insert(self):
		self.requester = self.requester or frappe.session.user
		self.opened_on = self.opened_on or now_datetime()

	def validate(self):
		if not (self.subject or "").strip() or not (self.description or "").strip():
			frappe.throw(_("Support ticket subject and description are required"))
		previous = self.get_doc_before_save()
		if previous and previous.status in {"Resolved", "Closed"} and self.status != previous.status:
			frappe.throw(_("A closed support ticket is immutable"))
		if self.status == "Resolved" and not (self.public_response or "").strip():
			frappe.throw(_("A public response is required before resolving support"))
		if previous and self.status != previous.status and self.status in {"Resolved", "Closed"}:
			self.resolved_by = frappe.session.user
			self.resolved_on = now_datetime()

	def on_trash(self):
		frappe.throw(_("Support tickets cannot be deleted; close them instead"))
