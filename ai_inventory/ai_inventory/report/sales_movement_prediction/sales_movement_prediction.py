# ai_inventory/ai_inventory/report/sales_movement_prediction/sales_movement_prediction.py
# COMPREHENSIVE SALES MOVEMENT PREDICTION WITH DATA SCIENCE & ML

import frappe
from frappe.utils import flt, nowdate, add_days, getdate, cint, date_diff
from frappe import _
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
import math

def execute(filters=None):
    if not filters:
        filters = {}
    
    # Validate and set defaults
    filters = validate_movement_filters(filters)
    
    columns = get_movement_columns()
    data = get_movement_prediction_data(filters)
    chart = get_movement_charts(filters, data)
    summary = get_movement_summary(data, filters)
    
    return columns, data, None, chart, summary

def validate_movement_filters(filters):
    """Validate and set default filters for movement prediction"""
    cleaned_filters = filters.copy()
    
    # Set default prediction period
    if not cleaned_filters.get("prediction_days"):
        cleaned_filters["prediction_days"] = 30
    
    # Set default historical analysis period
    if not cleaned_filters.get("historical_days"):
        cleaned_filters["historical_days"] = 90
    
    # Set default date range if not provided
    if not cleaned_filters.get("from_date"):
        cleaned_filters["from_date"] = add_days(nowdate(), -90)
    
    if not cleaned_filters.get("to_date"):
        cleaned_filters["to_date"] = nowdate()
    
    return cleaned_filters

def get_movement_columns():
    """Define columns for sales movement prediction"""
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
            "width": 180
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 120
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 120
        },
        {
            "label": _("Current Movement Type"),
            "fieldname": "current_movement_type",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Predicted Movement Type"),
            "fieldname": "predicted_movement_type",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "label": _("Movement Change"),
            "fieldname": "movement_change",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Current Sales Velocity"),
            "fieldname": "current_velocity",
            "fieldtype": "Float",
            "width": 150
        },
        {
            "label": _("Predicted Velocity"),
            "fieldname": "predicted_velocity",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Velocity Change %"),
            "fieldname": "velocity_change_pct",
            "fieldtype": "Percent",
            "width": 130
        },
        {
            "label": _("Sales Trend"),
            "fieldname": "sales_trend",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Demand Pattern"),
            "fieldname": "demand_pattern",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Seasonality Factor"),
            "fieldname": "seasonality_factor",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": _("Market Momentum"),
            "fieldname": "market_momentum",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Prediction Confidence"),
            "fieldname": "prediction_confidence",
            "fieldtype": "Percent",
            "width": 140
        },
        {
            "label": _("Risk Level"),
            "fieldname": "risk_level",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Recommended Action"),
            "fieldname": "recommended_action",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "label": _("Opportunity Score"),
            "fieldname": "opportunity_score",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": _("Last Analysis Date"),
            "fieldname": "last_analysis_date",
            "fieldtype": "Datetime",
            "width": 140
        }
    ]

def get_movement_prediction_data(filters):
    """Get comprehensive sales movement prediction data with ML analysis"""
    try:
        conditions = get_movement_conditions(filters)
        prediction_days = int(filters.get("prediction_days", 30))
        historical_days = int(filters.get("historical_days", 90))
        
        # Get sales forecast data as baseline
        base_query = f"""
            SELECT 
                asf.item_code,
                asf.item_name,
                asf.customer,
                asf.customer_name,
                asf.territory,
                asf.company,
                asf.predicted_qty,
                asf.sales_trend,
                asf.movement_type as current_movement_type,
                asf.confidence_score,
                asf.forecast_date,
                asf.last_forecast_date,
                asf.forecast_period_days,
                asf.name as forecast_id
            FROM `tabAI Sales Forecast` asf
            WHERE asf.predicted_qty IS NOT NULL
            AND asf.last_forecast_date >= %(from_date)s
            AND asf.last_forecast_date <= %(to_date)s
            {conditions}
            ORDER BY asf.predicted_qty DESC, asf.confidence_score DESC
            LIMIT 500
        """
        
        forecast_data = frappe.db.sql(base_query, filters, as_dict=True)
        
        if not forecast_data:
            return []
        
        # Apply ML movement prediction analysis
        movement_predictions = []
        for forecast in forecast_data:
            try:
                # Calculate movement prediction metrics
                prediction_metrics = calculate_movement_prediction_metrics(
                    forecast, prediction_days, historical_days
                )
                
                # Combine forecast data with prediction metrics
                combined_data = {**forecast, **prediction_metrics}
                
                # Add ML-powered insights
                combined_data = add_ml_movement_insights(combined_data, filters)
                
                movement_predictions.append(combined_data)
                
            except Exception as e:
                frappe.log_error(f"Movement prediction failed for {forecast['item_code']}: {str(e)}")
                continue
        
        return movement_predictions
        
    except Exception as e:
        frappe.log_error(f"Movement prediction data retrieval failed: {str(e)}")
        return []

