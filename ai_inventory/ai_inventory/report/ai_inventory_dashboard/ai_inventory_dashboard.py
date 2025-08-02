# ai_inventory/ai_inventory/report/ai_inventory_dashboard/ai_inventory_dashboard.py
# ENHANCED VERSION WITH DATA SCIENCE & ADVANCED FILTERING

import frappe
from frappe.utils import flt, nowdate, add_days, getdate, cint
from frappe import _
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import math

def execute(filters=None):
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

def validate_and_clean_filters(filters):
    """Validate and clean filter inputs with smart defaults"""
    cleaned_filters = filters.copy()
    
    # Set default date range if not provided (last 90 days)
    if not cleaned_filters.get("from_date"):
        cleaned_filters["from_date"] = add_days(nowdate(), -90)
    
    if not cleaned_filters.get("to_date"):
        cleaned_filters["to_date"] = nowdate()
    
    # Ensure from_date is not after to_date
    if getdate(cleaned_filters["from_date"]) > getdate(cleaned_filters["to_date"]):
        cleaned_filters["from_date"], cleaned_filters["to_date"] = cleaned_filters["to_date"], cleaned_filters["from_date"]
    
    # Convert string values to proper types
    if cleaned_filters.get("reorder_alert"):
        cleaned_filters["reorder_alert"] = cint(cleaned_filters["reorder_alert"])
    
    if cleaned_filters.get("low_confidence"):
        cleaned_filters["low_confidence"] = cint(cleaned_filters["low_confidence"])
    
    return cleaned_filters

def get_enhanced_columns():
    """Enhanced columns with data science metrics"""
    return [
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 250
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        },
        {
            "label": _("Supplier"),
            "fieldname": "preferred_supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 200
        },
        {
            "label": _("Current Stock"),
            "fieldname": "current_stock",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Predicted Consumption"),
            "fieldname": "predicted_consumption",
            "fieldtype": "Float",
            "width": 180
        },
        {
            "label": _("Demand Trend"),
            "fieldname": "demand_trend",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Seasonality Score"),
            "fieldname": "seasonality_score",
            "fieldtype": "Percent",
            "width": 150
        },
        {
            "label": _("Volatility Index"),
            "fieldname": "volatility_index",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Reorder Level"),
            "fieldname": "reorder_level",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Suggested Qty"),
            "fieldname": "suggested_qty",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("AI Confidence %"),
            "fieldname": "confidence_score",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Risk Score"),
            "fieldname": "risk_score",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Reorder Alert"),
            "fieldname": "reorder_alert",
            "fieldtype": "Check",
            "width": 120
        },
        {
            "label": _("Stock Days"),
            "fieldname": "stock_days",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Last Forecast"),
            "fieldname": "last_forecast_date",
            "fieldtype": "Datetime",
            "width": 180
        },
        {
            "label": _("Predicted Price"),
            "fieldname": "predicted_price",
            "fieldtype": "Currency",
            "width": 180
        }
    ]

def get_enhanced_data(filters):
    """Enhanced data retrieval with data science calculations"""
    conditions = get_enhanced_conditions(filters)
    
    # Base query with enhanced fields
    base_query = f"""
        SELECT 
            aif.item_code,
            aif.item_name,
            aif.company,
            aif.warehouse,
            COALESCE(aif.preferred_supplier, aif.supplier) as preferred_supplier,
            aif.current_stock,
            aif.movement_type,
            aif.predicted_consumption,
            aif.reorder_level,
            aif.suggested_qty,
            aif.confidence_score,
            aif.reorder_alert,
            aif.last_forecast_date,
            aif.forecast_period_days,
            aif.lead_time_days,
            CASE 
                WHEN aif.predicted_consumption > 0 AND aif.forecast_period_days > 0 
                THEN ROUND(aif.current_stock / (aif.predicted_consumption / aif.forecast_period_days))
                ELSE 999 
            END as stock_days,
            aif.name as forecast_id,
            aif.modified
        FROM `tabAI Inventory Forecast` aif
        WHERE 1=1 {conditions}
        ORDER BY 
            aif.reorder_alert DESC,
            aif.movement_type = 'Critical' DESC,
            aif.movement_type = 'Fast Moving' DESC,
            aif.confidence_score DESC,
            aif.current_stock DESC
        LIMIT 1000
    """
    
    data = frappe.db.sql(base_query, filters, as_dict=True)
    
    if not data:
        return []
    
    # Apply data science enhancements
    enhanced_data = apply_data_science_enhancements(data, filters)
    
    return enhanced_data

