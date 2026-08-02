import frappe
from frappe.utils import add_days, format_date, format_datetime, get_datetime, nowdate

from consultation_center.permissions import has_admin_app_access
from consultation_center.staff import (
	ADMIN_ACCESS,
	build_staff_context,
	get_supervised_case_detail,
	get_supervised_cases,
)

ACTIVE_CASE_STATES = (
	"Assigned",
	"Awaiting Appointment",
	"Active",
	"On Hold",
	"Awaiting Report",
	"Under Supervisor Review",
	"Follow-up",
	"Ready to Close",
)

REQUEST_STAGE_LABELS = {
	"Submitted": "طلبات جديدة",
	"Under Completeness Review": "تحت المراجعة",
	"Awaiting Beneficiary Information": "بانتظار المستفيد",
	"Ready for Triage": "جاهزة للفرز",
	"Eligible": "جاهزة للإسناد",
	"Converted to Case": "تحولت إلى حالات",
}

ROLE_CATALOG = [
	("System Manager", "مدير النظام", "إدارة تقنية كاملة تشمل الحسابات والإعدادات الحساسة."),
	("Center Director", "مدير المركز", "إدارة التشغيل والحوكمة والاطلاع الشامل على أعمال المركز."),
	("Consultation Supervisor", "المشرف الاستشاري", "الفرز والإسناد ومراجعة الحالات والجلسات والتصعيدات."),
	("Case Coordinator", "منسق الحالات", "تنسيق الطلبات والمواعيد والملفات دون صلاحيات الإدارة العليا."),
	("Intake Coordinator", "منسق الاستقبال", "مراجعة الطلبات الأولية واستكمال بيانات المستفيد."),
	("Operations Officer", "مسؤول التشغيل", "متابعة الدعم والمهام التشغيلية اليومية."),
	("Consultant", "المستشار", "الوصول إلى الحالات المسندة والجلسات والخطط والمقاييس."),
	("Assessment Manager", "مسؤول المقاييس", "بناء نسخ المقاييس ومراجعتها ونشرها."),
	("Content Manager", "مسؤول المحتوى", "إدارة الموارد والمحتوى المنشور داخل المنصة."),
]
PORTAL_ROLE_LABELS = {
	"Beneficiary": "المستفيد",
	"Guardian": "ولي الأمر",
}


def redirect_admin(target):
	if not has_admin_app_access():
		frappe.throw("ليس لديك صلاحية للوصول إلى إدارة رُشد", frappe.PermissionError)
	frappe.redirect(target)


def build_admin_context(context, active_nav: str, title: str):
	build_staff_context(context, active_nav, title, "admin", ADMIN_ACCESS)
	context.admin_technical_url = "/app/rushd"


def get_admin_dashboard():
	today_start = get_datetime(nowdate())
	tomorrow_start = get_datetime(add_days(nowdate(), 1))
	request_counts = {
		state: frappe.db.count("Consultation Request", {"workflow_state": state})
		for state in REQUEST_STAGE_LABELS
	}
	active_cases = frappe.db.count(
		"Consultation Case",
		{"case_status": ["in", ACTIVE_CASE_STATES]},
	)
	today_appointments = frappe.db.count(
		"Consultation Appointment",
		[
			["start_datetime", ">=", today_start],
			["start_datetime", "<", tomorrow_start],
		],
	)
	pending_sessions = frappe.db.count(
		"Consultation Session",
		{"status": "Pending Review"},
	)
	submitted_assessments = frappe.db.count(
		"Assessment Submission",
		{"status": "Submitted"},
	)
	urgent_cases = frappe.db.count(
		"Consultation Case",
		{
			"case_status": ["in", ACTIVE_CASE_STATES],
			"priority": ["in", ["High", "Urgent"]],
		},
	)

	return frappe._dict(
		request_counts=request_counts,
		active_cases=active_cases,
		today_appointments=today_appointments,
		pending_sessions=pending_sessions,
		submitted_assessments=submitted_assessments,
		urgent_cases=urgent_cases,
		consultants=frappe.db.count("Consultant", {"active": 1}),
		beneficiaries=frappe.db.count("Beneficiary", {"status": "Active"}),
		services=frappe.db.count("Consultation Service", {"active": 1}),
		attention_items=[
			frappe._dict(
				label="طلبات تحتاج مراجعة",
				count=request_counts.get("Submitted", 0)
				+ request_counts.get("Under Completeness Review", 0),
				description="تحقق من البيانات والنواقص قبل الفرز.",
				href="/operations/requests",
			),
			frappe._dict(
				label="طلبات جاهزة للفرز",
				count=request_counts.get("Ready for Triage", 0),
				description="تحتاج قرار المشرف المهني.",
				href="/supervisor/triage",
			),
			frappe._dict(
				label="طلبات جاهزة للإسناد",
				count=request_counts.get("Eligible", 0),
				description="اختر المستشار المناسب وأنشئ الحالة.",
				href="/supervisor/assignments",
			),
			frappe._dict(
				label="جلسات تنتظر المراجعة",
				count=pending_sessions,
				description="راجع التوثيق والإجراء التالي للحالة.",
				href="/supervisor/session-reviews",
			),
		],
	)


