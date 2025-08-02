# ai_inventory/ai_inventory/report/ai_sales_dashboard/ai_sales_dashboard.py
# ENHANCED AI SALES DASHBOARD WITH DATA SCIENCE & ML ANALYTICS

import frappe
from frappe.utils import flt, nowdate, add_days, getdate, cint, now_datetime
from frappe import _
import json
from datetime import datetime, timedelta
from collections import defaultdict
import math

# Safe imports for data science libraries
try:
    import numpy as np
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def execute(filters=None):
    """Main execution function for the report"""
    try:
        columns, data = [], []
        
        if not filters:
            filters = {}
        
        # Validate date filters
        filters = validate_and_clean_filters(filters)
        
        columns = get_enhanced_columns()
        data = get_enhanced_data(filters)
        chart = get_advanced_chart_data(filters)
        summary = get_smart_summary_data(filters)
        
        return columns, data, None, chart, summary
        
    except Exception as e:
        frappe.log_error(f"AI Sales Dashboard execution error: {str(e)}")
        frappe.msgprint(f"Error in AI Sales Dashboard: {str(e)}")
        
        # Return empty structure on error
        return get_enhanced_columns(), [], None, {"data": {"labels": [], "datasets": []}}, [
            {"value": "Error", "label": "Report Error", "datatype": "Data", "indicator": "Red"}
        ]

def validate_and_clean_filters(filters):
    """Validate and clean filter inputs with smart defaults"""
    try:
        cleaned_filters = filters.copy() if filters else {}
        
        # Set default date range if not provided (last 90 days)
        if not cleaned_filters.get("from_date"):
            cleaned_filters["from_date"] = add_days(nowdate(), -90)
        
        if not cleaned_filters.get("to_date"):
            cleaned_filters["to_date"] = nowdate()
        
        # Ensure from_date is not after to_date
        if getdate(cleaned_filters["from_date"]) > getdate(cleaned_filters["to_date"]):
            cleaned_filters["from_date"], cleaned_filters["to_date"] = cleaned_filters["to_date"], cleaned_filters["from_date"]
        
        # Convert string values to proper types
        if cleaned_filters.get("sales_alert"):
            cleaned_filters["sales_alert"] = cint(cleaned_filters["sales_alert"])
        
        if cleaned_filters.get("low_confidence"):
            cleaned_filters["low_confidence"] = cint(cleaned_filters["low_confidence"])
        
        return cleaned_filters
        
    except Exception as e:
        frappe.log_error(f"Filter validation error: {str(e)}")
        return {"from_date": add_days(nowdate(), -90), "to_date": nowdate()}

def get_enhanced_columns():
    """Enhanced columns with sales data science metrics"""
    return [
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 300
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 150
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 300
        },
        {
            "label": _("Predicted Consumption"),
            "fieldname": "predicted_qty",
            "fieldtype": "Float",
            "width": 170,
            "precision": 2
        },
        {
            "label": _("Demand Trend"),
            "fieldname": "sales_trend",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Seasonality Score"),
            "fieldname": "seasonality_index",
            "fieldtype": "Float",
            "width": 150,
            "precision": 2
        },
        {
            "label": _("Volatility Index"),
            "fieldname": "volatility_index",
            "fieldtype": "Float",
            "width": 140,
            "precision": 3
        },
        {
            "label": _("Reorder Level"),
            "fieldname": "reorder_level",
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "label": _("Suggested Qty"),
            "fieldname": "suggested_qty",
            "fieldtype": "Float",
            "width": 130,
            "precision": 2
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Demand Pattern"),
            "fieldname": "demand_pattern",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Customer Score"),
            "fieldname": "customer_score",
            "fieldtype": "Float",
            "width": 150,
            "precision": 1
        },
        {
            "label": _("Market Potential %"),
            "fieldname": "market_potential",
            "fieldtype": "Percent",
            "width": 180
        },
        {
            "label": _("Seasonality Index"),
            "fieldname": "seasonality_index",
            "fieldtype": "Float",
            "width": 180,
            "precision": 2
        },
        {
            "label": _("AI Confidence %"),
            "fieldname": "confidence_score",
            "fieldtype": "Percent",
            "width": 180,
        },
        {
            "label": _("Revenue Potential"),
            "fieldname": "revenue_potential",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Cross-sell Score"),
            "fieldname": "cross_sell_score",
            "fieldtype": "Float",
            "width": 130,
            "precision": 1
        },
        {
            "label": _("Churn Risk"),
            "fieldname": "churn_risk",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Customer Churn Probability (%)"),
            "fieldname": "customer_churn_probability",
            "fieldtype": "Float",
            "width": 180,
            "precision": 2
        },
        {
            "label": _("Item Forecasted Qty (Next 30 Days)"),
            "fieldname": "item_forecasted_qty_30_days",
            "fieldtype": "Float",
            "width": 220,
            "precision": 2
        },
        {
            "label": _("Sales Alert"),
            "fieldname": "sales_alert",
            "fieldtype": "Check",
            "width": 120
        },
        {
            "label": _("Forecast Date"),
            "fieldname": "forecast_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Last Updated"),
            "fieldname": "last_forecast_date",
            "fieldtype": "Datetime",
            "width": 180
        }
    ]

