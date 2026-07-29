from collections.abc import Callable

import frappe
from frappe.utils import getdate, nowdate

UNRESTRICTED_ROLES = {"System Manager", "Center Director"}
OPERATIONS_ROLES = {"Consultation Supervisor"}


def has_admin_app_access() -> bool:
	"""Keep the Desk administration app separate from role-specific web portals."""
	user = frappe.session.user
	return user == "Administrator" or bool(_roles(user) & UNRESTRICTED_ROLES)


def _user(user: str | None) -> str:
	return user or frappe.session.user


def _roles(user: str) -> set[str]:
	return set(frappe.get_roles(user))


def _is_unrestricted(user: str) -> bool:
	return user == "Administrator" or bool(_roles(user) & UNRESTRICTED_ROLES)


def _is_supervisor(user: str) -> bool:
	return "Consultation Supervisor" in _roles(user)


def _escape(user: str) -> str:
	return frappe.db.escape(user)


def _or_conditions(conditions: list[str]) -> str:
	return f"({' or '.join(conditions)})" if conditions else "1=0"


def _consultant_condition(consultant_expression: str, user: str) -> str:
	return f"""exists (
		select 1
		from `tabConsultant` rushd_consultant
		where rushd_consultant.name = {consultant_expression}
			and rushd_consultant.user = {_escape(user)}
			and rushd_consultant.active = 1
	)"""


def _guardian_condition(beneficiary_expression: str, scope: str, user: str) -> str:
	allowed_scopes = {
		"can_view_profile",
		"can_view_requests",
		"can_view_case",
		"can_manage_appointments",
		"can_view_reports",
	}
	if scope not in allowed_scopes:
		raise ValueError(f"Unsupported guardian scope: {scope}")

	return f"""exists (
		select 1
		from `tabGuardian Authorization` rushd_auth
		inner join `tabGuardian` rushd_guardian
			on rushd_guardian.name = rushd_auth.guardian
		where rushd_auth.beneficiary = {beneficiary_expression}
			and rushd_guardian.portal_user = {_escape(user)}
			and rushd_guardian.status = 'Active'
			and rushd_auth.authorization_status = 'Active'
			and rushd_auth.`{scope}` = 1
			and rushd_auth.effective_from <= current_date
			and (rushd_auth.effective_to is null or rushd_auth.effective_to >= current_date)
	)"""


def beneficiary_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES or "Case Coordinator" in roles:
		return ""

	conditions = []
	if "Beneficiary" in roles:
		conditions.append(f"`tabBeneficiary`.portal_user = {_escape(user)}")
	if "Guardian" in roles:
		conditions.append(_guardian_condition("`tabBeneficiary`.name", "can_view_profile", user))
	if "Consultant" in roles:
		conditions.append(
			f"""exists (
				select 1
				from `tabConsultation Case` rushd_case
				inner join `tabConsultant` rushd_consultant
					on rushd_consultant.name = rushd_case.primary_consultant
				where rushd_case.beneficiary = `tabBeneficiary`.name
					and rushd_consultant.user = {_escape(user)}
					and rushd_consultant.active = 1
			)"""
		)
	return _or_conditions(conditions)


def guardian_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES or "Case Coordinator" in roles:
		return ""
	if "Guardian" in roles:
		return f"`tabGuardian`.portal_user = {_escape(user)}"
	return "1=0"


def guardian_authorization_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES or "Case Coordinator" in roles:
		return ""
	if "Guardian" in roles:
		return f"""exists (
			select 1 from `tabGuardian` rushd_guardian
			where rushd_guardian.name = `tabGuardian Authorization`.guardian
				and rushd_guardian.portal_user = {_escape(user)}
		)"""
	return "1=0"


def consent_record_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES:
		return ""

	conditions = []
	if "Beneficiary" in roles:
		conditions.append(
			f"""exists (
				select 1 from `tabBeneficiary` rushd_beneficiary
				where rushd_beneficiary.name = `tabConsent Record`.beneficiary
					and rushd_beneficiary.portal_user = {_escape(user)}
			)"""
		)
	if "Guardian" in roles:
		conditions.append(
			f"""exists (
				select 1
				from `tabGuardian` rushd_guardian
				inner join `tabGuardian Authorization` rushd_auth
					on rushd_auth.guardian = rushd_guardian.name
				where rushd_guardian.name = `tabConsent Record`.guardian
					and rushd_guardian.portal_user = {_escape(user)}
					and rushd_auth.beneficiary = `tabConsent Record`.beneficiary
					and rushd_auth.authorization_status = 'Active'
					and rushd_auth.effective_from <= current_date
					and (rushd_auth.effective_to is null or rushd_auth.effective_to >= current_date)
			)"""
		)
	return _or_conditions(conditions)


