import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip_html_tags


class ConsentVersion(Document):
	def validate(self):
		self._validate_unique_version()
		self._protect_published_content()
		self.content_hash = self._content_hash()

	def _validate_unique_version(self):
		existing = frappe.db.exists(
			"Consent Version",
			{
				"consent_template": self.consent_template,
				"version_label": self.version_label,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(_("This consent version already exists"))

	def _protect_published_content(self):
		if self.is_new():
			return
		previous = self.get_doc_before_save()
		if not previous or previous.status != "Published":
			return

		if self.status not in {"Published", "Retired"}:
			frappe.throw(_("A published consent version can only be retired"))

		protected_fields = ("title", "simplified_text", "full_text", "effective_from")
		if any(self.get(field) != previous.get(field) for field in protected_fields):
			frappe.throw(_("Published consent content is immutable; create a new version"))

	def _content_hash(self):
		content = "\n".join(
			(
				self.title or "",
				strip_html_tags(self.simplified_text or ""),
				strip_html_tags(self.full_text or ""),
				str(self.effective_from or ""),
			)
		)
		return hashlib.sha256(content.encode()).hexdigest()
