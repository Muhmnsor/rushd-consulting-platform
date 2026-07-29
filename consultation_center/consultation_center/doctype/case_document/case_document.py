import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class CaseDocument(Document):
	def before_insert(self):
		self.uploaded_by = self.uploaded_by or frappe.session.user
		self.uploaded_on = self.uploaded_on or now_datetime()

	def validate(self):
		case = frappe.db.get_value("Consultation Case", self.case, ["beneficiary","primary_consultant"], as_dict=True)
		if not case or case.beneficiary != self.beneficiary:
			frappe.throw(_("Case document scope does not match the consultation case"))

	def on_trash(self):
		frappe.throw(_("Case documents cannot be deleted; archive them instead"))
