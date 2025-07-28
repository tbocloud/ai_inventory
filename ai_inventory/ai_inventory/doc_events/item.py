# ai_inventory/doc_events/item.py

import frappe
from frappe.utils import nowdate

def create_forecast_record(doc, method):
    """Create AI Inventory Forecast record when new item is created"""
    try:
        # Only create for stock items
        if not doc.is_stock_item:
            return
            
        # Get default warehouse (first warehouse alphabetically)
        default_warehouse = frappe.db.get_value("Warehouse", 
            {"disabled": 0}, "name", order_by="name")
        
        if not default_warehouse:
            return
            
        # Check if forecast record already exists
        existing_forecast = frappe.db.exists("AI Inventory Forecast", {
            "item_code": doc.name,
            "warehouse": default_warehouse
        })
        
        if existing_forecast:
            return
            
        # Create forecast record
        forecast_doc = frappe.get_doc({
            "doctype": "AI Inventory Forecast",
            "item_code": doc.name,
            "warehouse": default_warehouse,
            "forecast_period_days": 30
        })
        
        forecast_doc.insert(ignore_permissions=True)
        
        frappe.msgprint(f"AI Forecast record created for {doc.name}")
        
    except Exception as e:
        frappe.log_error(f"Failed to create forecast record for {doc.name}: {str(e)}")

def update_forecast_records(doc, method):
    """Update existing forecast records when item is updated"""
    try:
        # Get all forecast records for this item
        forecast_records = frappe.get_all("AI Inventory Forecast", 
            filters={"item_code": doc.name}, 
            fields=["name"])
        
        # Update each forecast record
        for record in forecast_records:
            forecast_doc = frappe.get_doc("AI Inventory Forecast", record.name)
            forecast_doc.save()  # This will trigger the forecast update
            
    except Exception as e:
        frappe.log_error(f"Failed to update forecast records for {doc.name}: {str(e)}")

# ai_inventory/doc_events/stock_ledger.py

import frappe
from frappe.utils import nowdate, now

def update_forecast_on_stock_change(doc, method):
    """Update AI forecast when stock levels change"""
    try:
        # Only process for actual stock movements
        if not doc.actual_qty or doc.actual_qty == 0:
            return
            
        # Get existing forecast record
        forecast_record = frappe.db.get_value("AI Inventory Forecast", {
            "item_code": doc.item_code,
            "warehouse": doc.warehouse
        }, "name")
        
        if not forecast_record:
            return
            
        # Update the forecast record
        forecast_doc = frappe.get_doc("AI Inventory Forecast", forecast_record)
        
        # Update current stock
        forecast_doc.current_stock = doc.qty_after_transaction
        
        # If this is a significant stock movement, re-run forecast
        movement_threshold = abs(doc.actual_qty)
        if movement_threshold > (forecast_doc.predicted_consumption / 30):  # More than daily average
            forecast_doc.run_ai_forecast()
            
        forecast_doc.save()
        
        # Check for immediate reorder alerts
        if forecast_doc.reorder_alert and doc.actual_qty < 0:  # Stock going out
            send_real_time_alert(forecast_doc)
            
    except Exception as e:
        frappe.log_error(f"Failed to update forecast on stock change: {str(e)}")

def send_real_time_alert(forecast_doc):
    """Send real-time alert for critical stock levels"""
    try:
        # Only send if stock is critically low (below 50% of reorder level)
        if forecast_doc.current_stock > (forecast_doc.reorder_level * 0.5):
            return
            
        # Send notification
        frappe.publish_realtime(
            event="stock_alert",
            message={
                "item_code": forecast_doc.item_code,
                "warehouse": forecast_doc.warehouse,
                "current_stock": forecast_doc.current_stock,
                "reorder_level": forecast_doc.reorder_level,
                "alert_type": "critical"
            },
            user="stock_managers"
        )
        
    except Exception as e:
        frappe.log_error(f"Real-time alert failed: {str(e)}")

# ai_inventory/doc_events/purchase_order.py

import frappe
from frappe.utils import add_days, nowdate

