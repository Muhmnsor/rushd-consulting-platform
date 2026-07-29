frappe.ready(() => {
	const form = document.querySelector("[data-plan-form]");
	if (!form) return;
	const message = form.querySelector("[data-form-message]");
	const show = (text, type) => {
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	const editor = form.querySelector("[data-goals-editor]");
	const goalMarkup = () => {
		const row = document.createElement("div");
		row.className = "rushd-goal-row";
		row.innerHTML = `<input data-goal-field="goal_title" placeholder="عنوان الهدف"><input data-goal-field="indicator" placeholder="مؤشر التقدم"><input data-goal-field="baseline_value" placeholder="خط الأساس"><input data-goal-field="target_value" placeholder="القيمة المستهدفة"><input type="date" data-goal-field="target_date"><label><input type="checkbox" data-goal-field="beneficiary_visible" checked> يظهر للمستفيد</label><button type="button" data-remove-goal>حذف</button>`;
		return row;
	};
	if (editor && !editor.children.length) editor.append(goalMarkup());
	form.querySelector("[data-add-goal]")?.addEventListener("click", () => editor.append(goalMarkup()));
	form.addEventListener("click", (event) => {
		if (event.target.matches("[data-remove-goal]")) event.target.closest(".rushd-goal-row").remove();
	});
	form.querySelectorAll("[data-plan-submit]").forEach((button) => {
		button.addEventListener("click", () => {
			const goals = [...editor.querySelectorAll(".rushd-goal-row")].map((row) => {
				const value = (name) => row.querySelector(`[data-goal-field="${name}"]`)?.value || "";
				return {goal_title:value("goal_title"), indicator:value("indicator"), baseline_value:value("baseline_value"), target_value:value("target_value"), target_date:value("target_date"), beneficiary_visible:row.querySelector('[data-goal-field="beneficiary_visible"]').checked ? 1 : 0};
			}).filter((goal) => goal.goal_title.trim());
			const values = Object.fromEntries(new FormData(form).entries());
			frappe.call({method:"consultation_center.api.plan_portal.save_consultation_plan", type:"POST", args:{...values, case:form.dataset.case, plan_name:form.dataset.planName || null, goals:JSON.stringify(goals), submit_for_review:button.dataset.planSubmit}, callback:(r)=>{show(r.message.message,"success"); setTimeout(()=>location.href=`/consultant/plans?plan=${r.message.name}`,650);}, error:()=>show("تعذر حفظ الخطة. راجع الحقول.","error")});
		});
	});
	const taskBox = form.querySelector("[data-task-create]");
	taskBox?.querySelector("[data-create-task]")?.addEventListener("click", () => {
		frappe.call({method:"consultation_center.api.plan_portal.create_beneficiary_task", type:"POST", args:{plan_name:taskBox.dataset.planName, task_title:taskBox.querySelector("[data-task-title]").value, due_date:taskBox.querySelector("[data-task-due]").value, instructions:taskBox.querySelector("[data-task-instructions]").value}, callback:(r)=>{show(r.message.message,"success"); setTimeout(()=>location.reload(),500);}, error:()=>show("تعذر إضافة المهمة.","error")});
	});
});
