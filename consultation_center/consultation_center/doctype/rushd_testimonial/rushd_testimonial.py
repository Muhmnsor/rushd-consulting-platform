import re

import frappe
from frappe.model.document import Document
from frappe.utils import strip_html_tags


CONTACT_PATTERN = re.compile(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\+?\d[\d\s()-]{7,}\d))")


class RushdTestimonial(Document):
	def validate(self):
		self.quote = strip_html_tags(self.quote or "").strip()
		self.display_name = strip_html_tags(self.display_name or "").strip() or "مستفيد من رُشد"
		self.service_label = strip_html_tags(self.service_label or "").strip()
		self.source_reference = strip_html_tags(self.source_reference or "").strip()
		self.sort_order = max(0, int(self.sort_order or 0))

		if len(self.quote) > 600:
			frappe.throw("نص الرأي أطول من الحد المسموح وهو 600 حرف")
		if len(self.display_name) > 100:
			frappe.throw("الاسم الظاهر أطول من الحد المسموح")
		if CONTACT_PATTERN.search(f"{self.display_name} {self.quote}"):
			frappe.throw("احذف البريد الإلكتروني أو رقم التواصل من النص العام حفاظًا على الخصوصية")
		if self.active and not self.consent_confirmed:
			frappe.throw("أكد موافقة المستفيد قبل نشر الرأي")
		if self.active and not self.consent_date:
			frappe.throw("حدد تاريخ موافقة المستفيد قبل نشر الرأي")
