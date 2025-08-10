# ============================================================================
# Forecast Synchronization System
# Comprehensive sync between AI Financial Forecast and specific forecast types
# ============================================================================

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

@frappe.whitelist()
def sync_all_forecasts(company=None, forecast_start_date=None):
    """
    Sync all forecast types with AI Financial Forecasts
    
    Args:
        company: Specific company to sync (optional)
        forecast_start_date: Specific start date to sync (optional)
    
    Returns:
        Dict with sync results
    """
    try:
        filters = {}
        if company:
            filters["company"] = company
        if forecast_start_date:
            filters["forecast_start_date"] = forecast_start_date
        
        # Get all AI Financial Forecasts to sync
        financial_forecasts = frappe.get_all("AI Financial Forecast",
                                           filters=filters,
                                           fields=["name", "company", "forecast_type", "forecast_start_date", 
                                                  "predicted_amount", "confidence_score", "prediction_model"],
                                           order_by="creation desc")
        
        sync_results = {
            "total_forecasts": len(financial_forecasts),
            "synced_successfully": 0,
            "sync_errors": 0,
            "results_by_type": {},
            "error_details": []
        }
        
        for forecast in financial_forecasts:
            try:
                result = sync_single_forecast(forecast.name)
                
                if result.get("success"):
                    sync_results["synced_successfully"] += 1
                    
                    # Track by type
                    ftype = forecast.forecast_type
                    if ftype not in sync_results["results_by_type"]:
                        sync_results["results_by_type"][ftype] = {"success": 0, "errors": 0}
                    sync_results["results_by_type"][ftype]["success"] += 1
                else:
                    sync_results["sync_errors"] += 1
                    error_msg = result.get("error", "Unknown error")
                    sync_results["error_details"].append({
                        "forecast_id": forecast.name,
                        "error": error_msg
                    })
                    frappe.log_error(f"Sync failed for forecast {forecast.name}: {error_msg}")
                    
                    # Track by type
                    ftype = forecast.forecast_type
                    if ftype not in sync_results["results_by_type"]:
                        sync_results["results_by_type"][ftype] = {"success": 0, "errors": 0}
                    sync_results["results_by_type"][ftype]["errors"] += 1
                    
            except Exception as e:
                sync_results["sync_errors"] += 1
                error_msg = f"Exception during sync: {str(e)}"
                sync_results["error_details"].append({
                    "forecast_id": forecast.name,
                    "error": error_msg
                })
                frappe.log_error(f"Sync exception for forecast {forecast.name}: {str(e)}")
        
        # Update sync log
        create_sync_log(sync_results)
        
        return {
            "success": True,
            "message": f"Sync completed. {sync_results['synced_successfully']}/{sync_results['total_forecasts']} forecasts synced successfully.",
            "results": sync_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def sync_single_forecast(financial_forecast_id):
    """
    Sync a single AI Financial Forecast to specific forecast types
    
    Args:
        financial_forecast_id: Name of the AI Financial Forecast document
    
    Returns:
        Dict with sync result
    """
    try:
        # Get the financial forecast
        forecast_doc = frappe.get_doc("AI Financial Forecast", financial_forecast_id)
        
        sync_result = {
            "success": True,
            "forecast_id": financial_forecast_id,
            "forecast_type": forecast_doc.forecast_type,
            "synced_to": [],
            "errors": []
        }
        
        # Sync based on forecast type
        if forecast_doc.forecast_type == "Cash Flow":
            try:
                result = sync_to_cashflow(forecast_doc)
                if result and result.get("success"):
                    sync_result["synced_to"].append("AI Cashflow Forecast")
                else:
                    error_msg = result.get("error", "Unknown cashflow sync error") if result else "Cashflow sync returned None"
                    sync_result["errors"].append(f"Cashflow sync: {error_msg}")
            except Exception as e:
                sync_result["errors"].append(f"Cashflow sync exception: {str(e)}")
        
        elif forecast_doc.forecast_type == "Revenue":
            try:
                result = sync_to_revenue(forecast_doc)
                if result and result.get("success"):
                    sync_result["synced_to"].append("AI Revenue Forecast")
                else:
                    error_msg = result.get("error", "Unknown revenue sync error") if result else "Revenue sync returned None"
                    sync_result["errors"].append(f"Revenue sync: {error_msg}")
            except Exception as e:
                sync_result["errors"].append(f"Revenue sync exception: {str(e)}")
        
        elif forecast_doc.forecast_type == "Expense":
            try:
                result = sync_to_expense(forecast_doc)
                if result and result.get("success"):
                    sync_result["synced_to"].append("AI Expense Forecast")
                else:
                    error_msg = result.get("error", "Unknown expense sync error") if result else "Expense sync returned None"
                    sync_result["errors"].append(f"Expense sync: {error_msg}")
            except Exception as e:
                sync_result["errors"].append(f"Expense sync exception: {str(e)}")
        
        # Always try to sync with inventory forecasts for financial impact analysis
        try:
            result = sync_to_inventory_forecast(forecast_doc)
            if result and result.get("success"):
                sync_result["synced_to"].append("AI Inventory Forecast")
                # Store inventory sync details for the frontend
                sync_result["inventory_forecast_details"] = {
                    "items_processed": result.get("items_processed", 0),
                    "synced_forecasts": result.get("synced_forecasts", []),
                    "inventory_forecast_id": result.get("inventory_forecast_id"),
                    "message": result.get("message", "")
                }
                # Update the related inventory forecast field
                if result.get("inventory_forecast_id"):
                    try:
                        # Get a fresh copy to avoid modification conflicts
                        fresh_doc = frappe.get_doc("AI Financial Forecast", forecast_doc.name)
                        fresh_doc.related_inventory_forecast = result.get("inventory_forecast_id")
                        fresh_doc.flags.ignore_permissions = True
                        fresh_doc.save()
                    except Exception as save_error:
                        # Log but don't fail the sync for this
                        frappe.log_error(f"Could not update related_inventory_forecast: {str(save_error)}", "Sync Warning")
            else:
                error_msg = result.get("error", "Unknown inventory sync error") if result else "Inventory sync returned None"
                sync_result["errors"].append(f"Inventory sync: {error_msg}")
        except Exception as e:
            sync_result["errors"].append(f"Inventory sync exception: {str(e)}")
        
        # Always try to create accuracy tracking
        try:
            accuracy_result = create_accuracy_tracking(forecast_doc)
            if accuracy_result and accuracy_result.get("success"):
                sync_result["synced_to"].append("AI Forecast Accuracy")
            else:
                error_msg = accuracy_result.get("error", "Unknown accuracy tracking error") if accuracy_result else "Accuracy tracking returned None"
                sync_result["errors"].append(f"Accuracy tracking: {error_msg}")
        except Exception as e:
            sync_result["errors"].append(f"Accuracy tracking exception: {str(e)}")
        
        # Determine overall success
        sync_result["success"] = len(sync_result["synced_to"]) > 0  # Success if at least one sync worked
        
        # If there are errors, include them in the error message (truncated for log)
        if sync_result["errors"]:
            error_summary = "; ".join(sync_result["errors"])
            if len(error_summary) > 120:  # Keep under 140 char limit
                error_summary = error_summary[:120] + "..."
            sync_result["error"] = error_summary
        
        return sync_result
        
    except Exception as e:
        frappe.log_error(f"sync_single_forecast error for {financial_forecast_id}: {str(e)}")
        return {
            "success": False,
            "error": f"Sync single forecast failed: {str(e)}"
        }

def sync_to_cashflow(forecast_doc):
    """Sync AI Financial Forecast to AI Cashflow Forecast"""
    try:
        if forecast_doc.forecast_type != "Cash Flow":
            return {"success": False, "error": "Not a cash flow forecast"}
        
        # Check if exists - use forecast_start_date for comparison
        existing = frappe.get_all("AI Cashflow Forecast",
                                filters={
                                    "company": forecast_doc.company,
                                    "forecast_date": forecast_doc.forecast_start_date
                                },
                                limit=1)
        
        if existing:
            # Update existing
            cashflow_doc = frappe.get_doc("AI Cashflow Forecast", existing[0].name)
        else:
            # Create new
            cashflow_doc = frappe.get_doc({
                "doctype": "AI Cashflow Forecast",
                "company": forecast_doc.company,
                "forecast_date": forecast_doc.forecast_start_date,
                "forecast_period": "Monthly",
                "forecast_type": "Operational"
            })
        
        # Update common fields - check if they exist first
        if hasattr(cashflow_doc, 'net_cash_flow'):
            cashflow_doc.net_cash_flow = forecast_doc.predicted_amount
        
        if hasattr(cashflow_doc, 'confidence_score'):
            cashflow_doc.confidence_score = forecast_doc.confidence_score
        
        if hasattr(cashflow_doc, 'model_used'):
            cashflow_doc.model_used = forecast_doc.prediction_model
        
        if hasattr(cashflow_doc, 'last_updated'):
            cashflow_doc.last_updated = frappe.utils.now()
        
        # Update from forecast details if available
        if forecast_doc.forecast_details:
            try:
                details = json.loads(forecast_doc.forecast_details)
                cashflow_breakdown = details.get("cashflow_breakdown", {})
                
                if hasattr(cashflow_doc, 'predicted_inflows'):
                    cashflow_doc.predicted_inflows = cashflow_breakdown.get("total_inflows", 0)
                if hasattr(cashflow_doc, 'predicted_outflows'):
                    cashflow_doc.predicted_outflows = cashflow_breakdown.get("total_outflows", 0)
                if hasattr(cashflow_doc, 'liquidity_ratio'):
                    cashflow_doc.liquidity_ratio = cashflow_breakdown.get("liquidity_ratio", 100)
                if hasattr(cashflow_doc, 'surplus_deficit'):
                    cashflow_doc.surplus_deficit = cashflow_breakdown.get("surplus_deficit", 0)
                
            except json.JSONDecodeError:
                pass
        
        if existing:
            cashflow_doc.save(ignore_permissions=True)
        else:
            cashflow_doc.flags.ignore_permissions = True
            cashflow_doc.insert()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Successfully synced to AI Cashflow Forecast ({cashflow_doc.name})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Cashflow sync failed: {str(e)}"
        }

