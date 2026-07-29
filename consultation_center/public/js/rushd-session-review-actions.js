frappe.ready(() => {
	const panel = document.querySelector("[data-session-review-panel]");
	if (!panel) return;

	const buttons = panel.querySelectorAll("[data-session-review]");
	const note = panel.querySelector("[data-review-note]");
	const message = panel.querySelector("[data-form-message]");

	const showMessage = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};

	buttons.forEach((button) => {
		button.addEventListener("click", () => {
			const decision = button.dataset.sessionReview;
			if (decision === "return" && !note.value.trim()) {
				showMessage("اكتب سبب إعادة الجلسة للمستشار.", "error");
				note.focus();
				return;
			}
			const confirmation =
				decision === "approve"
					? "هل تريد اعتماد الجلسة وتحديث تقدم الحالة؟"
					: "هل تريد إعادة الجلسة للمستشار لاستكمالها؟";
			if (!window.confirm(confirmation)) return;

			buttons.forEach((item) => (item.disabled = true));
			frappe.call({
				method:
					"consultation_center.api.staff_portal.review_consultation_session",
				type: "POST",
				args: {
					session_name: panel.dataset.sessionName,
					decision,
					review_note: note.value.trim(),
				},
				callback: (response) => {
					showMessage(response.message.message, "success");
					window.setTimeout(() => {
						window.location.href = "/supervisor/session-reviews";
					}, 700);
				},
				error: () => {
					showMessage("تعذر حفظ قرار المراجعة. تحقق من حالة الجلسة.", "error");
					buttons.forEach((item) => (item.disabled = false));
				},
			});
		});
	});
});
