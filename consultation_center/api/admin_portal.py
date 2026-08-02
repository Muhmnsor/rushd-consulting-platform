import json
import re

import frappe
from frappe.utils import cint, flt, now_datetime, strip_html_tags

from consultation_center.assessments import SUPPORTED_RESPONSE_TYPES
from consultation_center.codes import generate_record_code
from consultation_center.staff import ADMIN_ACCESS, require_staff_access

CASE_STATES = {
	"Assigned",
	"Awaiting Appointment",
	"Active",
	"On Hold",
	"Awaiting Report",
	"Under Supervisor Review",
	"Follow-up",
	"Ready to Close",
	"Closed",
}
VALID_WEEKDAYS = {
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
}


@frappe.whitelist(methods=["POST"])
def onboard_consultant(
	consultant_name: str,
	email: str,
	code: str | None = None,
	specializations: str | None = None,
	public_title: str | None = None,
	public_bio: str | None = None,
	profile_image: str | None = None,
	show_on_website: int | str = 0,
	services: str | list | None = None,
	supervisor: str | None = None,
	branch: str | None = None,
	maximum_daily_sessions: int | str = 4,
	weekday: str | None = None,
	start_time: str | None = None,
	end_time: str | None = None,
	availability_rules: str | list | None = None,
):
	require_staff_access(ADMIN_ACCESS)
	consultant_name = _clean(consultant_name, 140, "اسم المستشار")
	email = _clean(email, 140, "البريد الإلكتروني").lower()
	code = _code(code, "رمز المستشار") or generate_record_code("Consultant", "code", "CONS")
	if not consultant_name or not email:
		frappe.throw("أكمل اسم المستشار والبريد الإلكتروني")
	if frappe.db.exists("Consultant", code):
		frappe.throw("رمز المستشار مستخدم مسبقًا")

	user_name = frappe.db.exists("User", email)
	if not user_name:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": consultant_name,
				"full_name": consultant_name,
				"enabled": 1,
				"user_type": "Website User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		user_name = user.name

	service_names = _parse_list(services)
	for service in service_names:
		if not frappe.db.exists("Consultation Service", service):
			frappe.throw(f"الخدمة {service} غير موجودة")
	if supervisor and not frappe.db.exists("User", supervisor):
		frappe.throw("المشرف المحدد غير موجود")
	public_title = _clean(public_title, 140, "المسمى المهني العام")
	public_bio = _clean(public_bio, 1000, "النبذة العامة")
	profile_image = _clean(profile_image, 500, "مسار الصورة المهنية")
	if profile_image and not profile_image.startswith(("/files/", "/assets/")):
		frappe.throw("مسار الصورة المهنية غير صالح")
	show_on_website = cint(show_on_website)
	if show_on_website and (not public_title or not public_bio):
		frappe.throw("أكمل المسمى المهني والنبذة قبل إظهار المستشار في الموقع")
	availability = _normalize_availability_rules(availability_rules)
	legacy_availability = [weekday, start_time, end_time]
	if any(legacy_availability):
		if not all(legacy_availability):
			frappe.throw("أكمل يوم التوفر ووقت البداية والنهاية")
		availability.extend(
			_normalize_availability_rules(
				[{"weekday": weekday, "start_time": start_time, "end_time": end_time}]
			)
		)
	maximum_sessions = max(1, min(20, cint(maximum_daily_sessions) or 4))

	consultant = frappe.get_doc(
		{
			"doctype": "Consultant",
			"consultant_name": consultant_name,
			"code": code,
			"user": user_name,
			"active": 1,
			"supervisor": supervisor or None,
			"branch": _clean(branch, 120, "الفرع"),
			"specializations": _clean(specializations, 1000, "التخصصات"),
			"public_title": public_title,
			"public_bio": public_bio,
			"profile_image": profile_image or None,
			"show_on_website": show_on_website,
			"services": "\n".join(service_names),
			"maximum_daily_sessions": maximum_sessions,
		}
	).insert(ignore_permissions=True)

	for rule in availability:
		_create_consultant_availability(consultant.name, rule, maximum_sessions)

	return {
		"name": consultant.name,
		"user": user_name,
		"message": "تم إنشاء حساب المستشار وربطه بالخدمات والتوفر",
	}


