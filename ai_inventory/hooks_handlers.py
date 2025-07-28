# ai_inventory/hooks_handlers.py
# CORRECTED VERSION - Valid movement types and better error handling

import frappe
from frappe.utils import now, nowdate, add_days, flt
import json
import time
import os

def check_hooks_enabled():
    """Check if AI hooks are temporarily disabled"""
    try:
        flag_file = frappe.get_site_path("ai_hooks_disabled.flag")
        return not os.path.exists(flag_file)
    except:
        return True

# =============================================================================
# MAIN HOOK FUNCTIONS - THREAD SAFE VERSIONS
# =============================================================================

def on_stock_ledger_entry_submit_safe(doc, method):
    """Safe wrapper for stock ledger entry submit"""
    if not check_hooks_enabled():
        return
    try:
        on_stock_ledger_entry_submit(doc, method)
    except Exception as e:
        # Use simple logging to avoid cascade errors
        frappe.logger().error(f"Safe SLE hook failed: {str(e)[:100]}")

def on_stock_ledger_entry_submit(doc, method):
    """
    Triggered when Stock Ledger Entry is submitted
    Updates AI Inventory Forecast records for affected items - THREAD SAFE
    """
    try:
        # Skip if in bulk operation or hooks disabled
        if frappe.flags.in_bulk_operation or not check_hooks_enabled():
            return
            
        # Get company from warehouse
        warehouse_company = frappe.db.get_value("Warehouse", doc.warehouse, "company")
        
        # Use safe forecast update to avoid document conflicts
        safe_forecast_update_from_stock_entry(doc.item_code, doc.warehouse, warehouse_company, doc.actual_qty)
        
    except Exception as e:
        # Use simple logging to avoid cascade errors
        frappe.logger().error(f"AI Forecast update failed on stock movement: {str(e)[:100]}")

def safe_forecast_update_from_stock_entry(item_code, warehouse, company, qty_change):
    """Thread-safe forecast update from stock entry"""
    try:
        # Check if there's an AI Inventory Forecast for this item-warehouse-company combo
        forecast_name = frappe.db.exists("AI Inventory Forecast", {
            "item_code": item_code,
            "warehouse": warehouse,
            "company": company
        })
        
        # Also check for forecasts without company set
        if not forecast_name:
            forecast_name = frappe.db.exists("AI Inventory Forecast", {
                "item_code": item_code,
                "warehouse": warehouse,
                "company": ["in", [None, ""]]
            })
        
        if forecast_name:
            # Update current stock using direct SQL to avoid document conflicts
            frappe.db.sql("""
                UPDATE `tabAI Inventory Forecast`
                SET current_stock = (
                    SELECT COALESCE(b.actual_qty, 0)
                    FROM `tabBin` b
                    WHERE b.item_code = %s AND b.warehouse = %s
                ),
                modified = %s
                WHERE name = %s
            """, (item_code, warehouse, now(), forecast_name))
            
            # If it's a significant movement, queue forecast update
            if abs(qty_change) > 10:  # Configurable threshold
                queue_forecast_update(forecast_name, delay=2)  # 2 second delay
            
            frappe.db.commit()
            
        frappe.logger().info(f"Safe AI Forecast updated for {item_code} in {company}")
        
    except Exception as e:
        frappe.logger().error(f"Safe forecast update failed: {str(e)[:100]}")

def queue_forecast_update(forecast_name, delay=1):
    """Queue a forecast update with optional delay"""
    try:
        frappe.enqueue(
            'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.run_forecast_background',
            forecast_name=forecast_name,
            queue='short',
            timeout=300,
            is_async=True,
            enqueue_after_commit=True,
            now=False if delay > 0 else True
        )
    except Exception as e:
        frappe.logger().error(f"Forecast update queue failed: {str(e)[:100]}")

# =============================================================================
# FIXED ITEM HOOKS - AUTO CREATE FORECASTS WITH VALID MOVEMENT TYPES
# =============================================================================

def on_item_after_insert_safe(doc, method):
    """Safe wrapper for item after insert - AUTO CREATE FORECASTS"""
    if not check_hooks_enabled():
        return
    try:
        on_item_after_insert(doc, method)
    except Exception as e:
        # Use simple logging to avoid cascade errors
        frappe.logger().error(f"Safe item insert hook failed: {str(e)[:100]}")

