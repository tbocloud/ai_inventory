"""
Patch to add analytics fields to Customer and Item masters
Run this patch to add missing columns and populate initial data
"""

import frappe
from frappe.utils import flt, cint, nowdate, now_datetime
from datetime import datetime

def execute():
    """Main patch execution"""
    try:
        frappe.log_error("Starting master analytics fields patch", "Analytics Patch")
        
        # Add database columns
        add_customer_columns()
        add_item_columns()
        
        # Install custom fields
        install_custom_fields()
        
        # Populate initial data
        populate_customer_analytics()
        populate_item_analytics()
        
        frappe.log_error("Master analytics fields patch completed successfully", "Analytics Patch")
        
    except Exception as e:
        frappe.log_error(f"Master analytics fields patch failed: {str(e)}", "Analytics Patch Error")

def add_customer_columns():
    """Add Customer analytics columns"""
    try:
        # Add Customer fields if they don't exist
        customer_columns = [
            "ALTER TABLE `tabCustomer` ADD COLUMN IF NOT EXISTS `churn_probability` DECIMAL(8,2) DEFAULT 0.00",
            "ALTER TABLE `tabCustomer` ADD COLUMN IF NOT EXISTS `customer_lifetime_value` DECIMAL(18,2) DEFAULT 0.00", 
            "ALTER TABLE `tabCustomer` ADD COLUMN IF NOT EXISTS `last_analytics_update` DATETIME NULL"
        ]
        
        for sql in customer_columns:
            try:
                frappe.db.sql(sql)
            except Exception as e:
                if "Duplicate column name" not in str(e):
                    raise e
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Failed to add customer columns: {str(e)}", "Customer Columns Error")

def add_item_columns():
    """Add Item analytics columns"""
    try:
        # Add Item fields if they don't exist
        item_columns = [
            "ALTER TABLE `tabItem` ADD COLUMN IF NOT EXISTS `forecasted_qty_30_days` DECIMAL(18,2) DEFAULT 0.00",
            "ALTER TABLE `tabItem` ADD COLUMN IF NOT EXISTS `demand_pattern` VARCHAR(140) DEFAULT 'Unknown'",
            "ALTER TABLE `tabItem` ADD COLUMN IF NOT EXISTS `last_forecast_update` DATETIME NULL"
        ]
        
        for sql in item_columns:
            try:
                frappe.db.sql(sql)
            except Exception as e:
                if "Duplicate column name" not in str(e):
                    raise e
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Failed to add item columns: {str(e)}", "Item Columns Error")

def install_custom_fields():
    """Install custom fields from fixtures"""
    try:
        # Force reload custom fields
        frappe.reload_doc("ai_inventory", "custom", "customer", force=True)
        frappe.reload_doc("ai_inventory", "custom", "item", force=True)
        
        # Import custom field fixtures
        from frappe.core.doctype.data_import.data_import import import_doc
        
        # Import customer custom fields
        try:
            customer_fixture_path = frappe.get_app_path("ai_inventory", "ai_inventory", "custom", "customer.json")
            if frappe.utils.file_exists(customer_fixture_path):
                with open(customer_fixture_path, 'r') as f:
                    customer_data = frappe.parse_json(f.read())
                    for field in customer_data.get("custom_fields", []):
                        # Create or update custom field
                        if not frappe.db.exists("Custom Field", field.get("name")):
                            custom_field = frappe.get_doc({
                                "doctype": "Custom Field",
                                **field
                            })
                            custom_field.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Customer custom fields installation failed: {str(e)}")
        
        # Import item custom fields
        try:
            item_fixture_path = frappe.get_app_path("ai_inventory", "ai_inventory", "custom", "item.json")
            if frappe.utils.file_exists(item_fixture_path):
                with open(item_fixture_path, 'r') as f:
                    item_data = frappe.parse_json(f.read())
                    for field in item_data.get("custom_fields", []):
                        # Create or update custom field
                        if not frappe.db.exists("Custom Field", field.get("name")):
                            custom_field = frappe.get_doc({
                                "doctype": "Custom Field",
                                **field
                            })
                            custom_field.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Item custom fields installation failed: {str(e)}")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Custom fields installation failed: {str(e)}", "Custom Fields Error")