def get_enhanced_conditions(filters):
    """Enhanced filtering conditions"""
    conditions = ""
    
    # Date range filter
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND DATE(aif.last_forecast_date) BETWEEN %(from_date)s AND %(to_date)s"
    
    # Company filter
    if filters.get("company"):
        conditions += " AND aif.company = %(company)s"
    
    # Warehouse filter
    if filters.get("warehouse"):
        conditions += " AND aif.warehouse = %(warehouse)s"
    
    # Supplier filter (check both preferred_supplier and supplier fields)
    if filters.get("supplier"):
        conditions += """ AND (
            aif.preferred_supplier = %(supplier)s OR 
            (aif.preferred_supplier IS NULL AND aif.supplier = %(supplier)s)
        )"""
    
    # Item group filter
    if filters.get("item_group"):
        conditions += " AND aif.item_group = %(item_group)s"
    
    # Movement type filter with multiple selection support
    if filters.get("movement_type"):
        if isinstance(filters["movement_type"], list):
            movement_list = "', '".join(filters["movement_type"])
            conditions += f" AND aif.movement_type IN ('{movement_list}')"
        else:
            conditions += " AND aif.movement_type = %(movement_type)s"
    
    # Non Moving filter
    if filters.get("non_moving_only"):
        conditions += " AND aif.movement_type = 'Non Moving'"
    
    # Slow Moving filter
    if filters.get("slow_moving_only"):
        conditions += " AND aif.movement_type = 'Slow Moving'"
    
    # Reorder alerts filter
    if filters.get("reorder_alert"):
        conditions += " AND aif.reorder_alert = 1"
    
    # Low confidence filter
    if filters.get("low_confidence"):
        conditions += " AND aif.confidence_score < 70"
    
    # Stock level filters
    if filters.get("min_stock"):
        conditions += " AND aif.current_stock >= %(min_stock)s"
    
    if filters.get("max_stock"):
        conditions += " AND aif.current_stock <= %(max_stock)s"
    
    # Advanced filters
    if filters.get("critical_items_only"):
        conditions += " AND (aif.movement_type = 'Critical' OR aif.reorder_alert = 1)"
    
    if filters.get("high_value_items"):
        conditions += " AND aif.current_stock > (SELECT AVG(current_stock) FROM `tabAI Inventory Forecast`)"
    
    return conditions

def apply_data_science_enhancements(data, filters):
    """Apply advanced data science calculations to enhance the dataset"""
    try:
        if not data:
            return data
        
        # Check if required libraries are available
        try:
            import pandas as pd
            import numpy as np
        except ImportError as import_error:
            frappe.log_error(f"Required libraries not available: {str(import_error)}")
            # Apply basic enhancements without pandas
            return apply_basic_enhancements(data)
        
        # Convert to pandas DataFrame for easier manipulation
        df = pd.DataFrame(data)
        
        # Ensure all required columns exist with defaults
        df = ensure_required_columns(df)
        
        # Calculate demand trend using recent consumption patterns
        df['demand_trend'] = df.apply(lambda row: safe_calculate_demand_trend(row), axis=1)
        
        # Calculate seasonality score
        df['seasonality_score'] = df.apply(lambda row: safe_calculate_seasonality_score(row), axis=1)
        
        # Calculate volatility index
        df['volatility_index'] = df.apply(lambda row: safe_calculate_volatility_index(row), axis=1)
        
        # Calculate risk score (composite metric)
        df['risk_score'] = df.apply(lambda row: safe_calculate_risk_score(row), axis=1)
        
        # Get ML price predictions
        df['predicted_price'] = df.apply(lambda row: safe_get_ml_price_prediction(row), axis=1)
        
        # Add inventory efficiency metrics
        df = safe_add_inventory_efficiency_metrics(df)
        
        # Sort by risk score and reorder alerts
        try:
            df = df.sort_values(['reorder_alert', 'risk_score', 'confidence_score'], 
                               ascending=[False, False, False])
        except KeyError:
            # If sorting columns don't exist, sort by available columns
            available_cols = [col for col in ['reorder_alert', 'risk_score', 'confidence_score'] if col in df.columns]
            if available_cols:
                df = df.sort_values(available_cols, ascending=False)
        
        # Convert back to list of dictionaries
        enhanced_data = df.to_dict('records')
        
        # Clean up any NaN or inf values
        enhanced_data = clean_data_values(enhanced_data)
        
        return enhanced_data
        
    except Exception as e:
        frappe.log_error(f"Data science enhancement failed: {str(e)}")
        # Return basic enhanced data if pandas fails
        return apply_basic_enhancements(data)

