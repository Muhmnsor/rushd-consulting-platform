frappe.ready(() => {
	const submitForm = (selector, method) => {
		const form = document.querySelector(selector);
		if (!form) return;
		form.addEventListener("submit", (event) => {
			event.preventDefault();
			const button = form.querySelector("[type='submit']");
			const message = form.querySelector("[data-form-message]");
			button.disabled = true;
			frappe.call({
				method,
				type: "POST",
				args: Object.fromEntries(new FormData(form).entries()),
				callback: (response) => {
					message.textContent = response.message.message || "تم الحفظ";
					message.className = "rushd-form-message is-visible is-success";
					setTimeout(() => window.location.reload(), 500);
				},
				error: () => {
					message.textContent = "تعذر حفظ التغييرات. تحقق من الحقول وحاول مجددًا.";
					message.className = "rushd-form-message is-visible is-error";
					button.disabled = false;
				},
			});
		});
	};

	submitForm(
		"[data-professional-profile-form]",
		"consultation_center.api.consultant_settings.save_professional_profile",
	);
	submitForm(
		"[data-availability-form]",
		"consultation_center.api.consultant_settings.save_availability_rule",
	);
	submitForm(
		"[data-time-off-form]",
		"consultation_center.api.consultant_settings.add_time_off",
	);
	submitForm(
		"[data-capacity-form]",
		"consultation_center.api.consultant_settings.update_capacity",
	);
});