def test_quick_sync():
    """Quick sync test with limited results"""
    import frappe
    
    try:
        print("=== Quick Sync Test ===")
        
        # Test with just 5 forecasts
        financial_forecasts = frappe.get_all("AI Financial Forecast", 
                                            filters={}, 
                                            limit=5)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for forecast in financial_forecasts:
            try:
                result = sync_single_forecast(forecast.name)
                if result.get("success"):
                    success_count += 1
                    print(f"✓ {forecast.name}: Success")
                else:
                    error_count += 1
                    error_msg = result.get("error", "Unknown error")
                    errors.append(f"{forecast.name}: {error_msg}")
                    print(f"✗ {forecast.name}: {error_msg}")
            except Exception as e:
                error_count += 1
                errors.append(f"{forecast.name}: Exception: {str(e)}")
                print(f"✗ {forecast.name}: Exception: {str(e)}")
        
        print(f"\n=== Summary ===")
        print(f"Success: {success_count}/{len(financial_forecasts)}")
        print(f"Errors: {error_count}/{len(financial_forecasts)}")
        
        if errors:
            print(f"First few errors:")
            for error in errors[:3]:
                print(f"  - {error}")
        
        return {
            "success": error_count == 0,
            "total": len(financial_forecasts),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:5]  # Limit errors
        }
        
    except Exception as e:
        print(f"Test error: {e}")
        return {"success": False, "error": str(e)}

