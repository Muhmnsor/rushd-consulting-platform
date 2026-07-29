import frappe
from frappe.utils import cint, get_datetime, now_datetime, strip_html_tags

from consultation_center.consultant_portal import get_current_consultant

ATTENDANCE_VALUES = {"Attended", "No Show", "Late"}


@frappe.whitelist(methods=["POST"])
def record_appointment_attendance(appointment: str, attendance_status: str):
	consultant = _require_consultant()
	if attendance_status not in ATTENDANCE_VALUES:
		frappe.throw("حالة الحضور غير صالحة")

	doc = _get_owned_appointment(appointment, consultant.name)
	if doc.status in {"Cancelled by Beneficiary", "Cancelled by Center", "Expired"}:
		frappe.throw("لا يمكن تسجيل الحضور لموعد ملغى أو منتهي")
	if get_datetime(doc.start_datetime) > now_datetime():
		frappe.throw("لا يمكن تسجيل الحضور قبل بدء الموعد")

	doc.attendance_status = attendance_status
	doc.status = "No Show" if attendance_status == "No Show" else "Completed"
	doc.save(ignore_permissions=True)

	return {
		"name": doc.name,
		"attendance_status": doc.attendance_status,
		"message": {
			"Attended": "تم تسجيل حضور المستفيد",
			"Late": "تم تسجيل حضور المستفيد متأخرًا",
			"No Show": "تم تسجيل عدم الحضور",
		}[attendance_status],
	}


@frappe.whitelist(methods=["POST"])
def save_session_documentation(
	appointment: str,
	session_name: str | None = None,
	topic: str | None = None,
	goals_addressed: str | None = None,
	interventions: str | None = None,
	professional_notes: str | None = None,
	follow_up: str | None = None,
	beneficiary_summary: str | None = None,
	guardian_summary_allowed: int | str = 0,
	guardian_summary: str | None = None,
	next_action: str | None = None,
	next_action_due: str | None = None,
	actual_start: str | None = None,
	actual_end: str | None = None,
	submit_for_review: int | str = 0,
):
	consultant = _require_consultant()
	appointment_doc = _get_owned_appointment(appointment, consultant.name)
	if appointment_doc.attendance_status not in {"Attended", "Late"}:
		frappe.throw("سجل حضور المستفيد قبل توثيق الجلسة")

	if session_name:
		doc = frappe.get_doc("Consultation Session", session_name)
		if doc.consultant != consultant.name or doc.appointment != appointment_doc.name:
			frappe.throw("لا يمكنك تعديل سجل الجلسة", frappe.PermissionError)
		if doc.status in {"Pending Review", "Approved", "Cancelled"}:
			frappe.throw("سجل الجلسة في حالة لا تسمح بالتعديل")
	else:
		existing = frappe.db.get_value(
			"Consultation Session",
			{"appointment": appointment_doc.name},
			"name",
		)
		if existing:
			doc = frappe.get_doc("Consultation Session", existing)
			if doc.status in {"Pending Review", "Approved", "Cancelled"}:
				frappe.throw("سجل الجلسة في حالة لا تسمح بالتعديل")
		else:
			doc = frappe.new_doc("Consultation Session")
			doc.appointment = appointment_doc.name
			doc.case = appointment_doc.case
			doc.beneficiary = appointment_doc.beneficiary
			doc.consultant = appointment_doc.consultant
			doc.service = appointment_doc.service
			doc.attendance_status = appointment_doc.attendance_status

	values = {
		"topic": _clean_text(topic, 1000, "موضوع الجلسة"),
		"goals_addressed": _clean_text(goals_addressed, 2000, "الأهداف"),
		"interventions": _clean_text(interventions, 5000, "التدخلات"),
		"professional_notes": _clean_text(
			professional_notes,
			8000,
			"الملاحظة المهنية",
		),
		"follow_up": _clean_text(follow_up, 4000, "المتابعة"),
		"beneficiary_summary": _clean_text(
			beneficiary_summary,
			4000,
			"ملخص المستفيد",
		),
		"guardian_summary": _clean_text(
			guardian_summary,
			4000,
			"ملخص ولي الأمر",
		),
		"next_action": _clean_text(next_action, 1000, "الخطوة التالية"),
	}
	for fieldname, value in values.items():
		doc.set(fieldname, value)

	doc.guardian_summary_allowed = cint(guardian_summary_allowed)
	if not doc.guardian_summary_allowed:
		doc.guardian_summary = ""
	doc.next_action_due = next_action_due or None
	doc.actual_start = actual_start or appointment_doc.start_datetime
	doc.actual_end = actual_end or appointment_doc.end_datetime
	doc.attendance_status = appointment_doc.attendance_status
	doc.status = "Pending Review" if cint(submit_for_review) else "Draft"
	if doc.status == "Pending Review":
		if not doc.topic or not doc.professional_notes or not doc.beneficiary_summary:
			frappe.throw(
				"أكمل موضوع الجلسة والملاحظة المهنية وملخص المستفيد قبل الإرسال للمراجعة"
			)
		doc.submitted_on = now_datetime()

	doc.save(ignore_permissions=True)
	if not appointment_doc.created_session:
		frappe.db.set_value(
			"Consultation Appointment",
			appointment_doc.name,
			"created_session",
			doc.name,
			update_modified=False,
		)

	case_doc = frappe.get_doc("Consultation Case", appointment_doc.case)
	case_doc.next_action = doc.next_action or case_doc.next_action
	case_doc.next_action_due = doc.next_action_due or case_doc.next_action_due
	if case_doc.case_status in {"Assigned", "Awaiting Appointment"}:
		case_doc.case_status = "Active"
	case_doc.save(ignore_permissions=True)

	return {
		"name": doc.name,
		"status": doc.status,
		"message": (
			"تم إرسال توثيق الجلسة للمراجعة"
			if doc.status == "Pending Review"
			else "تم حفظ مسودة الجلسة"
		),
	}


def _require_consultant():
	if frappe.session.user == "Guest":
		frappe.throw("يلزم تسجيل الدخول", frappe.AuthenticationError)
	consultant = get_current_consultant()
	if not consultant:
		frappe.throw("لا يوجد ملف مستشار نشط مرتبط بالحساب", frappe.PermissionError)
	return consultant


def _get_owned_appointment(appointment: str, consultant: str):
	doc = frappe.get_doc("Consultation Appointment", appointment)
	if doc.consultant != consultant:
		frappe.throw("لا يمكنك الوصول إلى هذا الموعد", frappe.PermissionError)
	return doc


def _clean_text(value: str | None, limit: int, label: str) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > limit:
		frappe.throw(f"{label} أطول من الحد المسموح")
	return value
