import frappe
from frappe.utils import cint, now_datetime, strip_html_tags

from consultation_center.consultant_portal import get_current_consultant
from consultation_center.portal import get_beneficiary_for_user, require_portal_login
from consultation_center.staff import SUPERVISOR_ACCESS, require_staff_access


@frappe.whitelist(methods=["POST"])
def save_consultation_plan(
	case: str,
	plan_name: str | None = None,
	plan_title: str | None = None,
	plan_summary: str | None = None,
	start_date: str | None = None,
	review_date: str | None = None,
	expected_sessions: int | str = 0,
	goals: str | list | None = None,
	submit_for_review: int | str = 0,
):
	consultant = _require_consultant()
	case_doc = frappe.get_doc("Consultation Case", case)
	if case_doc.primary_consultant != consultant.name:
		frappe.throw("لا يمكنك إعداد خطة لهذه الحالة", frappe.PermissionError)

	if plan_name:
		doc = frappe.get_doc("Consultation Plan", plan_name)
		if doc.case != case_doc.name or doc.consultant != consultant.name:
			frappe.throw("لا يمكنك تعديل هذه الخطة", frappe.PermissionError)
		if doc.status not in {"Draft", "Returned"}:
			frappe.throw("الخطة في حالة لا تسمح بالتعديل")
	else:
		if frappe.db.exists(
			"Consultation Plan",
			{"case": case_doc.name, "status": ["in", ["Active", "Completed"]]},
		):
			frappe.throw("توجد خطة معتمدة للحالة؛ إنشاء نسخة جديدة سيضاف في المرحلة التالية")
		doc = frappe.new_doc("Consultation Plan")
		doc.case = case_doc.name
		doc.beneficiary = case_doc.beneficiary
		doc.consultant = consultant.name

	doc.plan_title = _clean(plan_title, 180, "عنوان الخطة")
	if not doc.plan_title:
		frappe.throw("اكتب عنوان الخطة")
	doc.plan_summary = _clean(plan_summary, 5000, "ملخص الخطة")
	doc.start_date = start_date or None
	doc.review_date = review_date or None
	doc.expected_sessions = max(0, min(cint(expected_sessions), 100))
	doc.set("goals", [])

	goal_rows = frappe.parse_json(goals) if isinstance(goals, str) else (goals or [])
	if len(goal_rows) > 12:
		frappe.throw("عدد أهداف الخطة أكبر من الحد المسموح")
	for goal in goal_rows:
		title = _clean(goal.get("goal_title"), 180, "عنوان الهدف")
		if not title:
			continue
		doc.append(
			"goals",
			{
				"goal_title": title,
				"goal_description": _clean(goal.get("goal_description"), 2000, "وصف الهدف"),
				"indicator": _clean(goal.get("indicator"), 180, "مؤشر التقدم"),
				"baseline_value": _clean(goal.get("baseline_value"), 120, "خط الأساس"),
				"target_value": _clean(goal.get("target_value"), 120, "القيمة المستهدفة"),
				"current_value": _clean(goal.get("current_value"), 120, "القيمة الحالية"),
				"target_date": goal.get("target_date") or None,
				"status": goal.get("status")
				if goal.get("status")
				in {"Not Started", "In Progress", "Achieved", "Paused", "Cancelled"}
				else "Not Started",
				"beneficiary_visible": cint(goal.get("beneficiary_visible", 1)),
			},
		)

	doc.status = "Pending Review" if cint(submit_for_review) else "Draft"
	if doc.status == "Pending Review":
		if not doc.goals:
			frappe.throw("أضف هدفًا واحدًا على الأقل قبل إرسال الخطة")
		doc.submitted_on = now_datetime()
	doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"status": doc.status,
		"message": (
			"تم إرسال الخطة للمشرف"
			if doc.status == "Pending Review"
			else "تم حفظ مسودة الخطة"
		),
	}