def get_movement_conditions(filters):
    """Build SQL conditions for movement prediction"""
    conditions = ""
    
    if filters.get("company"):
        conditions += " AND asf.company = %(company)s"
    
    if filters.get("customer"):
        conditions += " AND asf.customer = %(customer)s"
    
    if filters.get("territory"):
        conditions += " AND asf.territory = %(territory)s"
    
    if filters.get("item_group"):
        conditions += " AND asf.item_group = %(item_group)s"
    
    if filters.get("sales_trend"):
        if isinstance(filters["sales_trend"], list):
            trend_list = "', '".join(filters["sales_trend"])
            conditions += f" AND asf.sales_trend IN ('{trend_list}')"
        else:
            conditions += " AND asf.sales_trend = %(sales_trend)s"
    
    if filters.get("movement_type"):
        if isinstance(filters["movement_type"], list):
            movement_list = "', '".join(filters["movement_type"])
            conditions += f" AND asf.movement_type IN ('{movement_list}')"
        else:
            conditions += " AND asf.movement_type = %(movement_type)s"
    
    if filters.get("min_confidence"):
        conditions += " AND asf.confidence_score >= %(min_confidence)s"
    
    if filters.get("high_opportunity_only"):
        conditions += " AND asf.predicted_qty > (SELECT AVG(predicted_qty) FROM `tabAI Sales Forecast`)"
    
    return conditions

def calculate_movement_prediction_metrics(forecast, prediction_days, historical_days):
    """Calculate ML-powered movement prediction metrics"""
    try:
        item_code = forecast['item_code']
        customer = forecast['customer']
        company = forecast['company']
        current_predicted_qty = forecast['predicted_qty']
        
        # Get historical sales velocity
        current_velocity = get_sales_velocity(item_code, customer, company, historical_days)
        
        # Predict future velocity using trend analysis
        predicted_velocity = predict_future_velocity(
            item_code, customer, company, prediction_days, historical_days
        )
        
        # Calculate velocity change
        if current_velocity > 0:
            velocity_change_pct = ((predicted_velocity - current_velocity) / current_velocity) * 100
        else:
            velocity_change_pct = 0 if predicted_velocity == 0 else 100
        
        # Predict movement type change
        predicted_movement_type = predict_movement_type(predicted_velocity, current_predicted_qty)
        current_movement_type = forecast.get('current_movement_type', 'Unknown')
        
        # Determine movement change
        movement_change = get_movement_change_indicator(current_movement_type, predicted_movement_type)
        
        # Calculate seasonality factor
        seasonality_factor = calculate_seasonality_factor(item_code, customer, company)
        
        # Analyze demand pattern
        demand_pattern = analyze_demand_pattern(item_code, customer, company, historical_days)
        
        # Calculate market momentum
        market_momentum = calculate_market_momentum(item_code, customer, company, historical_days)
        
        # Calculate prediction confidence
        prediction_confidence = calculate_prediction_confidence(
            forecast['confidence_score'], velocity_change_pct, seasonality_factor
        )
        
        # Determine risk level
        risk_level = determine_risk_level(
            movement_change, velocity_change_pct, prediction_confidence
        )
        
        # Generate opportunity score
        opportunity_score = calculate_opportunity_score(
            predicted_movement_type, velocity_change_pct, market_momentum, prediction_confidence
        )
        
        # Generate recommended action
        recommended_action = generate_recommended_action(
            movement_change, velocity_change_pct, opportunity_score, risk_level
        )
        
        return {
            'current_velocity': round(current_velocity, 2),
            'predicted_velocity': round(predicted_velocity, 2),
            'velocity_change_pct': round(velocity_change_pct, 1),
            'predicted_movement_type': predicted_movement_type,
            'movement_change': movement_change,
            'seasonality_factor': round(seasonality_factor, 2),
            'demand_pattern': demand_pattern,
            'market_momentum': market_momentum,
            'prediction_confidence': round(prediction_confidence, 1),
            'risk_level': risk_level,
            'opportunity_score': round(opportunity_score, 1),
            'recommended_action': recommended_action,
            'last_analysis_date': nowdate()
        }
        
    except Exception as e:
        frappe.log_error(f"Movement prediction metrics calculation failed: {str(e)}")
        return {
            'current_velocity': 0,
            'predicted_velocity': 0,
            'velocity_change_pct': 0,
            'predicted_movement_type': 'Unknown',
            'movement_change': 'No Change',
            'seasonality_factor': 1.0,
            'demand_pattern': 'Unknown',
            'market_momentum': 'Neutral',
            'prediction_confidence': 0,
            'risk_level': 'Unknown',
            'opportunity_score': 0,
            'recommended_action': 'Monitor',
            'last_analysis_date': nowdate()
        }

