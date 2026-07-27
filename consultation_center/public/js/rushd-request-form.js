frappe.ready(() => {
	const form = document.querySelector("[data-rushd-request-form]");
	if (!form) return;

	const summary = form.querySelector("#request-summary");
	const counter = form.querySelector("[data-summary-counter]");
	const message = form.querySelector("[data-form-message]");
	const buttons = form.querySelectorAll("[data-submit-action]");

	const updateCounter = () => {
		counter.textContent = `${summary.value.length} / 2000`;
	};

	const showMessage = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
		message.scrollIntoView({ behavior: "smooth", block: "center" });
	};

	const setLoading = (loading) => {
		buttons.forEach((button) => {
			button.disabled = loading;
			if (loading) {
				button.dataset.originalText = button.textContent;
				button.textContent = "جاري الحفظ...";
			} else if (button.dataset.originalText) {
				button.textContent = button.dataset.originalText;
			}
		});
	};

	summary.addEventListener("input", updateCounter);
	updateCounter();

	buttons.forEach((button) => {
		button.addEventListener("click", () => {
			const shouldSubmit = button.dataset.submitAction === "submit";
			const service = form.querySelector("#requested-service");
			const preferredMode = form.querySelector("input[name='preferred_mode']:checked");
			const emergencyCheck = form.querySelector("#emergency-acknowledged");

			if (!service.value) {
				showMessage("اختر مجال الاستشارة أولًا.", "error");
				service.focus();
				return;
			}
			if (!summary.value.trim()) {
				showMessage("اكتب وصفًا مختصرًا لما ترغب بالحصول على مساعدة فيه.", "error");
				summary.focus();
				return;
			}
			if (shouldSubmit && summary.value.trim().length < 20) {
				showMessage("أضف قليلًا من التفاصيل قبل إرسال الطلب.", "error");
				summary.focus();
				return;
			}
			if (shouldSubmit && !emergencyCheck.checked) {
				showMessage("أكد أولًا أن الطلب ليس حالة طارئة.", "error");
				emergencyCheck.focus();
				return;
			}

			setLoading(true);
			frappe.call({
				method: "consultation_center.api.beneficiary_portal.save_consultation_request",
				type: "POST",
				args: {
					requested_service: service.value,
					summary: summary.value,
					preferred_mode: preferredMode ? preferredMode.value : "Either",
					preferred_times: form.querySelector("#preferred-times").value,
					submit: shouldSubmit ? 1 : 0,
					emergency_acknowledged: emergencyCheck.checked ? 1 : 0,
				},
				callback: (response) => {
					const result = response.message;
					showMessage(result.message, "success");
					window.setTimeout(() => {
						window.location.href = `/beneficiary/requests?request=${encodeURIComponent(result.name)}`;
					}, 650);
				},
				error: (response) => {
					const serverMessage =
						response?._server_messages &&
						JSON.parse(response._server_messages || "[]")[0];
					showMessage(
						serverMessage ? JSON.parse(serverMessage).message : "تعذر حفظ الطلب. حاول مرة أخرى.",
						"error",
					);
					setLoading(false);
				},
			});
		});
	});
});