def populate_customer_analytics():
    """Populate Customer analytics with initial calculated values"""
    try:
        # Get customers that need analytics updates
        customers = frappe.db.sql("""
            SELECT name, customer_name 
            FROM `tabCustomer` 
            WHERE disabled = 0 
            AND (churn_probability IS NULL OR churn_probability = 0)
            LIMIT 100
        """, as_dict=True)
        
        for customer in customers:
            try:
                # Calculate basic churn probability
                last_invoice = frappe.db.sql("""
                    SELECT MAX(posting_date) as last_date, COUNT(*) as invoice_count,
                           SUM(grand_total) as total_value
                    FROM `tabSales Invoice`
                    WHERE customer = %s AND docstatus = 1
                    AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
                """, (customer.name,), as_dict=True)
                
                if last_invoice and last_invoice[0].last_date:
                    days_since = (datetime.now().date() - last_invoice[0].last_date).days
                    invoice_count = last_invoice[0].invoice_count or 0
                    total_value = last_invoice[0].total_value or 0
                    
                    # Simple churn calculation
                    if days_since > 180:
                        churn_prob = min(85.0, 50.0 + (days_since - 180) * 0.15)
                    elif days_since > 90:
                        churn_prob = min(50.0, 25.0 + (days_since - 90) * 0.25)
                    else:
                        churn_prob = max(5.0, 30.0 - invoice_count * 3)
                    
                    clv = total_value
                else:
                    churn_prob = 75.0
                    clv = 0.0
                
                # Update customer
                frappe.db.sql("""
                    UPDATE `tabCustomer` 
                    SET churn_probability = %s, 
                        customer_lifetime_value = %s,
                        last_analytics_update = %s
                    WHERE name = %s
                """, (churn_prob, clv, now_datetime(), customer.name))
                
            except Exception as e:
                frappe.log_error(f"Failed to update customer {customer.name}: {str(e)}")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Customer analytics population failed: {str(e)}", "Customer Analytics Error")

def populate_item_analytics():
    """Populate Item analytics with initial calculated values"""
    try:
        # Get items that need analytics updates
        items = frappe.db.sql("""
            SELECT name, item_name 
            FROM `tabItem` 
            WHERE disabled = 0 AND is_sales_item = 1
            AND (forecasted_qty_30_days IS NULL OR forecasted_qty_30_days = 0)
            LIMIT 200
        """, as_dict=True)
        
        for item in items:
            try:
                # Calculate basic forecast based on recent sales
                sales_result = frappe.db.sql("""
                    SELECT AVG(sii.qty) as avg_qty, COUNT(*) as sales_count,
                           STDDEV(sii.qty) as qty_stddev
                    FROM `tabSales Invoice Item` sii
                    INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                    WHERE sii.item_code = %s AND si.docstatus = 1
                    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                """, (item.name,), as_dict=True)
                
                if sales_result and sales_result[0].avg_qty:
                    avg_qty = sales_result[0].avg_qty or 0
                    sales_count = sales_result[0].sales_count or 0
                    qty_stddev = sales_result[0].qty_stddev or 0
                    
                    # Calculate 30-day forecast
                    frequency_factor = min(sales_count / 90 * 30, 2.5)
                    forecasted_qty = avg_qty * frequency_factor
                    
                    # Determine pattern based on consistency
                    if qty_stddev / max(avg_qty, 1) < 0.3:  # Low variation
                        pattern = 'Stable'
                    elif sales_count > 10:
                        pattern = 'High Demand'
                    elif sales_count > 5:
                        pattern = 'Moderate'
                    else:
                        pattern = 'Low Demand'
                else:
                    forecasted_qty = 0.0
                    pattern = 'No Data'
                
                # Update item
                frappe.db.sql("""
                    UPDATE `tabItem` 
                    SET forecasted_qty_30_days = %s, 
                        demand_pattern = %s,
                        last_forecast_update = %s
                    WHERE name = %s
                """, (forecasted_qty, pattern, now_datetime(), item.name))
                
            except Exception as e:
                frappe.log_error(f"Failed to update item {item.name}: {str(e)}")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Item analytics population failed: {str(e)}", "Item Analytics Error")
