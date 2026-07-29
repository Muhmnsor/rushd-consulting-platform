frappe.ready(() => {
	const messageFor = (form) => form.querySelector("[data-form-message]");

	const showMessage = (form, text, type) => {
		const message = messageFor(form);
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};

	const openWizard = (name) => {
		document.querySelector(`[data-admin-wizard="${name}"]`)?.classList.add("is-open");
		document.body.classList.add("rushd-has-open-wizard");
	};

	document.querySelectorAll("[data-open-wizard]").forEach((button) => {
		button.addEventListener("click", () => openWizard(button.dataset.openWizard));
	});

	document.querySelectorAll("[data-admin-wizard].is-open").forEach(() => {
		document.body.classList.add("rushd-has-open-wizard");
	});

	document.querySelectorAll("[data-close-wizard]").forEach((button) => {
		button.addEventListener("click", () => {
			button.closest("[data-admin-wizard]")?.classList.remove("is-open");
			document.body.classList.remove("rushd-has-open-wizard");
		});
	});

	document.querySelectorAll("[data-admin-wizard]").forEach((wizard) => {
		const form = wizard.querySelector("[data-admin-form]");
		const steps = [...wizard.querySelectorAll("[data-wizard-step]")];
		const previous = wizard.querySelector("[data-wizard-prev]");
		const next = wizard.querySelector("[data-wizard-next]");
		const submit = wizard.querySelector("[data-wizard-submit]");
		let currentStep = 0;

		const renderStep = () => {
			steps.forEach((step, index) => step.classList.toggle("is-active", index === currentStep));
			wizard.querySelectorAll("[data-progress-step]").forEach((item, index) => {
				item.classList.toggle("is-active", index <= currentStep);
			});
			previous.disabled = currentStep === 0;
			next.hidden = currentStep === steps.length - 1;
			submit.hidden = currentStep !== steps.length - 1;
		};

		const stepIsValid = () => {
			const fields = [...steps[currentStep].querySelectorAll("input, select, textarea")];
			const invalid = fields.find((field) => !field.checkValidity());
			if (invalid) {
				invalid.reportValidity();
				invalid.focus();
				return false;
			}
			return true;
		};

		next?.addEventListener("click", () => {
			if (!stepIsValid()) return;
			currentStep = Math.min(currentStep + 1, steps.length - 1);
			renderStep();
		});
		previous?.addEventListener("click", () => {
			currentStep = Math.max(currentStep - 1, 0);
			renderStep();
		});
		renderStep();

		form?.addEventListener("submit", (event) => {
			event.preventDefault();
			if (!stepIsValid() || !form.reportValidity()) return;

			if (form.matches("[data-assessment-form]")) {
				const questions = [...form.querySelectorAll("[data-question-row]")].map((row) => {
					const result = {};
					row.querySelectorAll("[data-question-field]").forEach((field) => {
						result[field.dataset.questionField] = field.type === "checkbox"
							? (field.checked ? 1 : 0)
							: field.value;
					});
					return result;
				});
				form.querySelector("[data-questions-payload]").value = JSON.stringify(questions);
			}

			const args = {};
			new FormData(form).forEach((value, key) => {
				args[key] = value;
			});
			form.querySelectorAll("[data-json-multiselect]").forEach((select) => {
				args[select.name] = JSON.stringify([...select.selectedOptions].map((option) => option.value));
			});
			form.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
				args[checkbox.name] = checkbox.checked ? 1 : 0;
			});

			submit.disabled = true;
			showMessage(form, "جارٍ الحفظ والتحقق من البيانات…", "info");
			frappe.call({
				method: form.dataset.method,
				type: "POST",
				args,
				callback: (response) => {
					showMessage(form, response.message.message, "success");
					window.setTimeout(() => window.location.assign(window.location.pathname), 800);
				},
				error: (error) => {
					const serverMessage = error?._server_messages
						? JSON.parse(error._server_messages).map((item) => JSON.parse(item).message).join(" ")
						: "تعذر الحفظ. راجع الحقول ثم حاول مجددًا.";
					showMessage(form, serverMessage, "error");
					submit.disabled = false;
				},
			});
		});
	});

	document.querySelectorAll("[data-directory-search]").forEach((input) => {
		input.addEventListener("input", () => {
			const query = input.value.trim().toLocaleLowerCase("ar");
			document.querySelectorAll("[data-directory-row]").forEach((row) => {
				row.hidden = Boolean(query) && !row.dataset.search.toLocaleLowerCase("ar").includes(query);
			});
		});
	});

	const questionList = document.querySelector("[data-question-list]");
	const renumberQuestions = () => {
		questionList?.querySelectorAll("[data-question-row]").forEach((row, index) => {
			row.querySelector("[data-question-number]").textContent = index + 1;
			const code = row.querySelector('[data-question-field="question_code"]');
			if (!code.value || /^Q\d+$/.test(code.value)) code.value = `Q${index + 1}`;
			row.querySelector("[data-remove-question]").disabled =
				questionList.querySelectorAll("[data-question-row]").length === 1;
		});
	};
	document.querySelector("[data-add-question]")?.addEventListener("click", () => {
		const source = questionList.querySelector("[data-question-row]");
		const clone = source.cloneNode(true);
		clone.querySelectorAll("[data-question-field]").forEach((field) => {
			const name = field.dataset.questionField;
			if (field.type === "checkbox") {
				field.checked = ["required", "scored"].includes(name);
			} else if (field.tagName === "SELECT") {
				field.selectedIndex = 0;
			} else {
				field.value = {
					minimum_value: "1",
					maximum_value: "5",
					weight: "1",
					step_value: "1",
				}[name] || "";
			}
		});
		questionList.append(clone);
		renumberQuestions();
	});
	questionList?.addEventListener("change", (event) => {
		const field = event.target.closest("[data-question-field]");
		if (!field) return;
		const row = field.closest("[data-question-row]");
		if (field.dataset.questionField === "is_safety_item" && field.checked) {
			row.querySelector('[data-question-field="scored"]').checked = false;
			const action = row.querySelector('[data-question-field="critical_action"]');
			if (!action.value) action.value = "التواصل الفوري وفق بروتوكول الحماية المعتمد.";
		}
		const type = row.querySelector('[data-question-field="response_type"]').value;
		if (["Open Text", "Ranking"].includes(type)) {
			row.querySelector('[data-question-field="scored"]').checked = false;
		}
	});
	questionList?.addEventListener("click", (event) => {
		const button = event.target.closest("[data-remove-question]");
		if (!button || questionList.querySelectorAll("[data-question-row]").length === 1) return;
		button.closest("[data-question-row]").remove();
		renumberQuestions();
	});
	renumberQuestions();

	document.querySelectorAll("[data-case-tab]").forEach((button) => {
		button.addEventListener("click", () => {
			document.querySelectorAll("[data-case-tab]").forEach((item) => item.classList.remove("is-active"));
			document.querySelectorAll("[data-case-panel]").forEach((item) => item.classList.remove("is-active"));
			button.classList.add("is-active");
			document.querySelector(`[data-case-panel="${button.dataset.caseTab}"]`)?.classList.add("is-active");
		});
	});
});
