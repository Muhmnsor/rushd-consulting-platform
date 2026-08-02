(() => {
	const SIGNUP_METHOD = "frappe.core.doctype.user.user.sign_up";
	const DEFAULT_DESTINATION = "/beneficiary";
	const LOGOUT_DESTINATION = "/login#login";
	const LOGOUT_SELECTOR =
		'[data-rushd-logout], a[href*="cmd=web_logout"], a[href*="cmd=logout"]';

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

	const finishLogout = () => {
		window.location.replace(LOGOUT_DESTINATION);
	};

	const logout = (link) => {
		if (link.dataset.rushdLogoutBusy === "1") return;
		link.dataset.rushdLogoutBusy = "1";
		link.setAttribute("aria-disabled", "true");
		link.setAttribute("aria-busy", "true");

		if (window.frappe?.call) {
			frappe.call({
				method: "logout",
				callback: finishLogout,
				error: () => {
					link.dataset.rushdLogoutBusy = "0";
					link.removeAttribute("aria-disabled");
					link.removeAttribute("aria-busy");
				},
			});
			return;
		}

		fetch("/api/method/logout", {
			method: "POST",
			credentials: "same-origin",
			headers: {
				"X-Frappe-CSRF-Token": window.frappe?.csrf_token || "",
				"X-Requested-With": "XMLHttpRequest",
			},
		})
			.then((response) => {
				if (!response.ok) throw new Error("logout_failed");
				finishLogout();
			})
			.catch(() => {
				link.dataset.rushdLogoutBusy = "0";
				link.removeAttribute("aria-disabled");
				link.removeAttribute("aria-busy");
			});
	};

	document.addEventListener(
		"click",
		(event) => {
			const link = event.target.closest(LOGOUT_SELECTOR);
			if (!link) return;

			event.preventDefault();
			event.stopImmediatePropagation();
			logout(link);
		},
		true,
	);

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