def calculate_demand_trend(row):
    """Calculate demand trend based on historical consumption"""
    try:
        item_code = row.get('item_code')
        warehouse = row.get('warehouse')
        company = row.get('company')
        
        if not all([item_code, warehouse, company]):
            return "Missing Data"
        
        # Get consumption data for last 90 days
        consumption_data = frappe.db.sql("""
            SELECT 
                DATE(sle.posting_date) as date,
                SUM(ABS(sle.actual_qty)) as daily_consumption
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
            WHERE sle.item_code = %s 
            AND sle.warehouse = %s
            AND w.company = %s
            AND sle.actual_qty < 0
            AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            GROUP BY DATE(sle.posting_date)
            ORDER BY date
        """, (item_code, warehouse, company), as_dict=True)
        
        if len(consumption_data) < 5:
            return "Insufficient Data"
        
        # Calculate trend using linear regression
        dates = [(getdate(d['date']) - getdate(consumption_data[0]['date'])).days for d in consumption_data]
        consumptions = [flt(d['daily_consumption']) for d in consumption_data]
        
        if len(dates) > 1 and sum(consumptions) > 0:
            # Simple linear regression
            n = len(dates)
            sum_x = sum(dates)
            sum_y = sum(consumptions)
            sum_xy = sum(x * y for x, y in zip(dates, consumptions))
            sum_x2 = sum(x * x for x in dates)
            
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                
                if slope > 0.1:
                    return "📈 Increasing"
                elif slope < -0.1:
                    return "📉 Decreasing"
                else:
                    return "➡️ Stable"
        
        return "➡️ Stable"
        
    except Exception as e:
        frappe.log_error(f"Demand trend calculation error for {item_code}: {str(e)}")
        return "Error"

def calculate_seasonality_score(row):
    """Calculate seasonality score based on consumption patterns"""
    try:
        # Check if numpy is available
        try:
            import numpy as np
        except ImportError:
            return 0
            
        item_code = row.get('item_code')
        warehouse = row.get('warehouse')  
        company = row.get('company')
        
        if not all([item_code, warehouse, company]):
            return 0
        
        # Get monthly consumption for last 12 months
        monthly_data = frappe.db.sql("""
            SELECT 
                MONTH(sle.posting_date) as month,
                SUM(ABS(sle.actual_qty)) as monthly_consumption
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
            WHERE sle.item_code = %s 
            AND sle.warehouse = %s
            AND w.company = %s
            AND sle.actual_qty < 0
            AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY MONTH(sle.posting_date)
        """, (item_code, warehouse, company), as_dict=True)
        
        if len(monthly_data) < 6:
            return 0
        
        consumptions = [flt(d['monthly_consumption']) for d in monthly_data]
        mean_consumption = np.mean(consumptions)
        
        if mean_consumption == 0:
            return 0
        
        # Calculate coefficient of variation as seasonality indicator
        cv = np.std(consumptions) / mean_consumption
        seasonality_score = min(cv * 100, 100)  # Cap at 100%
        
        return round(seasonality_score, 1)
        
    except Exception as e:
        frappe.log_error(f"Seasonality calculation error for {row.get('item_code', 'unknown')}: {str(e)}")
        return 0

def calculate_volatility_index(row):
    """Calculate demand volatility index"""
    try:
        predicted_consumption = flt(row.get('predicted_consumption', 0))
        confidence_score = flt(row.get('confidence_score', 70))
        movement_type = row.get('movement_type', '')
        
        # Base volatility from confidence score
        base_volatility = (100 - confidence_score) / 100
        
        # Adjust based on movement type
        type_multipliers = {
            'Critical': 2.0,
            'Fast Moving': 1.2,
            'Slow Moving': 0.8,
            'Non Moving': 0.5
        }
        
        multiplier = type_multipliers.get(movement_type, 1.0)
        volatility_index = base_volatility * multiplier
        
        return round(min(volatility_index, 2.0), 2)  # Cap at 2.0
        
    except Exception as e:
        frappe.log_error(f"Volatility calculation error for {row.get('item_code', 'unknown')}: {str(e)}")
        return 1.0