@frappe.whitelist(methods=["POST"])
def update_consultant(
	consultant: str,
	consultant_name: str,
	email: str | None = None,
	code: str | None = None,
	specializations: str | None = None,
	public_title: str | None = None,
	public_bio: str | None = None,
	profile_image: str | None = None,
	show_on_website: int | str = 0,
	services: str | list | None = None,
	supervisor: str | None = None,
	branch: str | None = None,
	maximum_daily_sessions: int | str = 4,
	availability_rules: str | list | None = None,
):
	require_staff_access(ADMIN_ACCESS)
	doc = frappe.get_doc("Consultant", consultant)
	consultant_name = _clean(consultant_name, 140, "اسم المستشار")
	if not consultant_name:
		frappe.throw("اكتب اسم المستشار")

	service_names = _parse_list(services)
	for service in service_names:
		if not frappe.db.exists("Consultation Service", service):
			frappe.throw(f"الخدمة {service} غير موجودة")
	if supervisor and not frappe.db.exists("User", supervisor):
		frappe.throw("المشرف المحدد غير موجود")

	public_title = _clean(public_title, 140, "المسمى المهني العام")
	public_bio = _clean(public_bio, 1000, "النبذة العامة")
	profile_image = _clean(profile_image, 500, "مسار الصورة المهنية")
	if profile_image and not profile_image.startswith(("/files/", "/assets/")):
		frappe.throw("مسار الصورة المهنية غير صالح")
	show_on_website = cint(show_on_website)
	if show_on_website and (not public_title or not public_bio):
		frappe.throw("أكمل المسمى المهني والنبذة قبل إظهار المستشار في الموقع")

	availability = _normalize_availability_rules(availability_rules)
	maximum_sessions = max(1, min(20, cint(maximum_daily_sessions) or 4))
	doc.update(
		{
			"consultant_name": consultant_name,
			"supervisor": supervisor or None,
			"branch": _clean(branch, 120, "الفرع"),
			"specializations": _clean(specializations, 1000, "التخصصات"),
			"public_title": public_title,
			"public_bio": public_bio,
			"profile_image": profile_image or None,
			"show_on_website": show_on_website,
			"services": "\n".join(service_names),
			"maximum_daily_sessions": maximum_sessions,
		}
	)
	doc.save(ignore_permissions=True)

	user = frappe.get_doc("User", doc.user)
	user.first_name = consultant_name
	user.save(ignore_permissions=True)

	for rule_name in frappe.get_all(
		"Consultant Availability Rule",
		filters={"consultant": doc.name},
		pluck="name",
	):
		frappe.delete_doc("Consultant Availability Rule", rule_name, ignore_permissions=True)
	for rule in availability:
		_create_consultant_availability(doc.name, rule, maximum_sessions)

	return {
		"name": doc.name,
		"user": doc.user,
		"message": "تم تحديث ملف المستشار وجدول توفره",
	}