def update_forecast_on_po_submit(doc, method):
    """Update forecast records when Purchase Order is submitted"""
    try:
        for item in doc.items:
            # Get forecast record
            forecast_record = frappe.db.get_value("AI Inventory Forecast", {
                "item_code": item.item_code,
                "warehouse": item.warehouse or doc.set_warehouse
            }, "name")
            
            if not forecast_record:
                continue
                
            forecast_doc = frappe.get_doc("AI Inventory Forecast", forecast_record)
            
            # Add note about pending PO
            po_note = f"PO {doc.name} submitted for {item.qty} units (Expected: {item.schedule_date})"
            
            if forecast_doc.forecast_details:
                forecast_doc.forecast_details += f"\n\n📋 {po_note}"
            else:
                forecast_doc.forecast_details = po_note
                
            forecast_doc.save()
            
            # If this PO addresses the reorder alert, update the alert status
            if forecast_doc.reorder_alert and item.qty >= forecast_doc.suggested_qty:
                forecast_doc.reorder_alert = 0
                forecast_doc.save()
                
                # Notify about PO creation
                frappe.publish_realtime(
                    event="po_created",
                    message={
                        "item_code": item.item_code,
                        "po_name": doc.name,
                        "qty": item.qty,
                        "message": f"Purchase Order created for {item.item_code} - Reorder alert cleared"
                    },
                    user="stock_managers"
                )
                
    except Exception as e:
        frappe.log_error(f"Failed to update forecast on PO submit: {str(e)}")

# ai_inventory/doc_events/purchase_receipt.py

import frappe
from frappe.utils import nowdate

def update_stock_after_receipt(doc, method):
    """Update forecast after purchase receipt"""
    try:
        for item in doc.items:
            # Get forecast record
            forecast_record = frappe.db.get_value("AI Inventory Forecast", {
                "item_code": item.item_code,
                "warehouse": item.warehouse
            }, "name")
            
            if not forecast_record:
                continue
                
            forecast_doc = frappe.get_doc("AI Inventory Forecast", forecast_record)
            
            # Update last purchase date
            forecast_doc.last_purchase_date = doc.posting_date
            
            # Add receipt note
            receipt_note = f"Received {item.qty} units on {doc.posting_date} (Receipt: {doc.name})"
            
            if forecast_doc.forecast_details:
                forecast_doc.forecast_details += f"\n\n📦 {receipt_note}"
            else:
                forecast_doc.forecast_details = receipt_note
                
            # Re-run forecast with updated stock
            forecast_doc.run_ai_forecast()
            forecast_doc.save()
            
    except Exception as e:
        frappe.log_error(f"Failed to update forecast after receipt: {str(e)}")

# ai_inventory/doc_events/bin.py

import frappe
from frappe.utils import flt

def monitor_stock_levels(doc, method):
    """Monitor stock levels in real-time through Bin updates"""
    try:
        # Only process if actual_qty changed significantly
        if hasattr(doc, '_doc_before_save'):
            old_qty = flt(doc._doc_before_save.actual_qty)
            new_qty = flt(doc.actual_qty)
            qty_change = abs(new_qty - old_qty)
            
            # Only process significant changes (more than 1 unit or 5% change)
            if qty_change < 1 and qty_change < (old_qty * 0.05):
                return
        
        # Get forecast record
        forecast_record = frappe.db.get_value("AI Inventory Forecast", {
            "item_code": doc.item_code,
            "warehouse": doc.warehouse
        }, ["name", "reorder_level", "movement_type"])
        
        if not forecast_record:
            return
            
        forecast_name, reorder_level, movement_type = forecast_record
        
        # Check for critical stock levels
        if doc.actual_qty <= reorder_level and movement_type in ["Fast Moving", "Critical"]:
            # Send immediate notification
            send_critical_stock_notification(doc, forecast_name, reorder_level)
            
            # Update forecast record
            frappe.db.set_value("AI Inventory Forecast", forecast_name, {
                "current_stock": doc.actual_qty,
                "reorder_alert": 1
            })
            
    except Exception as e:
        frappe.log_error(f"Stock level monitoring failed: {str(e)}")

def send_critical_stock_notification(bin_doc, forecast_name, reorder_level):
    """Send real-time critical stock notification"""
    try:
        # Get item details
        item_details = frappe.db.get_value("Item", bin_doc.item_code, 
            ["item_name", "item_group"], as_dict=True)
        
        # Create notification
        notification_data = {
            "type": "alert",
            "title": f"Critical Stock: {bin_doc.item_code}",
            "message": f"{item_details.item_name} stock at {bin_doc.warehouse} is {bin_doc.actual_qty} units (below reorder level: {reorder_level})",
            "indicator": "red",
            "item_code": bin_doc.item_code,
            "warehouse": bin_doc.warehouse,
            "current_stock": bin_doc.actual_qty,
            "reorder_level": reorder_level,
            "forecast_link": f"/app/ai-inventory-forecast/{forecast_name}"
        }
        
        # Send real-time notification to stock managers
        frappe.publish_realtime(
            event="critical_stock_alert",
            message=notification_data,
            room="stock_managers"
        )
        
        # Also create a system notification
        for user in get_stock_managers():
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": notification_data["title"],
                "email_content": notification_data["message"],
                "for_user": user,
                "type": "Alert",
                "document_type": "AI Inventory Forecast",
                "document_name": forecast_name
            }).insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Critical stock notification failed: {str(e)}")