def on_item_after_insert(doc, method):
    """
    Triggered when new Item is created
    Auto-creates AI Inventory Forecast records for stock items
    """
    try:
        # Only process stock items
        if not doc.is_stock_item or doc.disabled:
            return
            
        # Skip if in bulk operation
        if frappe.flags.in_bulk_operation:
            # Queue for later processing
            queue_item_forecast_creation(doc.name)
            return
        
        # Create forecasts for all active warehouses
        created_count = create_forecasts_for_new_item(doc.name)
        
        if created_count > 0:
            frappe.logger().info(f"Created {created_count} AI Forecasts for new item: {doc.name}")
        
    except Exception as e:
        # Use simple logging to avoid cascade errors
        frappe.logger().error(f"Failed to create forecasts for new item {doc.name}: {str(e)[:100]}")

def create_forecasts_for_new_item(item_code):
    """Create AI Inventory Forecasts for a new item across all warehouses"""
    try:
        created_count = 0
        
        # Get all active warehouses
        warehouses = frappe.get_all("Warehouse", 
            filters={}, 
            fields=["name", "company"]
        )
        
        for warehouse in warehouses:
            try:
                # Check if forecast already exists
                existing = frappe.db.exists("AI Inventory Forecast", {
                    "item_code": item_code,
                    "warehouse": warehouse.name,
                    "company": warehouse.company
                })
                
                if not existing:
                    # Create new forecast with VALID movement type
                    forecast = frappe.get_doc({
                        "doctype": "AI Inventory Forecast",
                        "item_code": item_code,
                        "warehouse": warehouse.name,
                        "company": warehouse.company,
                        "forecast_period_days": 30,
                        "lead_time_days": 14,
                        "current_stock": 0,
                        "predicted_consumption": 0,
                        "movement_type": "Non Moving",  # FIXED: Use valid movement type
                        "confidence_score": 0,
                        "forecast_details": f"Auto-created forecast for new item {item_code}"
                    })
                    
                    # Skip forecast run during creation to avoid delays
                    forecast.flags.skip_forecast = True
                    forecast.insert(ignore_permissions=True)
                    created_count += 1
                    
                    # Queue forecast update for later
                    queue_forecast_update(forecast.name, delay=5)
                    
            except Exception as e:
                # Use simple logging to avoid cascade errors
                frappe.logger().error(f"Failed to create forecast for {item_code} in {warehouse.name}: {str(e)[:100]}")
                continue
        
        # Commit after each item to ensure data is saved
        frappe.db.commit()
        
        return created_count
        
    except Exception as e:
        frappe.logger().error(f"Failed to create forecasts for item {item_code}: {str(e)[:100]}")
        return 0

def queue_item_forecast_creation(item_code):
    """Queue forecast creation for bulk operations"""
    try:
        frappe.enqueue(
            'ai_inventory.hooks_handlers.create_forecasts_for_new_item',
            item_code=item_code,
            queue='long',
            timeout=600,
            is_async=True,
            enqueue_after_commit=True
        )
    except Exception as e:
        frappe.logger().error(f"Failed to queue forecast creation for {item_code}: {str(e)[:100]}")

def on_item_on_update_safe(doc, method):
    """Safe wrapper for item on update"""
    if not check_hooks_enabled():
        return
    try:
        on_item_on_update(doc, method)
    except Exception as e:
        frappe.logger().error(f"Safe item update hook failed: {str(e)[:100]}")

def on_item_on_update(doc, method):
    """
    Triggered when Item is updated
    Updates related AI Inventory Forecasts if item properties change
    """
    try:
        # Check if item was disabled/enabled or stock status changed
        if hasattr(doc, '_doc_before_save'):
            old_doc = doc._doc_before_save
            
            # If item was disabled, disable related forecasts
            if doc.disabled and not old_doc.disabled:
                disable_item_forecasts(doc.name)
            
            # If item was enabled, re-enable forecasts
            elif not doc.disabled and old_doc.disabled:
                enable_item_forecasts(doc.name)
            
            # If stock item status changed
            if doc.is_stock_item != old_doc.is_stock_item:
                if doc.is_stock_item:
                    # Item became stock item - create forecasts
                    create_forecasts_for_new_item(doc.name)
                else:
                    # Item is no longer stock item - disable forecasts
                    disable_item_forecasts(doc.name)
        
    except Exception as e:
        frappe.logger().error(f"Failed to update forecasts for item {doc.name}: {str(e)[:100]}")

