"""
AI Financial Forecast Integration & Sync Manager
Handles all synchronization and integration operations
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time

class AIFinancialForecastSyncManager:
    """Manages all sync operations for AI Financial Forecasts"""
    
    def __init__(self, forecast_doc):
        self.forecast = forecast_doc
        self.sync_results = {}
        self.errors = []
        
    def execute_full_sync(self):
        """Execute comprehensive sync across all systems"""
        try:
            # Update sync status to "Syncing"
            self.update_sync_status("Syncing", "Starting comprehensive sync")
            
            sync_operations = [
                ("inventory_sync", self.sync_to_inventory_forecast),
                ("revenue_sync", self.sync_to_revenue_forecast),
                ("cashflow_sync", self.sync_to_cashflow_forecast),
                ("expense_sync", self.sync_to_expense_forecast),
                ("accuracy_tracking", self.sync_to_accuracy_tracking),
                ("external_systems", self.sync_to_external_systems)
            ]
            
            total_operations = len(sync_operations)
            completed = 0
            
            for operation_name, operation_func in sync_operations:
                try:
                    result = operation_func()
                    self.sync_results[operation_name] = result
                    if result.get("success"):
                        completed += 1
                except Exception as e:
                    self.errors.append(f"{operation_name}: {str(e)}")
                    self.sync_results[operation_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Determine final status
            if completed == total_operations:
                self.update_sync_status("Completed", f"All {total_operations} operations successful")
            elif completed > 0:
                self.update_sync_status("Completed", f"{completed}/{total_operations} operations successful")
            else:
                self.update_sync_status("Failed", f"All operations failed: {'; '.join(self.errors[:3])}")
            
            return {
                "success": completed > 0,
                "completed_operations": completed,
                "total_operations": total_operations,
                "sync_results": self.sync_results,
                "errors": self.errors
            }
            
        except Exception as e:
            self.update_sync_status("Failed", f"Sync manager error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def sync_to_inventory_forecast(self):
        """Sync to AI Inventory Forecast"""
        try:
            if not self.forecast.inventory_sync_enabled:
                return {"success": True, "message": "Inventory sync disabled", "skipped": True}
            
            # Find related inventory items based on account
            inventory_items = self.get_related_inventory_items()
            
            if not inventory_items:
                return {"success": True, "message": "No related inventory items found", "skipped": True}
            
            synced_count = 0
            
            for item in inventory_items:
                try:
                    # Check if inventory forecast exists
                    existing_forecast = frappe.get_all("AI Inventory Forecast",
                                                     filters={
                                                         "item_code": item.item_code,
                                                         "company": self.forecast.company,
                                                         "forecast_date": self.forecast.forecast_start_date
                                                     },
                                                     limit=1)
                    
                    if existing_forecast:
                        # Update existing forecast
                        inv_doc = frappe.get_doc("AI Inventory Forecast", existing_forecast[0].name)
                        
                        # Update existing fields that we know exist
                        if hasattr(inv_doc, 'confidence_score'):
                            inv_doc.confidence_score = self.forecast.confidence_score
                        
                        # Add comment about the financial forecast relationship
                        inv_doc.add_comment("Comment", f"Synced from Financial Forecast: {self.forecast.name}")
                        inv_doc.save(ignore_permissions=True)
                        synced_count += 1
                    else:
                        # Create new inventory forecast if financial impact is significant
                        if abs(self.forecast.predicted_amount) > 10000:  # Threshold for significant impact
                            # Get the actual field list for AI Inventory Forecast
                            meta = frappe.get_meta("AI Inventory Forecast")
                            
                            inv_doc_data = {
                                "doctype": "AI Inventory Forecast",
                                "item_code": item.item_code,
                                "company": self.forecast.company,
                            }
                            
                            # Only add fields that exist in the DocType
                            if any(field.fieldname == 'confidence_score' for field in meta.fields):
                                inv_doc_data["confidence_score"] = self.forecast.confidence_score
                            
                            inv_doc = frappe.get_doc(inv_doc_data)
                            inv_doc.flags.ignore_permissions = True
                            inv_doc.insert()
                            synced_count += 1
                
                except Exception as item_error:
                    frappe.log_error(f"Inventory sync error for {item.item_code}: {str(item_error)}")
                    continue
            
            # Update the related inventory forecast field
            if synced_count > 0:
                self.forecast.related_inventory_forecast = f"Synced to {synced_count} inventory forecasts"
                self.forecast.save(ignore_permissions=True)
            
            return {
                "success": True,
                "synced_items": synced_count,
                "message": f"Synced to {synced_count} inventory forecasts"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_revenue_forecast(self):
        """Sync to specialized Revenue Forecast DocType"""
        try:
            if self.forecast.forecast_type != "Revenue":
                return {"success": True, "message": "Not a revenue forecast", "skipped": True}
            
            # Check if revenue forecast exists
            existing = frappe.get_all("AI Revenue Forecast",
                                    filters={
                                        "company": self.forecast.company,
                                        "forecast_period": self.forecast.forecast_start_date,
                                        "account": self.forecast.account
                                    },
                                    limit=1)
            
            revenue_data = {
                "company": self.forecast.company,
                "forecast_period": self.forecast.forecast_start_date,
                "account": self.forecast.account,
                "predicted_revenue": self.forecast.predicted_amount,
                "confidence_score": self.forecast.confidence_score,
                "model_used": self.forecast.prediction_model,
                "last_sync_date": frappe.utils.now(),
                "source_forecast": self.forecast.name,
                "currency": getattr(self.forecast, 'currency', 'INR')
            }
            
            # Parse additional revenue details from forecast_details
            if self.forecast.forecast_details:
                try:
                    details = json.loads(self.forecast.forecast_details)
                    revenue_breakdown = details.get("revenue_breakdown", {})
                    
                    revenue_data.update({
                        "recurring_revenue": revenue_breakdown.get("recurring_revenue", 0),
                        "one_time_revenue": revenue_breakdown.get("one_time_revenue", 0),
                        "growth_rate": revenue_breakdown.get("growth_rate", 0),
                        "seasonal_factor": revenue_breakdown.get("seasonal_factor", 1.0),
                        "market_trend_impact": revenue_breakdown.get("market_trend_impact", 0)
                    })
                except json.JSONDecodeError:
                    pass
            
            if existing:
                # Update existing
                rev_doc = frappe.get_doc("AI Revenue Forecast", existing[0].name)
                for key, value in revenue_data.items():
                    setattr(rev_doc, key, value)
                rev_doc.save(ignore_permissions=True)
                action = "Updated"
            else:
                # Create new
                revenue_data["doctype"] = "AI Revenue Forecast"
                rev_doc = frappe.get_doc(revenue_data)
                rev_doc.flags.ignore_permissions = True
                rev_doc.insert()
                action = "Created"
            
            return {
                "success": True,
                "action": action,
                "revenue_forecast": rev_doc.name,
                "message": f"{action} revenue forecast {rev_doc.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_cashflow_forecast(self):
        """Sync to specialized Cashflow Forecast DocType"""
        try:
            if self.forecast.forecast_type != "Cash Flow":
                return {"success": True, "message": "Not a cashflow forecast", "skipped": True}
            
            # Similar implementation to revenue but for cashflow
            existing = frappe.get_all("AI Cashflow Forecast",
                                    filters={
                                        "company": self.forecast.company,
                                        "forecast_date": self.forecast.forecast_start_date,
                                        "account": self.forecast.account
                                    },
                                    limit=1)
            
            cashflow_data = {
                "company": self.forecast.company,
                "forecast_date": self.forecast.forecast_start_date,
                "account": self.forecast.account,
                "net_cash_flow": self.forecast.predicted_amount,
                "confidence_score": self.forecast.confidence_score,
                "model_used": self.forecast.prediction_model,
                "last_sync_date": frappe.utils.now(),
                "source_forecast": self.forecast.name,
                "currency": getattr(self.forecast, 'currency', 'INR')
            }
            
            # Parse cashflow details
            if self.forecast.forecast_details:
                try:
                    details = json.loads(self.forecast.forecast_details)
                    cashflow_breakdown = details.get("cashflow_breakdown", {})
                    
                    cashflow_data.update({
                        "predicted_inflows": cashflow_breakdown.get("total_inflows", 0),
                        "predicted_outflows": cashflow_breakdown.get("total_outflows", 0),
                        "liquidity_ratio": cashflow_breakdown.get("liquidity_ratio", 100),
                        "cash_conversion_cycle": cashflow_breakdown.get("cash_conversion_cycle", 0)
                    })
                except json.JSONDecodeError:
                    pass
            
            if existing:
                cf_doc = frappe.get_doc("AI Cashflow Forecast", existing[0].name)
                for key, value in cashflow_data.items():
                    setattr(cf_doc, key, value)
                cf_doc.save(ignore_permissions=True)
                action = "Updated"
            else:
                cashflow_data["doctype"] = "AI Cashflow Forecast"
                cf_doc = frappe.get_doc(cashflow_data)
                cf_doc.flags.ignore_permissions = True
                cf_doc.insert()
                action = "Created"
            
            return {
                "success": True,
                "action": action,
                "cashflow_forecast": cf_doc.name,
                "message": f"{action} cashflow forecast {cf_doc.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_expense_forecast(self):
        """Sync to specialized Expense Forecast DocType"""
        try:
            if self.forecast.forecast_type != "Expense":
                return {"success": True, "message": "Not an expense forecast", "skipped": True}
            
            # Implementation similar to revenue/cashflow
            existing = frappe.get_all("AI Expense Forecast",
                                    filters={
                                        "company": self.forecast.company,
                                        "forecast_period": self.forecast.forecast_start_date,
                                        "expense_account": self.forecast.account
                                    },
                                    limit=1)
            
            expense_data = {
                "company": self.forecast.company,
                "forecast_period": self.forecast.forecast_start_date,
                "expense_account": self.forecast.account,
                "predicted_expense": self.forecast.predicted_amount,
                "confidence_score": self.forecast.confidence_score,
                "model_used": self.forecast.prediction_model,
                "last_sync_date": frappe.utils.now(),
                "source_forecast": self.forecast.name,
                "currency": getattr(self.forecast, 'currency', 'INR')
            }
            
            if existing:
                exp_doc = frappe.get_doc("AI Expense Forecast", existing[0].name)
                for key, value in expense_data.items():
                    setattr(exp_doc, key, value)
                exp_doc.save(ignore_permissions=True)
                action = "Updated"
            else:
                expense_data["doctype"] = "AI Expense Forecast"
                exp_doc = frappe.get_doc(expense_data)
                exp_doc.flags.ignore_permissions = True
                exp_doc.insert()
                action = "Created"
            
            return {
                "success": True,
                "action": action,
                "expense_forecast": exp_doc.name,
                "message": f"{action} expense forecast {exp_doc.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_accuracy_tracking(self):
        """Sync to AI Forecast Accuracy tracking"""
        try:
            # Check if accuracy record exists
            existing = frappe.get_all("AI Forecast Accuracy",
                                    filters={"forecast_reference": self.forecast.name},
                                    limit=1)
            
            accuracy_data = {
                "forecast_reference": self.forecast.name,
                "forecast_type": self.forecast.forecast_type,
                "company": self.forecast.company,
                "account": self.forecast.account,
                "predicted_value": self.forecast.predicted_amount,
                "prediction_date": self.forecast.forecast_start_date,
                "model_used": self.forecast.prediction_model,
                "confidence_score": self.forecast.confidence_score,
                "currency": getattr(self.forecast, 'currency', 'INR'),
                "measurement_date": frappe.utils.now()
            }
            
            if existing:
                acc_doc = frappe.get_doc("AI Forecast Accuracy", existing[0].name)
                for key, value in accuracy_data.items():
                    setattr(acc_doc, key, value)
                acc_doc.save(ignore_permissions=True)
                action = "Updated"
            else:
                accuracy_data["doctype"] = "AI Forecast Accuracy"
                acc_doc = frappe.get_doc(accuracy_data)
                acc_doc.flags.ignore_permissions = True
                acc_doc.insert()
                action = "Created"
            
            return {
                "success": True,
                "action": action,
                "accuracy_record": acc_doc.name,
                "message": f"{action} accuracy tracking record"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_external_systems(self):
        """Sync to external financial systems"""
        try:
            # Get integration settings
            integration_settings = frappe.get_single("AI Financial Integration Settings")
            
            if not integration_settings or not integration_settings.enabled:
                return {"success": True, "message": "External integration disabled", "skipped": True}
            
            sync_results = []
            
            # Sync to external ERP systems
            if integration_settings.erp_integration_enabled:
                erp_result = self.sync_to_external_erp()
                sync_results.append(("ERP", erp_result))
            
            # Sync to banking systems
            if integration_settings.banking_integration_enabled:
                bank_result = self.sync_to_banking_system()
                sync_results.append(("Banking", bank_result))
            
            # Sync to business intelligence tools
            if integration_settings.bi_integration_enabled:
                bi_result = self.sync_to_bi_tools()
                sync_results.append(("BI Tools", bi_result))
            
            successful_syncs = [r for r in sync_results if r[1].get("success")]
            
            return {
                "success": len(successful_syncs) > 0,
                "external_syncs": len(successful_syncs),
                "total_attempts": len(sync_results),
                "results": sync_results,
                "message": f"Synced to {len(successful_syncs)}/{len(sync_results)} external systems"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_external_erp(self):
        """Sync to external ERP systems"""
        try:
            # Placeholder for ERP integration
            # This would integrate with SAP, Oracle, NetSuite, etc.
            
            return {
                "success": True,
                "message": "ERP sync placeholder - ready for implementation",
                "systems_synced": 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_banking_system(self):
        """Sync to banking and financial institutions"""
        try:
            # Placeholder for banking API integration
            # This would integrate with Plaid, Open Banking, bank APIs
            
            return {
                "success": True,
                "message": "Banking sync placeholder - ready for implementation",
                "accounts_synced": 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_bi_tools(self):
        """Sync to Business Intelligence tools"""
        try:
            # Placeholder for BI integration
            # This would integrate with Power BI, Tableau, Looker, etc.
            
            return {
                "success": True,
                "message": "BI tools sync placeholder - ready for implementation",
                "dashboards_updated": 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_related_inventory_items(self):
        """Get inventory items related to this financial account"""
        try:
            # Find items based on account relationships
            items = frappe.db.sql("""
                SELECT DISTINCT i.item_code, i.item_name
                FROM `tabItem` i
                LEFT JOIN `tabStock Ledger Entry` sle ON sle.item_code = i.item_code
                LEFT JOIN `tabGL Entry` gle ON gle.voucher_no = sle.voucher_no
                WHERE gle.account = %s
                AND i.disabled = 0
                LIMIT 50
            """, (self.forecast.account,), as_dict=True)
            
            return items
            
        except Exception as e:
            frappe.log_error(f"Error finding related inventory items: {str(e)}")
            return []
    
    def update_sync_status(self, status, message=""):
        """Update the sync status of the forecast"""
        try:
            frappe.db.set_value("AI Financial Forecast", self.forecast.name, {
                "sync_status": status,
                "last_sync_date": frappe.utils.now()
            })
            
            if message:
                # Log sync status change
                self.log_sync_event(status, message)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error updating sync status: {str(e)}")
    
    def log_sync_event(self, status, message):
        """Log sync events for tracking"""
        try:
            sync_log = frappe.get_doc({
                "doctype": "AI Forecast Sync Log",
                "forecast_reference": self.forecast.name,
                "sync_status": status,
                "sync_message": message,
                "sync_timestamp": frappe.utils.now(),
                "sync_duration": 0  # Will be calculated based on start/end times
            })
            sync_log.flags.ignore_permissions = True
            sync_log.insert()
            
        except Exception as e:
            frappe.log_error(f"Error logging sync event: {str(e)}")

# ============================================================================
# Utility Functions for Sync Management
# ============================================================================

@frappe.whitelist()
def trigger_manual_sync(forecast_name):
    """Manually trigger sync for a specific forecast"""
    try:
        forecast_doc = frappe.get_doc("AI Financial Forecast", forecast_name)
        sync_manager = AIFinancialForecastSyncManager(forecast_doc)
        
        result = sync_manager.execute_full_sync()
        
        return {
            "success": True,
            "message": "Manual sync completed",
            "sync_results": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_sync_status_dashboard(company=None):
    """Get sync status dashboard data"""
    try:
        filters = {}
        if company:
            filters["company"] = company
        
        # Get sync status summary
        sync_status_data = frappe.db.sql("""
            SELECT 
                sync_status,
                COUNT(*) as count,
                AVG(CASE WHEN sync_status = 'Completed' THEN 100
                         WHEN sync_status = 'Failed' THEN 0
                         ELSE 50 END) as success_rate
            FROM `tabAI Financial Forecast`
            WHERE company = %(company)s OR %(company)s IS NULL
            GROUP BY sync_status
        """, {"company": company}, as_dict=True)
        
        # Recent sync activities
        recent_syncs = frappe.get_all("AI Forecast Sync Log",
                                    filters={"creation": [">=", frappe.utils.add_days(frappe.utils.now(), -7)]},
                                    fields=["forecast_reference", "sync_status", "sync_message", "creation"],
                                    order_by="creation desc",
                                    limit=10)
        
        return {
            "success": True,
            "sync_status_summary": sync_status_data,
            "recent_activities": recent_syncs,
            "total_forecasts": sum(s.count for s in sync_status_data),
            "overall_success_rate": sum(s.success_rate * s.count for s in sync_status_data) / sum(s.count for s in sync_status_data) if sync_status_data else 0
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def retry_failed_syncs(company=None):
    """Retry all failed sync operations"""
    try:
        filters = {"sync_status": "Failed"}
        if company:
            filters["company"] = company
        
        failed_forecasts = frappe.get_all("AI Financial Forecast",
                                        filters=filters,
                                        fields=["name"])
        
        retry_results = []
        
        for forecast in failed_forecasts:
            try:
                result = trigger_manual_sync(forecast.name)
                retry_results.append({
                    "forecast": forecast.name,
                    "success": result.get("success"),
                    "message": result.get("message", result.get("error"))
                })
            except Exception as e:
                retry_results.append({
                    "forecast": forecast.name,
                    "success": False,
                    "message": str(e)
                })
        
        successful_retries = len([r for r in retry_results if r["success"]])
        
        return {
            "success": True,
            "total_retried": len(retry_results),
            "successful_retries": successful_retries,
            "retry_results": retry_results,
            "message": f"Retried {len(retry_results)} forecasts, {successful_retries} successful"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