def consultant_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES or "Case Coordinator" in roles:
		return ""
	if "Consultant" in roles:
		return f"`tabConsultant`.user = {_escape(user)}"
	return "1=0"


def availability_query(user: str | None = None) -> str:
	return _consultant_owned_doctype_query("Consultant Availability Rule", user)


def time_off_query(user: str | None = None) -> str:
	return _consultant_owned_doctype_query("Consultant Time Off", user)


def _consultant_owned_doctype_query(doctype: str, user: str | None = None) -> str:
	user = _user(user)
	if _is_unrestricted(user) or _is_supervisor(user):
		return ""
	if "Consultant" in _roles(user):
		return _consultant_condition(f"`tab{doctype}`.consultant", user)
	return "1=0"


def request_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES or "Case Coordinator" in roles:
		return ""

	conditions = []
	if "Beneficiary" in roles:
		conditions.append(
			f"""exists (
				select 1 from `tabBeneficiary` rushd_beneficiary
				where rushd_beneficiary.name = `tabConsultation Request`.beneficiary
					and rushd_beneficiary.portal_user = {_escape(user)}
			)"""
		)
	if "Guardian" in roles:
		conditions.append(
			_guardian_condition(
				"`tabConsultation Request`.beneficiary",
				"can_view_requests",
				user,
			)
		)
	return _or_conditions(conditions)


def case_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & OPERATIONS_ROLES:
		return ""

	conditions = []
	if "Case Coordinator" in roles:
		conditions.append(f"`tabConsultation Case`.case_owner = {_escape(user)}")
	if "Consultant" in roles:
		conditions.append(
			_consultant_condition("`tabConsultation Case`.primary_consultant", user)
		)
	if "Beneficiary" in roles:
		conditions.append(
			f"""exists (
				select 1 from `tabBeneficiary` rushd_beneficiary
				where rushd_beneficiary.name = `tabConsultation Case`.beneficiary
					and rushd_beneficiary.portal_user = {_escape(user)}
			)"""
		)
	if "Guardian" in roles:
		conditions.append(
			_guardian_condition("`tabConsultation Case`.beneficiary", "can_view_case", user)
		)
	return _or_conditions(conditions)


def appointment_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if (
		_is_unrestricted(user)
		or roles & OPERATIONS_ROLES
		or "Case Coordinator" in roles
	):
		return ""

	conditions = []
	if "Consultant" in roles:
		conditions.append(
			_consultant_condition("`tabConsultation Appointment`.consultant", user)
		)
	if "Beneficiary" in roles:
		conditions.append(
			f"""exists (
				select 1 from `tabBeneficiary` rushd_beneficiary
				where rushd_beneficiary.name = `tabConsultation Appointment`.beneficiary
					and rushd_beneficiary.portal_user = {_escape(user)}
			)"""
		)
	if "Guardian" in roles:
		conditions.append(
			_guardian_condition(
				"`tabConsultation Appointment`.beneficiary",
				"can_manage_appointments",
				user,
			)
		)
	return _or_conditions(conditions)


def session_query(user: str | None = None) -> str:
	user = _user(user)
	if _is_unrestricted(user) or _is_supervisor(user):
		return ""
	if "Consultant" in _roles(user):
		return _consultant_condition("`tabConsultation Session`.consultant", user)
	return "1=0"


def plan_query(user: str | None = None) -> str:
	user = _user(user)
	if _is_unrestricted(user) or _is_supervisor(user):
		return ""
	conditions = []
	if "Consultant" in _roles(user):
		conditions.append(_consultant_condition("`tabConsultation Plan`.consultant", user))
	if "Beneficiary" in _roles(user):
		conditions.append(
			f"""exists (
				select 1 from `tabBeneficiary` rushd_beneficiary
				where rushd_beneficiary.name = `tabConsultation Plan`.beneficiary
					and rushd_beneficiary.portal_user = {_escape(user)}
					and `tabConsultation Plan`.status in ('Active', 'Completed')
			)"""
		)
	return _or_conditions(conditions)