def get_stock_managers():
    """Get list of users with Stock Manager role"""
    return frappe.get_all("Has Role", 
        filters={"role": "Stock Manager", "parenttype": "User"}, 
        pluck="parent")

# ai_inventory/doc_events/warehouse.py

import frappe

def create_forecast_for_warehouse_items(doc, method):
    """Create forecast records for all items when new warehouse is created"""
    try:
        if doc.disabled:
            return
            
        # Get all active stock items
        items = frappe.get_all("Item", 
            filters={"disabled": 0, "is_stock_item": 1}, 
            fields=["name"])
        
        created_count = 0
        for item in items[:50]:  # Limit to 50 items to avoid timeout
            # Check if forecast already exists
            exists = frappe.db.exists("AI Inventory Forecast", {
                "item_code": item.name,
                "warehouse": doc.name
            })
            
            if not exists:
                forecast_doc = frappe.get_doc({
                    "doctype": "AI Inventory Forecast",
                    "item_code": item.name,
                    "warehouse": doc.name,
                    "forecast_period_days": 30
                })
                forecast_doc.insert(ignore_permissions=True)
                created_count += 1
                
        if created_count > 0:
            frappe.msgprint(f"Created {created_count} AI Forecast records for warehouse {doc.name}")
            
    except Exception as e:
        frappe.log_error(f"Failed to create forecasts for warehouse {doc.name}: {str(e)}")

# ai_inventory/doc_events/stock_entry.py

import frappe
from frappe.utils import nowdate

def update_forecast_on_stock_entry(doc, method):
    """Update forecast when stock entry is submitted"""
    try:
        for item in doc.items:
            # Skip if no warehouse specified
            if not item.s_warehouse and not item.t_warehouse:
                continue
                
            # Handle source warehouse (stock going out)
            if item.s_warehouse:
                update_warehouse_forecast(item.item_code, item.s_warehouse, -item.qty, doc)
                
            # Handle target warehouse (stock coming in)
            if item.t_warehouse:
                update_warehouse_forecast(item.item_code, item.t_warehouse, item.qty, doc)
                
    except Exception as e:
        frappe.log_error(f"Failed to update forecast on stock entry: {str(e)}")

def update_warehouse_forecast(item_code, warehouse, qty_change, stock_entry_doc):
    """Update forecast for specific warehouse"""
    try:
        forecast_record = frappe.db.get_value("AI Inventory Forecast", {
            "item_code": item_code,
            "warehouse": warehouse
        }, "name")
        
        if not forecast_record:
            return
            
        forecast_doc = frappe.get_doc("AI Inventory Forecast", forecast_record)
        
        # Add stock entry note
        entry_note = f"Stock Entry {stock_entry_doc.name}: {'+' if qty_change > 0 else ''}{qty_change} units ({stock_entry_doc.stock_entry_type})"
        
        if forecast_doc.forecast_details:
            forecast_doc.forecast_details += f"\n\n📋 {entry_note}"
        else:
            forecast_doc.forecast_details = entry_note
            
        # If significant movement, re-run forecast
        if abs(qty_change) > (forecast_doc.predicted_consumption / 30):  # More than daily average
            forecast_doc.run_ai_forecast()
            
        forecast_doc.save()
        
    except Exception as e:
        frappe.log_error(f"Failed to update warehouse forecast: {str(e)}")

# ai_inventory/doc_events/sales_order.py

import frappe
from frappe.utils import add_days, getdate

def analyze_sales_demand(doc, method):
    """Analyze sales order patterns for demand forecasting"""
    try:
        for item in doc.items:
            # Get forecast record
            forecast_record = frappe.db.get_value("AI Inventory Forecast", {
                "item_code": item.item_code,
                "warehouse": item.warehouse or doc.set_warehouse
            }, "name")
            
            if not forecast_record:
                continue
                
            forecast_doc = frappe.get_doc("AI Inventory Forecast", forecast_record)
            
            # Calculate demand impact
            delivery_date = getdate(item.delivery_date or doc.delivery_date)
            demand_note = f"Sales Order {doc.name}: {item.qty} units (Delivery: {delivery_date})"
            
            if forecast_doc.forecast_details:
                forecast_doc.forecast_details += f"\n\n🛒 {demand_note}"
            else:
                forecast_doc.forecast_details = demand_note
                
            # If delivery is soon and stock is low, create urgent alert
            days_to_delivery = (delivery_date - getdate()).days
            if days_to_delivery <= 7 and forecast_doc.current_stock < item.qty:
                create_urgent_procurement_alert(forecast_doc, item, doc, days_to_delivery)
                
            forecast_doc.save()
            
    except Exception as e:
        frappe.log_error(f"Failed to analyze sales demand: {str(e)}")

