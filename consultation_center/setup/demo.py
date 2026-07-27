import frappe
from frappe.utils import nowdate

DEMO_USER = "beneficiary.demo@rushd.local"
DEMO_GUARDIAN_USER = "guardian.demo@rushd.local"
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
	guardian_user = _ensure_staff_user(
		DEMO_GUARDIAN_USER,
		"أمل",
		"ولي الأمر",
		"Guardian",
		password,
	)
	services = [_ensure_service(values) for values in DEMO_SERVICES]
	beneficiary = _ensure_beneficiary(user)
	_ensure_sample_requests(beneficiary, services)
	guardian = _ensure_guardian(guardian_user)
	authorization = _ensure_guardian_authorization(guardian, beneficiary)
	consent_record = _ensure_guardian_consent(guardian, beneficiary)
	frappe.db.commit()

	return {
		"user": user,
		"operations_user": operations_user,
		"supervisor_user": supervisor_user,
		"guardian_user": guardian_user,
		"beneficiary": beneficiary,
		"guardian": guardian,
		"authorization": authorization,
		"consent_record": consent_record,
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


def _ensure_guardian(user: str) -> str:
	existing = frappe.db.get_value("Guardian", {"portal_user": user}, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Guardian",
			"guardian_name": "أمل ولي الأمر",
			"portal_user": user,
			"mobile": "0500000001",
			"email": user,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _ensure_guardian_authorization(guardian: str, beneficiary: str) -> str:
	existing = frappe.db.get_value(
		"Guardian Authorization",
		{
			"guardian": guardian,
			"beneficiary": beneficiary,
			"authorization_status": "Active",
		},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Guardian Authorization",
			"guardian": guardian,
			"beneficiary": beneficiary,
			"relationship": "Mother",
			"authorization_status": "Active",
			"effective_from": nowdate(),
			"authorized_by": "Administrator",
			"can_view_profile": 1,
			"can_view_requests": 1,
			"can_view_case": 1,
			"can_manage_appointments": 1,
			"can_view_reports": 0,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _ensure_guardian_consent(guardian: str, beneficiary: str) -> str:
	template_name = "RUSHD-GUARDIAN-GENERAL"
	if not frappe.db.exists("Consent Template", template_name):
		frappe.get_doc(
			{
				"doctype": "Consent Template",
				"template_code": template_name,
				"template_title": "موافقة ولي الأمر على تقديم الخدمة",
				"consent_scope": "Minor Protection",
				"active": 1,
				"requires_beneficiary": 1,
				"requires_guardian": 1,
			}
		).insert(ignore_permissions=True)

	version = frappe.db.get_value(
		"Consent Version",
		{"consent_template": template_name, "version_label": "1.0"},
		"name",
	)
	if not version:
		version = frappe.get_doc(
			{
				"doctype": "Consent Version",
				"consent_template": template_name,
				"version_label": "1.0",
				"status": "Published",
				"effective_from": nowdate(),
				"title": "موافقة ولي الأمر على تقديم الخدمة",
				"simplified_text": (
					"هذا نص تجريبي غير معتمد قانونيًا. تسمح هذه الموافقة لفريق رُشد بتقديم "
					"الخدمة للمستفيد وفق حدود السرية والسياسات المعتمدة."
				),
				"full_text": (
					"نسخة العرض المحلي: أفهم أن حساب ولي الأمر مستقل، وأن الملاحظات المهنية "
					"ومحتوى الجلسات لا تظهر لي تلقائيًا، وأن الوصول تحدده مدة التفويض ونطاقه. "
					"يجب استبدال هذا النص بسياسة قانونية معتمدة قبل الإنتاج."
				),
			}
		).insert(ignore_permissions=True).name

	existing = frappe.db.get_value(
		"Consent Record",
		{
			"consent_template": template_name,
			"consent_version": version,
			"beneficiary": beneficiary,
			"guardian": guardian,
			"consent_role": "Guardian",
		},
		"name",
	)
	if existing:
		return existing

	return frappe.get_doc(
		{
			"doctype": "Consent Record",
			"consent_template": template_name,
			"consent_version": version,
			"beneficiary": beneficiary,
			"guardian": guardian,
			"consent_role": "Guardian",
			"status": "Pending",
		}
	).insert(ignore_permissions=True).name


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
