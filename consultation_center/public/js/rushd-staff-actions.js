frappe.ready(() => {
	const actionPanel = document.querySelector("[data-staff-action-panel]");
	if (!actionPanel) return;

	const buttons = actionPanel.querySelectorAll("[data-staff-action]");
	const message = actionPanel.querySelector("[data-form-message]");

	const showMessage = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};

	const setLoading = (loading) => {
		buttons.forEach((button) => {
			button.disabled = loading;
		});
	};

	buttons.forEach((button) => {
		button.addEventListener("click", () => {
			const action = button.dataset.staffAction;
			const publicNote =
				actionPanel.querySelector("[data-beneficiary-note]")?.value.trim() || "";
			const internalNote =
				actionPanel.querySelector("[data-internal-note]")?.value.trim() || "";

			if (
				["request_information", "not_eligible"].includes(action) &&
				!publicNote
			) {
				showMessage("اكتب أولًا توضيحًا عامًا مناسبًا للمستفيد.", "error");
				return;
			}
			if (
				action === "not_eligible" &&
				!window.confirm("هل أنت متأكد من حفظ قرار عدم ملاءمة الخدمة؟")
			) {
				return;
			}

			setLoading(true);
			const isTriage = actionPanel.dataset.actionType === "triage";
			frappe.call({
				method: isTriage
					? "consultation_center.api.staff_portal.triage_consultation_request"
					: "consultation_center.api.staff_portal.review_consultation_request",
				type: "POST",
				args: isTriage
					? {
							request_name: actionPanel.dataset.requestName,
							decision: action,
							triage_note: internalNote,
							beneficiary_note: publicNote,
						}
					: {
							request_name: actionPanel.dataset.requestName,
							action,
							operations_note: internalNote,
							beneficiary_note: publicNote,
						},
				callback: (response) => {
					showMessage(response.message.message, "success");
					window.setTimeout(() => window.location.reload(), 600);
				},
				error: () => {
					showMessage("تعذر تنفيذ الإجراء. تحقق من حالة الطلب وصلاحيتك.", "error");
					setLoading(false);
				},
			});
		});
	});
});

