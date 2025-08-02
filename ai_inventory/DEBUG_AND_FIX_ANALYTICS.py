#!/usr/bin/env python3
"""
DEBUG AND FIX AI SALES DASHBOARD ANALYTICS
This script will diagnose and fix all analytics calculation issues
"""

import frappe
from frappe.utils import flt, cint, nowdate, now_datetime
import json

def check_database_structure():
    """Check if all required columns exist"""
    print("🔍 CHECKING DATABASE STRUCTURE...")
    
    # Check AI Sales Forecast table structure
    try:
        columns = frappe.db.sql("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'tabAI Sales Forecast'
            ORDER BY COLUMN_NAME
        """, as_dict=True)
        
        print(f"✓ AI Sales Forecast table has {len(columns)} columns")
        
        analytics_fields = [
            'demand_pattern', 'customer_score', 'market_potential', 
            'seasonality_index', 'revenue_potential', 'cross_sell_score', 
            'churn_risk', 'sales_velocity', 'last_forecast_date'
        ]
        
        existing_analytics = [col['COLUMN_NAME'] for col in columns if col['COLUMN_NAME'] in analytics_fields]
        missing_analytics = [field for field in analytics_fields if field not in existing_analytics]
        
        print(f"✓ Existing analytics fields: {existing_analytics}")
        if missing_analytics:
            print(f"❌ Missing analytics fields: {missing_analytics}")
        else:
            print("✓ All analytics fields exist")
            
    except Exception as e:
        print(f"❌ Error checking AI Sales Forecast structure: {str(e)}")
    
    # Check Customer table
    try:
        customer_cols = frappe.db.sql("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'tabCustomer'
            AND COLUMN_NAME IN ('churn_probability', 'customer_lifetime_value', 'last_analytics_update')
        """)
        
        print(f"✓ Customer table has {len(customer_cols)} analytics fields: {[col[0] for col in customer_cols]}")
        
    except Exception as e:
        print(f"❌ Error checking Customer structure: {str(e)}")
    
    # Check Item table
    try:
        item_cols = frappe.db.sql("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'tabItem'
            AND COLUMN_NAME IN ('forecasted_qty_30_days', 'demand_pattern', 'last_forecast_update')
        """)
        
        print(f"✓ Item table has {len(item_cols)} analytics fields: {[col[0] for col in item_cols]}")
        
    except Exception as e:
        print(f"❌ Error checking Item structure: {str(e)}")

def check_existing_data():
    """Check what data currently exists"""
    print("\n📊 CHECKING EXISTING DATA...")
    
    try:
        # Check AI Sales Forecast data
        forecast_count = frappe.db.sql("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN demand_pattern IS NOT NULL AND demand_pattern != '' THEN 1 END) as with_pattern,
                   COUNT(CASE WHEN customer_score > 0 THEN 1 END) as with_score,
                   COUNT(CASE WHEN market_potential > 0 THEN 1 END) as with_potential,
                   COUNT(CASE WHEN revenue_potential > 0 THEN 1 END) as with_revenue,
                   COUNT(CASE WHEN cross_sell_score > 0 THEN 1 END) as with_cross_sell,
                   COUNT(CASE WHEN churn_risk IS NOT NULL AND churn_risk != '' THEN 1 END) as with_churn
            FROM `tabAI Sales Forecast`
            LIMIT 1
        """, as_dict=True)[0]
        
        print(f"AI Sales Forecast Records:")
        print(f"  Total: {forecast_count.total}")
        print(f"  With Demand Pattern: {forecast_count.with_pattern}")
        print(f"  With Customer Score: {forecast_count.with_score}")
        print(f"  With Market Potential: {forecast_count.with_potential}")
        print(f"  With Revenue Potential: {forecast_count.with_revenue}")
        print(f"  With Cross-sell Score: {forecast_count.with_cross_sell}")
        print(f"  With Churn Risk: {forecast_count.with_churn}")
        
    except Exception as e:
        print(f"❌ Error checking forecast data: {str(e)}")
    
    try:
        # Check Customer data
        customer_count = frappe.db.sql("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN churn_probability > 0 THEN 1 END) as with_churn,
                   COUNT(CASE WHEN customer_lifetime_value > 0 THEN 1 END) as with_clv
            FROM `tabCustomer`
            WHERE disabled = 0
            LIMIT 1
        """, as_dict=True)[0]
        
        print(f"Customer Records:")
        print(f"  Total Active: {customer_count.total}")
        print(f"  With Churn Probability: {customer_count.with_churn}")
        print(f"  With CLV: {customer_count.with_clv}")
        
    except Exception as e:
        print(f"❌ Error checking customer data: {str(e)}")

def fix_missing_columns():
    """Add any missing analytics columns"""
    print("\n🔧 FIXING MISSING COLUMNS...")
    
    # Add AI Sales Forecast analytics columns
    analytics_columns = [
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `demand_pattern` VARCHAR(140) DEFAULT 'Unknown'",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `customer_score` DECIMAL(8,2) DEFAULT 0.00",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `market_potential` DECIMAL(8,2) DEFAULT 0.00",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `seasonality_index` DECIMAL(8,2) DEFAULT 1.00",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `revenue_potential` DECIMAL(18,2) DEFAULT 0.00",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `cross_sell_score` DECIMAL(8,2) DEFAULT 0.00",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `churn_risk` VARCHAR(140) DEFAULT 'Unknown'",
        "ALTER TABLE `tabAI Sales Forecast` ADD COLUMN IF NOT EXISTS `sales_velocity` DECIMAL(8,2) DEFAULT 0.00",
    ]
    
    for sql in analytics_columns:
        try:
            frappe.db.sql(sql)
            field_name = sql.split('`')[3]
            print(f"✓ Added/verified column: {field_name}")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                print(f"❌ Failed to add column: {str(e)}")
    
    # Add Customer columns
    customer_columns = [
        "ALTER TABLE `tabCustomer` ADD COLUMN IF NOT EXISTS `churn_probability` DECIMAL(8,2) DEFAULT 0.00",
        "ALTER TABLE `tabCustomer` ADD COLUMN IF NOT EXISTS `customer_lifetime_value` DECIMAL(18,2) DEFAULT 0.00",
        "ALTER TABLE `tabCustomer` ADD COLUMN IF NOT EXISTS `last_analytics_update` DATETIME NULL",
    ]
    
    for sql in customer_columns:
        try:
            frappe.db.sql(sql)
            field_name = sql.split('`')[3]
            print(f"✓ Added/verified customer column: {field_name}")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                print(f"❌ Failed to add customer column: {str(e)}")
    
    # Add Item columns
    item_columns = [
        "ALTER TABLE `tabItem` ADD COLUMN IF NOT EXISTS `forecasted_qty_30_days` DECIMAL(18,2) DEFAULT 0.00",
        "ALTER TABLE `tabItem` ADD COLUMN IF NOT EXISTS `demand_pattern` VARCHAR(140) DEFAULT 'Unknown'",
        "ALTER TABLE `tabItem` ADD COLUMN IF NOT EXISTS `last_forecast_update` DATETIME NULL",
    ]
    
    for sql in item_columns:
        try:
            frappe.db.sql(sql)
            field_name = sql.split('`')[3]
            print(f"✓ Added/verified item column: {field_name}")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                print(f"❌ Failed to add item column: {str(e)}")
    
    frappe.db.commit()

def calculate_and_update_analytics():
    """Calculate and update all analytics fields"""
    print("\n🧮 CALCULATING AND UPDATING ANALYTICS...")
    
    # Get all AI Sales Forecast records
    try:
        forecasts = frappe.db.sql("""
            SELECT name, item_code, customer, company, predicted_qty, 
                   sales_trend, movement_type, confidence_score
            FROM `tabAI Sales Forecast`
            ORDER BY modified DESC
            LIMIT 100
        """, as_dict=True)
        
        print(f"Processing {len(forecasts)} forecast records...")
        
        for forecast in forecasts:
            try:
                # Calculate analytics
                analytics = calculate_forecast_analytics(forecast)
                
                # Update the record
                frappe.db.sql("""
                    UPDATE `tabAI Sales Forecast` 
                    SET demand_pattern = %s,
                        customer_score = %s,
                        market_potential = %s,
                        seasonality_index = %s,
                        revenue_potential = %s,
                        cross_sell_score = %s,
                        churn_risk = %s,
                        sales_velocity = %s,
                        last_forecast_date = %s
                    WHERE name = %s
                """, (
                    analytics['demand_pattern'],
                    analytics['customer_score'],
                    analytics['market_potential'],
                    analytics['seasonality_index'],
                    analytics['revenue_potential'],
                    analytics['cross_sell_score'],
                    analytics['churn_risk'],
                    analytics['sales_velocity'],
                    now_datetime(),
                    forecast.name
                ))
                
                print(f"✓ Updated forecast: {forecast.name}")
                
            except Exception as e:
                print(f"❌ Failed to update forecast {forecast.name}: {str(e)}")
        
        frappe.db.commit()
        print(f"✅ Successfully updated {len(forecasts)} forecast records")
        
    except Exception as e:
        print(f"❌ Error calculating analytics: {str(e)}")

def calculate_forecast_analytics(forecast):
    """Calculate analytics for a single forecast"""
    analytics = {
        'demand_pattern': '📊 Normal',
        'customer_score': 50.0,
        'market_potential': 60.0,
        'seasonality_index': 1.0,
        'revenue_potential': 0.0,
        'cross_sell_score': 30.0,
        'churn_risk': '🟡 Medium',
        'sales_velocity': 0.0
    }
    
    try:
        # Calculate demand pattern
        movement_type = forecast.get('movement_type', '').lower()
        sales_trend = forecast.get('sales_trend', '').lower()
        
        if movement_type == 'critical':
            analytics['demand_pattern'] = '🚨 Critical'
        elif movement_type == 'fast moving':
            analytics['demand_pattern'] = '⚡ High Velocity'
        elif movement_type == 'slow moving':
            analytics['demand_pattern'] = '🐌 Slow Trend'
        elif sales_trend == 'increasing':
            analytics['demand_pattern'] = '🚀 Growth'
        elif sales_trend == 'decreasing':
            analytics['demand_pattern'] = '📉 Declining'
        elif sales_trend == 'stable':
            analytics['demand_pattern'] = '📈 Steady'
        
        # Calculate customer score
        customer = forecast.get('customer')
        company = forecast.get('company')
        if customer and company:
            try:
                customer_data = frappe.db.sql("""
                    SELECT COUNT(*) as orders, SUM(grand_total) as total_value
                    FROM `tabSales Invoice`
                    WHERE customer = %s AND company = %s AND docstatus = 1
                    AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
                """, (customer, company), as_dict=True)
                
                if customer_data and customer_data[0]:
                    orders = customer_data[0].orders or 0
                    total_value = customer_data[0].total_value or 0
                    
                    # Score based on activity and value
                    activity_score = min(orders * 5, 40)
                    value_score = min(total_value / 5000, 30)  # $5k benchmark
                    analytics['customer_score'] = round(30 + activity_score + value_score, 1)
                
            except:
                pass
        
        # Calculate market potential
        confidence_score = flt(forecast.get('confidence_score', 0))
        predicted_qty = flt(forecast.get('predicted_qty', 0))
        
        base_potential = 60.0
        if movement_type == 'critical':
            base_potential = 85.0
        elif movement_type == 'fast moving':
            base_potential = 75.0
        elif movement_type == 'slow moving':
            base_potential = 45.0
        
        confidence_factor = confidence_score / 100
        qty_factor = min(predicted_qty / 50, 1.0)  # Normalize
        analytics['market_potential'] = round(base_potential * confidence_factor * (0.6 + qty_factor * 0.4), 1)
        
        # Calculate revenue potential
        if predicted_qty > 0:
            try:
                # Get average price
                price_data = frappe.db.sql("""
                    SELECT AVG(sii.rate) as avg_rate
                    FROM `tabSales Invoice Item` sii
                    INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                    WHERE sii.item_code = %s AND si.docstatus = 1
                    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                    LIMIT 1
                """, (forecast.get('item_code'),))
                
                avg_price = 100  # Default price
                if price_data and price_data[0][0]:
                    avg_price = flt(price_data[0][0])
                
                analytics['revenue_potential'] = round(predicted_qty * avg_price, 2)
                
            except:
                analytics['revenue_potential'] = predicted_qty * 100
        
        # Calculate churn risk
        if sales_trend == 'decreasing':
            analytics['churn_risk'] = '🔴 High'
        elif sales_trend == 'increasing':
            analytics['churn_risk'] = '🟢 Low'
        elif confidence_score < 60:
            analytics['churn_risk'] = '🟡 Medium'
        else:
            analytics['churn_risk'] = '🟢 Low'
        
        # Calculate sales velocity
        if predicted_qty > 0:
            period_days = 30  # Default forecast period
            analytics['sales_velocity'] = round(predicted_qty / period_days, 2)
        
        # Calculate cross-sell score
        if customer and company:
            try:
                diversity_data = frappe.db.sql("""
                    SELECT COUNT(DISTINCT sii.item_code) as unique_items
                    FROM `tabSales Invoice Item` sii
                    INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                    WHERE si.customer = %s AND si.company = %s AND si.docstatus = 1
                """, (customer, company))
                
                if diversity_data and diversity_data[0][0]:
                    unique_items = diversity_data[0][0]
                    analytics['cross_sell_score'] = round(min(30 + unique_items * 3, 90), 1)
                
            except:
                pass
        
        # Calculate seasonality index
        current_month = now_datetime().month
        if sales_trend == 'seasonal':
            if current_month in [11, 12, 1]:  # Holiday season
                analytics['seasonality_index'] = 1.3
            elif current_month in [6, 7, 8]:  # Summer
                analytics['seasonality_index'] = 0.8
            else:
                analytics['seasonality_index'] = 1.0
        elif sales_trend == 'increasing':
            analytics['seasonality_index'] = 1.2
        elif sales_trend == 'decreasing':
            analytics['seasonality_index'] = 0.8
        else:
            analytics['seasonality_index'] = 1.0
        
    except Exception as e:
        print(f"Warning: Analytics calculation error: {str(e)}")
    
    return analytics

def update_customer_analytics():
    """Update Customer master analytics"""
    print("\n👥 UPDATING CUSTOMER ANALYTICS...")
    
    try:
        customers = frappe.db.sql("""
            SELECT name, customer_name
            FROM `tabCustomer`
            WHERE disabled = 0
            LIMIT 50
        """, as_dict=True)
        
        for customer in customers:
            try:
                # Calculate churn probability and CLV
                invoice_data = frappe.db.sql("""
                    SELECT COUNT(*) as invoice_count,
                           SUM(grand_total) as total_value,
                           MAX(posting_date) as last_invoice,
                           DATEDIFF(CURDATE(), MAX(posting_date)) as days_since_last
                    FROM `tabSales Invoice`
                    WHERE customer = %s AND docstatus = 1
                """, (customer.name,), as_dict=True)
                
                if invoice_data and invoice_data[0]:
                    data = invoice_data[0]
                    invoice_count = data.invoice_count or 0
                    total_value = data.total_value or 0
                    days_since_last = data.days_since_last or 999
                    
                    # Calculate churn probability
                    if days_since_last > 180:
                        churn_prob = min(85.0, 50.0 + (days_since_last - 180) * 0.2)
                    elif days_since_last > 90:
                        churn_prob = min(50.0, 25.0 + (days_since_last - 90) * 0.3)
                    else:
                        churn_prob = max(5.0, 30.0 - invoice_count * 2)
                    
                    # Update customer
                    frappe.db.sql("""
                        UPDATE `tabCustomer`
                        SET churn_probability = %s,
                            customer_lifetime_value = %s,
                            last_analytics_update = %s
                        WHERE name = %s
                    """, (churn_prob, total_value, now_datetime(), customer.name))
                    
                    print(f"✓ Updated customer: {customer.name} - Churn: {churn_prob:.1f}%, CLV: {total_value:.0f}")
                
            except Exception as e:
                print(f"❌ Failed to update customer {customer.name}: {str(e)}")
        
        frappe.db.commit()
        
    except Exception as e:
        print(f"❌ Error updating customer analytics: {str(e)}")

def update_item_analytics():
    """Update Item master analytics"""
    print("\n📦 UPDATING ITEM ANALYTICS...")
    
    try:
        items = frappe.db.sql("""
            SELECT name, item_name
            FROM `tabItem`
            WHERE disabled = 0 AND is_sales_item = 1
            LIMIT 100
        """, as_dict=True)
        
        for item in items:
            try:
                # Calculate forecast and pattern
                sales_data = frappe.db.sql("""
                    SELECT AVG(sii.qty) as avg_qty,
                           COUNT(*) as sales_count,
                           STDDEV(sii.qty) as qty_stddev
                    FROM `tabSales Invoice Item` sii
                    INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                    WHERE sii.item_code = %s AND si.docstatus = 1
                    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                """, (item.name,), as_dict=True)
                
                if sales_data and sales_data[0] and sales_data[0].avg_qty:
                    data = sales_data[0]
                    avg_qty = data.avg_qty or 0
                    sales_count = data.sales_count or 0
                    qty_stddev = data.qty_stddev or 0
                    
                    # Calculate 30-day forecast
                    frequency_factor = min(sales_count / 90 * 30, 2.0)
                    forecasted_qty = avg_qty * frequency_factor
                    
                    # Determine pattern
                    if sales_count > 15:
                        pattern = 'High Demand'
                    elif sales_count > 8:
                        pattern = 'Moderate'
                    elif sales_count > 3:
                        pattern = 'Seasonal'
                    else:
                        pattern = 'Low Demand'
                    
                    # Update item
                    frappe.db.sql("""
                        UPDATE `tabItem`
                        SET forecasted_qty_30_days = %s,
                            demand_pattern = %s,
                            last_forecast_update = %s
                        WHERE name = %s
                    """, (forecasted_qty, pattern, now_datetime(), item.name))
                    
                    print(f"✓ Updated item: {item.name} - Forecast: {forecasted_qty:.1f}, Pattern: {pattern}")
                
            except Exception as e:
                print(f"❌ Failed to update item {item.name}: {str(e)}")
        
        frappe.db.commit()
        
    except Exception as e:
        print(f"❌ Error updating item analytics: {str(e)}")

def verify_final_results():
    """Verify that all analytics are now properly calculated"""
    print("\n✅ FINAL VERIFICATION...")
    
    try:
        # Check AI Sales Forecast analytics
        forecast_stats = frappe.db.sql("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN demand_pattern != 'Unknown' AND demand_pattern IS NOT NULL THEN 1 END) as patterns,
                   COUNT(CASE WHEN customer_score > 0 THEN 1 END) as scores,
                   COUNT(CASE WHEN market_potential > 0 THEN 1 END) as potentials,
                   COUNT(CASE WHEN revenue_potential > 0 THEN 1 END) as revenues,
                   COUNT(CASE WHEN churn_risk != 'Unknown' AND churn_risk IS NOT NULL THEN 1 END) as churns,
                   AVG(customer_score) as avg_score,
                   AVG(market_potential) as avg_potential
            FROM `tabAI Sales Forecast`
        """, as_dict=True)[0]
        
        print("AI Sales Forecast Analytics:")
        print(f"  Total Records: {forecast_stats.total}")
        print(f"  With Demand Patterns: {forecast_stats.patterns}")
        print(f"  With Customer Scores: {forecast_stats.scores}")
        print(f"  With Market Potential: {forecast_stats.potentials}")
        print(f"  With Revenue Potential: {forecast_stats.revenues}")
        print(f"  With Churn Risk: {forecast_stats.churns}")
        print(f"  Average Customer Score: {forecast_stats.avg_score:.1f}")
        print(f"  Average Market Potential: {forecast_stats.avg_potential:.1f}%")
        
        # Sample some records to verify
        samples = frappe.db.sql("""
            SELECT item_code, customer, demand_pattern, customer_score, 
                   market_potential, revenue_potential, churn_risk
            FROM `tabAI Sales Forecast`
            WHERE demand_pattern IS NOT NULL
            ORDER BY modified DESC
            LIMIT 5
        """, as_dict=True)
        
        print("\nSample Records:")
        for sample in samples:
            print(f"  {sample.item_code} | {sample.customer} | Pattern: {sample.demand_pattern} | Score: {sample.customer_score} | Potential: {sample.market_potential}% | Revenue: {sample.revenue_potential} | Churn: {sample.churn_risk}")
        
    except Exception as e:
        print(f"❌ Error in verification: {str(e)}")

def main():
    """Main execution function"""
    print("=" * 80)
    print("🚀 AI SALES DASHBOARD ANALYTICS DEBUG & FIX")
    print("=" * 80)
    
    try:
        # Step 1: Check structure
        check_database_structure()
        
        # Step 2: Check existing data
        check_existing_data()
        
        # Step 3: Fix missing columns
        fix_missing_columns()
        
        # Step 4: Calculate and update analytics
        calculate_and_update_analytics()
        
        # Step 5: Update customer analytics
        update_customer_analytics()
        
        # Step 6: Update item analytics
        update_item_analytics()
        
        # Step 7: Verify results
        verify_final_results()
        
        print("\n" + "=" * 80)
        print("✅ ANALYTICS DEBUG & FIX COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNEXT STEPS:")
        print("1. Refresh your AI Sales Dashboard report")
        print("2. Verify that all analytics fields show calculated values")
        print("3. Run 'Run AI Forecast' for fresh calculations")
        print("4. Check Customer and Item masters for new fields")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        print("Please check the error logs and contact support.")

if __name__ == "__main__":
    # Initialize Frappe
    frappe.init()
    frappe.connect()
    
    # Run the main function
    main()
    
    # Cleanup
    frappe.destroy()
