import frappe

def verify_dashboard_final():
    """Final verification that AI Sales Dashboard is fetching analytics fields correctly"""
    
    print("🔍 Final Dashboard Analytics Verification")
    print("=" * 60)
    
    # Get sample data directly from AI Sales Forecast
    print("\n1. Checking AI Sales Forecast data:")
    forecast_data = frappe.db.sql("""
        SELECT 
            name, customer, item_code,
            demand_pattern, customer_score, market_potential,
            revenue_potential, cross_sell_score, churn_risk,
            sales_alert, modified
        FROM `tabAI Sales Forecast`
        WHERE 
            demand_pattern IS NOT NULL 
            AND demand_pattern != '📊 Unknown'
            AND customer_score > 0
        LIMIT 5
    """, as_dict=True)
    
    if forecast_data:
        print(f"✅ Found {len(forecast_data)} records with analytics data")
        for i, record in enumerate(forecast_data[:3], 1):
            print(f"\n   Record {i}:")
            print(f"   Customer: {record.customer}")
            print(f"   Item: {record.item_code}")
            print(f"   Demand Pattern: {record.demand_pattern}")
            print(f"   Customer Score: {record.customer_score}")
            print(f"   Market Potential: {record.market_potential}%")
            print(f"   Revenue Potential: {record.revenue_potential}")
            print(f"   Cross-sell Score: {record.cross_sell_score}")
            print(f"   Churn Risk: {record.churn_risk}")
            print(f"   Sales Alert: {record.sales_alert}")
    else:
        print("❌ No analytics data found in AI Sales Forecast")
        return
    
    # Test the actual report function
    print("\n2. Testing AI Sales Dashboard Report:")
    try:
        from ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard import execute
        
        # Test with minimal filters
        filters = {
            'company': frappe.db.get_single_value('Global Defaults', 'default_company') or frappe.get_all('Company', limit=1)[0].name
        }
        
        columns, data = execute(filters)
        
        if data:
            print(f"✅ Report returned {len(data)} records")
            
            # Check first few records for analytics fields
            for i, row in enumerate(data[:3], 1):
                print(f"\n   Report Record {i}:")
                print(f"   Customer: {row.get('customer', 'N/A')}")
                print(f"   Item: {row.get('item_code', 'N/A')}")
                print(f"   Demand Pattern: {row.get('demand_pattern', 'N/A')}")
                print(f"   Customer Score: {row.get('customer_score', 'N/A')}")
                print(f"   Market Potential: {row.get('market_potential', 'N/A')}%")
                print(f"   Revenue Potential: {row.get('revenue_potential', 'N/A')}")
                print(f"   Cross-sell Score: {row.get('cross_sell_score', 'N/A')}")
                print(f"   Churn Risk: {row.get('churn_risk', 'N/A')}")
                print(f"   Sales Alert: {row.get('sales_alert', 'N/A')}")
                
                # Check if analytics fields have proper values
                analytics_ok = (
                    row.get('demand_pattern') not in ['📊 Unknown', None, ''] and
                    row.get('customer_score', 0) > 0 and
                    row.get('market_potential', 0) > 0 and
                    row.get('revenue_potential', 0) > 0 and
                    row.get('cross_sell_score', 0) > 0 and
                    row.get('churn_risk') not in ['❓ Unknown', None, '']
                )
                
                if analytics_ok:
                    print(f"   ✅ Analytics fields look good!")
                else:
                    print(f"   ❌ Some analytics fields still have default values")
            
            # Summary
            records_with_analytics = sum(1 for row in data if 
                row.get('demand_pattern') not in ['📊 Unknown', None, ''] and
                row.get('customer_score', 0) > 0 and
                row.get('market_potential', 0) > 0
            )
            
            print(f"\n📊 Summary:")
            print(f"   Total records: {len(data)}")
            print(f"   Records with analytics: {records_with_analytics}")
            print(f"   Analytics coverage: {(records_with_analytics/len(data)*100):.1f}%")
            
            if records_with_analytics > 0:
                print("✅ DASHBOARD IS NOW WORKING WITH ANALYTICS FIELDS!")
            else:
                print("❌ Dashboard still showing default values")
                
        else:
            print("❌ Report returned no data")
            
    except Exception as e:
        print(f"❌ Error testing report: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 Verification Complete!")
    
    return True
