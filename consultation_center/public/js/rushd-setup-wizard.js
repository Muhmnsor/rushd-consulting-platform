(function () {
	"use strict";

	const translations = Object.freeze({
		Welcome: "مرحبًا بك في رُشد",
		"Your Language": "لغة المنصة",
		"Select Language": "اختر اللغة",
		"Your Country": "الدولة",
		"Select Country": "اختر الدولة",
		"Time Zone": "المنطقة الزمنية",
		"Select Time Zone": "اختر المنطقة الزمنية",
		Currency: "العملة",
		"Select Currency": "اختر العملة",
		"Allow sending usage data for improving applications":
			"السماح بإرسال بيانات استخدام مجهولة لتحسين المنصة",
		"Let's set up your account": "لنُكمل إعداد حسابك",
		"Full Name": "الاسم الكامل",
		"Email Address": "البريد الإلكتروني",
		"Will be your login ID": "سيُستخدم لتسجيل الدخول",
		Password: "كلمة المرور",
		"Update Password": "تحديث كلمة المرور",
		Previous: "السابق",
		Next: "التالي",
		"Complete Setup": "إكمال الإعداد",
		"Setting up your system": "جارٍ إعداد منصة رُشد",
		"Starting Frappe ...": "جارٍ تجهيز رُشد…",
		Retry: "إعادة المحاولة",
		"Setup Complete": "اكتمل إعداد رُشد",
		"Refreshing...": "جارٍ فتح مركز الإدارة…",
		"Failed to complete setup": "تعذر إكمال إعداد المنصة",
		"Could not start up:": "تعذر بدء الإعداد:",
		"Setup failed": "تعذر الإعداد",
		"Updating global settings": "جارٍ تحديث إعدادات المنصة",
		"Failed to update global settings": "تعذر تحديث إعدادات المنصة",
		"Wrapping up": "جارٍ إنهاء الإعداد",
		"starting the setup...": "جارٍ بدء الإعداد…",
	});

	function installTranslations() {
		frappe._messages = frappe._messages || {};
		Object.assign(frappe._messages, translations);
	}

	function field(slide, fieldname) {
		return slide?.fields?.find((item) => item.fieldname === fieldname);
	}

	function configureSlides() {
		const slides = frappe.setup?.slides_settings;
		if (!Array.isArray(slides)) return;

		const welcome = slides.find((slide) => slide.name === "welcome");
		if (welcome) {
			welcome.title = () =>
				`مرحبًا بك في رُشد${frappe.setup.data.first_name ? `، ${frappe.setup.data.first_name}` : ""}`;
			Object.assign(field(welcome, "language"), {
				label: translations["Your Language"],
				placeholder: translations["Select Language"],
				default: "Arabic",
			});
			Object.assign(field(welcome, "country"), {
				label: translations["Your Country"],
				placeholder: translations["Select Country"],
				default: "Saudi Arabia",
			});
			Object.assign(field(welcome, "timezone"), {
				label: translations["Time Zone"],
				placeholder: translations["Select Time Zone"],
				default: "Asia/Riyadh",
			});
			Object.assign(field(welcome, "currency"), {
				label: translations.Currency,
				placeholder: translations["Select Currency"],
				default: "SAR",
			});
			field(welcome, "enable_telemetry").label =
				translations["Allow sending usage data for improving applications"];
		}

		const user = slides.find((slide) => slide.name === "user");
		if (user) {
			user.title = translations["Let's set up your account"];
			field(user, "full_name").label = translations["Full Name"];
			field(user, "email").label = `${translations["Email Address"]} (${translations["Will be your login ID"]})`;
			field(user, "password").label = translations.Password;
		}
	}

	function redirectToRushdAdmin() {
		const prototype = frappe.setup?.SetupWizard?.prototype;
		if (!prototype || prototype.rushdPostSetupSuccess) return;

		prototype.rushdPostSetupSuccess = true;
		prototype.post_setup_success = function () {
			this.set_setup_complete_message(
				translations["Setup Complete"],
				translations["Refreshing..."],
			);
			window.setTimeout(() => {
				localStorage.current_route = "";
				localStorage.current_app = "";
				window.location.assign("/admin");
			}, 1200);
		};
	}

	installTranslations();
	configureSlides();
	redirectToRushdAdmin();
	document.documentElement.setAttribute("dir", "rtl");
	document.documentElement.setAttribute("lang", "ar");
})();
