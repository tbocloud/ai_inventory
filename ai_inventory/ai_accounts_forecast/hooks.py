"""
Financial Forecasting Hooks Handler
Handles ERPNext document events for financial forecasting integration
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def validate_financial_forecast(doc, method):
    """Validate financial forecast before saving"""
    try:
        # Additional validation logic
        if doc.predicted_amount and doc.predicted_amount < 0:
            if doc.forecast_type in ["Revenue", "Income"]:
                frappe.msgprint(_("Warning: Negative predicted amount for revenue forecast"), alert=True)
        
        # Check for duplicate forecasts
        check_duplicate_forecasts(doc)
        
        # Validate model parameters
        validate_model_parameters(doc)
        
    except Exception as e:
        frappe.log_error(f"Financial forecast validation error: {str(e)}", "AI Financial Forecast Validation")

def on_financial_forecast_save(doc, method):
    """Actions when financial forecast is saved"""
    try:
        # Update related inventory forecasts if integration is enabled
        if doc.inventory_sync_enabled:
            sync_with_inventory_forecast(doc)
        
        # Update forecast summary cache
        update_forecast_cache(doc.company)
        
        # Trigger real-time notifications if needed
        if doc.forecast_alert:
            send_real_time_alert(doc)
        
        # Trigger automatic sync to specific forecast types (for updates)
        try:
            from ai_inventory.forecasting.sync_manager import sync_single_forecast
            frappe.enqueue(
                sync_single_forecast,
                financial_forecast_id=doc.name,
                queue="short",
                timeout=300,
                is_async=True
            )
        except Exception as sync_error:
            frappe.log_error(f"Auto-sync update enqueue error for {doc.name}: {str(sync_error)}", "AI Financial Forecast Auto-Sync Update")
            
    except Exception as e:
        frappe.log_error(f"Financial forecast save error: {str(e)}", "AI Financial Forecast Save")

def after_financial_forecast_insert(doc, method):
    """Actions after financial forecast is inserted"""
    try:
        # Log forecast creation
        log_forecast_activity(doc, "created")
        
        # Check if this is the first forecast for the account
        existing_count = frappe.db.count("AI Financial Forecast", {
            "account": doc.account,
            "company": doc.company,
            "name": ["!=", doc.name]
        })
        
        if existing_count == 0:
            # First forecast for this account - send welcome notification
            send_first_forecast_notification(doc)
        
        # Update dashboard cache
        frappe.cache().delete_key(f"financial_dashboard_{doc.company}")
        
        # Trigger automatic sync to specific forecast types
        try:
            from ai_inventory.forecasting.sync_manager import sync_single_forecast
            frappe.enqueue(
                sync_single_forecast,
                financial_forecast_id=doc.name,
                queue="short",
                timeout=300,
                is_async=True
            )
        except Exception as sync_error:
            frappe.log_error(f"Auto-sync enqueue error for {doc.name}: {str(sync_error)}", "AI Financial Forecast Auto-Sync")
        
    except Exception as e:
        frappe.log_error(f"Financial forecast insert error: {str(e)}", "AI Financial Forecast Insert")

def on_journal_entry_submit(doc, method):
    """Handle journal entry submission for financial forecasting"""
    try:
        # Extract relevant financial data
        for entry in doc.accounts:
            if entry.account and entry.debit_in_account_currency or entry.credit_in_account_currency:
                # Trigger forecast update for affected account
                enqueue_forecast_update(doc.company, entry.account, "Journal Entry")
                
    except Exception as e:
        frappe.log_error(f"Journal entry forecast trigger error: {str(e)}", "Financial Forecast Trigger")

def on_payment_entry_submit(doc, method):
    """Handle payment entry submission for financial forecasting"""
    try:
        accounts_to_update = []
        
        if doc.paid_from:
            accounts_to_update.append(doc.paid_from)
        if doc.paid_to:
            accounts_to_update.append(doc.paid_to)
        
        # Enqueue forecast updates for affected accounts
        for account in accounts_to_update:
            enqueue_forecast_update(doc.company, account, "Payment Entry")
            
    except Exception as e:
        frappe.log_error(f"Payment entry forecast trigger error: {str(e)}", "Financial Forecast Trigger")

def on_gl_entry_submit(doc, method):
    """Handle GL entry submission for financial forecasting"""
    try:
        # Only update for significant amounts (configurable threshold)
        amount_threshold = frappe.db.get_single_value("AI Financial Settings", "forecast_trigger_threshold") or 1000
        
        if doc.debit > amount_threshold or doc.credit > amount_threshold:
            enqueue_forecast_update(doc.company, doc.account, "GL Entry")
            
    except Exception as e:
        frappe.log_error(f"GL entry forecast trigger error: {str(e)}", "Financial Forecast Trigger")

def on_account_created(doc, method):
    """Handle new account creation"""
    try:
        # Check if auto-forecasting is enabled for new accounts
        auto_forecast_enabled = frappe.db.get_single_value("AI Financial Settings", "auto_forecast_new_accounts")
        
        if auto_forecast_enabled and not doc.is_group:
            # Create initial forecast for the new account
            priority_types = ["Asset", "Income", "Expense"]
            
            if doc.account_type in priority_types:
                enqueue_initial_forecast_creation(doc.company, doc.name, doc.account_type)
                
    except Exception as e:
        frappe.log_error(f"New account forecast creation error: {str(e)}", "Financial Forecast Account Creation")

# Utility Functions

def check_duplicate_forecasts(doc):
    """Check for duplicate forecasts"""
    existing = frappe.get_all("AI Financial Forecast", 
                             filters={
                                 "company": doc.company,
                                 "account": doc.account,
                                 "forecast_type": doc.forecast_type,
                                 "forecast_start_date": doc.forecast_start_date,
                                 "name": ["!=", doc.name]
                             },
                             limit=1)
    
    if existing:
        frappe.msgprint(
            _("Similar forecast already exists for this account and period. Consider updating the existing forecast instead."), 
            alert=True
        )

def validate_model_parameters(doc):
    """Validate model parameters"""
    if doc.prediction_model and doc.model_parameters:
        try:
            params = json.loads(doc.model_parameters)
            
            # Validate common parameters
            if "forecast_horizon" in params:
                if not isinstance(params["forecast_horizon"], int) or params["forecast_horizon"] <= 0:
                    frappe.throw(_("Invalid forecast horizon in model parameters"))
            
            if "confidence_interval" in params:
                interval = params["confidence_interval"]
                if not isinstance(interval, (int, float)) or not (0 < interval < 1):
                    frappe.throw(_("Confidence interval must be between 0 and 1"))
                    
        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON format in model parameters"))

def sync_with_inventory_forecast(doc):
    """Sync financial forecast with inventory forecasts"""
    try:
        # Get related inventory forecasts
        inventory_forecasts = frappe.get_all("AI Inventory Forecast",
                                           filters={"company": doc.company},
                                           fields=["name", "item_code", "predicted_consumption", "valuation_rate"])
        
        if inventory_forecasts:
            # Calculate inventory impact on financial forecast
            inventory_impact = calculate_inventory_financial_impact(inventory_forecasts, doc.forecast_type)
            
            # Update financial forecast with inventory insights
            if inventory_impact:
                update_forecast_with_inventory_data(doc, inventory_impact)
                
    except Exception as e:
        frappe.log_error(f"Inventory sync error: {str(e)}", "Financial Forecast Inventory Sync")

def calculate_inventory_financial_impact(inventory_forecasts, forecast_type):
    """Calculate financial impact from inventory forecasts"""
    impact = {"total_impact": 0, "details": []}
    
    for inv in inventory_forecasts:
        if forecast_type == "Cash Flow":
            # Calculate cash flow impact from inventory purchases
            purchase_impact = (inv.predicted_consumption or 0) * (inv.valuation_rate or 0)
            impact["total_impact"] += purchase_impact
            impact["details"].append({
                "item": inv.item_code,
                "impact": purchase_impact,
                "type": "purchase_cashflow"
            })
        
        elif forecast_type == "Revenue":
            # Estimate revenue impact (would need selling price)
            # For now, use a simple multiplier
            revenue_impact = (inv.predicted_consumption or 0) * (inv.valuation_rate or 0) * 1.3  # 30% markup assumption
            impact["total_impact"] += revenue_impact
            impact["details"].append({
                "item": inv.item_code,
                "impact": revenue_impact,
                "type": "sales_revenue"
            })
    
    return impact if impact["total_impact"] > 0 else None

def update_forecast_with_inventory_data(doc, inventory_impact):
    """Update forecast document with inventory impact data"""
    try:
        # Update predicted amount if significant impact
        if inventory_impact["total_impact"] > abs(doc.predicted_amount or 0) * 0.1:  # 10% threshold
            adjustment_factor = inventory_impact["total_impact"] / max(abs(doc.predicted_amount or 1), 1)
            
            # Store inventory impact in forecast details
            forecast_details = {}
            if doc.forecast_details:
                try:
                    forecast_details = json.loads(doc.forecast_details)
                except:
                    pass
            
            forecast_details["inventory_impact"] = inventory_impact
            doc.forecast_details = json.dumps(forecast_details)
            
            # Update sync status
            doc.sync_status = "Completed"
            doc.last_sync_date = frappe.utils.now()
            
    except Exception as e:
        frappe.log_error(f"Forecast update error: {str(e)}", "Financial Forecast Update")

def enqueue_forecast_update(company, account, trigger_source):
    """Enqueue forecast update job"""
    try:
        # Check if update is already queued
        queue_key = f"forecast_update_{company}_{account}"
        
        if not frappe.cache().get(queue_key):
            # Set cache to prevent duplicate jobs
            frappe.cache().set(queue_key, True, expires_in_sec=300)  # 5 minutes
            
            # Enqueue the update job
            frappe.enqueue(
                'ai_inventory.ai_accounts_forecast.jobs.update_account_forecast',
                company=company,
                account=account,
                trigger_source=trigger_source,
                queue='default',
                timeout=300
            )
            
    except Exception as e:
        frappe.log_error(f"Forecast update enqueue error: {str(e)}", "Financial Forecast Queue")

def enqueue_initial_forecast_creation(company, account, account_type):
    """Enqueue initial forecast creation for new account"""
    try:
        # Determine appropriate forecast types based on account type
        forecast_types = get_forecast_types_for_account(account_type)
        
        for forecast_type in forecast_types:
            frappe.enqueue(
                'ai_inventory.ai_accounts_forecast.jobs.create_initial_forecast',
                company=company,
                account=account,
                forecast_type=forecast_type,
                queue='default',
                timeout=180,
                is_async=True
            )
            
    except Exception as e:
        frappe.log_error(f"Initial forecast creation enqueue error: {str(e)}", "Financial Forecast Initial Creation")

def get_forecast_types_for_account(account_type):
    """Get appropriate forecast types for account type"""
    type_mapping = {
        "Asset": ["Cash Flow", "Balance Sheet"],
        "Income": ["Revenue", "Cash Flow"],
        "Expense": ["Expense", "Cash Flow"],
        "Liability": ["Cash Flow", "Balance Sheet"],
        "Equity": ["Balance Sheet"]
    }
    
    return type_mapping.get(account_type, ["Cash Flow"])

def update_forecast_cache(company):
    """Update forecast summary cache"""
    try:
        # Clear existing cache
        cache_keys = [
            f"financial_dashboard_{company}",
            f"forecast_summary_{company}",
            f"forecast_performance_{company}"
        ]
        
        for key in cache_keys:
            frappe.cache().delete_key(key)
            
    except Exception as e:
        frappe.log_error(f"Cache update error: {str(e)}", "Financial Forecast Cache")

def send_real_time_alert(doc):
    """Send real-time alert for forecast"""
    try:
        alert_data = {
            "type": "forecast_alert",
            "forecast_id": doc.name,
            "account": doc.account,
            "predicted_amount": doc.predicted_amount,
            "confidence_score": doc.confidence_score,
            "risk_category": doc.risk_category,
            "message": f"Forecast alert for {doc.account}: {doc.risk_category} risk detected"
        }
        
        # Send to relevant users
        recipients = get_alert_recipients(doc.company)
        
        for user in recipients:
            frappe.publish_realtime(
                "forecast_alert",
                alert_data,
                user=user
            )
            
    except Exception as e:
        frappe.log_error(f"Real-time alert error: {str(e)}", "Financial Forecast Alert")

def send_first_forecast_notification(doc):
    """Send notification for first forecast on an account"""
    try:
        message = f"""
        <h4>New Financial Forecast Created</h4>
        <p>First forecast has been created for account: <strong>{doc.account}</strong></p>
        <ul>
            <li>Forecast Type: {doc.forecast_type}</li>
            <li>Predicted Amount: {frappe.utils.fmt_money(doc.predicted_amount or 0)}</li>
            <li>Confidence Score: {doc.confidence_score}%</li>
        </ul>
        <p>You can view and manage this forecast in the AI Financial Forecast module.</p>
        """
        
        recipients = get_alert_recipients(doc.company)
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=f"New Financial Forecast - {doc.account}",
                message=message,
                reference_doctype=doc.doctype,
                reference_name=doc.name
            )
            
    except Exception as e:
        frappe.log_error(f"First forecast notification error: {str(e)}", "Financial Forecast Notification")

def get_alert_recipients(company):
    """Get list of users to receive forecast alerts"""
    try:
        # Get users with AI Inventory Manager role
        managers = frappe.get_all("Has Role",
                                filters={"role": "AI Inventory Manager"},
                                fields=["parent"])
        
        recipients = [m.parent for m in managers]
        
        # Add users with Accounts Manager role
        accounts_managers = frappe.get_all("Has Role",
                                         filters={"role": "Accounts Manager"},
                                         fields=["parent"])
        
        recipients.extend([am.parent for am in accounts_managers])
        
        # Map to emails, remove duplicates, and validate
        valid_emails = []
        for r in set(recipients):
            email = None
            if isinstance(r, str) and '@' in r:
                email = r
            else:
                if frappe.db.exists("User", r) and frappe.db.get_value("User", r, "enabled"):
                    email = frappe.db.get_value("User", r, "email")
            if email and frappe.utils.validate_email_address(email, throw=False):
                valid_emails.append(email)
        
        return list(set(valid_emails))
        
    except Exception as e:
        frappe.log_error(f"Get alert recipients error: {str(e)}", "Financial Forecast Recipients")
        return []

def log_forecast_activity(doc, activity):
    """Log forecast activity for audit trail"""
    try:
        activity_log = {
            "doctype": "AI Forecast Activity Log",
            "forecast_id": doc.name,
            "account": doc.account,
            "company": doc.company,
            "activity": activity,
            "forecast_type": doc.forecast_type,
            "predicted_amount": doc.predicted_amount,
            "confidence_score": doc.confidence_score,
            "user": frappe.session.user,
            "timestamp": frappe.utils.now()
        }
        
        # Create log entry (if DocType exists)
        if frappe.db.exists("DocType", "AI Forecast Activity Log"):
            log_doc = frappe.get_doc(activity_log)
            log_doc.insert(ignore_permissions=True)
        
    except Exception as e:
        # Don't break the main process for logging errors
        frappe.log_error(f"Activity logging error: {str(e)}", "Financial Forecast Activity Log")

# Background Jobs

def update_account_forecast(company, account, trigger_source):
    """Background job to update account forecast"""
    try:
        from ai_inventory.ai_accounts_forecast.models.account_forecast import create_financial_forecast
        
        # Create or update cash flow forecast (most common)
        result = create_financial_forecast(
            company=company,
            account=account,
            forecast_type="Cash Flow",
            forecast_period_days=30
        )
        
        frappe.logger().info(f"Updated forecast for {account} triggered by {trigger_source}")
        
    except Exception as e:
        frappe.log_error(f"Background forecast update error: {str(e)}", "Financial Forecast Background Update")
    finally:
        # Clear queue cache
        queue_key = f"forecast_update_{company}_{account}"
        frappe.cache().delete_key(queue_key)

def create_initial_forecast(company, account, forecast_type):
    """Background job to create initial forecast for new account"""
    try:
        from ai_inventory.ai_accounts_forecast.models.account_forecast import create_financial_forecast
        
        result = create_financial_forecast(
            company=company,
            account=account,
            forecast_type=forecast_type,
            forecast_period_days=90  # 3-month initial forecast
        )
        
        frappe.logger().info(f"Created initial {forecast_type} forecast for new account {account}")
        
    except Exception as e:
        frappe.log_error(f"Initial forecast creation error: {str(e)}", "Financial Forecast Initial Creation")
