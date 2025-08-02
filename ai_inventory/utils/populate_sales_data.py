#!/usr/bin/env python3
"""
Populate AI Sales Forecast with sample data for testing the dashboard
"""

import frappe
import random
from datetime import datetime, timedelta

def populate_sales_forecast_data():
    """Populate AI Sales Forecast with realistic sample data"""
    
    # Get actual data from system
    companies = [c.name for c in frappe.get_list("Company", fields=["name"])]
    territories = [t.name for t in frappe.get_list("Territory", fields=["name"])]
    
    # Sample data configurations
    items = ['ITEM-001', 'ITEM-002', 'ITEM-003', 'ITEM-004', 'ITEM-005']
    customers = ['CUST-001', 'CUST-002', 'CUST-003', 'CUST-004', 'CUST-005']
    sales_trends = ['Increasing', 'Decreasing', 'Stable', 'Volatile']
    movement_types = ['Fast Moving', 'Slow Moving', 'Non Moving', 'Critical']
    demand_patterns = ['Linear Growth', 'Exponential', 'Seasonal Peaks', 'Cyclical', 'Random Walk']
    churn_risks = ['🟢 Low', '🟡 Medium', '🔴 High', '❓ Unknown']
    
    frappe.db.sql("DELETE FROM `tabAI Sales Forecast`")
    frappe.db.commit()
    
    created_count = 0
    
    for i in range(50):  # Create 50 sample records
        try:
            # Create AI Sales Forecast record
            forecast = frappe.new_doc("AI Sales Forecast")
            
            # Basic Information
            forecast.item_code = random.choice(items)
            forecast.item_name = f"Sample Item {forecast.item_code}"
            forecast.item_group = "All Item Groups"
            forecast.customer = random.choice(customers)
            forecast.customer_name = f"Customer {forecast.customer}"
            forecast.territory = random.choice(territories) if territories else "All Territories"
            forecast.company = random.choice(companies) if companies else "Default Company"
            
            # Forecast Results
            forecast.forecast_period_days = random.randint(30, 90)
            forecast.forecast_date = datetime.now().date() + timedelta(days=random.randint(1, 30))
            forecast.predicted_qty = round(random.uniform(10, 500), 2)
            forecast.sales_trend = random.choice(sales_trends)
            forecast.movement_type = random.choice(movement_types)
            forecast.confidence_score = round(random.uniform(60, 95), 1)
            
            # Actual Data (for accuracy comparison)
            forecast.actual_qty = round(forecast.predicted_qty * random.uniform(0.8, 1.2), 2)
            forecast.accuracy_score = round(100 - abs(forecast.predicted_qty - forecast.actual_qty) / forecast.predicted_qty * 100, 1)
            forecast.sales_alert = random.choice([0, 1])
            forecast.last_forecast_date = datetime.now()
            
            # Advanced Analytics
            forecast.demand_pattern = random.choice(demand_patterns)
            forecast.customer_score = round(random.uniform(1, 10), 2)
            forecast.market_potential = round(random.uniform(10, 90), 1)
            forecast.seasonality_index = round(random.uniform(0.5, 2.0), 2)
            forecast.revenue_potential = round(forecast.predicted_qty * random.uniform(50, 200), 2)
            forecast.cross_sell_score = round(random.uniform(0, 1), 2)
            forecast.churn_risk = random.choice(churn_risks)
            forecast.sales_velocity = round(random.uniform(0.1, 5.0), 2)
            
            # Analysis Details
            forecast.historical_sales_data = f"Historical average: {round(random.uniform(100, 400), 2)} units per month"
            forecast.forecast_details = f"AI Model predicts {forecast.sales_trend.lower()} trend with {forecast.confidence_score}% confidence"
            
            # Settings
            forecast.auto_create_sales_order = random.choice([0, 1])
            forecast.delivery_days = random.randint(1, 14)
            forecast.trigger_source = random.choice(['Manual', 'Scheduled', 'API'])
            forecast.model_version = f"v{random.randint(1, 5)}.{random.randint(0, 9)}"
            forecast.horizon_days = forecast.forecast_period_days
            forecast.notes = f"Generated forecast for {forecast.item_code} targeting {forecast.customer}"
            
            forecast.insert(ignore_permissions=True)
            created_count += 1
            
            if created_count % 10 == 0:
                print(f"Created {created_count} AI Sales Forecast records...")
                
        except Exception as e:
            print(f"Error creating forecast record {i}: {str(e)}")
            continue
    
    frappe.db.commit()
    print(f"Successfully created {created_count} AI Sales Forecast records!")
    
    return {"status": "success", "created": created_count}

if __name__ == "__main__":
    populate_sales_forecast_data()