def disable_item_forecasts(item_code):
    """Disable all forecasts for an item"""
    try:
        frappe.db.sql("""
            UPDATE `tabAI Inventory Forecast`
            SET disabled = 1, modified = %s
            WHERE item_code = %s
        """, (now(), item_code))
        
        frappe.db.commit()
        frappe.logger().info(f"Disabled forecasts for item: {item_code}")
        
    except Exception as e:
        frappe.logger().error(f"Failed to disable forecasts for {item_code}: {str(e)[:100]}")

def enable_item_forecasts(item_code):
    """Enable all forecasts for an item"""
    try:
        frappe.db.sql("""
            UPDATE `tabAI Inventory Forecast`
            SET disabled = 0, modified = %s
            WHERE item_code = %s
        """, (now(), item_code))
        
        frappe.db.commit()
        frappe.logger().info(f"Enabled forecasts for item: {item_code}")
        
    except Exception as e:
        frappe.logger().error(f"Failed to enable forecasts for {item_code}: {str(e)[:100]}")

# =============================================================================
# WAREHOUSE HOOKS
# =============================================================================

def on_warehouse_after_insert_safe(doc, method):
    """Safe wrapper for warehouse after insert"""
    if not check_hooks_enabled():
        return
    try:
        on_warehouse_after_insert(doc, method)
    except Exception as e:
        frappe.logger().error(f"Safe warehouse hook failed: {str(e)[:100]}")

def on_warehouse_after_insert(doc, method):
    """
    Triggered when new Warehouse is created
    Creates AI Inventory Forecasts for all existing stock items
    """
    try:
        if doc.disabled:
            return
            
        # Skip if in bulk operation
        if frappe.flags.in_bulk_operation:
            queue_warehouse_forecast_creation(doc.name, doc.company)
            return
        
        # Create forecasts for all existing stock items
        created_count = create_forecasts_for_new_warehouse(doc.name, doc.company)
        
        if created_count > 0:
            frappe.logger().info(f"Created {created_count} AI Forecasts for new warehouse: {doc.name}")
        
    except Exception as e:
        frappe.logger().error(f"Failed to create forecasts for new warehouse {doc.name}: {str(e)[:100]}")

def create_forecasts_for_new_warehouse(warehouse, company):
    """Create AI Inventory Forecasts for all items in a new warehouse"""
    try:
        created_count = 0
        
        # Get all active stock items
        items = frappe.get_all("Item", 
            filters={"is_stock_item": 1, }, 
            fields=["name"]
        )
        
        for item in items:
            try:
                # Check if forecast already exists
                existing = frappe.db.exists("AI Inventory Forecast", {
                    "item_code": item.name,
                    "warehouse": warehouse,
                    "company": company
                })
                
                if not existing:
                    # Create new forecast with VALID movement type
                    forecast = frappe.get_doc({
                        "doctype": "AI Inventory Forecast",
                        "item_code": item.name,
                        "warehouse": warehouse,
                        "company": company,
                        "forecast_period_days": 30,
                        "lead_time_days": 14,
                        "current_stock": 0,
                        "predicted_consumption": 0,
                        "movement_type": "Non Moving",  # FIXED: Use valid movement type
                        "confidence_score": 0,
                        "forecast_details": f"Auto-created forecast for warehouse {warehouse}"
                    })
                    
                    # Skip forecast run during creation
                    forecast.flags.skip_forecast = True
                    forecast.insert(ignore_permissions=True)
                    created_count += 1
                    
            except Exception as e:
                frappe.logger().error(f"Failed to create forecast for {item.name} in {warehouse}: {str(e)[:100]}")
                continue
        
        # Commit after warehouse creation
        frappe.db.commit()
        
        return created_count
        
    except Exception as e:
        frappe.logger().error(f"Failed to create forecasts for warehouse {warehouse}: {str(e)[:100]}")
        return 0