def _create_consultant_availability(consultant: str, rule: dict, maximum_sessions: int):
	return frappe.get_doc(
		{
			"doctype": "Consultant Availability Rule",
			"consultant": consultant,
			"weekday": rule["weekday"],
			"active": 1,
			"start_time": rule["start_time"],
			"end_time": rule["end_time"],
			"slot_duration": 60,
			"capacity": maximum_sessions,
		}
	).insert(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def onboard_beneficiary(
	beneficiary_name: str,
	mobile: str | None = None,
	email: str | None = None,
	date_of_birth: str | None = None,
	city: str | None = None,
	guardian_required: int | str = 0,
	create_portal_account: int | str = 0,
	service: str | None = None,
	urgency: str = "Normal",
	summary: str | None = None,
	preferred_mode: str = "Either",
):
	require_staff_access(ADMIN_ACCESS)
	beneficiary_name = _clean(beneficiary_name, 140, "اسم المستفيد")
	email = _clean(email, 140, "البريد الإلكتروني").lower()
	if not beneficiary_name:
		frappe.throw("اكتب اسم المستفيد")
	if urgency not in {"Low", "Normal", "High", "Urgent"}:
		frappe.throw("الأولوية غير صالحة")
	if preferred_mode not in {"Online", "In Person", "Either"}:
		frappe.throw("نمط الخدمة غير صالح")

	portal_user = None
	if cint(create_portal_account):
		if not email:
			frappe.throw("البريد الإلكتروني مطلوب لإنشاء حساب المستفيد")
		portal_user = frappe.db.exists("User", email)
		if not portal_user:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": beneficiary_name,
					"full_name": beneficiary_name,
					"enabled": 1,
					"user_type": "Website User",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
			portal_user = user.name

	needs_guardian = bool(cint(guardian_required))
	beneficiary = frappe.get_doc(
		{
			"doctype": "Beneficiary",
			"naming_series": "BEN-.YYYY.-",
			"beneficiary_name": beneficiary_name,
			"status": "Active",
			"date_of_birth": date_of_birth or None,
			"mobile": _clean(mobile, 40, "الجوال"),
			"email": email or None,
			"preferred_language": "Arabic",
			"city": _clean(city, 120, "المدينة"),
			"portal_user": portal_user,
			"guardian_required": needs_guardian,
			"confidentiality_level": "Standard",
			"consent_status": "Pending" if needs_guardian else "Not Requested",
		}
	).insert(ignore_permissions=True)

	request_name = None
	if service:
		if not frappe.db.exists("Consultation Service", service):
			frappe.throw("الخدمة المحددة غير موجودة")
		request = frappe.get_doc(
			{
				"doctype": "Consultation Request",
				"naming_series": "REQ-.YYYY.-",
				"beneficiary": beneficiary.name,
				"requested_service": service,
				"workflow_state": "Submitted",
				"source": "Walk-in",
				"request_datetime": now_datetime(),
				"urgency": urgency,
				"summary": _clean(summary, 1000, "ملخص الاحتياج"),
				"preferred_mode": preferred_mode,
				"eligibility_status": "Pending",
				"screening_status": "Pending",
			}
		).insert(ignore_permissions=True)
		request_name = request.name

	return {
		"name": beneficiary.name,
		"request": request_name,
		"message": (
			"تم إنشاء ملف المستفيد وإرسال طلبه للمراجعة"
			if request_name
			else "تم إنشاء ملف المستفيد"
		),
	}


@frappe.whitelist(methods=["POST"])
def create_assessment(
	template_title: str,
	template_code: str | None = None,
	category: str | None = None,
	instrument_kind: str = "Outcome Measure",
	intended_use: str | None = None,
	responder: str = "Beneficiary",
	minimum_age: int | str | None = None,
	maximum_age: int | str | None = None,
	validation_status: str = "Internal Draft",
	reference_or_license: str | None = None,
	result_visibility: str = "After Professional Review",
	description: str | None = None,
	instructions: str | None = None,
	timeframe: str | None = None,
	scoring_method: str = "Percentage",
	minimum_answered_percent: float | str = 80,
	missing_answer_policy: str = "Exclude Missing",
	interpretation_rules: str | list | None = None,
	questions: str | list | None = None,
	publish: int | str = 0,
):
	require_staff_access(ADMIN_ACCESS)
	template_title = _clean(template_title, 180, "اسم المقياس")
	template_code = _code(template_code, "رمز المقياس") or generate_record_code(
		"Assessment Template",
		"template_code",
		"ASM",
	)
	if not template_title:
		frappe.throw("اكتب اسم المقياس")
	if instrument_kind not in {
		"Administrative Form",
		"Satisfaction Survey",
		"Outcome Measure",
		"Safety Screener",
	}:
		frappe.throw("غرض الأداة غير صالح")
	if responder not in {"Beneficiary", "Guardian", "Consultant", "Supervisor", "Mixed"}:
		frappe.throw("المجيب غير صالح")
	if validation_status not in {
		"Internal Draft",
		"Content Reviewed",
		"Piloted",
		"Validated",
		"Licensed",
	}:
		frappe.throw("حالة التحقق العلمي غير صالحة")
	if result_visibility not in {"Never", "After Professional Review"}:
		frappe.throw("سياسة عرض النتيجة غير صالحة")
	if scoring_method not in {"Total", "Average", "Percentage", "No Automated Score"}:
		frappe.throw("طريقة الاحتساب غير صالحة")
	if missing_answer_policy not in {"Exclude Missing", "Require Complete", "Prorate"}:
		frappe.throw("سياسة الإجابات المفقودة غير صالحة")
	minimum_answered_percent = flt(minimum_answered_percent)
	if minimum_answered_percent < 0 or minimum_answered_percent > 100:
		frappe.throw("الحد الأدنى للإجابة يجب أن يكون بين 0 و100")
	interpretation_rules = _normalize_interpretation_rules(interpretation_rules)
	minimum_age = cint(minimum_age) if str(minimum_age or "").strip() else None
	maximum_age = cint(maximum_age) if str(maximum_age or "").strip() else None
	if minimum_age is not None and maximum_age is not None and maximum_age < minimum_age:
		frappe.throw("العمر الأعلى يجب ألا يقل عن العمر الأدنى")
	if frappe.db.exists("Assessment Template", template_code):
		frappe.throw("رمز المقياس مستخدم مسبقًا")

	payload = frappe.parse_json(questions) if isinstance(questions, str) else (questions or [])
	if not isinstance(payload, list) or not payload:
		frappe.throw("أضف سؤالًا واحدًا على الأقل")
	if len(payload) > 100:
		frappe.throw("عدد الأسئلة أكبر من الحد المسموح")

	template = frappe.get_doc(
		{
			"doctype": "Assessment Template",
			"template_title": template_title,
			"template_code": template_code,
			"active": 1,
			"category": _clean(category, 140, "التصنيف"),
			"instrument_kind": instrument_kind,
			"intended_use": _clean(intended_use, 1000, "الاستخدام المقصود"),
			"responder": responder,
			"minimum_age": minimum_age,
			"maximum_age": maximum_age,
			"validation_status": validation_status,
			"reference_or_license": _clean(reference_or_license, 1000, "المرجع أو الترخيص"),
			"result_visibility": result_visibility,
			"description": _clean(description, 1000, "الوصف"),
		}
	).insert(ignore_permissions=True)

	version = frappe.get_doc(
		{
			"doctype": "Assessment Version",
			"naming_series": "ASSESS-VER-.YYYY.-",
			"assessment_template": template.name,
			"version_number": 1,
			"status": "Published" if cint(publish) else "Draft",
			"instructions": _clean(instructions, 1000, "التعليمات"),
			"timeframe": _clean(timeframe, 140, "الفترة الزمنية"),
			"scoring_method": scoring_method,
			"minimum_answered_percent": minimum_answered_percent,
			"missing_answer_policy": missing_answer_policy,
			"interpretation_rules_json": (
				json.dumps(interpretation_rules, ensure_ascii=False, separators=(",", ":"))
				if interpretation_rules
				else None
			),
			"questions": [_normalize_question(item, index) for index, item in enumerate(payload, 1)],
		}
	).insert(ignore_permissions=True)

	return {
		"name": template.name,
		"version": version.name,
		"status": version.status,
		"message": "تم إنشاء المقياس" + (" ونشر نسخته الأولى" if version.status == "Published" else " كمسودة"),
	}


@frappe.whitelist(methods=["POST"])
def update_case_direction(
	case_name: str,
	next_action: str,
	next_action_due: str | None = None,
	case_status: str | None = None,
):
	require_staff_access(ADMIN_ACCESS)
	doc = frappe.get_doc("Consultation Case", case_name)
	next_action = _clean(next_action, 1000, "الإجراء التالي")
	if not next_action:
		frappe.throw("اكتب الإجراء التالي للحالة")
	if case_status and case_status not in CASE_STATES:
		frappe.throw("حالة الملف غير صالحة")
	doc.next_action = next_action
	doc.next_action_due = next_action_due or None
	if case_status:
		doc.case_status = case_status
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "message": "تم تحديث اتجاه الحالة والخطوة التالية"}


