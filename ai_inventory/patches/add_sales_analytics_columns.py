# AI Sales Dashboard Analytics Database Patch
# This patch adds missing columns to the AI Sales Forecast table

import frappe

def execute():
    """Add missing analytics columns to AI Sales Forecast table"""
    
    # Define the columns that need to be added
    columns_to_add = [
        ("sales_velocity", "DECIMAL(10,2) DEFAULT 0"),
        ("customer_score", "DECIMAL(5,2) DEFAULT 0"),
        ("revenue_potential", "DECIMAL(12,2) DEFAULT 0"),
        ("cross_sell_score", "DECIMAL(4,2) DEFAULT 0"),
        ("market_potential", "DECIMAL(5,2) DEFAULT 0"),
        ("demand_pattern", "VARCHAR(50) DEFAULT NULL"),
        ("churn_risk", "VARCHAR(20) DEFAULT NULL"),
        ("sales_alert", "INT(1) DEFAULT 0"),
    ]
    
    table_name = "`tabAI Sales Forecast`"
    
    for column_name, column_definition in columns_to_add:
        try:
            # Check if column exists
            exists = frappe.db.sql(f"""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'tabAI Sales Forecast' 
                AND COLUMN_NAME = '{column_name}'
            """)
            
            if exists and exists[0][0] == 0:
                # Column doesn't exist, add it
                frappe.db.sql(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN {column_name} {column_definition}
                """)
                print(f"✅ Added column: {column_name}")
            else:
                print(f"ℹ️  Column {column_name} already exists")
                
        except Exception as e:
            print(f"❌ Error adding column {column_name}: {str(e)}")
    
    # Commit the changes
    frappe.db.commit()
    print("🎉 Database patch completed!")
