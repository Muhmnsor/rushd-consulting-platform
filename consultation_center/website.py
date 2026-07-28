import json
from copy import deepcopy

import frappe


SETTINGS_DOCTYPE = "Rushd Website Settings"
WEBSITE_WORKSPACE = "Website"

TEXT_DEFAULTS = {
	"page_title": "رُشد للاستشارات الشبابية",
	"meta_description": "منصة رُشد تربط الشباب بمستشارين مختصين ضمن رحلة واضحة تحترم الخصوصية.",
	"brand_subtitle": "للاستشارات الشبابية",
	"services_nav_label": "مجالات الاستشارة",
	"journey_nav_label": "كيف تعمل الخدمة؟",
	"privacy_nav_label": "الخصوصية",
	"faq_nav_label": "الأسئلة الشائعة",
	"hero_eyebrow": "مساحة آمنة، وخطوات واضحة",
	"hero_title": "نستمع إليك،",
	"hero_emphasis": "ونمشي معك.",
	"hero_description": "منصة رُشد تربط الشباب بمستشارين مختصين في رحلة تحترم الخصوصية، وتوضح لك دائمًا حالتك والخطوة التالية.",
	"hero_secondary_action_label": "تعرف على الرحلة",
	"request_status_label": "حالة الطلب",
	"request_status_value": "تحت المراجعة",
	"privacy_card_label": "الخصوصية",
	"privacy_card_value": "وصول حسب الدور",
	"next_step_label": "خطوتك التالية",
	"next_step_value": "اختيار الوقت المناسب",
	"intro_eyebrow": "لأن البداية قد تكون أصعب خطوة",
	"intro_title": "خدمة قريبة منك،",
	"intro_emphasis": "وليست حكمًا عليك.",
	"intro_description": "لا تحتاج إلى معرفة اسم المشكلة أو اختيار الحل وحدك. اكتب ما ترتاح لمشاركته، وسيساعدك فريق رُشد في الوصول إلى المجال والمستشار الأنسب.",
	"services_eyebrow": "مجالات الاستشارة",
	"services_title": "اختر الأقرب لما يشغلك",
	"services_description": "لا تقلق إن لم تكن متأكدًا من المجال؛ يستطيع فريق الاستقبال تعديل الاختيار بعد فهم احتياجك.",
	"service_category_fallback": "استشارة شبابية",
	"service_card_fallback": "خدمة استشارية مهنية تقدم ضمن رحلة واضحة تحافظ على خصوصيتك.",
	"empty_services_title": "الخدمات قيد الإعداد",
	"empty_services_description": "سيتم نشر مجالات الاستشارة المعتمدة قريبًا.",
	"journey_eyebrow": "رحلة الاستشارة",
	"journey_title": "نعرفك دائمًا أين وصلت",
	"journey_description": "من لحظة إرسال الطلب إلى المتابعة، تظهر لك الحالة والخطوة التالية بوضوح.",
	"privacy_eyebrow": "السرية والصلاحيات",
	"privacy_title": "لكل شخص نافذته،",
	"privacy_emphasis": "ولكل معلومة حدودها.",
	"privacy_description": "حساب ولي الأمر مستقل، ولا يعرض له رُشد الملاحظات المهنية أو محتوى الجلسات تلقائيًا. كل وصول مرتبط بالدور والتفويض والسياسة.",
	"beneficiary_label": "المستفيد",
	"guardian_label": "ولي الأمر",
	"consultant_label": "المستشار",
	"privacy_link_label": "اقرأ إجابات الخصوصية",
	"faq_eyebrow": "قبل أن تبدأ",
	"faq_title": "أسئلة قد تدور في بالك",
	"faq_description": "إن لم تجد إجابتك، تستطيع التواصل مع فريق المركز بعد تسجيل الدخول.",
	"cta_eyebrow": "خطوة صغيرة قد تصنع فرقًا",
	"cta_title": "ابدأ بما تستطيع قوله اليوم.",
	"cta_description": "يمكنك حفظ الطلب كمسودة والعودة إليه في الوقت المناسب.",
	"footer_description": "منصة لإدارة رحلة الاستشارة الشبابية بوضوح وخصوصية ومسؤولية.",
	"copyright_notice": "جميع الحقوق محفوظة.",
	"emergency_notice": "هذه المنصة ليست بديلًا لخدمات الطوارئ.",
}

NUMERIC_DEFAULTS = {
	"services_limit": 6,
}