def _normalize_question(item, index: int):
	if not isinstance(item, dict):
		frappe.throw(f"بيانات السؤال {index} غير صالحة")
	response_type = item.get("response_type") or "Likert Agreement"
	if response_type not in SUPPORTED_RESPONSE_TYPES:
		frappe.throw(f"نوع إجابة السؤال {index} غير صالح")
	minimum = flt(item.get("minimum_value", 1))
	maximum = flt(item.get("maximum_value", 5))
	options = _normalize_options(item.get("options"), index)
	critical_values = _parse_list(item.get("critical_values"))
	is_safety_item = cint(item.get("is_safety_item", 0))
	critical_action = _clean(item.get("critical_action"), 500, "الإجراء الفوري")
	if is_safety_item and not critical_action:
		frappe.throw(f"حدد الإجراء الفوري لسؤال السلامة {index}")
	return {
		"question_code": _code(item.get("question_code") or f"Q{index}", "رمز السؤال"),
		"question_text": _clean(item.get("question_text"), 1000, "نص السؤال"),
		"beneficiary_help": _clean(item.get("beneficiary_help"), 500, "مساعدة السؤال"),
		"dimension": _clean(item.get("dimension"), 140, "البعد"),
		"timeframe": _clean(item.get("timeframe"), 140, "الفترة الزمنية"),
		"response_type": response_type,
		"required": cint(item.get("required", 1)),
		"scored": 0 if is_safety_item else cint(item.get("scored", 1)),
		"weight": max(flt(item.get("weight", 1)), 0),
		"minimum_value": minimum if response_type != "Yes/No" else 0,
		"maximum_value": maximum if response_type != "Yes/No" else 1,
		"step_value": max(flt(item.get("step_value", 1)), 0.01),
		"reverse_scored": cint(item.get("reverse_scored", 0)),
		"left_anchor": _clean(item.get("left_anchor"), 140, "وصف البداية"),
		"right_anchor": _clean(item.get("right_anchor"), 140, "وصف النهاية"),
		"options_json": json.dumps(options, ensure_ascii=False, separators=(",", ":")) if options else None,
		"condition_question_code": _code(
			item.get("condition_question_code"),
			"رمز سؤال الشرط",
		),
		"condition_operator": item.get("condition_operator") or "Equals",
		"condition_value": _clean(item.get("condition_value"), 140, "قيمة الشرط"),
		"is_safety_item": is_safety_item,
		"critical_values_json": (
			json.dumps(critical_values, ensure_ascii=False, separators=(",", ":"))
			if critical_values
			else None
		),
		"critical_action": critical_action,
	}


