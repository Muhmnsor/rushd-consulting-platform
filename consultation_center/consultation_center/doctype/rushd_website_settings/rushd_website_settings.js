frappe.ui.form.on("Rushd Website Settings", {
	refresh(frm) {
		frm.page.wrapper.addClass("rushd-website-settings-form");
		frm.add_custom_button("معاينة الصفحة الرئيسية", () => {
			window.open("/", "_blank", "noopener");
		});
	},
});