def get_admin_consultants():
	rows = frappe.db.get_all(
		"Consultant",
		fields=[
			"name",
			"consultant_name",
			"user",
			"active",
			"supervisor",
			"branch",
			"specializations",
			"public_title",
			"public_bio",
			"profile_image",
			"show_on_website",
			"services",
			"maximum_daily_sessions",
			"credential_expiry",
		],
		order_by="active desc, consultant_name asc",
		limit=200,
	)
	for row in rows:
		row.active_cases = frappe.db.count(
			"Consultation Case",
			{
				"primary_consultant": row.name,
				"case_status": ["in", ACTIVE_CASE_STATES],
			},
		)
		row.supervisor_name = (
			frappe.db.get_value("User", row.supervisor, "full_name")
			if row.supervisor
			else "غير محدد"
		)
		row.credential_expiry_label = (
			format_date(row.credential_expiry) if row.credential_expiry else "غير محدد"
		)
	return rows


def get_admin_consultant_for_edit(consultant_name: str):
	row = frappe.db.get_value(
		"Consultant",
		consultant_name,
		[
			"name",
			"consultant_name",
			"code",
			"user",
			"supervisor",
			"branch",
			"specializations",
			"services",
			"public_title",
			"public_bio",
			"profile_image",
			"show_on_website",
			"maximum_daily_sessions",
		],
		as_dict=True,
	)
	if not row:
		return None

	row.email = frappe.db.get_value("User", row.user, "email") or row.user
	row.service_names = [value.strip() for value in (row.services or "").splitlines() if value.strip()]
	row.availability_rules = frappe.db.get_all(
		"Consultant Availability Rule",
		filters={"consultant": row.name, "active": 1},
		fields=["weekday", "start_time", "end_time"],
		order_by="weekday asc, start_time asc",
	)
	for rule in row.availability_rules:
		rule.start_time_value = str(rule.start_time or "")[:5]
		rule.end_time_value = str(rule.end_time or "")[:5]
	return row


def get_admin_beneficiaries():
	rows = frappe.db.get_all(
		"Beneficiary",
		fields=[
			"name",
			"beneficiary_name",
			"status",
			"mobile",
			"email",
			"city",
			"guardian_required",
			"consent_status",
			"portal_user",
			"modified",
		],
		order_by="modified desc",
		limit=200,
	)
	for row in rows:
		row.requests = frappe.db.count("Consultation Request", {"beneficiary": row.name})
		row.active_cases = frappe.db.count(
			"Consultation Case",
			{
				"beneficiary": row.name,
				"case_status": ["in", ACTIVE_CASE_STATES],
			},
		)
		row.consent_label = {
			"Not Requested": "لم تُطلب",
			"Pending": "معلقة",
			"Granted": "مكتملة",
			"Withdrawn": "مسحوبة",
		}.get(row.consent_status, row.consent_status or "غير محددة")
	return rows


def get_admin_services():
	return frappe.db.get_all(
		"Consultation Service",
		filters={"active": 1},
		fields=["name", "service_name", "service_code", "category", "duration_minutes"],
		order_by="service_name asc",
	)


