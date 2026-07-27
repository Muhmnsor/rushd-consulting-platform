import frappe
from frappe import _
from frappe.model.document import Document


class ConsultantTimeOff(Document):
	def validate(self):
		if self.from_datetime and self.to_datetime and self.from_datetime >= self.to_datetime:
			frappe.throw(_("'To' must be after 'From'"))