def create_urgent_procurement_alert(forecast_doc, sales_item, sales_order, days_to_delivery):
    """Create urgent procurement alert for sales order fulfillment"""
    try:
        alert_doc = frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"🚨 URGENT: Insufficient stock for SO {sales_order.name}",
            "email_content": f"""
            <h3>Urgent Procurement Required</h3>
            <p><strong>Sales Order:</strong> {sales_order.name}</p>
            <p><strong>Item:</strong> {sales_item.item_code}</p>
            <p><strong>Required Qty:</strong> {sales_item.qty}</p>
            <p><strong>Current Stock:</strong> {forecast_doc.current_stock}</p>
            <p><strong>Shortage:</strong> {sales_item.qty - forecast_doc.current_stock}</p>
            <p><strong>Delivery Date:</strong> {sales_item.delivery_date} ({days_to_delivery} days)</p>
            
            <p><strong>Immediate Action Required:</strong></p>
            <ul>
                <li>Expedite pending purchase orders</li>
                <li>Contact suppliers for urgent delivery</li>
                <li>Consider stock transfer from other warehouses</li>
                <li>Review delivery commitments with customer</li>
            </ul>
            """,
            "type": "Alert",
            "document_type": "AI Inventory Forecast",
            "document_name": forecast_doc.name
        })
        
        # Send to all stock and purchase managers
        managers = frappe.get_all("Has Role", 
            filters={"role": ["in", ["Stock Manager", "Purchase Manager"]], "parenttype": "User"}, 
            pluck="parent")
        
        for manager in managers:
            alert_doc.for_user = manager
            alert_doc.insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Failed to create urgent procurement alert: {str(e)}")

# ai_inventory/doc_events/common.py

import frappe
from frappe.utils import now, add_days

def log_forecast_event(item_code, warehouse, event_type, details, doc_name=None):
    """Common function to log forecast-related events"""
    try:
        event_log = frappe.get_doc({
            "doctype": "AI Forecast Event Log",
            "item_code": item_code,
            "warehouse": warehouse,
            "event_type": event_type,
            "event_details": details,
            "related_document": doc_name,
            "timestamp": now()
        })
        event_log.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Failed to log forecast event: {str(e)}")

def get_forecast_settings():
    """Get AI Inventory Forecast settings"""
    settings = frappe.get_single("AI Inventory Settings")
    return {
        "auto_forecast_enabled": settings.get("auto_forecast_enabled", 1),
        "notification_enabled": settings.get("notification_enabled", 1),
        "critical_stock_threshold": settings.get("critical_stock_threshold", 0.5),
        "forecast_frequency": settings.get("forecast_frequency", "Daily")
    }

def should_process_forecast_event(item_code, warehouse):
    """Check if forecast event should be processed based on settings"""
    settings = get_forecast_settings()
    
    if not settings["auto_forecast_enabled"]:
        return False
        
    # Check if item is excluded from auto-forecasting
    item_settings = frappe.db.get_value("Item", item_code, 
        ["ai_forecast_enabled", "disabled", "is_stock_item"], as_dict=True)
    
    if not item_settings:
        return False
        
    return (item_settings.get("ai_forecast_enabled", 1) and 
            not item_settings.get("disabled", 0) and 
            item_settings.get("is_stock_item", 0))

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
                    frappe.log_error(f"Batch forecast update failed for {update['forecast_id']}: {str(e)}")
                    
            # Commit after each batch
            frappe.db.commit()
            
        # Clear the queue
        frappe.cache().delete("forecast_update_queue")
        
    except Exception as e:
        frappe.log_error(f"Forecast update queue processing failed: {str(e)}")

def add_to_forecast_update_queue(forecast_id, priority="normal"):
    """Add forecast to update queue for batch processing"""
    try:
        queue = frappe.cache().get("forecast_update_queue") or []
        
        # Avoid duplicates
        if not any(item["forecast_id"] == forecast_id for item in queue):
            queue.append({
                "forecast_id": forecast_id,
                "priority": priority,
                "queued_at": now()
            })
            
            # Sort by priority (high priority first)
            queue.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
            
            frappe.cache().set("forecast_update_queue", queue, expires_in_sec=3600)
            
    except Exception as e:
        frappe.log_error(f"Failed to add to forecast update queue: {str(e)}")