def sync_to_revenue(forecast_doc):
    """Sync AI Financial Forecast to AI Revenue Forecast"""
    try:
        if forecast_doc.forecast_type != "Revenue":
            return {"success": False, "error": "Not a revenue forecast"}
        
        # Check if exists - use forecast_start_date for comparison
        existing = frappe.get_all("AI Revenue Forecast",
                                filters={
                                    "company": forecast_doc.company,
                                    "forecast_date": forecast_doc.forecast_start_date
                                },
                                limit=1)
        
        if existing:
            # Update existing
            revenue_doc = frappe.get_doc("AI Revenue Forecast", existing[0].name)
        else:
            # Create new
            revenue_doc = frappe.get_doc({
                "doctype": "AI Revenue Forecast",
                "company": forecast_doc.company,
                "forecast_date": forecast_doc.forecast_start_date,
                "forecast_period": "Monthly"
            })
        
        # Update common fields - check if they exist first
        if hasattr(revenue_doc, 'total_predicted_revenue'):
            revenue_doc.total_predicted_revenue = forecast_doc.predicted_amount
        elif hasattr(revenue_doc, 'predicted_revenue'):
            revenue_doc.predicted_revenue = forecast_doc.predicted_amount
        
        if hasattr(revenue_doc, 'confidence_score'):
            revenue_doc.confidence_score = forecast_doc.confidence_score
        
        if hasattr(revenue_doc, 'model_used'):
            revenue_doc.model_used = forecast_doc.prediction_model
        elif hasattr(revenue_doc, 'prediction_model'):
            revenue_doc.prediction_model = forecast_doc.prediction_model
        
        if hasattr(revenue_doc, 'last_updated'):
            revenue_doc.last_updated = frappe.utils.now()
        
        # Update from forecast details if available
        if forecast_doc.forecast_details:
            try:
                details = json.loads(forecast_doc.forecast_details)
                revenue_breakdown = details.get("revenue_breakdown", {})
                
                if hasattr(revenue_doc, 'product_revenue'):
                    revenue_doc.product_revenue = revenue_breakdown.get("product_revenue", 0)
                if hasattr(revenue_doc, 'service_revenue'):
                    revenue_doc.service_revenue = revenue_breakdown.get("service_revenue", 0)
                if hasattr(revenue_doc, 'recurring_revenue'):
                    revenue_doc.recurring_revenue = revenue_breakdown.get("recurring_revenue", 0)
                if hasattr(revenue_doc, 'growth_rate'):
                    revenue_doc.growth_rate = revenue_breakdown.get("growth_rate", 0)
                if hasattr(revenue_doc, 'seasonal_factor'):
                    revenue_doc.seasonal_factor = revenue_breakdown.get("seasonal_factor", 1.0)
                if hasattr(revenue_doc, 'market_factor'):
                    revenue_doc.market_factor = revenue_breakdown.get("market_factor", 1.0)
                
            except json.JSONDecodeError:
                pass
        
        if existing:
            revenue_doc.save(ignore_permissions=True)
        else:
            revenue_doc.flags.ignore_permissions = True
            revenue_doc.insert()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Successfully synced to AI Revenue Forecast ({revenue_doc.name})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Revenue sync failed: {str(e)}"
        }