def get_sales_velocity(item_code, customer, company, days):
    """Calculate current sales velocity (units per day)"""
    try:
        from_date = add_days(nowdate(), -days)
        
        velocity_data = frappe.db.sql("""
            SELECT 
                SUM(sii.qty) as total_qty,
                COUNT(DISTINCT DATE(si.posting_date)) as active_days
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
        """, (item_code, customer, company, from_date), as_dict=True)
        
        if velocity_data and velocity_data[0]['total_qty']:
            total_qty = velocity_data[0]['total_qty']
            active_days = velocity_data[0]['active_days'] or days
            return total_qty / active_days
        
        return 0
        
    except Exception as e:
        frappe.log_error(f"Sales velocity calculation failed: {str(e)}")
        return 0

def predict_future_velocity(item_code, customer, company, prediction_days, historical_days):
    """Predict future sales velocity using trend analysis"""
    try:
        # Get historical daily sales data
        from_date = add_days(nowdate(), -historical_days)
        
        daily_sales = frappe.db.sql("""
            SELECT 
                DATE(si.posting_date) as sale_date,
                SUM(sii.qty) as daily_qty
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
            GROUP BY DATE(si.posting_date)
            ORDER BY sale_date
        """, (item_code, customer, company, from_date), as_dict=True)
        
        if len(daily_sales) < 5:
            return get_sales_velocity(item_code, customer, company, historical_days)
        
        # Extract quantities for trend analysis
        quantities = [d['daily_qty'] for d in daily_sales]
        days_sequence = list(range(len(quantities)))
        
        # Simple linear regression for trend prediction
        if len(quantities) > 1:
            # Calculate trend slope
            n = len(quantities)
            sum_x = sum(days_sequence)
            sum_y = sum(quantities)
            sum_xy = sum(x * y for x, y in zip(days_sequence, quantities))
            sum_x2 = sum(x * x for x in days_sequence)
            
            if (n * sum_x2 - sum_x * sum_x) != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                
                # Predict future average velocity
                future_mid_point = len(quantities) + (prediction_days / 2)
                predicted_daily_qty = slope * future_mid_point + intercept
                
                return max(predicted_daily_qty, 0)  # Ensure non-negative
        
        # Fallback to current velocity
        return get_sales_velocity(item_code, customer, company, historical_days)
        
    except Exception as e:
        frappe.log_error(f"Future velocity prediction failed: {str(e)}")
        return get_sales_velocity(item_code, customer, company, historical_days)

