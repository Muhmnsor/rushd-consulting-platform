import re

import frappe
from frappe.auth import MAX_PASSWORD_SIZE
from frappe.core.doctype.user.user import handle_password_test_fail, test_password_strength
from frappe.utils import cint, strip_html_tags, today
from frappe.utils.password import update_password

PASSWORD_ADMIN_ROLES = {"System Manager"}
PROTECTED_USERS = {"Guest"}
MANAGED_STAFF_ROLES = {
	"System Manager",
	"Center Director",
	"Consultation Supervisor",
	"Case Coordinator",
	"Intake Coordinator",
	"Operations Officer",
	"Consultant",
	"Assessment Manager",
	"Content Manager",
}


@frappe.whitelist(methods=["POST"])
def set_user_password(
	user: str,
	new_password: str,
	logout_all_sessions: int | str = 1,
):
	"""Set a user's password directly without sending email."""
	_require_password_admin()
	user = (user or "").strip()
	if not user or not frappe.db.exists("User", user):
		frappe.throw("المستخدم غير موجود")
	if user in PROTECTED_USERS:
		frappe.throw("لا يمكن تغيير كلمة مرور هذا الحساب")
	if user == "Administrator" and frappe.session.user != "Administrator":
		frappe.throw(
			"لا يمكن تغيير كلمة مرور Administrator إلا من الحساب نفسه",
			frappe.PermissionError,
		)
	if not new_password:
		frappe.throw("اكتب كلمة المرور الجديدة")
	if len(new_password) > MAX_PASSWORD_SIZE:
		frappe.throw("كلمة المرور أطول من الحد المسموح")

	user_doc = frappe.get_doc("User", user)
	user_data = (
		user_doc.first_name,
		user_doc.middle_name,
		user_doc.last_name,
		user_doc.email,
		user_doc.birth_date,
	)
	result = test_password_strength(new_password, user_data=user_data)
	feedback = result.get("feedback") if result else None
	if feedback and not feedback.get("password_policy_validation_passed", False):
		handle_password_test_fail(feedback)

	update_password(
		user,
		new_password,
		logout_all_sessions=cint(logout_all_sessions),
	)
	frappe.db.set_value(
		"User",
		user,
		{
			"last_password_reset_date": today(),
			"reset_password_key": "",
		},
		update_modified=False,
	)
	user_doc.add_comment(
		"Info",
		f"تم تعيين كلمة المرور مباشرة بواسطة {frappe.session.user} دون إرسال بريد إلكتروني.",
	)

	return {
		"user": user,
		"message": "تم تعيين كلمة المرور دون إرسال رسالة للمستخدم",
	}


@frappe.whitelist(methods=["POST"])
def create_staff_user(
	full_name: str,
	email: str,
	roles: str | list | None = None,
	username: str | None = None,
):
	_require_password_admin()
	full_name = _clean(full_name, 140)
	email = _clean(email, 140).lower()
	username = _clean(username, 80)
	if not full_name or not email:
		frappe.throw("أكمل اسم الموظف والبريد الإلكتروني")
	if frappe.db.exists("User", email):
		frappe.throw("يوجد حساب بهذا البريد الإلكتروني")
	selected_roles = _parse_roles(roles)
	if not selected_roles:
		frappe.throw("اختر دورًا وظيفيًا واحدًا على الأقل")

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": full_name,
			"full_name": full_name,
			"username": username or None,
			"enabled": 1,
			"user_type": "System User",
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	user.add_roles(*selected_roles)
	return {
		"user": user.name,
		"message": "تم إنشاء حساب الموظف دون إرسال بريد. عيّن كلمة مروره من صفحة المستخدمين.",
	}


@frappe.whitelist(methods=["POST"])
def update_user_status(user: str, enabled: int | str):
	_require_password_admin()
	user = (user or "").strip()
	if not frappe.db.exists("User", user):
		frappe.throw("المستخدم غير موجود")
	if user in {"Administrator", "Guest"}:
		frappe.throw("لا يمكن تغيير حالة هذا الحساب")
	if user == frappe.session.user and not cint(enabled):
		frappe.throw("لا يمكنك تعطيل حسابك الحالي")
	doc = frappe.get_doc("User", user)
	doc.enabled = cint(enabled)
	doc.save(ignore_permissions=True)
	return {
		"user": user,
		"enabled": bool(doc.enabled),
		"message": "تم تفعيل الحساب" if doc.enabled else "تم إيقاف الحساب ومنع دخوله",
	}