def calculate_risk_score(row):
    """Calculate composite risk score (0-100, higher = more risky)"""
    try:
        risk_score = 0
        
        # Stock level risk (40% weight)
        current_stock = flt(row.get('current_stock', 0))
        reorder_level = flt(row.get('reorder_level', 0))
        
        if reorder_level > 0:
            stock_ratio = current_stock / reorder_level
            if stock_ratio <= 0.5:
                risk_score += 40  # Very low stock
            elif stock_ratio <= 1.0:
                risk_score += 25  # Below reorder level
            elif stock_ratio <= 1.5:
                risk_score += 10  # Near reorder level
        else:
            if current_stock <= 0:
                risk_score += 40
        
        # Confidence risk (25% weight)
        confidence_score = flt(row.get('confidence_score', 70))
        confidence_risk = (100 - confidence_score) * 0.25
        risk_score += confidence_risk
        
        # Movement type risk (20% weight)
        movement_type = row.get('movement_type', '')
        movement_risks = {
            'Critical': 20,
            'Fast Moving': 15,
            'Slow Moving': 5,
            'Non Moving': 2
        }
        risk_score += movement_risks.get(movement_type, 10)
        
        # Volatility risk (15% weight)
        volatility_index = flt(row.get('volatility_index', 1.0))
        volatility_risk = min(volatility_index * 15, 15)
        risk_score += volatility_risk
        
        return round(min(risk_score, 100), 1)
        
    except Exception as e:
        frappe.log_error(f"Risk score calculation error for {row.get('item_code', 'unknown')}: {str(e)}")
        return 50.0  # Default medium risk

def get_ml_price_prediction(row):
    """Get ML price prediction for the item"""
    try:
        item_code = row.get('item_code')
        preferred_supplier = row.get('preferred_supplier')
        company = row.get('company')
        suggested_qty = flt(row.get('suggested_qty', 1))
        
        if not preferred_supplier or not item_code:
            return 0
        
        # Try to import ML supplier analyzer
        try:
            from ai_inventory.ml_supplier_analyzer import MLSupplierAnalyzer
            analyzer = MLSupplierAnalyzer()
            
            price_result = analyzer.predict_item_price(
                item_code, preferred_supplier, company, suggested_qty
            )
            
            if price_result.get('status') == 'success':
                return flt(price_result.get('predicted_price', 0))
        except ImportError:
            pass
        except Exception as e:
            frappe.log_error(f"ML analyzer failed for {item_code}: {str(e)}")
        
        # Fallback: Get last purchase price
        last_price = frappe.db.sql("""
            SELECT poi.rate
            FROM `tabPurchase Order Item` poi
            INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
            WHERE poi.item_code = %s 
            AND po.supplier = %s
            AND po.company = %s
            AND po.docstatus = 1
            ORDER BY po.transaction_date DESC
            LIMIT 1
        """, (item_code, preferred_supplier, company))
        
        return flt(last_price[0][0]) if last_price else 0
        
    except Exception as e:
        frappe.log_error(f"Price prediction error for {row.get('item_code', 'unknown')}: {str(e)}")
        return 0

def add_inventory_efficiency_metrics(df):
    """Add inventory efficiency and performance metrics"""
    try:
        # Calculate ABC classification based on consumption value
        if len(df) > 0:
            df['consumption_value'] = df['predicted_consumption'] * df['predicted_price']
            df = df.sort_values('consumption_value', ascending=False)
            
            total_items = len(df)
            df['abc_class'] = 'C'  # Default
            
            # A class - top 20% by value (80% of consumption)
            a_cutoff = int(total_items * 0.2)
            df.iloc[:a_cutoff, df.columns.get_loc('abc_class')] = 'A'
            
            # B class - next 30% by value (15% of consumption)
            b_cutoff = int(total_items * 0.5)
            df.iloc[a_cutoff:b_cutoff, df.columns.get_loc('abc_class')] = 'B'
        
        # Calculate inventory turns
        df['inventory_turns'] = df.apply(lambda row: 
            (row['predicted_consumption'] * 12) / max(row['current_stock'], 1), axis=1)
        
        # Calculate days of inventory
        df['days_of_inventory'] = df.apply(lambda row:
            (row['current_stock'] / max(row['predicted_consumption'] / 30, 0.1)), axis=1)
        
        return df
        
    except Exception as e:
        frappe.log_error(f"Inventory efficiency metrics failed: {str(e)}")
        return df

