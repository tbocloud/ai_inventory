# ==========================================
# ai_inventory/forecasting/dashboard_methods.py
# Custom methods for AI Sales Dashboard doctype

import frappe
from frappe.model.document import Document

class AISalesDashboard(Document):
    def validate(self):
        """Validate dashboard settings"""
        if self.confidence_threshold and self.min_confidence_threshold:
            if self.confidence_threshold <= self.min_confidence_threshold:
                frappe.throw("Auto Create SO Confidence Threshold must be higher than Minimum Confidence Threshold")
    
    def on_update(self):
        """Trigger actions when dashboard is updated"""
        # If auto sync was just enabled, trigger immediate forecast
        if self.enable_auto_sync and self.has_value_changed("enable_auto_sync"):
            frappe.enqueue('ai_inventory.forecasting.core.generate_forecasts',
                         queue='short',
                         timeout=300)
