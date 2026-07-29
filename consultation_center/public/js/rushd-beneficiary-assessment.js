frappe.ready(() => {
	const form = document.querySelector("[data-beneficiary-assessment]");
	if (!form || form.dataset.editable !== "1") return;
	const message = document.querySelector("[data-form-message]");
	const show = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	form.querySelectorAll("[data-assessment-save]").forEach((button) => {
		button.addEventListener("click", () => {
			const responses = [...form.querySelectorAll("[data-question]")].map((row) => ({
				question_code: row.dataset.code,
				answer_value: row.querySelector("[data-answer]").value,
			}));
			frappe.call({
				method: "consultation_center.api.assessment_portal.save_assessment_responses",
				type: "POST",
				args: {
					submission_name: form.dataset.submission,
					responses: JSON.stringify(responses),
					submit: button.dataset.assessmentSave,
				},
				callback: (response) => {
					show(response.message.message, "success");
					setTimeout(() => location.reload(), 550);
				},
				error: () => show("تعذر حفظ الإجابات. تحقق من الأسئلة المطلوبة والقيم.", "error"),
			});
		});
	});
});
