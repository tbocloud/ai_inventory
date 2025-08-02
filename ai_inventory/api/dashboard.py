# ==========================================
# ai_inventory/api/dashboard.py
# Additional API endpoints for dashboard

import frappe
from frappe.utils import nowdate, add_days, get_datetime
import json

@frappe.whitelist()
def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    try:
        # Total forecasts for next 30 days
        total_forecasts = frappe.db.count("Sales Forecast", {
            "forecast_date": ["between", [nowdate(), add_days(nowdate(), 30)]]
        })
        
        # High confidence forecasts
        high_confidence = frappe.db.count("Sales Forecast", {
            "forecast_date": ["between", [nowdate(), add_days(nowdate(), 30)]],
            "confidence_score": [">=", 80]
        })
        
        # Items with forecasting enabled
        enabled_items = frappe.db.count("Item", {"enable_forecast": 1})
        
        # Recent accuracy
        accuracy = frappe.db.sql("""
            SELECT AVG(accuracy_score) as avg_accuracy
            FROM `tabSales Forecast`
            WHERE accuracy_score IS NOT NULL
            AND forecast_date >= %s
        """, (add_days(nowdate(), -30),))
        
        avg_accuracy = accuracy[0][0] if accuracy and accuracy[0][0] else 0
        
        # Trend data for charts
        trend_data = frappe.db.sql("""
            SELECT 
                DATE(forecast_date) as date,
                SUM(predicted_qty) as total_qty,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) as forecast_count
            FROM `tabSales Forecast`
            WHERE forecast_date >= %s
            GROUP BY DATE(forecast_date)
            ORDER BY date
        """, (add_days(nowdate(), -30),), as_dict=True)
        
        return {
            "success": True,
            "summary": {
                "total_forecasts": total_forecasts,
                "high_confidence_forecasts": high_confidence,
                "enabled_items": enabled_items,
                "average_accuracy": round(avg_accuracy, 2) if avg_accuracy else 0,
                "confidence_percentage": round((high_confidence / total_forecasts * 100), 2) if total_forecasts > 0 else 0
            },
            "trend_data": trend_data
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard summary failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def get_item_forecast_details(item_code, days=30):
    """Get detailed forecast for specific item"""
    try:
        forecasts = frappe.db.sql("""
            SELECT 
                sf.*,
                c.customer_name,
                c.customer_segment,
                i.item_name,
                i.item_group
            FROM `tabSales Forecast` sf
            LEFT JOIN `tabCustomer` c ON sf.customer = c.name
            LEFT JOIN `tabItem` i ON sf.item_code = i.name
            WHERE sf.item_code = %s
            AND sf.forecast_date BETWEEN %s AND %s
            ORDER BY sf.forecast_date, sf.confidence_score DESC
        """, (item_code, nowdate(), add_days(nowdate(), days)), as_dict=True)
        
        # Historical sales for comparison
        historical = frappe.db.sql("""
            SELECT 
                si.posting_date,
                sii.qty,
                sii.amount,
                si.customer
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
            WHERE sii.item_code = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
            ORDER BY si.posting_date DESC
        """, (item_code, add_days(nowdate(), -90)), as_dict=True)
        
        return {
            "success": True,
            "forecasts": forecasts,
            "historical_sales": historical
        }
        
    except Exception as e:
        frappe.log_error(f"Item forecast details failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def update_forecast_confidence(forecast_name, new_confidence, notes=""):
    """Manually update forecast confidence"""
    try:
        forecast = frappe.get_doc("Sales Forecast", forecast_name)
        
        old_confidence = forecast.confidence_score
        forecast.confidence_score = new_confidence
        forecast.notes = f"{forecast.notes or ''}\nManual adjustment: {old_confidence}% -> {new_confidence}% ({notes})"
        forecast.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": f"Confidence updated from {old_confidence}% to {new_confidence}%"
        }
        
    except Exception as e:
        frappe.log_error(f"Confidence update failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def bulk_update_item_forecast_settings(items_data):
    """Bulk update forecast settings for multiple items"""
    try:
        items_data = json.loads(items_data) if isinstance(items_data, str) else items_data
        updated_count = 0
        
        for item_data in items_data:
            item_code = item_data.get('item_code')
            enable_forecast = item_data.get('enable_forecast', 0)
            
            if item_code:
                frappe.db.set_value("Item", item_code, "enable_forecast", enable_forecast)
                updated_count += 1
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Updated forecast settings for {updated_count} items"
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk update failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def export_forecasts(filters=None):
    """Export forecasts to Excel/CSV"""
    try:
        filters = json.loads(filters) if isinstance(filters, str) else filters or {}
        
        conditions = ["1=1"]
        values = []
        
        if filters.get('item_code'):
            conditions.append("sf.item_code = %s")
            values.append(filters['item_code'])
        
        if filters.get('customer'):
            conditions.append("sf.customer = %s")
            values.append(filters['customer'])
        
        if filters.get('date_range'):
            conditions.append("sf.forecast_date BETWEEN %s AND %s")
            values.extend(filters['date_range'])
        
        where_clause = " AND ".join(conditions)
        
        forecasts = frappe.db.sql(f"""
            SELECT 
                sf.item_code,
                i.item_name,
                sf.customer,
                c.customer_name,
                sf.territory,
                sf.forecast_date,
                sf.predicted_qty,
                sf.confidence_score,
                sf.model_version,
                sf.actual_qty,
                sf.accuracy_score
            FROM `tabSales Forecast` sf
            LEFT JOIN `tabItem` i ON sf.item_code = i.name
            LEFT JOIN `tabCustomer` c ON sf.customer = c.name
            WHERE {where_clause}
            ORDER BY sf.forecast_date, sf.item_code
        """, values, as_dict=True)
        
        return {
            "success": True,
            "data": forecasts,
            "count": len(forecasts)
        }
        
    except Exception as e:
        frappe.log_error(f"Export failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}