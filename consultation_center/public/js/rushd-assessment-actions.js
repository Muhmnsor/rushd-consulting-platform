frappe.ready(() => {
	const message = document.querySelector("[data-form-message]");
	const show = (text, type = "success") => {
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};

	const assign = document.querySelector("[data-assessment-assign]");
	assign?.addEventListener("submit", (event) => {
		event.preventDefault();
		const values = Object.fromEntries(new FormData(assign).entries());
		frappe.call({
			method: "consultation_center.api.assessment_portal.assign_assessment",
			type: "POST",
			args: {...values, case: assign.dataset.case},
			callback: (response) => {
				show(response.message.message);
				setTimeout(() => location.reload(), 500);
			},
			error: () => show("تعذر إرسال المقياس. راجع الاختيار.", "error"),
		});
	});

	const review = document.querySelector("[data-assessment-review]");
	review?.addEventListener("submit", (event) => {
		event.preventDefault();
		const values = Object.fromEntries(new FormData(review).entries());
		values.publish_result = review.querySelector('[name="publish_result"]').checked ? 1 : 0;
		frappe.call({
			method: "consultation_center.api.assessment_portal.review_assessment",
			type: "POST",
			args: {...values, submission_name: review.dataset.submission},
			callback: (response) => {
				show(response.message.message);
				setTimeout(() => location.reload(), 500);
			},
			error: () => show("تعذر اعتماد المراجعة. تحقق من الملخص وسياسة العرض.", "error"),
		});
	});
});
