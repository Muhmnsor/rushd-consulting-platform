import json

import frappe
from frappe.utils import cint, getdate, now_datetime, nowdate, strip_html_tags

from consultation_center.assessments import (
	calculate_submission,
	interpretation_for_age,
	validate_completion,
)
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
	if not isinstance(payload, list):
		frappe.throw("صيغة الإجابات غير صالحة")
	answer_by_code = {}
	for item in payload:
		if not isinstance(item, dict):
			frappe.throw("صيغة إحدى الإجابات غير صالحة")
		code = str(item.get("question_code") or "").strip().upper()
		if code:
			answer_by_code[code] = item.get("answer_value")

	result = calculate_submission(version, answer_by_code)
	if cint(submit):
		validate_completion(version, result, answer_by_code)
	doc.set("responses", [])
	for row in result["rows"]:
		doc.append("responses", row)

	doc.raw_score = result["raw_score"]
	doc.percentage_score = result["percentage_score"]
	doc.answered_count = result["answered_count"]
	doc.scored_count = result["scored_count"]
	doc.dimension_scores_json = json.dumps(
		result["dimension_scores"],
		ensure_ascii=False,
		separators=(",", ":"),
	)
	doc.interpretation_band = interpretation_for_age(
		version,
		result["percentage_score"],
		_beneficiary_age(doc.beneficiary),
	)
	if result["alerts"]:
		doc.safety_alert_triggered = 1
		doc.safety_alert_summary = " | ".join(
			f'{alert["question_code"]}: {alert["answer_label"]}' for alert in result["alerts"]
		)
		doc.professional_escalation = _ensure_safety_escalation(doc, result["alerts"])
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
def _ensure_safety_escalation(submission, alerts):
	existing = submission.professional_escalation or frappe.db.get_value(
		"Professional Escalation",
		{"source_assessment": submission.name, "status": ["not in", ["Closed", "Cancelled"]]},
		"name",
	)
	if existing:
		return existing
	case = frappe.db.get_value(
		"Consultation Case",
		submission.case,
		["supervisor", "case_owner"],
		as_dict=True,
	)
	supervisor = case.supervisor or case.case_owner or "Administrator"
	summary = "\n".join(
		f'- {alert["question_text"]}: {alert["answer_label"]}' for alert in alerts
	)
	action = "\n".join(dict.fromkeys(alert["action"] for alert in alerts))
	escalation = frappe.get_doc(
		{
			"doctype": "Professional Escalation",
			"case": submission.case,
			"beneficiary": submission.beneficiary,
			"consultant": submission.consultant,
			"assigned_supervisor": supervisor,
			"source_assessment": submission.name,
			"status": "Open",
			"severity": "Critical",
			"alert_type": "Safeguarding",
			"alert_summary": f"إجابة سلامة حرجة في المقياس {submission.assessment_template}\n{summary}",
			"immediate_action": action,
			"emergency_protocol_activated": 0,
		}
	).insert(ignore_permissions=True)
	return escalation.name


def _beneficiary_age(beneficiary):
	date_of_birth = frappe.db.get_value("Beneficiary", beneficiary, "date_of_birth")
	if not date_of_birth:
		return None
	born = getdate(date_of_birth)
	today = getdate(nowdate())
	return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


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
