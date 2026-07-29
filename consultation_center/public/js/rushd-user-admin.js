frappe.ui.form.on("User", {
	refresh(frm) {
		if (
			frm.is_new()
			|| !frappe.user.has_role("System Manager")
			|| frm.doc.name === "Guest"
			|| (frm.doc.name === "Administrator" && frappe.session.user !== "Administrator")
		) {
			return;
		}

		frm.add_custom_button(
			"تعيين كلمة مرور مباشرة",
			() => {
				const dialog = new frappe.ui.Dialog({
					title: `تعيين كلمة مرور — ${frm.doc.full_name || frm.doc.name}`,
					fields: [
						{
							fieldtype: "HTML",
							options:
								'<div class="alert alert-warning">لن تُرسل رسالة أو رابط للمستخدم. سيُسجّل هذا الإجراء في سجل المستخدم.</div>',
						},
						{
							label: "كلمة المرور الجديدة",
							fieldname: "new_password",
							fieldtype: "Password",
							reqd: 1,
						},
						{
							label: "تأكيد كلمة المرور",
							fieldname: "confirm_password",
							fieldtype: "Password",
							reqd: 1,
						},
						{
							label: "تسجيل خروج المستخدم من الجلسات الحالية",
							fieldname: "logout_all_sessions",
							fieldtype: "Check",
							default: 1,
						},
					],
					primary_action_label: "حفظ كلمة المرور",
					primary_action(values) {
						if (values.new_password !== values.confirm_password) {
							frappe.msgprint({
								title: "تحقق من كلمة المرور",
								message: "كلمتا المرور غير متطابقتين.",
								indicator: "red",
							});
							return;
						}

						dialog.get_primary_btn().prop("disabled", true);
						frappe.call({
							method: "consultation_center.api.user_admin.set_user_password",
							type: "POST",
							args: {
								user: frm.doc.name,
								new_password: values.new_password,
								logout_all_sessions: values.logout_all_sessions,
							},
							callback(response) {
								dialog.hide();
								frappe.show_alert({
									message: response.message.message,
									indicator: "green",
								});
								frm.reload_doc();
							},
							error() {
								dialog.get_primary_btn().prop("disabled", false);
							},
						});
					},
				});
				dialog.show();
			},
			"كلمة المرور"
		);
	},
});