@frappe.whitelist(methods=["POST"])
def update_user_roles(user: str, roles: str | list | None = None):
	_require_password_admin()
	user = (user or "").strip()
	if not frappe.db.exists("User", user):
		frappe.throw("المستخدم غير موجود")
	if user in {"Administrator", "Guest"}:
		frappe.throw("لا تُدار أدوار هذا الحساب من الواجهة المبسطة")
	selected_roles = _parse_roles(roles)
	if user == frappe.session.user and not set(selected_roles) & PASSWORD_ADMIN_ROLES:
		frappe.throw("لا يمكنك إزالة صلاحية إدارة النظام من حسابك الحالي")

	doc = frappe.get_doc("User", user)
	existing = {row.role for row in doc.roles}
	for role in existing & MANAGED_STAFF_ROLES - set(selected_roles):
		doc.remove_roles(role)
	for role in set(selected_roles) - existing:
		doc.add_roles(role)
	return {
		"user": user,
		"roles": selected_roles,
		"message": "تم تحديث مسؤوليات المستخدم وصلاحياته",
	}


@frappe.whitelist(methods=["POST"])
def update_security_settings(
	enable_password_policy: int | str = 1,
	minimum_password_score: int | str = 3,
	allow_consecutive_login_attempts: int | str = 5,
	allow_login_after_fail: int | str = 60,
	session_expiry: str = "12:00",
	deny_multiple_sessions: int | str = 1,
	allow_login_using_user_name: int | str = 1,
	enable_two_factor_auth: int | str = 0,
):
	_require_password_admin()
	score = cint(minimum_password_score)
	attempts = cint(allow_consecutive_login_attempts)
	retry_seconds = cint(allow_login_after_fail)
	session_expiry = _clean(session_expiry, 12)
	if score not in {1, 2, 3, 4}:
		frappe.throw("درجة قوة كلمة المرور غير صالحة")
	if attempts < 1 or attempts > 20:
		frappe.throw("عدد محاولات الدخول يجب أن يكون بين 1 و20")
	if retry_seconds < 10 or retry_seconds > 3600:
		frappe.throw("مدة الانتظار بعد الفشل يجب أن تكون بين 10 و3600 ثانية")
	if not re.fullmatch(r"\d{1,3}:[0-5]\d", session_expiry):
		frappe.throw("مدة انتهاء الجلسة غير صالحة؛ استخدم مثل 12:00")

	settings = frappe.get_single("System Settings")
	settings.enable_password_policy = cint(enable_password_policy)
	settings.minimum_password_score = str(score)
	settings.allow_consecutive_login_attempts = attempts
	settings.allow_login_after_fail = retry_seconds
	settings.session_expiry = session_expiry
	settings.deny_multiple_sessions = cint(deny_multiple_sessions)
	settings.allow_login_using_user_name = cint(allow_login_using_user_name)
	settings.enable_two_factor_auth = cint(enable_two_factor_auth)
	settings.save(ignore_permissions=True)
	return {"message": "تم تحديث سياسات الدخول والحماية"}


def _require_password_admin():
	if frappe.session.user == "Administrator":
		return
	if not set(frappe.get_roles(frappe.session.user)) & PASSWORD_ADMIN_ROLES:
		frappe.throw(
			"ليس لديك صلاحية لتغيير كلمات مرور المستخدمين",
			frappe.PermissionError,
		)


def _parse_roles(value):
	if isinstance(value, str):
		try:
			value = frappe.parse_json(value)
		except (TypeError, ValueError):
			value = [item.strip() for item in value.split(",") if item.strip()]
	value = list(dict.fromkeys(value or []))
	invalid = set(value) - MANAGED_STAFF_ROLES
	if invalid:
		frappe.throw("توجد أدوار غير مسموح بإدارتها من هذه الصفحة")
	for role in value:
		if not frappe.db.exists("Role", role):
			frappe.throw(f"الدور {role} غير موجود")
	return value


def _clean(value, limit):
	value = strip_html_tags(str(value or "")).strip()
	if len(value) > limit:
		frappe.throw("القيمة أطول من الحد المسموح")
	return value
