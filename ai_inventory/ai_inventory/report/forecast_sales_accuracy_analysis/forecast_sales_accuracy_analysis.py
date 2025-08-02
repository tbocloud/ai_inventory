# ai_inventory/ai_inventory/report/forecast_sales_accuracy_analysis/forecast_sales_accuracy_analysis.py
# COMPREHENSIVE SALES FORECAST ACCURACY ANALYSIS WITH DATA SCIENCE & ML

import frappe
from frappe.utils import flt, nowdate, add_days, getdate, cint, date_diff
from frappe import _
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error
import math

def execute(filters=None):
    if not filters:
        filters = {}
    
    # Validate and set defaults
    filters = validate_sales_accuracy_filters(filters)
    
    columns = get_sales_accuracy_columns()
    data = get_sales_accuracy_analysis_data(filters)
    chart = get_sales_accuracy_charts(filters, data)
    summary = get_sales_accuracy_summary(data, filters)
    
    return columns, data, None, chart, summary

def validate_sales_accuracy_filters(filters):
    """Validate and set default filters for sales accuracy analysis"""
    cleaned_filters = filters.copy()
    
    # Set default date range (last 30 days)
    if not cleaned_filters.get("from_date"):
        cleaned_filters["from_date"] = add_days(nowdate(), -30)
    
    if not cleaned_filters.get("to_date"):
        cleaned_filters["to_date"] = nowdate()
    
    # Set default accuracy threshold
    if not cleaned_filters.get("accuracy_threshold"):
        cleaned_filters["accuracy_threshold"] = 80.0
    
    # Set default analysis period
    if not cleaned_filters.get("analysis_period"):
        cleaned_filters["analysis_period"] = "30"
    
    return cleaned_filters

def get_sales_accuracy_columns():
    """Define columns for sales forecast accuracy analysis"""
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
            "width": 150
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 120
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 100
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 100
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Forecasted Sales Qty"),
            "fieldname": "forecasted_sales",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Actual Sales Qty"),
            "fieldname": "actual_sales",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Forecast Error"),
            "fieldname": "forecast_error",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Absolute Error"),
            "fieldname": "absolute_error",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Error %"),
            "fieldname": "error_percentage",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("Accuracy %"),
            "fieldname": "accuracy_percentage",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("AI Confidence"),
            "fieldname": "ai_confidence",
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "label": _("Confidence vs Accuracy"),
            "fieldname": "confidence_accuracy_gap",
            "fieldtype": "Float",
            "width": 150
        },
        {
            "label": _("Bias Direction"),
            "fieldname": "bias_direction",
            "fieldtype": "Data",
            "width": 110
        },
        {
            "label": _("Error Category"),
            "fieldname": "error_category",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Forecast Quality"),
            "fieldname": "forecast_quality",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Sales Trend"),
            "fieldname": "sales_trend",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Market Performance"),
            "fieldname": "market_performance",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Improvement Potential"),
            "fieldname": "improvement_potential",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Revenue Impact"),
            "fieldname": "revenue_impact",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Last Forecast Date"),
            "fieldname": "last_forecast_date",
            "fieldtype": "Datetime",
            "width": 140
        },
        {
            "label": _("Days Since Forecast"),
            "fieldname": "days_since_forecast",
            "fieldtype": "Int",
            "width": 130
        }
    ]

