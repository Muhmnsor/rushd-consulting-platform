frappe.ready(() => {
	const panel = document.querySelector("[data-plan-review-panel]");
	if (!panel) return;
	const note = panel.querySelector("[data-review-note]");
	const message = panel.querySelector("[data-form-message]");
	panel.querySelectorAll("[data-plan-review]").forEach((button) => button.addEventListener("click", () => {
		const decision = button.dataset.planReview;
		if (decision === "return" && !note.value.trim()) {
			message.textContent = "اكتب سبب إعادة الخطة.";
			message.className = "rushd-form-message is-visible is-error";
			return;
		}
		frappe.call({method:"consultation_center.api.plan_portal.review_consultation_plan", type:"POST", args:{plan_name:panel.dataset.planName, decision, review_note:note.value.trim()}, callback:(r)=>{message.textContent=r.message.message; message.className="rushd-form-message is-visible is-success"; setTimeout(()=>location.href="/supervisor/plan-reviews",600);}, error:()=>{message.textContent="تعذر حفظ القرار."; message.className="rushd-form-message is-visible is-error";}});
	}));
});
