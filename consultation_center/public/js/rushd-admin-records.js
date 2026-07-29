frappe.ready(() => {
	const dialog = document.querySelector("[data-catalog-dialog]");
	const form = document.querySelector("[data-catalog-form]");
	if (!dialog || !form) return;
	const resource = dialog.dataset.resource;

	const message = (target, text, type = "info") => {
		const box = target.querySelector("[data-form-message]");
		if (!box) return;
		box.textContent = text;
		box.className = `rushd-form-message is-visible is-${type}`;
	};
	const errorText = (error) => {
		try {
			return JSON.parse(error?._server_messages || "[]")
				.map((item) => JSON.parse(item).message)
				.join(" ");
		} catch {
			return "تعذر تنفيذ الإجراء. راجع البيانات ثم حاول مجددًا.";
		}
	};
	const call = (method, args, type = "POST") => new Promise((resolve, reject) => {
		frappe.call({method, args, type, callback: (response) => resolve(response.message), error: reject});
	});
	const valuesFromForm = () => {
		const values = {};
		form.querySelectorAll("[name]").forEach((field) => {
			if (field.name === "record_name_key") return;
			values[field.name] = field.type === "checkbox" ? (field.checked ? 1 : 0) : field.value;
		});
		return values;
	};
	const clearMessage = () => {
		const box = form.querySelector("[data-form-message]");
		if (box) box.className = "rushd-form-message";
	};
	const openCreate = () => {
		form.reset();
		form.dataset.recordName = "";
		clearMessage();
		dialog.querySelector("[data-catalog-dialog-eyebrow]").textContent = "سجل جديد";
		dialog.showModal();
	};
	const openEdit = async (name) => {
		form.reset();
		clearMessage();
		form.dataset.recordName = name || "";
		dialog.querySelector("[data-catalog-dialog-eyebrow]").textContent = "تعديل السجل";
		dialog.showModal();
		message(form, "جارٍ تحميل البيانات…");
		try {
			const result = await call(
				"consultation_center.api.admin_records.get_admin_record",
				{resource, name: name || ""},
				"GET"
			);
			Object.entries(result.values || {}).forEach(([fieldname, value]) => {
				const field = form.elements[fieldname];
				if (!field) return;
				if (field.type === "checkbox") field.checked = Boolean(Number(value));
				else field.value = value ?? "";
			});
			clearMessage();
		} catch (error) {
			message(form, errorText(error), "error");
		}
	};

	document.querySelector("[data-catalog-create]")?.addEventListener("click", openCreate);
	document.querySelectorAll("[data-catalog-edit]").forEach((button) => {
		button.addEventListener("click", () => openEdit(button.dataset.record));
	});
	document.querySelector("[data-catalog-cancel]")?.addEventListener("click", () => dialog.close());

	form.addEventListener("submit", async (event) => {
		event.preventDefault();
		const submit = form.querySelector('[type="submit"]');
		submit.disabled = true;
		message(form, "جارٍ التحقق والحفظ…");
		try {
			const result = await call(
				"consultation_center.api.admin_records.save_admin_record",
				{
					resource,
					name: form.dataset.recordName || "",
					values: JSON.stringify(valuesFromForm()),
				}
			);
			message(form, result.message, "success");
			setTimeout(() => location.reload(), 650);
		} catch (error) {
			message(form, errorText(error), "error");
			submit.disabled = false;
		}
	});

	const deleteDialog = document.querySelector("[data-catalog-delete-dialog]");
	const deleteForm = document.querySelector("[data-catalog-delete-form]");
	document.querySelectorAll("[data-catalog-delete]").forEach((button) => {
		button.addEventListener("click", () => {
			deleteForm.elements.record_name.value = button.dataset.record;
			deleteDialog.querySelector("[data-delete-label]").textContent = button.dataset.label;
			const box = deleteForm.querySelector("[data-form-message]");
			if (box) box.className = "rushd-form-message";
			deleteDialog.showModal();
		});
	});
	deleteForm?.addEventListener("submit", async (event) => {
		event.preventDefault();
		const submit = deleteForm.querySelector('[type="submit"]');
		submit.disabled = true;
		message(deleteForm, "جارٍ التحقق من ارتباطات السجل…");
		try {
			const result = await call(
				"consultation_center.api.admin_records.delete_admin_record",
				{resource, name: deleteForm.elements.record_name.value}
			);
			message(deleteForm, result.message, "success");
			setTimeout(() => location.reload(), 650);
		} catch (error) {
			message(deleteForm, errorText(error), "error");
			submit.disabled = false;
		}
	});
});
