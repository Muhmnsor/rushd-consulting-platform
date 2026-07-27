from urllib.parse import urlencode

import frappe
import frappe.sessions
from frappe.utils import date_diff, format_date, getdate, nowdate

from consultation_center.portal import REQUEST_STATUS

ADMIN_ACCESS = {"System Manager", "Center Director"}
OPERATIONS_ACCESS = ADMIN_ACCESS | {"Case Coordinator", "Intake Coordinator", "Operations Officer"}
SUPERVISOR_ACCESS = ADMIN_ACCESS | {"Consultation Supervisor"}

ROLE_LABELS = {
	"System Manager": "مسؤول النظام",
	"Center Director": "مدير المركز",
	"Consultation Supervisor": "مشرف مهني",
	"Case Coordinator": "منسق حالات",
	"Intake Coordinator": "منسق استقبال وفرز",
	"Operations Officer": "موظف تشغيل",
}


def require_staff_access(allowed_roles: set[str]) -> tuple[str, set[str]]:
	user = frappe.session.user
	if user == "Guest":
		redirect_to = frappe.request.path if frappe.request else "/operations"
		frappe.redirect(f"/login?{urlencode({'redirect-to': redirect_to})}")

	roles = set(frappe.get_roles(user))
	if user != "Administrator" and not roles & allowed_roles:
		frappe.throw("ليس لديك صلاحية للوصول إلى هذه الواجهة", frappe.PermissionError)
	return user, roles


def build_staff_context(
	context,
	active_nav: str,
	title: str,
	staff_section: str,
	allowed_roles: set[str],
):
	user, roles = require_staff_access(allowed_roles)
	frappe.sessions.get_csrf_token()
	frappe.db.commit()
	display_name = frappe.db.get_value("User", user, "full_name") or user
	role_label = next(
		(ROLE_LABELS[role] for role in ROLE_LABELS if role in roles),
		"فريق رُشد",
	)
	if user == "Administrator":
		role_label = "مسؤول النظام"

	context.update(
		{
			"title": title,
			"no_cache": 1,
			"body_class": "rushd-staff-page",
			"active_nav": active_nav,
			"staff_section": staff_section,
			"staff_user": user,
			"display_name": display_name,
			"role_label": role_label,
		}
	)


def get_request_counts() -> dict[str, int]:
	statuses = (
		"Submitted",
		"Under Completeness Review",
		"Awaiting Beneficiary Information",
		"Ready for Triage",
		"Eligible",
		"Not Eligible",
	)
	return {
		status: frappe.db.count("Consultation Request", {"workflow_state": status})
		for status in statuses
	}


def get_staff_requests(states: tuple[str, ...] | list[str], limit: int | None = None):
	rows = frappe.db.get_all(
		"Consultation Request",
		filters={"workflow_state": ["in", states]},
		fields=[
			"name",
			"beneficiary",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"assigned_coordinator",
			"urgency",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)
	for row in rows:
		_decorate_request(row)
	return rows


def get_staff_request_detail(request_name: str | None):
	if not request_name:
		return None
	row = frappe.db.get_value(
		"Consultation Request",
		request_name,
		[
			"name",
			"beneficiary",
			"requested_service",
			"workflow_state",
			"request_datetime",
			"source",
			"urgency",
			"summary",
			"preferred_mode",
			"preferred_times",
			"eligibility_status",
			"screening_status",
			"assigned_coordinator",
			"operations_note",
			"beneficiary_action_note",
			"triage_note",
			"decision_by",
			"decision_on",
			"rejection_reason",
		],
		as_dict=True,
	)
	if not row:
		return None

	_decorate_request(row)
	beneficiary = frappe.db.get_value(
		"Beneficiary",
		row.beneficiary,
		[
			"beneficiary_name",
			"date_of_birth",
			"city",
			"mobile",
			"email",
			"guardian_required",
			"consent_status",
		],
		as_dict=True,
	)
	if beneficiary:
		beneficiary.age = (
			int(date_diff(nowdate(), beneficiary.date_of_birth) / 365.25)
			if beneficiary.date_of_birth
			else None
		)
		beneficiary.date_of_birth_label = (
			format_date(getdate(beneficiary.date_of_birth)) if beneficiary.date_of_birth else "غير مسجل"
		)
	row.beneficiary_profile = beneficiary
	return row


def _decorate_request(row):
	row.beneficiary_name = (
		frappe.db.get_value("Beneficiary", row.beneficiary, "beneficiary_name") or row.beneficiary
	)
	row.service_name = (
		frappe.db.get_value("Consultation Service", row.requested_service, "service_name")
		or row.requested_service
	)
	status = REQUEST_STATUS.get(row.workflow_state, REQUEST_STATUS["Submitted"])
	row.status_label = status["label"]
	row.status_tone = status["tone"]
	row.next_step = status["next_step"]
	row.request_date_label = format_date(row.request_datetime) if row.request_datetime else "—"
	row.mode_label = {
		"Online": "عن بُعد",
		"In Person": "حضوري",
		"Either": "لا فرق",
	}.get(row.get("preferred_mode"), "غير محدد")
