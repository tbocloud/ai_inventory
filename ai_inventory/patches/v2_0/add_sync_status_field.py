import frappe
from frappe.model.utils.rename_field import rename_field

def execute():
    """Add sync_status field to AI Financial Forecast if missing"""
    
    # Check if sync_status column exists
    if not frappe.db.has_column("AI Financial Forecast", "sync_status"):
        # Add the column manually
        frappe.db.sql("""
            ALTER TABLE `tabAI Financial Forecast` 
            ADD COLUMN `sync_status` varchar(140) DEFAULT 'Pending'
        """)
        
        # Update existing records to have Pending status
        frappe.db.sql("""
            UPDATE `tabAI Financial Forecast` 
            SET sync_status = 'Pending' 
            WHERE sync_status IS NULL OR sync_status = ''
        """)
        
        frappe.db.commit()
        print("Added sync_status field to AI Financial Forecast")
    
    # Reload DocType to ensure all fields are properly updated
    frappe.reload_doc("ai_inventory", "doctype", "ai_financial_forecast")
    frappe.reload_doc("ai_inventory", "doctype", "ai_forecast_sync_log")
    
    print("AI Financial Forecast sync field migration completed")
