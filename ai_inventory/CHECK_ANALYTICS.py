#!/usr/bin/env python3
"""
SIMPLE ANALYTICS VERIFICATION SCRIPT
Check if analytics fields are working in AI Sales Dashboard
"""

import frappe
from frappe.utils import flt

def main():
    """Simple verification of analytics status"""
    print("=" * 60)
    print("🔍 ANALYTICS VERIFICATION")
    print("=" * 60)
    
    try:
        # Check AI Sales Forecast records with analytics
        data = frappe.db.sql("""
            SELECT 
                item_code, customer, 
                demand_pattern, customer_score, market_potential,
                revenue_potential, cross_sell_score, churn_risk
            FROM `tabAI Sales Forecast`
            ORDER BY modified DESC
            LIMIT 10
        """, as_dict=True)
        
        print(f"📊 Found {len(data)} AI Sales Forecast records")
        
        if data:
            working_count = 0
            for row in data:
                has_analytics = (
                    row.demand_pattern and row.demand_pattern != 'Unknown' and
                    row.customer_score and flt(row.customer_score) > 0 and
                    row.market_potential and flt(row.market_potential) > 0 and
                    row.revenue_potential and flt(row.revenue_potential) > 0 and
                    row.cross_sell_score and flt(row.cross_sell_score) > 0 and
                    row.churn_risk and row.churn_risk != 'Unknown'
                )
                
                if has_analytics:
                    working_count += 1
                
                status = "✅" if has_analytics else "❌"
                print(f"{status} {row.item_code} | {row.customer}")
                print(f"    Pattern: {row.demand_pattern}")
                print(f"    Score: {row.customer_score}")
                print(f"    Potential: {row.market_potential}%")
                print(f"    Revenue: {row.revenue_potential}")
                print(f"    Cross-sell: {row.cross_sell_score}")
                print(f"    Churn: {row.churn_risk}")
                print()
            
            print(f"🎯 RESULT: {working_count}/{len(data)} records have working analytics")
            
            if working_count == len(data):
                print("✅ ALL ANALYTICS FIELDS ARE WORKING!")
            elif working_count > 0:
                print("⚠️  SOME ANALYTICS WORKING - May need refresh")
            else:
                print("❌ NO ANALYTICS WORKING - Need to run fix script")
        else:
            print("❌ No AI Sales Forecast records found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
