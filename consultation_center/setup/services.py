import frappe


LEGACY_DEMO_DESCRIPTION = "خدمة تجريبية للعرض المحلي وتطوير رحلة المستفيد."

DEFAULT_SERVICES = (
	{
		"service_code": "RUSHD-ACADEMIC",
		"service_name": "الدعم الأكاديمي والتعامل مع التعثر",
		"category": "الدراسة الجامعية",
		"delivery_modes": "Both",
		"description": "مساندة عملية لتنظيم الدراسة، تجاوز التعثر، الاستعداد للاختبارات، وبناء عادات تعلم تناسبك.",
	},
	{
		"service_code": "RUSHD-CAREER",
		"service_name": "التوجيه الدراسي والمهني",
		"category": "التعليم والعمل",
		"delivery_modes": "Both",
		"description": "مساعدة في اختيار التخصص، استكشاف المسارات المهنية، واتخاذ قرارات أوضح للدراسة والعمل.",
	},
	{
		"service_code": "RUSHD-WELLBEING",
		"service_name": "إدارة الضغوط والتوازن النفسي",
		"category": "الصحة النفسية",
		"delivery_modes": "Both",
		"description": "مساحة مهنية لفهم الضغوط والقلق اليومي وتعلّم أساليب عملية للتعامل معها واستعادة التوازن.",
	},
	{
		"service_code": "RUSHD-SELF",
		"service_name": "تطوير الذات والمهارات",
		"category": "تطوير شخصي",
		"delivery_modes": "Both",
		"description": "دعم لبناء الثقة، تحسين إدارة الوقت، تطوير العادات، وتحويل أهدافك إلى خطوات قابلة للتنفيذ.",
	},
	{
		"service_code": "RUSHD-RELATIONSHIPS",
		"service_name": "العلاقات والتواصل",
		"category": "العلاقات",
		"delivery_modes": "Online",
		"description": "مساعدة على فهم التحديات في العلاقات الأسرية والاجتماعية وتحسين التواصل ووضع حدود صحية.",
	},
	{
		"service_code": "RUSHD-DIGITAL-BALANCE",
		"service_name": "التوازن الرقمي ونمط الحياة",
		"category": "نمط الحياة",
		"delivery_modes": "Online",
		"description": "إرشاد لتنظيم استخدام التقنية والألعاب والشبكات الاجتماعية وبناء روتين يومي أكثر توازنًا.",
	},
)


def ensure_default_services():
	"""Create the public starter catalogue without overwriting editorial changes."""
	if not frappe.db.exists("DocType", "Consultation Service"):
		return

	for values in DEFAULT_SERVICES:
		service_code = values["service_code"]
		if not frappe.db.exists("Consultation Service", service_code):
			frappe.get_doc(
				{
					"doctype": "Consultation Service",
					**values,
					"active": 1,
					"duration_minutes": 60,
				}
			).insert(ignore_permissions=True)
			continue

		service = frappe.get_doc("Consultation Service", service_code)
		if service.description not in (None, "", LEGACY_DEMO_DESCRIPTION):
			continue

		for fieldname, value in values.items():
			service.set(fieldname, value)
		service.active = 1
		service.save(ignore_permissions=True)
