import frappe
from frappe.model.document import Document


class RushdWebsiteSettings(Document):
	def on_update(self):
		frappe.clear_cache()
