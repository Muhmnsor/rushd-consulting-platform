"""Assessment response parsing, scoring, and safety-rule evaluation.

Automated scores are operational follow-up indicators. Safety items are deliberately
excluded from ordinary scores and are returned as alerts for professional action.
"""

import json
from dataclasses import dataclass

import frappe
from frappe.utils import cint, flt


NUMERIC_TYPES = {
	"Scale",
	"Likert Agreement",
	"Frequency",
	"Frequency Scale",
	"Intensity",
	"Intensity Scale",
	"Difficulty",
	"Difficulty Scale",
	"Confidence",
	"Confidence Scale",
	"Numeric Rating",
	"Semantic Differential",
	"Number",
	"Goal Rating",
}
SINGLE_OPTION_TYPES = {
	"Yes/No",
	"Single Select",
	"Scenario Based",
	"Parent/Proxy Item",
	"Observer Item",
}
STRUCTURED_TYPES = {"Multi Select", "Ranking", "Matrix"}
SUPPORTED_RESPONSE_TYPES = NUMERIC_TYPES | SINGLE_OPTION_TYPES | STRUCTURED_TYPES | {"Open Text"}


@dataclass
class ScoredAnswer:
	answer_value: str
	answer_label: str
	raw_score: float | None
	normalized_score: float | None
	excluded: bool
	safety_triggered: bool


def parse_json_list(value, label="القيم"):
	if not value:
		return []
	if isinstance(value, list):
		return value
	try:
		parsed = json.loads(value)
	except (TypeError, ValueError):
		frappe.throw(f"{label} غير صالحة")
	if not isinstance(parsed, list):
		frappe.throw(f"{label} يجب أن تكون قائمة")
	return parsed


def question_options(question):
	options = parse_json_list(getattr(question, "options_json", None), "خيارات السؤال")
	cleaned = []
	for index, option in enumerate(options, 1):
		if not isinstance(option, dict):
			frappe.throw(f"الخيار {index} في السؤال {question.question_code} غير صالح")
		value = str(option.get("value", "")).strip()
		label = str(option.get("label") or value).strip()
		if not value or not label:
			frappe.throw(f"الخيار {index} في السؤال {question.question_code} يحتاج قيمة ونصًا")
		cleaned.append(
			{
				"value": value,
				"label": label,
				"score": option.get("score"),
				"excluded": bool(cint(option.get("excluded"))),
				"critical": bool(cint(option.get("critical"))),
			}
		)
	return cleaned


def is_question_applicable(question, answers):
	depends_on = str(getattr(question, "condition_question_code", "") or "").strip().upper()
	if not depends_on:
		return True
	actual = answers.get(depends_on)
	expected = str(getattr(question, "condition_value", "") or "")
	operator = getattr(question, "condition_operator", None) or "Equals"
	actual_values = _answer_values(actual)
	if operator == "Contains":
		return expected in actual_values
	if operator == "Not Equals":
		return expected not in actual_values
	return expected in actual_values


