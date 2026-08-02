frappe.ready(() => {
	const messageFor = (form) => form.querySelector("[data-form-message]");
	const scoringExplanations = {
		Percentage: {
			symbol: "٪",
			title: "نسبة من 0 إلى 100",
			description: "تحوّل كل إجابة إلى نسبة موحّدة بحسب حدها الأدنى والأعلى، ثم تحسب المتوسط المرجّح بأوزان البنود.",
			example: "مثال: (25 + 75 + 100) ÷ 3 = 66.67٪",
			guidance: "مناسب لمقارنة بنود لها نطاقات مختلفة أو لمتابعة التغير عبر الزمن.",
		},
		Total: {
			symbol: "∑",
			title: "مجموع الدرجات الخام",
			description: "تجمع الدرجات الأصلية للبنود المحتسبة كما هي. لا تدخل أوزان البنود في هذا الرقم الخام، وتبقى النسبة المعيارية محفوظة بشكل منفصل.",
			example: "مثال: 3 + 4 + 5 = 12 نقطة",
			guidance: "استخدمه عندما تكون جميع البنود على السلم نفسه ويعتمد دليل الأداة على مجموع محدد.",
		},
		Average: {
			symbol: "x̄",
			title: "متوسط الدرجات الخام",
			description: "تجمع الدرجات الأصلية ثم تقسمها على عدد البنود المحتسبة. لا تدخل الأوزان في المتوسط الخام.",
			example: "مثال: (3 + 4 + 5) ÷ 3 = 4 من 5",
			guidance: "مناسب عندما تريد نتيجة سهلة القراءة على نفس سلم الإجابة، مثل متوسط من 1 إلى 5.",
		},
		"No Automated Score": {
			symbol: "—",
			title: "لا يظهر رقم آلي",
			description: "تحفظ الإجابات للمراجعة المهنية دون مجموع أو نسبة. تبقى تنبيهات السلامة فعّالة ولا تُلغى.",
			example: "الناتج: إجابات وصفية للمراجعة، والدرجة الرقمية = 0",
			guidance: "مناسب للنماذج الإدارية والأسئلة المفتوحة أو الأدوات التي لا يجوز تفسيرها رقميًا.",
		},
	};
	const instrumentExplanations = {
		"Outcome Measure": {
			symbol: "↗",
			title: "لمتابعة التغيّر قبل الخدمة وبعدها",
			description: "يقيس حالة أو مهارة يمكن متابعتها في أكثر من نقطة زمنية لمعرفة مقدار التحسن أو التراجع.",
			output: "الناتج المعتاد: درجة قابلة للمقارنة بين القياسات",
			guidance: "الدرجة تساعد في المتابعة المهنية، لكنها لا تعني تشخيصًا طبيًا أو نفسيًا بمفردها.",
		},
		"Safety Screener": {
			symbol: "!",
			title: "لاكتشاف مؤشرات تحتاج استجابة آمنة",
			description: "يتضمن أسئلة قصيرة تكشف إجابات حرجة أو مؤشرات خطر تستدعي مراجعة بشرية وإجراءً مهنيًا واضحًا.",
			output: "الناتج: تنبيه سلامة ومسار متابعة، وليس تشخيصًا أو قرارًا آليًا",
			guidance: "اختره فقط عند وجود بروتوكول استجابة، ومسؤول واضح، وزمن محدد للتعامل مع التنبيه.",
		},
		"Satisfaction Survey": {
			symbol: "★",
			title: "لقياس تجربة المستفيد مع الخدمة",
			description: "يجمع رأي المستفيد في سهولة الوصول، وجودة التواصل، وملاءمة التجربة بعد تقديم الخدمة أو في محطة محددة.",
			output: "الناتج المعتاد: مؤشرات رضا وملاحظات تساعد في تحسين الخدمة",
			guidance: "لا تستخدم نتيجة الرضا لقياس التحسن النفسي أو للحكم على أداء المستشار دون سياق إضافي.",
		},
		"Administrative Form": {
			symbol: "≡",
			title: "لجمع بيانات تشغيلية دون قياس مهني",
			description: "ينظم معلومات مثل الموافقات، والتفضيلات، وبيانات التواصل، والتحقق، وإجراءات المتابعة الداخلية.",
			output: "الناتج: سجل منظم أو إجابات وصفية، وغالبًا دون درجة رقمية",
			guidance: "عند اختياره تكون «دون احتساب آلي» عادةً أنسب طريقة للنتيجة.",
		},
	};

	const showMessage = (form, text, type) => {
		const message = messageFor(form);
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	const scoringMethod = document.querySelector("[data-scoring-method]");
	const scoringExplainer = document.querySelector("[data-scoring-explainer]");
	const renderScoringExplanation = () => {
		if (!scoringMethod || !scoringExplainer) return;
		const content = scoringExplanations[scoringMethod.value] || scoringExplanations.Percentage;
		scoringExplainer.querySelector("[data-scoring-symbol]").textContent = content.symbol;
		scoringExplainer.querySelector("[data-scoring-title]").textContent = content.title;
		scoringExplainer.querySelector("[data-scoring-description]").textContent = content.description;
		scoringExplainer.querySelector("[data-scoring-example]").textContent = content.example;
		scoringExplainer.querySelector("[data-scoring-guidance]").textContent = content.guidance;
	};
	scoringMethod?.addEventListener("change", renderScoringExplanation);
	renderScoringExplanation();

	const instrumentKind = document.querySelector("[data-instrument-kind]");
	const instrumentExplainer = document.querySelector("[data-instrument-explainer]");
	const renderInstrumentExplanation = () => {
		if (!instrumentKind || !instrumentExplainer) return;
		const content = instrumentExplanations[instrumentKind.value] || instrumentExplanations["Outcome Measure"];
		instrumentExplainer.querySelector("[data-instrument-symbol]").textContent = content.symbol;
		instrumentExplainer.querySelector("[data-instrument-title]").textContent = content.title;
		instrumentExplainer.querySelector("[data-instrument-description]").textContent = content.description;
		instrumentExplainer.querySelector("[data-instrument-output]").textContent = content.output;
		instrumentExplainer.querySelector("[data-instrument-guidance]").textContent = content.guidance;
	};
	instrumentKind?.addEventListener("change", renderInstrumentExplanation);
	renderInstrumentExplanation();

	const syncServicePayloads = (scope = document) => {
		const groups = scope.matches?.("[data-service-options]")
			? [scope]
			: [...scope.querySelectorAll("[data-service-options]")];
		groups.forEach((group) => {
			const payload = group.querySelector("[data-services-payload]");
			if (!payload) return;
			payload.value = JSON.stringify(
				[...group.querySelectorAll("[data-service-option]:checked")].map((option) => option.value)
			);
		});
	};
	document.querySelectorAll("[data-service-options]").forEach((group) => {
		group.addEventListener("change", () => syncServicePayloads(group));
	});
	syncServicePayloads();

	const syncAvailabilityPayloads = (scope = document) => {
		let valid = true;
		const builders = scope.matches?.("[data-availability-builder]")
			? [scope]
			: [...scope.querySelectorAll("[data-availability-builder]")];
		builders.forEach((builder) => {
			const rules = [];
			builder.querySelectorAll("[data-availability-row]").forEach((row) => {
				const weekday = row.querySelector('[data-availability-field="weekday"]');
				const startTime = row.querySelector('[data-availability-field="start_time"]');
				const endTime = row.querySelector('[data-availability-field="end_time"]');
				const fields = [weekday, startTime, endTime];
				fields.forEach((field) => field.setCustomValidity(""));
				const hasAnyValue = fields.some((field) => field.value);
				if (!hasAnyValue) return;
				fields.forEach((field) => {
					if (!field.value) {
						field.setCustomValidity("أكمل اليوم ووقت البداية والنهاية لهذه الفترة");
						valid = false;
					}
				});
				if (startTime.value && endTime.value && startTime.value >= endTime.value) {
					endTime.setCustomValidity("وقت النهاية يجب أن يكون بعد وقت البداية");
					valid = false;
				}
				if (fields.every((field) => field.value) && startTime.value < endTime.value) {
					rules.push({
						weekday: weekday.value,
						start_time: startTime.value,
						end_time: endTime.value,
					});
				}
			});
			const payload = builder.querySelector("[data-availability-payload]");
			if (payload) payload.value = JSON.stringify(rules);
		});
		return valid;
	};
	document.querySelectorAll("[data-availability-builder]").forEach((builder) => {
		const list = builder.querySelector("[data-availability-list]");
		const firstRow = list?.querySelector("[data-availability-row]");
		builder.querySelector("[data-add-availability]")?.addEventListener("click", () => {
			if (!firstRow) return;
			const row = firstRow.cloneNode(true);
			row.querySelectorAll("[data-availability-field]").forEach((field) => {
				field.value = "";
				field.setCustomValidity("");
			});
			list.appendChild(row);
			row.querySelector('[data-availability-field="weekday"]')?.focus();
			syncAvailabilityPayloads(builder);
		});
		list?.addEventListener("click", (event) => {
			const remove = event.target.closest("[data-remove-availability]");
			if (!remove) return;
			const row = remove.closest("[data-availability-row]");
			if (list.querySelectorAll("[data-availability-row]").length === 1) {
				row.querySelectorAll("[data-availability-field]").forEach((field) => {
					field.value = "";
					field.setCustomValidity("");
				});
			} else {
				row.remove();
			}
			syncAvailabilityPayloads(builder);
		});
		list?.addEventListener("input", () => syncAvailabilityPayloads(builder));
		list?.addEventListener("change", () => syncAvailabilityPayloads(builder));
	});
	syncAvailabilityPayloads();

	const inspectProfileImage = (input) => new Promise((resolve) => {
		const uploader = input.closest("[data-profile-image-uploader]");
		const message = uploader?.querySelector("[data-profile-image-message]");
		const preview = uploader?.querySelector("[data-profile-image-preview]");
		const previewImage = preview?.querySelector("img");
		const placeholder = preview?.querySelector("span");
		const file = input.files?.[0];
		input.setCustomValidity("");
		message?.classList.remove("is-error", "is-success");
		if (!file) {
			if (previewImage) previewImage.hidden = true;
			if (placeholder) placeholder.hidden = false;
			if (message) message.textContent = "إذا لم تُضف صورة، تظهر الأحرف الأولى من اسم المستشار.";
			resolve(true);
			return;
		}
		if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
			input.setCustomValidity("اختر صورة بصيغة JPG أو PNG أو WebP");
			if (message) {
				message.textContent = input.validationMessage;
				message.classList.add("is-error");
			}
			resolve(false);
			return;
		}
		if (file.size > 2 * 1024 * 1024) {
			input.setCustomValidity("حجم الصورة يجب ألا يتجاوز 2 ميجابايت");
			if (message) {
				message.textContent = input.validationMessage;
				message.classList.add("is-error");
			}
			resolve(false);
			return;
		}
		const objectUrl = URL.createObjectURL(file);
		const image = new Image();
		image.onload = () => {
			const ratio = image.naturalWidth / image.naturalHeight;
			if (image.naturalWidth < 600 || image.naturalHeight < 600) {
				input.setCustomValidity("أبعاد الصورة يجب ألا تقل عن 600 × 600 بكسل");
			} else if (ratio < .85 || ratio > 1.15) {
				input.setCustomValidity("استخدم صورة مربعة تقريبًا حتى لا يُقص الوجه عند العرض");
			}
			if (previewImage) {
				previewImage.src = objectUrl;
				previewImage.hidden = false;
			}
			if (placeholder) placeholder.hidden = true;
			if (message) {
				message.textContent = input.validationMessage || `جاهزة للرفع · ${image.naturalWidth} × ${image.naturalHeight} بكسل`;
				message.classList.add(input.validationMessage ? "is-error" : "is-success");
			}
			resolve(!input.validationMessage);
		};
		image.onerror = () => {
			URL.revokeObjectURL(objectUrl);
			input.setCustomValidity("تعذر قراءة الصورة المختارة");
			if (message) {
				message.textContent = input.validationMessage;
				message.classList.add("is-error");
			}
			resolve(false);
		};
		image.src = objectUrl;
	});

	document.querySelectorAll("[data-profile-image-file]").forEach((input) => {
		input.addEventListener("change", async () => {
			const valid = await inspectProfileImage(input);
			if (!valid) input.reportValidity();
		});
	});

	const uploadProfileImage = async (form) => {
		const input = form.querySelector("[data-profile-image-file]");
		const file = input?.files?.[0];
		if (!file) return;
		if (!(await inspectProfileImage(input))) throw new Error(input.validationMessage);
		const upload = new FormData();
		upload.append("file", file, file.name);
		upload.append("is_private", "0");
		upload.append("folder", "Home/Attachments");
		const response = await fetch("/api/method/upload_file", {
			method: "POST",
			headers: {"X-Frappe-CSRF-Token": frappe.csrf_token},
			body: upload,
		});
		const payload = await response.json();
		const fileUrl = payload?.message?.file_url;
		if (!response.ok || !fileUrl) {
			throw new Error(payload?.message || "تعذر رفع الصورة المهنية");
		}
		form.querySelector("[data-profile-image-url]").value = fileUrl;
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

		form?.addEventListener("submit", async (event) => {
			event.preventDefault();
			syncServicePayloads(form);
			syncAvailabilityPayloads(form);
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

			submit.disabled = true;
			showMessage(form, "جارٍ الحفظ والتحقق من البيانات…", "info");
			try {
				await uploadProfileImage(form);
			} catch (error) {
				showMessage(form, error.message || "تعذر رفع الصورة المهنية.", "error");
				submit.disabled = false;
				return;
			}

			const args = {};
			new FormData(form).forEach((value, key) => {
				if (!(value instanceof File)) args[key] = value;
			});
			form.querySelectorAll("[data-json-multiselect]").forEach((select) => {
				args[select.name] = JSON.stringify([...select.selectedOptions].map((option) => option.value));
			});
			form.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
				if (checkbox.name) args[checkbox.name] = checkbox.checked ? 1 : 0;
			});

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
