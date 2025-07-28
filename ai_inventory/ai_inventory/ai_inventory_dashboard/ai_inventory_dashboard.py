# ai_inventory/ai_inventory/report/ai_inventory_dashboard/ai_inventory_dashboard.py

import frappe
from frappe.utils import flt, nowdate, add_days
from frappe import _
import json

def execute(filters=None):
    columns, data = [], []
    
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(filters)
    summary = get_summary_data(filters)
    
    return columns, data, None, chart, summary

def get_columns():
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
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 100
        },
        {
            "label": _("Current Stock"),
            "fieldname": "current_stock",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Predicted Consumption"),
            "fieldname": "predicted_consumption",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Reorder Level"),
            "fieldname": "reorder_level",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Suggested Qty"),
            "fieldname": "suggested_qty",
            "fieldtype": "Float",
            "width": 110
        },
        {
            "label": _("Confidence %"),
            "fieldname": "confidence_score",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("Reorder Alert"),
            "fieldname": "reorder_alert",
            "fieldtype": "Check",
            "width": 100
        },
        {
            "label": _("Last Forecast"),
            "fieldname": "last_forecast_date",
            "fieldtype": "Datetime",
            "width": 140
        },
        {
            "label": _("Stock Days"),
            "fieldname": "stock_days",
            "fieldtype": "Int",
            "width": 90
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            aif.item_code,
            aif.item_name,
            aif.warehouse,
            aif.current_stock,
            aif.movement_type,
            aif.predicted_consumption,
            aif.reorder_level,
            aif.suggested_qty,
            aif.confidence_score,
            aif.reorder_alert,
            aif.last_forecast_date,
            CASE 
                WHEN aif.predicted_consumption > 0 AND aif.forecast_period_days > 0 
                THEN ROUND(aif.current_stock / (aif.predicted_consumption / aif.forecast_period_days))
                ELSE 999 
            END as stock_days,
            aif.name as forecast_id
        FROM `tabAI Inventory Forecast` aif
        WHERE 1=1 {conditions}
        ORDER BY 
            aif.reorder_alert DESC,
            aif.movement_type = 'Fast Moving' DESC,
            aif.confidence_score DESC
    """, filters, as_dict=True)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("warehouse"):
        conditions += " AND aif.warehouse = %(warehouse)s"
    
    if filters.get("item_group"):
        conditions += " AND aif.item_group = %(item_group)s"
    
    if filters.get("movement_type"):
        conditions += " AND aif.movement_type = %(movement_type)s"
    
    if filters.get("reorder_alert"):
        conditions += " AND aif.reorder_alert = 1"
    
    if filters.get("low_confidence"):
        conditions += " AND aif.confidence_score < 70"
    
    return conditions

def get_chart_data(filters):
    # Movement Type Distribution
    movement_data = frappe.db.sql(f"""
        SELECT 
            movement_type as name,
            COUNT(*) as value
        FROM `tabAI Inventory Forecast` aif
        WHERE 1=1 {get_conditions(filters)}
        GROUP BY movement_type
        ORDER BY value DESC
    """, filters, as_dict=True)
    
    # Reorder Alerts Trend (last 30 days)
    alert_trend = frappe.db.sql(f"""
        SELECT 
            DATE(last_forecast_date) as date,
            SUM(CASE WHEN reorder_alert = 1 THEN 1 ELSE 0 END) as alerts,
            COUNT(*) as total_forecasts
        FROM `tabAI Inventory Forecast` aif
        WHERE last_forecast_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        {get_conditions(filters)}
        GROUP BY DATE(last_forecast_date)
        ORDER BY date
    """, filters, as_dict=True)
    
    return {
        "data": {
            "labels": [d.name for d in movement_data],
            "datasets": [
                {
                    "name": "Movement Distribution",
                    "values": [d.value for d in movement_data]
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#28a745", "#ffc107", "#dc3545", "#6f42c1"]
    }

def get_summary_data(filters):
    summary = frappe.db.sql(f"""
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE WHEN reorder_alert = 1 THEN 1 ELSE 0 END) as reorder_alerts,
            SUM(CASE WHEN movement_type = 'Fast Moving' THEN 1 ELSE 0 END) as fast_moving,
            SUM(CASE WHEN movement_type = 'Slow Moving' THEN 1 ELSE 0 END) as slow_moving,
            SUM(CASE WHEN movement_type = 'Non Moving' THEN 1 ELSE 0 END) as non_moving,
            AVG(confidence_score) as avg_confidence,
            SUM(current_stock * 
                CASE 
                    WHEN movement_type = 'Fast Moving' THEN 3
                    WHEN movement_type = 'Slow Moving' THEN 1.5
                    WHEN movement_type = 'Non Moving' THEN 0.5
                    ELSE 2
                END
            ) as weighted_stock_value
        FROM `tabAI Inventory Forecast` aif
        WHERE 1=1 {get_conditions(filters)}
    """, filters, as_dict=True)[0]
    
    return [
        {
            "value": summary.total_items,
            "label": "Total Items",
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": summary.reorder_alerts,
            "label": "Reorder Alerts",
            "datatype": "Int", 
            "indicator": "Red" if summary.reorder_alerts > 0 else "Green"
        },
        {
            "value": summary.fast_moving,
            "label": "Fast Moving",
            "datatype": "Int",
            "indicator": "Green"
        },
        {
            "value": summary.slow_moving,
            "label": "Slow Moving", 
            "datatype": "Int",
            "indicator": "Orange"
        },
        {
            "value": summary.non_moving,
            "label": "Non Moving",
            "datatype": "Int",
            "indicator": "Red"
        },
        {
            "value": f"{summary.avg_confidence:.1f}%",
            "label": "Avg Confidence",
            "datatype": "Data",
            "indicator": "Green" if summary.avg_confidence > 80 else "Orange" if summary.avg_confidence > 60 else "Red"
        }
    ]

# ai_inventory/ai_inventory/report/ai_inventory_dashboard/ai_inventory_dashboard.json
{
    "add_total_row": 0,
    "columns": [],
    "creation": "2024-01-01 10:00:00.000000",
    "disable_prepared_report": 0,
    "disabled": 0,
    "docstatus": 0,
    "doctype": "Report",
    "filters": [
        {
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "label": "Warehouse",
            "mandatory": 0,
            "options": "Warehouse",
            "wildcard_filter": 0
        },
        {
            "fieldname": "item_group", 
            "fieldtype": "Link",
            "label": "Item Group",
            "mandatory": 0,
            "options": "Item Group",
            "wildcard_filter": 0
        },
        {
            "fieldname": "movement_type",
            "fieldtype": "Select",
            "label": "Movement Type",
            "mandatory": 0,
            "options": "\nFast Moving\nSlow Moving\nNon Moving\nCritical",
            "wildcard_filter": 0
        },
        {
            "default": "0",
            "fieldname": "reorder_alert",
            "fieldtype": "Check",
            "label": "Reorder Alerts Only",
            "mandatory": 0,
            "wildcard_filter": 0
        },
        {
            "default": "0",
            "fieldname": "low_confidence", 
            "fieldtype": "Check",
            "label": "Low Confidence Only",
            "mandatory": 0,
            "wildcard_filter": 0
        }
    ],
    "idx": 0,
    "is_standard": "Yes",
    "letter_head": "",
    "modified": "2024-01-01 10:00:00.000000",
    "modified_by": "Administrator",
    "module": "AI Inventory",
    "name": "AI Inventory Dashboard",
    "owner": "Administrator",
    "prepared_report": 0,
    "ref_doctype": "AI Inventory Forecast",
    "report_name": "AI Inventory Dashboard", 
    "report_type": "Script Report",
    "roles": [
        {
            "role": "Stock Manager"
        },
        {
            "role": "Stock User"
        },
        {
            "role": "Purchase Manager"
        },
        {
            "role": "System Manager"
        }
    ]
}

# ai_inventory/ai_inventory/report/forecast_accuracy_analysis/forecast_accuracy_analysis.py

import frappe
from frappe.utils import flt, getdate, add_days
from frappe import _
import json

def execute(filters=None):
    if not filters:
        filters = {}
        
    columns = get_columns()
    data = get_accuracy_data(filters)
    chart = get_accuracy_chart(filters)
    summary = get_accuracy_summary(data)
    
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "label": _("Item Code"),
            "fieldname": "item_code", 
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link", 
            "options": "Warehouse",
            "width": 100
        },
        {
            "label": _("Forecast Date"),
            "fieldname": "forecast_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Predicted Consumption"),
            "fieldname": "predicted_consumption",
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
            "label": _("Accuracy %"),
            "fieldname": "accuracy_percentage",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("Variance"),
            "fieldname": "variance",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Confidence Score"),
            "fieldname": "confidence_score",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Movement Type"),
            "fieldname": "movement_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Performance Grade"),
            "fieldname": "performance_grade",
            "fieldtype": "Data",
            "width": 120
        }
    ]

def get_accuracy_data(filters):
    # Get forecasts from the specified period
    from_date = filters.get('from_date', add_days(frappe.utils.nowdate(), -30))
    to_date = filters.get('to_date', frappe.utils.nowdate())
    
    # Get forecast data with actual consumption
    data = frappe.db.sql("""
        SELECT 
            aif.item_code,
            aif.warehouse,
            DATE(aif.last_forecast_date) as forecast_date,
            aif.predicted_consumption,
            aif.forecast_period_days,
            aif.confidence_score,
            aif.movement_type,
            (
                SELECT ABS(SUM(actual_qty))
                FROM `tabStock Ledger Entry` sle
                WHERE sle.item_code = aif.item_code
                AND sle.warehouse = aif.warehouse
                AND sle.posting_date BETWEEN DATE(aif.last_forecast_date) 
                    AND DATE_ADD(DATE(aif.last_forecast_date), INTERVAL aif.forecast_period_days DAY)
                AND sle.actual_qty < 0
            ) as actual_consumption
        FROM `tabAI Inventory Forecast` aif
        WHERE DATE(aif.last_forecast_date) BETWEEN %(from_date)s AND %(to_date)s
        AND aif.predicted_consumption > 0
        ORDER BY aif.last_forecast_date DESC
    """, {
        'from_date': from_date,
        'to_date': to_date
    }, as_dict=True)
    
    # Calculate accuracy metrics
    for row in data:
        if row.actual_consumption is not None and row.predicted_consumption > 0:
            variance = row.actual_consumption - row.predicted_consumption
            accuracy = 100 - (abs(variance) / row.predicted_consumption * 100)
            accuracy = max(0, min(100, accuracy))
            
            row.variance = variance
            row.accuracy_percentage = accuracy
            
            # Performance grading
            if accuracy >= 90:
                row.performance_grade = "Excellent"
            elif accuracy >= 80:
                row.performance_grade = "Good"
            elif accuracy >= 70:
                row.performance_grade = "Fair"
            elif accuracy >= 60:
                row.performance_grade = "Poor"
            else:
                row.performance_grade = "Very Poor"
        else:
            row.actual_consumption = 0
            row.variance = -row.predicted_consumption
            row.accuracy_percentage = 0
            row.performance_grade = "No Data"
    
    return data

def get_accuracy_chart(filters):
    from_date = filters.get('from_date', add_days(frappe.utils.nowdate(), -30))
    to_date = filters.get('to_date', frappe.utils.nowdate())
    
    # Daily accuracy trend
    daily_accuracy = frappe.db.sql("""
        SELECT 
            DATE(aif.last_forecast_date) as date,
            AVG(
                CASE 
                    WHEN actual_consumption.actual > 0 AND aif.predicted_consumption > 0
                    THEN 100 - (ABS(actual_consumption.actual - aif.predicted_consumption) / aif.predicted_consumption * 100)
                    ELSE 0
                END
            ) as avg_accuracy
        FROM `tabAI Inventory Forecast` aif
        LEFT JOIN (
            SELECT 
                item_code,
                warehouse,
                DATE(posting_date) as date,
                ABS(SUM(actual_qty)) as actual
            FROM `tabStock Ledger Entry`
            WHERE actual_qty < 0
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY item_code, warehouse, DATE(posting_date)
        ) actual_consumption ON actual_consumption.item_code = aif.item_code 
            AND actual_consumption.warehouse = aif.warehouse
            AND actual_consumption.date = DATE(aif.last_forecast_date)
        WHERE DATE(aif.last_forecast_date) BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY DATE(aif.last_forecast_date)
        ORDER BY date
    """, {
        'from_date': from_date,
        'to_date': to_date
    }, as_dict=True)
    
    return {
        "data": {
            "labels": [d.date.strftime('%Y-%m-%d') for d in daily_accuracy],
            "datasets": [
                {
                    "name": "Accuracy %",
                    "values": [round(d.avg_accuracy, 1) for d in daily_accuracy]
                }
            ]
        },
        "type": "line",
        "height": 300,
        "colors": ["#28a745"]
    }

def get_accuracy_summary(data):
    if not data:
        return []
    
    total_forecasts = len(data)
    accurate_forecasts = len([d for d in data if d.accuracy_percentage >= 80])
    avg_accuracy = sum(d.accuracy_percentage for d in data) / total_forecasts
    
    excellent_count = len([d for d in data if d.performance_grade == "Excellent"])
    good_count = len([d for d in data if d.performance_grade == "Good"])
    poor_count = len([d for d in data if d.performance_grade in ["Poor", "Very Poor"]])
    
    return [
        {
            "value": total_forecasts,
            "label": "Total Forecasts",
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": f"{avg_accuracy:.1f}%",
            "label": "Average Accuracy",
            "datatype": "Data",
            "indicator": "Green" if avg_accuracy > 80 else "Orange" if avg_accuracy > 60 else "Red"
        },
        {
            "value": accurate_forecasts,
            "label": "Accurate Forecasts (>80%)",
            "datatype": "Int",
            "indicator": "Green"
        },
        {
            "value": excellent_count,
            "label": "Excellent Performance",
            "datatype": "Int",
            "indicator": "Green"
        },
        {
            "value": good_count,
            "label": "Good Performance", 
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": poor_count,
            "label": "Poor Performance",
            "datatype": "Int",
            "indicator": "Red"
        }
    ]

# ai_inventory/ai_inventory/report/stock_movement_prediction/stock_movement_prediction.py

import frappe
from frappe.utils import flt, nowdate, add_days, getdate
from frappe import _
import json

def execute(filters=None):
    if not filters:
        filters = {}
        
    columns = get_columns()
    data = get_prediction_data(filters)
    chart = get_prediction_chart(filters)
    summary = get_prediction_summary(data)
    
    return columns, data, None, chart, summary

def get_columns():
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
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 100
        },
        {
            "label": _("Current Stock"),
            "fieldname": "current_stock",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("7-Day Prediction"),
            "fieldname": "prediction_7d",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("15-Day Prediction"),
            "fieldname": "prediction_15d",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("30-Day Prediction"),
            "fieldname": "prediction_30d",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Stock Out Date"),
            "fieldname": "stock_out_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Days to Stock Out"),
            "fieldname": "days_to_stockout",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": _("Risk Level"),
            "fieldname": "risk_level",
            "fieldtype": "Data",
            "width": 100
        }
    ]

def get_prediction_data(filters):
    conditions = ""
    if filters.get("warehouse"):
        conditions += " AND aif.warehouse = %(warehouse)s"
    if filters.get("item_group"):
        conditions += " AND aif.item_group = %(item_group)s"
    if filters.get("movement_type"):
        conditions += " AND aif.movement_type = %(movement_type)s"
    
    data = frappe.db.sql(f"""
        SELECT 
            aif.item_code,
            aif.item_name,
            aif.warehouse,
            aif.current_stock,
            aif.predicted_consumption,
            aif.forecast_period_days,
            aif.movement_type,
            aif.confidence_score
        FROM `tabAI Inventory Forecast` aif
        WHERE aif.predicted_consumption > 0
        {conditions}
        ORDER BY aif.movement_type = 'Fast Moving' DESC, aif.current_stock ASC
    """, filters, as_dict=True)
    
    for row in data:
        daily_consumption = row.predicted_consumption / row.forecast_period_days if row.forecast_period_days > 0 else 0
        
        # Calculate predictions for different periods
        row.prediction_7d = daily_consumption * 7
        row.prediction_15d = daily_consumption * 15  
        row.prediction_30d = daily_consumption * 30
        
        # Calculate stock out date
        if daily_consumption > 0:
            days_until_stockout = row.current_stock / daily_consumption
            row.days_to_stockout = int(days_until_stockout)
            row.stock_out_date = add_days(nowdate(), int(days_until_stockout))
            
            # Risk assessment
            if days_until_stockout <= 7:
                row.risk_level = "Critical"
            elif days_until_stockout <= 15:
                row.risk_level = "High"
            elif days_until_stockout <= 30:
                row.risk_level = "Medium" 
            else:
                row.risk_level = "Low"
        else:
            row.days_to_stockout = 999
            row.stock_out_date = None
            row.risk_level = "No Risk"
    
    return data

def get_prediction_chart(filters):
    # Risk level distribution
    risk_data = frappe.db.sql(f"""
        SELECT 
            CASE 
                WHEN aif.current_stock / (aif.predicted_consumption / aif.forecast_period_days) <= 7 THEN 'Critical'
                WHEN aif.current_stock / (aif.predicted_consumption / aif.forecast_period_days) <= 15 THEN 'High'
                WHEN aif.current_stock / (aif.predicted_consumption / aif.forecast_period_days) <= 30 THEN 'Medium'
                ELSE 'Low'
            END as risk_level,
            COUNT(*) as count
        FROM `tabAI Inventory Forecast` aif
        WHERE aif.predicted_consumption > 0 
        AND aif.forecast_period_days > 0
        GROUP BY risk_level
        ORDER BY FIELD(risk_level, 'Critical', 'High', 'Medium', 'Low')
    """, as_dict=True)
    
    return {
        "data": {
            "labels": [d.risk_level for d in risk_data],
            "datasets": [
                {
                    "name": "Risk Distribution",
                    "values": [d.count for d in risk_data]
                }
            ]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#dc3545", "#fd7e14", "#ffc107", "#28a745"]
    }

def get_prediction_summary(data):
    if not data:
        return []
    
    critical_items = len([d for d in data if d.risk_level == "Critical"])
    high_risk_items = len([d for d in data if d.risk_level == "High"])
    avg_days_to_stockout = sum(d.days_to_stockout for d in data if d.days_to_stockout < 999) / len([d for d in data if d.days_to_stockout < 999])
    
    return [
        {
            "value": len(data),
            "label": "Total Items Analyzed",
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": critical_items,
            "label": "Critical Risk Items",
            "datatype": "Int",
            "indicator": "Red"
        },
        {
            "value": high_risk_items,
            "label": "High Risk Items",
            "datatype": "Int",
            "indicator": "Orange"
        },
        {
            "value": f"{avg_days_to_stockout:.0f}",
            "label": "Avg Days to Stock Out",
            "datatype": "Data",
            "indicator": "Orange" if avg_days_to_stockout < 30 else "Green"
        }
    ]

# ai_inventory/ai_inventory/page/ai_inventory_control_center/ai_inventory_control_center.py

import frappe
from frappe import _
import json
from frappe.utils import nowdate, now, add_days

@frappe.whitelist()
def get_control_center_data():
    """Get comprehensive data for AI Inventory Control Center"""
    
    # Get summary statistics
    summary_stats = get_summary_statistics()
    
    # Get critical alerts
    critical_alerts = get_critical_alerts()
    
    # Get performance metrics
    performance_metrics = get_performance_metrics()
    
    # Get recent activities
    recent_activities = get_recent_activities()
    
    # Get warehouse-wise breakdown
    warehouse_breakdown = get_warehouse_breakdown()
    
    return {
        "summary_stats": summary_stats,
        "critical_alerts": critical_alerts,
        "performance_metrics": performance_metrics,
        "recent_activities": recent_activities,
        "warehouse_breakdown": warehouse_breakdown,
        "last_updated": now()
    }

def get_summary_statistics():
    """Get overall summary statistics"""
    stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE WHEN reorder_alert = 1 THEN 1 ELSE 0 END) as total_alerts,
            SUM(CASE WHEN movement_type = 'Fast Moving' THEN 1 ELSE 0 END) as fast_moving,
            SUM(CASE WHEN movement_type = 'Slow Moving' THEN 1 ELSE 0 END) as slow_moving,
            SUM(CASE WHEN movement_type = 'Non Moving' THEN 1 ELSE 0 END) as non_moving,
            SUM(CASE WHEN movement_type = 'Critical' THEN 1 ELSE 0 END) as critical_items,
            AVG(confidence_score) as avg_confidence,
            SUM(CASE WHEN confidence_score < 60 THEN 1 ELSE 0 END) as low_confidence_items,
            COUNT(DISTINCT warehouse) as total_warehouses
        FROM `tabAI Inventory Forecast`
        WHERE last_forecast_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    """, as_dict=True)[0]
    
    return stats