def get_enhanced_data(filters):
    """Enhanced data retrieval with sales data science calculations"""
    try:
        # Check if AI Sales Forecast table exists
        if not frappe.db.table_exists("AI Sales Forecast"):
            frappe.msgprint(_("AI Sales Forecast table not found. Please ensure the doctype is installed."))
            return []
        
        conditions = get_enhanced_conditions(filters)
        
        # Simplified base query - only use fields that exist in database
        base_query = f"""
            SELECT 
                asf.item_code,
                COALESCE(asf.item_name, asf.item_code) as item_name,
                asf.customer,
                COALESCE(asf.customer_name, asf.customer) as customer_name,
                COALESCE(asf.territory, 'All Territories') as territory,
                asf.company,
                COALESCE(asf.predicted_qty, 0) as predicted_qty,
                COALESCE(asf.sales_trend, 'Unknown') as sales_trend,
                COALESCE(asf.movement_type, 'Normal') as movement_type,
                COALESCE(asf.confidence_score, 0) as confidence_score,
                COALESCE(asf.sales_alert, 0) as sales_alert,
                asf.forecast_date,
                asf.last_forecast_date,
                COALESCE(asf.forecast_period_days, 30) as forecast_period_days,
                COALESCE(asf.delivery_days, 7) as delivery_days,
                COALESCE(asf.preferred_customer, 0) as preferred_customer,
                COALESCE(asf.auto_create_sales_order, 0) as auto_create_sales_order,
                -- Analytics fields that exist in database
                COALESCE(asf.demand_pattern, '📊 Normal') as demand_pattern,
                COALESCE(asf.customer_score, 50.0) as customer_score,
                COALESCE(asf.market_potential, 60.0) as market_potential,
                COALESCE(asf.seasonality_index, 1.0) as seasonality_index,
                COALESCE(asf.revenue_potential, 0) as revenue_potential,
                COALESCE(asf.cross_sell_score, 40.0) as cross_sell_score,
                COALESCE(asf.churn_risk, '🟡 Medium') as churn_risk,
                COALESCE(asf.sales_velocity, 0) as sales_velocity,
                -- Calculate these fields in Python instead of SQL
                0 as volatility_index,
                0 as reorder_level,
                0 as suggested_qty,
                0 as current_stock,
                asf.name as forecast_id,
                asf.modified
            FROM `tabAI Sales Forecast` asf
            WHERE 1=1 {conditions}
            ORDER BY 
                asf.sales_alert DESC,
                asf.confidence_score DESC,
                asf.predicted_qty DESC
            LIMIT 1000
        """
        
        # Create clean parameters for SQL execution
        clean_params = {}
        for key, value in filters.items():
            if key in ['from_date', 'to_date', 'company', 'customer', 'territory', 'item_group']:
                clean_params[key] = value
            elif key in ['sales_trend', 'movement_type'] and isinstance(value, str) and ',' not in value:
                clean_params[key] = value
        
        data = frappe.db.sql(base_query, clean_params, as_dict=True)
        
        if not data:
            return []
        
        # Apply data science enhancements
        enhanced_data = apply_sales_data_science_enhancements(data, filters)
        
        return enhanced_data
        
    except Exception as e:
        frappe.log_error(f"Enhanced data retrieval error: {str(e)}")
        return []

def get_enhanced_conditions(filters):
    """Enhanced filtering conditions for sales data"""
    try:
        conditions = ""
        
        # Date range filter
        if filters.get("from_date") and filters.get("to_date"):
            conditions += " AND DATE(COALESCE(asf.last_forecast_date, asf.creation)) BETWEEN %(from_date)s AND %(to_date)s"
        
        # Company filter
        if filters.get("company"):
            conditions += " AND asf.company = %(company)s"
        
        # Customer filter
        if filters.get("customer"):
            conditions += " AND asf.customer = %(customer)s"
        
        # Territory filter
        if filters.get("territory"):
            conditions += " AND asf.territory = %(territory)s"
        
        # Item group filter
        if filters.get("item_group"):
            conditions += " AND asf.item_group = %(item_group)s"
        
        # Sales trend filter - simplified approach
        if filters.get("sales_trend"):
            sales_trend = filters["sales_trend"]
            if isinstance(sales_trend, str):
                if ',' in sales_trend:
                    # Handle comma-separated string from MultiSelectList
                    trend_list = [f"'{t.strip()}'" for t in sales_trend.split(',')]
                    conditions += f" AND asf.sales_trend IN ({','.join(trend_list)})"
                else:
                    conditions += " AND asf.sales_trend = %(sales_trend)s"
            elif isinstance(sales_trend, list):
                trend_list = [f"'{t}'" for t in sales_trend]
                conditions += f" AND asf.sales_trend IN ({','.join(trend_list)})"
        
        # Movement type filter - simplified approach
        if filters.get("movement_type"):
            movement_type = filters["movement_type"]
            if isinstance(movement_type, str):
                if ',' in movement_type:
                    # Handle comma-separated string from MultiSelectList
                    movement_list = [f"'{m.strip()}'" for m in movement_type.split(',')]
                    conditions += f" AND asf.movement_type IN ({','.join(movement_list)})"
                else:
                    conditions += " AND asf.movement_type = %(movement_type)s"
            elif isinstance(movement_type, list):
                movement_list = [f"'{m}'" for m in movement_type]
                conditions += f" AND asf.movement_type IN ({','.join(movement_list)})"
        
        # Sales alerts filter
        if filters.get("sales_alert"):
            conditions += " AND asf.sales_alert = 1"
        
        # Low confidence filter
        if filters.get("low_confidence"):
            conditions += " AND COALESCE(asf.confidence_score, 0) < 70"
        
        # High opportunity filter
        if filters.get("high_opportunity"):
            conditions += " AND COALESCE(asf.predicted_qty, 0) > 10"
        
        # Fast moving filter
        if filters.get("fast_moving_only"):
            conditions += " AND asf.movement_type = 'Fast Moving'"
        
        # Critical items filter
        if filters.get("critical_items_only"):
            conditions += " AND (asf.movement_type = 'Critical' OR asf.sales_alert = 1)"
        
        return conditions
        
    except Exception as e:
        frappe.log_error(f"Conditions building error: {str(e)}")
        return ""