def get_sales_accuracy_analysis_data(filters):
    """Get comprehensive sales forecast accuracy analysis data"""
    try:
        conditions = get_sales_accuracy_conditions(filters)
        analysis_period = int(filters.get("analysis_period", 30))
        
        # Get sales forecast data with actual sales
        base_query = f"""
            SELECT 
                asf.item_code,
                asf.item_name,
                asf.customer,
                asf.customer_name,
                asf.territory,
                asf.company,
                asf.movement_type,
                asf.predicted_qty as forecasted_sales,
                asf.confidence_score as ai_confidence,
                asf.sales_trend,
                asf.last_forecast_date,
                asf.forecast_period_days,
                asf.name as forecast_id
            FROM `tabAI Sales Forecast` asf
            WHERE asf.predicted_qty > 0
            AND asf.last_forecast_date >= %(from_date)s
            AND asf.last_forecast_date <= %(to_date)s
            {conditions}
            ORDER BY asf.last_forecast_date DESC, asf.item_code
            LIMIT 500
        """
        
        forecast_data = frappe.db.sql(base_query, filters, as_dict=True)
        
        if not forecast_data:
            return []
        
        # Calculate actual sales and accuracy metrics for each forecast
        accuracy_data = []
        for forecast in forecast_data:
            try:
                # Get actual sales for the forecast period
                actual_sales = get_actual_sales(
                    forecast['item_code'],
                    forecast['customer'],
                    forecast['company'],
                    forecast['last_forecast_date'],
                    analysis_period
                )
                
                # Calculate accuracy metrics
                accuracy_metrics = calculate_sales_accuracy_metrics(
                    forecast['forecasted_sales'],
                    actual_sales,
                    forecast['ai_confidence']
                )
                
                # Combine forecast data with accuracy metrics
                combined_data = {**forecast, **accuracy_metrics}
                combined_data['actual_sales'] = actual_sales
                
                # Calculate days since forecast
                combined_data['days_since_forecast'] = date_diff(
                    nowdate(), getdate(forecast['last_forecast_date'])
                )
                
                # Add revenue impact calculation
                combined_data['revenue_impact'] = calculate_revenue_impact(
                    forecast['item_code'], 
                    accuracy_metrics['forecast_error']
                )
                
                # Add advanced sales analytics
                combined_data = add_advanced_sales_accuracy_analytics(combined_data)
                
                accuracy_data.append(combined_data)
                
            except Exception as e:
                frappe.log_error(f"Sales accuracy calculation failed for {forecast['item_code']}: {str(e)}")
                continue
        
        return accuracy_data
        
    except Exception as e:
        frappe.log_error(f"Sales accuracy analysis data retrieval failed: {str(e)}")
        return []

def get_sales_accuracy_conditions(filters):
    """Build SQL conditions for sales accuracy analysis"""
    conditions = ""
    
    if filters.get("company"):
        conditions += " AND asf.company = %(company)s"
    
    if filters.get("customer"):
        conditions += " AND asf.customer = %(customer)s"
    
    if filters.get("territory"):
        conditions += " AND asf.territory = %(territory)s"
    
    if filters.get("item_group"):
        conditions += " AND asf.item_group = %(item_group)s"
    
    if filters.get("movement_type"):
        if isinstance(filters["movement_type"], list):
            movement_list = "', '".join(filters["movement_type"])
            conditions += f" AND asf.movement_type IN ('{movement_list}')"
        else:
            conditions += " AND asf.movement_type = %(movement_type)s"
    
    if filters.get("sales_trend"):
        if isinstance(filters["sales_trend"], list):
            trend_list = "', '".join(filters["sales_trend"])
            conditions += f" AND asf.sales_trend IN ('{trend_list}')"
        else:
            conditions += " AND asf.sales_trend = %(sales_trend)s"
    
    if filters.get("min_confidence"):
        conditions += " AND asf.confidence_score >= %(min_confidence)s"
    
    if filters.get("accuracy_category"):
        # This will be applied after accuracy calculation
        pass
    
    return conditions

def get_actual_sales(item_code, customer, company, forecast_date, analysis_period):
    """Get actual sales for the specified period after forecast"""
    try:
        from_date = getdate(forecast_date)
        to_date = add_days(from_date, analysis_period)
        
        actual_sales = frappe.db.sql("""
            SELECT 
                SUM(sii.qty) as total_sales
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s 
            AND si.customer = %s
            AND si.company = %s
            AND si.docstatus = 1
            AND DATE(si.posting_date) >= %s
            AND DATE(si.posting_date) <= %s
        """, (item_code, customer, company, from_date, to_date))
        
        return flt(actual_sales[0][0]) if actual_sales and actual_sales[0][0] else 0
        
    except Exception as e:
        frappe.log_error(f"Actual sales calculation failed: {str(e)}")
        return 0

