import frappe

def get_context(context):
    context.no_cache = 1
    context.title = "AI Financial Forecast - System Health Dashboard"
    context.include_js = [
        "https://cdn.jsdelivr.net/npm/chart.js",
        "https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"
    ]
    return context
