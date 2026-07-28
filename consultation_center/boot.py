import frappe
from frappe import _
from frappe.translate import get_user_lang

from consultation_center.permissions import has_admin_app_access


def add_rushd_display_translations(bootinfo):
	"""Expose translated DocType and module names without changing their stored values."""
	if (
		frappe.session.user == "Guest"
		or not get_user_lang().startswith("ar")
		or not has_admin_app_access()
		or bootinfo.get("rushd_display_translations")
	):
		return

	values = set()
	for row in frappe.get_all("DocType", fields=["name", "module"]):
		values.add(row.name)
		values.add(row.module)

	translated_values = {}
	for value in sorted(values):
		translated_value = _(value)
		if translated_value and translated_value != value:
			translated_values[value] = translated_value

	bootinfo["rushd_display_translations"] = translated_values
