import frappe

DEMO_USER = "beneficiary.demo@rushd.local"

DEMO_SERVICES = (
	{
		"service_code": "RUSHD-SELF",
		"service_name": "تطوير الذات والمهارات",
		"category": "تطوير شخصي",
		"delivery_modes": "Both",
	},
	{
		"service_code": "RUSHD-CAREER",
		"service_name": "التوجيه الدراسي والمهني",
		"category": "التعليم والعمل",
		"delivery_modes": "Both",
	},
	{
		"service_code": "RUSHD-FAMILY",
		"service_name": "العلاقات الأسرية والاجتماعية",
		"category": "العلاقات",
		"delivery_modes": "Online",
	},
)


def create_local_beneficiary_demo(password: str):
	"""Create repeatable local-only demo data for visually testing the beneficiary portal."""
	if not frappe.conf.developer_mode:
		frappe.throw("Demo data can only be created when developer_mode is enabled")
	if not password or len(password) < 12:
		frappe.throw("Use a local demo password with at least 12 characters")

	user = _ensure_demo_user(password)
	services = [_ensure_service(values) for values in DEMO_SERVICES]
	beneficiary = _ensure_beneficiary(user)
	_ensure_sample_request(beneficiary, services[0])
	frappe.db.commit()

	return {
		"user": user,
		"beneficiary": beneficiary,
		"services": services,
		"portal": "/beneficiary",
	}


def _ensure_demo_user(password: str) -> str:
	if frappe.db.exists("User", DEMO_USER):
		user = frappe.get_doc("User", DEMO_USER)
		user.enabled = 1
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": DEMO_USER,
				"first_name": "سارة",
				"last_name": "التجريبية",
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)

	user.new_password = password
	user.save(ignore_permissions=True)
	user.add_roles("Beneficiary")
	return user.name


def _ensure_service(values: dict) -> str:
	if frappe.db.exists("Consultation Service", values["service_code"]):
		return values["service_code"]

	doc = frappe.get_doc(
		{
			"doctype": "Consultation Service",
			**values,
			"active": 1,
			"duration_minutes": 60,
			"description": "خدمة تجريبية للعرض المحلي وتطوير رحلة المستفيد.",
		}
	).insert(ignore_permissions=True)
	return doc.name


def _ensure_beneficiary(user: str) -> str:
	existing = frappe.db.get_value("Beneficiary", {"portal_user": user}, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Beneficiary",
			"beneficiary_name": "سارة التجريبية",
			"portal_user": user,
			"mobile": "0500000000",
			"email": user,
			"city": "الرياض",
			"date_of_birth": "2002-01-01",
			"preferred_language": "Arabic",
			"consent_status": "Granted",
		}
	).insert(ignore_permissions=True)
	return doc.name


def _ensure_sample_request(beneficiary: str, service: str) -> str:
	existing = frappe.db.get_value(
		"Consultation Request",
		{
			"beneficiary": beneficiary,
			"requested_service": service,
			"summary": ["like", "طلب تجريبي للعرض المحلي%"],
		},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Consultation Request",
			"beneficiary": beneficiary,
			"requested_service": service,
			"workflow_state": "Under Completeness Review",
			"source": "Portal",
			"summary": "طلب تجريبي للعرض المحلي لمسار المستفيد في منصة رُشد.",
			"preferred_mode": "Either",
			"preferred_times": "بعد الساعة الخامسة مساءً",
		}
	).insert(ignore_permissions=True)
	return doc.name

