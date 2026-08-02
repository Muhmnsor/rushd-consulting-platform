app_name = "consultation_center"
app_title = "رُشد"
app_publisher = "رُشد"
app_description = "منصة رُشد للاستشارات الشبابية"
app_email = "admin@rushd.local"
app_license = "mit"
app_logo_url = "/assets/consultation_center/images/rushd-logo.svg"
rushd_asset_version = "20260802-22"
brand_html = """
<span class="rushd-brand-wordmark">
	<img class="rushd-brand-symbol" src="/assets/consultation_center/images/rushd-logo.svg" alt="">
	<span>رُشد</span>
</span>
"""

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "consultation_center",
		"title": "رُشد",
		"route": "/admin",
		"has_permission": "consultation_center.permissions.has_admin_app_access",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	f"/assets/consultation_center/css/fonts.css?v={rushd_asset_version}",
	f"/assets/consultation_center/css/rushd-rtl.css?v={rushd_asset_version}",
]
app_include_js = [
	f"/assets/consultation_center/js/rushd-rtl.js?v={rushd_asset_version}",
	f"/assets/consultation_center/js/rushd-admin-entry.js?v={rushd_asset_version}",
]

# include js, css files in header of web template
web_include_css = [
	f"/assets/consultation_center/css/fonts.css?v={rushd_asset_version}",
	f"/assets/consultation_center/css/rushd-rtl.css?v={rushd_asset_version}",
]
web_include_js = [
	f"/assets/consultation_center/js/rushd-rtl.js?v={rushd_asset_version}",
	f"/assets/consultation_center/js/rushd-auth.js?v={rushd_asset_version}",
]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "consultation_center/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}
page_js = {"setup-wizard": "public/js/rushd-setup-wizard.js"}

# include js in doctype views
doctype_js = {"User": "public/js/rushd-user-admin.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "consultation_center/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "index"

signup_form_template = "consultation_center/templates/includes/rushd_signup.html"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "consultation_center.utils.jinja_methods",
# 	"filters": "consultation_center.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "consultation_center.install.before_install"
after_install = "consultation_center.setup.install.after_install"
after_migrate = "consultation_center.setup.install.after_migrate"
boot_session = "consultation_center.boot.add_rushd_display_translations"
extend_bootinfo = ["consultation_center.boot.add_rushd_display_translations"]

# Uninstallation
# ------------

# before_uninstall = "consultation_center.uninstall.before_uninstall"
# after_uninstall = "consultation_center.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "consultation_center.utils.before_app_install"
# after_app_install = "consultation_center.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "consultation_center.utils.before_app_uninstall"
# after_app_uninstall = "consultation_center.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "consultation_center.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Beneficiary": "consultation_center.permissions.beneficiary_query",
	"Guardian": "consultation_center.permissions.guardian_query",
	"Guardian Authorization": "consultation_center.permissions.guardian_authorization_query",
	"Consent Record": "consultation_center.permissions.consent_record_query",
	"Consultant": "consultation_center.permissions.consultant_query",
	"Consultant Availability Rule": "consultation_center.permissions.availability_query",
	"Consultant Time Off": "consultation_center.permissions.time_off_query",
	"Consultation Request": "consultation_center.permissions.request_query",
	"Consultation Case": "consultation_center.permissions.case_query",
	"Consultation Appointment": "consultation_center.permissions.appointment_query",
	"Consultation Session": "consultation_center.permissions.session_query",
	"Consultation Plan": "consultation_center.permissions.plan_query",
	"Beneficiary Task": "consultation_center.permissions.beneficiary_task_query",
	"Assessment Template": "consultation_center.permissions.assessment_template_query",
	"Assessment Version": "consultation_center.permissions.assessment_version_query",
	"Assessment Submission": "consultation_center.permissions.assessment_submission_query",
	"Case Referral": "consultation_center.permissions.case_referral_query",
	"Supervision Request": "consultation_center.permissions.supervision_request_query",
	"Professional Escalation": "consultation_center.permissions.professional_escalation_query",
	"Support Ticket": "consultation_center.permissions.support_ticket_query",
	"Complaint": "consultation_center.permissions.complaint_query",
	"Case Document": "consultation_center.permissions.case_document_query",
}

has_permission = {
	"Beneficiary": "consultation_center.permissions.has_permission",
	"Guardian": "consultation_center.permissions.has_permission",
	"Guardian Authorization": "consultation_center.permissions.has_permission",
	"Consent Record": "consultation_center.permissions.has_permission",
	"Consultant": "consultation_center.permissions.has_permission",
	"Consultant Availability Rule": "consultation_center.permissions.has_permission",
	"Consultant Time Off": "consultation_center.permissions.has_permission",
	"Consultation Request": "consultation_center.permissions.has_permission",
	"Consultation Case": "consultation_center.permissions.has_permission",
	"Consultation Appointment": "consultation_center.permissions.has_permission",
	"Consultation Session": "consultation_center.permissions.has_permission",
	"Consultation Plan": "consultation_center.permissions.has_permission",
	"Beneficiary Task": "consultation_center.permissions.has_permission",
	"Assessment Template": "consultation_center.permissions.has_permission",
	"Assessment Version": "consultation_center.permissions.has_permission",
	"Assessment Submission": "consultation_center.permissions.has_permission",
	"Case Referral": "consultation_center.permissions.has_permission",
	"Supervision Request": "consultation_center.permissions.has_permission",
	"Professional Escalation": "consultation_center.permissions.has_permission",
	"Support Ticket": "consultation_center.permissions.has_permission",
	"Complaint": "consultation_center.permissions.has_permission",
	"Case Document": "consultation_center.permissions.has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"consultation_center.tasks.all"
# 	],
# 	"daily": [
# 		"consultation_center.tasks.daily"
# 	],
# 	"hourly": [
# 		"consultation_center.tasks.hourly"
# 	],
# 	"weekly": [
# 		"consultation_center.tasks.weekly"
# 	],
# 	"monthly": [
# 		"consultation_center.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "consultation_center.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.core.doctype.user.user.sign_up": "consultation_center.api.auth.sign_up",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "consultation_center.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["consultation_center.localization.force_arabic_for_guests"]
# after_request = ["consultation_center.utils.after_request"]

# Job Events
# ----------
# before_job = ["consultation_center.utils.before_job"]
# after_job = ["consultation_center.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "Beneficiary",
		"filter_by": "email",
		"redact_fields": ["beneficiary_name", "mobile", "id_number_encrypted"],
	},
	{
		"doctype": "Guardian",
		"filter_by": "email",
		"redact_fields": ["guardian_name", "mobile", "id_number_encrypted"],
	},
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"consultation_center.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
