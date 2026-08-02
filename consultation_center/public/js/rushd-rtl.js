(function () {
	"use strict";

	const RUSHD_NAME = "رُشد";
	const ARABIC_LANGUAGE = "ar";
	const TEXT_TRANSLATIONS = Object.freeze({
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
		"Add More": "إضافة المزيد",
		"Search or type a command ({0})": "ابحث أو اكتب أمرًا ({0})",
		"Begin typing for results.": "ابدأ الكتابة لعرض النتائج.",
		"Clear all filters": "إزالة جميع المرشحات",
		"Generic Empty State": "لا توجد بيانات",
		"Grid Empty State": "لا توجد بيانات في الجدول",
		"Toggle Section: {0}": "تبديل القسم: {0}",
		"Add Row": "إضافة صف",
		"Clear Cache": "مسح ذاكرة التخزين المؤقت",
		"Filter By": "تصفية حسب",
		"Save Filter": "حفظ المرشح",
		"Hide Saved": "إخفاء المحفوظ",
		"كلف إلى": "إسناد إلى",
		"هوية شخصية": "المعرّف",
		"آخر تحديث يوم": "آخر تحديث",
		"إتبع": "متابعة",
		"عرض منسدل": "عرض القائمة",
		"بطاقات": "الوسوم",
		"Reports & Masters": "التقارير والبيانات الأساسية",
		"Let's Set Up Your Website.": "لنُعِدّ موقعك الإلكتروني",
		"Blogs, Website View Tracking, and more.":
			"المدونات، وتتبع زيارات الموقع، والمزيد.",
		"Introduction to Website": "مقدمة عن إدارة الموقع",
		"Create Blogger": "إضافة كاتب للمدونة",
		"Add Blog Category": "إضافة تصنيف للمدونة",
		"Enable Website Tracking": "تفعيل تتبع زيارات الموقع",
		"Learn about Web Pages": "التعرّف على صفحات الويب",
		"Create Entry": "إنشاء سجل",
		"Loading user profile": "جارٍ تحميل الملف الشخصي",
		"User does not exist": "المستخدم غير موجود",
		"Edit Profile": "تعديل الملف الشخصي",
		"User Settings": "إعدادات المستخدم",
		Leaderboard: "لوحة المتصدرين",
		Details: "تفاصيل الحساب",
		"تفاصيل الطلب": "تفاصيل الحساب",
		Intro: "نبذة",
		Interests: "الاهتمامات",
		Overview: "نظرة عامة",
		"Type Distribution": "توزيع أنواع النشاط",
		"No Data to Show": "لا توجد بيانات لعرضها",
		"Recent Activity": "النشاط الأخير",
		"No activities to show": "لا توجد أنشطة لعرضها",
		"Show More Activity": "عرض المزيد من النشاط",
		Rank: "الترتيب العام",
		"Monthly Rank": "الترتيب الشهري",
		Daily: "يوميًا",
		"Last Month": "الشهر الماضي",
		All: "الكل",
		name: "المعرّف",
		case: "الحالة الاستشارية",
		appointment: "الموعد",
		beneficiary: "المستفيد",
		consultant: "المستشار",
		service: "الخدمة",
		status: "الحالة",
		JAN: "ينا",
		FEB: "فبر",
		MAR: "مار",
		APR: "أبر",
		MAY: "ماي",
		JUN: "يون",
		JUL: "يول",
		AUG: "أغس",
		SEP: "سبت",
		OCT: "أكت",
		NOV: "نوف",
		DEC: "ديس",
		Sun: "أحد",
		Mon: "اثن",
		Tue: "ثلا",
		Wed: "أرب",
		Thu: "خمي",
		Fri: "جمع",
		Sat: "سبت",
		"Import Data": "استيراد البيانات",
		"Deleted Documents": "المستندات المحذوفة",
		"Alerts and Notifications": "التنبيهات والإشعارات",
		"Print Format Builder (New)": "منشئ تنسيقات الطباعة الجديد",
		Models: "نماذج البيانات",
		"Navbar Settings": "إعدادات شريط التنقل",
		"Module Onboarding": "تهيئة الوحدة",
		"To use Google Indexing, enable": "لاستخدام فهرسة جوجل، فعّل",
		"Google Settings": "إعدادات جوجل",
		Standard: "قياسي",
		undefined: "",
	});
	const INLINE_TRANSLATIONS = Object.freeze({
		"Under Completeness Review": "تحت مراجعة الاكتمال",
		"Awaiting Beneficiary Information": "بانتظار معلومات المستفيد",
		"Ready for Triage": "جاهز للفرز",
		"Awaiting Consent": "بانتظار الموافقة",
		"Ready for Assignment": "جاهز للإسناد",
		"Converted to Case": "تحول إلى حالة",
		"Not Eligible": "غير مؤهل",
		"في الامس": "أمس",
	});
	const FIELD_VALUE_TRANSLATIONS = Object.freeze({
		website_theme: Object.freeze({
			Standard: "قياسي",
		}),
	});

	const TRANSLATABLE_ATTRIBUTES = ["aria-label", "alt", "placeholder", "title"];

	function translateInterfaceText(value) {
		if (!value) return value;

		const leadingWhitespace = value.match(/^\s*/)?.[0] || "";
		const trailingWhitespace = value.match(/\s*$/)?.[0] || "";
		const source = value.trim();
		let translated = Object.prototype.hasOwnProperty.call(
			TEXT_TRANSLATIONS,
			source,
		)
			? TEXT_TRANSLATIONS[source]
			: null;

		if (translated === null) {
			const displayTranslations =
				window.frappe?.boot?.rushd_display_translations || {};
			if (Object.prototype.hasOwnProperty.call(displayTranslations, source)) {
				translated = displayTranslations[source];
			} else {
				const separatorIndex = source.lastIndexOf(": ");
				const displayValue =
					separatorIndex === -1 ? "" : source.slice(separatorIndex + 2);
				if (
					displayValue &&
					Object.prototype.hasOwnProperty.call(
						displayTranslations,
						displayValue,
					)
				) {
					translated = `${source.slice(0, separatorIndex + 2)}${
						displayTranslations[displayValue]
					}`;
				}
			}
		}

		if (translated === null) {
			const resultCount = source.match(/^(\d+)\s+results? found$/i);
			if (resultCount) {
				const count = Number(resultCount[1]);
				translated = count === 1 ? "نتيجة واحدة" : `${count} نتائج`;
			}
		}

		if (translated === null) {
			const searchLabel = source.match(/^Search or type a command \((.+)\)$/);
			if (searchLabel) {
				translated = `ابحث أو اكتب أمرًا (${searchLabel[1]})`;
			}
		}

		if (translated === null) {
			const sectionLabel = source.match(/^Toggle Section:\s*(.+)$/);
			if (sectionLabel) {
				translated = `تبديل القسم: ${sectionLabel[1]}`;
			}
		}

		if (translated === null) {
			const publishedCount = source.match(/^(\d+)\s+Published$/);
			if (publishedCount) {
				translated = `${publishedCount[1]} منشور`;
			}
		}

		if (translated === null) {
			const activeCount = source.match(/^(\d+)\s+Active$/);
			if (activeCount) {
				translated = `${activeCount[1]} نشط`;
			}
		}

		if (translated === null) {
			let translatedInlineText = source;
			for (const [englishText, arabicText] of Object.entries(INLINE_TRANSLATIONS)) {
				translatedInlineText = translatedInlineText.replaceAll(
					englishText,
					arabicText,
				);
			}
			if (translatedInlineText !== source) {
				translated = translatedInlineText;
			}
		}

		return translated !== null
			? `${leadingWhitespace}${translated}${trailingWhitespace}`
			: value;
	}

	function localizeControlValue(node) {
		if (!(node instanceof HTMLInputElement)) return;

		const fieldName = node.closest("[data-fieldname]")?.dataset.fieldname;
		const translations = FIELD_VALUE_TRANSLATIONS[fieldName];
		if (!translations) return;

		const originalValue = node.dataset.rushdOriginalValue;
		if (originalValue && node.value === translations[originalValue]) return;

		const translatedValue = translations[node.value];
		if (translatedValue && document.activeElement !== node) {
			node.dataset.rushdOriginalValue = node.value;
			node.value = translatedValue;
		} else if (originalValue && node.value !== originalValue) {
			delete node.dataset.rushdOriginalValue;
		}
	}

	function localizeElement(element) {
		if (!(element instanceof Element)) return;

		for (const node of [element, ...element.querySelectorAll("*")]) {
			if (node.matches("script, style, textarea, code, pre, [contenteditable='true']")) {
				continue;
			}

			for (const attribute of TRANSLATABLE_ATTRIBUTES) {
				const currentValue = node.getAttribute(attribute);
				const translatedValue = translateInterfaceText(currentValue);
				if (translatedValue !== currentValue) {
					node.setAttribute(attribute, translatedValue);
				}
			}

			localizeControlValue(node);
		}

		const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
		let textNode = walker.nextNode();
		while (textNode) {
			const parent = textNode.parentElement;
			if (
				parent &&
				!parent.closest("script, style, textarea, code, pre, [contenteditable='true']")
			) {
				const translatedValue = translateInterfaceText(textNode.nodeValue);
				if (translatedValue !== textNode.nodeValue) {
					textNode.nodeValue = translatedValue;
				}
			}
			textNode = walker.nextNode();
		}
	}

	function installRushdTranslations() {
		if (!window.frappe) return;
		frappe._messages = frappe._messages || {};
		Object.assign(
			frappe._messages,
			frappe.boot?.rushd_display_translations || {},
		);
		Object.assign(frappe._messages, TEXT_TRANSLATIONS);
	}

	function localizeWorkspaceSidebarSections(root = document) {
		const sectionLabels = {
			Personal: "مساحاتي الخاصة",
			Public: "مساحات العمل المشتركة",
		};

		root
			.querySelectorAll?.(".standard-sidebar-section[data-title]")
			.forEach((section) => {
				const label = sectionLabels[section.dataset.title];
				if (!label) return;

				const title = section.querySelector(".section-title");
				if (title && title.textContent.trim() !== label) {
					title.textContent = label;
				}

				const toggle = section.querySelector(".standard-sidebar-label");
				if (toggle) {
					toggle.setAttribute("aria-label", `تبديل القسم: ${label}`);
					toggle.setAttribute("title", label);
				}
			});
	}

	function redirectAdminLegacyProfile() {
		if (window.location.pathname !== "/app/user-profile") return false;

		const isAdministrator = window.frappe?.session?.user === "Administrator";
		const hasAdminRole =
			window.frappe?.user?.has_role?.("System Manager") ||
			window.frappe?.user?.has_role?.("Center Director");
		if (!isAdministrator && !hasAdminRole) return false;

		window.location.replace("/admin");
		return true;
	}

	function navigateDeskBack() {
		const previousRoute = window.frappe?.get_prev_route?.() || [];
		const currentRoute = window.frappe?.get_route?.() || [];
		if (
			previousRoute.length &&
			JSON.stringify(previousRoute) !== JSON.stringify(currentRoute)
		) {
			frappe.set_route(...previousRoute);
			return;
		}

		if (window.history.length > 1) {
			window.history.back();
			return;
		}

		window.location.assign("/app/rushd");
	}

	function installDeskBackButton() {
		if (!window.location.pathname.startsWith("/app")) return;

		const navbarHome = document.querySelector(".navbar .navbar-home");
		if (!navbarHome) return;

		let backButton = document.querySelector(".rushd-navbar-back");
		if (!backButton) {
			backButton = document.createElement("button");
			backButton.type = "button";
			backButton.className = "btn-reset rushd-navbar-back";
			backButton.setAttribute("aria-label", "رجوع");
			backButton.setAttribute("title", "رجوع");
			backButton.innerHTML = `
				<span class="rushd-navbar-back-icon" aria-hidden="true">→</span>
				<span class="rushd-navbar-back-label">رجوع</span>
			`;
			backButton.addEventListener("click", navigateDeskBack);
			navbarHome.insertAdjacentElement("afterend", backButton);
		}

		backButton.hidden = /^\/app\/?$/.test(window.location.pathname);
	}

	function installWebsiteSettingsEntry() {
		if (window.location.pathname !== "/app/website") return;
		if (document.querySelector(".rushd-website-settings-entry")) return;

		const workspaceContent = document.querySelector(
			".layout-main-section .workspace-container, .layout-main-section",
		);
		if (!workspaceContent) return;

		const entry = document.createElement("section");
		entry.className = "rushd-website-settings-entry";
		entry.setAttribute("aria-label", "إدارة الصفحة الرئيسية لرُشد");
		entry.innerHTML = `
			<div>
				<span>صفحة رُشد العامة</span>
				<h2>إدارة الصفحة الرئيسية</h2>
				<p>عدّل العناوين والأقسام والخطوات والأسئلة الشائعة من مكان واحد.</p>
			</div>
			<div class="rushd-website-settings-entry__actions">
				<a class="btn btn-default" href="/" target="_blank" rel="noopener">معاينة الموقع</a>
				<a class="btn btn-primary" href="/app/rushd-website-settings/Rushd%20Website%20Settings">تحرير المحتوى</a>
			</div>
		`;
		workspaceContent.prepend(entry);
	}

	const RUSHD_WORKSPACE_ACTIONS = Object.freeze({
		"واجهة الاستقبال والتشغيل": Object.freeze({
			label: "أعمال الاستقبال والتشغيل",
			description: "الطلبات الجديدة والنواقص والمواعيد والدعم",
		}),
		"واجهة الإشراف والفرز": Object.freeze({
			label: "الإشراف والفرز المهني",
			description: "الفرز والإسناد ومراجعة العمل المهني",
		}),
		"تحرير الصفحة الرئيسية": Object.freeze({
			label: "إدارة محتوى الموقع",
			description: "العناوين والخدمات والخطوات والأسئلة الشائعة",
		}),
		"الموقع العام لرُشد": Object.freeze({
			label: "معاينة الموقع العام",
			description: "افتح الصفحة كما يراها الزائر",
		}),
	});

	const RUSHD_WORKSPACE_STEPS = Object.freeze({
		"طلبات تحتاج مراجعة": "الخطوة ١ من ٤",
		"بانتظار معلومات المستفيد": "الخطوة ٢ من ٤",
		"جاهزة للفرز": "الخطوة ٣ من ٤",
		"جاهزة للإسناد": "الخطوة ٤ من ٤",
	});

	const RUSHD_WORKSPACE_DAILY_CONTEXT = Object.freeze({
		"الحالات النشطة": "قيد تقديم الخدمة",
		"المواعيد القادمة": "بانتظار التنفيذ",
		"الموافقات المعلقة": "تحتاج استكمالاً",
		"المستشارون النشطون": "متاحون للعمل",
	});

	function makeWorkspaceSectionHeading(kicker, title, description) {
		const block = document.createElement("div");
		block.className = "ce-block col-xs-12 rushd-ux-section-heading";
		block.innerHTML = `
			<div class="ce-block__content">
				<div class="rushd-ux-section-heading__kicker">${kicker}</div>
				<div class="rushd-ux-section-heading__copy">
					<h2>${title}</h2>
					<p>${description}</p>
				</div>
			</div>
		`;
		return block;
	}

	function makeWorkspaceSpacer() {
		const block = document.createElement("div");
		block.className = "ce-block col-xs-12 rushd-ux-spacer";
		block.innerHTML =
			'<div class="ce-block__content"><div class="widget spacer"></div></div>';
		return block;
	}

	function closestWorkspaceBlock(element) {
		return element?.closest(".ce-block") || null;
	}

	function setWorkspaceWidgetContext(container, text) {
		const subtitle = container?.querySelector(".widget-subtitle");
		if (subtitle) subtitle.textContent = text;
	}

	function decorateRushdWorkspace() {
		if (!["/app/rushd", "/app/Workspaces/Rushd"].includes(window.location.pathname)) {
			return;
		}

		const redactor = document.querySelector(
			".editor-js-container .codex-editor__redactor",
		);
		if (!redactor) return;
		const hasCompleteRushdExperience =
			redactor.dataset.rushdUxReady === "1" &&
			redactor.querySelectorAll(".rushd-ux-section-heading").length === 5 &&
			redactor.querySelectorAll("[data-rushd-action='1']").length === 4;
		if (hasCompleteRushdExperience) return;
		delete redactor.dataset.rushdUxReady;

		const shortcutBlocks = new Map(
			Array.from(redactor.querySelectorAll("[shortcut_name]")).map((element) => [
				element.getAttribute("shortcut_name"),
				closestWorkspaceBlock(element),
			]),
		);
		const quickListBlocks = new Map(
			Array.from(redactor.querySelectorAll("[quick_list_name]")).map((element) => [
				element.getAttribute("quick_list_name"),
				closestWorkspaceBlock(element),
			]),
		);
		const cardBlocks = new Map(
			Array.from(redactor.querySelectorAll("[card_name]")).map((element) => [
				element.getAttribute("card_name"),
				closestWorkspaceBlock(element),
			]),
		);
		const hero = closestWorkspaceBlock(redactor.querySelector(".ce-header .h3"));
		const intro = closestWorkspaceBlock(redactor.querySelector(".ce-paragraph"));

		const actionNames = Object.keys(RUSHD_WORKSPACE_ACTIONS);
		const stepNames = Object.keys(RUSHD_WORKSPACE_STEPS);
		const dailyNames = Object.keys(RUSHD_WORKSPACE_DAILY_CONTEXT);
		const quickListNames = ["طلبات الاستقبال", "طلبات الفرز المهني"];
		const cardNames = [
			"الرحلة الاستشارية",
			"الأشخاص والصلاحيات",
			"تشغيل المستشارين",
			"الخدمات والموافقات",
			"الإشراف والتنسيق",
			"إعداد المنصة",
		];
		const requiredBlocks = [
			hero,
			intro,
			...actionNames.map((name) => shortcutBlocks.get(name)),
			...stepNames.map((name) => shortcutBlocks.get(name)),
			...dailyNames.map((name) => shortcutBlocks.get(name)),
			...quickListNames.map((name) => quickListBlocks.get(name)),
			...cardNames.map((name) => cardBlocks.get(name)),
		];
		if (requiredBlocks.some((block) => !block)) return;

		hero.querySelector(".h3").innerHTML = "<b>مركز إدارة رُشد</b>";
		intro.querySelector(".ce-paragraph").textContent =
			"رتّب يومك من هنا: ابدأ بمساحة العمل المناسبة، راجع الطلبات التي تحتاج قراراً، ثم انتقل إلى السجلات والإعدادات عند الحاجة.";

		for (const [name, action] of Object.entries(RUSHD_WORKSPACE_ACTIONS)) {
			const block = shortcutBlocks.get(name);
			const container = block.querySelector(`[shortcut_name="${name}"]`);
			const widget = container.querySelector(".shortcut-widget-box");
			const title = widget.querySelector(".widget-title .ellipsis");
			container.dataset.rushdAction = "1";
			widget.setAttribute("aria-label", action.label);
			if (title) {
				title.textContent = action.label;
				title.setAttribute("title", action.label);
			}
			setWorkspaceWidgetContext(container, action.description);
		}

		for (const [name, context] of Object.entries(RUSHD_WORKSPACE_STEPS)) {
			setWorkspaceWidgetContext(
				shortcutBlocks.get(name).querySelector(`[shortcut_name="${name}"]`),
				context,
			);
		}

		for (const [name, context] of Object.entries(RUSHD_WORKSPACE_DAILY_CONTEXT)) {
			setWorkspaceWidgetContext(
				shortcutBlocks.get(name).querySelector(`[shortcut_name="${name}"]`),
				context,
			);
		}

		const fragment = document.createDocumentFragment();
		fragment.append(hero, intro);
		fragment.append(
			makeWorkspaceSectionHeading(
				"وصول مباشر",
				"ابدأ من المهمة التي تريد إنجازها",
				"اختر مساحة العمل؛ ستنتقل مباشرة إلى الأدوات المخصصة لدورك دون البحث بين السجلات.",
			),
			...actionNames.map((name) => shortcutBlocks.get(name)),
			makeWorkspaceSpacer(),
			makeWorkspaceSectionHeading(
				"رحلة الطلب",
				"مسار الطلبات",
				"اتبع الطلبات من المراجعة حتى الإسناد؛ كل بطاقة تفتح القائمة المفلترة للمرحلة نفسها.",
			),
			...stepNames.map((name) => shortcutBlocks.get(name)),
			makeWorkspaceSpacer(),
			makeWorkspaceSectionHeading(
				"متابعة اليوم",
				"التشغيل اليومي",
				"نظرة سريعة على العمل الجاري والموارد المتاحة وما قد يؤخر تقديم الخدمة.",
			),
			...dailyNames.map((name) => shortcutBlocks.get(name)),
			makeWorkspaceSpacer(),
			makeWorkspaceSectionHeading(
				"الأولوية الآن",
				"قرارات تحتاج متابعة",
				"تعرض القوائم أحدث الطلبات التي تنتظر تدخلاً؛ افتح الطلب مباشرة أو اعرض القائمة الكاملة.",
			),
			...quickListNames.map((name) => quickListBlocks.get(name)),
			makeWorkspaceSpacer(),
			makeWorkspaceSectionHeading(
				"استخدام ثانوي",
				"السجلات والإعدادات",
				"استخدم هذا القسم لإدارة البيانات المرجعية والملفات والصلاحيات، وليس كنقطة بداية للعمل اليومي.",
			),
			...cardNames.map((name) => cardBlocks.get(name)),
		);
		redactor.replaceChildren(fragment);
		redactor.dataset.rushdUxReady = "1";
	}

	function applyRushdIdentity() {
		if (redirectAdminLegacyProfile()) return;

		const root = document.documentElement;
		root.setAttribute("dir", "rtl");
		root.setAttribute("lang", ARABIC_LANGUAGE);
		root.classList.add("rushd-rtl");

		if (document.body) {
			document.body.setAttribute("dir", "rtl");
			document.body.classList.add("rushd-rtl");
		}

		if (document.title) {
			document.title = document.title
				.replace(/Frappe(?: Framework)?|Rushd/gi, RUSHD_NAME)
				.replace(/\bLogin\b/g, "تسجيل الدخول")
				.replace(/\bSign Up\b/g, "إنشاء حساب")
				.replace(/\bForgot Password\b/g, "نسيت كلمة المرور");
		}

		const applicationName = document.querySelector('meta[name="application-name"]');
		if (applicationName) {
			applicationName.setAttribute("content", RUSHD_NAME);
		}

		if (window.frappe) {
			frappe.app_name = RUSHD_NAME;
			installRushdTranslations();

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

		if (document.body) {
			installDeskBackButton();
			installWebsiteSettingsEntry();
			decorateRushdWorkspace();
			localizeElement(document.body);
			localizeWorkspaceSidebarSections(document.body);
		}
	}

	function watchDynamicInterface() {
		if (!document.body || document.body.dataset.rushdTranslationObserver) return;

		document.body.dataset.rushdTranslationObserver = "1";
		document.addEventListener(
			"focusin",
			(event) => {
				const input = event.target;
				if (!(input instanceof HTMLInputElement)) return;

				const originalValue = input.dataset.rushdOriginalValue;
				if (originalValue) {
					input.value = originalValue;
				}
			},
			true,
		);
		document.addEventListener(
			"focusout",
			(event) => {
				const input = event.target;
				if (!(input instanceof HTMLInputElement)) return;

				window.setTimeout(() => localizeControlValue(input), 0);
			},
			true,
		);
		const observer = new MutationObserver((mutations) => {
			installRushdTranslations();
			installDeskBackButton();
			installWebsiteSettingsEntry();
			decorateRushdWorkspace();
			for (const mutation of mutations) {
				if (mutation.type === "characterData" && mutation.target.parentElement) {
					localizeElement(mutation.target.parentElement);
				}
				for (const node of mutation.addedNodes) {
					if (node.nodeType === Node.ELEMENT_NODE) {
						localizeElement(node);
					} else if (node.nodeType === Node.TEXT_NODE && node.parentElement) {
						localizeElement(node.parentElement);
					}
				}
			}
			localizeWorkspaceSidebarSections(document.body);
		});

		observer.observe(document.body, {
			childList: true,
			characterData: true,
			subtree: true,
		});
	}

	applyRushdIdentity();

	if (document.readyState === "loading") {
		document.addEventListener(
			"DOMContentLoaded",
			() => {
				applyRushdIdentity();
				watchDynamicInterface();
			},
			{ once: true },
		);
	} else {
		watchDynamicInterface();
	}

	window.addEventListener(
		"load",
		() => {
			applyRushdIdentity();
			watchDynamicInterface();
		},
		{ once: true },
	);
})();
