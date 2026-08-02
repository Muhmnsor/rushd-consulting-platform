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
		"Frappe Framework": "منصة رُشد",
		"Role Permissions Manager": "مدير صلاحيات الأدوار",
		"Set User Permissions": "تقييد وصول المستخدمين",
		"View Permitted Documents": "عرض السجلات المسموح بها",
		"View Doctype Permissions": "عرض صلاحيات أنواع السجلات",
		"Permissions > Set User Permissions": "الصلاحيات ← تقييد وصول المستخدمين",
		"Restore Original Permissions": "استعادة الصلاحيات الأصلية",
		Actions: "الإجراءات",
		Permissions: "الصلاحيات",
		"Permission Inspector": "فاحص الصلاحيات",
		Audits: "سجلات المراجعة",
		"Activity Log": "سجل النشاط",
		"Permission Log": "سجل الصلاحيات",
		"Access Log": "سجل الوصول",
		Search: "بحث",
		Notification: "الإشعارات",
		"Add Sidebar Item": "إضافة عنصر إلى القائمة الجانبية",
		Discard: "تجاهل التغييرات",
		Save: "حفظ",
		"Getting Started": "دليل البدء",
		"User Menu": "قائمة المستخدم",
		"Toggle Sidebar": "إظهار أو إخفاء القائمة الجانبية",
		"Looks like you haven’t received any notifications.":
			"لا توجد إشعارات جديدة.",
		"There are no upcoming events for you.": "لا توجد أحداث قادمة.",
		"There is nothing new to show you right now.":
			"لا توجد تحديثات جديدة حاليًا.",
		Menu: "القائمة",
		Report: "التقارير",
		Export: "تصدير",
		Print: "طباعة",
		Email: "البريد الإلكتروني",
		Select: "اختيار",
		Read: "قراءة",
		Write: "تعديل",
		Create: "إنشاء",
		Delete: "حذف",
		Submit: "اعتماد",
		Cancel: "إلغاء",
		Amend: "تعديل بعد الاعتماد",
		Share: "مشاركة",
		Import: "استيراد",
		Mask: "إخفاء البيانات الحساسة",
		Permission: "الصلاحية",
		Description: "الوصف",
		Example: "مثال",
		"Document Type": "نوع السجل",
		Role: "الدور",
		Level: "المستوى",
		Loading: "جارٍ التحميل…",
		"No Permissions set for this criteria.":
			"لا توجد صلاحيات مطابقة للاختيار الحالي.",
		"Only if Creator": "فقط إذا أنشأ المستخدم السجل",
		"Add A New Rule": "إضافة قاعدة صلاحية",
		"Add New Permission Rule": "إضافة قاعدة صلاحية جديدة",
		"Permission Level": "مستوى الصلاحية",
		"Level 0 is for document level permissions, higher levels for field level permissions.":
			"المستوى 0 لصلاحيات السجل كاملة، والمستويات الأعلى لصلاحيات الحقول.",
		Add: "إضافة",
		"Did not add": "تعذرت إضافة قاعدة الصلاحية",
		"Did not remove": "تعذر حذف قاعدة الصلاحية",
		"Reset Permissions for {0}?": "هل تريد استعادة الصلاحيات الأصلية لـ {0}؟",
		"Standard Permissions": "الصلاحيات الأصلية",
		Users: "المستخدمون",
		User: "مستخدم",
		"No user has the role <strong>{0}</strong>":
			"لا يوجد مستخدم مسند إليه الدور <strong>{0}</strong>",
		"{0} with the role <strong>{1}</strong>":
			"{0} بالدور <strong>{1}</strong>",
		"View all {0} users": "عرض المستخدمين وعددهم {0}",
		"Select Document Type or Role to start.":
			"اختر نوع السجل أو الدور للبدء.",
		Roles: "الدور",
		"Quick Help for Setting Permissions:": "دليل مبسط لضبط الصلاحيات:",
		"Permissions are set on Roles and Document Types (called DocTypes) by setting rights like Read, Write, Create, Delete, Submit, Cancel, Amend, Report, Import, Export, Print, Email and Set User Permissions.":
			"تُضبط صلاحيات كل دور على أنواع السجلات، مثل القراءة والتعديل والإنشاء والحذف والاعتماد والتقارير والاستيراد والتصدير والطباعة والبريد وتقييد الوصول.",
		"Permissions get applied on Users based on what Roles they are assigned.":
			"تُطبّق الصلاحيات على المستخدم بحسب الأدوار المسندة إليه.",
		"Roles can be set for users from their User page.":
			"يمكن إسناد الأدوار للمستخدم من صفحة حسابه.",
		"Setup > User": "تهيئة المنصة ← المستخدمون",
		"The system provides many pre-defined roles. You can add new roles to set finer permissions.":
			"توفر المنصة أدوارًا جاهزة، ويمكن إضافة دور جديد عند الحاجة إلى نطاق أدق.",
		"Add a New Role": "إضافة دور جديد",
		"Permissions are automatically applied to Standard Reports and searches.":
			"تُطبّق الصلاحيات تلقائيًا على التقارير القياسية ونتائج البحث.",
		"As a best practice, do not assign the same set of permission rule to different Roles. Instead, set multiple Roles to the same User.":
			"لإدارة أوضح، لا تكرر قواعد الصلاحية نفسها في عدة أدوار؛ أسند للمستخدم أكثر من دور عند الحاجة.",
		"Meaning of Different Permission Types:": "معنى أنواع الصلاحيات:",
		"Allows the user to search and see records.":
			"تسمح للمستخدم بالبحث عن السجلات ورؤيتها في حقول الاختيار.",
		"Allows the user to view the document.": "تسمح للمستخدم بعرض السجل.",
		"Allows the user to edit existing records they have access to.":
			"تسمح للمستخدم بتعديل السجلات التي يمكنه الوصول إليها.",
		"Allows the user to create new documents.": "تسمح للمستخدم بإنشاء سجلات جديدة.",
		"Allows the user to delete documents.": "تسمح للمستخدم بحذف السجلات.",
		"Allows printing or PDF download of documents.":
			"تسمح بطباعة السجل أو تنزيله بصيغة PDF.",
		"Allows the user to email from the document.":
			"تسمح بإرسال البريد الإلكتروني من داخل السجل.",
		"Allows the user to access reports related to the document.":
			"تسمح بالوصول إلى التقارير المرتبطة بنوع السجل.",
		"Allows the user to export data from the Report view.":
			"تسمح بتصدير البيانات من شاشة التقرير.",
		"Allows the user to use Data Import tool to create / update records.":
			"تسمح باستخدام أداة الاستيراد لإنشاء السجلات أو تحديثها.",
		"Allows sharing document access with other users.":
			"تسمح بمشاركة الوصول إلى السجل مع مستخدمين آخرين.",
		"Allows users to enable the mask property for any field of the respective doctype.":
			"تسمح بإخفاء قيمة الحقول الحساسة عن العرض الكامل.",
		"The user can select a Customer in Sales Order but cannot open the Customer master.":
			"يمكن للمستخدم اختيار سجل مرتبط داخل الطلب، لكنه لا يستطيع فتح السجل نفسه.",
		"The user can view Sales Invoices but cannot modify any field values in them.":
			"يمكن للمستخدم عرض السجل، لكنه لا يستطيع تعديل قيمه.",
		"The user can update a customer or any other fields in an existing Sales Order but cannot create a new Sales Order.":
			"يمكن للمستخدم تحديث سجل موجود، لكنه لا يستطيع إنشاء سجل جديد.",
		"The user can create a new Item but cannot edit existing items.":
			"يمكن للمستخدم إنشاء سجل جديد، لكنه لا يستطيع تعديل السجلات الموجودة.",
		"The user can delete Draft / Cancelled documents.":
			"يمكن للمستخدم حذف السجلات المسودة أو الملغاة.",
		"The print button is enabled for the user in the document.":
			"يظهر زر الطباعة للمستخدم داخل السجل.",
		"The email button is enabled for the user in the document.":
			"يظهر زر البريد الإلكتروني للمستخدم داخل السجل.",
		"If the user has access to Employee and Report is enabled, they can view Employee-based reports.":
			"إذا كان للمستخدم وصول إلى نوع السجل وفُعّلت التقارير، فيمكنه عرض تقاريره.",
		"The user can export report data.": "يمكن للمستخدم تصدير بيانات التقرير.",
		"The user can import new records or update existing data for the document.":
			"يمكن للمستخدم استيراد سجلات جديدة أو تحديث السجلات الموجودة.",
		"The user can share document access with another user.":
			"يمكن للمستخدم مشاركة الوصول إلى السجل مع مستخدم آخر.",
		"If the user enables the mask property for the phone number field, the value will be displayed in a masked format (e.g., 811XXXXXXX).":
			"عند تفعيل الإخفاء على حقل حساس، تظهر القيمة بشكل محجوب جزئيًا.",
		"Permission Levels:": "مستويات الصلاحية:",
		"Permissions at level 0 are Document Level permissions, i.e. they are primary for access to the document.":
			"صلاحيات المستوى 0 هي صلاحيات السجل الأساسية التي تحدد إمكانية الوصول إليه.",
		"If a Role does not have access at Level 0, then higher levels are meaningless.":
			"إذا لم يملك الدور وصولًا في المستوى 0 فلن يكون للمستويات الأعلى أثر.",
		"Permissions at higher levels are Field Level permissions. All Fields have a Permission Level set against them and the rules defined at that permissions apply to the field. This is useful in case you want to hide or make certain field read-only for certain Roles.":
			"المستويات الأعلى تخص الحقول؛ وتفيد في إخفاء حقول محددة أو جعلها للقراءة فقط بحسب الدور.",
		"You can use Customize Form to set levels on fields.":
			"يمكن ضبط مستوى كل حقل من شاشة تخصيص النماذج.",
		"Setup > Customize Form": "تهيئة المنصة ← تخصيص النماذج",
		"User Permissions:": "قيود وصول المستخدم:",
		"User Permissions are used to limit users to specific records.":
			"تُستخدم قيود الوصول لحصر المستخدم في سجلات محددة.",
		"Setup > User Permissions": "تهيئة المنصة ← قيود وصول المستخدمين",
		"Select Document Types to set which User Permissions are used to limit access.":
			"اختر أنواع السجلات التي ستُطبّق عليها قيود الوصول.",
		"Once you have set this, the users will only be able access documents (eg. Blog Post) where the link exists (eg. Blogger).":
			"بعد ضبطها، لن يصل المستخدم إلا إلى السجلات المرتبطة بالقيمة المسموح له بها.",
		"Apart from System Manager, roles with Set User Permissions right can set permissions for other users for that Document Type.":
			"إضافة إلى مسؤول النظام، يمكن للأدوار المخولة بتقييد الوصول ضبط هذه القيود للمستخدمين الآخرين.",
		"Submit an Issue": "العودة إلى إدارة الأدوار",
		"If these instructions where not helpful, please add in your suggestions on GitHub Issues.":
			"إذا احتجت إلى مساعدة تشغيلية، ارجع إلى صفحة إدارة الأدوار المبسطة.",
		"System Health": "صحة النظام",
		Logout: "تسجيل الخروج",
		"You do not have enough permissions to complete the action":
			"لا تملك الصلاحية الكافية لإكمال هذا الإجراء.",
		"You do not have enough permissions to access this resource. Please contact your manager to get access.":
			"لا تملك الصلاحية للوصول إلى هذه الصفحة. تواصل مع مسؤول النظام إذا كنت تحتاج إليها.",
		"Show Error": "عرض التفاصيل التقنية",
		"Not permitted": "غير مسموح",
		Today: "اليوم",
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

	function applyRushdDeskBrand(root = document) {
		root
			.querySelectorAll?.(
				'.body-sidebar .header-logo img, img[src*="frappe-framework-logo.svg"]',
			)
			.forEach((logo) => {
				logo.src = "/assets/consultation_center/images/rushd-logo.svg";
				logo.alt = RUSHD_NAME;
			});

		root.querySelectorAll?.(".body-sidebar .header-subtitle").forEach((label) => {
			if (label.textContent.trim() === "Frappe Framework") {
				label.textContent = "منصة رُشد";
			}
		});
	}

	function installPermissionManagerIdentity() {
		const page = document.querySelector("#page-permission-manager");
		if (!page) return;

		page.classList.add("rushd-permission-manager");
		const permissionActions = {
			"Set User Permissions": "تقييد وصول المستخدمين",
			"Restore Original Permissions": "استعادة الصلاحيات الأصلية",
			Actions: "الإجراءات",
		};
		page.querySelectorAll("[data-label]").forEach((element) => {
			let source = element.dataset.label || "";
			try {
				source = decodeURIComponent(source);
			} catch (_error) {
				return;
			}
			if (permissionActions[source]) {
				if (element.textContent.trim() !== permissionActions[source]) {
					element.textContent = permissionActions[source];
				}
			}
		});
		const issueLink = [...page.querySelectorAll("a")].find(
			(link) =>
				["Submit an Issue", "العودة إلى إدارة الأدوار"].includes(
					link.textContent.trim(),
				),
		);
		if (issueLink) {
			issueLink.href = "/admin/roles";
			issueLink.removeAttribute("target");
			issueLink.removeAttribute("rel");
		}

		if (page.querySelector(".rushd-permission-page-intro")) return;
		const content = page.querySelector(".page-content, .layout-main-section-wrapper");
		if (!content) return;

		const intro = document.createElement("section");
		intro.className = "rushd-permission-page-intro";
		intro.innerHTML = `
			<div>
				<span>إعداد متقدم لمسؤول النظام</span>
				<strong>صلاحيات واضحة وآمنة لكل دور</strong>
				<p>اختر نوع السجل والدور، ثم فعّل أقل قدر من الصلاحيات اللازمة للعمل. التغييرات هنا تؤثر مباشرة في وصول المستخدمين إلى بيانات المنصة.</p>
			</div>
			<a href="/admin/roles">العودة إلى إدارة الأدوار</a>
		`;
		content.prepend(intro);
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
			applyRushdDeskBrand(document.body);
			installPermissionManagerIdentity();
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
			applyRushdDeskBrand(document.body);
			installPermissionManagerIdentity();
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
			applyRushdDeskBrand(document.body);
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