def get_admin_supervisors():
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Consultation Supervisor", "Center Director"]]},
		pluck="parent",
	)
	if "Administrator" not in users:
		users.append("Administrator")
	rows = frappe.db.get_all(
		"User",
		filters={"name": ["in", users], "enabled": 1},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)
	return rows


def get_admin_users(query: str | None = None):
	query = (query or "").strip()
	filters = {"name": ["not in", ["Guest"]]}
	or_filters = None
	if query:
		like = f"%{query}%"
		or_filters = {
			"name": ["like", like],
			"full_name": ["like", like],
			"username": ["like", like],
		}
	rows = frappe.db.get_all(
		"User",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"email",
			"full_name",
			"username",
			"enabled",
			"user_type",
			"last_login",
			"last_active",
			"restrict_ip",
		],
		order_by="enabled desc, full_name asc",
		limit=250,
	)
	role_labels = {name: label for name, label, _ in ROLE_CATALOG}
	role_order = [name for name, _, _ in ROLE_CATALOG]
	display_role_labels = role_labels | PORTAL_ROLE_LABELS
	display_role_order = role_order + list(PORTAL_ROLE_LABELS)
	for row in rows:
		display_roles = frappe.db.get_all(
			"Has Role",
			filters={"parent": row.name, "role": ["in", display_role_order]},
			pluck="role",
		)
		row.display_roles = sorted(display_roles, key=lambda role: display_role_order.index(role))
		row.roles = [role for role in row.display_roles if role in role_order]
		row.role_labels = [display_role_labels.get(role, role) for role in row.display_roles]
		row.primary_role = row.role_labels[0] if row.role_labels else "دون دور تشغيلي"
		row.type_label = "موظف" if row.user_type == "System User" else "مستخدم بوابة"
		row.last_seen_label = (
			format_datetime(row.last_active or row.last_login)
			if row.last_active or row.last_login
			else "لم يسجل الدخول"
		)
		row.protected = row.name == "Administrator"
	return frappe._dict(
		rows=rows,
		total=frappe.db.count("User", {"name": ["not in", ["Guest"]]}),
		enabled=frappe.db.count("User", {"enabled": 1, "name": ["not in", ["Guest"]]}),
		system_users=frappe.db.count("User", {"enabled": 1, "user_type": "System User"}),
		without_roles=sum(1 for row in rows if not row.display_roles),
		query=query,
		can_manage=(
			frappe.session.user == "Administrator"
			or "System Manager" in frappe.get_roles(frappe.session.user)
		),
		can_change_administrator_password=frappe.session.user == "Administrator",
		roles=[
			frappe._dict(name=name, label=label)
			for name, label, _ in ROLE_CATALOG
			if frappe.db.exists("Role", name)
		],
	)


def get_admin_roles():
	rows = []
	for role_name, label, description in ROLE_CATALOG:
		if not frappe.db.exists("Role", role_name):
			continue
		users = frappe.db.get_all(
			"Has Role",
			filters={"role": role_name, "parenttype": "User"},
			pluck="parent",
		)
		active_count = (
			frappe.db.count("User", {"name": ["in", users], "enabled": 1})
			if users
			else 0
		)
		rows.append(
			frappe._dict(
				name=role_name,
				label=label,
				description=description,
				active_users=active_count,
				scope=_role_scope(role_name),
				is_sensitive=role_name == "System Manager",
			)
		)
	return rows