def calculate_sales_accuracy_metrics(forecasted, actual, confidence):
    """Calculate comprehensive sales accuracy metrics"""
    try:
        # Basic error calculations
        forecast_error = forecasted - actual
        absolute_error = abs(forecast_error)
        
        # Percentage calculations
        if actual > 0:
            error_percentage = (absolute_error / actual) * 100
            accuracy_percentage = max(0, 100 - error_percentage)
        else:
            if forecasted > 0:
                error_percentage = 100  # Complete miss if actual is 0 but forecast > 0
                accuracy_percentage = 0
            else:
                error_percentage = 0  # Perfect if both are 0
                accuracy_percentage = 100
        
        # Confidence vs accuracy gap
        confidence_accuracy_gap = confidence - accuracy_percentage
        
        # Bias direction
        if forecast_error > 0:
            bias_direction = "Over-forecast"
        elif forecast_error < 0:
            bias_direction = "Under-forecast"
        else:
            bias_direction = "Perfect"
        
        return {
            'forecast_error': round(forecast_error, 2),
            'absolute_error': round(absolute_error, 2),
            'error_percentage': round(error_percentage, 1),
            'accuracy_percentage': round(accuracy_percentage, 1),
            'confidence_accuracy_gap': round(confidence_accuracy_gap, 1),
            'bias_direction': bias_direction
        }
        
    except Exception as e:
        frappe.log_error(f"Sales accuracy metrics calculation failed: {str(e)}")
        return {
            'forecast_error': 0,
            'absolute_error': 0,
            'error_percentage': 0,
            'accuracy_percentage': 0,
            'confidence_accuracy_gap': 0,
            'bias_direction': 'Unknown'
        }

def calculate_revenue_impact(item_code, forecast_error):
    """Calculate revenue impact of forecast error"""
    try:
        # Get average selling price for the item
        avg_price = frappe.db.sql("""
            SELECT AVG(sii.rate) as avg_rate
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s
            AND si.docstatus = 1
            AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        """, (item_code,))
        
        if avg_price and avg_price[0][0]:
            price = flt(avg_price[0][0])
            return abs(forecast_error) * price
        
        return 0
        
    except Exception as e:
        frappe.log_error(f"Revenue impact calculation failed: {str(e)}")
        return 0

def add_advanced_sales_accuracy_analytics(data):
    """Add advanced analytics to sales accuracy data"""
    try:
        accuracy = data.get('accuracy_percentage', 0)
        error_pct = data.get('error_percentage', 0)
        confidence_gap = data.get('confidence_accuracy_gap', 0)
        sales_trend = data.get('sales_trend', 'Unknown')
        
        # Error categorization
        if error_pct <= 10:
            data['error_category'] = "🎯 Excellent"
        elif error_pct <= 25:
            data['error_category'] = "✅ Good"
        elif error_pct <= 50:
            data['error_category'] = "⚠️ Fair"
        elif error_pct <= 75:
            data['error_category'] = "❌ Poor"
        else:
            data['error_category'] = "🚫 Very Poor"
        
        # Forecast quality assessment
        if accuracy >= 90:
            data['forecast_quality'] = "🌟 Outstanding"
        elif accuracy >= 80:
            data['forecast_quality'] = "⭐ Excellent"
        elif accuracy >= 70:
            data['forecast_quality'] = "👍 Good"
        elif accuracy >= 60:
            data['forecast_quality'] = "🤔 Average"
        elif accuracy >= 40:
            data['forecast_quality'] = "👎 Below Average"
        else:
            data['forecast_quality'] = "💥 Poor"
        
        # Market performance analysis
        if sales_trend == "Increasing" and accuracy >= 80:
            data['market_performance'] = "🚀 Growth Captured"
        elif sales_trend == "Increasing" and accuracy < 60:
            data['market_performance'] = "📈 Growth Missed"
        elif sales_trend == "Decreasing" and accuracy >= 80:
            data['market_performance'] = "📉 Decline Predicted"
        elif sales_trend == "Stable" and accuracy >= 80:
            data['market_performance'] = "➡️ Stability Maintained"
        elif sales_trend == "Volatile":
            data['market_performance'] = "⚡ Volatility Challenge"
        else:
            data['market_performance'] = "❓ Market Unclear"
        
        # Improvement potential analysis
        if abs(confidence_gap) <= 10 and accuracy >= 80:
            data['improvement_potential'] = "🎯 Well Calibrated"
        elif confidence_gap > 20:
            data['improvement_potential'] = "📉 Overconfident"
        elif confidence_gap < -20:
            data['improvement_potential'] = "📈 Underconfident"
        elif accuracy < 60:
            data['improvement_potential'] = "🔧 Needs Model Tuning"
        elif sales_trend == "Volatile":
            data['improvement_potential'] = "📊 Add Volatility Handling"
        else:
            data['improvement_potential'] = "⚖️ Minor Adjustments"
        
        return data
        
    except Exception as e:
        frappe.log_error(f"Advanced sales analytics failed: {str(e)}")
        return data

