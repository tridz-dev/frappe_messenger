app_name = "frappe_messenger"
app_title = "Frappe Messenger"
app_publisher = "Tridz Technologies Pvt. Ltd."
app_description = "Integrate and manage Facebook Messenger and Instagram messages from Frappe."
app_email = "info@tridz.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "frappe_messenger",
# 		"logo": "/assets/frappe_messenger/logo.png",
# 		"title": "Frappe Messenger",
# 		"route": "/frappe_messenger",
# 		"has_permission": "frappe_messenger.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/frappe_messenger/css/frappe_messenger.css"
# app_include_js = "/assets/frappe_messenger/js/frappe_messenger.js"

# include js, css files in header of web template
# web_include_css = "/assets/frappe_messenger/css/frappe_messenger.css"
# web_include_js = "/assets/frappe_messenger/js/frappe_messenger.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "frappe_messenger/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"Messenger Message" : "public/js/messenger_message_list.js"}
doctype_list_js = {"Messenger Message" : "public/js/messenger_message_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "frappe_messenger/public/icons.svg"

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
# jinja = {
# 	"methods": "frappe_messenger.utils.jinja_methods",
# 	"filters": "frappe_messenger.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "frappe_messenger.install.before_install"
after_install = "frappe_messenger.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "frappe_messenger.uninstall.before_uninstall"
# after_uninstall = "frappe_messenger.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "frappe_messenger.utils.before_app_install"
# after_app_install = "frappe_messenger.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "frappe_messenger.utils.before_app_uninstall"
# after_app_uninstall = "frappe_messenger.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frappe_messenger.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
permission_query_conditions = {
	"Messenger Conversation": "frappe_messenger.frappe_messenger.doctype.messenger_message.messenger_message.get_permission_query_conditions",
}

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
	"WhatsApp Message": {
		"on_update": "frappe_messenger.utils.whatsapp_to_messenger.get_whatsapp_message"
	}
}
# doc_events = {
# 	"Messenger Message ": {
# 		"after_insert": "frappe_messenger.utils.webhook.send_message_on_creation"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"frappe_messenger.tasks.all"
# 	],
# 	"daily": [
# 		"frappe_messenger.tasks.daily"
# 	],
# 	"hourly": [
# 		"frappe_messenger.tasks.hourly"
# 	],
# 	"weekly": [
# 		"frappe_messenger.tasks.weekly"
# 	],
# 	"monthly": [
# 		"frappe_messenger.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "frappe_messenger.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "frappe_messenger.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "frappe_messenger.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["frappe_messenger.utils.before_request"]
# after_request = ["frappe_messenger.utils.after_request"]

# Job Events
# ----------
# before_job = ["frappe_messenger.utils.before_job"]
# after_job = ["frappe_messenger.utils.after_job"]

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
# 	"frappe_messenger.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                {
                    "WhatsApp Message-custom_message_from_messenger",
                    "CRM Lead-custom_messenger_conversation"
                },
            ]
        ],
    }
]

