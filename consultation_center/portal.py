import json
from urllib.parse import urlencode

import frappe
import frappe.sessions
from frappe.utils import format_date, format_time, get_datetime, now_datetime

from consultation_center.assessments import NUMERIC_TYPES, question_options

REQUEST_STATUS = {
	"Draft": {
		"label": "مسودة",
		"tone": "neutral",
		"next_step": "أكمل بيانات الطلب ثم أرسله إلى فريق الاستقبال.",
	},
	"Submitted": {
		"label": "تم استلام الطلب",
		"tone": "blue",
		"next_step": "سيبدأ فريق الاستقبال مراجعة اكتمال البيانات.",
	},
	"Under Completeness Review": {
		"label": "تحت مراجعة الاكتمال",
		"tone": "blue",
		"next_step": "لا يلزمك إجراء حاليًا، وسنبلغك إذا احتجنا معلومات إضافية.",
	},
	"Ready for Triage": {
		"label": "جاهز للفرز",
		"tone": "blue",
		"next_step": "يراجع المشرف المختص ملاءمة الخدمة والخطوة الأنسب.",
	},
	"Awaiting Beneficiary Information": {
		"label": "بانتظار استكمال البيانات",
		"tone": "gold",
		"next_step": "راجع الطلب وأكمل المعلومات التي طلبها فريق الاستقبال.",
	},
	"Eligible": {
		"label": "مؤهل للخدمة",
		"tone": "green",
		"next_step": "سيتم استكمال الموافقات ثم تجهيز الطلب للإسناد.",
	},
	"Not Eligible": {
		"label": "الخدمة غير مناسبة",
		"tone": "red",
		"next_step": "راجع التوضيح العام أو تواصل مع فريق الدعم لمعرفة البدائل.",
	},
	"Awaiting Consent": {
		"label": "بانتظار الموافقة",
		"tone": "gold",
		"next_step": "أكمل الموافقة المطلوبة للانتقال إلى الإسناد.",
	},
	"Ready for Assignment": {
		"label": "جاهز للإسناد",
		"tone": "green",
		"next_step": "يعمل الفريق على اختيار المستشار الأنسب والتواصل معك.",
	},
	"Converted to Case": {
		"label": "تحول إلى حالة نشطة",
		"tone": "green",
		"next_step": "يمكنك متابعة الموعد والخطوات القادمة من لوحة المستفيد.",
	},
	"Cancelled": {
		"label": "ملغي",
		"tone": "neutral",
		"next_step": "يمكنك تقديم طلب جديد عندما تحتاج إلى الخدمة.",
	},
}


def require_portal_login() -> str:
	user = frappe.session.user
	if user == "Guest":
		redirect_to = frappe.request.path if frappe.request else "/beneficiary"
		frappe.redirect(f"/login?{urlencode({'redirect-to': redirect_to})}")
	return user


def get_beneficiary_for_user(user: str | None = None):
	user = user or require_portal_login()
	return frappe.db.get_value(
		"Beneficiary",
		{"portal_user": user, "status": "Active"},
		[
			"name",
			"beneficiary_name",
			"mobile",
			"email",
			"city",
			"date_of_birth",
			"consent_status",
			"guardian_required",
			"preferred_language",
		],
		as_dict=True,
	)


def build_portal_context(context, active_nav: str, title: str):
	user = require_portal_login()
	frappe.sessions.get_csrf_token()
	frappe.db.commit()
	beneficiary = get_beneficiary_for_user(user)
	display_name = (
		beneficiary.beneficiary_name
		if beneficiary
		else frappe.db.get_value("User", user, "full_name") or user
	)

	context.update(
		{
			"title": title,
			"no_cache": 1,
			"body_class": "rushd-portal-page",
			"active_nav": active_nav,
			"portal_user": user,
			"display_name": display_name,
			"beneficiary": beneficiary,
		}
	)
	return beneficiary