def apply_sales_data_science_enhancements(data, filters):
    """Enhanced data processing with calculated fields"""
    if not data:
        return data
    
    try:
        # Calculate missing metrics for each row
        for row in data:
            # Calculate sales alert directly
            row['sales_alert'] = calculate_sales_alert_direct(row)
            
            # Calculate volatility index if not in database
            if not row.get('volatility_index') or row['volatility_index'] == 0:
                row['volatility_index'] = calculate_volatility_index_direct(row)
            
            # Calculate reorder level if not in database
            if not row.get('reorder_level') or row['reorder_level'] == 0:
                row['reorder_level'] = calculate_reorder_level_direct(row)
            
            # Calculate suggested quantity if not in database
            if not row.get('suggested_qty') or row['suggested_qty'] == 0:
                row['suggested_qty'] = calculate_suggested_qty_direct(row)
            
            # Ensure default values for display
            row['predicted_qty'] = flt(row.get('predicted_qty', 0))
            row['confidence_score'] = flt(row.get('confidence_score', 50))
            row['delivery_days'] = flt(row.get('delivery_days', 7))
            row['sales_trend'] = row.get('sales_trend', 'Stable').title()
            row['movement_type'] = row.get('movement_type', 'Normal').title()
        
        # Convert to DataFrame only for sorting if pandas is available
        if PANDAS_AVAILABLE:
            import pandas as pd
            df = pd.DataFrame(data)
            
            # Sort by priority without modifying any analytics fields
            df = df.sort_values(['sales_alert', 'revenue_potential', 'confidence_score'], 
                               ascending=[False, False, False])
            
            # Convert back to list of dictionaries
            return df.to_dict('records')
        else:
            # Sort data without pandas
            sorted_data = sorted(data, key=lambda x: (
                -int(x.get('sales_alert', 0)),  # Sales alert desc
                -float(x.get('revenue_potential', 0)),  # Revenue potential desc  
                -float(x.get('confidence_score', 0))  # Confidence desc
            ))
            
            return sorted_data
            
    except Exception as e:
        frappe.log_error(f"Data enhancement failed: {str(e)}")
        return data

def save_calculated_values_to_doctype(df):
    """Save calculated analytical values back to DocType records"""
    try:
        # Check which columns exist in the database
        existing_columns = get_existing_analytics_columns()
        
        for index, row in df.iterrows():
            forecast_id = row.get('forecast_id')
            if forecast_id:
                update_values = {}
                
                # Only update fields that exist in the database
                if 'demand_pattern' in existing_columns:
                    update_values["demand_pattern"] = row.get('demand_pattern', '📊 Unknown')
                if 'customer_score' in existing_columns:
                    update_values["customer_score"] = flt(row.get('customer_score', 0))
                if 'market_potential' in existing_columns:
                    update_values["market_potential"] = flt(row.get('market_potential', 0))
                if 'seasonality_index' in existing_columns:
                    update_values["seasonality_index"] = flt(row.get('seasonality_index', 1.0))
                if 'revenue_potential' in existing_columns:
                    update_values["revenue_potential"] = flt(row.get('revenue_potential', 0))
                if 'cross_sell_score' in existing_columns:
                    update_values["cross_sell_score"] = flt(row.get('cross_sell_score', 0))
                if 'churn_risk' in existing_columns:
                    update_values["churn_risk"] = row.get('churn_risk', '❓ Unknown')
                if 'sales_velocity' in existing_columns:
                    update_values["sales_velocity"] = flt(row.get('sales_velocity', 0))
                
                # Always update last_forecast_date if possible
                if 'last_forecast_date' in existing_columns:
                    update_values["last_forecast_date"] = now_datetime()
                
                if update_values:
                    frappe.db.set_value("AI Sales Forecast", forecast_id, update_values)
        
        # Commit changes in batches
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Failed to save calculated values to DocType: {str(e)}")

