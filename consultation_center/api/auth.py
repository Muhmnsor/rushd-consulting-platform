import frappe
from frappe.core.doctype.user.user import sign_up as frappe_sign_up


LOGIN_DESTINATION = "/login#login"


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def logout():
	"""End the current session and safely return portal users to Rushd login."""
	frappe.local.login_manager.logout()
	frappe.db.commit()

	if frappe.request.method == "GET":
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = LOGIN_DESTINATION

	return {"redirect_to": LOGIN_DESTINATION}


@frappe.whitelist(allow_guest=True)
def sign_up(
	email: str,
	full_name: str,
	redirect_to: str | None = None,
	password: str | None = None,
):
	"""Use Frappe's secure sign-up flow, then prepare the Rushd beneficiary account."""
	existing_user = frappe.db.exists("User", {"email": email})
	if existing_user and password:
		frappe.throw("يوجد حساب مسجل بهذا البريد. استخدم تسجيل الدخول.")

	result = frappe_sign_up(email, full_name, redirect_to or "/beneficiary")

	if not existing_user and result[0] in (1, 2):
		user = frappe.db.get_value("User", {"email": email}, "name")
		if user:
			if password:
				_set_signup_password(user, password)
			_provision_beneficiary(user)

	return result


def _set_signup_password(user: str, password: str):
	user_doc = frappe.get_doc("User", user)
	user_doc.new_password = password
	user_doc.flags.ignore_password_policy = False
	user_doc.save(ignore_permissions=True)


def _provision_beneficiary(user: str):
	user_doc = frappe.get_doc("User", user)
	user_doc.add_roles("Beneficiary")

	if frappe.db.exists("Beneficiary", {"portal_user": user}):
		return

	frappe.get_doc(
		{
			"doctype": "Beneficiary",
			"naming_series": "BEN-.YYYY.-",
			"beneficiary_name": user_doc.full_name or user_doc.first_name or user,
			"status": "Active",
			"email": user_doc.email,
			"preferred_language": "Arabic",
			"portal_user": user,
			"guardian_required": 0,
			"confidentiality_level": "Standard",
			"consent_status": "Not Requested",
		}
	).insert(ignore_permissions=True)
