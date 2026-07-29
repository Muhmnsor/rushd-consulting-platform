frappe.ready(() => {
	const form = document.querySelector("[data-beneficiary-assessment]");
	if (!form || form.dataset.editable !== "1") return;
	const message = document.querySelector("[data-form-message]");
	const show = (text, type) => {
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	const readAnswer = (row) => {
		const type = row.dataset.type;
		if (type === "Multi Select") {
			return [...row.querySelectorAll("[data-answer]:checked")].map((input) => input.value);
		}
		if (type === "Matrix") {
			return Object.fromEntries(
				[...row.querySelectorAll("[data-matrix-key]")]
					.filter((input) => input.value !== "")
					.map((input) => [input.dataset.matrixKey, input.value])
			);
		}
		if (["Single Select", "Scenario Based", "Parent/Proxy Item", "Observer Item"].includes(type)
			|| (type === "Yes/No" && row.querySelector('[data-answer][type="radio"]'))) {
			return row.querySelector("[data-answer]:checked")?.value || "";
		}
		const input = row.querySelector("[data-answer]");
		if (input?.matches("[data-ranking]")) {
			return input.value.split(/[,،\\n]+/).map((value) => value.trim()).filter(Boolean);
		}
		return input?.value || "";
	};
	const conditionMatches = (row) => {
		if (!row.dataset.conditionCode) return true;
		const dependency = form.querySelector(`[data-question][data-code="${CSS.escape(row.dataset.conditionCode)}"]`);
		if (!dependency) return false;
		const value = readAnswer(dependency);
		const values = Array.isArray(value) ? value.map(String) : [String(value)];
		if (row.dataset.conditionOperator === "Not Equals") return !values.includes(row.dataset.conditionValue);
		return values.includes(row.dataset.conditionValue);
	};
	const refreshConditions = () => {
		form.querySelectorAll("[data-question]").forEach((row) => {
			row.hidden = !conditionMatches(row);
		});
	};
	form.addEventListener("input", refreshConditions);
	form.addEventListener("change", refreshConditions);
	refreshConditions();
	form.querySelectorAll("[data-assessment-save]").forEach((button) => {
		button.addEventListener("click", () => {
			const responses = [...form.querySelectorAll("[data-question]")].filter((row) => !row.hidden).map((row) => ({
				question_code: row.dataset.code,
				answer_value: readAnswer(row),
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