def get_existing_analytics_columns():
    """Check which analytics columns exist in the AI Sales Forecast table"""
    try:
        columns_result = frappe.db.sql("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'tabAI Sales Forecast' 
            AND COLUMN_NAME IN (
                'demand_pattern', 'customer_score', 'market_potential', 
                'seasonality_index', 'revenue_potential', 'cross_sell_score', 
                'churn_risk', 'sales_velocity', 'last_forecast_date'
            )
        """)
        
        return [col[0] for col in columns_result] if columns_result else []
        
    except Exception as e:
        frappe.log_error(f"Failed to check existing columns: {str(e)}")
        return []

def save_single_row_values_to_doctype(row):
    """Save single row calculated values to DocType"""
    try:
        forecast_id = row.get('forecast_id')
        if forecast_id:
            # Check which columns exist
            existing_columns = get_existing_analytics_columns()
            update_values = {}
            
            # Only update fields that exist in the database
            if 'demand_pattern' in existing_columns:
                update_values["demand_pattern"] = row.get('demand_pattern', '📊 Unknown')
            if 'customer_score' in existing_columns:
                update_values["customer_score"] = flt(row.get('customer_score', 0))
            if 'market_potential' in existing_columns:
                update_values["market_potential"] = flt(row.get('market_potential', 0))
            if 'seasonality_index' in existing_columns:
                update_values["seasonality_index"] = flt(row.get('seasonality_index', 1.0))
            if 'revenue_potential' in existing_columns:
                update_values["revenue_potential"] = flt(row.get('revenue_potential', 0))
            if 'cross_sell_score' in existing_columns:
                update_values["cross_sell_score"] = flt(row.get('cross_sell_score', 0))
            if 'churn_risk' in existing_columns:
                update_values["churn_risk"] = row.get('churn_risk', '❓ Unknown')
            if 'sales_velocity' in existing_columns:
                update_values["sales_velocity"] = flt(row.get('sales_velocity', 0))
            if 'last_forecast_date' in existing_columns:
                update_values["last_forecast_date"] = now_datetime()
            
            if update_values:
                frappe.db.set_value("AI Sales Forecast", forecast_id, update_values)
            
    except Exception as e:
        frappe.log_error(f"Failed to save single row values: {str(e)}")

# Safe calculation functions with better error handling
def safe_calculate_demand_pattern(row):
    """Safe demand pattern calculation"""
    try:
        return calculate_demand_pattern(row)
    except Exception as e:
        frappe.log_error(f"Demand pattern calculation error for {row.get('item_code', 'Unknown')}: {str(e)}")
        return "📊 Unknown"

def safe_calculate_customer_score(row):
    """Safe customer score calculation"""
    try:
        return calculate_customer_score(row)
    except Exception as e:
        frappe.log_error(f"Customer score calculation error for {row.get('customer', 'Unknown')}: {str(e)}")
        return 0.0

def safe_calculate_market_potential(row):
    """Safe market potential calculation"""
    try:
        return calculate_market_potential(row)
    except Exception as e:
        frappe.log_error(f"Market potential calculation error: {str(e)}")
        return 0.0

def safe_calculate_seasonality_index(row):
    """Safe seasonality index calculation"""
    try:
        return calculate_seasonality_index(row)
    except Exception as e:
        frappe.log_error(f"Seasonality calculation error: {str(e)}")
        return 1.0

def safe_calculate_revenue_potential(row):
    """Safe revenue potential calculation"""
    try:
        return calculate_revenue_potential(row)
    except Exception as e:
        frappe.log_error(f"Revenue potential calculation error: {str(e)}")
        return 0.0

def safe_calculate_cross_sell_score(row):
    """Safe cross-sell score calculation"""
    try:
        return calculate_cross_sell_score(row)
    except Exception as e:
        frappe.log_error(f"Cross-sell calculation error: {str(e)}")
        return 0.0

def safe_calculate_churn_risk(row):
    """Safe churn risk calculation"""
    try:
        return calculate_churn_risk(row)
    except Exception as e:
        frappe.log_error(f"Churn risk calculation error: {str(e)}")
        return "❓ Unknown"

def calculate_revenue_potential(row):
    """Calculate revenue potential based on predicted quantity and pricing"""
    try:
        item_code = row.get('item_code')
        customer = row.get('customer')
        company = row.get('company')
        predicted_qty = flt(row.get('predicted_qty', 0))
        
        if not predicted_qty or not item_code or not customer or not company:
            return 0.0
        
        # Get average selling price from recent sales
        avg_price_result = frappe.db.sql("""
            SELECT AVG(sii.rate) as avg_rate
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
            LIMIT 1
        """, (item_code, customer, company))
        
        avg_price = 0
        if avg_price_result and avg_price_result[0][0]:
            avg_price = flt(avg_price_result[0][0])
        else:
            # Fallback to item's standard selling rate
            std_rate = frappe.db.get_value("Item Price", {
                "item_code": item_code,
                "selling": 1
            }, "price_list_rate")
            avg_price = flt(std_rate) if std_rate else 100  # Default fallback price
        
        revenue_potential = predicted_qty * avg_price
        return round(revenue_potential, 2)
        
    except Exception as e:
        return 0.0

def calculate_demand_pattern(row):
    """Calculate demand pattern based on historical sales and trends"""
    try:
        item_code = row.get('item_code')
        customer = row.get('customer')
        company = row.get('company')
        sales_trend = row.get('sales_trend', '').lower()
        movement_type = row.get('movement_type', '').lower()
        predicted_qty = flt(row.get('predicted_qty', 0))
        
        if not all([item_code, customer, company]):
            return "🔍 Emerging"
        
        # Quick pattern based on existing data
        if movement_type == 'critical':
            return "🚨 Critical"
        elif sales_trend == 'increasing' or (predicted_qty > 10):
            return "🚀 Growth"
        elif sales_trend == 'decreasing' or (predicted_qty > 0):
            return "📉 Declining"
        elif sales_trend == 'stable':
            return "📈 Steady"
        elif movement_type == 'fast moving':
            return "⚡ High Velocity"
        elif movement_type == 'slow moving':
            return "🐌 Slow Trend"
        else:
            return "📊 Normal"
        
    except Exception as e:
        return "📊 Unknown"

def calculate_customer_score(row):
    """Calculate customer scoring based on purchase history"""
    try:
        customer = row.get('customer')
        company = row.get('company')
        
        if not customer or not company:
            return 0.0
        
        # Simplified scoring based on recent activity
        score = 50.0  # Base score
        
        # Check recent purchase activity
        recent_purchases = frappe.db.sql("""
            SELECT COUNT(*) as purchase_count, SUM(grand_total) as total_amount
            FROM `tabSales Invoice`
            WHERE customer = %s AND company = %s AND docstatus = 1
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
        """, (customer, company), as_dict=True)
        
        if recent_purchases and recent_purchases[0]:
            purchase_count = cint(recent_purchases[0].get('purchase_count', 0))
            total_amount = flt(recent_purchases[0].get('total_amount', 0))
            
            # Activity score (0-30 points)
            activity_score = min(purchase_count * 3, 30)
            
            # Value score (0-20 points)
            value_score = min(total_amount / 10000, 20)  # Assuming 10k as good benchmark
            
            score += activity_score + value_score
        
        return round(min(score, 100.0), 1)
        
    except Exception as e:
        return 0.0

def calculate_market_potential(row):
    """Calculate market potential percentage"""
    try:
        predicted_qty = flt(row.get('predicted_qty', 0))
        confidence_score = flt(row.get('confidence_score', 0))
        movement_type = row.get('movement_type', '').lower()
        
        # Base potential calculation
        if movement_type == 'critical':
            base_potential = 90.0
        elif movement_type == 'fast moving':
            base_potential = 75.0
        elif movement_type == 'slow moving':
            base_potential = 40.0
        else:
            base_potential = 60.0
        
        # Adjust based on confidence and quantity
        confidence_factor = confidence_score / 100
        quantity_factor = min(predicted_qty / 100, 1.0)  # Normalize to max 1
        
        market_potential = base_potential * confidence_factor * (0.5 + quantity_factor * 0.5)
        
        return round(market_potential, 1)
        
    except Exception as e:
        return 0.0

def calculate_seasonality_index(row):
    """Calculate seasonality index"""
    try:
        sales_trend = row.get('sales_trend', '').lower()
        current_month = datetime.now().month
        
        # Simplified seasonality based on trend and month
        base_index = 1.0
        
        if sales_trend == 'seasonal':
            # Seasonal adjustment based on month
            if current_month in [11, 12, 1]:  # Holiday season
                base_index = 1.3
            elif current_month in [6, 7, 8]:  # Summer
                base_index = 0.8
            else:
                base_index = 1.0
        elif sales_trend == 'increasing':
            base_index = 1.2
        elif sales_trend == 'decreasing':
            base_index = 0.8
        
        return round(base_index, 2)
        
    except Exception as e:
        return 1.0

def calculate_cross_sell_score(row):
    """Calculate cross-selling potential"""
    try:
        customer = row.get('customer')
        item_code = row.get('item_code')
        company = row.get('company')
        
        if not all([customer, item_code, company]):
            return 0.0
        
        # Simplified cross-sell scoring
        base_score = 30.0
        
        # Check customer's purchase diversity
        unique_items = frappe.db.sql("""
            SELECT COUNT(DISTINCT sii.item_code) as item_count
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.customer = %s AND si.company = %s AND si.docstatus = 1
        """, (customer, company))
        
        if unique_items and unique_items[0][0]:
            diversity_score = min(cint(unique_items[0][0]) * 5, 40)
            base_score += diversity_score
        
        return round(min(base_score, 100.0), 1)
        
    except Exception as e:
        return 0.0

def calculate_churn_risk(row):
    """Calculate customer churn risk"""
    try:
        customer = row.get('customer')
        company = row.get('company')
        sales_trend = row.get('sales_trend', '').lower()
        
        if not customer or not company:
            return "❓ Unknown"
        
        # Simple risk assessment
        if sales_trend == 'decreasing':
            return "🔴 High"
        elif sales_trend == 'stable':
            return "🟡 Medium"
        elif sales_trend == 'increasing':
            return "🟢 Low"
        else:
            return "🟡 Medium"
        
    except Exception as e:
        return "❓ Unknown"

def add_sales_efficiency_metrics(df):
    """Add sales efficiency metrics to dataframe"""
    try:
        if len(df) > 0:
            # Calculate sales velocity
            df['sales_velocity'] = df.apply(lambda row:
                flt(row.get('predicted_qty', 0)) / max(cint(row.get('forecast_period_days', 30)), 1), axis=1)
            
            # Calculate conversion potential
            df['conversion_potential'] = df.apply(lambda row:
                flt(row.get('customer_score', 0)) * flt(row.get('market_potential', 0)) / 100, axis=1)
        
        return df
        
    except Exception as e:
        frappe.log_error(f"Sales efficiency metrics failed: {str(e)}")
        return df

def get_advanced_chart_data(filters):
    """Generate advanced chart data for visualization"""
    try:
        conditions = get_enhanced_conditions(filters)
        
        if not frappe.db.table_exists("AI Sales Forecast"):
            return {"data": {"labels": [], "datasets": []}, "type": "bar"}
        
        # Movement type distribution
        chart_data = frappe.db.sql(f"""
            SELECT 
                COALESCE(asf.movement_type, 'Unknown') as name,
                COUNT(*) as count,
                SUM(CASE WHEN asf.sales_alert = 1 THEN 1 ELSE 0 END) as alerts,
                AVG(COALESCE(asf.confidence_score, 0)) as avg_confidence,
                SUM(COALESCE(asf.predicted_qty, 0)) as total_qty
            FROM `tabAI Sales Forecast` asf
            WHERE 1=1 {conditions}
            GROUP BY asf.movement_type
            ORDER BY count DESC
        """, filters, as_dict=True)
        
        if not chart_data:
            return {"data": {"labels": [], "datasets": []}, "type": "bar"}
        
        return {
            "data": {
                "labels": [d.name for d in chart_data],
                "datasets": [
                    {
                        "name": "Forecast Count",
                        "values": [cint(d.count) for d in chart_data]
                    },
                    {
                        "name": "Sales Alerts",
                        "values": [cint(d.alerts) for d in chart_data]
                    }
                ]
            },
            "type": "bar",
            "height": 350,
            "colors": ["#28a745", "#17a2b8", "#ffc107", "#dc3545"],
            "axisOptions": {
                "xAxisMode": "tick",
                "yAxisMode": "tick"
            },
            "barOptions": {
                "spaceRatio": 0.5
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Chart data generation failed: {str(e)}")
        return {"data": {"labels": [], "datasets": []}, "type": "bar"}

def get_smart_summary_data(filters):
    """Generate smart summary cards with key insights"""
    try:
        conditions = get_enhanced_conditions(filters)
        
        if not frappe.db.table_exists("AI Sales Forecast"):
            return [{
                "value": "Table Missing",
                "label": "AI Sales Forecast table not found",
                "datatype": "Data",
                "indicator": "Red"
            }]
        
        # Main statistics query
        stats_result = frappe.db.sql(f"""
            SELECT 
                COUNT(*) as total_forecasts,
                SUM(CASE WHEN COALESCE(asf.sales_alert, 0) = 1 THEN 1 ELSE 0 END) as sales_alerts,
                SUM(CASE WHEN asf.movement_type = 'Fast Moving' THEN 1 ELSE 0 END) as fast_moving,
                SUM(CASE WHEN asf.movement_type = 'Slow Moving' THEN 1 ELSE 0 END) as slow_moving,
                SUM(CASE WHEN asf.movement_type = 'Critical' THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN asf.sales_trend = 'Increasing' THEN 1 ELSE 0 END) as increasing,
                SUM(CASE WHEN asf.sales_trend = 'Decreasing' THEN 1 ELSE 0 END) as decreasing,
                AVG(COALESCE(asf.confidence_score, 0)) as avg_confidence,
                COUNT(DISTINCT asf.customer) as unique_customers,
                COUNT(DISTINCT asf.company) as companies,
                COUNT(DISTINCT COALESCE(asf.territory, 'All Territories')) as territories,
                SUM(COALESCE(asf.predicted_qty, 0)) as total_predicted_qty
            FROM `tabAI Sales Forecast` asf
            WHERE 1=1 {conditions}
        """, filters, as_dict=True)
        
        if not stats_result:
            return [{
                "value": "No Data",
                "label": "No forecast data available",
                "datatype": "Data",
                "indicator": "Orange"
            }]
        
        stats = stats_result[0]
        
        # Calculate percentages and ratios
        total = cint(stats.total_forecasts) or 1  # Prevent division by zero
        alert_pct = (cint(stats.sales_alerts) / total * 100)
        growth_pct = (cint(stats.increasing) / total * 100)
        avg_conf = flt(stats.avg_confidence)
        
        # Determine overall health
        if avg_conf > 80 and growth_pct > 40:
            health_status = "Excellent"
            health_indicator = "Green"
        elif avg_conf > 60 and growth_pct > 25:
            health_status = "Good"
            health_indicator = "Blue"
        else:
            health_status = "Needs Attention"
            health_indicator = "Orange"
        
        return [
            {
                "value": cint(stats.total_forecasts),
                "label": "Total Sales Forecasts",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": cint(stats.sales_alerts),
                "label": f"High Priority Alerts ({alert_pct:.1f}%)",
                "datatype": "Int",
                "indicator": "Green" if cint(stats.sales_alerts) > 0 else "Grey"
            },
            {
                "value": cint(stats.increasing),
                "label": f"Growing Trends ({growth_pct:.1f}%)",
                "datatype": "Int",
                "indicator": "Green" if growth_pct > 30 else "Orange"
            },
            {
                "value": cint(stats.fast_moving),
                "label": "Fast Moving Items",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": cint(stats.critical),
                "label": "Critical Items",
                "datatype": "Int",
                "indicator": "Red" if cint(stats.critical) > 0 else "Green"
            },
            {
                "value": cint(stats.decreasing),
                "label": "Declining Items",
                "datatype": "Int",
                "indicator": "Red" if cint(stats.decreasing) > 0 else "Green"
            },
            {
                "value": f"{avg_conf:.1f}%",
                "label": "Average AI Confidence",
                "datatype": "Data",
                "indicator": "Green" if avg_conf > 80 else "Orange" if avg_conf > 60 else "Red"
            },
            {
                "value": health_status,
                "label": "Overall Sales Health",
                "datatype": "Data",
                "indicator": health_indicator
            },
            {
                "value": cint(stats.unique_customers),
                "label": "Active Customers",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": cint(stats.territories),
                "label": "Coverage Areas",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": f"{flt(stats.total_predicted_qty):,.0f}",
                "label": "Total Predicted Volume",
                "datatype": "Data",
                "indicator": "Blue"
            },
            {
                "value": cint(stats.companies),
                "label": "Companies",
                "datatype": "Int",
                "indicator": "Blue"
            }
        ]
        
    except Exception as e:
        frappe.log_error(f"Summary data generation failed: {str(e)}")
        return [
            {
                "value": "Error",
                "label": "Summary calculation failed",
                "datatype": "Data",
                "indicator": "Red"
            }
        ]

# Additional utility functions for bulk operations
@frappe.whitelist()
def create_bulk_sales_orders(forecast_ids):
    """Create sales orders from selected forecasts"""
    try:
        if not forecast_ids:
            return {"success": False, "message": "No forecasts selected"}
        
        if isinstance(forecast_ids, str):
            forecast_ids = json.loads(forecast_ids)
        
        created_count = 0
        errors = []
        
        for forecast_id in forecast_ids:
            try:
                forecast = frappe.get_doc("AI Sales Forecast", forecast_id)
                
                # Check if auto-create is enabled
                if not forecast.auto_create_sales_order:
                    continue
                
                # Create sales order
                so = frappe.get_doc({
                    "doctype": "Sales Order",
                    "customer": forecast.customer,
                    "company": forecast.company,
                    "territory": forecast.territory,
                    "delivery_date": add_days(nowdate(), forecast.delivery_days or 7),
                    "items": [{
                        "item_code": forecast.item_code,
                        "qty": forecast.predicted_qty,
                        "delivery_date": add_days(nowdate(), forecast.delivery_days or 7)
                    }]
                })
                
                so.insert(ignore_permissions=True)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Failed to create SO for {forecast_id}: {str(e)}")
        
        return {
            "success": True,
            "created_count": created_count,
            "errors": errors
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk sales order creation failed: {str(e)}")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def update_bulk_forecasts(forecast_ids):
    """Update selected forecasts with latest data"""
    try:
        if not forecast_ids:
            return {"success": False, "message": "No forecasts selected"}
        
        if isinstance(forecast_ids, str):
            forecast_ids = json.loads(forecast_ids)
        
        updated_count = 0
        
        for forecast_id in forecast_ids:
            try:
                forecast = frappe.get_doc("AI Sales Forecast", forecast_id)
                forecast.last_forecast_date = now_datetime()
                forecast.save(ignore_permissions=True)
                updated_count += 1
                
            except Exception as e:
                frappe.log_error(f"Failed to update forecast {forecast_id}: {str(e)}")
        
        return {
            "success": True,
            "updated_count": updated_count
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk forecast update failed: {str(e)}")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def get_forecast_insights(filters=None):
    """Get AI-powered insights for the dashboard"""
    try:
        if isinstance(filters, str):
            filters = json.loads(filters)
        
        data = get_enhanced_data(filters or {})
        
        if not data:
            return {"insights": [], "recommendations": []}
        
        insights = []
        recommendations = []
        
        # Analyze data patterns
        high_confidence = [d for d in data if flt(d.get('confidence_score', 0)) > 80]
        critical_items = [d for d in data if d.get('movement_type') == 'Critical']
        growing_trends = [d for d in data if d.get('sales_trend') == 'Increasing']
        high_revenue = [d for d in data if flt(d.get('revenue_potential', 0)) > 10000]
        
        # Generate insights
        if high_confidence:
            insights.append({
                "type": "success",
                "title": "High Confidence Predictions",
                "message": f"{len(high_confidence)} forecasts have >80% confidence scores",
                "count": len(high_confidence)
            })
        
        if critical_items:
            insights.append({
                "type": "warning",
                "title": "Critical Items Alert",
                "message": f"{len(critical_items)} items need immediate attention",
                "count": len(critical_items)
            })
        
        if growing_trends:
            insights.append({
                "type": "info",
                "title": "Growth Opportunities",
                "message": f"{len(growing_trends)} items show increasing demand trends",
                "count": len(growing_trends)
            })
        
        # Generate recommendations
        if critical_items:
            recommendations.append({
                "priority": "high",
                "action": "Immediate Review Required",
                "description": f"Review {len(critical_items)} critical items for inventory planning",
                "items": [item.get('item_code') for item in critical_items[:5]]
            })
        
        if high_revenue:
            recommendations.append({
                "priority": "medium",
                "action": "Revenue Optimization",
                "description": f"Focus on {len(high_revenue)} high-revenue potential items",
                "items": [item.get('item_code') for item in high_revenue[:5]]
            })
        
        if growing_trends:
            recommendations.append({
                "priority": "medium",
                "action": "Inventory Build-up",
                "description": f"Consider increasing stock for {len(growing_trends)} growing items",
                "items": [item.get('item_code') for item in growing_trends[:5]]
            })
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "total_items": len(data),
            "analysis_date": nowdate()
        }
        
    except Exception as e:
        frappe.log_error(f"Forecast insights generation failed: {str(e)}")
        return {"insights": [], "recommendations": [], "error": str(e)}

# Performance optimization functions
def get_cached_customer_metrics(customer, company):
    """Get cached customer metrics to improve performance"""
    cache_key = f"customer_metrics_{customer}_{company}"
    
    cached_data = frappe.cache().get_value(cache_key)
    if cached_data:
        return cached_data
    
    # Calculate and cache for 1 hour
    metrics = calculate_fresh_customer_metrics(customer, company)
    frappe.cache().set_value(cache_key, metrics, expires_in_sec=3600)
    
    return metrics

def calculate_fresh_customer_metrics(customer, company):
    """Calculate fresh customer metrics"""
    try:
        metrics = frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT si.name) as invoice_count,
                SUM(si.grand_total) as total_revenue,
                AVG(si.grand_total) as avg_order_value,
                DATEDIFF(CURDATE(), MAX(si.posting_date)) as days_since_last_order,
                COUNT(DISTINCT sii.item_code) as unique_items
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
            WHERE si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
        """, (customer, company), as_dict=True)
        
        return metrics[0] if metrics else {}
        
    except Exception as e:
        frappe.log_error(f"Customer metrics calculation failed: {str(e)}")
        return {}