def apply_basic_enhancements(data):
    """Apply basic enhancements when pandas is not available"""
    try:
        enhanced_data = []
        
        for row in data:
            enhanced_row = row.copy()
            
            # Add default values for calculated fields
            enhanced_row['demand_trend'] = "Data Processing..."
            enhanced_row['seasonality_score'] = 0
            enhanced_row['volatility_index'] = 1.0
            enhanced_row['risk_score'] = 50.0  # Default medium risk
            enhanced_row['predicted_price'] = 0
            
            # Try to calculate basic risk score
            try:
                enhanced_row['risk_score'] = calculate_basic_risk_score(row)
            except:
                enhanced_row['risk_score'] = 50.0
            
            # Try to get last purchase price
            try:
                enhanced_row['predicted_price'] = get_simple_last_price(row)
            except:
                enhanced_row['predicted_price'] = 0
                
            enhanced_data.append(enhanced_row)
        
        return enhanced_data
        
    except Exception as e:
        frappe.log_error(f"Basic enhancement failed: {str(e)}")
        return data

def ensure_required_columns(df):
    """Ensure all required columns exist with proper defaults"""
    required_columns = {
        'predicted_consumption': 0,
        'reorder_level': 0,
        'suggested_qty': 0,
        'confidence_score': 70,
        'current_stock': 0,
        'movement_type': 'Unknown',
        'preferred_supplier': None,
        'item_code': '',
        'warehouse': '',
        'company': ''
    }
    
    for col, default_val in required_columns.items():
        if col not in df.columns:
            df[col] = default_val
        else:
            # Fill NaN values with defaults
            df[col] = df[col].fillna(default_val)
    
    return df

def safe_calculate_demand_trend(row):
    """Safe wrapper for demand trend calculation"""
    try:
        return calculate_demand_trend(row)
    except Exception as e:
        frappe.log_error(f"Demand trend calculation failed for {row.get('item_code', 'unknown')}: {str(e)}")
        return "Calculation Error"

def safe_calculate_seasonality_score(row):
    """Safe wrapper for seasonality score calculation"""
    try:
        return calculate_seasonality_score(row)
    except Exception as e:
        frappe.log_error(f"Seasonality calculation failed for {row.get('item_code', 'unknown')}: {str(e)}")
        return 0

def safe_calculate_volatility_index(row):
    """Safe wrapper for volatility index calculation"""
    try:
        return calculate_volatility_index(row)
    except Exception as e:
        frappe.log_error(f"Volatility calculation failed for {row.get('item_code', 'unknown')}: {str(e)}")
        return 1.0

def safe_calculate_risk_score(row):
    """Safe wrapper for risk score calculation"""
    try:
        return calculate_risk_score(row)
    except Exception as e:
        frappe.log_error(f"Risk score calculation failed for {row.get('item_code', 'unknown')}: {str(e)}")
        return 50.0

def safe_get_ml_price_prediction(row):
    """Safe wrapper for ML price prediction"""
    try:
        return get_ml_price_prediction(row)
    except Exception as e:
        frappe.log_error(f"Price prediction failed for {row.get('item_code', 'unknown')}: {str(e)}")
        return 0

def safe_add_inventory_efficiency_metrics(df):
    """Safe wrapper for inventory efficiency metrics"""
    try:
        return add_inventory_efficiency_metrics(df)
    except Exception as e:
        frappe.log_error(f"Inventory efficiency metrics failed: {str(e)}")
        return df

def clean_data_values(data):
    """Clean NaN and infinite values from data"""
    try:
        import math
        
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        # Set appropriate defaults for different field types
                        if 'score' in key or 'index' in key:
                            cleaned_row[key] = 0
                        elif 'price' in key or 'consumption' in key or 'qty' in key:
                            cleaned_row[key] = 0
                        else:
                            cleaned_row[key] = 0
                    else:
                        cleaned_row[key] = value
                else:
                    cleaned_row[key] = value
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
        
    except Exception as e:
        frappe.log_error(f"Data cleaning failed: {str(e)}")
        return data