def score_answer(question, answer):
	answer_value = _serialize_answer(answer)
	response_type = question.response_type
	options = question_options(question)
	critical_values = {
		str(value) for value in parse_json_list(getattr(question, "critical_values_json", None), "القيم الحرجة")
	}
	answer_values = _answer_values(answer)
	safety_triggered = bool(
		cint(getattr(question, "is_safety_item", 0))
		and (
			critical_values.intersection(answer_values)
			or any(
				option["critical"] and option["value"] in answer_values
				for option in options
			)
		)
	)

	# Safety and descriptive items never enter the ordinary numerical result.
	if cint(getattr(question, "is_safety_item", 0)) or not cint(getattr(question, "scored", 1)):
		return ScoredAnswer(
			answer_value,
			_answer_label(answer, options),
			None,
			None,
			True,
			safety_triggered,
		)

	if response_type in SINGLE_OPTION_TYPES and options:
		option = next((row for row in options if row["value"] in answer_values), None)
		if not option:
			frappe.throw(f"إجابة السؤال {question.question_code} ليست ضمن الخيارات المتاحة")
		if option["excluded"] or option["score"] in (None, ""):
			return ScoredAnswer(answer_value, option["label"], None, None, True, safety_triggered)
		raw = flt(option["score"])
		minimum, maximum = _option_score_range(
			options,
			flt(question.minimum_value),
			flt(question.maximum_value),
		)
		normalized = _normalize(raw, minimum, maximum, bool(question.reverse_scored))
		return ScoredAnswer(answer_value, option["label"], raw, normalized, False, safety_triggered)

	if response_type == "Multi Select":
		selected = [row for row in options if row["value"] in answer_values and not row["excluded"]]
		scored = [flt(row["score"]) for row in selected if row["score"] not in (None, "")]
		if not scored:
			return ScoredAnswer(answer_value, _answer_label(answer, options), None, None, True, safety_triggered)
		minimum, maximum = _option_score_range(
			options,
			flt(question.minimum_value),
			flt(question.maximum_value),
		)
		raw = sum(scored) / len(scored)
		return ScoredAnswer(
			answer_value,
			_answer_label(answer, options),
			raw,
			_normalize(raw, minimum, maximum, bool(question.reverse_scored)),
			False,
			safety_triggered,
		)

	if response_type == "Matrix":
		matrix = _parse_structured_answer(answer, dict)
		values = []
		for value in matrix.values():
			try:
				values.append(float(value))
			except (TypeError, ValueError):
				frappe.throw(f"إجابة السؤال {question.question_code} غير صالحة")
		if not values:
			return ScoredAnswer(answer_value, answer_value, None, None, True, safety_triggered)
		raw = sum(values) / len(values)
		minimum, maximum = flt(question.minimum_value), flt(question.maximum_value)
		_validate_range(question, values, minimum, maximum)
		return ScoredAnswer(
			answer_value,
			"؛ ".join(f"{key}: {value}" for key, value in matrix.items()),
			raw,
			_normalize(raw, minimum, maximum, bool(question.reverse_scored)),
			False,
			safety_triggered,
		)

	if response_type in {"Open Text", "Ranking"}:
		return ScoredAnswer(
			answer_value,
			_answer_label(answer, options),
			None,
			None,
			True,
			safety_triggered,
		)

	if response_type == "Yes/No":
		text = next(iter(answer_values), "")
		if text not in {"0", "1", "No", "no", "لا", "Yes", "yes", "نعم"}:
			frappe.throw(f"إجابة السؤال {question.question_code} غير صالحة")
		raw = 1.0 if text in {"1", "Yes", "yes", "نعم"} else 0.0
		return ScoredAnswer(
			answer_value,
			"نعم" if raw else "لا",
			raw,
			_normalize(raw, 0, 1, bool(question.reverse_scored)),
			False,
			safety_triggered,
		)

	if response_type not in NUMERIC_TYPES:
		frappe.throw(f"نوع إجابة السؤال {question.question_code} غير مدعوم")
	try:
		raw = float(str(answer).strip())
	except (TypeError, ValueError):
		frappe.throw(f"إجابة السؤال {question.question_code} غير صالحة")
	minimum, maximum = flt(question.minimum_value), flt(question.maximum_value)
	_validate_range(question, [raw], minimum, maximum)
	return ScoredAnswer(
		answer_value,
		f"{raw:g}",
		raw,
		_normalize(raw, minimum, maximum, bool(question.reverse_scored)),
		False,
		safety_triggered,
	)


def calculate_submission(version, answers):
	applicable = [question for question in version.questions if is_question_applicable(question, answers)]
	rows = []
	dimensions = {}
	alerts = []
	for question in applicable:
		answer = answers.get(question.question_code)
		if _is_empty(answer):
			continue
		scored = score_answer(question, answer)
		weight = max(flt(question.weight), 0) or 1
		weighted = scored.normalized_score * weight if scored.normalized_score is not None else 0
		row = {
			"question_code": question.question_code,
			"question_text": question.question_text,
			"dimension": question.dimension or "عام",
			"response_type": question.response_type,
			"answer_value": scored.answer_value,
			"answer_label": scored.answer_label,
			"raw_score": scored.raw_score,
			"numeric_score": scored.normalized_score,
			"weighted_score": weighted,
			"excluded_from_score": scored.excluded,
			"safety_triggered": scored.safety_triggered,
		}
		rows.append(row)
		if scored.normalized_score is not None and not scored.excluded:
			bucket = dimensions.setdefault(question.dimension or "عام", {"weighted": 0, "weight": 0, "count": 0})
			bucket["weighted"] += weighted
			bucket["weight"] += weight
			bucket["count"] += 1
		if scored.safety_triggered:
			alerts.append(
				{
					"question_code": question.question_code,
					"question_text": question.question_text,
					"answer_label": scored.answer_label,
					"action": question.critical_action or "التواصل الفوري وفق بروتوكول الحماية المعتمد.",
				}
			)

	scored_rows = [row for row in rows if not row["excluded_from_score"]]
	weights = {question.question_code: max(flt(question.weight), 0) or 1 for question in applicable}
	total_weight = sum(weights[row["question_code"]] for row in scored_rows)
	weighted_total = sum(row["weighted_score"] for row in scored_rows)
	percentage = round(weighted_total / total_weight, 2) if total_weight else 0
	raw_values = [row["raw_score"] for row in scored_rows if row["raw_score"] is not None]
	method = version.scoring_method or "Percentage"
	if method == "No Automated Score":
		raw_score, percentage = 0, 0
	elif method == "Average":
		raw_score = round(sum(raw_values) / len(raw_values), 4) if raw_values else 0
	elif method == "Percentage":
		raw_score = percentage
	else:
		raw_score = round(sum(raw_values), 4)

	dimension_scores = {
		name: {
			"percentage": round(values["weighted"] / values["weight"], 2),
			"answered": values["count"],
		}
		for name, values in dimensions.items()
		if values["weight"]
	}
	return {
		"rows": rows,
		"applicable_questions": applicable,
		"answered_count": len(rows),
		"scored_count": len(scored_rows),
		"raw_score": raw_score,
		"percentage_score": percentage,
		"dimension_scores": dimension_scores,
		"alerts": alerts,
	}


