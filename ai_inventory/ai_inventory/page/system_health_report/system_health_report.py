import frappe
from frappe import _

def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
