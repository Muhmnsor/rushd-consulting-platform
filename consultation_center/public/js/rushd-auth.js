(() => {
	const SIGNUP_METHOD = "frappe.core.doctype.user.user.sign_up";
	const DEFAULT_DESTINATION = "/beneficiary";

	const safeDestination = () => {
		const destination = new URLSearchParams(window.location.search).get("redirect-to");
		return destination?.startsWith("/") && !destination.startsWith("//")
			? destination
			: DEFAULT_DESTINATION;
	};

	const setSubmitting = (form, submitting) => {
		const button = form.querySelector(".btn-signup");
		if (!button) return;
		button.disabled = submitting;
		button.textContent = submitting ? "جارٍ إنشاء الحساب…" : "إنشاء الحساب";
	};

	const loginNewUser = (email, password, form) => {
		frappe.call({
			method: "login",
			args: { usr: email, pwd: password },
			callback: () => {
				window.location.assign(safeDestination());
			},
			error: () => setSubmitting(form, false),
		});
	};

	document.addEventListener(
		"submit",
		(event) => {
			const form = event.target.closest("form[data-rushd-signup]");
			if (!form) return;

			event.preventDefault();
			event.stopImmediatePropagation();

			const fullName = form.querySelector("#signup_fullname")?.value.trim();
			const email = form.querySelector("#signup_email")?.value.trim();
			const password = form.querySelector("#signup_password")?.value || "";
			const passwordConfirm =
				form.querySelector("#signup_password_confirm")?.value || "";

			if (!fullName || !email || !password) {
				frappe.msgprint("أكمل جميع بيانات إنشاء الحساب.");
				return;
			}
			if (password !== passwordConfirm) {
				frappe.msgprint("كلمتا المرور غير متطابقتين.");
				return;
			}

			setSubmitting(form, true);
			frappe.call({
				method: SIGNUP_METHOD,
				args: {
					email,
					full_name: fullName,
					password,
					redirect_to: safeDestination(),
				},
				callback: () => loginNewUser(email, password, form),
				error: () => setSubmitting(form, false),
			});
		},
		true,
	);
})();