def beneficiary_task_query(user: str | None = None) -> str:
	user = _user(user)
	if _is_unrestricted(user) or _is_supervisor(user):
		return ""
	conditions = []
	if "Consultant" in _roles(user):
		conditions.append(_consultant_condition("`tabBeneficiary Task`.consultant", user))
	if "Beneficiary" in _roles(user):
		conditions.append(
			f"""exists (
				select 1 from `tabBeneficiary` rushd_beneficiary
				where rushd_beneficiary.name = `tabBeneficiary Task`.beneficiary
					and rushd_beneficiary.portal_user = {_escape(user)}
			)"""
		)
	return _or_conditions(conditions)


def assessment_template_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or _is_supervisor(user) or "Assessment Manager" in roles:
		return ""
	if "Consultant" in roles:
		return "`tabAssessment Template`.active = 1"
	return "1=0"


def assessment_version_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or _is_supervisor(user) or "Assessment Manager" in roles:
		return ""
	if "Consultant" in roles:
		return "`tabAssessment Version`.status = 'Published'"
	return "1=0"


def assessment_submission_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or _is_supervisor(user) or "Assessment Manager" in roles:
		return ""
	if "Consultant" in roles:
		return _consultant_condition("`tabAssessment Submission`.consultant", user)
	return "1=0"


def case_referral_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user):
		return ""
	conditions = []
	if "Consultant" in roles:
		conditions.append(_consultant_condition("`tabCase Referral`.consultant", user))
	if "Consultation Supervisor" in roles:
		conditions.append(
			f"""exists (
				select 1 from `tabConsultation Case` rushd_case
				where rushd_case.name = `tabCase Referral`.case
					and rushd_case.supervisor = {_escape(user)}
			)"""
		)
	return _or_conditions(conditions)


def supervision_request_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user):
		return ""
	conditions = []
	if "Consultant" in roles:
		conditions.append(_consultant_condition("`tabSupervision Request`.consultant", user))
	if "Consultation Supervisor" in roles:
		conditions.append(f"`tabSupervision Request`.supervisor = {_escape(user)}")
	return _or_conditions(conditions)


def professional_escalation_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user):
		return ""
	conditions = []
	if "Consultant" in roles:
		conditions.append(
			_consultant_condition("`tabProfessional Escalation`.consultant", user)
		)
	if "Consultation Supervisor" in roles:
		conditions.append(
			f"`tabProfessional Escalation`.assigned_supervisor = {_escape(user)}"
		)
	return _or_conditions(conditions)


def support_ticket_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or roles & {"Operations Officer", "Case Coordinator"}:
		return ""
	if roles & {"Beneficiary", "Guardian"}:
		return f"`tabSupport Ticket`.requester = {_escape(user)}"
	return "1=0"


def complaint_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or "Quality Reviewer" in roles:
		return ""
	if roles & {"Beneficiary", "Guardian"}:
		return f"`tabComplaint`.complainant = {_escape(user)}"
	return "1=0"


def case_document_query(user: str | None = None) -> str:
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user) or _is_supervisor(user):
		return ""
	conditions = []
	if "Consultant" in roles:
		conditions.append(
			f"""exists (
				select 1 from `tabConsultation Case` rushd_case
				inner join `tabConsultant` rushd_consultant
					on rushd_consultant.name = rushd_case.primary_consultant
				where rushd_case.name = `tabCase Document`.case
					and rushd_consultant.user = {_escape(user)}
					and rushd_consultant.active = 1
			)"""
		)
	if "Beneficiary" in roles:
		conditions.append(f"""`tabCase Document`.visibility in ('Beneficiary','Beneficiary and Guardian') and exists (select 1 from `tabBeneficiary` b where b.name=`tabCase Document`.beneficiary and b.portal_user={_escape(user)})""")
	if "Guardian" in roles:
		conditions.append(f"""`tabCase Document`.visibility in ('Guardian','Beneficiary and Guardian') and {_guardian_condition("`tabCase Document`.beneficiary", "can_view_reports", user)}""")
	return _or_conditions(conditions)


