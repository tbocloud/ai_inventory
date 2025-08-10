"""
Financial Forecast Dashboard
Comprehensive dashboard for AI financial forecasting analytics
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

@frappe.whitelist()
def get_dashboard_data(company=None, period="month"):
    """
    Get comprehensive dashboard data for financial forecasting
    """
    try:
        dashboard_data = {
            "summary_metrics": get_summary_metrics(company, period),
            "forecast_performance": get_forecast_performance(company, period),
            "trend_analysis": get_trend_analysis(company, period),
            "risk_analysis": get_risk_analysis(company),
            "recent_forecasts": get_recent_forecasts(company),
            "alerts_notifications": get_alerts_and_notifications(company),
            "integration_status": get_integration_status(company)
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard data error: {str(e)}", "Financial Forecast Dashboard")
        return {
            "success": False,
            "error": str(e)
        }

def get_summary_metrics(company=None, period="month"):
    """Get high-level summary metrics"""
    
    # Date filter
    if period == "week":
        start_date = datetime.now() - timedelta(days=7)
    elif period == "month":
        start_date = datetime.now() - timedelta(days=30)
    elif period == "quarter":
        start_date = datetime.now() - timedelta(days=90)
    else:
        start_date = datetime.now() - timedelta(days=365)
    
    filters = {"creation": [">=", start_date.strftime("%Y-%m-%d")]}
    if company:
        filters["company"] = company
    
    # Get all forecasts in period
    forecasts = frappe.get_all("AI Financial Forecast", 
                              filters=filters,
                              fields=["predicted_amount", "confidence_score", "forecast_type", 
                                     "risk_category", "company", "currency"])
    
    if not forecasts:
        return {
            "total_forecasts": 0,
            "total_predicted_value": 0,
            "average_confidence": 0,
            "high_confidence_count": 0,
            "currency": "INR"
        }
    
    total_predicted = sum(f.predicted_amount for f in forecasts if f.predicted_amount)
    avg_confidence = sum(f.confidence_score for f in forecasts) / len(forecasts)
    high_confidence = len([f for f in forecasts if f.confidence_score >= 80])
    
    # Get most common currency
    currencies = [f.currency for f in forecasts if f.currency]
    most_common_currency = max(set(currencies), key=currencies.count) if currencies else "INR"
    
    # Forecast type distribution
    type_distribution = {}
    for f in forecasts:
        if f.forecast_type in type_distribution:
            type_distribution[f.forecast_type] += 1
        else:
            type_distribution[f.forecast_type] = 1
    
    return {
        "total_forecasts": len(forecasts),
        "total_predicted_value": total_predicted,
        "average_confidence": round(avg_confidence, 1),
        "high_confidence_count": high_confidence,
        "high_confidence_percentage": round(high_confidence / len(forecasts) * 100, 1),
        "type_distribution": type_distribution,
        "currency": most_common_currency,
        "period": period
    }

def get_forecast_performance(company=None, period="month"):
    """Get forecast performance metrics"""
    
    # Get forecasts with historical comparison
    sql_query = """
        SELECT 
            forecast_type,
            AVG(confidence_score) as avg_confidence,
            COUNT(*) as count,
            AVG(predicted_amount) as avg_predicted,
            SUM(CASE WHEN confidence_score >= 80 THEN 1 ELSE 0 END) as high_confidence_count
        FROM `tabAI Financial Forecast`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        {company_filter}
        GROUP BY forecast_type
        ORDER BY avg_confidence DESC
    """.format(
        company_filter="AND company = %(company)s" if company else ""
    )
    
    params = {"company": company} if company else {}
    performance_data = frappe.db.sql(sql_query, params, as_dict=True)
    
    # Calculate performance trends
    performance_metrics = []
    for data in performance_data:
        performance_metrics.append({
            "forecast_type": data.forecast_type,
            "average_confidence": round(data.avg_confidence, 1),
            "forecast_count": data.count,
            "average_predicted": data.avg_predicted or 0,
            "high_confidence_ratio": round((data.high_confidence_count / data.count) * 100, 1),
            "performance_score": calculate_performance_score(data)
        })
    
    return {
        "by_type": performance_metrics,
        "overall_performance": calculate_overall_performance(performance_metrics)
    }

def get_trend_analysis(company=None, period="month"):
    """Get trend analysis for forecasts"""
    
    # Get daily forecast creation trends
    sql_query = """
        SELECT 
            DATE(creation) as date,
            COUNT(*) as forecasts_created,
            AVG(confidence_score) as avg_confidence,
            SUM(predicted_amount) as total_predicted
        FROM `tabAI Financial Forecast`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        {company_filter}
        GROUP BY DATE(creation)
        ORDER BY date
    """.format(
        company_filter="AND company = %(company)s" if company else ""
    )
    
    params = {"company": company} if company else {}
    trend_data = frappe.db.sql(sql_query, params, as_dict=True)
    
    # Calculate trends
    dates = [str(t.date) for t in trend_data]
    forecast_counts = [t.forecasts_created for t in trend_data]
    confidence_scores = [t.avg_confidence for t in trend_data]
    predicted_amounts = [t.total_predicted or 0 for t in trend_data]
    
    return {
        "dates": dates,
        "forecast_creation_trend": forecast_counts,
        "confidence_trend": confidence_scores,
        "predicted_amount_trend": predicted_amounts,
        "trend_direction": calculate_trend_direction(confidence_scores)
    }

def get_risk_analysis(company=None):
    """Get risk analysis for forecasts"""
    
    filters = {}
    if company:
        filters["company"] = company
    
    forecasts = frappe.get_all("AI Financial Forecast",
                              filters=filters,
                              fields=["risk_category", "confidence_score", "predicted_amount", 
                                     "volatility_score", "forecast_type"])
    
    if not forecasts:
        return {"risk_distribution": {}, "risk_metrics": {}}
    
    # Risk category distribution
    risk_distribution = {}
    for f in forecasts:
        risk_cat = f.risk_category or "Unknown"
        if risk_cat in risk_distribution:
            risk_distribution[risk_cat] += 1
        else:
            risk_distribution[risk_cat] = 1
    
    # Risk metrics by forecast type
    risk_by_type = {}
    for f in forecasts:
        ftype = f.forecast_type
        if ftype not in risk_by_type:
            risk_by_type[ftype] = {
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "total": 0
            }
        
        risk_by_type[ftype]["total"] += 1
        risk_cat = f.risk_category or "Unknown"
        
        if risk_cat in ["High", "Critical"]:
            risk_by_type[ftype]["high_risk"] += 1
        elif risk_cat == "Medium":
            risk_by_type[ftype]["medium_risk"] += 1
        else:
            risk_by_type[ftype]["low_risk"] += 1
    
    return {
        "risk_distribution": risk_distribution,
        "risk_by_type": risk_by_type,
        "overall_risk_score": calculate_overall_risk_score(forecasts)
    }

def get_recent_forecasts(company=None, limit=10):
    """Get recent forecasts for display"""
    
    filters = {"creation": [">=", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]}
    if company:
        filters["company"] = company
    
    recent_forecasts = frappe.get_all("AI Financial Forecast",
                                    filters=filters,
                                    fields=["name", "account", "forecast_type", "predicted_amount",
                                           "confidence_score", "risk_category", "creation"],
                                    order_by="creation desc",
                                    limit=limit)
    
    return [
        {
            "id": f.name,
            "account": f.account,
            "type": f.forecast_type,
            "predicted_amount": f.predicted_amount or 0,
            "confidence": f.confidence_score,
            "risk": f.risk_category or "Unknown",
            "created": f.creation.strftime("%Y-%m-%d %H:%M") if f.creation else ""
        }
        for f in recent_forecasts
    ]

def get_alerts_and_notifications(company=None):
    """Get active alerts and notifications"""
    
    filters = {"forecast_alert": 1}
    if company:
        filters["company"] = company
    
    alerts = frappe.get_all("AI Financial Forecast",
                          filters=filters,
                          fields=["name", "account", "forecast_type", "confidence_score",
                                 "risk_category", "predicted_amount"])
    
    notifications = []
    for alert in alerts:
        if alert.confidence_score < 60:
            notifications.append({
                "type": "warning",
                "title": f"Low Confidence Alert",
                "message": f"Forecast for {alert.account} has low confidence ({alert.confidence_score}%)",
                "forecast_id": alert.name
            })
        
        if alert.risk_category in ["High", "Critical"]:
            notifications.append({
                "type": "danger",
                "title": f"High Risk Alert",
                "message": f"Forecast for {alert.account} is high risk ({alert.risk_category})",
                "forecast_id": alert.name
            })
    
    return {
        "active_alerts": len(alerts),
        "notifications": notifications[:5]  # Limit to 5 most important
    }

def get_integration_status(company=None):
    """Get integration status with inventory and other modules"""
    
    # Check inventory sync status
    inventory_synced = frappe.db.count("AI Financial Forecast", {
        "inventory_sync_enabled": 1,
        "company": company if company else ["like", "%"]
    })
    
    total_forecasts = frappe.db.count("AI Financial Forecast", {
        "company": company if company else ["like", "%"]
    })
    
    # Check sync errors
    sync_errors = frappe.db.count("AI Financial Forecast", {
        "sync_status": "Failed",
        "company": company if company else ["like", "%"]
    })
    
    return {
        "inventory_sync_enabled": inventory_synced,
        "total_forecasts": total_forecasts,
        "sync_success_rate": round((inventory_synced / max(total_forecasts, 1)) * 100, 1),
        "sync_errors": sync_errors,
        "integration_health": "Good" if sync_errors == 0 else "Needs Attention"
    }

# Utility functions
def calculate_performance_score(data):
    """Calculate performance score for forecast type"""
    confidence_weight = 0.4
    volume_weight = 0.3
    consistency_weight = 0.3
    
    confidence_score = (data.avg_confidence / 100) * confidence_weight
    volume_score = min(data.count / 10, 1) * volume_weight  # Normalize to max 10
    consistency_score = (data.high_confidence_count / max(data.count, 1)) * consistency_weight
    
    return round((confidence_score + volume_score + consistency_score) * 100, 1)

def calculate_overall_performance(performance_metrics):
    """Calculate overall system performance"""
    if not performance_metrics:
        return {"score": 0, "status": "No Data"}
    
    avg_score = sum(p["performance_score"] for p in performance_metrics) / len(performance_metrics)
    
    if avg_score >= 80:
        status = "Excellent"
    elif avg_score >= 70:
        status = "Good"
    elif avg_score >= 60:
        status = "Fair"
    else:
        status = "Needs Improvement"
    
    return {
        "score": round(avg_score, 1),
        "status": status
    }

def calculate_trend_direction(data_points):
    """Calculate trend direction from data points"""
    if len(data_points) < 2:
        return "Stable"
    
    # Simple linear trend calculation
    recent_avg = sum(data_points[-3:]) / min(len(data_points), 3)
    earlier_avg = sum(data_points[:3]) / min(len(data_points), 3)
    
    if recent_avg > earlier_avg * 1.05:
        return "Improving"
    elif recent_avg < earlier_avg * 0.95:
        return "Declining"
    else:
        return "Stable"

def calculate_overall_risk_score(forecasts):
    """Calculate overall risk score"""
    if not forecasts:
        return {"score": 0, "level": "Unknown"}
    
    risk_weights = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    total_weight = 0
    total_forecasts = len(forecasts)
    
    for f in forecasts:
        risk_cat = f.risk_category or "Medium"
        total_weight += risk_weights.get(risk_cat, 2)
    
    avg_risk = total_weight / total_forecasts
    
    if avg_risk <= 1.5:
        level = "Low"
    elif avg_risk <= 2.5:
        level = "Medium"
    elif avg_risk <= 3.5:
        level = "High"
    else:
        level = "Critical"
    
    return {
        "score": round(avg_risk, 2),
        "level": level
    }

@frappe.whitelist()
def get_forecast_chart_data(company=None, chart_type="confidence_trend", period="month"):
    """Get data for specific chart types"""
    
    try:
        if chart_type == "confidence_trend":
            return get_confidence_trend_data(company, period)
        elif chart_type == "type_distribution":
            return get_type_distribution_data(company, period)
        elif chart_type == "risk_analysis":
            return get_risk_chart_data(company)
        elif chart_type == "performance_comparison":
            return get_performance_comparison_data(company, period)
        else:
            return {"error": "Unknown chart type"}
            
    except Exception as e:
        frappe.log_error(f"Chart data error: {str(e)}", "Financial Forecast Charts")
        return {"error": str(e)}

def get_confidence_trend_data(company=None, period="month"):
    """Get confidence trend data for charts"""
    days = 30 if period == "month" else 7 if period == "week" else 90
    
    sql_query = """
        SELECT 
            DATE(creation) as date,
            AVG(confidence_score) as avg_confidence,
            MIN(confidence_score) as min_confidence,
            MAX(confidence_score) as max_confidence
        FROM `tabAI Financial Forecast`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        {company_filter}
        GROUP BY DATE(creation)
        ORDER BY date
    """.format(
        days=days,
        company_filter="AND company = %(company)s" if company else ""
    )
    
    params = {"company": company} if company else {}
    data = frappe.db.sql(sql_query, params, as_dict=True)
    
    return {
        "labels": [str(d.date) for d in data],
        "datasets": [
            {
                "label": "Average Confidence",
                "data": [d.avg_confidence for d in data],
                "borderColor": "#3498db",
                "backgroundColor": "rgba(52, 152, 219, 0.1)"
            },
            {
                "label": "Min Confidence",
                "data": [d.min_confidence for d in data],
                "borderColor": "#e74c3c",
                "backgroundColor": "rgba(231, 76, 60, 0.1)"
            },
            {
                "label": "Max Confidence",
                "data": [d.max_confidence for d in data],
                "borderColor": "#27ae60",
                "backgroundColor": "rgba(39, 174, 96, 0.1)"
            }
        ]
    }

def get_type_distribution_data(company=None, period="month"):
    """Get forecast type distribution for pie charts"""
    days = 30 if period == "month" else 7 if period == "week" else 90
    
    sql_query = """
        SELECT 
            forecast_type,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence
        FROM `tabAI Financial Forecast`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        {company_filter}
        GROUP BY forecast_type
        ORDER BY count DESC
    """.format(
        days=days,
        company_filter="AND company = %(company)s" if company else ""
    )
    
    params = {"company": company} if company else {}
    data = frappe.db.sql(sql_query, params, as_dict=True)
    
    return {
        "labels": [d.forecast_type for d in data],
        "data": [d.count for d in data],
        "backgroundColor": [
            "#3498db", "#e74c3c", "#27ae60", "#f39c12", "#9b59b6"
        ][:len(data)]
    }

def get_risk_chart_data(company=None):
    """Get risk analysis data for charts"""
    filters = {}
    if company:
        filters["company"] = company
    
    forecasts = frappe.get_all("AI Financial Forecast",
                              filters=filters,
                              fields=["risk_category", "forecast_type"])
    
    risk_by_type = {}
    for f in forecasts:
        ftype = f.forecast_type
        risk_cat = f.risk_category or "Unknown"
        
        if ftype not in risk_by_type:
            risk_by_type[ftype] = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
        
        if risk_cat in risk_by_type[ftype]:
            risk_by_type[ftype][risk_cat] += 1
    
    return {
        "categories": list(risk_by_type.keys()),
        "series": [
            {
                "name": "Low Risk",
                "data": [risk_by_type[cat]["Low"] for cat in risk_by_type.keys()]
            },
            {
                "name": "Medium Risk", 
                "data": [risk_by_type[cat]["Medium"] for cat in risk_by_type.keys()]
            },
            {
                "name": "High Risk",
                "data": [risk_by_type[cat]["High"] for cat in risk_by_type.keys()]
            },
            {
                "name": "Critical Risk",
                "data": [risk_by_type[cat]["Critical"] for cat in risk_by_type.keys()]
            }
        ]
    }

def get_performance_comparison_data(company=None, period="month"):
    """Get performance comparison data"""
    days = 30 if period == "month" else 7 if period == "week" else 90
    
    # Current period performance
    current_perf = get_forecast_performance(company, period)
    
    # Previous period for comparison
    sql_query = """
        SELECT 
            forecast_type,
            AVG(confidence_score) as avg_confidence,
            COUNT(*) as count
        FROM `tabAI Financial Forecast`
        WHERE creation BETWEEN DATE_SUB(CURDATE(), INTERVAL {days2} DAY) 
              AND DATE_SUB(CURDATE(), INTERVAL {days1} DAY)
        {company_filter}
        GROUP BY forecast_type
    """.format(
        days1=days,
        days2=days*2,
        company_filter="AND company = %(company)s" if company else ""
    )
    
    params = {"company": company} if company else {}
    prev_data = frappe.db.sql(sql_query, params, as_dict=True)
    
    prev_perf = {d.forecast_type: d.avg_confidence for d in prev_data}
    
    comparison_data = []
    for curr in current_perf["by_type"]:
        ftype = curr["forecast_type"]
        current_conf = curr["average_confidence"]
        previous_conf = prev_perf.get(ftype, current_conf)
        
        comparison_data.append({
            "forecast_type": ftype,
            "current_confidence": current_conf,
            "previous_confidence": previous_conf,
            "improvement": round(current_conf - previous_conf, 1)
        })
    
    return {
        "comparison": comparison_data,
        "labels": [d["forecast_type"] for d in comparison_data],
        "current_period": [d["current_confidence"] for d in comparison_data],
        "previous_period": [d["previous_confidence"] for d in comparison_data]
    }
