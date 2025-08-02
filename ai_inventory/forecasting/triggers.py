# ==========================================
# ai_inventory/forecasting/triggers.py
# Event triggers for real-time updates

import frappe
from frappe.utils import nowdate, add_days

def on_sales_invoice_submit(doc, method):
    """Trigger when sales invoice is submitted"""
    try:
        # Update forecast accuracy if we have predictions for this period
        for item in doc.items:
            update_forecast_accuracy(item.item_code, doc.customer, doc.posting_date, item.qty)
            
        # Check if we need to retrain models
        check_retrain_trigger()
        
    except Exception as e:
        frappe.log_error(f"Error in sales invoice trigger: {str(e)}", "AI Forecasting Trigger")

def on_sales_invoice_cancel(doc, method):
    """Trigger when sales invoice is cancelled"""
    try:
        # Remove the accuracy data for cancelled invoices
        for item in doc.items:
            remove_forecast_accuracy(item.item_code, doc.customer, doc.posting_date)
    except Exception as e:
        frappe.log_error(f"Error in sales invoice cancel trigger: {str(e)}", "AI Forecasting Trigger")

def on_sales_order_submit(doc, method):
    """Trigger when sales order is submitted"""
    try:
        # If this is an AI-generated order, mark it as processed
        if hasattr(doc, 'custom_ai_generated') and doc.custom_ai_generated:
            update_forecast_processing_status(doc)
    except Exception as e:
        frappe.log_error(f"Error in sales order trigger: {str(e)}", "AI Forecasting Trigger")

def update_forecast_accuracy(item_code, customer, posting_date, actual_qty):
    """Update forecast accuracy based on actual sales"""
    try:
        # Find corresponding forecasts
        forecasts = frappe.db.get_all("AI Sales Forecast", 
                                     filters={
                                         "item_code": item_code,
                                         "customer": customer,
                                         "forecast_date": posting_date
                                     },
                                     fields=["name", "predicted_qty", "confidence_score"])
        
        for forecast in forecasts:
            # Calculate accuracy
            predicted = forecast['predicted_qty'] or 0
            accuracy = 100 - (abs(predicted - actual_qty) / max(predicted, actual_qty, 1) * 100)
            
            # Update forecast record with notes about actual sales
            notes = f"Actual: {actual_qty}, Predicted: {predicted}, Accuracy: {accuracy:.1f}%"
            frappe.db.set_value("AI Sales Forecast", forecast['name'], {
                "notes": notes
            })
            
            # Log the accuracy for monitoring
            frappe.log_error(f"Forecast accuracy: {accuracy:.1f}% for {item_code}", "AI Forecast Accuracy")
            
    except Exception as e:
        frappe.log_error(f"Error updating forecast accuracy: {str(e)}", "AI Forecasting Trigger")

def remove_forecast_accuracy(item_code, customer, posting_date):
    """Remove accuracy data when invoice is cancelled"""
    try:
        forecasts = frappe.db.get_all("AI Sales Forecast", 
                                     filters={
                                         "item_code": item_code,
                                         "customer": customer,
                                         "forecast_date": posting_date
                                     })
        
        for forecast in forecasts:
            # Clear notes when invoice is cancelled
            frappe.db.set_value("AI Sales Forecast", forecast['name'], {
                "notes": ""
            })
            
    except Exception as e:
        frappe.log_error(f"Error removing forecast accuracy: {str(e)}", "AI Forecasting Trigger")

def update_forecast_processing_status(sales_order):
    """Mark forecasts as processed when SO is created"""
    try:
        for item in sales_order.items:
            # Add note that this forecast led to a sales order
            forecasts = frappe.db.get_all("AI Sales Forecast",
                                         filters={
                                             "item_code": item.item_code,
                                             "customer": sales_order.customer,
                                             "forecast_date": item.delivery_date
                                         })
            
            for forecast in forecasts:
                current_notes = frappe.db.get_value("AI Sales Forecast", forecast['name'], "notes") or ""
                new_note = f"Sales Order {sales_order.name} created"
                updated_notes = f"{current_notes}\n{new_note}" if current_notes else new_note
                
                frappe.db.set_value("AI Sales Forecast", forecast['name'], {
                    "notes": updated_notes
                })
                
    except Exception as e:
        frappe.log_error(f"Error updating forecast processing status: {str(e)}", "AI Forecasting Trigger")

def check_retrain_trigger():
    """Check if models need retraining based on activity"""
    try:
        config = frappe.get_single("AI Sales Dashboard")
        
        # Count total forecasts in last 30 days
        total_forecasts = frappe.db.sql("""
            SELECT COUNT(*) as total
            FROM `tabAI Sales Forecast`
            WHERE forecast_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        
        if total_forecasts and total_forecasts[0][0] > 100:  # If many forecasts, schedule retraining
            # Schedule retraining
            frappe.enqueue('ai_inventory.forecasting.ai_sales_forecast.train_models',
                         queue='long',
                         timeout=1800)
            frappe.log_error("Scheduled model retraining due to high forecast activity", "AI Forecasting")
            
    except Exception as e:
        frappe.log_error(f"Error checking retrain trigger: {str(e)}", "AI Forecasting Trigger")

