import frappe
from frappe import _
from frappe.model.document import Document


class BeneficiaryTask(Document):
	def validate(self):
		plan = frappe.db.get_value(
			"Consultation Plan",
			self.plan,
			["case", "beneficiary", "consultant", "status"],
			as_dict=True,
		)
		if not plan or plan.status != "Active":
			frappe.throw(_("Tasks can only be added to an active consultation plan"))
		if (
			plan.case != self.case
			or plan.beneficiary != self.beneficiary
			or plan.consultant != self.consultant
		):
			frappe.throw(_("Task details do not match the consultation plan"))

	def on_trash(self):
		frappe.throw(_("Tasks cannot be deleted; cancel the task instead"))
