app_name = "po"
app_title = "PO Limiter"
app_publisher = "Ejiroghene Dominic"
app_description = "Purchase Order Limiter"
app_email = "ejise45@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/po/css/po_limiter.css"
# app_include_js = "/assets/po/js/po.js"

# include js, css files in header of web template
# web_include_css = "/assets/po/css/po.css"
# web_include_js = "/assets/po/js/po.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "po/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Include PO Limiter client-side script for Purchase Order
doctype_js = {
	"Purchase Order": "po.po_limiter.purchase_order_client"
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

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
jinja = {
	"methods": "po.po_limiter.utils.jinja_methods"
}

# Installation
# ------------

# before_install = "po.install.before_install"
# after_install = "po.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "po.uninstall.before_uninstall"
# after_uninstall = "po.uninstall.after_uninstall"

# Additional DocTypes to be installed
# -----------------------------------

doctype_list = [
	"User PO Limit",
	"PO Limit Increase Request"
]

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "po.utils.before_app_install"
# after_app_install = "po.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "po.utils.before_app_uninstall"
# after_app_uninstall = "po.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "po.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Order": {
		"validate": "po.po_limiter.po_validation.validate_po_limits",
		"on_submit": "po.po_limiter.po_validation.validate_po_limits",
		"on_cancel": "po.po_limiter.po_validation.update_monthly_usage_on_po_cancel"
	},
	"User": {
		"after_insert": "po.po_limiter.user_hooks.create_default_po_limit"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"po.tasks.all"
# 	],
# 	"daily": [
# 		"po.tasks.daily"
# 	],
# 	"hourly": [
# 		"po.tasks.hourly"
# 	],
# 	"weekly": [
# 		"po.tasks.weekly"
# 	],
# 	"monthly": [
# 		"po.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "po.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "po.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "po.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["po.utils.before_request"]
# after_request = ["po.utils.after_request"]

# Job Events
# ----------
# before_job = ["po.utils.before_job"]
# after_job = ["po.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"po.auth.validate"
# ]
