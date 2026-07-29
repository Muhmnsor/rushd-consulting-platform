import frappe
from frappe.utils import cint, flt, getdate, now_datetime, strip_html_tags

from consultation_center.codes import generate_record_code
from consultation_center.staff import ADMIN_ACCESS, require_staff_access


def _field(
	fieldname,
	label,
	fieldtype="Data",
	required=False,
	default=None,
	options=None,
	direction=None,
	auto=False,
):
	return {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
		"required": required,
		"default": default,
		"options": options,
		"direction": direction,
		"auto": auto,
	}


def _options(*items):
	return [{"value": value, "label": label} for value, label in items]


def _audiences():
	return _options(
		("All", "الجميع"),
		("Beneficiary", "المستفيدون"),
		("Guardian", "أولياء الأمور"),
		("Consultant", "المستشارون"),
		("Consultation Supervisor", "المشرفون"),
		("Operations", "فريق التشغيل"),
	)


RESOURCE_SCHEMAS = {
	"services": {
		"doctype": "Consultation Service",
		"auto_code": ("service_code", "SRV"),
		"can_create": True,
		"can_edit": True,
		"can_delete": True,
		"delete_label": "حذف الخدمة",
		"fields": [
			_field("service_name", "اسم الخدمة", required=True),
			_field("service_code", "رمز الخدمة", direction="ltr", auto=True),
			_field("category", "التصنيف"),
			_field("active", "الخدمة نشطة", "Check", default=1),
			_field("duration_minutes", "مدة الجلسة بالدقائق", "Int", default=60),
			_field("delivery_modes", "طريقة التقديم", "Select", options=_options(("Online", "عن بُعد"), ("In Person", "حضوري"), ("Both", "حضوري وعن بُعد"))),
			_field("session_limit", "الحد المقترح للجلسات", "Int"),
			_field("requires_supervisor_approval", "تتطلب موافقة المشرف", "Check"),
			_field("description", "وصف الخدمة", "Text"),
			_field("eligibility_rules", "قواعد الأهلية", "Text"),
			_field("follow_up_policy", "سياسة المتابعة", "Text"),
		],
	},
	"consents": {
		"doctype": "Consent Template",
		"auto_code": ("template_code", "CONSENT"),
		"can_create": True,
		"can_edit": True,
		"can_delete": True,
		"delete_label": "حذف القالب",
		"fields": [
			_field("template_title", "اسم نموذج الموافقة", required=True),
			_field("template_code", "رمز النموذج", direction="ltr", auto=True),
			_field("consent_scope", "نطاق الموافقة", "Select", default="General", options=_options(("General", "عام"), ("Privacy", "الخصوصية"), ("Service", "الخدمة"), ("Minor Protection", "حماية القاصر"), ("Data Sharing", "مشاركة البيانات"))),
			_field("active", "القالب نشط", "Check", default=1),
			_field("requires_beneficiary", "يتطلب موافقة المستفيد", "Check", default=1),
			_field("requires_guardian", "يتطلب موافقة ولي الأمر", "Check"),
			_field("service", "الخدمة المرتبطة", "Link", options="Consultation Service"),
		],
	},
	"announcements": {
		"doctype": "Internal Announcement",
		"can_create": True,
		"can_edit": True,
		"can_delete": True,
		"delete_label": "حذف الإعلان",
		"fields": [
			_field("title", "عنوان الإعلان", required=True),
			_field("audience", "المستهدفون", "Select", required=True, default="All", options=_audiences()),
			_field("priority", "الأولوية", "Select", default="Normal", options=_options(("Normal", "عادية"), ("High", "عالية"), ("Urgent", "عاجلة"))),
			_field("active", "الإعلان نشط", "Check", default=1),
			_field("start_date", "تاريخ البداية", "Date"),
			_field("end_date", "تاريخ النهاية", "Date"),
			_field("service", "خدمة محددة", "Link", options="Consultation Service"),
			_field("summary", "الملخص", "Text", required=True),
			_field("content", "محتوى الإعلان", "Text"),
			_field("mandatory_read", "إلزامي الاطلاع", "Check"),
		],
	},
	"resources": {
		"doctype": "Resource Content",
		"can_create": True,
		"can_edit": True,
		"can_delete": True,
		"delete_label": "حذف المورد",
		"fields": [
			_field("title", "عنوان المورد", required=True),
			_field("content_type", "نوع المحتوى", "Select", required=True, default="Article", options=_options(("Article", "مقال"), ("Guide", "دليل"), ("File", "ملف"), ("Video", "فيديو"), ("External Link", "رابط خارجي"))),
			_field("audience", "المستهدفون", "Select", required=True, default="All", options=_audiences()),
			_field("active", "المورد منشور", "Check", default=1),
			_field("service", "خدمة محددة", "Link", options="Consultation Service"),
			_field("minimum_age", "العمر الأدنى", "Int"),
			_field("maximum_age", "العمر الأعلى", "Int"),
			_field("summary", "الملخص", "Text", required=True),
			_field("content", "المحتوى", "Text"),
			_field("external_url", "الرابط الخارجي", direction="ltr"),
			_field("copyright_note", "ملاحظة حقوق النشر", "Text"),
		],
	},
	"message-templates": {
		"doctype": "Notification",
		"can_create": True,
		"can_edit": True,
		"can_delete": True,
		"delete_label": "حذف القالب",
		"prompt_name": True,
		"fields": [
			_field("record_name", "اسم القالب", required=True),
			_field("enabled", "القالب مفعّل", "Check", default=1),
			_field("channel", "قناة الإرسال", "Select", required=True, default="Email", options=_options(("Email", "البريد الإلكتروني"), ("System Notification", "تنبيه داخل المنصة"), ("SMS", "رسالة نصية"))),
			_field("document_type", "السجل الذي يطلق الرسالة", "Link", required=True, options="DocType"),
			_field("event", "متى تُرسل؟", "Select", required=True, default="New", options=_options(("New", "عند الإنشاء"), ("Save", "عند الحفظ"), ("Submit", "عند الاعتماد"), ("Cancel", "عند الإلغاء"))),
			_field("subject", "عنوان الرسالة", required=True),
			_field("message", "نص الرسالة", "Text", required=True),
			_field("recipient_role", "الدور المستلم", "Link", options="Role"),
		],
	},
	"complaints": {
		"doctype": "Complaint",
		"can_create": True,
		"can_edit": True,
		"can_delete": False,
		"immutable_note": "لا تُحذف الشكاوى؛ تُغلق بعد توثيق الإجراء والرد.",
		"fields": [
			_field("beneficiary", "المستفيد", "Link", options="Beneficiary"),
			_field("complaint_type", "نوع البلاغ", "Select", required=True, default="Service Feedback", options=_options(("Service Feedback", "تقييم الخدمة"), ("Confidential Complaint", "شكوى سرية"), ("Suggestion", "اقتراح"), ("Change Consultant", "طلب تغيير مستشار"))),
			_field("confidentiality", "السرية", "Select", required=True, default="Standard", options=_options(("Standard", "عادية"), ("Confidential", "سرية"), ("Restricted", "مقيدة"))),
			_field("priority", "الأولوية", "Select", required=True, default="Normal", options=_options(("Low", "منخفضة"), ("Normal", "عادية"), ("High", "عالية"), ("Urgent", "عاجلة"))),
			_field("status", "الحالة", "Select", required=True, default="Submitted", options=_options(("Submitted", "مقدمة"), ("Under Review", "قيد المراجعة"), ("Action Required", "تتطلب إجراء"), ("Resolved", "محلولة"), ("Closed", "مغلقة"))),
			_field("details", "تفاصيل البلاغ", "Text", required=True),
			_field("assigned_to", "مسندة إلى", "Link", options="User"),
			_field("investigation_note", "ملاحظة التحقيق", "Text"),
			_field("action_taken", "الإجراء المتخذ", "Text"),
			_field("public_response", "الرد العام", "Text"),
		],
	},
	"website": {
		"doctype": "Rushd Website Settings",
		"singleton": True,
		"can_create": False,
		"can_edit": True,
		"can_delete": False,
		"fields": [
			_field("page_title", "عنوان الصفحة في المتصفح"),
			_field("meta_description", "وصف محركات البحث", "Text"),
			_field("brand_subtitle", "وصف العلامة"),
			_field("hero_eyebrow", "النص التمهيدي"),
			_field("hero_title", "العنوان الرئيسي"),
			_field("hero_emphasis", "السطر البارز"),
			_field("hero_description", "وصف واجهة البداية", "Text"),
			_field("journey_title", "عنوان رحلة الاستشارة"),
			_field("journey_description", "وصف رحلة الاستشارة", "Text"),
			_field("privacy_title", "عنوان الخصوصية"),
			_field("privacy_description", "وصف الخصوصية", "Text"),
			_field("faq_title", "عنوان الأسئلة الشائعة"),
			_field("faq_description", "وصف الأسئلة الشائعة", "Text"),
			_field("emergency_notice", "تنبيه الطوارئ", "Text"),
		],
	},
	"privacy": {
		"doctype": "Consent Record",
		"can_create": False,
		"can_edit": True,
		"can_delete": False,
		"immutable_note": "سجل الموافقة لا يُحذف. عند سحبها يُحفظ السبب ووقت السحب ضمن سجل التدقيق.",
		"fields": [
			_field(
				"status",
				"حالة الموافقة",
				"Select",
				required=True,
				options=_options(
					("Pending", "بانتظار الموافقة"),
					("Granted", "ممنوحة"),
					("Withdrawn", "مسحوبة"),
					("Expired", "منتهية"),
				),
			),
			_field("withdrawal_reason", "سبب السحب أو الانتهاء", "Text"),
		],
	},
}


