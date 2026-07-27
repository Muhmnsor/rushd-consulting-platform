(function () {
	"use strict";

	const RUSHD_NAME = "Rushd";
	const ARABIC_LANGUAGE = "ar";

	function applyRushdIdentity() {
		const root = document.documentElement;
		root.setAttribute("dir", "rtl");
		root.setAttribute("lang", ARABIC_LANGUAGE);
		root.classList.add("rushd-rtl");

		if (document.body) {
			document.body.setAttribute("dir", "rtl");
			document.body.classList.add("rushd-rtl");
		}

		if (document.title) {
			document.title = document.title.replace(/Frappe(?: Framework)?/gi, RUSHD_NAME);
		}

		const applicationName = document.querySelector('meta[name="application-name"]');
		if (applicationName) {
			applicationName.setAttribute("content", RUSHD_NAME);
		}

		if (window.frappe) {
			frappe.app_name = RUSHD_NAME;

			if (frappe.boot) {
				frappe.boot.lang = ARABIC_LANGUAGE;
				frappe.boot.sysdefaults = frappe.boot.sysdefaults || {};
				frappe.boot.sysdefaults.language = ARABIC_LANGUAGE;
			}

			if (frappe.utils) {
				frappe.utils.is_rtl = function () {
					return true;
				};
			}
		}
	}

	applyRushdIdentity();

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", applyRushdIdentity, { once: true });
	}

	window.addEventListener("load", applyRushdIdentity, { once: true });
})();
