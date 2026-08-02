(function () {
	"use strict";

	const ADMIN_ENTRY_ROUTES = new Set([
		"/app",
		"/app/",
		"/desk",
		"/desk/",
		"/app/setup-wizard",
		"/desk/setup-wizard",
	]);

	function redirectCompletedAdminSetup() {
		if (!ADMIN_ENTRY_ROUTES.has(window.location.pathname)) return;
		if (!window.frappe?.boot?.setup_complete) return;

		const isAdministrator = frappe.session?.user === "Administrator";
		const hasAdminRole =
			frappe.user?.has_role?.("System Manager") ||
			frappe.user?.has_role?.("Center Director");
		if (!isAdministrator && !hasAdminRole) return;

		window.location.replace("/admin");
	}

	redirectCompletedAdminSetup();
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", redirectCompletedAdminSetup, {
			once: true,
		});
	}
	window.addEventListener("load", redirectCompletedAdminSetup, { once: true });
})();