# Data validation and cleanup functions
def validate_forecast_data(data):
    """Validate and clean forecast data"""
    validated_data = []
    
    for row in data:
        try:
            # Ensure required fields
            if not row.get('item_code') or not row.get('customer'):
                continue
            
            # Clean numeric fields
            row['predicted_qty'] = max(flt(row.get('predicted_qty', 0)), 0)
            row['confidence_score'] = max(min(flt(row.get('confidence_score', 0)), 100), 0)
            
            # Clean text fields
            row['sales_trend'] = str(row.get('sales_trend', 'Unknown')).title()
            row['movement_type'] = str(row.get('movement_type', 'Normal')).title()
            
            validated_data.append(row)
            
        except Exception as e:
            frappe.log_error(f"Data validation failed for row: {str(e)}")
            continue
    
    return validated_data

# Direct calculation functions that always return calculated values
def calculate_demand_pattern_direct(row):
    """Direct demand pattern calculation with guaranteed return"""
    try:
        movement_type = row.get('movement_type', '').lower()
        sales_trend = row.get('sales_trend', '').lower()
        predicted_qty = flt(row.get('predicted_qty', 0))
        
        if movement_type == 'critical':
            return "🚨 Critical"
        elif movement_type == 'fast moving' or predicted_qty > 10:
            return "⚡ High Velocity"  
        elif movement_type == 'slow moving' or (predicted_qty <= 10 and predicted_qty > 5):
            return "🐌 Slow Trend"
        elif sales_trend == 'increasing' or predicted_qty > 10:
            return "🚀 Growth"
        elif sales_trend == 'decreasing' or (predicted_qty > 0 and predicted_qty <= 5):
            return "📉 Declining"
        elif sales_trend == 'stable' or predicted_qty == 0:
            return "📈 Steady"
        else:
            return "📊 Normal"
    except:
        return "📊 Normal"