TABLE_DEFAULTS = {
	"hero_trust_items": [
		{"title": "خصوصية مصممة من البداية"},
		{"title": "مستشارون معتمدون من المركز"},
		{"title": "متابعة واضحة للطلب"},
	],
	"intro_promises": [
		{"title": "لغة واضحة", "description": "من دون تعقيد أو مصطلحات مبهمة."},
		{"title": "قرار إنساني", "description": "لا تشخيص أو قرار حساس بواسطة نتيجة آلية."},
		{"title": "خصوصية عملية", "description": "ولي الأمر لا يرى محتوى الجلسة تلقائيًا."},
		{"title": "رحلة متصلة", "description": "طلبك وموعدك وخطتك في مكان واحد."},
	],
	"journey_steps": [
		{
			"step_number": "١",
			"stage": "ابدأ",
			"title": "أرسل طلبك",
			"description": "اختر المجال واكتب وصفًا مختصرًا، واحفظه كمسودة إن أردت.",
		},
		{
			"step_number": "٢",
			"stage": "نراجع",
			"title": "نفرز الاحتياج",
			"description": "يتحقق الفريق من الاكتمال والملاءمة دون قرارات آلية حساسة.",
		},
		{
			"step_number": "٣",
			"stage": "ننسق",
			"title": "نحدد المستشار والموعد",
			"description": "وفق التخصص والتوفر والطاقة، ثم تختار الوقت المناسب.",
		},
		{
			"step_number": "٤",
			"stage": "نتابع",
			"title": "جلسة وخطوة تالية",
			"description": "ملخص مسموح وخطة متابعة واضحة مع احترام حدود السرية.",
		},
	],
	"privacy_items": [
		{"title": "الملاحظة المهنية تبقى داخل الفريق المصرح له."},
		{"title": "ملخص المستفيد وملخص ولي الأمر حقول منفصلة."},
		{"title": "الملفات الحساسة لا تستخدم روابط عامة."},
		{"title": "فتح السجلات الحساسة والتعديلات قابل للتدقيق."},
	],
	"faqs": [
		{
			"question": "هل يجب أن أعرف نوع الاستشارة التي أحتاجها؟",
			"answer": "لا. اختر المجال الأقرب واكتب ما يشغلك، وسيساعدك فريق الاستقبال في توجيه الطلب.",
		},
		{
			"question": "هل يرى ولي الأمر ما أقوله للمستشار؟",
			"answer": "ليس تلقائيًا. الملاحظات المهنية خاصة، وما يظهر لولي الأمر يكون ملخصًا منفصلًا تسمح به السياسة والتفويض.",
		},
		{
			"question": "ماذا يحدث بعد إرسال الطلب؟",
			"answer": "يراجع فريق الاستقبال اكتمال البيانات، ثم ينتقل الطلب للفرز والإسناد، وتظهر لك الحالة والخطوة التالية في البوابة.",
		},
		{
			"question": "هل رُشد مناسب للحالات الطارئة؟",
			"answer": "رُشد خدمة استشارية وليست خدمة طوارئ. عند وجود خطر مباشر يجب التواصل فورًا مع خدمات الطوارئ المحلية المناسبة.",
		},
	],
}


def get_rushd_website_settings():
	"""Return persisted homepage content, with safe defaults during installation."""
	values = frappe._dict(deepcopy(TEXT_DEFAULTS))
	values.update(deepcopy(NUMERIC_DEFAULTS))
	for fieldname, rows in TABLE_DEFAULTS.items():
		values[fieldname] = [frappe._dict(row) for row in deepcopy(rows)]

	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return values

	settings = frappe.get_single(SETTINGS_DOCTYPE)
	for fieldname, fallback in TEXT_DEFAULTS.items():
		values[fieldname] = settings.get(fieldname) or fallback
	for fieldname, fallback in NUMERIC_DEFAULTS.items():
		values[fieldname] = settings.get(fieldname) or fallback
	for fieldname, fallback in TABLE_DEFAULTS.items():
		rows = settings.get(fieldname) or fallback
		values[fieldname] = [frappe._dict(row.as_dict() if hasattr(row, "as_dict") else row) for row in rows]

	return values


def ensure_rushd_website_settings():
	"""Seed only missing fields so migrations never overwrite editorial changes."""
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return

	settings = frappe.get_single(SETTINGS_DOCTYPE)
	changed = settings.is_new()

	for fieldname, value in {**TEXT_DEFAULTS, **NUMERIC_DEFAULTS}.items():
		if settings.get(fieldname) in (None, ""):
			settings.set(fieldname, value)
			changed = True

	for fieldname, rows in TABLE_DEFAULTS.items():
		if not settings.get(fieldname):
			for row in rows:
				settings.append(fieldname, deepcopy(row))
			changed = True

	if changed:
		settings.save(ignore_permissions=True)


def remove_legacy_settings_from_website_workspace():
	"""Clean an early database-only workspace link without changing Frappe source files."""
	if not frappe.db.exists("Workspace", WEBSITE_WORKSPACE):
		return

	workspace = frappe.get_doc("Workspace", WEBSITE_WORKSPACE)
	for row in [*workspace.links, *workspace.shortcuts]:
		if row.get("link_to") == SETTINGS_DOCTYPE:
			frappe.db.delete(row.doctype, {"name": row.name})

	content = json.loads(workspace.content or "[]")
	cleaned_content = [
		block
		for block in content
		if block.get("id") not in {"rushd_website_header", "rushd_website_settings"}
		and block.get("data", {}).get("shortcut_name")
		!= "إعدادات الصفحة الرئيسية لرُشد"
	]
	if cleaned_content != content:
		frappe.db.set_value(
			"Workspace",
			WEBSITE_WORKSPACE,
			"content",
			json.dumps(cleaned_content, ensure_ascii=False, separators=(",", ":")),
			update_modified=False,
		)
	frappe.clear_document_cache("Workspace", WEBSITE_WORKSPACE)
