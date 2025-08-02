#!/usr/bin/env python3
"""
CLEAR ANALYTICS CACHE AND FORCE REFRESH
This script will clear all caches and force refresh analytics data
"""

import frappe

def clear_analytics_cache():
    """Clear all analytics-related caches"""
    print("🔄 CLEARING ANALYTICS CACHE...")
    
    try:
        # Clear Redis cache
        frappe.cache().delete_keys("ai_sales_dashboard")
        frappe.cache().delete_keys("analytics_*")
        
        # Clear report cache
        from frappe.desk.query_report import delete_saved_report
        try:
            frappe.db.sql("DELETE FROM `tabReport` WHERE ref_doctype = 'AI Sales Dashboard'")
        except:
            pass
        
        # Clear doctype cache
        frappe.clear_cache(doctype="AI Sales Forecast")
        frappe.clear_cache(doctype="Customer") 
        frappe.clear_cache(doctype="Item")
        
        # Force reload doctypes
        frappe.reload_doctype("AI Sales Forecast")
        frappe.reload_doctype("Customer")
        frappe.reload_doctype("Item")
        
        print("✅ Cache cleared successfully!")
        
    except Exception as e:
        print(f"⚠️ Cache clearing warning: {str(e)}")

def force_refresh_analytics():
    """Force refresh analytics data"""
    print("🔄 FORCE REFRESHING ANALYTICS DATA...")
    
    try:
        # Update all AI Sales Forecast records to trigger refresh
        frappe.db.sql("""
            UPDATE `tabAI Sales Forecast` 
            SET modified = NOW()
            WHERE docstatus = 1
        """)
        
        # Clear any cached report results
        frappe.db.sql("DELETE FROM `tabTabbed Dashboard` WHERE name LIKE '%AI%Dashboard%'")
        
        frappe.db.commit()
        print("✅ Analytics data refreshed!")
        
    except Exception as e:
        print(f"❌ Error refreshing analytics: {str(e)}")

def verify_current_data():
    """Verify the current data in database"""
    print("🔍 VERIFYING CURRENT DATA...")
    
    try:
        # Get sample data to verify
        samples = frappe.db.sql("""
            SELECT name, item_code, customer, demand_pattern, customer_score, 
                   market_potential, revenue_potential, churn_risk, modified
            FROM `tabAI Sales Forecast`
            WHERE docstatus = 1
            ORDER BY modified DESC
            LIMIT 3
        """, as_dict=True)
        
        print(f"📊 Found {len(samples)} recent forecast records:")
        for sample in samples:
            print(f"  🔹 {sample.name}")
            print(f"     Item: {sample.item_code} | Customer: {sample.customer}")
            print(f"     Pattern: {sample.demand_pattern}")
            print(f"     Score: {sample.customer_score}")
            print(f"     Potential: {sample.market_potential}%")
            print(f"     Revenue: {sample.revenue_potential}")
            print(f"     Churn: {sample.churn_risk}")
            print(f"     Modified: {sample.modified}")
            print()
        
        # Check if data looks good
        has_good_data = all([
            sample.demand_pattern and sample.demand_pattern != 'Unknown',
            sample.customer_score and sample.customer_score > 0,
            sample.market_potential and sample.market_potential > 0
        ] for sample in samples)
        
        if has_good_data:
            print("✅ Data looks good in database!")
        else:
            print("⚠️ Data may still have default values")
            
        return has_good_data
        
    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🔄 ANALYTICS CACHE CLEAR & FORCE REFRESH")
    print("=" * 60)
    
    # Step 1: Clear cache
    clear_analytics_cache()
    
    # Step 2: Force refresh
    force_refresh_analytics()
    
    # Step 3: Verify data
    data_good = verify_current_data()
    
    print("=" * 60)
    if data_good:
        print("✅ CACHE CLEARED & DATA REFRESHED!")
        print("\n📋 NEXT STEPS:")
        print("1. Open AI Sales Dashboard in browser")
        print("2. Hard refresh (Ctrl+F5 or Cmd+Shift+R)")
        print("3. Check if analytics fields now show calculated values")
        print("4. If still showing cached data, try incognito/private mode")
    else:
        print("⚠️ DATA NEEDS RECALCULATION")
        print("\nRun the DEBUG_AND_FIX_ANALYTICS script again if needed")
    print("=" * 60)

if __name__ == "__main__":
    main()
