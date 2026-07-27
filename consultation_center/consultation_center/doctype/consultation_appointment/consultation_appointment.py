import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime

CANCELLED_STATUSES = {"Cancelled by Beneficiary", "Cancelled by Center", "Expired"}
WEEKDAYS = [
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
]


class ConsultationAppointment(Document):
	def validate(self):
		self.set_end_datetime()
		self.check_time_off()
		self.check_availability()
		self.check_overlap()

	def set_end_datetime(self):
		if not self.start_datetime:
			frappe.throw(_("Start Datetime is required"))

		duration = frappe.db.get_value("Consultation Service", self.service, "duration_minutes") or 60
		self.end_datetime = add_to_date(get_datetime(self.start_datetime), minutes=duration)

	def check_time_off(self):
		overlapping = frappe.db.exists(
			"Consultant Time Off",
			{
				"consultant": self.consultant,
				"from_datetime": ["<", self.end_datetime],
				"to_datetime": [">", self.start_datetime],
			},
		)
		if overlapping:
			frappe.throw(_("Consultant is on time off during this slot"))

	def check_availability(self):
		start = get_datetime(self.start_datetime)
		weekday = WEEKDAYS[start.weekday()]
		start_time = start.time()
		end_time = get_datetime(self.end_datetime).time()

		rules = frappe.db.get_all(
			"Consultant Availability Rule",
			filters={
				"consultant": self.consultant,
				"weekday": weekday,
				"active": 1,
				"start_time": ["<=", start_time],
				"end_time": [">=", end_time],
			},
			fields=["name", "service"],
		)
		matching = [r for r in rules if r.service in (None, "", self.service)]

		if not matching:
			frappe.throw(_("Consultant is not available at this time"))

	def check_overlap(self):
		consultant = frappe.get_cached_doc("Consultant", self.consultant)
		buffer_before = consultant.buffer_before or 0
		buffer_after = consultant.buffer_after or 0

		window_start = add_to_date(get_datetime(self.start_datetime), minutes=-buffer_before)
		window_end = add_to_date(get_datetime(self.end_datetime), minutes=buffer_after)

		conflict = frappe.db.get_all(
			"Consultation Appointment",
			filters={
				"consultant": self.consultant,
				"name": ["!=", self.name or ""],
				"status": ["not in", list(CANCELLED_STATUSES)],
				"start_datetime": ["<", window_end],
				"end_datetime": [">", window_start],
			},
			limit=1,
		)
		if conflict:
			frappe.throw(_("This slot conflicts with another appointment for the same consultant"))