def queue_warehouse_forecast_creation(warehouse, company):
    """Queue forecast creation for new warehouse"""
    try:
        frappe.enqueue(
            'ai_inventory.hooks_handlers.create_forecasts_for_new_warehouse',
            warehouse=warehouse,
            company=company,
            queue='long',
            timeout=1200,
            is_async=True,
            enqueue_after_commit=True
        )
    except Exception as e:
        frappe.logger().error(f"Failed to queue forecast creation for warehouse {warehouse}: {str(e)[:100]}")

# =============================================================================
# BULK IMPORT HANDLER
# =============================================================================

@frappe.whitelist()
def handle_bulk_item_import():
    """Handle bulk item import - create forecasts for all new items"""
    try:
        # Set bulk operation flag
        frappe.flags.in_bulk_operation = True
        
        # Get all stock items without forecasts
        items_without_forecasts = frappe.db.sql("""
            SELECT DISTINCT i.name, i.item_name
            FROM `tabItem` i
            WHERE i.is_stock_item = 1 
            AND i.disabled = 0
            AND NOT EXISTS (
                SELECT 1 FROM `tabAI Inventory Forecast` aif 
                WHERE aif.item_code = i.name
            )
            LIMIT 1000
        """, as_dict=True)
        
        if not items_without_forecasts:
            return {
                "status": "info",
                "message": "All items already have forecasts",
                "items_processed": 0
            }
        
        total_created = 0
        
        # Process items in batches
        batch_size = 50
        for i in range(0, len(items_without_forecasts), batch_size):
            batch = items_without_forecasts[i:i + batch_size]
            
            for item in batch:
                try:
                    created_count = create_forecasts_for_new_item(item.name)
                    total_created += created_count
                except Exception as e:
                    frappe.logger().error(f"Bulk import forecast creation failed for {item.name}: {str(e)[:100]}")
                    continue
            
            # Commit after each batch
            frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Created forecasts for {len(items_without_forecasts)} items. Total forecasts: {total_created}",
            "items_processed": len(items_without_forecasts),
            "forecasts_created": total_created
        }
        
    except Exception as e:
        error_msg = f"Bulk import handler failed: {str(e)}"
        frappe.logger().error(error_msg[:100])
        return {
            "status": "error",
            "message": error_msg
        }
    finally:
        frappe.flags.in_bulk_operation = False

# =============================================================================
# API FUNCTIONS WITH SAFETY CHECKS
# =============================================================================

@frappe.whitelist()
def bulk_create_forecasts_for_existing_items(company=None):
    """Bulk create AI Inventory Forecast records - THREAD SAFE"""
    try:
        # Set bulk operation flag
        frappe.flags.in_bulk_operation = True
        
        # Build query with optional company filter
        company_filter = ""
        params = []
        if company:
            company_filter = "AND w.company = %s"
            params.append(company)
        
        # Get all stock items that don't have forecasts for specified company
        items_without_forecasts = frappe.db.sql(f"""
            SELECT DISTINCT 
                i.name as item_code, 
                i.item_name,
                w.name as warehouse,
                w.company
            FROM `tabItem` i
            CROSS JOIN `tabWarehouse` w
            WHERE i.is_stock_item = 1 
            AND i.disabled = 0
            AND w.disabled = 0
            {company_filter}
            AND NOT EXISTS (
                SELECT 1 FROM `tabAI Inventory Forecast` aif 
                WHERE aif.item_code = i.name 
                AND aif.warehouse = w.name
                AND aif.company = w.company
            )
            LIMIT 500
        """, params, as_dict=True)
        
        total_created = 0
        processed_items = 0
        company_counts = {}
        
        for item in items_without_forecasts:
            try:
                # Create forecast with VALID movement type
                forecast = frappe.get_doc({
                    "doctype": "AI Inventory Forecast",
                    "item_code": item.item_code,
                    "warehouse": item.warehouse,
                    "company": item.company,
                    "forecast_period_days": 30,
                    "lead_time_days": 14,
                    "movement_type": "Non Moving"  # FIXED: Use valid movement type
                })
                
                forecast.flags.skip_forecast = True
                forecast.insert(ignore_permissions=True)
                total_created += 1
                
                # Track by company
                company_counts[item.company] = company_counts.get(item.company, 0) + 1
                
            except Exception as e:
                frappe.logger().error(f"Failed to create forecast for {item.item_code}: {str(e)[:100]}")
            
            processed_items += 1
            
            # Commit every 25 items to avoid timeout
            if processed_items % 25 == 0:
                frappe.db.commit()
        
        # Final commit
        frappe.db.commit()
        
        company_summary = ", ".join([f"{comp}: {count}" for comp, count in company_counts.items()])
        
        return {
            "status": "success",
            "message": f"Created {total_created} forecast records{' in ' + company if company else ''}\nCompany breakdown: {company_summary}",
            "items_processed": processed_items,
            "forecasts_created": total_created,
            "company_breakdown": company_counts,
            "company": company
        }
        
    except Exception as e:
        frappe.logger().error(f"Safe bulk creation failed: {str(e)[:100]}")
        return {"status": "error", "message": str(e)}
    finally:
        frappe.flags.in_bulk_operation = False

