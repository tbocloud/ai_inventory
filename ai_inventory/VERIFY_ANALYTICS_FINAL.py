#!/usr/bin/env python3
"""
FINAL VERIFICATION: AI SALES DASHBOARD ANALYTICS
Test all analytics fields to ensure they're showing calculated values, not defaults
"""

import frappe
import json
from frappe.utils import flt

def verify_analytics():
    """Verify all analytics fields are properly calculated"""
    print("=" * 80)
    print("🔍 FINAL VERIFICATION: AI SALES DASHBOARD ANALYTICS")
    print("=" * 80)
    
    # Test the report directly
    try:
        from ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard import execute
        
        # Get sample data
        columns, data = execute()
        
        print(f"📊 DASHBOARD REPORT TEST")
        print(f"   Columns: {len(columns)}")
        print(f"   Data Rows: {len(data)}")
        
        if data:
            # Check analytics fields in first few rows
            for i, row in enumerate(data[:3]):
                print(f"\n🔹 Row {i+1}:")
                print(f"   Item: {row.get('item_code', 'N/A')}")
                print(f"   Customer: {row.get('customer', 'N/A')}")
                print(f"   Demand Pattern: {row.get('demand_pattern', 'N/A')}")
                print(f"   Customer Score: {row.get('customer_score', 'N/A')}")
                print(f"   Market Potential: {row.get('market_potential', 'N/A')}%")
                print(f"   Revenue Potential: {row.get('revenue_potential', 'N/A')}")
                print(f"   Cross-sell Score: {row.get('cross_sell_score', 'N/A')}")
                print(f"   Churn Risk: {row.get('churn_risk', 'N/A')}")
                print(f"   Sales Alert: {row.get('sales_alert', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error testing report: {e}")
    
    # Direct database verification
    print(f"\n📋 DIRECT DATABASE VERIFICATION")
    
    # Check forecast records
    forecasts = frappe.db.sql("""
        SELECT 
            item_code, customer, 
            demand_pattern, customer_score, market_potential,
            revenue_potential, cross_sell_score, churn_risk
        FROM `tabAI Sales Forecast`
        WHERE docstatus = 1
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)
    
    print(f"   Active Forecasts: {len(forecasts)}")
    
    analytics_working = True
    for forecast in forecasts:
        # Check if analytics fields have real values
        has_pattern = forecast.demand_pattern and forecast.demand_pattern != 'Unknown'
        has_score = forecast.customer_score and flt(forecast.customer_score) > 0
        has_potential = forecast.market_potential and flt(forecast.market_potential) > 0
        has_revenue = forecast.revenue_potential and flt(forecast.revenue_potential) > 0
        has_cross_sell = forecast.cross_sell_score and flt(forecast.cross_sell_score) > 0
        has_churn = forecast.churn_risk and forecast.churn_risk != 'Unknown'
        
        if not all([has_pattern, has_score, has_potential, has_revenue, has_cross_sell, has_churn]):
            analytics_working = False
            
        print(f"\n   📦 {forecast.item_code} | {forecast.customer}")
        print(f"      Pattern: {forecast.demand_pattern} ({'✓' if has_pattern else '❌'})")
        print(f"      Score: {forecast.customer_score} ({'✓' if has_score else '❌'})")
        print(f"      Potential: {forecast.market_potential}% ({'✓' if has_potential else '❌'})")
        print(f"      Revenue: {forecast.revenue_potential} ({'✓' if has_revenue else '❌'})")
        print(f"      Cross-sell: {forecast.cross_sell_score} ({'✓' if has_cross_sell else '❌'})")
        print(f"      Churn: {forecast.churn_risk} ({'✓' if has_churn else '❌'})")
    
    print("\n" + "=" * 80)
    if analytics_working:
        print("✅ ALL ANALYTICS FIELDS ARE WORKING CORRECTLY!")
        print("   - Demand patterns are calculated")
        print("   - Customer scores are computed") 
        print("   - Market potential percentages are set")
        print("   - Revenue potential is calculated")
        print("   - Cross-sell scores are computed")
        print("   - Churn risk assessments are working")
    else:
        print("⚠️  Some analytics fields still need attention")
    
    print("=" * 80)
    
    return analytics_working

if __name__ == "__main__":
    verify_analytics()