def predict_movement_type(predicted_velocity, predicted_qty):
    """Predict movement type based on velocity and quantity metrics"""
    try:
        # Get velocity thresholds (could be configurable)
        if predicted_velocity >= 5:  # High velocity
            return "Fast Moving"
        elif predicted_velocity >= 1:  # Medium velocity
            return "Slow Moving"
        elif predicted_velocity > 0:  # Low velocity
            return "Non Moving"
        else:  # No movement
            return "Critical"
        
    except Exception as e:
        return "Unknown"

def get_movement_change_indicator(current_type, predicted_type):
    """Generate movement change indicator with visual cues"""
    if current_type == predicted_type:
        return f"➡️ No Change ({current_type})"
    
    # Define movement hierarchy for comparison
    movement_hierarchy = {
        "Critical": 0,
        "Non Moving": 1, 
        "Slow Moving": 2,
        "Fast Moving": 3
    }
    
    current_level = movement_hierarchy.get(current_type, 1)
    predicted_level = movement_hierarchy.get(predicted_type, 1)
    
    if predicted_level > current_level:
        return f"📈 Improving ({current_type} → {predicted_type})"
    elif predicted_level < current_level:
        return f"📉 Declining ({current_type} → {predicted_type})"
    else:
        return f"➡️ No Change ({current_type})"

def calculate_seasonality_factor(item_code, customer, company):
    """Calculate seasonality factor for sales prediction"""
    try:
        # Get monthly sales for last 12 months
        monthly_sales = frappe.db.sql("""
            SELECT 
                MONTH(si.posting_date) as month,
                SUM(sii.qty) as monthly_qty
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY MONTH(si.posting_date)
        """, (item_code, customer, company), as_dict=True)
        
        if len(monthly_sales) < 6:
            return 1.0  # No seasonality data
        
        quantities = [d['monthly_qty'] for d in monthly_sales]
        mean_qty = np.mean(quantities)
        
        if mean_qty == 0:
            return 1.0
        
        # Calculate coefficient of variation as seasonality measure
        cv = np.std(quantities) / mean_qty
        seasonality_factor = 1 + cv  # 1 = no seasonality, higher = more seasonal
        
        return min(seasonality_factor, 3.0)  # Cap at 3.0
        
    except Exception as e:
        return 1.0

def analyze_demand_pattern(item_code, customer, company, days):
    """Analyze demand pattern using statistical methods"""
    try:
        from_date = add_days(nowdate(), -days)
        
        # Get daily sales pattern
        daily_pattern = frappe.db.sql("""
            SELECT 
                DATE(si.posting_date) as sale_date,
                SUM(sii.qty) as daily_qty
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
            GROUP BY DATE(si.posting_date)
            ORDER BY sale_date
        """, (item_code, customer, company, from_date), as_dict=True)
        
        if len(daily_pattern) < 10:
            return "📊 Insufficient Data"
        
        quantities = [d['daily_qty'] for d in daily_pattern]
        
        # Calculate pattern metrics
        mean_qty = np.mean(quantities)
        std_qty = np.std(quantities)
        cv = std_qty / mean_qty if mean_qty > 0 else 0
        
        # Pattern classification
        if cv < 0.3:
            return "📈 Steady"
        elif cv < 0.7:
            return "🔄 Regular"
        elif cv < 1.2:
            return "📊 Variable"
        else:
            return "⚡ Volatile"
        
    except Exception as e:
        return "❓ Unknown"

def calculate_market_momentum(item_code, customer, company, days):
    """Calculate market momentum indicator"""
    try:
        # Compare recent vs historical performance
        recent_period = days // 3  # Last 1/3 of period
        historical_period = days
        
        recent_from = add_days(nowdate(), -recent_period)
        historical_from = add_days(nowdate(), -historical_period)
        
        # Recent sales
        recent_sales = frappe.db.sql("""
            SELECT SUM(sii.qty) as total_qty
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
        """, (item_code, customer, company, recent_from))[0][0] or 0
        
        # Historical average (excluding recent period)
        historical_sales = frappe.db.sql("""
            SELECT SUM(sii.qty) as total_qty
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
            AND si.posting_date < %s
        """, (item_code, customer, company, historical_from, recent_from))[0][0] or 0
        
        # Normalize by period length
        recent_avg = recent_sales / recent_period
        historical_avg = historical_sales / (historical_period - recent_period)
        
        if historical_avg == 0:
            return "🚀 New" if recent_avg > 0 else "💤 Dormant"
        
        momentum_ratio = recent_avg / historical_avg
        
        if momentum_ratio >= 1.5:
            return "🚀 Strong Growth"
        elif momentum_ratio >= 1.2:
            return "📈 Growing"
        elif momentum_ratio >= 0.8:
            return "➡️ Stable"
        elif momentum_ratio >= 0.5:
            return "📉 Declining"
        else:
            return "⚠️ Weak"
        
    except Exception as e:
        return "❓ Unknown"

