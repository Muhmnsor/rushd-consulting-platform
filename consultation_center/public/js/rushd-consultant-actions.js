frappe.ready(() => {
	const pageMessage = document.querySelector("[data-form-message]");
	const showMessage = (text, type) => {
		if (!pageMessage) return;
		pageMessage.textContent = text;
		pageMessage.className = `rushd-form-message is-visible is-${type}`;
	};

	document.querySelectorAll("[data-attendance-action]").forEach((button) => {
		button.addEventListener("click", () => {
			const attendance = button.dataset.attendanceAction;
			if (
				attendance === "No Show" &&
				!window.confirm("هل أنت متأكد من تسجيل عدم حضور المستفيد؟")
			) {
				return;
			}
			document
				.querySelectorAll("[data-attendance-action]")
				.forEach((item) => (item.disabled = true));
			frappe.call({
				method:
					"consultation_center.api.consultant_portal.record_appointment_attendance",
				type: "POST",
				args: {
					appointment: button.dataset.appointment,
					attendance_status: attendance,
				},
				callback: (response) => {
					showMessage(response.message.message, "success");
					window.setTimeout(() => window.location.reload(), 600);
				},
				error: () => {
					showMessage("تعذر تسجيل الحضور. تحقق من الموعد وحاول مجددًا.", "error");
					document
						.querySelectorAll("[data-attendance-action]")
						.forEach((item) => (item.disabled = false));
				},
			});
		});
	});

	const form = document.querySelector("[data-session-form]");
	if (!form) return;

	const guardianToggle = form.querySelector("[data-guardian-summary-toggle]");
	const guardianField = form.querySelector("[data-guardian-summary-field]");
	guardianToggle?.addEventListener("change", () => {
		guardianField.hidden = !guardianToggle.checked;
		if (!guardianToggle.checked) {
			guardianField.querySelector("textarea").value = "";
		}
	});

	const buttons = form.querySelectorAll("[data-session-submit]");
	buttons.forEach((button) => {
		button.addEventListener("click", () => {
			const submitForReview = button.dataset.sessionSubmit === "1";
			const values = Object.fromEntries(new FormData(form).entries());
			if (
				submitForReview &&
				(!values.topic?.trim() ||
					!values.professional_notes?.trim() ||
					!values.beneficiary_summary?.trim())
			) {
				showMessage(
					"أكمل موضوع الجلسة والملاحظة المهنية وملخص المستفيد قبل الإرسال.",
					"error",
				);
				return;
			}

			buttons.forEach((item) => (item.disabled = true));
			frappe.call({
				method:
					"consultation_center.api.consultant_portal.save_session_documentation",
				type: "POST",
				args: {
					...values,
					appointment: form.dataset.appointment,
					session_name: form.dataset.sessionName || null,
					guardian_summary_allowed: guardianToggle?.checked ? 1 : 0,
					submit_for_review: submitForReview ? 1 : 0,
				},
				callback: (response) => {
					form.dataset.sessionName = response.message.name;
					showMessage(response.message.message, "success");
					window.setTimeout(() => {
						window.location.href = "/consultant/sessions";
					}, 700);
				},
				error: () => {
					showMessage("تعذر حفظ التوثيق. راجع الحقول ثم حاول مجددًا.", "error");
					buttons.forEach((item) => (item.disabled = false));
				},
			});
		});
	});
});