def get_critical_alerts():
    """Get critical stock alerts requiring immediate attention"""
    alerts = frappe.db.sql("""
        SELECT 
            aif.item_code,
            aif.item_name,
            aif.warehouse,
            aif.current_stock,
            aif.reorder_level,
            aif.movement_type,
            aif.suggested_qty,
            aif.confidence_score,
            ROUND((aif.current_stock / NULLIF(aif.reorder_level, 0)) * 100, 1) as stock_ratio
        FROM `tabAI Inventory Forecast` aif
        WHERE aif.reorder_alert = 1
        AND aif.movement_type IN ('Fast Moving', 'Critical')
        ORDER BY 
            (aif.current_stock / NULLIF(aif.reorder_level, 0)) ASC,
            aif.movement_type = 'Critical' DESC
        LIMIT 20
    """, as_dict=True)
    
    return alerts

def get_performance_metrics():
    """Get AI forecasting performance metrics"""
    # Get accuracy data from last 30 days
    accuracy_data = frappe.db.sql("""
        SELECT 
            DATE(aif.last_forecast_date) as forecast_date,
            COUNT(*) as total_forecasts,
            AVG(aif.confidence_score) as avg_confidence,
            SUM(CASE WHEN aif.confidence_score >= 80 THEN 1 ELSE 0 END) as high_confidence_count
        FROM `tabAI Inventory Forecast` aif
        WHERE aif.last_forecast_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(aif.last_forecast_date)
        ORDER BY forecast_date DESC
        LIMIT 30
    """, as_dict=True)
    
    # Calculate trends
    if len(accuracy_data) >= 2:
        recent_confidence = accuracy_data[0]['avg_confidence'] or 0
        previous_confidence = accuracy_data[1]['avg_confidence'] or 0
        confidence_trend = recent_confidence - previous_confidence
    else:
        confidence_trend = 0
    
    return {
        "accuracy_trend": accuracy_data,
        "confidence_trend": confidence_trend,
        "total_forecasts_today": accuracy_data[0]['total_forecasts'] if accuracy_data else 0
    }