def get_admin_security():
	settings = frappe.get_single("System Settings")
	recent_activity = frappe.db.get_all(
		"Activity Log",
		filters={"operation": "Login"},
		fields=["user", "full_name", "status", "communication_date", "ip_address"],
		order_by="communication_date desc",
		limit=15,
	)
	for row in recent_activity:
		row.status_label = "ناجحة" if row.status == "Success" else "فاشلة"
		row.date_label = (
			format_datetime(row.communication_date) if row.communication_date else "غير محدد"
		)
	return frappe._dict(
		can_manage=(
			frappe.session.user == "Administrator"
			or "System Manager" in frappe.get_roles(frappe.session.user)
		),
		password_policy=bool(settings.enable_password_policy),
		minimum_password_score=int(settings.minimum_password_score or 2),
		consecutive_attempts=int(settings.allow_consecutive_login_attempts or 10),
		login_retry_seconds=int(settings.allow_login_after_fail or 60),
		session_expiry=settings.session_expiry or "170:00",
		deny_multiple_sessions=bool(settings.deny_multiple_sessions),
		username_login=bool(settings.allow_login_using_user_name),
		two_factor_auth=bool(settings.enable_two_factor_auth),
		restricted_users=frappe.db.count("User", {"restrict_ip": ["!=", ""]}),
		failed_logins_today=frappe.db.count(
			"Activity Log",
			{
				"operation": "Login",
				"status": "Failed",
				"communication_date": [">=", get_datetime(nowdate())],
			},
		),
		inactive_users=frappe.db.count("User", {"enabled": 0, "name": ["!=", "Guest"]}),
		recent_activity=recent_activity,
	)


def _role_scope(role_name):
	return {
		"System Manager": ["الحسابات", "الإعدادات", "البيانات", "الأمان"],
		"Center Director": ["التشغيل", "الحوكمة", "التقارير", "الإدارة"],
		"Consultation Supervisor": ["الفرز", "الإسناد", "المراجعة", "التصعيد"],
		"Case Coordinator": ["الطلبات", "المواعيد", "الملفات"],
		"Intake Coordinator": ["الاستقبال", "الاكتمال", "التواصل"],
		"Operations Officer": ["الدعم", "التشغيل", "المتابعة"],
		"Consultant": ["الحالات المسندة", "الجلسات", "الخطط", "المقاييس"],
		"Assessment Manager": ["بناء المقاييس", "النشر", "المراجعة"],
		"Content Manager": ["الموارد", "المحتوى", "الإعلانات"],
	}.get(role_name, [])


def build_admin_catalog_context(context, section: str):
	from consultation_center.api.admin_records import get_resource_ui_schema

	pages = {
		"services": (
			"الخدمات الاستشارية",
			"الخدمة ورحلة المستفيد",
			"تعريف الخدمات ومدتها وطريقة تقديمها وسياسات المتابعة.",
			"/app/consultation-service",
		),
		"consents": (
			"نماذج الموافقة",
			"الخدمة ورحلة المستفيد",
			"الموافقات المطلوبة من المستفيد وولي الأمر وربطها بالخدمات.",
			"/app/consent-template",
		),
		"forms": (
			"النماذج",
			"الخدمة ورحلة المستفيد",
			"نقاط جمع البيانات التي تظهر خلال رحلة المستفيد.",
			"/app/doctype",
		),
		"website": (
			"محتوى الموقع",
			"المحتوى والتواصل",
			"إدارة الرسالة العامة والصفحات التي يراها الزائر قبل تسجيل الدخول.",
			"/app/rushd-website-settings/Rushd%20Website%20Settings",
		),
		"testimonials": (
			"آراء المستفيدين",
			"المحتوى والتواصل",
			"راجع موافقة النشر والصياغة العامة قبل إظهار أي رأي في الصفحة الرئيسية.",
			"/app/rushd-testimonial",
		),
		"announcements": (
			"الإعلانات",
			"المحتوى والتواصل",
			"تنبيهات موجهة للفريق أو فئات محددة داخل المنصة.",
			"/app/internal-announcement",
		),
		"resources": (
			"الموارد",
			"المحتوى والتواصل",
			"الأدلة والمواد المساندة المنشورة للمستفيدين والفريق.",
			"/app/resource-content",
		),
		"message-templates": (
			"قوالب الرسائل",
			"المحتوى والتواصل",
			"الرسائل الموحدة التي ترسلها المنصة عند الأحداث التشغيلية.",
			"/app/notification",
		),
		"privacy": (
			"الخصوصية والموافقات",
			"الحوكمة والمتابعة",
			"حالة موافقات استخدام البيانات وسحبها وتوثيقها.",
			"/app/consent-record",
		),
		"audit": (
			"سجل التدقيق",
			"الحوكمة والمتابعة",
			"أحدث التغييرات المسجلة لمعرفة من غيّر ماذا ومتى.",
			"/app/version",
		),
		"complaints": (
			"الشكاوى والبلاغات",
			"الحوكمة والمتابعة",
			"متابعة الاستقبال والتحقيق والرد والإغلاق.",
			"/app/complaint",
		),
		"integrations": (
			"التكاملات",
			"الحوكمة والمتابعة",
			"نقاط الاتصال بالرسائل والبريد والخدمات الخارجية.",
			"/app/integrations",
		),
	}
	title, eyebrow, description, technical_url = pages[section]
	build_admin_context(context, "admin-settings", title)
	context.catalog_title = title
	context.catalog_eyebrow = eyebrow
	context.catalog_description = description
	context.catalog_technical_url = technical_url
	context.catalog_rows = _get_admin_catalog_rows(section)
	context.catalog_empty = "لا توجد سجلات في هذا القسم بعد"
	context.catalog_section = section
	context.catalog_schema = get_resource_ui_schema(section)