QUERY_BY_DOCTYPE: dict[str, Callable[[str | None], str]] = {
	"Beneficiary": beneficiary_query,
	"Guardian": guardian_query,
	"Guardian Authorization": guardian_authorization_query,
	"Consent Record": consent_record_query,
	"Consultant": consultant_query,
	"Consultant Availability Rule": availability_query,
	"Consultant Time Off": time_off_query,
	"Consultation Request": request_query,
	"Consultation Case": case_query,
	"Consultation Appointment": appointment_query,
	"Consultation Session": session_query,
	"Consultation Plan": plan_query,
	"Beneficiary Task": beneficiary_task_query,
	"Assessment Template": assessment_template_query,
	"Assessment Version": assessment_version_query,
	"Assessment Submission": assessment_submission_query,
	"Case Referral": case_referral_query,
	"Supervision Request": supervision_request_query,
	"Professional Escalation": professional_escalation_query,
	"Support Ticket": support_ticket_query,
	"Complaint": complaint_query,
	"Case Document": case_document_query,
}


def has_permission(doc, user: str | None = None, ptype: str | None = None, **kwargs) -> bool:
	"""Deny direct-record access when the row is outside the user's Rushd scope."""
	user = _user(user)
	roles = _roles(user)
	if _is_unrestricted(user):
		return True
	if doc.doctype in {
		"Case Referral",
		"Supervision Request",
		"Professional Escalation",
	} and "Consultation Supervisor" in roles:
		return _supervisor_can_access_professional_record(doc, user)
	if doc.doctype == "Support Ticket":
		return bool(
			roles & {"Operations Officer", "Case Coordinator"}
			or doc.requester == user
		)
	if doc.doctype == "Complaint":
		return bool("Quality Reviewer" in roles or doc.complainant == user)
	if doc.doctype == "Case Document":
		if "Consultant" in roles:
			consultant = _consultant_name(user)
			return (
				frappe.db.get_value("Consultation Case", doc.case, "primary_consultant")
				== consultant
			)
		if "Beneficiary" in roles:
			return (
				doc.beneficiary == _beneficiary_for_user(user)
				and doc.visibility in {"Beneficiary", "Beneficiary and Guardian"}
			)
		if "Guardian" in roles:
			return (
				doc.visibility in {"Guardian", "Beneficiary and Guardian"}
				and doc.beneficiary in authorized_beneficiaries(user, "can_view_reports")
			)
		return False
	if roles & OPERATIONS_ROLES:
		return True
	if "Assessment Manager" in roles and doc.doctype in {
		"Assessment Template",
		"Assessment Version",
		"Assessment Submission",
	}:
		return True
	if "Case Coordinator" in roles:
		if doc.doctype == "Consultation Case":
			return doc.case_owner == user
		return doc.doctype in {
			"Beneficiary",
			"Guardian",
			"Guardian Authorization",
			"Consultant",
			"Consultation Request",
			"Consultation Appointment",
		}
	if "Consultant" in roles and _consultant_can_access(doc, user):
		return True
	if "Beneficiary" in roles and _beneficiary_can_access(doc, user):
		return True
	if "Guardian" in roles and _guardian_can_access(doc, user):
		return True
	return False


def _consultant_name(user: str) -> str | None:
	return frappe.db.get_value("Consultant", {"user": user, "active": 1}, "name")


def _consultant_can_access(doc, user: str) -> bool:
	consultant = _consultant_name(user)
	if not consultant:
		return False
	if doc.doctype == "Consultant":
		return doc.name == consultant or doc.user == user
	if doc.doctype in {"Consultant Availability Rule", "Consultant Time Off"}:
		return doc.consultant == consultant
	if doc.doctype == "Consultation Case":
		return doc.primary_consultant == consultant
	if doc.doctype == "Consultation Appointment":
		return doc.consultant == consultant
	if doc.doctype == "Consultation Session":
		return doc.consultant == consultant
	if doc.doctype in {"Consultation Plan", "Beneficiary Task"}:
		return doc.consultant == consultant
	if doc.doctype == "Assessment Template":
		return bool(doc.active)
	if doc.doctype == "Assessment Version":
		return doc.status == "Published"
	if doc.doctype == "Assessment Submission":
		return doc.consultant == consultant
	if doc.doctype in {"Case Referral", "Supervision Request", "Professional Escalation"}:
		return doc.consultant == consultant
	if doc.doctype == "Beneficiary":
		return bool(
			frappe.db.exists(
				"Consultation Case",
				{"beneficiary": doc.name, "primary_consultant": consultant},
			)
		)
	return False