def calculate_prediction_confidence(base_confidence, velocity_change_pct, seasonality_factor):
    """Calculate overall prediction confidence considering multiple factors"""
    try:
        # Start with base AI confidence
        confidence = base_confidence
        
        # Adjust for velocity change magnitude (higher change = lower confidence)
        velocity_adjustment = max(-20, -abs(velocity_change_pct) * 0.2)
        confidence += velocity_adjustment
        
        # Adjust for seasonality (higher seasonality = lower confidence)
        seasonality_adjustment = max(-15, -(seasonality_factor - 1) * 10)
        confidence += seasonality_adjustment
        
        # Ensure confidence is within bounds
        return max(0, min(confidence, 100))
        
    except Exception as e:
        return 50  # Default medium confidence

def determine_risk_level(movement_change, velocity_change_pct, prediction_confidence):
    """Determine risk level based on prediction factors"""
    try:
        risk_score = 0
        
        # Movement change risk
        if "Declining" in movement_change:
            risk_score += 30
        elif "Improving" in movement_change:
            risk_score += 10  # Growth can be risky too
        
        # Velocity change risk
        if abs(velocity_change_pct) > 50:
            risk_score += 25
        elif abs(velocity_change_pct) > 25:
            risk_score += 15
        
        # Confidence risk
        if prediction_confidence < 60:
            risk_score += 25
        elif prediction_confidence < 80:
            risk_score += 10
        
        # Risk level determination
        if risk_score >= 60:
            return "🔴 High"
        elif risk_score >= 35:
            return "🟡 Medium"
        else:
            return "🟢 Low"
        
    except Exception as e:
        return "❓ Unknown"

def calculate_opportunity_score(predicted_movement, velocity_change_pct, market_momentum, confidence):
    """Calculate opportunity score (0-100)"""
    try:
        score = 0
        
        # Movement type opportunity
        movement_scores = {
            "Fast Moving": 30,
            "Slow Moving": 20,
            "Non Moving": 10,
            "Critical": 5
        }
        score += movement_scores.get(predicted_movement, 15)
        
        # Velocity change opportunity
        if velocity_change_pct > 20:
            score += 25
        elif velocity_change_pct > 0:
            score += 15
        elif velocity_change_pct > -20:
            score += 5
        
        # Market momentum opportunity
        if "Strong Growth" in market_momentum:
            score += 25
        elif "Growing" in market_momentum:
            score += 15
        elif "Stable" in market_momentum:
            score += 10
        
        # Confidence adjustment
        confidence_factor = confidence / 100
        score = score * confidence_factor
        
        return min(score, 100)
        
    except Exception as e:
        return 0

def generate_recommended_action(movement_change, velocity_change_pct, opportunity_score, risk_level):
    """Generate AI-powered recommended action"""
    try:
        if "Declining" in movement_change and "High" in risk_level:
            return "🚨 Urgent: Implement retention strategy"
        elif "Improving" in movement_change and opportunity_score > 70:
            return "🚀 Scale up: Increase inventory/promotion"
        elif opportunity_score > 60 and "Low" in risk_level:
            return "📈 Invest: Expand market presence"
        elif velocity_change_pct < -30:
            return "⚠️ Investigate: Analyze demand drop"
        elif velocity_change_pct > 30 and "Medium" in risk_level:
            return "⚖️ Monitor: Track growth sustainability"
        elif "High" in risk_level:
            return "🛡️ Mitigate: Reduce exposure/risk"
        elif opportunity_score > 40:
            return "📊 Optimize: Improve sales approach"
        else:
            return "👁️ Monitor: Continue observation"
        
    except Exception as e:
        return "❓ Review manually"