def get_recent_activities():
    """Get recent forecast activities and system events"""
    activities = []
    
    # Recent forecast updates
    recent_forecasts = frappe.db.sql("""
        SELECT 
            item_code,
            warehouse,
            movement_type,
            last_forecast_date,
            'forecast_update' as activity_type
        FROM `tabAI Inventory Forecast`
        WHERE last_forecast_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY last_forecast_date DESC
        LIMIT 10
    """, as_dict=True)
    
    activities.extend(recent_forecasts)
    
    # Recent reorder alerts
    recent_alerts = frappe.db.sql("""
        SELECT 
            item_code,
            warehouse,
            'New reorder alert triggered' as description,
            last_forecast_date,
            'reorder_alert' as activity_type
        FROM `tabAI Inventory Forecast`
        WHERE reorder_alert = 1
        AND last_forecast_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY last_forecast_date DESC
        LIMIT 5
    """, as_dict=True)
    
    activities.extend(recent_alerts)
    
    # Sort by timestamp
    activities.sort(key=lambda x: x.get('last_forecast_date', ''), reverse=True)
    
    return activities[:15]

def get_warehouse_breakdown():
    """Get warehouse-wise inventory breakdown"""
    breakdown = frappe.db.sql("""
        SELECT 
            warehouse,
            COUNT(*) as total_items,
            SUM(CASE WHEN reorder_alert = 1 THEN 1 ELSE 0 END) as alert_count,
            SUM(CASE WHEN movement_type = 'Fast Moving' THEN 1 ELSE 0 END) as fast_moving_count,
            AVG(confidence_score) as avg_confidence,
            SUM(current_stock) as total_stock_units
        FROM `tabAI Inventory Forecast`
        GROUP BY warehouse
        ORDER BY alert_count DESC, total_items DESC
    """, as_dict=True)
    
    return breakdown

