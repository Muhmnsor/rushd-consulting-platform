frappe.ready(() => {
	const panel = document.querySelector("[data-assignment-panel]");
	if (!panel) return;

	const button = panel.querySelector("[data-assign-button]");
	const consultant = panel.querySelector("[data-consultant]");
	const priority = panel.querySelector("[data-priority]");
	const message = panel.querySelector("[data-form-message]");

	const showMessage = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};

	button.addEventListener("click", () => {
		if (!consultant.value) {
			showMessage("اختر المستشار الذي ستُسند إليه الحالة.", "error");
			consultant.focus();
			return;
		}
		if (!window.confirm("هل تريد إنشاء الحالة وإسنادها إلى المستشار المحدد؟")) {
			return;
		}

		button.disabled = true;
		frappe.call({
			method: "consultation_center.api.staff_portal.assign_consultation_request",
			type: "POST",
			args: {
				request_name: panel.dataset.requestName,
				consultant: consultant.value,
				priority: priority.value,
			},
			callback: (response) => {
				showMessage(response.message.message, "success");
				window.setTimeout(() => {
					window.location.href = "/supervisor/assignments";
				}, 700);
			},
			error: () => {
				showMessage("تعذر إسناد الحالة. تحقق من الطلب والمستشار ثم حاول مجددًا.", "error");
				button.disabled = false;
			},
		});
	});
});
