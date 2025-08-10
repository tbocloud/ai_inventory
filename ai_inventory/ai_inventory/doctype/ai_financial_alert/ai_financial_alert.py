# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime


class AIFinancialAlert(Document):
    def validate(self):
        """Validate alert data"""
        # Validate related_forecast exists if provided
        if self.related_forecast:
            if not frappe.db.exists("AI Financial Forecast", self.related_forecast):
                # Clear the invalid reference instead of throwing error
                frappe.logger().warning(f"Related forecast {self.related_forecast} not found, clearing reference")
                self.related_forecast = None
    
    def before_save(self):
        """Validate and set defaults before saving"""
        if not self.alert_date:
            self.alert_date = frappe.utils.today()
        
        # Calculate variance percentage if values are available
        if self.actual_value and self.threshold_value:
            variance = abs(self.actual_value - self.threshold_value)
            if self.threshold_value != 0:
                self.variance_percentage = (variance / abs(self.threshold_value)) * 100
    
    def after_insert(self):
        """Send notifications after alert creation"""
        if self.priority in ["High", "Critical"]:
            self.send_alert_notification()
    
    def send_alert_notification(self):
        """Send notification for high priority alerts"""
        try:
            # Send email to assigned user if available
            if self.assigned_to:
                # Resolve assigned_to to a valid email address
                recipient = None
                if isinstance(self.assigned_to, str) and '@' in self.assigned_to:
                    recipient = self.assigned_to
                else:
                    recipient = frappe.db.get_value("User", self.assigned_to, "email")
                if recipient and frappe.utils.validate_email_address(recipient, throw=False):
                    frappe.sendmail(
                        recipients=[recipient],
                    subject=f"AI Financial Alert: {self.alert_title}",
                    message=f"""
                    <h3>Financial Alert Notification</h3>
                    <p><strong>Priority:</strong> {self.priority}</p>
                    <p><strong>Company:</strong> {self.company}</p>
                    <p><strong>Alert Type:</strong> {self.alert_type}</p>
                    <p><strong>Message:</strong> {self.alert_message}</p>
                    <p><strong>Date:</strong> {self.alert_date}</p>
                    {f'<p><strong>Threshold Value:</strong> ₹{self.threshold_value:,.2f}</p>' if self.threshold_value else ''}
                    {f'<p><strong>Actual Value:</strong> ₹{self.actual_value:,.2f}</p>' if self.actual_value else ''}
                    <p><strong>Recommended Action:</strong> {self.recommended_action or 'Review required'}</p>
                    """
                    )
        except Exception as e:
            frappe.log_error(title="Failed to send alert notification", message=frappe.get_traceback())


@frappe.whitelist()
def debug_forecast_references():
    """Debug forecast references to identify the source of the error"""
    try:
        # Get alerts with related_forecast
        alerts = frappe.get_all("AI Financial Alert",
            filters={"related_forecast": ["!=", ""]},
            fields=["name", "related_forecast", "alert_title", "creation"],
            limit=20
        )
        
        debug_info = []
        for alert in alerts:
            forecast_exists = frappe.db.exists("AI Financial Forecast", alert.related_forecast)
            debug_info.append({
                "alert_name": alert.name,
                "related_forecast": alert.related_forecast,
                "forecast_exists": forecast_exists,
                "alert_title": alert.alert_title,
                "creation": str(alert.creation)
            })
        
        return {
            "success": True,
            "debug_info": debug_info,
            "total_alerts_with_refs": len(alerts)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def cleanup_invalid_forecast_references():
    """Clean up invalid related_forecast references in alerts"""
    try:
        # Get all alerts with related_forecast values
        alerts_with_refs = frappe.get_all("AI Financial Alert", 
            filters={"related_forecast": ["!=", ""]},
            fields=["name", "related_forecast"]
        )
        
        cleaned_count = 0
        for alert in alerts_with_refs:
            if alert.related_forecast and not frappe.db.exists("AI Financial Forecast", alert.related_forecast):
                frappe.db.set_value("AI Financial Alert", alert.name, "related_forecast", None)
                cleaned_count += 1
                frappe.logger().info(f"Cleaned invalid reference {alert.related_forecast} from alert {alert.name}")
        
        frappe.db.commit()
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"Cleaned {cleaned_count} invalid forecast references"
        }
        
    except Exception as e:
        frappe.log_error(title="Cleanup invalid references failed", message=frappe.get_traceback())
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def create_financial_alert(alert_data):
    """Create a new financial alert record"""
    try:
        alert_doc = frappe.get_doc({
            "doctype": "AI Financial Alert",
            "company": alert_data.get("company"),
            "alert_type": alert_data.get("alert_type", "Financial Threshold"),
            "alert_title": alert_data.get("title"),
            "alert_message": alert_data.get("message"),
            "priority": alert_data.get("priority", "Medium"),
            "threshold_value": alert_data.get("threshold_value"),
            "actual_value": alert_data.get("actual_value"),
            "related_forecast": alert_data.get("related_forecast"),
            "forecast_type": alert_data.get("forecast_type"),
            "confidence_level": alert_data.get("confidence_level"),
            "recommended_action": alert_data.get("recommended_action"),
            "assigned_to": alert_data.get("assigned_to")
        })
        
        alert_doc.insert()
        frappe.db.commit()
        
        return {
            "success": True,
            "alert_id": alert_doc.name,
            "message": f"Alert {alert_doc.name} created successfully"
        }
        
    except Exception as e:
        frappe.log_error(title="Create financial alert error", message=frappe.get_traceback())
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_active_alerts(company=None, priority=None):
    """Get active financial alerts"""
    try:
        filters = {"status": ["in", ["Open", "Investigating"]]}
        
        if company:
            filters["company"] = company
        if priority:
            filters["priority"] = priority
            
        alerts = frappe.get_all(
            "AI Financial Alert",
            filters=filters,
            fields=[
                "name", "company", "alert_type", "alert_title", 
                "priority", "status", "alert_date", "assigned_to",
                "threshold_value", "actual_value", "variance_percentage"
            ],
            order_by="alert_date desc, priority desc"
        )
        
        return {"success": True, "alerts": alerts}
        
    except Exception as e:
        frappe.log_error(title="Get active alerts error", message=frappe.get_traceback())
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def resolve_alert(alert_id, action_taken=None, action_result=None):
    """Mark an alert as resolved"""
    try:
        alert_doc = frappe.get_doc("AI Financial Alert", alert_id)
        alert_doc.status = "Resolved"
        alert_doc.action_taken = action_taken or "Manual resolution"
        alert_doc.action_result = action_result
        alert_doc.action_date = frappe.utils.now()
        alert_doc.save()
        
        return {"success": True, "message": f"Alert {alert_id} resolved successfully"}
        
    except Exception as e:
        frappe.log_error(title="Resolve alert error", message=frappe.get_traceback())
        return {"success": False, "error": str(e)}