def calculate_customer_score_direct(row):
    """Direct customer score calculation with guaranteed return"""
    try:
        customer = row.get('customer')
        company = row.get('company')
        
        if not customer or not company:
            return 45.0
        
        # Get recent activity
        recent_data = frappe.db.sql("""
            SELECT COUNT(*) as orders, SUM(grand_total) as total_value
            FROM `tabSales Invoice`
            WHERE customer = %s AND company = %s AND docstatus = 1
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
        """, (customer, company), as_dict=True)
        
        if recent_data and recent_data[0]:
            orders = recent_data[0].orders or 0
            total_value = recent_data[0].total_value or 0
            
            # Calculate score: Base 30 + Activity (max 40) + Value (max 30)
            activity_score = min(orders * 4, 40)
            value_score = min(total_value / 8000, 30)  # $8k benchmark
            
            return round(30 + activity_score + value_score, 1)
        else:
            return 35.0
    except:
        return 50.0

def calculate_market_potential_direct(row):
    """Direct market potential calculation with guaranteed return"""
    try:
        confidence_score = flt(row.get('confidence_score', 0))
        predicted_qty = flt(row.get('predicted_qty', 0))
        movement_type = row.get('movement_type', '').lower()
        
        # Base potential based on movement type
        if movement_type == 'critical':
            base_potential = 85.0
        elif movement_type == 'fast moving':
            base_potential = 75.0
        elif movement_type == 'slow moving':
            base_potential = 45.0
        else:
            base_potential = 60.0
        
        # Adjust for confidence and quantity
        confidence_factor = max(confidence_score / 100, 0.3)  # Minimum 30%
        qty_factor = min(predicted_qty / 100, 1.0) if predicted_qty > 0 else 0.5
        
        final_potential = base_potential * confidence_factor * (0.5 + qty_factor * 0.5)
        return round(final_potential, 1)
    except:
        return 55.0