def calculate_basic_risk_score(row):
    """Calculate basic risk score without complex calculations"""
    try:
        risk_score = 0
        
        # Stock level risk
        current_stock = flt(row.get('current_stock', 0))
        reorder_level = flt(row.get('reorder_level', 0))
        
        if reorder_level > 0:
            stock_ratio = current_stock / reorder_level
            if stock_ratio <= 0.5:
                risk_score += 40
            elif stock_ratio <= 1.0:
                risk_score += 25
            elif stock_ratio <= 1.5:
                risk_score += 10
        
        # Confidence risk
        confidence_score = flt(row.get('confidence_score', 70))
        confidence_risk = (100 - confidence_score) * 0.25
        risk_score += confidence_risk
        
        # Movement type risk
        movement_type = row.get('movement_type', '')
        movement_risks = {
            'Critical': 20,
            'Fast Moving': 15,
            'Slow Moving': 5,
            'Non Moving': 2
        }
        risk_score += movement_risks.get(movement_type, 10)
        
        return round(min(risk_score, 100), 1)
        
    except Exception:
        return 50.0

def get_simple_last_price(row):
    """Get simple last purchase price without ML analyzer"""
    try:
        item_code = row.get('item_code')
        preferred_supplier = row.get('preferred_supplier')
        company = row.get('company')
        
        if not preferred_supplier or not item_code:
            return 0
        
        last_price = frappe.db.sql("""
            SELECT poi.rate
            FROM `tabPurchase Order Item` poi
            INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
            WHERE poi.item_code = %s 
            AND po.supplier = %s
            AND po.company = %s
            AND po.docstatus = 1
            ORDER BY po.transaction_date DESC
            LIMIT 1
        """, (item_code, preferred_supplier, company))
        
        return flt(last_price[0][0]) if last_price else 0
        
    except Exception:
        return 0

