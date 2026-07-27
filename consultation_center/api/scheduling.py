from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, getdate, now_datetime

from consultation_center.consultation_center.doctype.consultation_appointment.consultation_appointment import (
	CANCELLED_STATUSES,
	WEEKDAYS,
)
from consultation_center.permissions import can_manage_case_appointments


@frappe.whitelist()
def get_available_slots(consultant, service=None, date=None):
	if not date:
		frappe.throw(_("Date is required"))

	day = getdate(date)
	weekday = WEEKDAYS[day.weekday()]

	rules = frappe.db.get_all(
		"Consultant Availability Rule",
		filters={"consultant": consultant, "weekday": weekday, "active": 1},
		fields=["start_time", "end_time", "slot_duration", "service"],
	)
	rules = [r for r in rules if r.service in (None, "", service)]
	if not rules:
		return []

	consultant_doc = frappe.get_cached_doc("Consultant", consultant)
	buffer_before = consultant_doc.buffer_before or 0
	buffer_after = consultant_doc.buffer_after or 0
	duration = frappe.db.get_value("Consultation Service", service, "duration_minutes") or 60

	time_off = frappe.db.get_all(
		"Consultant Time Off",
		filters={
			"consultant": consultant,
			"from_datetime": ["<", f"{day} 23:59:59"],
			"to_datetime": [">", f"{day} 00:00:00"],
		},
		fields=["from_datetime", "to_datetime"],
	)

	busy = frappe.db.get_all(
		"Consultation Appointment",
		filters={
			"consultant": consultant,
			"status": ["not in", list(CANCELLED_STATUSES)],
			"start_datetime": ["<", f"{day} 23:59:59"],
			"end_datetime": [">", f"{day} 00:00:00"],
		},
		fields=["start_datetime", "end_datetime"],
	)

	slots = []
	for rule in rules:
		slot_duration = rule.slot_duration or duration
		cursor = get_datetime(f"{day} {rule.start_time}")
		window_end = get_datetime(f"{day} {rule.end_time}")

		while cursor + timedelta(minutes=duration) <= window_end:
			slot_start = cursor
			slot_end = add_to_date(cursor, minutes=duration)
			buffered_start = add_to_date(slot_start, minutes=-buffer_before)
			buffered_end = add_to_date(slot_end, minutes=buffer_after)

			blocked = any(
				buffered_start < get_datetime(t.to_datetime) and buffered_end > get_datetime(t.from_datetime)
				for t in time_off
			) or any(
				buffered_start < get_datetime(b.end_datetime) and buffered_end > get_datetime(b.start_datetime)
				for b in busy
			)

			if not blocked and slot_start > now_datetime():
				slots.append(
					{
						"start_datetime": slot_start.strftime("%Y-%m-%d %H:%M:%S"),
						"end_datetime": slot_end.strftime("%Y-%m-%d %H:%M:%S"),
					}
				)

			cursor = add_to_date(cursor, minutes=slot_duration)

	slots.sort(key=lambda s: s["start_datetime"])
	return slots


@frappe.whitelist()
def book_appointment(case, start_datetime):
	case_doc = frappe.get_doc("Consultation Case", case)
	_check_case_ownership(case_doc)

	if not case_doc.primary_consultant:
		frappe.throw(_("This case has no assigned consultant yet"))

	# Serialize bookings per consultant so concurrent requests cannot take the same slot.
	frappe.db.sql(
		"select name from `tabConsultant` where name = %s for update",
		(case_doc.primary_consultant,),
	)

	appointment = frappe.get_doc(
		{
			"doctype": "Consultation Appointment",
			"case": case_doc.name,
			"beneficiary": case_doc.beneficiary,
			"consultant": case_doc.primary_consultant,
			"service": case_doc.service,
			"start_datetime": start_datetime,
			"booking_source": "Portal",
		}
	)
	appointment.insert(ignore_permissions=True)
	return appointment.name


def _check_case_ownership(case_doc):
	if not can_manage_case_appointments(case_doc, frappe.session.user):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
