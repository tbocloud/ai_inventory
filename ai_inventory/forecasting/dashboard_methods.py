# ==========================================
# ai_inventory/forecasting/dashboard_methods.py
# Custom methods for AI Sales Dashboard doctype

import frappe
from frappe.model.document import Document
import json

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

@frappe.whitelist()
def sync_all_forecasts():
    """Manually sync all forecast types"""
    try:
        from ai_inventory.forecasting.sync_manager import sync_all_forecast_types
        result = sync_all_forecast_types()
        return {"status": "success", "data": result}
    except Exception as e:
        frappe.log_error(f"Sync all forecasts error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_forecast_comparison():
    """Get comparison data for all forecast types"""
    try:
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        # Get latest forecasts for all types
        financial_data = frappe.db.sql("""
            SELECT forecast_start_date, predicted_amount, confidence_score, prediction_model
            FROM `tabAI Financial Forecast`
            WHERE company = %s
            ORDER BY forecast_start_date DESC
            LIMIT 10
        """, [company], as_dict=True)
        
        cashflow_data = frappe.db.sql("""
            SELECT forecast_date, net_cash_flow, confidence_score, model_used
            FROM `tabAI Cashflow Forecast`
            WHERE company = %s
            ORDER BY forecast_date DESC
            LIMIT 10
        """, [company], as_dict=True)
        
        revenue_data = frappe.db.sql("""
            SELECT forecast_date, total_predicted_revenue, confidence_score, model_used
            FROM `tabAI Revenue Forecast`
            WHERE company = %s
            ORDER BY forecast_date DESC
            LIMIT 10
        """, [company], as_dict=True)
        
        # Format data for comparison
        comparison_data = {
            "financial": financial_data,
            "cashflow": cashflow_data,
            "revenue": revenue_data,
            "sync_status": {
                "last_sync": frappe.utils.now(),
                "total_synced": len(financial_data) + len(cashflow_data) + len(revenue_data)
            }
        }
        
        return {"status": "success", "data": comparison_data}
        
    except Exception as e:
        frappe.log_error(f"Forecast comparison error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_financial_forecast_summary():
    """Get comprehensive AI Financial Forecast summary"""
    try:
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        # Recent forecasts
        recent_forecasts = frappe.db.sql("""
            SELECT 
                name,
                forecast_start_date,
                forecast_end_date,
                predicted_amount,
                confidence_score,
                prediction_model,
                forecast_type,
                forecast_status
            FROM `tabAI Financial Forecast`
            WHERE company = %s
            ORDER BY forecast_start_date DESC
            LIMIT 5
        """, [company], as_dict=True)
        
        # Accuracy metrics
        accuracy_data = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_forecasts,
                AVG(confidence_score) as avg_confidence,
                COUNT(CASE WHEN confidence_score >= 80 THEN 1 END) as high_confidence_count
            FROM `tabAI Financial Forecast`
            WHERE company = %s
            AND forecast_start_date >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
        """, [company], as_dict=True)
        
        # Model performance
        model_performance = frappe.db.sql("""
            SELECT 
                prediction_model,
                COUNT(*) as usage_count,
                AVG(confidence_score) as avg_confidence
            FROM `tabAI Financial Forecast`
            WHERE company = %s
            AND forecast_start_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            GROUP BY prediction_model
            ORDER BY usage_count DESC
        """, [company], as_dict=True)
        
        return {
            "status": "success",
            "data": {
                "recent_forecasts": recent_forecasts,
                "accuracy_metrics": accuracy_data[0] if accuracy_data else {},
                "model_performance": model_performance,
                "total_forecasts": len(recent_forecasts)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Financial forecast summary error: {str(e)}")
        return {"status": "error", "message": str(e)}
