import frappe
from frappe import _
from frappe.model.document import Document


class AssessmentTemplate(Document):
	def validate(self):
		self.template_code = (self.template_code or "").strip().upper()
		self.template_title = (self.template_title or "").strip()
		if not self.template_code:
			frappe.throw(_("Assessment template code is required"))
		if self.minimum_age is not None and self.maximum_age is not None:
			if self.maximum_age < self.minimum_age:
				frappe.throw("العمر الأعلى يجب ألا يقل عن العمر الأدنى")
		if self.validation_status in {"Validated", "Licensed"} and not (
			self.reference_or_license or ""
		).strip():
			frappe.throw("أضف مرجع التحقق أو الترخيص قبل اعتماد حالة الأداة")
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