@frappe.whitelist()
def auto_create_forecasts_for_items_with_stock(company=None):
    """Create forecasts only for items that have actual stock - THREAD SAFE"""
    try:
        # Set bulk operation flag
        frappe.flags.in_bulk_operation = True
        
        # Build query with optional company filter
        company_filter = ""
        params = []
        if company:
            company_filter = "AND w.company = %s"
            params.append(company)
        
        # Get items that have stock but no forecasts for specified company
        items_with_stock = frappe.db.sql(f"""
            SELECT DISTINCT 
                b.item_code, 
                b.warehouse,
                w.company,
                i.item_name,
                b.actual_qty
            FROM `tabBin` b
            INNER JOIN `tabItem` i ON i.name = b.item_code
            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
            WHERE i.is_stock_item = 1 
            AND i.disabled = 0
            AND w.disabled = 0
            {company_filter}
            AND (b.actual_qty > 0 OR b.planned_qty > 0 OR b.ordered_qty > 0)
            AND NOT EXISTS (
                SELECT 1 FROM `tabAI Inventory Forecast` aif 
                WHERE aif.item_code = b.item_code 
                AND aif.warehouse = b.warehouse
                AND aif.company = w.company
            )
            LIMIT 300
        """, params, as_dict=True)
        
        created_count = 0
        company_counts = {}
        
        for item in items_with_stock:
            try:
                # Create forecast for this specific item-warehouse-company combination
                forecast = frappe.get_doc({
                    "doctype": "AI Inventory Forecast",
                    "item_code": item.item_code,
                    "warehouse": item.warehouse,
                    "company": item.company,
                    "forecast_period_days": 30,
                    "lead_time_days": 14,
                    "current_stock": item.actual_qty,
                    "movement_type": "Non Moving"  # FIXED: Use valid movement type
                })
                
                forecast.flags.skip_forecast = True
                forecast.insert(ignore_permissions=True)
                created_count += 1
                
                # Track by company
                company_counts[item.company] = company_counts.get(item.company, 0) + 1
                
                # Commit every 25 records
                if created_count % 25 == 0:
                    frappe.db.commit()
                    
            except Exception as e:
                frappe.logger().error(f"Failed to create forecast: {str(e)[:100]}")
        
        # Final commit
        frappe.db.commit()
        
        company_summary = ", ".join([f"{comp}: {count}" for comp, count in company_counts.items()])
        
        return {
            "status": "success", 
            "message": f"Created {created_count} forecasts{' in ' + company if company else ''}\nCompany breakdown: {company_summary}",
            "forecasts_created": created_count,
            "company_breakdown": company_counts,
            "company": company
        }
        
    except Exception as e:
        frappe.logger().error(f"Auto-create for items with stock failed: {str(e)[:100]}")
        return {"status": "error", "message": str(e)}
    finally:
        frappe.flags.in_bulk_operation = False