def sync_to_expense(forecast_doc):
    """Sync AI Financial Forecast to AI Expense Forecast"""
    try:
        if forecast_doc.forecast_type != "Expense":
            return {"success": False, "error": "Not an expense forecast"}
        
        # Check if exists - use forecast_start_date for comparison
        existing = frappe.get_all("AI Expense Forecast",
                                filters={
                                    "company": forecast_doc.company,
                                    "forecast_date": forecast_doc.forecast_start_date
                                },
                                limit=1)
        
        if existing:
            # Update existing
            expense_doc = frappe.get_doc("AI Expense Forecast", existing[0].name)
        else:
            # Create new - ensure all required fields are set
            expense_data = {
                "doctype": "AI Expense Forecast",
                "company": forecast_doc.company,
                "forecast_date": forecast_doc.forecast_start_date,
                "forecast_period": "Monthly"  # Set default forecast_period
            }
            expense_doc = frappe.get_doc(expense_data)
        
        # Update expense amount - use correct field name
        if hasattr(expense_doc, 'total_predicted_expense'):
            expense_doc.total_predicted_expense = forecast_doc.predicted_amount
        elif hasattr(expense_doc, 'predicted_expenses'):
            expense_doc.predicted_expenses = forecast_doc.predicted_amount
        
        # Update confidence in available field
        if hasattr(expense_doc, 'confidence_score'):
            expense_doc.confidence_score = forecast_doc.confidence_score
        elif hasattr(expense_doc, 'prediction_confidence'):
            expense_doc.prediction_confidence = forecast_doc.confidence_score
        
        # Update model in available field
        if hasattr(expense_doc, 'model_used'):
            expense_doc.model_used = forecast_doc.prediction_model
        elif hasattr(expense_doc, 'prediction_model'):
            expense_doc.prediction_model = forecast_doc.prediction_model
        
        # Update timestamp
        if hasattr(expense_doc, 'last_updated'):
            expense_doc.last_updated = frappe.utils.now()
        
        # Add any forecast details if available
        if forecast_doc.forecast_details:
            try:
                details = json.loads(forecast_doc.forecast_details)
                expense_breakdown = details.get("expense_breakdown", {})
                
                if hasattr(expense_doc, 'fixed_expenses'):
                    expense_doc.fixed_expenses = expense_breakdown.get("fixed_expenses", 0)
                if hasattr(expense_doc, 'variable_expenses'):
                    expense_doc.variable_expenses = expense_breakdown.get("variable_expenses", 0)
                if hasattr(expense_doc, 'operational_expenses'):
                    expense_doc.operational_expenses = expense_breakdown.get("operational_expenses", 0)
                    
            except json.JSONDecodeError:
                pass
        
        if existing:
            expense_doc.save(ignore_permissions=True)
        else:
            expense_doc.flags.ignore_permissions = True
            expense_doc.insert()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "expense_id": expense_doc.name,
            "action": "updated" if existing else "created"
        }
        
    except Exception as e:
        # Enhanced error logging for debugging
        frappe.log_error(f"Expense sync error for forecast {forecast_doc.name}: {str(e)}")
        return {"success": False, "error": f"Expense sync failed: {str(e)}"}

