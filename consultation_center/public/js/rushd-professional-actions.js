frappe.ready(() => {
	const show = (root, text, type = "success") => {
		const message = root?.querySelector("[data-form-message]") || document.querySelector("[data-form-message]");
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	const call = (root, method, args, fallback) => {
		frappe.call({
			method,
			type: "POST",
			args,
			callback: (response) => {
				show(root, response.message.message);
				setTimeout(() => location.reload(), 550);
			},
			error: () => show(root, fallback, "error"),
		});
	};

	const referralForm = document.querySelector("[data-referral-form]");
	referralForm?.querySelectorAll("[data-referral-submit]").forEach((button) => {
		button.addEventListener("click", () => {
			const values = Object.fromEntries(new FormData(referralForm).entries());
			values.consent_confirmed = referralForm.querySelector('[name="consent_confirmed"]').checked ? 1 : 0;
			call(referralForm, "consultation_center.api.professional_portal.save_case_referral", {
				...values,
				case: referralForm.dataset.case,
				referral_name: referralForm.dataset.referral || null,
				submit_for_approval: button.dataset.referralSubmit,
			}, "تعذر حفظ الإحالة. تحقق من السبب والموافقة ونطاق البيانات.");
		});
	});

	const referralFollowup = document.querySelector("[data-referral-followup]");
	referralFollowup?.querySelectorAll("[data-referral-action]").forEach((button) => {
		button.addEventListener("click", () => call(
			referralFollowup,
			"consultation_center.api.professional_portal.update_case_referral",
			{
				referral_name: referralFollowup.dataset.referral,
				action: button.dataset.referralAction,
				follow_up_note: referralFollowup.querySelector("[data-follow-up]").value,
				outcome: referralFollowup.querySelector("[data-outcome]").value,
			},
			"تعذر تحديث الإحالة.",
		));
	});

	const supervisionCreate = document.querySelector("[data-supervision-create]");
	supervisionCreate?.addEventListener("submit", (event) => {
		event.preventDefault();
		call(
			supervisionCreate,
			"consultation_center.api.professional_portal.create_supervision_request",
			Object.fromEntries(new FormData(supervisionCreate).entries()),
			"تعذر إرسال طلب الإشراف.",
		);
	});
	document.querySelectorAll("[data-close-supervision]").forEach((button) => {
		button.addEventListener("click", () => call(
			button.closest("article"),
			"consultation_center.api.professional_portal.close_supervision_request",
			{request_name: button.dataset.closeSupervision},
			"تعذر إغلاق طلب الإشراف.",
		));
	});

	const escalationCreate = document.querySelector("[data-escalation-create]");
	escalationCreate?.addEventListener("submit", (event) => {
		event.preventDefault();
		const values = Object.fromEntries(new FormData(escalationCreate).entries());
		values.emergency_protocol_activated = escalationCreate.querySelector('[name="emergency_protocol_activated"]').checked ? 1 : 0;
		call(
			escalationCreate,
			"consultation_center.api.professional_portal.create_professional_escalation",
			values,
			"تعذر فتح التصعيد. تحقق من الملخص والإجراء الفوري.",
		);
	});

	const referralReview = document.querySelector("[data-referral-review]");
	referralReview?.querySelectorAll("[data-referral-review-action]").forEach((button) => {
		button.addEventListener("click", () => call(
			referralReview,
			"consultation_center.api.professional_portal.review_case_referral",
			{
				referral_name: referralReview.dataset.referral,
				decision: button.dataset.referralReviewAction,
				supervisor_note: referralReview.querySelector("[data-supervisor-note]").value,
			},
			"تعذر تسجيل قرار الإحالة.",
		));
	});

	const supervisionResponse = document.querySelector("[data-supervision-response]");
	supervisionResponse?.querySelectorAll("[data-supervision-action]").forEach((button) => {
		button.addEventListener("click", () => call(
			supervisionResponse,
			"consultation_center.api.professional_portal.respond_supervision_request",
			{
				request_name: supervisionResponse.dataset.request,
				action: button.dataset.supervisionAction,
				supervisor_response: supervisionResponse.querySelector("[data-response]").value,
				required_action: supervisionResponse.querySelector("[data-required-action]").value,
				follow_up_date: supervisionResponse.querySelector("[data-follow-up-date]").value,
			},
			"تعذر تحديث طلب الإشراف.",
		));
	});

	const escalationResponse = document.querySelector("[data-escalation-response]");
	escalationResponse?.querySelectorAll("[data-escalation-action]").forEach((button) => {
		button.addEventListener("click", () => call(
			escalationResponse,
			"consultation_center.api.professional_portal.update_professional_escalation",
			{
				escalation_name: escalationResponse.dataset.escalation,
				action: button.dataset.escalationAction,
				supervisor_action: escalationResponse.querySelector("[data-supervisor-action]").value,
				resolution_note: escalationResponse.querySelector("[data-resolution-note]").value,
				follow_up_date: escalationResponse.querySelector("[data-follow-up-date]").value,
			},
			"تعذر تحديث التصعيد.",
		));
	});
});