@frappe.whitelist()
def get_admin_record(resource: str, name: str | None = None):
	require_staff_access(ADMIN_ACCESS)
	config = _config(resource)
	doc = frappe.get_single(config["doctype"]) if config.get("singleton") else frappe.get_doc(config["doctype"], name)
	values = {field["fieldname"]: doc.get(field["fieldname"]) for field in config["fields"] if field["fieldname"] != "record_name"}
	if config.get("prompt_name"):
		values["record_name"] = doc.name
		values["recipient_role"] = next(
			(row.receiver_by_role for row in doc.recipients if row.receiver_by_role),
			"",
		)
	return {"name": doc.name, "values": values}


@frappe.whitelist(methods=["POST"])
def save_admin_record(resource: str, values: str | dict, name: str | None = None):
	require_staff_access(ADMIN_ACCESS)
	config = _config(resource)
	payload = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(payload, dict):
		frappe.throw("بيانات النموذج غير صالحة")
	if name and not config.get("can_edit"):
		frappe.throw("هذا القسم لا يسمح بالتعديل")
	if not name and not config.get("can_create") and not config.get("singleton"):
		frappe.throw("هذا القسم لا يسمح بالإنشاء")
	if config.get("auto_code"):
		fieldname, prefix = config["auto_code"]
		payload = dict(payload)
		if name and not payload.get(fieldname):
			payload[fieldname] = frappe.db.get_value(config["doctype"], name, fieldname)
		elif not name and not payload.get(fieldname):
			payload[fieldname] = generate_record_code(config["doctype"], fieldname, prefix)
	cleaned = _clean_values(config, payload)

	if config.get("singleton"):
		doc = frappe.get_single(config["doctype"])
	elif name:
		doc = frappe.get_doc(config["doctype"], name)
	else:
		doc = frappe.new_doc(config["doctype"])
		if config["doctype"] == "Complaint":
			doc.naming_series = "COMP-.YYYY.-"
			doc.complainant = frappe.session.user
	original_status = doc.get("status")
	record_name = cleaned.pop("record_name", None)
	recipient_role = cleaned.pop("recipient_role", None)
	if config.get("prompt_name") and doc.is_new():
		doc.name = record_name

	for fieldname, value in cleaned.items():
		doc.set(fieldname, value)
	if config["doctype"] == "Consent Record":
		if cleaned.get("status") == "Withdrawn":
			if not cleaned.get("withdrawal_reason"):
				frappe.throw("سبب سحب الموافقة مطلوب")
			if original_status != "Withdrawn":
				doc.withdrawn_at = now_datetime()
		elif cleaned.get("status") != "Withdrawn" and original_status == "Withdrawn":
			frappe.throw("لا يمكن إعادة تفعيل موافقة مسحوبة؛ أنشئ موافقة جديدة من رحلة المستفيد")
	if config.get("prompt_name"):
		doc.set("recipients", [])
		if recipient_role:
			doc.append("recipients", {"receiver_by_role": recipient_role})
	doc.save(ignore_permissions=True) if not doc.is_new() else doc.insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"message": "تم تحديث السجل" if name or config.get("singleton") else "تم إنشاء السجل",
	}