def _normalize_options(value, question_index):
	if not value:
		return []
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (TypeError, ValueError):
			rows = [row.strip() for row in value.splitlines() if row.strip()]
			value = []
			for option_index, row in enumerate(rows, 1):
				parts = [part.strip() for part in row.split("|")]
				value.append(
					{
						"value": f"O{option_index}",
						"label": parts[0],
						"score": parts[1] if len(parts) > 1 and parts[1] != "" else None,
						"excluded": len(parts) > 2 and parts[2] in {"مستبعد", "excluded", "na"},
						"critical": len(parts) > 2 and parts[2] in {"حرج", "critical"},
					}
				)
	if not isinstance(value, list):
		frappe.throw(f"خيارات السؤال {question_index} غير صالحة")
	result = []
	for option_index, option in enumerate(value, 1):
		if not isinstance(option, dict):
			frappe.throw(f"الخيار {option_index} في السؤال {question_index} غير صالح")
		label = _clean(option.get("label"), 180, "نص الخيار")
		option_value = _clean(option.get("value") or f"O{option_index}", 80, "قيمة الخيار")
		if not label:
			frappe.throw(f"اكتب نص الخيار {option_index} في السؤال {question_index}")
		score = option.get("score")
		if score not in (None, ""):
			score = flt(score)
		result.append(
			{
				"value": option_value,
				"label": label,
				"score": score,
				"excluded": bool(cint(option.get("excluded"))),
				"critical": bool(cint(option.get("critical"))),
			}
		)
	return result