@frappe.whitelist()
def run_emergency_forecast(item_codes=None, warehouse=None):
    """Run emergency forecast for specific items or warehouse"""
    try:
        filters = {}
        if item_codes:
            if isinstance(item_codes, str):
                item_codes = json.loads(item_codes)
            filters['item_code'] = ['in', item_codes]
        
        if warehouse:
            filters['warehouse'] = warehouse
        
        forecasts = frappe.get_all("AI Inventory Forecast", 
            filters=filters, 
            fields=["name", "item_code", "warehouse"])
        
        results = []
        for forecast in forecasts:
            doc = frappe.get_doc("AI Inventory Forecast", forecast.name)
            doc.run_ai_forecast()
            doc.save()
            
            results.append({
                "item_code": doc.item_code,
                "warehouse": doc.warehouse,
                "movement_type": doc.movement_type,
                "reorder_alert": doc.reorder_alert,
                "confidence_score": doc.confidence_score
            })
        
        return {
            "success": True,
            "message": f"Emergency forecast completed for {len(results)} items",
            "results": results
        }
        
    except Exception as e:
        frappe.log_error(f"Emergency forecast failed: {str(e)}")
        return {
            "success": False,
            "message": f"Emergency forecast failed: {str(e)}"
        }

@frappe.whitelist()
def bulk_create_purchase_orders(item_data=None):
    """Create purchase orders for multiple items"""
    try:
        if isinstance(item_data, str):
            item_data = json.loads(item_data)
        
        created_pos = []
        
        # Group by supplier
        supplier_items = {}
        for item in item_data:
            forecast_doc = frappe.get_doc("AI Inventory Forecast", item['forecast_id'])
            supplier = forecast_doc.supplier or item.get('supplier')
            
            if not supplier:
                continue
                
            if supplier not in supplier_items:
                supplier_items[supplier] = []
            
            supplier_items[supplier].append({
                'item_code': forecast_doc.item_code,
                'qty': forecast_doc.suggested_qty,
                'warehouse': forecast_doc.warehouse,
                'schedule_date': add_days(nowdate(), forecast_doc.lead_time_days)
            })
        
        # Create POs for each supplier
        for supplier, items in supplier_items.items():
            po_doc = frappe.get_doc({
                "doctype": "Purchase Order",
                "supplier": supplier,
                "transaction_date": nowdate(),
                "items": items
            })
            
            po_doc.insert()
            created_pos.append(po_doc.name)
        
        return {
            "success": True,
            "message": f"Created {len(created_pos)} Purchase Orders",
            "po_names": created_pos
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk PO creation failed: {str(e)}")
        return {
            "success": False,
            "message": f"Bulk PO creation failed: {str(e)}"
        }

@frappe.whitelist()
def get_forecast_analytics(period="30_days"):
    """Get advanced analytics for forecast performance"""
    try:
        if period == "7_days":
            date_filter = "DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif period == "30_days":
            date_filter = "DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        else:
            date_filter = "DATE_SUB(CURDATE(), INTERVAL 90 DAY)"
        
        # Movement type trends
        movement_trends = frappe.db.sql(f"""
            SELECT 
                DATE(last_forecast_date) as date,
                movement_type,
                COUNT(*) as count
            FROM `tabAI Inventory Forecast`
            WHERE last_forecast_date >= {date_filter}
            GROUP BY DATE(last_forecast_date), movement_type
            ORDER BY date, movement_type
        """, as_dict=True)
        
        # Confidence distribution
        confidence_dist = frappe.db.sql(f"""
            SELECT 
                CASE 
                    WHEN confidence_score >= 90 THEN '90-100%'
                    WHEN confidence_score >= 80 THEN '80-89%'
                    WHEN confidence_score >= 70 THEN '70-79%'
                    WHEN confidence_score >= 60 THEN '60-69%'
                    ELSE 'Below 60%'
                END as confidence_range,
                COUNT(*) as count
            FROM `tabAI Inventory Forecast`
            WHERE last_forecast_date >= {date_filter}
            GROUP BY confidence_range
            ORDER BY confidence_range DESC
        """, as_dict=True)
        
        # Reorder alert trends
        alert_trends = frappe.db.sql(f"""
            SELECT 
                DATE(last_forecast_date) as date,
                SUM(CASE WHEN reorder_alert = 1 THEN 1 ELSE 0 END) as alert_count,
                COUNT(*) as total_forecasts
            FROM `tabAI Inventory Forecast`
            WHERE last_forecast_date >= {date_filter}
            GROUP BY DATE(last_forecast_date)
            ORDER BY date
        """, as_dict=True)
        
        return {
            "movement_trends": movement_trends,
            "confidence_distribution": confidence_dist,
            "alert_trends": alert_trends
        }
        
    except Exception as e:
        frappe.log_error(f"Analytics generation failed: {str(e)}")
        return {"error": str(e)}