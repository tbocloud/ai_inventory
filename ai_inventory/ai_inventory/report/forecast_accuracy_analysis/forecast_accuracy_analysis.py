# ai_inventory/ai_inventory/report/forecast_accuracy_analysis/forecast_accuracy_analysis.py
# COMPREHENSIVE FORECAST ACCURACY ANALYSIS WITH DATA SCIENCE

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
    filters = validate_accuracy_filters(filters)
    
    columns = get_accuracy_columns()
    data = get_accuracy_analysis_data(filters)
    chart = get_accuracy_charts(filters, data)
    summary = get_accuracy_summary(data, filters)
    
    return columns, data, None, chart, summary

def validate_accuracy_filters(filters):
    """Validate and set default filters for accuracy analysis"""
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

def get_accuracy_columns():
    """Define columns for forecast accuracy analysis"""
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
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 100
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 100
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Forecasted Consumption"),
            "fieldname": "forecasted_consumption",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Actual Consumption"),
            "fieldname": "actual_consumption",
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
            "label": _("Improvement Potential"),
            "fieldname": "improvement_potential",
            "fieldtype": "Data",
            "width": 140
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

def get_accuracy_analysis_data(filters):
    """Get comprehensive forecast accuracy analysis data"""
    try:
        conditions = get_accuracy_conditions(filters)
        analysis_period = int(filters.get("analysis_period", 30))
        
        # Get forecast data with actual consumption
        base_query = f"""
            SELECT 
                aif.item_code,
                aif.item_name,
                aif.company,
                aif.warehouse,
                aif.movement_type,
                aif.predicted_consumption as forecasted_consumption,
                aif.confidence_score as ai_confidence,
                aif.last_forecast_date,
                aif.forecast_period_days,
                aif.name as forecast_id
            FROM `tabAI Inventory Forecast` aif
            WHERE aif.predicted_consumption > 0
            AND aif.last_forecast_date >= %(from_date)s
            AND aif.last_forecast_date <= %(to_date)s
            {conditions}
            ORDER BY aif.last_forecast_date DESC, aif.item_code
            LIMIT 500
        """
        
        forecast_data = frappe.db.sql(base_query, filters, as_dict=True)
        
        if not forecast_data:
            return []
        
        # Calculate actual consumption and accuracy metrics for each forecast
        accuracy_data = []
        for forecast in forecast_data:
            try:
                # Get actual consumption for the forecast period
                actual_consumption = get_actual_consumption(
                    forecast['item_code'],
                    forecast['warehouse'], 
                    forecast['company'],
                    forecast['last_forecast_date'],
                    analysis_period
                )
                
                # Calculate accuracy metrics
                accuracy_metrics = calculate_accuracy_metrics(
                    forecast['forecasted_consumption'],
                    actual_consumption,
                    forecast['ai_confidence']
                )
                
                # Combine forecast data with accuracy metrics
                combined_data = {**forecast, **accuracy_metrics}
                combined_data['actual_consumption'] = actual_consumption
                
                # Calculate days since forecast
                combined_data['days_since_forecast'] = date_diff(
                    nowdate(), getdate(forecast['last_forecast_date'])
                )
                
                # Add advanced analytics
                combined_data = add_advanced_accuracy_analytics(combined_data)
                
                accuracy_data.append(combined_data)
                
            except Exception as e:
                frappe.log_error(f"Accuracy calculation failed for {forecast['item_code']}: {str(e)}")
                continue
        
        return accuracy_data
        
    except Exception as e:
        frappe.log_error(f"Accuracy analysis data retrieval failed: {str(e)}")
        return []

def get_accuracy_conditions(filters):
    """Build SQL conditions for accuracy analysis"""
    conditions = ""
    
    if filters.get("company"):
        conditions += " AND aif.company = %(company)s"
    
    if filters.get("warehouse"):
        conditions += " AND aif.warehouse = %(warehouse)s"
    
    if filters.get("item_group"):
        conditions += " AND aif.item_group = %(item_group)s"
    
    if filters.get("movement_type"):
        if isinstance(filters["movement_type"], list):
            movement_list = "', '".join(filters["movement_type"])
            conditions += f" AND aif.movement_type IN ('{movement_list}')"
        else:
            conditions += " AND aif.movement_type = %(movement_type)s"
    
    if filters.get("supplier"):
        conditions += """ AND (
            aif.preferred_supplier = %(supplier)s OR 
            (aif.preferred_supplier IS NULL AND aif.supplier = %(supplier)s)
        )"""
    
    if filters.get("min_confidence"):
        conditions += " AND aif.confidence_score >= %(min_confidence)s"
    
    if filters.get("accuracy_category"):
        # This will be applied after accuracy calculation
        pass
    
    return conditions

