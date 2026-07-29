import frappe
from frappe.utils import cint, flt, now_datetime, strip_html_tags

from consultation_center.consultant_portal import get_current_consultant
from consultation_center.portal import get_beneficiary_for_user, require_portal_login


@frappe.whitelist(methods=["POST"])
def assign_assessment(
	case: str,
	assessment_version: str,
	assessment_type: str = "Baseline",
	due_date: str | None = None,
):
	consultant = _require_consultant()
	case_doc = frappe.get_doc("Consultation Case", case)
	if case_doc.primary_consultant != consultant.name:
		frappe.throw("لا يمكنك إسناد مقياس لهذه الحالة", frappe.PermissionError)
	if assessment_type not in {"Baseline", "Follow-up", "Closing"}:
		frappe.throw("نوع التقييم غير صالح")

	version = frappe.get_doc("Assessment Version", assessment_version)
	template = frappe.get_doc("Assessment Template", version.assessment_template)
	if version.status != "Published" or not template.active:
		frappe.throw("اختر نسخة منشورة من مقياس نشط")
	if template.responder != "Beneficiary":
		frappe.throw("هذه النسخة ليست مخصصة لإجابة المستفيد")
	if frappe.db.exists(
		"Assessment Submission",
		{
			"case": case_doc.name,
			"assessment_version": version.name,
			"assessment_type": assessment_type,
			"status": ["!=", "Cancelled"],
		},
	):
		frappe.throw("سبق إسناد هذه النسخة ونوع التقييم للحالة")

	doc = frappe.get_doc(
		{
			"doctype": "Assessment Submission",
			"case": case_doc.name,
			"beneficiary": case_doc.beneficiary,
			"consultant": consultant.name,
			"assessment_template": template.name,
			"assessment_version": version.name,
			"assessment_type": assessment_type,
			"due_date": due_date or None,
			"status": "Assigned",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "message": "تم إرسال المقياس للمستفيد"}


@frappe.whitelist(methods=["POST"])
def save_assessment_responses(
	submission_name: str,
	responses: str | list | None = None,
	submit: int | str = 0,
):
	user = require_portal_login()
	beneficiary = get_beneficiary_for_user(user)
	if not beneficiary:
		frappe.throw("لا يوجد ملف مستفيد نشط", frappe.PermissionError)

	doc = frappe.get_doc("Assessment Submission", submission_name)
	if doc.beneficiary != beneficiary.name:
		frappe.throw("لا يمكنك تعبئة هذا المقياس", frappe.PermissionError)
	if doc.status not in {"Assigned", "In Progress"}:
		frappe.throw("المقياس في حالة لا تسمح بالتعديل")

	version = frappe.get_doc("Assessment Version", doc.assessment_version)
	payload = frappe.parse_json(responses) if isinstance(responses, str) else (responses or [])
	if len(payload) > len(version.questions):
		frappe.throw("عدد الإجابات غير صالح")
	answer_by_code = {
		str(item.get("question_code") or "").strip().upper(): item.get("answer_value")
		for item in payload
	}

	doc.set("responses", [])
	raw_total = 0.0
	normalized_scores = []
	for question in version.questions:
		answer = answer_by_code.get(question.question_code)
		if answer is None or str(answer).strip() == "":
			continue
		raw_value, normalized = _score_answer(question, answer)
		raw_total += raw_value
		normalized_scores.append(normalized)
		doc.append(
			"responses",
			{
				"question_code": question.question_code,
				"question_text": question.question_text,
				"response_type": question.response_type,
				"answer_value": str(answer).strip(),
				"numeric_score": normalized,
			},
		)

	doc.raw_score = raw_total
	doc.percentage_score = (
		round(sum(normalized_scores) / len(normalized_scores), 2)
		if normalized_scores
		else 0
	)
	doc.status = "Submitted" if cint(submit) else "In Progress"
	if doc.status == "Submitted":
		doc.submitted_on = now_datetime()
	doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"status": doc.status,
		"message": "تم إرسال إجاباتك للمراجعة" if doc.status == "Submitted" else "تم حفظ الإجابات",
	}


@frappe.whitelist(methods=["POST"])
def review_assessment(
	submission_name: str,
	professional_interpretation: str | None = None,
	beneficiary_result_summary: str | None = None,
	publish_result: int | str = 0,
):
	consultant = _require_consultant()
	doc = frappe.get_doc("Assessment Submission", submission_name)
	if doc.consultant != consultant.name:
		frappe.throw("لا يمكنك مراجعة هذا المقياس", frappe.PermissionError)
	if doc.status != "Submitted":
		frappe.throw("لا يمكن مراجعة المقياس من حالته الحالية")

	template = frappe.get_doc("Assessment Template", doc.assessment_template)
	internal = _clean(professional_interpretation, 5000, "التفسير المهني")
	public_summary = _clean(beneficiary_result_summary, 3000, "ملخص النتيجة")
	should_publish = bool(cint(publish_result))
	if should_publish and template.result_visibility == "Never":
		frappe.throw("سياسة هذا المقياس لا تسمح بعرض النتيجة للمستفيد")
	if should_publish and not public_summary:
		frappe.throw("اكتب ملخصًا واضحًا للمستفيد قبل نشر النتيجة")

	doc.professional_interpretation = internal
	doc.beneficiary_result_summary = public_summary
	doc.result_visible = should_publish
	doc.status = "Reviewed"
	doc.reviewed_by = frappe.session.user
	doc.reviewed_on = now_datetime()
	doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"status": doc.status,
		"result_visible": doc.result_visible,
		"message": "تمت مراجعة المقياس",
	}


def _score_answer(question, answer) -> tuple[float, float]:
	if question.response_type == "Yes/No":
		answer_text = str(answer).strip()
		if answer_text not in {"0", "1", "No", "no", "لا", "Yes", "yes", "نعم"}:
			frappe.throw(f"إجابة السؤال {question.question_code} غير صالحة")
		value = 1.0 if answer_text in {"1", "Yes", "yes", "نعم"} else 0.0
		minimum, maximum = 0.0, 1.0
	else:
		try:
			value = float(str(answer).strip())
		except (TypeError, ValueError):
			frappe.throw(f"إجابة السؤال {question.question_code} غير صالحة")
		minimum = flt(question.minimum_value)
		maximum = flt(question.maximum_value)
		if value < minimum or value > maximum:
			frappe.throw(
				f"إجابة السؤال {question.question_code} يجب أن تكون بين {minimum:g} و{maximum:g}"
			)

	normalized = ((value - minimum) / (maximum - minimum)) * 100
	if question.reverse_scored:
		normalized = 100 - normalized
	return value, round(normalized, 2)


def _require_consultant():
	consultant = get_current_consultant()
	if not consultant:
		frappe.throw("لا يوجد ملف مستشار نشط مرتبط بالحساب", frappe.PermissionError)
	return consultant


def _clean(value: str | None, limit: int, label: str) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > limit:
		frappe.throw(f"{label} أطول من الحد المسموح")
	return value