@frappe.whitelist()
def trigger_immediate_forecast_update(item_code, warehouse):
    """Trigger immediate forecast update safely"""
    try:
        # Find the forecast
        forecast_name = frappe.db.get_value("AI Inventory Forecast", {
            "item_code": item_code,
            "warehouse": warehouse
        })
        
        if forecast_name:
            # Queue the update instead of running immediately
            queue_forecast_update(forecast_name, delay=0)
            
            return {
                "status": "success",
                "message": f"Forecast update queued for {item_code} at {warehouse}"
            }
        else:
            return {
                "status": "error",
                "message": "No forecast record found"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =============================================================================
# DAILY MAINTENANCE FUNCTIONS
# =============================================================================

def daily_create_missing_forecasts():
    """Daily task to ensure all stock items have forecast records"""
    try:
        # Create forecasts for items with stock
        result = auto_create_forecasts_for_items_with_stock()
        
        if result.get("status") == "success" and result.get("forecasts_created", 0) > 0:
            frappe.logger().info(f"Daily forecast creation: {result['message']}")
            
    except Exception as e:
        frappe.logger().error(f"Daily create missing forecasts failed: {str(e)[:100]}")

def process_forecast_update_queue():
    """Process queued forecast updates (called by scheduler)"""
    try:
        # Get queued updates from Redis or database
        queued_updates = frappe.cache().get("forecast_update_queue") or []
        
        if not queued_updates:
            return
            
        # Process in batches
        batch_size = 50
        for i in range(0, len(queued_updates), batch_size):
            batch = queued_updates[i:i + batch_size]
            
            for update in batch:
                try:
                    forecast_doc = frappe.get_doc("AI Inventory Forecast", update["forecast_id"])
                    forecast_doc.run_ai_forecast()
                    forecast_doc.save()
                    
                except Exception as e:
                    frappe.logger().error(f"Batch forecast update failed for {update['forecast_id']}: {str(e)[:100]}")
                    
            # Commit after each batch
            frappe.db.commit()
            
        # Clear the queue
        frappe.cache().delete("forecast_update_queue")
        
    except Exception as e:
        frappe.logger().error(f"Forecast update queue processing failed: {str(e)[:100]}")

# =============================================================================
# SAFE WRAPPERS FOR ALL OTHER HOOKS
# =============================================================================

def on_purchase_order_submit_safe(doc, method):
    """Safe wrapper for purchase order submit"""
    if not check_hooks_enabled():
        return
    try:
        frappe.logger().info(f"Purchase Order {doc.name} submitted for {doc.company}")
    except Exception as e:
        frappe.logger().error(f"Safe PO hook failed: {str(e)[:100]}")

def on_purchase_receipt_submit_safe(doc, method):
    """Safe wrapper for purchase receipt submit"""
    if not check_hooks_enabled():
        return
    try:
        frappe.logger().info(f"Purchase Receipt {doc.name} submitted for {doc.company}")
    except Exception as e:
        frappe.logger().error(f"Safe PR hook failed: {str(e)[:100]}")

def validate_ai_inventory_forecast_safe(doc, method):
    """Safe wrapper for AI forecast validation"""
    if not check_hooks_enabled():
        return
    try:
        if not doc.company and doc.warehouse:
            doc.company = frappe.db.get_value("Warehouse", doc.warehouse, "company")
    except Exception as e:
        frappe.logger().error(f"Safe forecast validation failed: {str(e)[:100]}")

def on_ai_inventory_forecast_save_safe(doc, method):
    """Safe wrapper for AI forecast save"""
    if not check_hooks_enabled():
        return
    try:
        frappe.logger().info(f"AI Forecast saved: {doc.name}")
    except Exception as e:
        frappe.logger().error(f"Safe forecast save hook failed: {str(e)[:100]}")

def on_bin_update_safe(doc, method):
    """Safe wrapper for bin update"""
    if not check_hooks_enabled():
        return
    try:
        if hasattr(doc, '_doc_before_save'):
            old_qty = flt(doc._doc_before_save.actual_qty)
            new_qty = flt(doc.actual_qty)
            if abs(new_qty - old_qty) > 10:
                frappe.logger().info(f"Significant stock change for {doc.item_code}: {old_qty} -> {new_qty}")
    except Exception as e:
        frappe.logger().error(f"Safe bin update hook failed: {str(e)[:100]}")

def on_stock_entry_submit_safe(doc, method):
    """Safe wrapper for stock entry submit"""
    if not check_hooks_enabled():
        return
    try:
        frappe.logger().info(f"Stock Entry {doc.name} submitted")
    except Exception as e:
        frappe.logger().error(f"Safe stock entry hook failed: {str(e)[:100]}")

def on_sales_order_submit_safe(doc, method):
    """Safe wrapper for sales order submit"""
    if not check_hooks_enabled():
        return
    try:
        frappe.logger().info(f"Sales Order {doc.name} submitted for {doc.company}")
    except Exception as e:
        frappe.logger().error(f"Safe sales order hook failed: {str(e)[:100]}")