def _get_admin_catalog_rows(section):
	if section == "services":
		rows = frappe.db.get_all(
			"Consultation Service",
			fields=["name", "service_name", "service_code", "category", "active", "duration_minutes", "delivery_modes"],
			order_by="active desc, service_name asc",
		)
		return [
			_catalog_row(
				row.service_name,
				f"{row.service_code} · {row.category or 'دون تصنيف'}",
				f"{row.duration_minutes or 0} دقيقة · {_admin_value_label(row.delivery_modes) if row.delivery_modes else 'طريقة التقديم غير محددة'}",
				"نشطة" if row.active else "موقوفة",
				row.active,
				record_name=row.name,
			)
			for row in rows
		]
	if section == "consents":
		rows = frappe.db.get_all(
			"Consent Template",
			fields=["name", "template_title", "template_code", "consent_scope", "active", "requires_guardian", "service"],
			order_by="active desc, template_title asc",
		)
		return [
			_catalog_row(
				row.template_title,
				f"{row.template_code} · {_admin_value_label(row.consent_scope)}",
				f"{'يتطلب ولي الأمر' if row.requires_guardian else 'موافقة المستفيد'} · {row.service or 'كل الخدمات'}",
				"نشط" if row.active else "موقوف",
				row.active,
				record_name=row.name,
			)
			for row in rows
		]
	if section == "forms":
		return [
			_catalog_row("مقاييس المتابعة", "قبل الجلسات وبعدها", "أنشئ البنود والأبعاد وقواعد الاحتساب والسلامة.", "جاهز", 1, "/admin/assessments"),
			_catalog_row("نماذج الموافقة", "المستفيد وولي الأمر", "اضبط نطاق الموافقة وربطها بالخدمة.", "جاهز", 1, "/admin/consents"),
			_catalog_row("الشكاوى والبلاغات", "استقبال ومتابعة", "نموذج منظم للبلاغ والاستجابة والإغلاق.", "جاهز", 1, "/admin/complaints"),
		]
	if section == "website":
		settings = frappe.get_single("Rushd Website Settings")
		testimonial_count = frappe.db.count(
			"Rushd Testimonial",
			{"active": 1, "consent_confirmed": 1},
		)
		return [
			_catalog_row("الصفحة الرئيسية", settings.hero_title or "رُشد", settings.hero_description or "لم يحدد وصف رئيسي", "منشورة", 1, "/"),
			_catalog_row("آراء المستفيدين", "محتوى موثّق بموافقة", f"{testimonial_count} آراء منشورة", "منشورة" if testimonial_count else "بانتظار المحتوى", bool(testimonial_count), "/admin/testimonials"),
			_catalog_row("رحلة المستفيد", "خطوات الموقع العامة", f"{len(settings.journey_steps or [])} خطوات معرفة", "منشورة", 1, "/#journey"),
			_catalog_row("الأسئلة الشائعة", "محتوى مساعد للزوار", f"{len(settings.faqs or [])} أسئلة", "منشورة", 1, "/#faq"),
		]
	if section == "testimonials":
		rows = frappe.db.get_all(
			"Rushd Testimonial",
			fields=["name", "display_name", "service_label", "quote", "active", "consent_confirmed", "consent_date"],
			order_by="active desc, sort_order asc, modified desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.display_name or "مستفيد من رُشد",
				row.service_label or "تجربة مع رُشد",
				(row.quote or "دون نص")[:180],
				"منشور" if row.active and row.consent_confirmed else "غير منشور",
				row.active and row.consent_confirmed,
				record_name=row.name,
			)
			for row in rows
		]
	if section == "announcements":
		rows = frappe.db.get_all(
			"Internal Announcement",
			fields=["name", "title", "audience", "priority", "active", "start_date", "end_date", "summary"],
			order_by="active desc, modified desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.title,
				f"{_admin_value_label(row.audience)} · {_admin_value_label(row.priority)}",
				row.summary or "دون ملخص",
				"نشط" if row.active else "متوقف",
				row.active,
				record_name=row.name,
			)
			for row in rows
		]
	if section == "resources":
		rows = frappe.db.get_all(
			"Resource Content",
			fields=["name", "title", "content_type", "audience", "active", "summary"],
			order_by="active desc, modified desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.title,
				f"{_admin_value_label(row.content_type)} · {_admin_value_label(row.audience)}",
				row.summary or "دون ملخص",
				"منشور" if row.active else "مسودة",
				row.active,
				record_name=row.name,
			)
			for row in rows
		]
	if section == "message-templates":
		rows = frappe.db.get_all(
			"Notification",
			fields=["name", "subject", "document_type", "event", "enabled"],
			order_by="enabled desc, modified desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.name,
				f"{_admin_value_label(row.document_type)} · {_admin_value_label(row.event)}",
				row.subject or "دون عنوان",
				"مفعّل" if row.enabled else "متوقف",
				row.enabled,
				record_name=row.name,
			)
			for row in rows
		]
	if section == "privacy":
		rows = frappe.db.get_all(
			"Consent Record",
			fields=["name", "beneficiary", "guardian", "consent_role", "status", "granted_at", "withdrawn_at"],
			order_by="modified desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.beneficiary or row.name,
				f"{_admin_value_label(row.consent_role)} · {_status_label(row.status)}",
				f"{'ولي الأمر: ' + row.guardian if row.guardian else 'موافقة مباشرة'}",
				_status_label(row.status),
				row.status == "Granted",
				record_name=row.name,
			)
			for row in rows
		]
	if section == "audit":
		rows = frappe.db.get_all(
			"Version",
			fields=["ref_doctype", "docname", "owner", "creation"],
			order_by="creation desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.docname,
				row.ref_doctype,
				f"عدّله {row.owner} · {format_datetime(row.creation)}",
				"تغيير مسجل",
				1,
			)
			for row in rows
		]
	if section == "complaints":
		rows = frappe.db.get_all(
			"Complaint",
			fields=["name", "beneficiary", "complaint_type", "priority", "status", "details"],
			order_by="modified desc",
			limit=100,
		)
		return [
			_catalog_row(
				row.name,
				f"{_admin_value_label(row.complaint_type)} · {_admin_value_label(row.priority)}",
				row.details or "دون تفاصيل",
				_status_label(row.status),
				row.status in {"Resolved", "Closed"},
				record_name=row.name,
			)
			for row in rows
		]
	if section == "integrations":
		return [
			_catalog_row("البريد الإلكتروني", "إرسال التنبيهات والرسائل", "راجع الحساب المرسل والقوالب قبل تفعيل الإرسال الخارجي.", "يحتاج تحقق", 0),
			_catalog_row("الرسائل النصية", "قناة اختيارية", "لا يوجد مزود رسائل معتمد من هذه الصفحة حاليًا.", "غير مربوط", 0),
			_catalog_row("الاجتماعات عن بُعد", "روابط الجلسات", "تُحفظ الروابط في المواعيد مع ضوابط وصول الحالة.", "متاح يدويًا", 1),
		]
	return []