def get_advanced_chart_data(filters):
    """Advanced chart data with multiple visualizations"""
    conditions = get_enhanced_conditions(filters)
    
    try:
        # Movement Type Distribution with Risk Analysis
        movement_risk_data = frappe.db.sql(f"""
            SELECT 
                aif.movement_type as name,
                COUNT(*) as count,
                SUM(CASE WHEN aif.reorder_alert = 1 THEN 1 ELSE 0 END) as alerts,
                AVG(aif.confidence_score) as avg_confidence,
                SUM(aif.current_stock * COALESCE(aif.predicted_consumption, 0)) as total_value
            FROM `tabAI Inventory Forecast` aif
            WHERE 1=1 {conditions}
            GROUP BY aif.movement_type
            ORDER BY count DESC
        """, filters, as_dict=True)
        
        # Time-based Alert Trend (last 30 days)
        alert_trend = frappe.db.sql(f"""
            SELECT 
                DATE(aif.last_forecast_date) as date,
                SUM(CASE WHEN aif.reorder_alert = 1 THEN 1 ELSE 0 END) as alerts,
                COUNT(*) as total_forecasts,
                AVG(aif.confidence_score) as avg_confidence
            FROM `tabAI Inventory Forecast` aif
            WHERE aif.last_forecast_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            {conditions}
            GROUP BY DATE(aif.last_forecast_date)
            ORDER BY date
        """, filters, as_dict=True)
        
        # Company-wise Performance
        company_performance = frappe.db.sql(f"""
            SELECT 
                aif.company as name,
                COUNT(*) as total_items,
                SUM(CASE WHEN aif.reorder_alert = 1 THEN 1 ELSE 0 END) as alerts,
                AVG(aif.confidence_score) as avg_confidence,
                COUNT(DISTINCT aif.warehouse) as warehouses
            FROM `tabAI Inventory Forecast` aif
            WHERE 1=1 {conditions}
            GROUP BY aif.company
            ORDER BY total_items DESC
        """, filters, as_dict=True)
        
        return {
            "data": {
                "labels": [d.name for d in movement_risk_data],
                "datasets": [
                    {
                        "name": "Item Count",
                        "values": [d.count for d in movement_risk_data]
                    },
                    {
                        "name": "Reorder Alerts",
                        "values": [d.alerts for d in movement_risk_data]
                    }
                ]
            },
            "type": "bar",
            "height": 350,
            "colors": ["#28a745", "#ffc107", "#dc3545", "#6f42c1"],
            "axisOptions": {
                "xAxisMode": "tick",
                "yAxisMode": "tick"
            },
            "barOptions": {
                "spaceRatio": 0.5
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Advanced chart data failed: {str(e)}")
        return {"data": {"labels": [], "datasets": []}, "type": "bar"}

def get_smart_summary_data(filters):
    """Enhanced summary with data science insights"""
    conditions = get_enhanced_conditions(filters)
    
    try:
        # Main statistics
        main_stats = frappe.db.sql(f"""
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN aif.reorder_alert = 1 THEN 1 ELSE 0 END) as reorder_alerts,
                SUM(CASE WHEN aif.movement_type = 'Fast Moving' THEN 1 ELSE 0 END) as fast_moving,
                SUM(CASE WHEN aif.movement_type = 'Slow Moving' THEN 1 ELSE 0 END) as slow_moving,
                SUM(CASE WHEN aif.movement_type = 'Non Moving' THEN 1 ELSE 0 END) as non_moving,
                SUM(CASE WHEN aif.movement_type = 'Critical' THEN 1 ELSE 0 END) as critical,
                AVG(aif.confidence_score) as avg_confidence,
                COUNT(DISTINCT aif.company) as companies,
                COUNT(DISTINCT aif.warehouse) as warehouses,
                COUNT(DISTINCT aif.preferred_supplier) as suppliers
            FROM `tabAI Inventory Forecast` aif
            WHERE 1=1 {conditions}
        """, filters, as_dict=True)[0]
        
        # Risk analysis
        risk_stats = frappe.db.sql(f"""
            SELECT 
                SUM(CASE WHEN aif.confidence_score < 50 THEN 1 ELSE 0 END) as high_risk,
                SUM(CASE WHEN aif.confidence_score BETWEEN 50 AND 80 THEN 1 ELSE 0 END) as medium_risk,
                SUM(CASE WHEN aif.confidence_score > 80 THEN 1 ELSE 0 END) as low_risk,
                SUM(aif.current_stock * COALESCE(aif.predicted_consumption, 0)) as total_forecasted_value
            FROM `tabAI Inventory Forecast` aif
            WHERE 1=1 {conditions}
        """, filters, as_dict=True)[0]
        
        # Calculate efficiency metrics
        total_items = main_stats.total_items or 0
        alert_percentage = (main_stats.reorder_alerts / total_items * 100) if total_items > 0 else 0
        avg_confidence = main_stats.avg_confidence or 0
        
        # Determine system health
        if avg_confidence > 80 and alert_percentage < 20:
            system_health = "Excellent"
            health_indicator = "Green"
        elif avg_confidence > 60 and alert_percentage < 40:
            system_health = "Good"
            health_indicator = "Orange"
        else:
            system_health = "Needs Attention"
            health_indicator = "Red"
        
        return [
            {
                "value": total_items,
                "label": "Total Items Analyzed",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": main_stats.reorder_alerts or 0,
                "label": f"Reorder Alerts ({alert_percentage:.1f}%)",
                "datatype": "Int", 
                "indicator": "Red" if main_stats.reorder_alerts > 0 else "Green"
            },
            {
                "value": main_stats.critical or 0,
                "label": "Critical Items",
                "datatype": "Int",
                "indicator": "Red" if main_stats.critical > 0 else "Green"
            },
            {
                "value": main_stats.fast_moving or 0,
                "label": "Fast Moving",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": main_stats.slow_moving or 0,
                "label": "Slow Moving", 
                "datatype": "Int",
                "indicator": "Orange"
            },
            {
                "value": main_stats.non_moving or 0,
                "label": "Non Moving",
                "datatype": "Int",
                "indicator": "Red"
            },
            {
                "value": f"{avg_confidence:.1f}%",
                "label": "AI Confidence Avg",
                "datatype": "Data",
                "indicator": "Green" if avg_confidence > 80 else "Orange" if avg_confidence > 60 else "Red"
            },
            {
                "value": system_health,
                "label": "System Health",
                "datatype": "Data",
                "indicator": health_indicator
            },
            {
                "value": main_stats.companies or 0,
                "label": "Companies",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": main_stats.warehouses or 0,
                "label": "Warehouses",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": main_stats.suppliers or 0,
                "label": "Suppliers",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": risk_stats.high_risk or 0,
                "label": "High Risk Items",
                "datatype": "Int",
                "indicator": "Red" if risk_stats.high_risk > 0 else "Green"
            }
        ]
        
    except Exception as e:
        frappe.log_error(f"Smart summary data failed: {str(e)}")
        return [
            {
                "value": "Error",
                "label": "Data Load Failed",
                "datatype": "Data",
                "indicator": "Red"
            }
        ]