frappe.ready(() => {
	const form = document.querySelector("[data-rushd-profile-form]");
	if (!form) return;

	const button = form.querySelector("[data-profile-submit]");
	const message = form.querySelector("[data-form-message]");

	const showMessage = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};

	form.addEventListener("submit", (event) => {
		event.preventDefault();
		const originalText = button.textContent;
		button.disabled = true;
		button.textContent = "جاري الحفظ...";

		frappe.call({
			method: "consultation_center.api.beneficiary_portal.update_beneficiary_profile",
			type: "POST",
			args: {
				beneficiary_name: form.querySelector("#beneficiary-name").value,
				mobile: form.querySelector("#beneficiary-mobile").value,
				email: form.querySelector("#beneficiary-email").value,
				city: form.querySelector("#beneficiary-city").value,
				date_of_birth: form.querySelector("#beneficiary-birth-date").value,
				preferred_language: form.querySelector("#preferred-language").value,
			},
			callback: (response) => {
				showMessage(response.message.message, "success");
				button.disabled = false;
				button.textContent = originalText;
			},
			error: () => {
				showMessage("تعذر حفظ البيانات. تحقق من الحقول وحاول مرة أخرى.", "error");
				button.disabled = false;
				button.textContent = originalText;
			},
		});
	});
});