def _catalog_row(title, meta, description, status, positive, href=None, record_name=None):
	return frappe._dict(
		title=title,
		meta=meta,
		description=description,
		status=status,
		positive=bool(positive),
		href=href,
		record_name=record_name,
	)


def _status_label(value):
	return {
		"Granted": "ممنوحة",
		"Pending": "معلقة",
		"Withdrawn": "مسحوبة",
		"Expired": "منتهية",
		"Submitted": "مقدمة",
		"Open": "مفتوحة",
		"Under Review": "قيد المراجعة",
		"Action Required": "تتطلب إجراء",
		"Resolved": "محلولة",
		"Closed": "مغلقة",
	}.get(value, value or "غير محدد")


def _admin_value_label(value):
	return {
		"Online": "عن بُعد",
		"In Person": "حضوري",
		"Both": "حضوري وعن بُعد",
		"General": "عام",
		"Privacy": "الخصوصية",
		"Service": "الخدمة",
		"Minor Protection": "حماية القاصر",
		"Data Sharing": "مشاركة البيانات",
		"All": "الجميع",
		"Beneficiary": "المستفيد",
		"Guardian": "ولي الأمر",
		"Consultant": "المستشار",
		"Consultation Supervisor": "المشرفون",
		"Operations": "فريق التشغيل",
		"Normal": "عادية",
		"High": "عالية",
		"Urgent": "عاجلة",
		"Low": "منخفضة",
		"Article": "مقال",
		"Guide": "دليل",
		"File": "ملف",
		"Video": "فيديو",
		"External Link": "رابط خارجي",
		"New": "عند الإنشاء",
		"Save": "عند الحفظ",
		"Submit": "عند الاعتماد",
		"Cancel": "عند الإلغاء",
		"Service Feedback": "تقييم الخدمة",
		"Confidential Complaint": "شكوى سرية",
		"Suggestion": "اقتراح",
		"Change Consultant": "طلب تغيير مستشار",
	}.get(value, value or "غير محدد")