def sync_to_inventory_forecast(financial_forecast):
    """
    Sync AI Financial Forecast to AI Inventory Forecast
    Creates or updates inventory forecasts based on financial predictions
    """
    try:
        # Handle both document object and name string
        if isinstance(financial_forecast, str):
            # If it's a string, get the document
            financial_forecast = frappe.get_doc("AI Financial Forecast", financial_forecast)
        
        # Get items that might be impacted by this financial forecast
        items_to_forecast = []
        
        # Get default warehouse for the company
        default_warehouse = None
        
        # Try to get warehouse from company settings first
        try:
            company_doc = frappe.get_doc("Company", financial_forecast.company)
            # Check if company has a default warehouse field
            if hasattr(company_doc, 'default_warehouse') and company_doc.default_warehouse:
                default_warehouse = company_doc.default_warehouse
        except Exception:
            pass
        
        # If no default warehouse found, get the first available warehouse for the company
        if not default_warehouse:
            warehouses = frappe.get_all("Warehouse", 
                                      filters={"company": financial_forecast.company, "disabled": 0},
                                      fields=["name"],
                                      order_by="creation asc",
                                      limit=1)
            if warehouses:
                default_warehouse = warehouses[0].name
            else:
                return {
                    "success": False,
                    "error": f"No warehouse found for company {financial_forecast.company}. Please create a warehouse first."
                }
        
        if financial_forecast.forecast_type == "Revenue":
            # For revenue forecasts, find top-selling items
            items_to_forecast = frappe.db.sql("""
                SELECT DISTINCT si_item.item_code, si_item.item_name,
                       SUM(si_item.amount) as total_revenue,
                       AVG(si_item.qty) as avg_qty
                FROM `tabSales Invoice Item` si_item
                INNER JOIN `tabSales Invoice` si ON si.name = si_item.parent
                WHERE si.company = %s 
                AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                AND si.docstatus = 1
                GROUP BY si_item.item_code
                ORDER BY total_revenue DESC
                LIMIT 10
            """, (financial_forecast.company,), as_dict=True)
            
        elif financial_forecast.forecast_type == "Expense":
            # For expense forecasts, find high-cost purchase items
            items_to_forecast = frappe.db.sql("""
                SELECT DISTINCT pi_item.item_code, pi_item.item_name,
                       SUM(pi_item.amount) as total_cost,
                       AVG(pi_item.qty) as avg_qty
                FROM `tabPurchase Invoice Item` pi_item
                INNER JOIN `tabPurchase Invoice` pi ON pi.name = pi_item.parent
                WHERE pi.company = %s 
                AND pi.posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                AND pi.docstatus = 1
                GROUP BY pi_item.item_code
                ORDER BY total_cost DESC
                LIMIT 10
            """, (financial_forecast.company,), as_dict=True)
            
        elif financial_forecast.forecast_type == "Cash Flow":
            # For cash flow forecasts, find items with high inventory value
            items_to_forecast = frappe.db.sql("""
                SELECT DISTINCT sle.item_code, item.item_name,
                       SUM(ABS(sle.actual_qty * sle.valuation_rate)) as inventory_value,
                       AVG(ABS(sle.actual_qty)) as avg_movement
                FROM `tabStock Ledger Entry` sle
                INNER JOIN `tabItem` item ON item.name = sle.item_code
                WHERE sle.company = %s 
                AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
                GROUP BY sle.item_code
                HAVING inventory_value > 1000
                ORDER BY inventory_value DESC
                LIMIT 5
            """, (financial_forecast.company,), as_dict=True)
        
        if not items_to_forecast:
            return {
                "success": True,
                "message": "No relevant items found for inventory forecasting",
                "inventory_forecast_id": None
            }
        
        # Create or update inventory forecasts
        synced_forecasts = []
        primary_forecast_id = None
        
        for item_data in items_to_forecast:
            try:
                # Check if inventory forecast already exists
                existing_forecast = frappe.get_all("AI Inventory Forecast",
                                                 filters={
                                                     "item_code": item_data.item_code,
                                                     "company": financial_forecast.company,
                                                     "warehouse": default_warehouse
                                                 },
                                                 order_by="creation desc",
                                                 limit=1)
                
                if existing_forecast:
                    # Update existing forecast
                    inv_forecast = frappe.get_doc("AI Inventory Forecast", existing_forecast[0].name)
                    
                    # Update confidence score based on financial forecast confidence
                    if hasattr(inv_forecast, 'confidence_score'):
                        inv_forecast.confidence_score = min(95, financial_forecast.confidence_score + 10)
                    
                    # Set bidirectional reference
                    if hasattr(inv_forecast, 'source_financial_forecast'):
                        inv_forecast.source_financial_forecast = financial_forecast.name
                    
                    # Add comment linking to financial forecast
                    inv_forecast.add_comment("Comment", 
                                           f"Updated from Financial Forecast: {financial_forecast.name} "
                                           f"({financial_forecast.forecast_type})")
                    
                    inv_forecast.flags.ignore_permissions = True
                    inv_forecast.save()
                    
                    synced_forecasts.append(inv_forecast.name)
                    if not primary_forecast_id:
                        primary_forecast_id = inv_forecast.name
                
                else:
                    # Create new inventory forecast
                    # Calculate predicted consumption based on financial forecast
                    predicted_qty = 0
                    if financial_forecast.forecast_type == "Revenue" and item_data.get('avg_qty'):
                        # Estimate demand increase based on revenue prediction
                        growth_factor = max(1.0, financial_forecast.confidence_score / 100)
                        predicted_qty = int(item_data.avg_qty * growth_factor * 30)  # Monthly prediction
                    
                    elif financial_forecast.forecast_type == "Expense" and item_data.get('avg_qty'):
                        # Estimate supply needs based on expense forecast
                        predicted_qty = int(item_data.avg_qty * 1.2 * 30)  # Monthly prediction with buffer
                    
                    elif financial_forecast.forecast_type == "Cash Flow" and item_data.get('avg_movement'):
                        # Estimate movement based on cash flow prediction
                        predicted_qty = int(item_data.avg_movement * 0.8 * 30)  # Conservative monthly prediction
                    
                    if predicted_qty > 0:
                        # Validate that the item exists and is active
                        item_exists = frappe.db.exists("Item", item_data.item_code)
                        if not item_exists:
                            frappe.log_error(f"Item {item_data.item_code} does not exist, skipping forecast creation")
                            continue
                        
                        inv_forecast = frappe.get_doc({
                            "doctype": "AI Inventory Forecast",
                            "item_code": item_data.item_code,
                            "warehouse": default_warehouse,
                            "company": financial_forecast.company,
                            "predicted_consumption": predicted_qty,
                            "confidence_score": max(60, financial_forecast.confidence_score - 10),
                            "movement_type": "",  # Leave empty as "Normal" is not a valid option
                            "forecast_period_days": 30,
                            "source_financial_forecast": financial_forecast.name
                        })
                        
                        # Validate the document before inserting
                        try:
                            inv_forecast.flags.ignore_permissions = True
                            inv_forecast.insert()
                            
                            # Add comment linking to financial forecast
                            inv_forecast.add_comment("Comment", 
                                                   f"Created from Financial Forecast: {financial_forecast.name} "
                                                   f"({financial_forecast.forecast_type})")
                            
                            synced_forecasts.append(inv_forecast.name)
                            if not primary_forecast_id:
                                primary_forecast_id = inv_forecast.name
                                
                        except frappe.ValidationError as ve:
                            frappe.log_error(f"Validation error creating inventory forecast for {item_data.item_code}: {str(ve)}")
                            continue
                            
            except Exception as item_error:
                frappe.log_error(f"Error syncing item {item_data.item_code} to inventory forecast: {str(item_error)}")
                continue
        
        return {
            "success": True,
            "message": f"Synced {len(synced_forecasts)} inventory forecasts",
            "inventory_forecast_id": primary_forecast_id,
            "synced_forecasts": synced_forecasts,
            "items_processed": len(items_to_forecast)
        }
        
    except Exception as e:
        frappe.log_error(f"Inventory forecast sync error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def create_accuracy_tracking(forecast_doc):
    """Create accuracy tracking record"""
    try:
        # Check if accuracy record exists
        existing = frappe.get_all("AI Forecast Accuracy",
                                filters={
                                    "forecast_reference": forecast_doc.name,
                                    "measurement_date": forecast_doc.forecast_start_date
                                },
                                limit=1)
        
        if existing:
            return {"success": True, "action": "already_exists"}
        
        # Create new accuracy tracking record
        accuracy_doc = frappe.get_doc({
            "doctype": "AI Forecast Accuracy",
            "company": forecast_doc.company,
            "forecast_type": forecast_doc.forecast_type,
            "measurement_date": forecast_doc.forecast_start_date,
            "forecast_reference": forecast_doc.name,
            "model_used": forecast_doc.prediction_model,
            "measurement_period": "Monthly",
            "predicted_value": forecast_doc.predicted_amount,
            # Initialize accuracy metrics (will be updated when actual values are available)
            "actual_value": 0,
            "accuracy_percentage": 0,
            "absolute_error": 0,
            "percentage_error": 0,
            "squared_error": 0,
            "performance_grade": "C",  # Default grade for new forecasts
            "accuracy_trend": "Stable",
            "model_reliability_score": forecast_doc.confidence_score,
            "confidence_calibration": forecast_doc.confidence_score,
            "contextual_factors": f"Created from AI Financial Forecast {forecast_doc.name}"
        })
        
        accuracy_doc.flags.ignore_permissions = True
        accuracy_doc.insert()
        frappe.db.commit()
        
        return {
            "success": True,
            "accuracy_id": accuracy_doc.name,
            "action": "created"
        }
        
    except Exception as e:
        frappe.log_error(f"Accuracy tracking creation error: {str(e)}")
        return {"success": False, "error": str(e)}

def create_sync_log(sync_results, forecast_reference=None):
    """Create sync log entry"""
    try:
        # Calculate success rate
        total = sync_results.get("total_forecasts", 0)
        successful = sync_results.get("synced_successfully", 0)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        log_doc = frappe.get_doc({
            "doctype": "AI Forecast Sync Log",
            "forecast_reference": forecast_reference,
            "sync_date": frappe.utils.nowdate(),
            "sync_time": frappe.utils.now(),
            "sync_timestamp": frappe.utils.now(),
            "sync_type": "Manual Sync",  # Default to Manual Sync
            "sync_status": "Completed" if total > 0 and sync_results.get("sync_errors", 0) == 0 else "Failed",
            "sync_message": f"Sync completed. {successful} successful, {sync_results.get('sync_errors', 0)} failed.",
            "sync_duration": sync_results.get("sync_duration", 0),
            "total_items": total,
            "successful_items": successful,
            "failed_items": sync_results.get("sync_errors", 0),
            "success_rate": success_rate,
            "sync_details": json.dumps(sync_results)
        })
        
        log_doc.flags.ignore_permissions = True
        log_doc.insert()
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating sync log: {str(e)}")

@frappe.whitelist()
def trigger_manual_sync(forecast_name):
    """Trigger manual sync for a specific forecast"""
    try:
        import time
        start_time = time.time()
        
        # Get a fresh copy of the forecast document
        forecast = frappe.get_doc("AI Financial Forecast", forecast_name)
        
        # Update sync status without conflicts
        try:
            frappe.db.set_value("AI Financial Forecast", forecast_name, "sync_status", "Syncing")
            frappe.db.commit()
        except Exception as update_error:
            # Continue even if status update fails
            pass
        
        # Perform the sync
        result = sync_single_forecast(forecast_name)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update sync status based on result using direct DB update to avoid conflicts
        if result.get("success"):
            sync_status = "Completed"
            sync_message = "Manual sync completed successfully"
            try:
                frappe.db.set_value("AI Financial Forecast", forecast_name, {
                    "sync_status": sync_status,
                    "last_sync_date": frappe.utils.now()
                })
                frappe.db.commit()
            except Exception:
                pass
        else:
            sync_status = "Failed"
            error_msg = result.get('error', 'Unknown error')
            # Truncate error message to prevent "Value too big" error
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            sync_message = f"Manual sync failed: {error_msg}"
            try:
                frappe.db.set_value("AI Financial Forecast", forecast_name, "sync_status", sync_status)
                frappe.db.commit()
            except Exception:
                pass
        
        # Create individual sync log
        sync_log_data = {
            "total_forecasts": 1,
            "synced_successfully": 1 if result.get("success") else 0,
            "sync_errors": 0 if result.get("success") else 1,
            "sync_duration": duration,
            "sync_details": result
        }
        
        create_sync_log(sync_log_data, forecast_name)
        frappe.db.commit()
        
        return {
            "success": result.get("success", False),
            "message": sync_message,
            "error": result.get("error") if not result.get("success") else None
        }
        
    except Exception as e:
        # Create a short error message for logging
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        
        frappe.log_error(f"Manual sync error: {error_msg}", "Sync Error")
        
        # Update forecast status to failed
        try:
            forecast = frappe.get_doc("AI Financial Forecast", forecast_name)
            forecast.sync_status = "Failed"
            forecast.flags.ignore_permissions = True
            forecast.save()
            frappe.db.commit()
        except:
            pass
            
        return {
            "success": False,
            "error": error_msg
        }

@frappe.whitelist()
def bulk_sync_to_inventory():
    """Sync all AI Financial Forecasts to inventory forecasts"""
    try:
        # Get all financial forecasts
        forecasts = frappe.get_all("AI Financial Forecast",
                                  fields=["name", "company", "forecast_type"],
                                  filters={"docstatus": ["!=", 2]})  # Exclude cancelled
        
        if not forecasts:
            return {
                "success": False,
                "error": "No financial forecasts found to sync"
            }
        
        total_processed = 0
        total_synced = 0
        errors = []
        company_breakdown = {}
        
        for forecast in forecasts:
            try:
                total_processed += 1
                
                # Sync individual forecast to inventory
                result = sync_to_inventory_forecast(forecast.name)
                
                if result and result.get("success"):
                    total_synced += result.get("items_processed", 0)
                    
                    # Track by company
                    company = forecast.company
                    if company not in company_breakdown:
                        company_breakdown[company] = {"synced": 0, "errors": 0}
                    company_breakdown[company]["synced"] += result.get("items_processed", 0)
                    
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Sync returned None"
                    errors.append(f"{forecast.name}: {error_msg}")
                    
                    # Track error by company
                    company = forecast.company
                    if company not in company_breakdown:
                        company_breakdown[company] = {"synced": 0, "errors": 0}
                    company_breakdown[company]["errors"] += 1
                    
            except Exception as e:
                error_msg = str(e)
                if len(error_msg) > 80:
                    error_msg = error_msg[:80] + "..."
                errors.append(f"{forecast.name}: {error_msg}")
        
        # Determine success
        success = total_synced > 0
        
        result = {
            "success": success,
            "total_processed": total_processed,
            "total_synced": total_synced,
            "errors": errors,
            "company_breakdown": company_breakdown,
            "message": f"Processed {total_processed} AI Financial Forecasts, created {total_synced} inventory forecasts"
        }
        
        if errors:
            result["error"] = f"Completed with {len(errors)} errors"
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 120:
            error_msg = error_msg[:120] + "..."
        frappe.log_error(f"Bulk inventory sync error: {error_msg}", "Bulk Sync Error")
        return {
            "success": False,
            "error": error_msg
        }

@frappe.whitelist()
def get_sync_status(company=None, days=7):
    """Get sync status summary"""
    try:
        filters = {}
        if company:
            filters["company"] = company
        
        # Get recent financial forecasts
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))
        filters["creation"] = [">=", from_date]
        
        financial_forecasts = frappe.get_all("AI Financial Forecast",
                                           filters=filters,
                                           fields=["name", "forecast_type", "company", "forecast_start_date"],
                                           order_by="creation desc")
        
        sync_status = {
            "total_financial_forecasts": len(financial_forecasts),
            "sync_summary": {
                "Cash Flow": {"financial": 0, "synced": 0, "sync_rate": 0},
                "Revenue": {"financial": 0, "synced": 0, "sync_rate": 0},
                "Expense": {"financial": 0, "synced": 0, "sync_rate": 0}
            },
            "accuracy_tracking": 0,
            "last_sync_date": None
        }
        
        # Count by forecast type
        for forecast in financial_forecasts:
            ftype = forecast.forecast_type
            if ftype in sync_status["sync_summary"]:
                sync_status["sync_summary"][ftype]["financial"] += 1
        
        # Check sync status for each type
        for ftype in sync_status["sync_summary"]:
            target_doctype = {
                "Cash Flow": "AI Cashflow Forecast",
                "Revenue": "AI Revenue Forecast",
                "Expense": "AI Expense Forecast"
            }.get(ftype)
            
            if target_doctype:
                synced_count = frappe.db.count(target_doctype, 
                                             {"creation": [">=", from_date]})
                sync_status["sync_summary"][ftype]["synced"] = synced_count
                
                # Calculate sync rate
                financial_count = sync_status["sync_summary"][ftype]["financial"]
                if financial_count > 0:
                    sync_status["sync_summary"][ftype]["sync_rate"] = (synced_count / financial_count) * 100
        
        # Check accuracy tracking
        sync_status["accuracy_tracking"] = frappe.db.count("AI Forecast Accuracy",
                                                          {"creation": [">=", from_date]})
        
        # Get last sync log
        last_sync = frappe.get_all("AI Forecast Sync Log",
                                 order_by="creation desc",
                                 fields=["sync_date"],
                                 limit=1)
        
        if last_sync:
            sync_status["last_sync_date"] = last_sync[0].sync_date
        
        return sync_status
        
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def force_sync_specific_forecast(forecast_type, company=None, forecast_start_date=None):
    """Force sync for specific forecast type and date"""
    try:
        # If forecast_start_date is not provided, use today's date
        if not forecast_start_date:
            forecast_start_date = frappe.utils.nowdate()
        
        # If company is not provided, get default company
        if not company:
            company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        # Find the financial forecast
        financial_forecast = frappe.get_all("AI Financial Forecast",
                                          filters={
                                              "forecast_type": forecast_type,
                                              "company": company,
                                              "forecast_start_date": forecast_start_date
                                          },
                                          limit=1)
        
        if not financial_forecast:
            # If no exact match, find the most recent forecast of this type
            financial_forecast = frappe.get_all("AI Financial Forecast",
                                              filters={
                                                  "forecast_type": forecast_type,
                                                  "company": company
                                              },
                                              order_by="forecast_start_date desc",
                                              limit=1)
        
        if not financial_forecast:
            return {
                "success": False,
                "error": f"No AI Financial Forecast found for {forecast_type} in company {company}"
            }
        
        # Sync the forecast
        result = sync_single_forecast(financial_forecast[0].name)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Successfully synced {forecast_type} forecast for {forecast_start_date}",
                "sync_result": result
            }
        else:
            return {
                "success": False,
                "error": f"Sync failed: {result.get('error')}",
                "sync_result": result
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Auto-sync hook function
def auto_sync_on_financial_forecast_change(doc, method):
    """Hook function to auto-sync when AI Financial Forecast changes"""
    try:
        if doc.doctype == "AI Financial Forecast" and method in ["on_update", "after_insert"]:
            # Trigger sync in background
            frappe.enqueue(
                sync_single_forecast,
                financial_forecast_id=doc.name,
                queue="short",
                timeout=300
            )
    except Exception as e:
        frappe.log_error(f"Auto-sync error: {str(e)}")
