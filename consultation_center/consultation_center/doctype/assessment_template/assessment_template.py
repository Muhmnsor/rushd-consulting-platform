import frappe
from frappe import _
from frappe.model.document import Document


class AssessmentTemplate(Document):
	def validate(self):
		self.template_code = (self.template_code or "").strip().upper()
		self.template_title = (self.template_title or "").strip()
		if not self.template_code:
			frappe.throw(_("Assessment template code is required"))
		if self.current_published_version:
			version_template = frappe.db.get_value(
				"Assessment Version",
				self.current_published_version,
				"assessment_template",
			)
			if version_template != self.name:
				frappe.throw(_("Published version must belong to the same assessment template"))

	def on_trash(self):
		if frappe.db.exists("Assessment Version", {"assessment_template": self.name}):
			frappe.throw(_("Assessment templates with versions cannot be deleted"))