def get_admin_case_context(case_name: str | None = None, query: str | None = None):
	cases = get_supervised_cases(frappe.session.user)
	query = (query or "").strip().casefold()
	if query:
		cases = [
			row
			for row in cases
			if query
			in " ".join(
				[
					row.name,
					row.beneficiary_name or "",
					row.consultant_name or "",
					row.service_name or "",
				]
			).casefold()
		]
	selected = get_supervised_case_detail(case_name, cases) if case_name else None
	return frappe._dict(cases=cases, selected_case=selected, query=query)


def get_admin_assessments():
	rows = frappe.db.get_all(
		"Assessment Template",
		fields=[
			"name",
			"template_title",
			"template_code",
			"active",
			"category",
			"instrument_kind",
			"validation_status",
			"responder",
			"result_visibility",
			"current_published_version",
			"modified",
		],
		order_by="active desc, template_title asc",
	)
	for row in rows:
		row.versions = frappe.db.count(
			"Assessment Version",
			{"assessment_template": row.name},
		)
		row.submissions = frappe.db.count(
			"Assessment Submission",
			{"assessment_template": row.name},
		)
		row.responder_label = {
			"Beneficiary": "المستفيد",
			"Guardian": "ولي الأمر",
			"Consultant": "المستشار",
			"Supervisor": "المشرف",
			"Mixed": "أكثر من طرف",
		}.get(row.responder, row.responder)
		row.instrument_kind_label = {
			"Administrative Form": "نموذج إداري",
			"Satisfaction Survey": "استبيان رضا",
			"Outcome Measure": "مقياس متابعة",
			"Safety Screener": "فاحص سلامة",
		}.get(row.instrument_kind, row.instrument_kind)
		row.validation_status_label = {
			"Internal Draft": "مسودة داخلية",
			"Content Reviewed": "مراجعة محتوى",
			"Piloted": "مجرّبة مبدئيًا",
			"Validated": "متحقق منها",
			"Licensed": "مرخّصة",
		}.get(row.validation_status, row.validation_status)
		row.visibility_label = {
			"Never": "لا تظهر للمستفيد",
			"After Professional Review": "بعد المراجعة المهنية",
		}.get(row.result_visibility, row.result_visibility)
	return rows