def get_actual_consumption(item_code, warehouse, company, forecast_date, analysis_period):
    """Get actual consumption for the specified period after forecast"""
    try:
        from_date = getdate(forecast_date)
        to_date = add_days(from_date, analysis_period)
        
        actual_consumption = frappe.db.sql("""
            SELECT 
                SUM(ABS(sle.actual_qty)) as total_consumption
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
            WHERE sle.item_code = %s 
            AND sle.warehouse = %s
            AND w.company = %s
            AND sle.actual_qty < 0
            AND DATE(sle.posting_date) >= %s
            AND DATE(sle.posting_date) <= %s
        """, (item_code, warehouse, company, from_date, to_date))
        
        return flt(actual_consumption[0][0]) if actual_consumption and actual_consumption[0][0] else 0
        
    except Exception as e:
        frappe.log_error(f"Actual consumption calculation failed: {str(e)}")
        return 0

def calculate_accuracy_metrics(forecasted, actual, confidence):
    """Calculate comprehensive accuracy metrics"""
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
        frappe.log_error(f"Accuracy metrics calculation failed: {str(e)}")
        return {
            'forecast_error': 0,
            'absolute_error': 0,
            'error_percentage': 0,
            'accuracy_percentage': 0,
            'confidence_accuracy_gap': 0,
            'bias_direction': 'Unknown'
        }

def add_advanced_accuracy_analytics(data):
    """Add advanced analytics to accuracy data"""
    try:
        accuracy = data.get('accuracy_percentage', 0)
        error_pct = data.get('error_percentage', 0)
        confidence_gap = data.get('confidence_accuracy_gap', 0)
        
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
        
        # Improvement potential analysis
        if abs(confidence_gap) <= 10 and accuracy >= 80:
            data['improvement_potential'] = "🎯 Well Calibrated"
        elif confidence_gap > 20:
            data['improvement_potential'] = "📉 Overconfident"
        elif confidence_gap < -20:
            data['improvement_potential'] = "📈 Underconfident"
        elif accuracy < 60:
            data['improvement_potential'] = "🔧 Needs Model Tuning"
        else:
            data['improvement_potential'] = "⚖️ Minor Adjustments"
        
        return data
        
    except Exception as e:
        frappe.log_error(f"Advanced analytics failed: {str(e)}")
        return data