def calculate_seasonality_index_direct(row):
    """Direct seasonality index calculation with guaranteed return"""
    try:
        sales_trend = row.get('sales_trend', '').lower()
        current_month = datetime.now().month
        
        if sales_trend == 'seasonal':
            if current_month in [11, 12, 1]:  # Holiday season
                return 1.3
            elif current_month in [6, 7, 8]:  # Summer
                return 0.8
            else:
                return 1.0
        elif sales_trend == 'increasing':
            return 1.2
        elif sales_trend == 'decreasing':
            return 0.8
        else:
            return 1.0
    except:
        return 1.0

def calculate_revenue_potential_direct(row):
    """Direct revenue potential calculation with guaranteed return"""
    try:
        item_code = row.get('item_code')
        customer = row.get('customer')
        company = row.get('company')
        predicted_qty = flt(row.get('predicted_qty', 0))
        
        if not predicted_qty or predicted_qty <= 0:
            return 0.0
        
        # Get average price from recent sales
        avg_price = 150.0  # Default price
        if item_code and customer and company:
            try:
                price_data = frappe.db.sql("""
                    SELECT AVG(sii.rate) as avg_rate
                    FROM `tabSales Invoice Item` sii
                    INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                    WHERE sii.item_code = %s AND si.customer = %s AND si.company = %s
                    AND si.docstatus = 1 AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
                    AND sii.rate > 0
                    LIMIT 1
                """, (item_code, customer, company))
                
                if price_data and price_data[0][0]:
                    avg_price = flt(price_data[0][0])
            except:
                pass
        
        revenue = predicted_qty * avg_price
        return round(revenue, 2)
    except:
        return 0.0

