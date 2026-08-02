from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from consultation_center.api.number_card import get_result


class TestNumberCardCompatibility(FrappeTestCase):
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