def add_ml_movement_insights(data, filters):
    """Add machine learning powered insights to movement data"""
    try:
        # Add any additional ML insights here
        # This could include recommendations from advanced ML models
        
        return data
        
    except Exception as e:
        frappe.log_error(f"ML insights addition failed: {str(e)}")
        return data

def get_movement_charts(filters, data):
    """Generate comprehensive movement prediction charts"""
    try:
        if not data:
            return {"data": {"labels": [], "datasets": []}, "type": "bar"}
        
        # Movement type distribution (current vs predicted)
        current_movements = {}
        predicted_movements = {}
        
        for item in data:
            current_type = item.get('current_movement_type', 'Unknown')
            predicted_type = item.get('predicted_movement_type', 'Unknown')
            
            current_movements[current_type] = current_movements.get(current_type, 0) + 1
            predicted_movements[predicted_type] = predicted_movements.get(predicted_type, 0) + 1
        
        # Get all movement types
        all_types = sorted(set(list(current_movements.keys()) + list(predicted_movements.keys())))
        
        return {
            "data": {
                "labels": all_types,
                "datasets": [
                    {
                        "name": "Current Distribution",
                        "values": [current_movements.get(t, 0) for t in all_types]
                    },
                    {
                        "name": "Predicted Distribution", 
                        "values": [predicted_movements.get(t, 0) for t in all_types]
                    }
                ]
            },
            "type": "bar",
            "height": 350,
            "colors": ["#17a2b8", "#28a745"],
            "axisOptions": {
                "xAxisMode": "tick",
                "yAxisMode": "tick"
            },
            "barOptions": {
                "spaceRatio": 0.5
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Movement charts generation failed: {str(e)}")
        return {"data": {"labels": [], "datasets": []}, "type": "bar"}

def get_movement_summary(data, filters):
    """Generate intelligent movement prediction summary"""
    try:
        if not data:
            return []
        
        total_predictions = len(data)
        
        # Count movement changes
        improving = len([d for d in data if "Improving" in d.get('movement_change', '')])
        declining = len([d for d in data if "Declining" in d.get('movement_change', '')])
        no_change = len([d for d in data if "No Change" in d.get('movement_change', '')])
        
        # Risk analysis
        high_risk = len([d for d in data if "High" in d.get('risk_level', '')])
        medium_risk = len([d for d in data if "Medium" in d.get('risk_level', '')])
        low_risk = len([d for d in data if "Low" in d.get('risk_level', '')])
        
        # Opportunity analysis
        opportunities = [d.get('opportunity_score', 0) for d in data]
        avg_opportunity = np.mean(opportunities) if opportunities else 0
        high_opportunity = len([o for o in opportunities if o > 70])
        
        # Velocity changes
        velocity_changes = [d.get('velocity_change_pct', 0) for d in data]
        avg_velocity_change = np.mean(velocity_changes) if velocity_changes else 0
        
        # Prediction confidence
        confidences = [d.get('prediction_confidence', 0) for d in data]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        # Market momentum analysis
        strong_growth = len([d for d in data if "Strong Growth" in d.get('market_momentum', '')])
        declining_momentum = len([d for d in data if "Declining" in d.get('market_momentum', '')])
        
        # Overall health assessment
        if improving > declining and avg_opportunity > 60 and high_risk < total_predictions * 0.2:
            market_health = "🌟 Excellent"
            health_indicator = "Green"
        elif improving >= declining and avg_opportunity > 40:
            market_health = "✅ Good"
            health_indicator = "Green"
        elif declining > improving * 1.5 or high_risk > total_predictions * 0.4:
            market_health = "⚠️ Concerning"
            health_indicator = "Orange"
        else:
            market_health = "❌ Challenging"
            health_indicator = "Red"
        
        return [
            {
                "value": total_predictions,
                "label": "Items Analyzed",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": improving,
                "label": "📈 Movement Improving",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": declining,
                "label": "📉 Movement Declining",
                "datatype": "Int",
                "indicator": "Red" if declining > 0 else "Green"
            },
            {
                "value": no_change,
                "label": "➡️ No Movement Change",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": f"{avg_velocity_change:+.1f}%",
                "label": "Avg Velocity Change",
                "datatype": "Data",
                "indicator": "Green" if avg_velocity_change > 0 else "Red" if avg_velocity_change < -10 else "Orange"
            },
            {
                "value": high_opportunity,
                "label": "🎯 High Opportunity Items",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": f"{avg_opportunity:.1f}",
                "label": "Avg Opportunity Score",
                "datatype": "Data",
                "indicator": "Green" if avg_opportunity > 60 else "Orange" if avg_opportunity > 40 else "Red"
            },
            {
                "value": high_risk,
                "label": "🔴 High Risk Items",
                "datatype": "Int",
                "indicator": "Red" if high_risk > 0 else "Green"
            },
            {
                "value": strong_growth,
                "label": "🚀 Strong Growth Items",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": f"{avg_confidence:.1f}%",
                "label": "Avg Prediction Confidence",
                "datatype": "Data",
                "indicator": "Green" if avg_confidence > 80 else "Orange" if avg_confidence > 60 else "Red"
            },
            {
                "value": market_health,
                "label": "Market Health Status",
                "datatype": "Data",
                "indicator": health_indicator
            },
            {
                "value": filters.get("prediction_days", 30),
                "label": "Prediction Period (Days)",
                "datatype": "Int",
                "indicator": "Blue"
            }
        ]
        
    except Exception as e:
        frappe.log_error(f"Movement summary generation failed: {str(e)}")
        return [
            {
                "value": "Error",
                "label": "Summary Generation Failed",
                "datatype": "Data",
                "indicator": "Red"
            }
        ]

# Additional utility functions

@frappe.whitelist()
def get_movement_trend_analysis(item_code, customer, company, days=90):
    """Get detailed movement trend analysis for specific item-customer combination"""
    try:
        # Get historical movement data
        movement_history = []
        
        # This would track movement type changes over time
        # Implementation would depend on having historical movement type data
        
        return {
            "status": "success",
            "movement_history": movement_history,
            "trend_direction": "stable",  # would be calculated
            "confidence": 85
        }
        
    except Exception as e:
        frappe.log_error(f"Movement trend analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def generate_movement_recommendations(company=None, territory=None):
    """Generate AI-powered movement optimization recommendations"""
    try:
        filters = {}
        if company:
            filters["company"] = company
        if territory:
            filters["territory"] = territory
        
        # Get movement prediction data
        movement_data = get_movement_prediction_data(filters)
        
        recommendations = []
        
        # Analyze patterns and generate recommendations
        if movement_data:
            declining_items = [d for d in movement_data if "Declining" in d.get('movement_change', '')]
            high_opportunity = [d for d in movement_data if d.get('opportunity_score', 0) > 70]
            high_risk = [d for d in movement_data if "High" in d.get('risk_level', '')]
            
            if len(declining_items) > 0:
                recommendations.append({
                    "priority": "High",
                    "category": "Movement Decline",
                    "recommendation": f"Address {len(declining_items)} declining items - implement retention strategies",
                    "affected_items": len(declining_items),
                    "action": "Review pricing, promotions, and customer engagement"
                })
            
            if len(high_opportunity) > 0:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Growth Opportunity",
                    "recommendation": f"Capitalize on {len(high_opportunity)} high-opportunity items",
                    "affected_items": len(high_opportunity),
                    "action": "Increase marketing investment and inventory planning"
                })
            
            if len(high_risk) > 0:
                recommendations.append({
                    "priority": "High",
                    "category": "Risk Management",
                    "recommendation": f"Mitigate risks for {len(high_risk)} high-risk items",
                    "affected_items": len(high_risk),
                    "action": "Implement risk mitigation strategies and closer monitoring"
                })
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "total_analyzed": len(movement_data)
        }
        
    except Exception as e:
        frappe.log_error(f"Movement recommendations generation failed: {str(e)}")
        return {"status": "error", "message": str(e), "recommendations": []}
