from datetime import date, datetime
from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import flt


@frappe.whitelist()
def get_result(
	doc: str | dict[str, Any] | Document,
	filters: str | list | dict[str, Any],
	to_date: str | datetime | date | None = None,
):
	"""Return an aggregate Number Card result without PostgreSQL's invalid default order."""
	doc = frappe.parse_json(doc)
	sql_function_map = {
		"Count": "COUNT",
		"Sum": "SUM",
		"Average": "AVG",
		"Minimum": "MIN",
		"Maximum": "MAX",
	}

	function = sql_function_map[doc.function]
	argument = "*" if function == "COUNT" else doc.aggregate_function_based_on
	fields = _aggregate_fields(function, argument)

	if not filters:
		filters = []
	elif isinstance(filters, str):
		filters = frappe.parse_json(filters)

	if to_date:
		if isinstance(filters, dict):
			filters = {**filters, "creation": ["<", to_date]}
		else:
			filters.append([doc.document_type, "creation", "<", to_date])

	result = frappe.get_list(
		doc.document_type,
		fields=fields,
		filters=filters,
		parent_doctype=doc.parent_document_type,
		order_by="result",
	)

	return flt(result[0]["result"] if result else 0)


@frappe.whitelist()
def get_percentage_difference(
	doc: str | dict[str, Any],
	filters: str | list | dict[str, Any],
	result: float | int | str,
):
	"""Calculate Number Card trends through the PostgreSQL-safe aggregate query."""
	doc = frappe.parse_json(doc)
	result = frappe.parse_json(result)
	doc = frappe.get_doc("Number Card", doc.name)

	if not doc.get("show_percentage_stats"):
		return None

	previous_result = _calculate_previous_result(doc, filters)
	if previous_result == 0:
		return None
	if result == previous_result:
		return 0

	return ((result / previous_result) - 1) * 100.0


def _calculate_previous_result(doc, filters):
	from frappe.utils import add_to_date

	current_date = frappe.utils.now()
	if doc.stats_time_interval == "Daily":
		previous_date = add_to_date(current_date, days=-1)
	elif doc.stats_time_interval == "Weekly":
		previous_date = add_to_date(current_date, weeks=-1)
	elif doc.stats_time_interval == "Monthly":
		previous_date = add_to_date(current_date, months=-1)
	else:
		previous_date = add_to_date(current_date, years=-1)

	return get_result(doc, filters, previous_date)


def _aggregate_fields(function: str, argument: str):
	"""Use the aggregate field format supported by the installed Frappe major version."""
	try:
		frappe_major_version = int(str(getattr(frappe, "__version__", "16")).split(".", 1)[0])
	except ValueError:
		frappe_major_version = 16

	if frappe_major_version >= 16:
		return [{function: argument, "as": "result"}]

	return [f"{function}({argument}) as result"]