def get_sales_accuracy_charts(filters, data):
    """Generate comprehensive sales accuracy analysis charts"""
    try:
        if not data:
            return {"data": {"labels": [], "datasets": []}, "type": "bar"}
        
        # Accuracy distribution
        accuracy_ranges = {
            "90-100%": 0,
            "80-89%": 0, 
            "70-79%": 0,
            "60-69%": 0,
            "Below 60%": 0
        }
        
        # Sales trend accuracy
        trend_accuracy = {}
        
        # Movement type accuracy
        movement_accuracy = {}
        
        for item in data:
            accuracy = item.get('accuracy_percentage', 0)
            trend = item.get('sales_trend', 'Unknown')
            movement_type = item.get('movement_type', 'Unknown')
            
            # Accuracy range distribution
            if accuracy >= 90:
                accuracy_ranges["90-100%"] += 1
            elif accuracy >= 80:
                accuracy_ranges["80-89%"] += 1
            elif accuracy >= 70:
                accuracy_ranges["70-79%"] += 1
            elif accuracy >= 60:
                accuracy_ranges["60-69%"] += 1
            else:
                accuracy_ranges["Below 60%"] += 1
            
            # Sales trend accuracy
            if trend not in trend_accuracy:
                trend_accuracy[trend] = {'total': 0, 'sum_accuracy': 0}
            trend_accuracy[trend]['total'] += 1
            trend_accuracy[trend]['sum_accuracy'] += accuracy
            
            # Movement type accuracy
            if movement_type not in movement_accuracy:
                movement_accuracy[movement_type] = {'total': 0, 'sum_accuracy': 0}
            movement_accuracy[movement_type]['total'] += 1
            movement_accuracy[movement_type]['sum_accuracy'] += accuracy
        
        # Calculate average accuracy by trend
        trend_avg_accuracy = {}
        for trend, stats in trend_accuracy.items():
            trend_avg_accuracy[trend] = stats['sum_accuracy'] / stats['total']
        
        return {
            "data": {
                "labels": list(accuracy_ranges.keys()),
                "datasets": [
                    {
                        "name": "Sales Forecast Accuracy Distribution",
                        "values": list(accuracy_ranges.values())
                    }
                ]
            },
            "type": "bar",
            "height": 350,
            "colors": ["#28a745", "#20c997", "#ffc107", "#fd7e14", "#dc3545"],
            "axisOptions": {
                "xAxisMode": "tick",
                "yAxisMode": "tick"
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Sales accuracy charts generation failed: {str(e)}")
        return {"data": {"labels": [], "datasets": []}, "type": "bar"}

def get_sales_accuracy_summary(data, filters):
    """Generate intelligent sales accuracy summary with insights"""
    try:
        if not data:
            return []
        
        total_forecasts = len(data)
        
        # Calculate key metrics
        accuracies = [item.get('accuracy_percentage', 0) for item in data]
        errors = [item.get('error_percentage', 0) for item in data]
        confidence_gaps = [item.get('confidence_accuracy_gap', 0) for item in data]
        revenue_impacts = [item.get('revenue_impact', 0) for item in data]
        
        avg_accuracy = np.mean(accuracies)
        avg_error = np.mean(errors)
        avg_confidence_gap = np.mean(confidence_gaps)
        total_revenue_impact = sum(revenue_impacts)
        
        # Count categories
        excellent_forecasts = len([d for d in data if d.get('accuracy_percentage', 0) >= 90])
        good_forecasts = len([d for d in data if d.get('accuracy_percentage', 0) >= 80])
        poor_forecasts = len([d for d in data if d.get('accuracy_percentage', 0) < 60])
        
        # Bias analysis
        over_forecasts = len([d for d in data if d.get('bias_direction') == 'Over-forecast'])
        under_forecasts = len([d for d in data if d.get('bias_direction') == 'Under-forecast'])
        
        # Sales trend performance
        trend_performance = {}
        for item in data:
            trend = item.get('sales_trend', 'Unknown')
            if trend not in trend_performance:
                trend_performance[trend] = []
            trend_performance[trend].append(item.get('accuracy_percentage', 0))
        
        best_trend_performance = max(trend_performance.items(), 
                                   key=lambda x: np.mean(x[1]))[0] if trend_performance else "N/A"
        
        # Market performance analysis
        growth_captured = len([d for d in data if "Growth Captured" in d.get('market_performance', '')])
        growth_missed = len([d for d in data if "Growth Missed" in d.get('market_performance', '')])
        
        # Confidence calibration
        well_calibrated = len([d for d in data if abs(d.get('confidence_accuracy_gap', 0)) <= 10])
        overconfident = len([d for d in data if d.get('confidence_accuracy_gap', 0) > 20])
        
        # Overall system health
        if avg_accuracy >= 85 and abs(avg_confidence_gap) <= 10 and growth_missed < total_forecasts * 0.2:
            system_health = "🌟 Excellent"
            health_indicator = "Green"
        elif avg_accuracy >= 75 and abs(avg_confidence_gap) <= 15:
            system_health = "✅ Good"  
            health_indicator = "Green"
        elif avg_accuracy >= 65:
            system_health = "⚠️ Fair"
            health_indicator = "Orange"
        else:
            system_health = "❌ Poor"
            health_indicator = "Red"
        
        return [
            {
                "value": total_forecasts,
                "label": "Total Sales Forecasts Analyzed",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": f"{avg_accuracy:.1f}%",
                "label": "Average Sales Accuracy",
                "datatype": "Data",
                "indicator": "Green" if avg_accuracy >= 80 else "Orange" if avg_accuracy >= 60 else "Red"
            },
            {
                "value": f"{avg_error:.1f}%",
                "label": "Average Error Rate",
                "datatype": "Data",
                "indicator": "Green" if avg_error <= 20 else "Orange" if avg_error <= 40 else "Red"
            },
            {
                "value": excellent_forecasts,
                "label": "🎯 Excellent Forecasts (≥90%)",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": good_forecasts,
                "label": "✅ Good Forecasts (≥80%)",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": poor_forecasts,
                "label": "❌ Poor Forecasts (<60%)",
                "datatype": "Int",
                "indicator": "Red" if poor_forecasts > 0 else "Green"
            },
            {
                "value": growth_captured,
                "label": "🚀 Growth Opportunities Captured",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": growth_missed,
                "label": "📈 Growth Opportunities Missed",
                "datatype": "Int",
                "indicator": "Red" if growth_missed > 0 else "Green"
            },
            {
                "value": f"{total_revenue_impact:,.0f}",
                "label": "Total Revenue Impact",
                "datatype": "Currency",
                "indicator": "Orange" if total_revenue_impact > 0 else "Green"
            },
            {
                "value": f"{avg_confidence_gap:+.1f}%",
                "label": "Confidence Calibration Gap",
                "datatype": "Data",
                "indicator": "Green" if abs(avg_confidence_gap) <= 10 else "Orange" if abs(avg_confidence_gap) <= 20 else "Red"
            },
            {
                "value": f"{over_forecasts}/{under_forecasts}",
                "label": "Over/Under Forecasts",
                "datatype": "Data",
                "indicator": "Blue"
            },
            {
                "value": well_calibrated,
                "label": "⚖️ Well Calibrated Forecasts",
                "datatype": "Int",
                "indicator": "Green"
            },
            {
                "value": overconfident,
                "label": "📉 Overconfident Forecasts",
                "datatype": "Int",
                "indicator": "Orange" if overconfident > 0 else "Green"
            },
            {
                "value": best_trend_performance,
                "label": "Best Performing Trend",
                "datatype": "Data",
                "indicator": "Green"
            },
            {
                "value": system_health,
                "label": "Overall Sales Forecast Health",
                "datatype": "Data",
                "indicator": health_indicator
            }
        ]
        
    except Exception as e:
        frappe.log_error(f"Sales accuracy summary generation failed: {str(e)}")
        return [
            {
                "value": "Error",
                "label": "Summary Generation Failed",
                "datatype": "Data",
                "indicator": "Red"
            }
        ]

# Additional utility functions for advanced sales analytics

@frappe.whitelist()
def get_sales_forecast_trend_analysis(item_code, customer, company, days=90):
    """Get sales forecast trend analysis for a specific item-customer combination"""
    try:
        from_date = add_days(nowdate(), -days)
        
        # Get forecast history
        forecast_history = frappe.db.sql("""
            SELECT 
                DATE(last_forecast_date) as forecast_date,
                predicted_qty,
                confidence_score,
                movement_type,
                sales_trend
            FROM `tabAI Sales Forecast`
            WHERE item_code = %s
            AND customer = %s
            AND company = %s
            AND last_forecast_date >= %s
            ORDER BY last_forecast_date
        """, (item_code, customer, company, from_date), as_dict=True)
        
        if not forecast_history:
            return {"status": "no_data", "message": "No sales forecast history found"}
        
        # Analyze trends
        forecasts = [f['predicted_qty'] for f in forecast_history]
        confidences = [f['confidence_score'] for f in forecast_history]
        
        # Calculate trend
        if len(forecasts) >= 2:
            forecast_trend = np.polyfit(range(len(forecasts)), forecasts, 1)[0]
            confidence_trend = np.polyfit(range(len(confidences)), confidences, 1)[0]
        else:
            forecast_trend = 0
            confidence_trend = 0
        
        return {
            "status": "success",
            "forecast_history": forecast_history,
            "forecast_trend": round(forecast_trend, 3),
            "confidence_trend": round(confidence_trend, 3),
            "avg_forecast": round(np.mean(forecasts), 2),
            "avg_confidence": round(np.mean(confidences), 1)
        }
        
    except Exception as e:
        frappe.log_error(f"Sales forecast trend analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_comparative_sales_accuracy_analysis(company=None, period_days=30):
    """Get comparative sales accuracy analysis across categories"""
    try:
        from_date = add_days(nowdate(), -period_days)
        
        filters = {"from_date": from_date, "to_date": nowdate()}
        if company:
            filters["company"] = company
        
        # Get accuracy data
        accuracy_data = get_sales_accuracy_analysis_data(filters)
        
        if not accuracy_data:
            return {"status": "no_data", "message": "No sales accuracy data found"}
        
        # Analyze by sales trend
        trend_analysis = {}
        for item in accuracy_data:
            trend = item.get('sales_trend', 'Unknown')
            if trend not in trend_analysis:
                trend_analysis[trend] = {
                    'accuracies': [],
                    'errors': [],
                    'confidence_gaps': [],
                    'revenue_impacts': []
                }
            
            trend_analysis[trend]['accuracies'].append(item.get('accuracy_percentage', 0))
            trend_analysis[trend]['errors'].append(item.get('error_percentage', 0))
            trend_analysis[trend]['confidence_gaps'].append(item.get('confidence_accuracy_gap', 0))
            trend_analysis[trend]['revenue_impacts'].append(item.get('revenue_impact', 0))
        
        # Calculate statistics for each trend
        trend_stats = {}
        for trend, data in trend_analysis.items():
            trend_stats[trend] = {
                'avg_accuracy': round(np.mean(data['accuracies']), 1),
                'avg_error': round(np.mean(data['errors']), 1),
                'avg_confidence_gap': round(np.mean(data['confidence_gaps']), 1),
                'total_revenue_impact': round(sum(data['revenue_impacts']), 2),
                'forecast_count': len(data['accuracies']),
                'accuracy_std': round(np.std(data['accuracies']), 1)
            }
        
        return {
            "status": "success",
            "trend_stats": trend_stats,
            "total_forecasts": len(accuracy_data),
            "analysis_period": period_days
        }
        
    except Exception as e:
        frappe.log_error(f"Comparative sales accuracy analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def generate_sales_accuracy_improvement_recommendations(company=None, min_accuracy=80):
    """Generate AI-powered recommendations for sales forecast improvement"""
    try:
        # Get recent accuracy data
        from_date = add_days(nowdate(), -30)  
        filters = {"from_date": from_date, "to_date": nowdate()}
        if company:
            filters["company"] = company
        
        accuracy_data = get_sales_accuracy_analysis_data(filters)
        
        if not accuracy_data:
            return {"status": "no_data", "recommendations": []}
        
        recommendations = []
        
        # Analyze patterns and generate recommendations
        poor_performers = [d for d in accuracy_data if d.get('accuracy_percentage', 0) < min_accuracy]
        growth_missed = [d for d in accuracy_data if "Growth Missed" in d.get('market_performance', '')]
        high_revenue_impact = [d for d in accuracy_data if d.get('revenue_impact', 0) > 10000]
        overconfident_items = [d for d in accuracy_data if d.get('confidence_accuracy_gap', 0) > 20]
        
        # Generate specific recommendations
        if len(poor_performers) > len(accuracy_data) * 0.3:
            recommendations.append({
                "priority": "High",
                "category": "Sales Model Performance",
                "recommendation": f"Review sales forecasting algorithm - {len(poor_performers)} items have accuracy below {min_accuracy}%",
                "affected_items": len(poor_performers),
                "action": "Consider retraining AI models with recent sales data and market trends"
            })
        
        if len(growth_missed) > 0:
            recommendations.append({
                "priority": "High",
                "category": "Market Opportunity",
                "recommendation": f"Improve growth trend detection - {len(growth_missed)} growth opportunities missed",
                "affected_items": len(growth_missed),
                "action": "Enhance market trend analysis and incorporate external market indicators"
            })
        
        if len(high_revenue_impact) > 0:
            total_impact = sum([d.get('revenue_impact', 0) for d in high_revenue_impact])
            recommendations.append({
                "priority": "High",
                "category": "Revenue Impact",
                "recommendation": f"Focus on high-impact forecasts - {total_impact:,.0f} revenue at risk",
                "affected_items": len(high_revenue_impact),
                "action": "Prioritize accuracy improvement for high-value items and customers"
            })
        
        if len(overconfident_items) > 0:
            recommendations.append({
                "priority": "Medium", 
                "category": "Confidence Calibration",
                "recommendation": f"Recalibrate sales confidence scoring - {len(overconfident_items)} items are overconfident",
                "affected_items": len(overconfident_items),
                "action": "Adjust confidence calculation to reflect sales volatility and market uncertainty"
            })
        
        # Sales trend specific recommendations
        trend_performance = {}
        for item in accuracy_data:
            trend = item.get('sales_trend', 'Unknown')
            if trend not in trend_performance:
                trend_performance[trend] = []
            trend_performance[trend].append(item.get('accuracy_percentage', 0))
        
        for trend, accuracies in trend_performance.items():
            avg_accuracy = np.mean(accuracies)
            if avg_accuracy < min_accuracy:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Trend Specific",
                    "recommendation": f"Improve {trend} sales forecasting - average accuracy: {avg_accuracy:.1f}%",
                    "affected_items": len(accuracies),
                    "action": f"Review {trend} specific forecasting parameters and market factors"
                })
        
        # Customer/Territory performance
        customer_performance = {}
        for item in accuracy_data:
            customer = item.get('customer', 'Unknown')
            if customer not in customer_performance:
                customer_performance[customer] = []
            customer_performance[customer].append(item.get('accuracy_percentage', 0))
        
        # Find customers with consistently poor accuracy
        poor_customer_performance = {
            customer: np.mean(accuracies) 
            for customer, accuracies in customer_performance.items() 
            if len(accuracies) >= 3 and np.mean(accuracies) < min_accuracy
        }
        
        if poor_customer_performance:
            worst_customers = sorted(poor_customer_performance.items(), key=lambda x: x[1])[:3]
            recommendations.append({
                "priority": "Medium",
                "category": "Customer Specific",
                "recommendation": f"Review customer-specific forecasting for {len(poor_customer_performance)} customers with poor accuracy",
                "affected_items": sum([len(customer_performance[c]) for c, _ in worst_customers]),
                "action": "Analyze customer buying patterns and adjust forecasting parameters accordingly"
            })
        
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "total_analyzed": len(accuracy_data),
            "overall_accuracy": round(np.mean([d.get('accuracy_percentage', 0) for d in accuracy_data]), 1),
            "total_revenue_at_risk": round(sum([d.get('revenue_impact', 0) for d in accuracy_data]), 2)
        }
        
    except Exception as e:
        frappe.log_error(f"Sales accuracy improvement recommendations failed: {str(e)}")
        return {"status": "error", "message": str(e), "recommendations": []}