def validate_completion(version, result, answers):
	for question in result["applicable_questions"]:
		if question.required and _is_empty(answers.get(question.question_code)):
			frappe.throw("أجب عن جميع الأسئلة المطلوبة قبل الإرسال")
	applicable_count = len(result["applicable_questions"])
	answered_percent = (result["answered_count"] / applicable_count * 100) if applicable_count else 100
	minimum = flt(version.minimum_answered_percent)
	if answered_percent < minimum:
		frappe.throw(f"أجب عن {minimum:g}% على الأقل من أسئلة المقياس قبل الإرسال")
	if version.missing_answer_policy == "Require Complete" and result["answered_count"] < applicable_count:
		frappe.throw("يجب إكمال جميع الأسئلة قبل الإرسال")


def interpretation_for_age(version, percentage_score, age):
	rules = parse_json_list(
		getattr(version, "interpretation_rules_json", None),
		"قواعد تفسير النتائج",
	)
	for rule in rules:
		if not isinstance(rule, dict):
			frappe.throw("إحدى قواعد تفسير النتائج غير صالحة")
		min_age = rule.get("minimum_age")
		max_age = rule.get("maximum_age")
		min_score = flt(rule.get("minimum_score"))
		max_score = flt(rule.get("maximum_score"))
		if age is not None and min_age not in (None, "") and age < cint(min_age):
			continue
		if age is not None and max_age not in (None, "") and age > cint(max_age):
			continue
		if age is None and (min_age not in (None, "") or max_age not in (None, "")):
			continue
		if min_score <= percentage_score <= max_score:
			return str(rule.get("label") or "").strip()
	return ""


def _normalize(value, minimum, maximum, reverse):
	if maximum <= minimum:
		frappe.throw("الحد الأعلى للدرجة يجب أن يكون أكبر من الحد الأدنى")
	normalized = ((value - minimum) / (maximum - minimum)) * 100
	if reverse:
		normalized = 100 - normalized
	return round(normalized, 2)


def _option_score_range(options, fallback_minimum, fallback_maximum):
	scores = [flt(row["score"]) for row in options if row["score"] not in (None, "") and not row["excluded"]]
	if not scores:
		return fallback_minimum, fallback_maximum
	minimum, maximum = min(scores), max(scores)
	if maximum > minimum:
		return minimum, maximum
	if fallback_maximum > fallback_minimum:
		return fallback_minimum, fallback_maximum
	return minimum, minimum + 1


def _validate_range(question, values, minimum, maximum):
	if maximum <= minimum:
		frappe.throw(f"حدود السؤال {question.question_code} غير صالحة")
	if any(value < minimum or value > maximum for value in values):
		frappe.throw(
			f"إجابة السؤال {question.question_code} يجب أن تكون بين {minimum:g} و{maximum:g}"
		)


def _answer_values(answer):
	if isinstance(answer, (list, tuple, set)):
		return {str(value).strip() for value in answer}
	if isinstance(answer, dict):
		return {str(value).strip() for value in answer.values()}
	if isinstance(answer, str):
		try:
			parsed = json.loads(answer)
		except (TypeError, ValueError):
			return {answer.strip()}
		if isinstance(parsed, (list, tuple, set)):
			return {str(value).strip() for value in parsed}
		if isinstance(parsed, dict):
			return {str(value).strip() for value in parsed.values()}
	return {str(answer).strip()}


def _answer_label(answer, options):
	labels = {row["value"]: row["label"] for row in options}
	values = _answer_values(answer)
	return "، ".join(labels.get(value, value) for value in values)


def _serialize_answer(answer):
	if isinstance(answer, (list, tuple, dict)):
		return json.dumps(answer, ensure_ascii=False, separators=(",", ":"))
	return str(answer).strip()


def _parse_structured_answer(answer, expected_type):
	if isinstance(answer, expected_type):
		return answer
	try:
		parsed = json.loads(str(answer))
	except (TypeError, ValueError):
		frappe.throw("الإجابة المركبة غير صالحة")
	if not isinstance(parsed, expected_type):
		frappe.throw("الإجابة المركبة غير صالحة")
	return parsed


def _is_empty(value):
	return value is None or value == "" or value == [] or value == {}
