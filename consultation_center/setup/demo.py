import frappe

DEMO_USER = "beneficiary.demo@rushd.local"
DEMO_OPERATIONS_USER = "operations.demo@rushd.local"
DEMO_SUPERVISOR_USER = "supervisor.demo@rushd.local"

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
	operations_user = _ensure_staff_user(
		DEMO_OPERATIONS_USER,
		"نورة",
		"الاستقبال",
		"Intake Coordinator",
		password,
	)
	supervisor_user = _ensure_staff_user(
		DEMO_SUPERVISOR_USER,
		"خالد",
		"المشرف",
		"Consultation Supervisor",
		password,
	)
	services = [_ensure_service(values) for values in DEMO_SERVICES]
	beneficiary = _ensure_beneficiary(user)
	_ensure_sample_requests(beneficiary, services)
	frappe.db.commit()

	return {
		"user": user,
		"operations_user": operations_user,
		"supervisor_user": supervisor_user,
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


def _ensure_staff_user(
	email: str,
	first_name: str,
	last_name: str,
	role: str,
	password: str,
) -> str:
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		user.enabled = 1
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)

	user.new_password = password
	user.save(ignore_permissions=True)
	user.add_roles(role)
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


def _ensure_sample_requests(beneficiary: str, services: list[str]) -> list[str]:
	samples = (
		(
			services[0],
			"Under Completeness Review",
			"طلب تجريبي للعرض المحلي لمسار المستفيد في منصة رُشد.",
		),
		(
			services[1],
			"Submitted",
			"أرغب في ترتيب خياراتي الدراسية والمهنية ومعرفة الخطوة الأنسب لي.",
		),
		(
			services[2],
			"Ready for Triage",
			"أحتاج إلى مساعدة في تحسين التواصل ووضع حدود صحية في علاقاتي الأسرية.",
		),
	)
	names = []
	for service, workflow_state, summary in samples:
		existing = frappe.db.get_value(
			"Consultation Request",
			{
				"beneficiary": beneficiary,
				"requested_service": service,
				"summary": summary,
			},
			"name",
		)
		if existing:
			names.append(existing)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Consultation Request",
				"beneficiary": beneficiary,
				"requested_service": service,
				"workflow_state": workflow_state,
				"source": "Portal",
				"summary": summary,
				"preferred_mode": "Either",
				"preferred_times": "بعد الساعة الخامسة مساءً",
			}
		).insert(ignore_permissions=True)
		names.append(doc.name)
	return names