def calculate_cross_sell_score_direct(row):
    """Direct cross-sell score calculation with guaranteed return"""
    try:
        customer = row.get('customer')
        company = row.get('company')
        
        if not customer or not company:
            return 35.0
        
        # Get customer's item diversity
        diversity_data = frappe.db.sql("""
            SELECT COUNT(DISTINCT sii.item_code) as item_count
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.customer = %s AND si.company = %s AND si.docstatus = 1
            AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
        """, (customer, company))
        
        if diversity_data and diversity_data[0][0]:
            unique_items = diversity_data[0][0]
            # Base score 25 + diversity bonus (max 65)
            diversity_score = min(unique_items * 4, 65)
            return round(25 + diversity_score, 1)
        else:
            return 30.0
    except:
        return 40.0

def calculate_churn_risk_direct(row):
    """Direct churn risk calculation with guaranteed return"""
    try:
        customer = row.get('customer')
        company = row.get('company')
        sales_trend = row.get('sales_trend', '').lower()
        confidence_score = flt(row.get('confidence_score', 0))
        
        # Base assessment on sales trend
        if sales_trend == 'decreasing':
            return "🔴 High"
        elif sales_trend == 'increasing':
            return "🟢 Low"
        elif confidence_score < 50:
            return "🟡 Medium"
        elif confidence_score > 80:
            return "🟢 Low"
        else:
            return "🟡 Medium"
    except:
        return "🟡 Medium"

def calculate_sales_velocity_direct(row):
    """Direct sales velocity calculation with guaranteed return"""
    try:
        predicted_qty = flt(row.get('predicted_qty', 0))
        forecast_period = cint(row.get('forecast_period_days', 30))
        
        if forecast_period <= 0:
            forecast_period = 30
        
        velocity = predicted_qty / forecast_period
        return round(velocity, 2)
    except:
        return 0.0

def calculate_sales_alert_direct(row):
    """Direct sales alert calculation with guaranteed return"""
    try:
        movement_type = row.get('movement_type', '').lower()
        predicted_qty = flt(row.get('predicted_qty', 0))
        confidence_score = flt(row.get('confidence_score', 0))
        sales_trend = row.get('sales_trend', '').lower()
        
        # Critical alerts
        if movement_type == 'critical':
            return "🚨 CRITICAL STOCK"
        elif predicted_qty <= 0:
            return "⚠️ NO DEMAND"
        elif confidence_score < 30:
            return "❓ UNCERTAIN FORECAST"
        elif sales_trend == 'decreasing':
            return "📉 DECLINING SALES"
        elif movement_type == 'fast moving':
            return "⚡ HIGH DEMAND"
        elif sales_trend == 'increasing':
            return "🚀 GROWING DEMAND"
        else:
            return "📊 NORMAL"
    except:
        return "📊 NORMAL"

def calculate_volatility_index_direct(row):
    """Calculate volatility index based on sales patterns"""
    try:
        item_code = row.get('item_code')
        customer = row.get('customer')
        company = row.get('company')
        sales_trend = row.get('sales_trend', '').lower()
        
        if not all([item_code, customer, company]):
            return 0.5
        
        # Base volatility on sales trend
        if sales_trend == 'volatile':
            return 0.8
        elif sales_trend == 'decreasing':
            return 0.6
        elif sales_trend == 'increasing':
            return 0.3
        elif sales_trend == 'stable':
            return 0.2
        else:
            return 0.5
    except:
        return 0.5

def calculate_reorder_level_direct(row):
    """Calculate reorder level based on consumption and lead time"""
    try:
        predicted_qty = flt(row.get('predicted_qty', 0))
        forecast_period = flt(row.get('forecast_period_days', 30))
        delivery_days = flt(row.get('delivery_days', 7))
        movement_type = row.get('movement_type', '').lower()
        
        if predicted_qty <= 0 or forecast_period <= 0:
            return 0.0
        
        # Calculate daily consumption
        daily_consumption = predicted_qty / forecast_period
        
        # Safety factor based on movement type
        if movement_type == 'critical':
            safety_factor = 2.0
        elif movement_type == 'fast moving':
            safety_factor = 1.5
        elif movement_type == 'slow moving':
            safety_factor = 1.2
        else:
            safety_factor = 1.3
        
        # Reorder level = (daily consumption * lead time) * safety factor
        reorder_level = (daily_consumption * delivery_days) * safety_factor
        
        return round(reorder_level, 2)
    except:
        return 0.0

def calculate_suggested_qty_direct(row):
    """Calculate suggested quantity for procurement"""
    try:
        predicted_qty = flt(row.get('predicted_qty', 0))
        reorder_level = flt(row.get('reorder_level', 0))
        current_stock = flt(row.get('current_stock', 0))
        movement_type = row.get('movement_type', '').lower()
        
        if predicted_qty <= 0:
            return 0.0
        
        # Base suggestion on predicted consumption plus buffer
        if movement_type == 'critical':
            buffer_factor = 1.5
        elif movement_type == 'fast moving':
            buffer_factor = 1.3
        elif movement_type == 'slow moving':
            buffer_factor = 1.1
        else:
            buffer_factor = 1.2
        
        # Suggested qty = predicted qty + buffer - current stock
        suggested_qty = (predicted_qty * buffer_factor) - current_stock
        
        # Ensure minimum order quantity
        min_order_qty = max(predicted_qty * 0.1, 1)
        
        return round(max(suggested_qty, min_order_qty), 2)
    except:
        return 0.0