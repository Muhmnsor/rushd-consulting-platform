frappe.ready(() => {
	document.querySelectorAll("[data-consent-card]").forEach((card) => {
		const button = card.querySelector("[data-grant-consent]");
		if (!button) return;
		const checkbox = card.querySelector("[data-consent-confirmed]");
		const message = card.querySelector("[data-form-message]");

		button.addEventListener("click", () => {
			if (!checkbox.checked) {
				message.textContent = "أكد قراءة النص وفهمه قبل تسجيل الموافقة.";
				message.className = "rushd-form-message is-visible is-error";
				return;
			}
			button.disabled = true;
			frappe.call({
				method: "consultation_center.api.guardian_portal.grant_guardian_consent",
				type: "POST",
				args: {
					consent_record: card.dataset.consentCard,
					confirmed: 1,
				},
				callback: (response) => {
					message.textContent = response.message.message;
					message.className = "rushd-form-message is-visible is-success";
					window.setTimeout(() => window.location.reload(), 600);
				},
				error: () => {
					message.textContent = "تعذر تسجيل الموافقة. حاول مرة أخرى.";
					message.className = "rushd-form-message is-visible is-error";
					button.disabled = false;
				},
			});
		});
	});
});