def _normalize_interpretation_rules(value):
	if not value:
		return []
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (TypeError, ValueError):
			rows = [row.strip() for row in value.splitlines() if row.strip()]
			value = []
			for index, row in enumerate(rows, 1):
				parts = [part.strip() for part in row.split("|")]
				if len(parts) != 3 or "-" not in parts[0] or "-" not in parts[1]:
					frappe.throw(f"قاعدة التفسير {index} يجب أن تكون: العمر من-إلى | النتيجة من-إلى | الوصف")
				age_range = [part.strip() for part in parts[0].split("-", 1)]
				score_range = [part.strip() for part in parts[1].split("-", 1)]
				value.append(
					{
						"minimum_age": cint(age_range[0]),
						"maximum_age": cint(age_range[1]),
						"minimum_score": flt(score_range[0]),
						"maximum_score": flt(score_range[1]),
						"label": parts[2],
					}
				)
	if not isinstance(value, list):
		frappe.throw("قواعد تفسير النتائج غير صالحة")
	result = []
	for index, rule in enumerate(value, 1):
		if not isinstance(rule, dict):
			frappe.throw(f"قاعدة التفسير {index} غير صالحة")
		minimum_age = cint(rule.get("minimum_age"))
		maximum_age = cint(rule.get("maximum_age"))
		minimum_score = flt(rule.get("minimum_score"))
		maximum_score = flt(rule.get("maximum_score"))
		label = _clean(rule.get("label"), 180, "وصف قاعدة التفسير")
		if maximum_age < minimum_age or maximum_score < minimum_score or not label:
			frappe.throw(f"حدود قاعدة التفسير {index} غير صالحة")
		result.append(
			{
				"minimum_age": minimum_age,
				"maximum_age": maximum_age,
				"minimum_score": minimum_score,
				"maximum_score": maximum_score,
				"label": label,
			}
		)
	return result


def _parse_list(value):
	if not value:
		return []
	if isinstance(value, str):
		try:
			parsed = json.loads(value)
		except (TypeError, ValueError):
			parsed = re.split(r"[\n,]+", value)
	else:
		parsed = value
	return list(dict.fromkeys(_clean(item, 180, "القيمة") for item in parsed if _clean(item, 180, "القيمة")))


def _normalize_availability_rules(value):
	if not value:
		return []
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (TypeError, ValueError):
			frappe.throw("بيانات أوقات التوفر غير صالحة")
	if not isinstance(value, list):
		frappe.throw("بيانات أوقات التوفر غير صالحة")

	result = []
	for index, rule in enumerate(value, 1):
		if not isinstance(rule, dict):
			frappe.throw(f"فترة التوفر {index} غير صالحة")
		weekday = _clean(rule.get("weekday"), 20, "يوم التوفر")
		start_time = _clean(rule.get("start_time"), 8, "وقت البداية")
		end_time = _clean(rule.get("end_time"), 8, "وقت النهاية")
		if weekday not in VALID_WEEKDAYS:
			frappe.throw(f"يوم فترة التوفر {index} غير صالح")
		if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", start_time):
			frappe.throw(f"وقت بداية فترة التوفر {index} غير صالح")
		if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", end_time):
			frappe.throw(f"وقت نهاية فترة التوفر {index} غير صالح")
		start_time = start_time[:5]
		end_time = end_time[:5]
		if start_time >= end_time:
			frappe.throw(f"وقت نهاية فترة التوفر {index} يجب أن يكون بعد وقت البداية")
		result.append(
			{
				"weekday": weekday,
				"start_time": start_time,
				"end_time": end_time,
			}
		)

	for weekday in VALID_WEEKDAYS:
		day_rules = sorted(
			(rule for rule in result if rule["weekday"] == weekday),
			key=lambda rule: rule["start_time"],
		)
		for previous, current in zip(day_rules, day_rules[1:]):
			if current["start_time"] < previous["end_time"]:
				frappe.throw("توجد فترات توفر متداخلة في اليوم نفسه")
	return result


def _code(value, label):
	value = _clean(value, 80, label).upper().replace(" ", "-")
	if value and not re.fullmatch(r"[A-Z0-9_-]+", value):
		frappe.throw(f"{label} يجب أن يحتوي على أحرف إنجليزية وأرقام فقط")
	return value


def _clean(value, limit: int, label: str):
	value = strip_html_tags(str(value or "")).strip()
	if len(value) > limit:
		frappe.throw(f"{label} أطول من الحد المسموح")
	return value
