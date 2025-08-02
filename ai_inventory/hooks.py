# ai_inventory/hooks.py
# UPDATED VERSION - Replace your existing hooks.py

app_name = "ai_inventory"
app_title = "Ai Inventory"
app_publisher = "sammish"
app_description = "Ai Inventory"
app_email = "sammish.thundiyil@gmail.com"
app_license = "mit"

# Document Events with Safety Wrappers
doc_events = {
    "Stock Ledger Entry": {
        "on_submit": "ai_inventory.hooks_handlers.on_stock_ledger_entry_submit_safe"
    },
    "Purchase Order": {
        "on_submit": "ai_inventory.hooks_handlers.on_purchase_order_submit_safe"
    },
    "Purchase Receipt": {
        "on_submit": "ai_inventory.hooks_handlers.on_purchase_receipt_submit_safe"
    },
    "Item": {
        "after_insert": "ai_inventory.hooks_handlers.on_item_after_insert_safe",
        "on_update": "ai_inventory.hooks_handlers.on_item_on_update_safe"
    },
    "Warehouse": {
        "after_insert": "ai_inventory.hooks_handlers.on_warehouse_after_insert_safe"
    },
    "AI Inventory Forecast": {
        "validate": "ai_inventory.hooks_handlers.validate_ai_inventory_forecast_safe",
        "on_save": "ai_inventory.hooks_handlers.on_ai_inventory_forecast_save_safe"
    },
    "Bin": {
        "on_update": "ai_inventory.hooks_handlers.on_bin_update_safe"
    },
    "Stock Entry": {
        "on_submit": "ai_inventory.hooks_handlers.on_stock_entry_submit_safe"
    },
    "Sales Order": {
        "on_submit": "ai_inventory.forecasting.triggers.on_sales_order_submit"
    },
    "Sales Invoice": {
        "on_submit": "ai_inventory.forecasting.triggers.on_sales_invoice_submit",
        "on_cancel": "ai_inventory.forecasting.triggers.on_sales_invoice_cancel"
    }
}

# Scheduled Tasks
scheduler_events = {
    # Real-time monitoring (every 5 minutes)
    "cron": {
        "*/5 * * * *": [
            "ai_inventory.scheduled_tasks.real_time_stock_monitor"
        ]
    },
    
    # Hourly tasks
    "hourly": [
        "ai_inventory.scheduled_tasks.hourly_critical_stock_check",
        "ai_inventory.hooks_handlers.process_forecast_update_queue"
    ],
    
    # Daily tasks (6 AM)
    "daily": [
        "ai_inventory.scheduled_tasks.daily_ai_forecast",
        "ai_inventory.hooks_handlers.daily_create_missing_forecasts",
        "ai_inventory.ml_supplier_analyzer.daily_ml_supplier_analysis"
    ],
    
    # Weekly tasks (Sunday 7 AM)
    "weekly": [
        "ai_inventory.scheduled_tasks.weekly_forecast_analysis",
        "ai_inventory.ml_supplier_analyzer.weekly_supplier_segmentation"
    ],
    
    # Monthly tasks (1st of month, 8 AM)
    "monthly": [
        "ai_inventory.scheduled_tasks.optimize_forecast_performance",
        "ai_inventory.scheduled_tasks.cleanup_old_forecast_data"
    ]
}

# Installation Hooks - CRITICAL: This ensures packages are installed BEFORE DocType creation
before_install = "ai_inventory.install.before_install"
after_install = "ai_inventory.install.after_install"
before_uninstall = "ai_inventory.install.before_uninstall"

# Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt", "in", [
                    "Purchase Order",
                    "Purchase Order Item",
                    "Supplier", 
                    "AI Inventory Forecast"
                ]
            ]
        ]
    },
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "doc_type", "in", [
                    "Purchase Order",
                    "Purchase Order Item",
                    "Supplier",
                    "AI Inventory Forecast"
                ]
            ]
        ]
    }
]

# include js, css files in header of desk.html
# app_include_css = "/assets/ai_inventory/css/ai_inventory.css"
# app_include_js = "/assets/ai_inventory/js/ai_inventory.js"

# include js, css files in header of web template
# web_include_css = "/assets/ai_inventory/css/ai_inventory.css"
# web_include_js = "/assets/ai_inventory/js/ai_inventory.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ai_inventory/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ai_inventory/public/icons.svg"

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
# 	"methods": "ai_inventory.utils.jinja_methods",
# 	"filters": "ai_inventory.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ai_inventory.install.before_install"
# after_install = "ai_inventory.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ai_inventory.uninstall.before_uninstall"
# after_uninstall = "ai_inventory.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ai_inventory.utils.before_app_install"
# after_app_install = "ai_inventory.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ai_inventory.utils.before_app_uninstall"
# after_app_uninstall = "ai_inventory.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ai_inventory.notifications.get_notification_config"

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
# 		"ai_inventory.tasks.all"
# 	],
# 	"daily": [
# 		"ai_inventory.tasks.daily"
# 	],
# 	"hourly": [
# 		"ai_inventory.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ai_inventory.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ai_inventory.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ai_inventory.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ai_inventory.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ai_inventory.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ai_inventory.utils.before_request"]
# after_request = ["ai_inventory.utils.after_request"]

# Job Events
# ----------
# before_job = ["ai_inventory.utils.before_job"]
# after_job = ["ai_inventory.utils.after_job"]

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
# 	"ai_inventory.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }