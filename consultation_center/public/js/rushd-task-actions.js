frappe.ready(() => {
	const message = document.querySelector("[data-form-message]");
	document.querySelectorAll("[data-task-card]").forEach((card) => card.querySelector("[data-update-task]").addEventListener("click", () => {
		frappe.call({method:"consultation_center.api.plan_portal.update_own_task", type:"POST", args:{task_name:card.dataset.taskName, status:card.querySelector("[data-task-status]").value, beneficiary_note:card.querySelector("[data-task-note]").value}, callback:(r)=>{message.textContent=r.message.message; message.className="rushd-form-message is-visible is-success"; setTimeout(()=>location.reload(),500);}, error:()=>{message.textContent="تعذر تحديث المهمة."; message.className="rushd-form-message is-visible is-error";}});
	}));
});
