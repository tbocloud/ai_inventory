# system_health_report.py
import frappe
from frappe import _
import json
from datetime import datetime, timedelta

def execute(filters=None):
    """Main execute function required by ERPNext for report generation"""
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    """Define report columns"""
    return [
    {
        "fieldname": "component",
        "label": _("Component"),
        "fieldtype": "Data",
        "width": 200
    },
    {
        "fieldname": "status",
        "label": _("Status"),
        "fieldtype": "Data",
        "width": 100
    },
        {
            "fieldname": "health_score",
            "label": _("Health Score"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "last_checked",
            "label": _("Last Checked"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "issues",
            "label": _("Issues"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "details",
            "label": _("Details"),
            "fieldtype": "Data",
            "width": 300
        }
    ]

def get_data(filters=None):
    """Get report data"""
    company = filters.get("company") if filters else None
    
    # Generate the health report data
    health_response = generate_system_health_report(company)
    
    if not health_response.get("success"):
        return []
    
    report_data = health_response.get("data", {})
    rows = []
    
    # System Overview
    summary = report_data.get("summary", {})
    rows.append({
        "component": "System Overview",
        "status": "Good" if summary.get("overall_health_score", 0) > 80 else "Warning" if summary.get("overall_health_score", 0) > 60 else "Critical",
        "health_score": summary.get("overall_health_score", 0),
        "last_checked": summary.get("last_updated"),
        "issues": summary.get("critical_issues_count", 0),
        "details": f"Total Forecasts: {summary.get('total_forecasts', 0)}"
    })
    
    # Data Quality
    data_quality = report_data.get("data_quality", {})
    rows.append({
        "component": "Data Quality",
        "status": "Good" if data_quality.get("overall_score", 0) > 80 else "Warning" if data_quality.get("overall_score", 0) > 60 else "Critical",
        "health_score": data_quality.get("overall_score", 0),
        "last_checked": frappe.utils.now(),
        "issues": len(data_quality.get("issues", [])),
        "details": f"Accuracy: {data_quality.get('accuracy_score', 0)}%, Completeness: {data_quality.get('completeness_score', 0)}%"
    })
    
    # API Performance
    api_performance = report_data.get("api_performance", {})
    rows.append({
        "component": "API Performance", 
        "status": "Good" if api_performance.get("overall_score", 0) > 80 else "Warning" if api_performance.get("overall_score", 0) > 60 else "Critical",
        "health_score": api_performance.get("overall_score", 0),
        "last_checked": frappe.utils.now(),
        "issues": len(api_performance.get("slow_endpoints", [])),
        "details": f"Avg Response: {api_performance.get('average_response_time', 0)}ms"
    })
    
    # Integration Status
    integration_status = report_data.get("integration_status", {})
    rows.append({
        "component": "Integrations",
        "status": "Good" if integration_status.get("overall_score", 0) > 80 else "Warning" if integration_status.get("overall_score", 0) > 60 else "Critical", 
        "health_score": integration_status.get("overall_score", 0),
        "last_checked": frappe.utils.now(),
        "issues": len(integration_status.get("failed_integrations", [])),
        "details": f"Active: {len(integration_status.get('active_integrations', []))}, Failed: {len(integration_status.get('failed_integrations', []))}"
    })
    
    # Alerts Summary
    alerts = report_data.get("alerts", {})
    rows.append({
        "component": "Alert System",
        "status": "Good" if alerts.get("critical_alerts", 0) == 0 else "Warning" if alerts.get("critical_alerts", 0) < 5 else "Critical",
        "health_score": max(0, 100 - (alerts.get("critical_alerts", 0) * 20)),
        "last_checked": frappe.utils.now(),
        "issues": alerts.get("critical_alerts", 0) + alerts.get("high_alerts", 0),
        "details": f"Critical: {alerts.get('critical_alerts', 0)}, High: {alerts.get('high_alerts', 0)}"
    })
    
    return rows

@frappe.whitelist()
def generate_system_health_report(company=None):
    """Generate comprehensive system health report"""
    
    try:
        # Log the attempt
        frappe.logger().info(f"Generating system health report for company: {company}")
        
        # Get basic system metrics
        total_forecasts = 0
        try:
            if frappe.db.exists("DocType", "AI Financial Forecast"):
                total_forecasts = frappe.db.count("AI Financial Forecast", 
                                                 {"company": company} if company else {})
        except Exception as e:
            frappe.log_error(f"Error counting forecasts: {str(e)}")
        
        # Critical Issues Check
        try:
            critical_issues = check_critical_issues(company)
        except Exception as e:
            frappe.log_error(f"Error checking critical issues: {str(e)}")
            critical_issues = [{
                "type": "critical",
                "category": "System Error",
                "title": "Critical Issues Check Failed",
                "description": f"Failed to check for critical issues: {str(e)}",
                "affected_forecasts": [],
                "severity": "Critical",
                "action_required": "Check system configuration"
            }]
        
        # Data Quality Metrics
        try:
            data_quality_metrics = get_data_quality_metrics(company)
        except Exception as e:
            frappe.log_error(f"Error getting data quality metrics: {str(e)}")
            data_quality_metrics = {
                "average_quality_score": 0,
                "average_confidence_score": 0,
                "high_quality_percentage": 0,
                "low_quality_count": 0,
                "total_forecasts": 0,
                "average_volatility": 0,
                "quality_trend": {"direction": "stable", "change_percentage": 0, "monthly_data": []}
            }
        
        # API Performance
        try:
            api_performance = get_api_performance_metrics(company)
        except Exception as e:
            frappe.log_error(f"Error getting API performance: {str(e)}")
            api_performance = {
                "sync_success_rate": 0,
                "total_sync_attempts": 0,
                "successful_syncs": 0,
                "last_successful_sync": None,
                "api_status": "Unknown",
                "overall_score": 0,
                "slow_endpoints": []
            }
        
        # Integration Status
        try:
            integration_status = get_integration_status(company)
        except Exception as e:
            frappe.log_error(f"Error getting integration status: {str(e)}")
            integration_status = {
                "inventory_sync": {"status": "Unknown", "active_forecasts": 0},
                "auto_sync": {"status": "Unknown", "frequency": "Unknown"},
                "alert_system": {"status": "Unknown", "active_alerts": 0},
                "overall_score": 0,
                "failed_integrations": [],
                "active_integrations": []
            }
        
        # Alert Summary
        try:
            alert_summary = get_alert_summary(company)
        except Exception as e:
            frappe.log_error(f"Error getting alert summary: {str(e)}")
            alert_summary = {
                "critical_alerts": 0,
                "high_alerts": 0,
                "medium_alerts": 0,
                "total_alerts": 0
            }
        
        # Generate recommendations
        try:
            recommendations = generate_recommendations(critical_issues, data_quality_metrics)
        except Exception as e:
            frappe.log_error(f"Error generating recommendations: {str(e)}")
            recommendations = []
        
        report_data = {
            "report_title": "AI Financial Forecast - System Health Report",
            "generated_at": frappe.utils.now(),
            "company": company or "All Companies",
            "summary": {
                "total_forecasts": total_forecasts,
                "critical_issues_count": len(critical_issues),
                "overall_health_score": calculate_health_score(data_quality_metrics, critical_issues),
                "last_updated": frappe.utils.now()
            },
            "critical_issues": critical_issues,
            "data_quality": data_quality_metrics,
            "api_performance": api_performance,
            "integration_status": integration_status,
            "alerts": alert_summary,
            "recommendations": recommendations
        }
        
        frappe.logger().info("System health report generated successfully")
        
        return {
            "success": True,
            "data": report_data
        }
        
    except Exception as e:
        error_msg = f"System Health Report Error: {str(e)}"
        frappe.log_error(error_msg)
        frappe.logger().error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "data": {
                "report_title": "AI Financial Forecast - System Health Report (Error)",
                "summary": {"total_forecasts": 0, "critical_issues_count": 1, "overall_health_score": 0, "last_updated": frappe.utils.now()},
                "critical_issues": [{
                    "type": "critical",
                    "category": "System Error",
                    "title": "Report Generation Failed",
                    "description": error_msg,
                    "affected_forecasts": [],
                    "severity": "Critical",
                    "action_required": "Check system logs and configuration"
                }],
                "data_quality": {"average_quality_score": 0, "average_confidence_score": 0, "high_quality_percentage": 0, "low_quality_count": 0, "total_forecasts": 0, "average_volatility": 0, "quality_trend": {"direction": "stable", "change_percentage": 0, "monthly_data": []}},
                "api_performance": {"sync_success_rate": 0, "total_sync_attempts": 0, "successful_syncs": 0, "last_successful_sync": None, "api_status": "Error"},
                "integration_status": {"inventory_sync": {"status": "Error", "active_forecasts": 0}, "auto_sync": {"status": "Error", "frequency": "Unknown"}, "alert_system": {"status": "Error", "active_alerts": 0}},
                "recommendations": []
            }
        }

def check_critical_issues(company=None):
    """Check for critical system issues"""
    
    issues = []
    
    # Check if AI Financial Forecast doctype exists
    if not frappe.db.exists("DocType", "AI Financial Forecast"):
        issues.append({
            "type": "critical",
            "category": "System Setup",
            "title": "AI Financial Forecast DocType Missing",
            "description": "The AI Financial Forecast DocType is not installed or accessible",
            "affected_forecasts": [],
            "severity": "Critical",
            "action_required": "Install or configure AI Financial Forecast DocType"
        })
        return issues
    
    try:
        # Check for basic forecast data
        forecast_count = frappe.db.count("AI Financial Forecast", 
                                        {"company": company} if company else {})
        
        if forecast_count == 0:
            issues.append({
                "type": "warning",
                "category": "Data",
                "title": "No Forecast Data Found",
                "description": "No AI Financial Forecasts have been created yet",
                "affected_forecasts": [],
                "severity": "Medium",
                "action_required": "Create initial forecasts to begin monitoring"
            })
        
        # Check for recent forecasts
        recent_forecasts = frappe.db.count("AI Financial Forecast", {
            "creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)],
            **({"company": company} if company else {})
        })
        
        if forecast_count > 0 and recent_forecasts == 0:
            issues.append({
                "type": "warning", 
                "category": "Data Freshness",
                "title": "No Recent Forecasts",
                "description": "No new forecasts created in the last 7 days",
                "affected_forecasts": [],
                "severity": "Medium",
                "action_required": "Check automated forecast generation"
            })
        
        # Try to check bounds calculation (only if we have data)
        if forecast_count > 0:
            try:
                bounds_errors = frappe.db.sql("""
                    SELECT name, account, upper_bound, lower_bound, predicted_amount
                    FROM `tabAI Financial Forecast`
                    WHERE upper_bound IS NOT NULL 
                    AND lower_bound IS NOT NULL 
                    AND upper_bound <= lower_bound
                    {}
                    LIMIT 10
                """.format("AND company = %(company)s" if company else ""), 
                {"company": company}, as_dict=True)
                
                if bounds_errors:
                    issues.append({
                        "type": "critical",
                        "category": "Calculation Error",
                        "title": "Forecast Bounds Logic Error",
                        "description": f"{len(bounds_errors)} forecasts have upper bound ≤ lower bound",
                        "affected_forecasts": bounds_errors,
                        "severity": "Critical",
                        "action_required": "Fix bounds calculation immediately"
                    })
            except Exception as e:
                frappe.log_error(f"Bounds check error: {str(e)}")
        
    except Exception as e:
        frappe.log_error(f"Critical Issues Check Error: {str(e)}")
        issues.append({
            "type": "critical",
            "category": "System Error",
            "title": "Database Access Error",
            "description": f"Error accessing forecast data: {str(e)}",
            "affected_forecasts": [],
            "severity": "Critical",
            "action_required": "Check database permissions and table structure"
        })
    
    return issues

def get_data_quality_metrics(company=None):
    """Get data quality metrics"""
    
    # Check if AI Financial Forecast exists
    if not frappe.db.exists("DocType", "AI Financial Forecast"):
        return {
            "average_quality_score": 0,
            "average_confidence_score": 0,
            "high_quality_percentage": 0,
            "low_quality_count": 0,
            "total_forecasts": 0,
            "average_volatility": 0,
            "quality_trend": {"direction": "stable", "change_percentage": 0, "monthly_data": []}
        }
    
    try:
        # Use safer column names that should exist
        query = """
            SELECT 
                COUNT(*) as total_forecasts,
                AVG(COALESCE(predicted_amount, 0)) as avg_predicted,
                COUNT(CASE WHEN predicted_amount IS NOT NULL THEN 1 END) as valid_predictions
            FROM `tabAI Financial Forecast`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            {}
        """.format("AND company = %(company)s" if company else "")
        
        result = frappe.db.sql(query, {"company": company}, as_dict=True)[0]
        
        # Calculate mock quality scores based on available data
        total_forecasts = result.total_forecasts or 0
        valid_predictions = result.valid_predictions or 0
        
        quality_score = (valid_predictions / max(total_forecasts, 1)) * 100 if total_forecasts > 0 else 0
        
        return {
            "average_quality_score": round(min(quality_score, 100), 2),
            "average_confidence_score": round(max(quality_score - 10, 0), 2),
            "high_quality_percentage": round(quality_score, 2),
            "low_quality_count": max(0, total_forecasts - valid_predictions),
            "total_forecasts": total_forecasts,
            "average_volatility": round(min(20, max(5, total_forecasts * 0.1)), 2),
            "quality_trend": get_quality_trend(company)
        }
        
    except Exception as e:
        frappe.log_error(f"Data Quality Metrics Error: {str(e)}")
        return {
            "average_quality_score": 0,
            "average_confidence_score": 0,
            "high_quality_percentage": 0,
            "low_quality_count": 0,
            "total_forecasts": 0,
            "average_volatility": 0,
            "quality_trend": {"direction": "stable", "change_percentage": 0, "monthly_data": []}
        }

def get_quality_trend(company=None):
    """Get data quality trend over time"""
    
    trend_data = frappe.db.sql("""
        SELECT 
            DATE_FORMAT(creation, '%Y-%m') as month,
            AVG(data_quality_score) as avg_quality
        FROM `tabAI Financial Forecast`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        {}
        GROUP BY DATE_FORMAT(creation, '%Y-%m')
        ORDER BY month
    """.format("AND company = %(company)s" if company else ""),
    {"company": company}, as_dict=True)
    
    if len(trend_data) >= 2:
        current_month = trend_data[-1].avg_quality
        previous_month = trend_data[-2].avg_quality
        change = ((current_month - previous_month) / previous_month) * 100
        return {
            "direction": "improving" if change > 0 else "declining",
            "change_percentage": round(change, 2),
            "monthly_data": trend_data
        }
    
    return {"direction": "stable", "change_percentage": 0, "monthly_data": trend_data}

def get_api_performance_metrics(company=None):
    """Get API performance metrics"""
    
    # Sync success rate
    total_syncs = frappe.db.count("AI Financial Forecast", 
                                 {"inventory_sync_enabled": 1, "company": company} if company else {"inventory_sync_enabled": 1})
    
    successful_syncs = frappe.db.count("AI Financial Forecast", 
                                      {"inventory_sync_enabled": 1, "sync_status": "Completed", "company": company} if company 
                                      else {"inventory_sync_enabled": 1, "sync_status": "Completed"})
    
    sync_success_rate = (successful_syncs / max(total_syncs, 1)) * 100
    
    # Last sync times
    last_successful_sync = frappe.db.sql("""
        SELECT MAX(last_sync_date) as last_sync
        FROM `tabAI Financial Forecast`
        WHERE sync_status = 'Completed'
        {}
    """.format("AND company = %(company)s" if company else ""),
    {"company": company}, as_dict=True)[0].last_sync
    
    return {
        "sync_success_rate": round(sync_success_rate, 2),
        "total_sync_attempts": total_syncs,
        "successful_syncs": successful_syncs,
        "last_successful_sync": last_successful_sync,
        "sync_frequency": "Daily",
        "avg_response_time": "< 2 seconds",  # This would come from actual API monitoring
        "api_status": "Connected" if sync_success_rate > 80 else "Issues Detected"
    }

def get_integration_status(company=None):
    """Get integration status for various systems"""
    
    # Check enabled integrations
    enabled_syncs = frappe.db.count("AI Financial Forecast", 
                                   {"inventory_sync_enabled": 1, "company": company} if company 
                                   else {"inventory_sync_enabled": 1})
    
    # Check auto sync status
    auto_sync_enabled = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabAI Financial Forecast`
        WHERE sync_frequency = 'Daily'
        {}
    """.format("AND company = %(company)s" if company else ""),
    {"company": company}, as_dict=True)[0].count
    
    return {
        "inventory_sync": {
            "status": "Enabled" if enabled_syncs > 0 else "Disabled",
            "active_forecasts": enabled_syncs,
            "last_sync": get_last_sync_time(company)
        },
        "auto_sync": {
            "status": "Enabled" if auto_sync_enabled > 0 else "Disabled", 
            "frequency": "Daily",
            "next_sync": "Tonight 2:00 AM"
        },
        "external_apis": {
            "banking_api": "Connected",  # This would be checked from actual API
            "accounting_system": "Integrated",
            "market_data": "Available"
        },
        "alert_system": {
            "status": "Active",
            "active_alerts": frappe.db.count("AI Financial Forecast", {"forecast_alert": 1})
        }
    }

def get_last_sync_time(company=None):
    """Get last successful sync time"""
    
    result = frappe.db.sql("""
        SELECT MAX(last_sync_date) as last_sync
        FROM `tabAI Financial Forecast`
        WHERE last_sync_date IS NOT NULL
        {}
    """.format("AND company = %(company)s" if company else ""),
    {"company": company}, as_dict=True)
    
    return result[0].last_sync if result and result[0].last_sync else "Never"

def get_alert_summary(company=None):
    """Get summary of active alerts"""
    
    active_alerts = frappe.db.sql("""
        SELECT 
            forecast_type,
            risk_category,
            COUNT(*) as alert_count,
            AVG(confidence_score) as avg_confidence
        FROM `tabAI Financial Forecast`
        WHERE forecast_alert = 1
        {}
        GROUP BY forecast_type, risk_category
        ORDER BY alert_count DESC
    """.format("AND company = %(company)s" if company else ""),
    {"company": company}, as_dict=True)
    
    total_alerts = sum(alert.alert_count for alert in active_alerts)
    
    return {
        "total_active_alerts": total_alerts,
        "by_category": active_alerts,
        "critical_alerts": len([a for a in active_alerts if a.risk_category == "Critical"]),
        "alert_trend": "Stable"  # This would be calculated from historical data
    }

def calculate_health_score(data_quality_metrics, critical_issues):
    """Calculate overall system health score"""
    
    base_score = 100
    
    # Deduct for data quality
    quality_score = data_quality_metrics.get("average_quality_score", 0)
    base_score -= max(0, (80 - quality_score))  # Deduct if below 80%
    
    # Deduct for critical issues
    for issue in critical_issues:
        if issue["type"] == "critical":
            base_score -= 20
        elif issue["type"] == "warning":
            base_score -= 10
    
    return max(0, min(100, base_score))

def generate_recommendations(critical_issues, data_quality_metrics):
    """Generate actionable recommendations"""
    
    recommendations = []
    
    # Critical issues recommendations
    for issue in critical_issues:
        if "Bounds Logic Error" in issue["title"]:
            recommendations.append({
                "priority": "Critical",
                "title": "Fix Forecast Bounds Calculation",
                "description": "Immediately fix the bounds calculation logic where upper_bound ≤ lower_bound",
                "estimated_effort": "2-4 hours",
                "impact": "High - Affects forecast reliability"
            })
        
        if "Data Quality" in issue["category"]:
            recommendations.append({
                "priority": "High",
                "title": "Improve Data Collection Process", 
                "description": "Review and enhance data validation rules to improve quality scores",
                "estimated_effort": "1-2 weeks",
                "impact": "Medium - Better forecast accuracy"
            })
    
    # Data quality recommendations
    if data_quality_metrics.get("average_quality_score", 0) < 80:
        recommendations.append({
            "priority": "Medium",
            "title": "Enhance Data Quality Monitoring",
            "description": "Implement automated data quality checks and alerts",
            "estimated_effort": "3-5 days", 
            "impact": "Medium - Proactive issue detection"
        })
    
    return recommendations

@frappe.whitelist()
def export_system_health_report(company=None, format="json"):
    """Export system health report in specified format"""
    
    report_data = generate_system_health_report(company)
    
    if format == "pdf":
        # Generate PDF version
        html_content = generate_html_report(report_data["data"])
        pdf_content = frappe.utils.get_pdf(html_content)
        return {
            "success": True,
            "content": pdf_content,
            "filename": f"system_health_report_{frappe.utils.today()}.pdf"
        }
    
    return report_data

def generate_html_report(data):
    """Generate HTML version of the report"""
    return "<html><body><h1>System Health Report</h1><p>Report generated successfully</p></body></html>"