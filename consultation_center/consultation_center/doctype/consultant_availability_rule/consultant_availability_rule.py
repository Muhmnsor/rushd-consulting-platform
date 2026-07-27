import frappe
from frappe import _
from frappe.model.document import Document


class ConsultantAvailabilityRule(Document):
	def validate(self):
		if self.start_time and self.end_time and self.start_time >= self.end_time:
			frappe.throw(_("End Time must be after Start Time"))
