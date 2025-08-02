"""
Force update analytics for AI Sales Dashboard
"""

import frappe
from frappe.utils import flt, cint, nowdate, now_datetime

@frappe.whitelist()
def force_update_analytics():
    """Force update all analytics in AI Sales Dashboard"""
    
    try:
        # Import the calculation functions
        from ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard import (
            calculate_demand_pattern_direct,
            calculate_customer_score_direct,
            calculate_market_potential_direct,
            calculate_seasonality_index_direct,
            calculate_revenue_potential_direct,
            calculate_cross_sell_score_direct,
            calculate_churn_risk_direct,
            calculate_sales_velocity_direct
        )
        
        results = {"success": True, "message": "Analytics updated successfully", "details": []}
        
        # Test the functions with sample data
        test_row = {
            'item_code': 'TEST-ITEM-001',
            'customer': 'Test Customer',
            'company': 'Test Company',
            'predicted_qty': 100,
            'movement_type': 'Fast Moving',
            'sales_trend': 'Increasing',
            'confidence_score': 85,
            'forecast_period_days': 30
        }
        
        results["details"].append("✅ Successfully imported calculation functions")
        
        # Test each function
        functions_to_test = [
            ('Demand Pattern', calculate_demand_pattern_direct),
            ('Customer Score', calculate_customer_score_direct),
            ('Market Potential', calculate_market_potential_direct),
            ('Seasonality Index', calculate_seasonality_index_direct),
            ('Revenue Potential', calculate_revenue_potential_direct),
            ('Cross-sell Score', calculate_cross_sell_score_direct),
            ('Churn Risk', calculate_churn_risk_direct),
            ('Sales Velocity', calculate_sales_velocity_direct)
        ]
        
        for name, func in functions_to_test:
            try:
                result = func(test_row)
                results["details"].append(f"✅ {name}: {result}")
            except Exception as e:
                results["details"].append(f"❌ {name}: ERROR - {e}")
        
        # Check if AI Sales Forecast table exists and has data
        if not frappe.db.table_exists("AI Sales Forecast"):
            results["details"].append("❌ AI Sales Forecast table does not exist!")
            results["success"] = False
            return results
        
        # Get count of records
        total_records = frappe.db.count("AI Sales Forecast")
        results["details"].append(f"📈 Total AI Sales Forecast records: {total_records}")
        
        if total_records == 0:
            results["details"].append("⚠️ No AI Sales Forecast records found. Creating sample data...")
            
            # Create a sample forecast record
            sample_forecast = frappe.get_doc({
                "doctype": "AI Sales Forecast",
                "item_code": "TEST-ITEM-001",
                "item_name": "Test Item",
                "customer": "Test Customer",
                "customer_name": "Test Customer",
                "company": "Test Company",
                "territory": "All Territories",
                "predicted_qty": 100,
                "sales_trend": "Increasing",
                "movement_type": "Fast Moving",
                "confidence_score": 85,
                "forecast_period_days": 30,
                "forecast_date": nowdate(),
                "sales_alert": 1
            })
            
            try:
                sample_forecast.insert(ignore_permissions=True)
                frappe.db.commit()
                results["details"].append("✅ Created sample forecast record")
                total_records = 1
            except Exception as e:
                results["details"].append(f"❌ Failed to create sample record: {e}")
                results["success"] = False
                return results
        
        # Update existing records with calculated analytics
        results["details"].append(f"🔄 Updating analytics for {total_records} records...")
        
        forecasts = frappe.get_all("AI Sales Forecast", 
            fields=["name", "item_code", "customer", "company", "predicted_qty", 
                   "sales_trend", "movement_type", "confidence_score", "forecast_period_days"],
            limit=100)
        
        updated_count = 0
        
        for forecast in forecasts:
            try:
                # Calculate all analytics
                analytics = {
                    'demand_pattern': calculate_demand_pattern_direct(forecast),
                    'customer_score': calculate_customer_score_direct(forecast),
                    'market_potential': calculate_market_potential_direct(forecast),
                    'seasonality_index': calculate_seasonality_index_direct(forecast),
                    'revenue_potential': calculate_revenue_potential_direct(forecast),
                    'cross_sell_score': calculate_cross_sell_score_direct(forecast),
                    'churn_risk': calculate_churn_risk_direct(forecast),
                    'sales_velocity': calculate_sales_velocity_direct(forecast),
                    'last_forecast_date': now_datetime()
                }
                
                # Update the record
                frappe.db.set_value("AI Sales Forecast", forecast.name, analytics)
                updated_count += 1
                
            except Exception as e:
                results["details"].append(f"❌ Failed to update record {forecast.name}: {e}")
        
        frappe.db.commit()
        results["details"].append(f"✅ Updated {updated_count} records with calculated analytics")
        
        # Clear cache to ensure fresh data
        frappe.clear_cache()
        frappe.db.commit()
        results["details"].append("✅ Cache cleared successfully")
        
        # Test the report execution
        try:
            from ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard import execute
            
            test_filters = {
                'from_date': '2024-01-01',
                'to_date': '2024-12-31'
            }
            
            columns, data, message, chart, summary = execute(test_filters)
            
            results["details"].append(f"✅ Report executed successfully:")
            results["details"].append(f"   - Columns: {len(columns)}")
            results["details"].append(f"   - Data rows: {len(data) if data else 0}")
            
            if data and len(data) > 0:
                first_row = data[0]
                results["details"].append(f"📊 Sample row analytics:")
                results["details"].append(f"   - Demand Pattern: {first_row.get('demand_pattern', 'NOT SET')}")
                results["details"].append(f"   - Customer Score: {first_row.get('customer_score', 'NOT SET')}")
                results["details"].append(f"   - Market Potential: {first_row.get('market_potential', 'NOT SET')}")
                results["details"].append(f"   - Revenue Potential: {first_row.get('revenue_potential', 'NOT SET')}")
                results["details"].append(f"   - Cross-sell Score: {first_row.get('cross_sell_score', 'NOT SET')}")
                results["details"].append(f"   - Churn Risk: {first_row.get('churn_risk', 'NOT SET')}")
                
        except Exception as e:
            results["details"].append(f"❌ Report execution failed: {e}")
            results["success"] = False
        
        results["details"].append("🎉 Analytics force update completed!")
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Force update failed: {e}",
            "details": [f"❌ Error: {e}"]
        }