def get_beneficiary_requests(beneficiary: str, limit: int | None = None):
	rows = frappe.db.get_all(
		"Consultation Request",
		filters={"beneficiary": beneficiary},
		fields=[
			"name",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"preferred_mode",
			"beneficiary_action_note",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)
	for row in rows:
		row.service_name = (
			frappe.db.get_value("Consultation Service", row.requested_service, "service_name")
			or row.requested_service
		)
		status = REQUEST_STATUS.get(row.workflow_state, REQUEST_STATUS["Submitted"])
		row.status_label = status["label"]
		row.status_tone = status["tone"]
		row.next_step = status["next_step"]
		row.request_date_label = format_date(row.request_datetime) if row.request_datetime else "—"
	return rows


def get_next_appointment(beneficiary: str):
	row = frappe.db.get_value(
		"Consultation Appointment",
		{
			"beneficiary": beneficiary,
			"status": ["in", ["Pending Approval", "Confirmed", "Rescheduled"]],
			"start_datetime": [">=", now_datetime()],
		},
		["name", "start_datetime", "delivery_mode", "service", "status"],
		order_by="start_datetime asc",
		as_dict=True,
	)
	if not row:
		return None

	start = get_datetime(row.start_datetime)
	row.date_label = format_date(start)
	row.time_label = format_time(start, format="HH:mm")
	row.service_name = frappe.db.get_value("Consultation Service", row.service, "service_name")
	row.delivery_label = "عن بُعد" if row.delivery_mode == "Online" else "حضوري"
	return row


def calculate_profile_completion(beneficiary) -> int:
	if not beneficiary:
		return 0
	fields = ("beneficiary_name", "mobile", "email", "city", "date_of_birth")
	completed = sum(bool(beneficiary.get(field)) for field in fields)
	return round((completed / len(fields)) * 100)


def get_active_beneficiary_plan(beneficiary: str):
	name = frappe.db.get_value(
		"Consultation Plan",
		{"beneficiary": beneficiary, "status": ["in", ["Active", "Completed"]]},
		"name",
		order_by="modified desc",
	)
	if not name:
		return None
	doc = frappe.get_doc("Consultation Plan", name)
	doc.visible_goals = [goal for goal in doc.goals if goal.beneficiary_visible]
	doc.start_date_label = format_date(doc.start_date) if doc.start_date else "غير محددة"
	doc.review_date_label = format_date(doc.review_date) if doc.review_date else "غير محددة"
	doc.status_label = "مكتملة" if doc.status == "Completed" else "معتمدة"
	return doc


def get_beneficiary_tasks(beneficiary: str):
	rows = frappe.db.get_all(
		"Beneficiary Task",
		filters={"beneficiary": beneficiary, "status": ["!=", "Cancelled"]},
		fields=[
			"name",
			"plan",
			"task_title",
			"instructions",
			"due_date",
			"status",
			"beneficiary_note",
			"completed_on",
		],
		order_by="due_date asc, creation asc",
	)
	labels = {
		"Pending": "لم تبدأ",
		"In Progress": "قيد التنفيذ",
		"Completed": "مكتملة",
	}
	for row in rows:
		row.status_label = labels.get(row.status, row.status)
		row.due_date_label = format_date(row.due_date) if row.due_date else "دون موعد محدد"
	return rows


def get_beneficiary_assessments(beneficiary: str):
	rows = frappe.db.get_all(
		"Assessment Submission",
		filters={"beneficiary": beneficiary, "status": ["!=", "Cancelled"]},
		fields=[
			"name",
			"assessment_template",
			"assessment_type",
			"status",
			"due_date",
			"percentage_score",
			"result_visible",
			"beneficiary_result_summary",
			"modified",
		],
		order_by="due_date asc, modified desc",
	)
	statuses = {
		"Assigned": "مطلوب",
		"In Progress": "محفوظ جزئيًا",
		"Submitted": "أُرسل للمراجعة",
		"Reviewed": "تمت المراجعة",
	}
	types = {"Baseline": "قبلي", "Follow-up": "متابعة", "Closing": "بعدي"}
	for row in rows:
		row.template_title = (
			frappe.db.get_value(
				"Assessment Template",
				row.assessment_template,
				"template_title",
			)
			or row.assessment_template
		)
		row.status_label = statuses.get(row.status, row.status)
		row.type_label = types.get(row.assessment_type, row.assessment_type)
		row.due_date_label = format_date(row.due_date) if row.due_date else "دون موعد محدد"
		row.editable = row.status in {"Assigned", "In Progress"}
	return rows


def get_beneficiary_assessment_detail(beneficiary: str, submission_name: str | None):
	if not submission_name:
		return None
	name = frappe.db.get_value(
		"Assessment Submission",
		{"name": submission_name, "beneficiary": beneficiary, "status": ["!=", "Cancelled"]},
		"name",
	)
	if not name:
		return None
	submission = frappe.get_doc("Assessment Submission", name)
	version = frappe.get_doc("Assessment Version", submission.assessment_version)
	template = frappe.get_doc("Assessment Template", submission.assessment_template)
	answers = {row.question_code: row.answer_value for row in submission.responses}
	questions = []
	for question in version.questions:
		answer_value = answers.get(question.question_code, "")
		options = question_options(question)
		structured_answer = _assessment_structured_answer(answer_value)
		for option in options:
			option["selected"] = (
				option["value"] in structured_answer
				if isinstance(structured_answer, list)
				else option["value"] == str(answer_value)
			)
			option["matrix_value"] = (
				structured_answer.get(option["value"], "")
				if isinstance(structured_answer, dict)
				else ""
			)
		questions.append(
			{
				"question_code": question.question_code,
				"question_text": question.question_text,
				"beneficiary_help": question.beneficiary_help,
				"dimension": question.dimension,
				"timeframe": question.timeframe or version.timeframe,
				"response_type": question.response_type,
				"required": question.required,
				"minimum_value": question.minimum_value,
				"maximum_value": question.maximum_value,
				"step_value": question.step_value or 1,
				"left_anchor": question.left_anchor,
				"right_anchor": question.right_anchor,
				"options": options,
				"answer_value": answer_value,
				"structured_answer": structured_answer,
				"is_numeric": question.response_type in NUMERIC_TYPES,
				"is_safety_item": bool(question.is_safety_item),
				"condition_question_code": question.condition_question_code,
				"condition_operator": question.condition_operator,
				"condition_value": question.condition_value,
			}
		)
	return {
		"name": submission.name,
		"template_title": template.template_title,
		"instructions": version.instructions,
		"status": submission.status,
		"editable": submission.status in {"Assigned", "In Progress"},
		"questions": questions,
		"result_visible": bool(submission.result_visible and submission.status == "Reviewed"),
		"percentage_score": (
			round(submission.percentage_score or 0, 1)
			if submission.result_visible and submission.status == "Reviewed"
			else None
		),
		"beneficiary_result_summary": (
			submission.beneficiary_result_summary
			if submission.result_visible and submission.status == "Reviewed"
			else ""
		),
	}


def _assessment_structured_answer(value):
	if not isinstance(value, str) or not value:
		return value
	try:
		parsed = json.loads(value)
	except (TypeError, ValueError):
		return value
	return parsed if isinstance(parsed, (list, dict)) else value