def _supervisor_can_access_professional_record(doc, user: str) -> bool:
	if doc.doctype == "Supervision Request":
		return doc.supervisor == user
	if doc.doctype == "Professional Escalation":
		return doc.assigned_supervisor == user
	if doc.doctype == "Case Referral":
		return (
			frappe.db.get_value("Consultation Case", doc.case, "supervisor") == user
		)
	return False


def _beneficiary_for_user(user: str) -> str | None:
	return frappe.db.get_value("Beneficiary", {"portal_user": user}, "name")


def _beneficiary_can_access(doc, user: str) -> bool:
	beneficiary = _beneficiary_for_user(user)
	if not beneficiary:
		return False
	if doc.doctype == "Beneficiary":
		return doc.name == beneficiary or doc.portal_user == user
	if doc.doctype in {
		"Consultation Request",
		"Consultation Case",
		"Consultation Appointment",
		"Consent Record",
	}:
		return doc.beneficiary == beneficiary
	if doc.doctype == "Consultation Plan":
		return doc.beneficiary == beneficiary and doc.status in {"Active", "Completed"}
	if doc.doctype == "Beneficiary Task":
		return doc.beneficiary == beneficiary
	return False


def _guardian_for_user(user: str) -> str | None:
	return frappe.db.get_value("Guardian", {"portal_user": user, "status": "Active"}, "name")


def authorized_beneficiaries(user: str, scope: str) -> list[str]:
	guardian = _guardian_for_user(user)
	if not guardian:
		return []

	rows = frappe.db.get_all(
		"Guardian Authorization",
		filters={
			"guardian": guardian,
			"authorization_status": "Active",
			scope: 1,
		},
		fields=["beneficiary", "effective_from", "effective_to"],
	)
	today = getdate(nowdate())
	return [
		row.beneficiary
		for row in rows
		if (not row.effective_from or getdate(row.effective_from) <= today)
		and (not row.effective_to or getdate(row.effective_to) >= today)
	]


def can_manage_case_appointments(case_doc, user: str | None = None) -> bool:
	user = _user(user)
	if _is_unrestricted(user) or _is_supervisor(user) or "Case Coordinator" in _roles(user):
		return True
	if _beneficiary_for_user(user) == case_doc.beneficiary:
		return True

	guardian = _guardian_for_user(user)
	return bool(
		guardian
		and _has_active_guardian_scope(
			guardian,
			case_doc.beneficiary,
			"can_manage_appointments",
		)
	)


def _guardian_can_access(doc, user: str) -> bool:
	guardian = _guardian_for_user(user)
	if not guardian:
		return False
	if doc.doctype == "Guardian":
		return doc.name == guardian or doc.portal_user == user
	if doc.doctype == "Guardian Authorization":
		return doc.guardian == guardian
	if doc.doctype == "Consent Record":
		return doc.guardian == guardian and _has_active_guardian_scope(
			guardian,
			doc.beneficiary,
			"can_view_profile",
		)

	scope_by_doctype = {
		"Beneficiary": "can_view_profile",
		"Consultation Request": "can_view_requests",
		"Consultation Case": "can_view_case",
		"Consultation Appointment": "can_manage_appointments",
	}
	scope = scope_by_doctype.get(doc.doctype)
	beneficiary = doc.name if doc.doctype == "Beneficiary" else doc.get("beneficiary")
	return bool(scope and beneficiary and _has_active_guardian_scope(guardian, beneficiary, scope))


def _has_active_guardian_scope(guardian: str, beneficiary: str, scope: str) -> bool:
	auth = frappe.db.get_value(
		"Guardian Authorization",
		{
			"guardian": guardian,
			"beneficiary": beneficiary,
			"authorization_status": "Active",
			scope: 1,
		},
		["effective_from", "effective_to"],
		as_dict=True,
	)
	if not auth:
		return False

	today = getdate(nowdate())
	return (not auth.effective_from or getdate(auth.effective_from) <= today) and (
		not auth.effective_to or getdate(auth.effective_to) >= today
	)
