import frappe
from frappe.model.document import Document

from consultation_center.user_roles import ensure_user_role


class Consultant(Document):
	def on_update(self):
		ensure_user_role(self.user, "Consultant")