@frappe.whitelist(methods=["POST"])
def review_consultation_plan(
	plan_name: str,
	decision: str,
	review_note: str | None = None,
):
	require_staff_access(SUPERVISOR_ACCESS)
	if decision not in {"approve", "return"}:
		frappe.throw("قرار مراجعة الخطة غير صالح")
	doc = frappe.get_doc("Consultation Plan", plan_name)
	if doc.status != "Pending Review":
		frappe.throw("لا يمكن مراجعة الخطة من حالتها الحالية")
	review_note = _clean(review_note, 3000, "ملاحظة المراجعة")
	if decision == "return" and not review_note:
		frappe.throw("اكتب سبب إعادة الخطة للمستشار")
	doc.review_note = review_note
	doc.status = "Active" if decision == "approve" else "Returned"
	doc.save(ignore_permissions=True)

	if decision == "approve":
		case_doc = frappe.get_doc("Consultation Case", doc.case)
		case_doc.goal_summary = doc.plan_summary
		case_doc.planned_sessions = doc.expected_sessions
		case_doc.next_action = "بدء تنفيذ الخطة الاستشارية"
		case_doc.save(ignore_permissions=True)
	return {
		"name": doc.name,
		"status": doc.status,
		"message": "تم اعتماد الخطة" if decision == "approve" else "أعيدت الخطة للمستشار",
	}


@frappe.whitelist(methods=["POST"])
def create_beneficiary_task(
	plan_name: str,
	task_title: str,
	instructions: str | None = None,
	due_date: str | None = None,
):
	consultant = _require_consultant()
	plan = frappe.get_doc("Consultation Plan", plan_name)
	if plan.consultant != consultant.name or plan.status != "Active":
		frappe.throw("لا يمكنك إضافة مهمة إلى هذه الخطة", frappe.PermissionError)
	task = frappe.get_doc(
		{
			"doctype": "Beneficiary Task",
			"plan": plan.name,
			"case": plan.case,
			"beneficiary": plan.beneficiary,
			"consultant": plan.consultant,
			"task_title": _clean(task_title, 180, "عنوان المهمة"),
			"instructions": _clean(instructions, 4000, "تعليمات المهمة"),
			"due_date": due_date or None,
			"created_by": frappe.session.user,
		}
	)
	if not task.task_title:
		frappe.throw("اكتب عنوان المهمة")
	task.insert(ignore_permissions=True)
	return {"name": task.name, "message": "تمت إضافة المهمة للمستفيد"}


@frappe.whitelist(methods=["POST"])
def update_own_task(
	task_name: str,
	status: str,
	beneficiary_note: str | None = None,
):
	user = require_portal_login()
	beneficiary = get_beneficiary_for_user(user)
	if not beneficiary:
		frappe.throw("لا يوجد ملف مستفيد نشط", frappe.PermissionError)
	if status not in {"Pending", "In Progress", "Completed"}:
		frappe.throw("حالة المهمة غير صالحة")
	task = frappe.get_doc("Beneficiary Task", task_name)
	if task.beneficiary != beneficiary.name or task.status == "Cancelled":
		frappe.throw("لا يمكنك تحديث هذه المهمة", frappe.PermissionError)
	task.status = status
	task.beneficiary_note = _clean(beneficiary_note, 1000, "ملاحظة المهمة")
	task.completed_on = now_datetime() if status == "Completed" else None
	task.save(ignore_permissions=True)
	return {"name": task.name, "status": task.status, "message": "تم تحديث المهمة"}


def _require_consultant():
	consultant = get_current_consultant()
	if not consultant:
		frappe.throw("لا يوجد ملف مستشار نشط مرتبط بالحساب", frappe.PermissionError)
	return consultant


def _clean(value: str | None, limit: int, label: str) -> str:
	value = strip_html_tags(value or "").strip()
	if len(value) > limit:
		frappe.throw(f"{label} أطول من الحد المسموح")
	return value