def get_accuracy_charts(filters, data):
    """Generate comprehensive accuracy analysis charts"""
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
        
        # Error category distribution
        error_categories = {}
        
        # Movement type accuracy
        movement_accuracy = {}
        
        for item in data:
            accuracy = item.get('accuracy_percentage', 0)
            error_cat = item.get('error_category', 'Unknown')
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
            
            # Error categories
            error_categories[error_cat] = error_categories.get(error_cat, 0) + 1
            
            # Movement type accuracy
            if movement_type not in movement_accuracy:
                movement_accuracy[movement_type] = {'total': 0, 'sum_accuracy': 0}
            movement_accuracy[movement_type]['total'] += 1
            movement_accuracy[movement_type]['sum_accuracy'] += accuracy
        
        # Calculate average accuracy by movement type
        movement_avg_accuracy = {}
        for movement, stats in movement_accuracy.items():
            movement_avg_accuracy[movement] = stats['sum_accuracy'] / stats['total']
        
        return {
            "data": {
                "labels": list(accuracy_ranges.keys()),
                "datasets": [
                    {
                        "name": "Accuracy Distribution",
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
        frappe.log_error(f"Accuracy charts generation failed: {str(e)}")
        return {"data": {"labels": [], "datasets": []}, "type": "bar"}

def get_accuracy_summary(data, filters):
    """Generate intelligent accuracy summary with insights"""
    try:
        if not data:
            return []
        
        total_forecasts = len(data)
        
        # Calculate key metrics
        accuracies = [item.get('accuracy_percentage', 0) for item in data]
        errors = [item.get('error_percentage', 0) for item in data]
        confidence_gaps = [item.get('confidence_accuracy_gap', 0) for item in data]
        
        avg_accuracy = np.mean(accuracies)
        avg_error = np.mean(errors)
        avg_confidence_gap = np.mean(confidence_gaps)
        
        # Count categories
        excellent_forecasts = len([d for d in data if d.get('accuracy_percentage', 0) >= 90])
        good_forecasts = len([d for d in data if d.get('accuracy_percentage', 0) >= 80])
        poor_forecasts = len([d for d in data if d.get('accuracy_percentage', 0) < 60])
        
        # Bias analysis
        over_forecasts = len([d for d in data if d.get('bias_direction') == 'Over-forecast'])
        under_forecasts = len([d for d in data if d.get('bias_direction') == 'Under-forecast'])
        
        # Confidence calibration
        well_calibrated = len([d for d in data if abs(d.get('confidence_accuracy_gap', 0)) <= 10])
        overconfident = len([d for d in data if d.get('confidence_accuracy_gap', 0) > 20])
        
        # Movement type performance
        movement_performance = {}
        for item in data:
            movement = item.get('movement_type', 'Unknown')
            if movement not in movement_performance:
                movement_performance[movement] = []
            movement_performance[movement].append(item.get('accuracy_percentage', 0))
        
        best_movement_type = max(movement_performance.items(), 
                               key=lambda x: np.mean(x[1]))[0] if movement_performance else "N/A"
        
        # Overall system health
        if avg_accuracy >= 85 and abs(avg_confidence_gap) <= 10:
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
                "label": "Total Forecasts Analyzed",
                "datatype": "Int",
                "indicator": "Blue"
            },
            {
                "value": f"{avg_accuracy:.1f}%",
                "label": "Average Accuracy",
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
                "value": best_movement_type,
                "label": "Best Performing Category",
                "datatype": "Data",
                "indicator": "Green"
            },
            {
                "value": system_health,
                "label": "Overall Forecast Health",
                "datatype": "Data",
                "indicator": health_indicator
            }
        ]
        
    except Exception as e:
        frappe.log_error(f"Accuracy summary generation failed: {str(e)}")
        return [
            {
                "value": "Error",
                "label": "Summary Generation Failed",
                "datatype": "Data",
                "indicator": "Red"
            }
        ]

# Additional utility functions for advanced analytics

@frappe.whitelist()
def get_forecast_trend_analysis(item_code, warehouse, company, days=90):
    """Get forecast trend analysis for a specific item"""
    try:
        from_date = add_days(nowdate(), -days)
        
        # Get forecast history
        forecast_history = frappe.db.sql("""
            SELECT 
                DATE(last_forecast_date) as forecast_date,
                predicted_consumption,
                confidence_score,
                movement_type
            FROM `tabAI Inventory Forecast`
            WHERE item_code = %s
            AND warehouse = %s
            AND company = %s
            AND last_forecast_date >= %s
            ORDER BY last_forecast_date
        """, (item_code, warehouse, company, from_date), as_dict=True)
        
        if not forecast_history:
            return {"status": "no_data", "message": "No forecast history found"}
        
        # Analyze trends
        forecasts = [f['predicted_consumption'] for f in forecast_history]
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
        frappe.log_error(f"Forecast trend analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_comparative_accuracy_analysis(company=None, period_days=30):
    """Get comparative accuracy analysis across categories"""
    try:
        from_date = add_days(nowdate(), -period_days)
        
        filters = {"from_date": from_date, "to_date": nowdate()}
        if company:
            filters["company"] = company
        
        # Get accuracy data
        accuracy_data = get_accuracy_analysis_data(filters)
        
        if not accuracy_data:
            return {"status": "no_data", "message": "No accuracy data found"}
        
        # Analyze by movement type
        movement_analysis = {}
        for item in accuracy_data:
            movement = item.get('movement_type', 'Unknown')
            if movement not in movement_analysis:
                movement_analysis[movement] = {
                    'accuracies': [],
                    'errors': [],
                    'confidence_gaps': []
                }
            
            movement_analysis[movement]['accuracies'].append(item.get('accuracy_percentage', 0))
            movement_analysis[movement]['errors'].append(item.get('error_percentage', 0))
            movement_analysis[movement]['confidence_gaps'].append(item.get('confidence_accuracy_gap', 0))
        
        # Calculate statistics for each movement type
        movement_stats = {}
        for movement, data in movement_analysis.items():
            movement_stats[movement] = {
                'avg_accuracy': round(np.mean(data['accuracies']), 1),
                'avg_error': round(np.mean(data['errors']), 1),
                'avg_confidence_gap': round(np.mean(data['confidence_gaps']), 1),
                'forecast_count': len(data['accuracies']),
                'accuracy_std': round(np.std(data['accuracies']), 1)
            }
        
        return {
            "status": "success",
            "movement_stats": movement_stats,
            "total_forecasts": len(accuracy_data),
            "analysis_period": period_days
        }
        
    except Exception as e:
        frappe.log_error(f"Comparative accuracy analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def generate_accuracy_improvement_recommendations(company=None, min_accuracy=80):
    """Generate AI-powered recommendations for forecast improvement"""
    try:
        # Get recent accuracy data
        from_date = add_days(nowdate(), -30)  
        filters = {"from_date": from_date, "to_date": nowdate()}
        if company:
            filters["company"] = company
        
        accuracy_data = get_accuracy_analysis_data(filters)
        
        if not accuracy_data:
            return {"status": "no_data", "recommendations": []}
        
        recommendations = []
        
        # Analyze patterns and generate recommendations
        poor_performers = [d for d in accuracy_data if d.get('accuracy_percentage', 0) < min_accuracy]
        overconfident_items = [d for d in accuracy_data if d.get('confidence_accuracy_gap', 0) > 20]
        high_error_items = [d for d in accuracy_data if d.get('error_percentage', 0) > 50]
        
        # Generate specific recommendations
        if len(poor_performers) > len(accuracy_data) * 0.3:
            recommendations.append({
                "priority": "High",
                "category": "Model Performance",
                "recommendation": f"Review forecasting algorithm - {len(poor_performers)} items have accuracy below {min_accuracy}%",
                "affected_items": len(poor_performers),
                "action": "Consider retraining AI models with recent data"
            })
        
        if len(overconfident_items) > 0:
            recommendations.append({
                "priority": "Medium", 
                "category": "Confidence Calibration",
                "recommendation": f"Recalibrate confidence scoring - {len(overconfident_items)} items are overconfident",
                "affected_items": len(overconfident_items),
                "action": "Adjust confidence calculation parameters"
            })
        
        if len(high_error_items) > 0:
            recommendations.append({
                "priority": "High",
                "category": "Data Quality",
                "recommendation": f"Investigate data quality issues - {len(high_error_items)} items have >50% error",
                "affected_items": len(high_error_items),
                "action": "Review historical data and consumption patterns"
            })
        
        # Movement type specific recommendations
        movement_performance = {}
        for item in accuracy_data:
            movement = item.get('movement_type', 'Unknown')
            if movement not in movement_performance:
                movement_performance[movement] = []
            movement_performance[movement].append(item.get('accuracy_percentage', 0))
        
        for movement, accuracies in movement_performance.items():
            avg_accuracy = np.mean(accuracies)
            if avg_accuracy < min_accuracy:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Category Specific",
                    "recommendation": f"Improve {movement} forecasting - average accuracy: {avg_accuracy:.1f}%",
                    "affected_items": len(accuracies),
                    "action": f"Review {movement} specific forecasting parameters"
                })
        
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "total_analyzed": len(accuracy_data),
            "overall_accuracy": round(np.mean([d.get('accuracy_percentage', 0) for d in accuracy_data]), 1)
        }
        
    except Exception as e:
        frappe.log_error(f"Accuracy improvement recommendations failed: {str(e)}")
        return {"status": "error", "message": str(e), "recommendations": []}