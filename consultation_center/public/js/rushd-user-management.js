frappe.ready(() => {
	const showMessage = (form, text, type = "info") => {
		const message = form?.querySelector("[data-form-message]");
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	const serverMessage = (error) => {
		try {
			return JSON.parse(error?._server_messages || "[]")
				.map((item) => JSON.parse(item).message)
				.join(" ");
		} catch {
			return "تعذر تنفيذ الإجراء. راجع البيانات ثم حاول مجددًا.";
		}
	};
	const call = (method, args) => new Promise((resolve, reject) => {
		frappe.call({method, type: "POST", args, callback: (response) => resolve(response.message), error: reject});
	});
	const formArgs = (form) => {
		const args = {};
		new FormData(form).forEach((value, key) => {
			if (key !== "roles") args[key] = value;
		});
		form.querySelectorAll('input[type="checkbox"]:not([name="roles"])').forEach((field) => {
			args[field.name] = field.checked ? 1 : 0;
		});
		return args;
	};

	document.querySelectorAll("[data-open-wizard]").forEach((button) => {
		button.addEventListener("click", () => {
			document.querySelector(`[data-admin-wizard="${button.dataset.openWizard}"]`)?.classList.add("is-open");
			document.body.classList.add("rushd-has-open-wizard");
		});
	});
	document.querySelectorAll("[data-close-wizard]").forEach((button) => {
		button.addEventListener("click", () => {
			button.closest("[data-admin-wizard]")?.classList.remove("is-open");
			document.body.classList.remove("rushd-has-open-wizard");
		});
	});

	document.querySelector("[data-user-create]")?.addEventListener("submit", async (event) => {
		event.preventDefault();
		const form = event.currentTarget;
		const submit = form.querySelector('[type="submit"]');
		const args = formArgs(form);
		args.roles = JSON.stringify([...form.querySelectorAll('[name="roles"]:checked')].map((field) => field.value));
		submit.disabled = true;
		showMessage(form, "جارٍ إنشاء الحساب والتحقق من المسؤوليات…");
		try {
			const result = await call("consultation_center.api.user_admin.create_staff_user", args);
			showMessage(form, result.message, "success");
			setTimeout(() => location.reload(), 650);
		} catch (error) {
			showMessage(form, serverMessage(error), "error");
			submit.disabled = false;
		}
	});

	const passwordDialog = document.querySelector("[data-password-dialog]");
	const passwordForm = document.querySelector("[data-password-form]");
	document.querySelectorAll("[data-set-password]").forEach((button) => {
		button.addEventListener("click", () => {
			passwordForm.reset();
			passwordForm.elements.user.value = button.dataset.user;
			document.querySelector("[data-password-user-label]").textContent = button.dataset.label;
			passwordDialog.showModal();
		});
	});
	passwordForm?.addEventListener("submit", async (event) => {
		event.preventDefault();
		const form = event.currentTarget;
		const submit = form.querySelector('[type="submit"]');
		if (form.elements.new_password.value !== form.elements.confirm_password.value) {
			showMessage(form, "كلمتا المرور غير متطابقتين. أعد كتابتهما ثم حاول مجددًا.", "error");
			form.elements.confirm_password.focus();
			return;
		}
		const args = formArgs(form);
		delete args.confirm_password;
		submit.disabled = true;
		showMessage(form, "جارٍ تعيين كلمة المرور…");
		try {
			const result = await call("consultation_center.api.user_admin.set_user_password", args);
			showMessage(form, result.message, "success");
			form.elements.new_password.value = "";
			form.elements.confirm_password.value = "";
			submit.disabled = false;
		} catch (error) {
			showMessage(form, serverMessage(error), "error");
			submit.disabled = false;
		}
	});

	const rolesDialog = document.querySelector("[data-roles-dialog]");
	const rolesForm = document.querySelector("[data-roles-form]");
	document.querySelectorAll("[data-manage-roles]").forEach((button) => {
		button.addEventListener("click", () => {
			const assigned = new Set(JSON.parse(button.dataset.roles || "[]"));
			rolesForm.elements.user.value = button.dataset.user;
			rolesForm.querySelectorAll('[name="roles"]').forEach((field) => {
				field.checked = assigned.has(field.value);
			});
			rolesDialog.showModal();
		});
	});
	rolesForm?.addEventListener("submit", async (event) => {
		event.preventDefault();
		const form = event.currentTarget;
		const submit = form.querySelector('[type="submit"]');
		const roles = [...form.querySelectorAll('[name="roles"]:checked')].map((field) => field.value);
		submit.disabled = true;
		showMessage(form, "جارٍ تحديث المسؤوليات…");
		try {
			const result = await call("consultation_center.api.user_admin.update_user_roles", {
				user: form.elements.user.value,
				roles: JSON.stringify(roles),
			});
			showMessage(form, result.message, "success");
			setTimeout(() => location.reload(), 650);
		} catch (error) {
			showMessage(form, serverMessage(error), "error");
			submit.disabled = false;
		}
	});

	document.querySelectorAll("[data-user-status]").forEach((button) => {
		button.addEventListener("click", async () => {
			button.disabled = true;
			const original = button.textContent;
			button.textContent = "جارٍ الحفظ…";
			try {
				await call("consultation_center.api.user_admin.update_user_status", {
					user: button.dataset.user,
					enabled: button.dataset.enabled,
				});
				location.reload();
			} catch (error) {
				button.textContent = original;
				button.disabled = false;
				window.alert(serverMessage(error));
			}
		});
	});

	document.querySelector("[data-security-form]")?.addEventListener("submit", async (event) => {
		event.preventDefault();
		const form = event.currentTarget;
		const submit = form.querySelector('[type="submit"]');
		submit.disabled = true;
		showMessage(form, "جارٍ التحقق من السياسات وتطبيقها…");
		try {
			const result = await call("consultation_center.api.user_admin.update_security_settings", formArgs(form));
			showMessage(form, result.message, "success");
		} catch (error) {
			showMessage(form, serverMessage(error), "error");
		} finally {
			submit.disabled = false;
		}
	});
});