@frappe.whitelist(methods=["POST"])
def delete_admin_record(resource: str, name: str):
	require_staff_access(ADMIN_ACCESS)
	config = _config(resource)
	if not config.get("can_delete"):
		frappe.throw(config.get("immutable_note") or "لا يسمح بحذف سجلات هذا القسم")
	if not name or not frappe.db.exists(config["doctype"], name):
		frappe.throw("السجل غير موجود")
	frappe.delete_doc(config["doctype"], name, ignore_permissions=True)
	return {"message": "تم حذف السجل"}


def get_resource_ui_schema(resource):
	config = RESOURCE_SCHEMAS.get(resource)
	if not config:
		return None
	return frappe._dict(
		can_create=config.get("can_create", False),
		can_edit=config.get("can_edit", False),
		can_delete=config.get("can_delete", False),
		delete_label=config.get("delete_label", "حذف"),
		immutable_note=config.get("immutable_note"),
		singleton=config.get("singleton", False),
		fields=[frappe._dict(field) for field in config["fields"]],
	)


def _config(resource):
	config = RESOURCE_SCHEMAS.get((resource or "").strip())
	if not config:
		frappe.throw("مكوّن الإدارة غير صالح")
	return config


def _clean_values(config, payload):
	result = {}
	for field in config["fields"]:
		fieldname = field["fieldname"]
		value = payload.get(fieldname)
		if field["fieldtype"] == "Check":
			value = cint(value)
		elif field["fieldtype"] == "Int":
			value = cint(value) if str(value or "").strip() else None
		elif field["fieldtype"] in {"Float", "Currency"}:
			value = flt(value) if str(value or "").strip() else None
		elif field["fieldtype"] == "Date":
			value = getdate(value) if value else None
		else:
			value = strip_html_tags(str(value or "")).strip()
			if len(value) > 5000:
				frappe.throw(f'{field["label"]} أطول من الحد المسموح')
		if field.get("required") and value in (None, "", 0):
			frappe.throw(f'{field["label"]} مطلوب')
		if field["fieldtype"] == "Select" and value:
			allowed = {option["value"] for option in field.get("options") or []}
			if value not in allowed:
				frappe.throw(f'{field["label"]} غير صالح')
		if field["fieldtype"] == "Link" and value and not frappe.db.exists(field["options"], value):
			frappe.throw(f'{field["label"]} غير موجود')
		result[fieldname] = value
	if config.get("prompt_name") and payload.get("record_name"):
		result["record_name"] = strip_html_tags(str(payload["record_name"])).strip()
	return result
