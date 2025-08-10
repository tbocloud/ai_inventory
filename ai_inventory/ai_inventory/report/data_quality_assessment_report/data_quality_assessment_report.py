# data_quality_assessment_report.py
import frappe
from frappe import _
import json
from datetime import datetime, timedelta
import statistics
import calendar

def execute(filters=None):
    """Main execute function for ERPNext report"""
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    """Define report columns"""
    return [
        {
            "fieldname": "metric",
            "label": _("Quality Metric"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "score",
            "label": _("Score"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "grade",
            "label": _("Grade"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "details",
            "label": _("Details"),
            "fieldtype": "Data",
            "width": 300
        }
    ]

def get_data(filters):
    """Get data for the report"""
    try:
        # Extract filters
        company = filters.get('company') if filters else None
        assessment_days = int(filters.get('assessment_days', 90)) if filters else 90
        
        # Generate the quality assessment
        quality_data = generate_data_quality_assessment_report(company, assessment_days)
        
        if not quality_data:
            return generate_sample_quality_data()
        
        # Format data for the report
        data = []
        
        # Overall Score
        data.append({
            "metric": "Overall Quality Score",
            "score": quality_data.get("overall_score", 0),
            "grade": quality_data.get("quality_grade", "N/A"),
            "status": "Good" if quality_data.get("overall_score", 0) >= 80 else "Needs Improvement",
            "details": f"Based on {assessment_days} days assessment"
        })
        
        # Completeness
        completeness = quality_data.get("completeness_metrics", {})
        data.append({
            "metric": "Data Completeness",
            "score": completeness.get("completeness_score", 0),
            "grade": get_quality_grade(completeness.get("completeness_score", 0)),
            "status": "Good" if completeness.get("completeness_score", 0) >= 80 else "Needs Improvement",
            "details": f"Missing fields: {completeness.get('missing_fields_count', 0)}"
        })
        
        # Accuracy
        accuracy = quality_data.get("accuracy_metrics", {})
        data.append({
            "metric": "Data Accuracy",
            "score": accuracy.get("accuracy_score", 0),
            "grade": get_quality_grade(accuracy.get("accuracy_score", 0)),
            "status": "Good" if accuracy.get("accuracy_score", 0) >= 80 else "Needs Improvement",
            "details": f"Outliers detected: {accuracy.get('outliers_detected', 0)}"
        })
        
        # Consistency
        consistency = quality_data.get("consistency_metrics", {})
        data.append({
            "metric": "Data Consistency",
            "score": consistency.get("consistency_score", 0),
            "grade": get_quality_grade(consistency.get("consistency_score", 0)),
            "status": "Good" if consistency.get("consistency_score", 0) >= 80 else "Needs Improvement",
            "details": f"Issues found: {consistency.get('total_issues', 0)}"
        })
        
        # Timeliness
        timeliness = quality_data.get("timeliness_metrics", {})
        data.append({
            "metric": "Data Timeliness",
            "score": timeliness.get("freshness_score", 0),
            "grade": get_quality_grade(timeliness.get("freshness_score", 0)),
            "status": "Good" if timeliness.get("freshness_score", 0) >= 80 else "Needs Improvement",
            "details": f"Last update: {timeliness.get('days_since_last', 'N/A')} days ago"
        })
        
        return data
        
    except Exception as e:
        frappe.log_error(f"Error in Data Quality Assessment Report: {str(e)}")
        return generate_sample_quality_data()

def generate_sample_quality_data():
    """Generate sample data when no real data is available"""
    return [
        {
            "metric": "Overall Quality Score",
            "score": 85.5,
            "grade": "A",
            "status": "Good",
            "details": "Based on 90 days assessment (Sample Data)"
        },
        {
            "metric": "Data Completeness",
            "score": 92.0,
            "grade": "A",
            "status": "Good",
            "details": "Missing fields: 3 (Sample Data)"
        },
        {
            "metric": "Data Accuracy",
            "score": 78.5,
            "grade": "B",
            "status": "Needs Improvement",
            "details": "Outliers detected: 12 (Sample Data)"
        },
        {
            "metric": "Data Consistency",
            "score": 88.0,
            "grade": "A",
            "status": "Good",
            "details": "Issues found: 5 (Sample Data)"
        },
        {
            "metric": "Data Timeliness",
            "score": 83.5,
            "grade": "B",
            "status": "Good",
            "details": "Last update: 2 days ago (Sample Data)"
        }
    ]

def generate_data_quality_assessment_report(company=None, assessment_days=90):
    """Generate comprehensive data quality assessment"""
    try:
        # Check if we have data
        total_records = frappe.db.count("AI Financial Forecast", {
            "creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -assessment_days)],
            "company": company
        } if company else {
            "creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -assessment_days)]
        })
        
        if total_records == 0:
            return None
        
        # Assess different quality dimensions
        completeness_metrics = assess_data_completeness(company, assessment_days)
        accuracy_metrics = assess_data_accuracy(company, assessment_days)
        consistency_metrics = assess_data_consistency(company, assessment_days)
        timeliness_metrics = assess_data_timeliness(company, assessment_days)
        
        # Calculate overall quality score
        overall_score = calculate_overall_quality_score(
            completeness_metrics, accuracy_metrics, 
            consistency_metrics, timeliness_metrics
        )
        
        return {
            "overall_score": overall_score,
            "quality_grade": get_quality_grade(overall_score),
            "completeness_metrics": completeness_metrics,
            "accuracy_metrics": accuracy_metrics,
            "consistency_metrics": consistency_metrics,
            "timeliness_metrics": timeliness_metrics,
            "assessment_period": assessment_days,
            "company": company,
            "total_records": total_records
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating data quality assessment: {str(e)}")
        return None

def assess_data_completeness(company=None, assessment_days=90):
    """Assess data completeness"""
    try:
        # Query for completeness metrics
        filters = {
            "creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -assessment_days)]
        }
        if company:
            filters["company"] = company
            
        total_records = frappe.db.count("AI Financial Forecast", filters)
        
        if total_records == 0:
            return {"completeness_score": 0, "missing_fields_count": 0}
        
        # Count missing critical fields
        missing_company = frappe.db.count("AI Financial Forecast", dict(filters, company=["is", "not set"]))
        missing_amount = frappe.db.count("AI Financial Forecast", dict(filters, predicted_amount=["is", "not set"]))
        missing_date = frappe.db.count("AI Financial Forecast", dict(filters, forecast_start_date=["is", "not set"]))
        
        missing_count = missing_company + missing_amount + missing_date
        completeness_score = max(0, 100 - (missing_count / total_records) * 100)
        
        return {
            "completeness_score": round(completeness_score, 1),
            "total_records": total_records,
            "missing_fields_count": missing_count,
            "missing_company": missing_company,
            "missing_amount": missing_amount,
            "missing_date": missing_date
        }
        
    except Exception as e:
        frappe.log_error(f"Error assessing data completeness: {str(e)}")
        return {"completeness_score": 0, "missing_fields_count": 0}

def assess_data_accuracy(company=None, assessment_days=90):
    """Assess data accuracy"""
    try:
        # Query for accuracy metrics
        query = """
            SELECT 
                predicted_amount,
                confidence_score,
                forecast_type
            FROM `tabAI Financial Forecast`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL %(assessment_days)s DAY)
            {}
        """.format("AND company = %(company)s" if company else "")
        
        records = frappe.db.sql(query, {
            "company": company, 
            "assessment_days": assessment_days
        }, as_dict=True)
        
        if not records:
            return {"accuracy_score": 0, "outliers_detected": 0}
        
        # Check for outliers and anomalies
        amounts = [float(r.predicted_amount) for r in records if r.predicted_amount]
        outliers_detected = 0
        
        if amounts:
            q1 = statistics.quantiles(amounts, n=4)[0]
            q3 = statistics.quantiles(amounts, n=4)[2]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers_detected = len([a for a in amounts if a < lower_bound or a > upper_bound])
        
        # Calculate accuracy score
        accuracy_score = max(0, 100 - (outliers_detected / len(records)) * 100)
        
        return {
            "accuracy_score": round(accuracy_score, 1),
            "total_records": len(records),
            "outliers_detected": outliers_detected,
            "mean_confidence": round(statistics.mean([r.confidence_score or 0 for r in records]), 1)
        }
        
    except Exception as e:
        frappe.log_error(f"Error assessing data accuracy: {str(e)}")
        return {"accuracy_score": 0, "outliers_detected": 0}

def assess_data_consistency(company=None, assessment_days=90):
    """Assess data consistency"""
    try:
        # Query for consistency checks
        query = """
            SELECT 
                company,
                forecast_type,
                predicted_amount,
                forecast_start_date
            FROM `tabAI Financial Forecast`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL %(assessment_days)s DAY)
            {}
        """.format("AND company = %(company)s" if company else "")
        
        records = frappe.db.sql(query, {
            "company": company, 
            "assessment_days": assessment_days
        }, as_dict=True)
        
        if not records:
            return {"consistency_score": 0, "total_issues": 0}
        
        total_issues = 0
        
        # Check for duplicate records
        seen_combinations = set()
        for record in records:
            key = (record.company, record.forecast_type, str(record.forecast_start_date))
            if key in seen_combinations:
                total_issues += 1
            seen_combinations.add(key)
        
        # Calculate consistency score
        consistency_score = max(0, 100 - (total_issues / len(records)) * 100)
        
        return {
            "consistency_score": round(consistency_score, 1),
            "total_records": len(records),
            "total_issues": total_issues
        }
        
    except Exception as e:
        frappe.log_error(f"Error assessing data consistency: {str(e)}")
        return {"consistency_score": 0, "total_issues": 0}

def assess_data_timeliness(company=None, assessment_days=90):
    """Assess data timeliness"""
    try:
        # Check last forecast creation date
        query = """
            SELECT 
                MAX(creation) as latest_creation,
                MAX(modified) as latest_modification,
                COUNT(*) as total_forecasts
            FROM `tabAI Financial Forecast`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL %(assessment_days)s DAY)
            {}
        """.format("AND company = %(company)s" if company else "")
        
        result = frappe.db.sql(query, {
            "company": company, 
            "assessment_days": assessment_days
        }, as_dict=True)[0]
        
        if not result.latest_creation:
            return {"freshness_score": 0, "days_since_last": "N/A"}
        
        # Calculate data freshness
        hours_since_last = frappe.utils.time_diff_in_hours(frappe.utils.now(), result.latest_creation)
        days_since_last = hours_since_last / 24
        
        # Freshness score based on recency
        if days_since_last <= 1:
            freshness_score = 100
        elif days_since_last <= 7:
            freshness_score = 80
        elif days_since_last <= 30:
            freshness_score = 60
        else:
            freshness_score = 40
        
        return {
            "freshness_score": round(freshness_score, 1),
            "days_since_last": round(days_since_last, 1),
            "latest_creation": result.latest_creation,
            "total_forecasts": result.total_forecasts
        }
        
    except Exception as e:
        frappe.log_error(f"Error assessing data timeliness: {str(e)}")
        return {"freshness_score": 0, "days_since_last": "N/A"}

def calculate_overall_quality_score(completeness_metrics, accuracy_metrics, consistency_metrics, timeliness_metrics):
    """Calculate overall quality score with weighted average"""
    try:
        # Define weights for each dimension
        weights = {
            "completeness": 0.3,
            "accuracy": 0.3,
            "consistency": 0.2,
            "timeliness": 0.2
        }
        
        # Extract scores
        completeness_score = completeness_metrics.get("completeness_score", 0)
        accuracy_score = accuracy_metrics.get("accuracy_score", 0)
        consistency_score = consistency_metrics.get("consistency_score", 0)
        timeliness_score = timeliness_metrics.get("freshness_score", 0)
        
        # Calculate weighted average
        overall_score = (
            completeness_score * weights["completeness"] +
            accuracy_score * weights["accuracy"] +
            consistency_score * weights["consistency"] +
            timeliness_score * weights["timeliness"]
        )
        
        return round(overall_score, 1)
        
    except Exception as e:
        frappe.log_error(f"Error calculating overall quality score: {str(e)}")
        return 0

def get_quality_grade(score):
    """Convert quality score to letter grade"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
