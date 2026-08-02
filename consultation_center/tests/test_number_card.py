from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.number_card import (
	_aggregate_fields,
	get_percentage_difference,
	get_result,
)


class TestNumberCardCompatibility(FrappeTestCase):
	def test_percentage_difference_uses_compatible_result_query(self):
		doc = frappe._dict(
			name="Total Website Users",
			show_percentage_stats=1,
			stats_time_interval="Daily",
		)

		with (
			patch("consultation_center.api.number_card.frappe.get_doc", return_value=doc),
			patch("consultation_center.api.number_card.get_result", return_value=2) as get_card_result,
		):
			percentage = get_percentage_difference(
				frappe._dict(name=doc.name),
				filters='[["User", "user_type", "=", "Website User"]]',
				result="3",
			)

		self.assertEqual(percentage, 50)
		get_card_result.assert_called_once()

	def test_frappe_16_uses_structured_aggregate_fields(self):
		with patch.object(frappe, "__version__", "16.22.0"):
			self.assertEqual(
				_aggregate_fields("COUNT", "*"),
				[{"COUNT": "*", "as": "result"}],
			)

	def test_frappe_15_uses_legacy_aggregate_fields(self):
		with patch.object(frappe, "__version__", "15.116.0"):
			self.assertEqual(
				_aggregate_fields("COUNT", "*"),
				["COUNT(*) as result"],
			)

	def test_website_user_count_executes_on_postgres(self):
		doc = frappe._dict(
			function="Count",
			aggregate_function_based_on="",
			document_type="User",
			parent_document_type="",
		)

		result = get_result(
			doc,
			filters=[["User", "user_type", "=", "Website User"]],
		)

		self.assertGreaterEqual(result, 0)

	def test_aggregate_query_orders_by_result_alias(self):
		doc = frappe._dict(
			function="Count",
			aggregate_function_based_on="",
			document_type="User",
			parent_document_type="",
		)

		with patch(
			"consultation_center.api.number_card.frappe.get_list",
			return_value=[{"result": 3}],
		) as get_list:
			result = get_result(
				doc,
				filters='[["User", "user_type", "=", "Website User"]]',
			)

		self.assertEqual(result, 3)
		self.assertEqual(get_list.call_args.kwargs["order_by"], "result")

	def test_empty_result_returns_zero(self):
		doc = frappe._dict(
			function="Count",
			aggregate_function_based_on="",
			document_type="User",
			parent_document_type="",
		)

		with patch("consultation_center.api.number_card.frappe.get_list", return_value=[]):
			self.assertEqual(get_result(doc, filters=[]), 0)
