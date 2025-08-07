# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

class AIFinancialSettings(Document):
    def validate(self):
        """Validate financial settings"""
        if self.confidence_threshold and (self.confidence_threshold < 0 or self.confidence_threshold > 100):
            frappe.throw(_("Confidence threshold must be between 0 and 100"))
        
        if self.default_forecast_period and self.default_forecast_period < 1:
            frappe.throw(_("Default forecast period must be at least 1 day"))

@frappe.whitelist()
def generate_bulk_forecasts(scope="all_companies", settings=None):
    """Generate forecasts for all companies or specified scope"""
    try:
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        # Get all companies
        companies = frappe.get_all("Company", pluck="name")
        
        results = {
            "success": True,
            "total_created": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0,
            "avg_confidence": 0
        }
        
        total_confidence = 0
        
        for company in companies:
            try:
                # Generate forecasts for each company
                company_result = generate_company_forecasts(
                    company=company,
                    forecast_types=["Cash Flow", "Revenue", "Expense"],
                    forecast_period=settings.get("default_forecast_period", 90),
                    settings=settings
                )
                
                if company_result.get("success"):
                    results["successful"] += company_result.get("forecasts_created", 0)
                    total_confidence += company_result.get("avg_confidence", 0)
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                frappe.log_error(f"Bulk forecast failed for {company}: {str(e)}")
                results["failed"] += 1
        
        results["total_created"] = results["successful"] + results["failed"]
        results["success_rate"] = (results["successful"] / max(results["total_created"], 1)) * 100
        results["avg_confidence"] = total_confidence / max(len(companies), 1)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Bulk forecast generation failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def generate_company_forecasts(company, forecast_types=None, forecast_period=90, settings=None):
    """Generate forecasts for a specific company"""
    try:
        if isinstance(forecast_types, str):
            forecast_types = json.loads(forecast_types)
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        if not forecast_types:
            forecast_types = ["Cash Flow"]
        
        from ai_inventory.ai_accounts_forecast.api.forecast_api import api_create_forecast
        
        results = {
            "success": True,
            "forecasts_created": 0,
            "avg_confidence": 0,
            "status": "Completed",
            "details": []
        }
        
        # Get company accounts
        accounts = frappe.get_all("Account", 
            filters={"company": company, "is_group": 0},
            fields=["name", "account_type"],
            limit=20  # Limit for performance
        )
        
        total_confidence = 0
        
        for account in accounts:
            for forecast_type in forecast_types:
                try:
                    # Create forecast using the API
                    forecast_result = api_create_forecast(
                        company=company,
                        account=account.name,
                        forecast_type=forecast_type,
                        forecast_period_days=forecast_period,
                        confidence_threshold=settings.get("confidence_threshold", 70)
                    )
                    
                    if forecast_result.get("success"):
                        results["forecasts_created"] += 1
                        data = forecast_result.get("data", {})
                        total_confidence += data.get("confidence_score", 0) or forecast_result.get("confidence_score", 0)
                        results["details"].append(f"{forecast_type} forecast for {account.name}")
                    else:
                        # Log the specific error but continue processing
                        error_msg = forecast_result.get("error", "Unknown error")
                        if len(error_msg) > 100:
                            error_msg = error_msg[:100] + "..."
                        frappe.logger().error(f"Forecast failed for {account.name}: {error_msg}")
                        
                except Exception as e:
                    error_msg = str(e)
                    if len(error_msg) > 100:
                        error_msg = error_msg[:100] + "..."
                    frappe.logger().error(f"Company forecast exception for {company} - {account.name}: {error_msg}")
        
        results["avg_confidence"] = total_confidence / max(results["forecasts_created"], 1)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Company forecast generation failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def generate_account_type_forecasts(account_type, company=None, forecast_type="Cash Flow", forecast_period=90, settings=None):
    """Generate forecasts for specific account type"""
    try:
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        filters = {"account_type": account_type, "is_group": 0}
        if company:
            filters["company"] = company
        
        accounts = frappe.get_all("Account", 
            filters=filters,
            fields=["name", "company"],
            limit=50  # Limit for performance
        )
        
        from ai_inventory.ai_accounts_forecast.api.forecast_api import api_create_forecast
        
        results = {
            "success": True,
            "forecasts_created": 0,
            "avg_confidence": 0,
            "status": "Completed"
        }
        
        total_confidence = 0
        
        for account in accounts:
            try:
                forecast_result = api_create_forecast(
                    company=account.company,
                    account=account.name,
                    forecast_type=forecast_type,
                    forecast_period_days=forecast_period,
                    confidence_threshold=settings.get("confidence_threshold", 70)
                )
                
                if forecast_result.get("success"):
                    results["forecasts_created"] += 1
                    data = forecast_result.get("data", {})
                    total_confidence += data.get("confidence_score", 0) or forecast_result.get("confidence_score", 0)
                else:
                    error_msg = forecast_result.get("error", "Unknown error")
                    if len(error_msg) > 100:
                        error_msg = error_msg[:100] + "..."
                    frappe.logger().error(f"Account type forecast failed for {account.name}: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                frappe.logger().error(f"Account type forecast exception for {account.name}: {error_msg}")
        
        results["avg_confidence"] = total_confidence / max(results["forecasts_created"], 1)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Account type forecast generation failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def generate_quick_cash_flow(settings=None):
    """Generate quick cash flow forecasts for all companies"""
    try:
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        companies = frappe.get_all("Company", pluck="name")
        
        from ai_inventory.ai_accounts_forecast.api.forecast_api import api_create_forecast
        
        results = {
            "success": True,
            "forecasts_created": 0,
            "avg_confidence": 0,
            "status": "Completed"
        }
        
        total_confidence = 0
        
        for company in companies:
            # Get main cash/bank accounts
            cash_accounts = frappe.get_all("Account",
                filters={
                    "company": company,
                    "account_type": ["in", ["Cash", "Bank"]],
                    "is_group": 0
                },
                pluck="name",
                limit=5
            )
            
            for account in cash_accounts:
                try:
                    forecast_result = api_create_forecast(
                        company=company,
                        account=account,
                        forecast_type="Cash Flow",
                        forecast_period_days=30,  # Quick 30-day forecast
                        confidence_threshold=settings.get("confidence_threshold", 70)
                    )
                    
                    if forecast_result.get("success"):
                        results["forecasts_created"] += 1
                        total_confidence += forecast_result.get("confidence_score", 0)
                        
                except Exception as e:
                    frappe.log_error(f"Quick cash flow forecast failed for {account}: {str(e)}")
        
        results["avg_confidence"] = total_confidence / max(results["forecasts_created"], 1)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Quick cash flow generation failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def generate_revenue_forecasts(settings=None):
    """Generate revenue forecasts for all companies"""
    return generate_forecast_by_type("Revenue", settings)

@frappe.whitelist()
def generate_expense_forecasts(settings=None):
    """Generate expense forecasts for all companies"""
    return generate_forecast_by_type("Expense", settings)

def generate_forecast_by_type(forecast_type, settings=None):
    """Helper function to generate forecasts by type"""
    try:
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        companies = frappe.get_all("Company", pluck="name")
        
        from ai_inventory.ai_accounts_forecast.api.forecast_api import api_create_forecast
        
        results = {
            "success": True,
            "forecasts_created": 0,
            "avg_confidence": 0,
            "status": "Completed"
        }
        
        total_confidence = 0
        
        # Map forecast types to account types
        account_type_map = {
            "Revenue": ["Income"],
            "Expense": ["Expense"],
            "Cash Flow": ["Cash", "Bank"]
        }
        
        account_types = account_type_map.get(forecast_type, ["Asset"])
        
        for company in companies:
            accounts = frappe.get_all("Account",
                filters={
                    "company": company,
                    "account_type": ["in", account_types],
                    "is_group": 0
                },
                pluck="name",
                limit=10
            )
            
            for account in accounts:
                try:
                    forecast_result = api_create_forecast(
                        company=company,
                        account=account,
                        forecast_type=forecast_type,
                        forecast_period_days=settings.get("default_forecast_period", 90),
                        confidence_threshold=settings.get("confidence_threshold", 70)
                    )
                    
                    if forecast_result.get("success"):
                        results["forecasts_created"] += 1
                        total_confidence += forecast_result.get("confidence_score", 0)
                        
                except Exception as e:
                    frappe.log_error(f"{forecast_type} forecast failed for {account}: {str(e)}")
        
        results["avg_confidence"] = total_confidence / max(results["forecasts_created"], 1)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"{forecast_type} forecast generation failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def run_system_health_check():
    """Perform comprehensive system health check"""
    try:
        from ai_inventory.ai_accounts_forecast.api.forecast_api import get_system_health
        
        # Get overall system health
        health_data = get_system_health()
        
        # Ensure we have valid data structure
        if not health_data:
            health_data = {
                "status": "Unknown",
                "health_score": 0,
                "avg_confidence": 0,
                "high_confidence_ratio": 0,
                "forecast_types_active": 0
            }
        
        # Add additional metrics
        health_data.update({
            "total_forecasts": frappe.db.count("AI Financial Forecast"),
            "active_companies": frappe.db.count("Company"),
            "model_performance": "Good" if health_data.get("health_score", 0) >= 75 else "Needs Improvement",
            "data_quality": "Excellent" if health_data.get("avg_confidence", 0) >= 80 else "Good",
            "integration_status": "Active",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return health_data
        
    except Exception as e:
        frappe.log_error(f"System health check failed: {str(e)}")
        return {
            "status": "Error",
            "health_score": 0,
            "error": str(e),
            "avg_confidence": 0,
            "high_confidence_ratio": 0,
            "forecast_types_active": 0,
            "total_forecasts": 0,
            "active_companies": 0,
            "model_performance": "Unknown",
            "data_quality": "Unknown", 
            "integration_status": "Error",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

@frappe.whitelist()
def sync_all_forecasts():
    """Synchronize all existing forecasts"""
    try:
        forecasts = frappe.get_all("AI Financial Forecast", 
            filters={"docstatus": ["!=", 2]},
            fields=["name", "company", "account"]
        )
        
        results = {
            "success": True,
            "synced_count": 0,
            "updated_count": 0,
            "error_count": 0,
            "duration": "N/A"
        }
        
        start_time = datetime.now()
        
        for forecast in forecasts:
            try:
                # Refresh forecast data
                doc = frappe.get_doc("AI Financial Forecast", forecast.name)
                doc.save()
                
                results["synced_count"] += 1
                results["updated_count"] += 1
                
            except Exception as e:
                frappe.log_error(f"Sync failed for forecast {forecast.name}: {str(e)}")
                results["error_count"] += 1
        
        end_time = datetime.now()
        results["duration"] = str(end_time - start_time)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Sync all forecasts failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def cleanup_old_data(days_old=365, delete_details=True, delete_logs=True):
    """Cleanup old forecast data"""
    try:
        cutoff_date = (datetime.now() - timedelta(days=int(days_old))).date()
        
        results = {
            "success": True,
            "forecasts_cleaned": 0,
            "logs_cleaned": 0,
            "space_freed": "N/A"
        }
        
        if delete_details:
            # Archive old forecast details
            updated = frappe.db.sql("""
                UPDATE `tabAI Financial Forecast`
                SET forecast_details = 'Archived - details cleared for performance'
                WHERE creation < %s
                AND LENGTH(COALESCE(forecast_details, '')) > 1000
            """, (cutoff_date,))
            
            results["forecasts_cleaned"] = len(updated) if updated else 0
        
        if delete_logs:
            # Delete old log entries
            log_count = frappe.db.sql("""
                DELETE FROM `tabError Log`
                WHERE creation < %s
                AND error LIKE '%forecast%'
            """, (cutoff_date,))
            
            results["logs_cleaned"] = log_count[0][0] if log_count else 0
        
        frappe.db.commit()
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Data cleanup failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_model_performance_report():
    """Get model performance analysis"""
    try:
        # Get performance metrics from forecasts
        performance_data = frappe.db.sql("""
            SELECT 
                prediction_model,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) as usage_count,
                AVG(CASE WHEN confidence_score >= 80 THEN 1 ELSE 0 END) * 100 as high_confidence_rate
            FROM `tabAI Financial Forecast`
            WHERE docstatus != 2
            GROUP BY prediction_model
        """, as_dict=True)
        
        # Determine best performing model
        best_model = "ARIMA"  # Default
        best_score = 0
        
        model_stats = {}
        for row in performance_data:
            model = row.prediction_model
            score = row.avg_confidence
            model_stats[f"{model.lower()}_accuracy"] = f"{score:.1f}%"
            
            if score > best_score:
                best_score = score
                best_model = model
        
        # Determine most used model
        most_used = max(performance_data, key=lambda x: x.usage_count, default={})
        
        report = {
            "overall_accuracy": f"{sum(row.avg_confidence for row in performance_data) / len(performance_data):.1f}%" if performance_data else "N/A",
            "most_used_model": most_used.get("prediction_model", "N/A"),
            "best_performing": best_model,
            "recommendation": f"Consider using {best_model} for better accuracy"
        }
        
        report.update(model_stats)
        
        return report
        
    except Exception as e:
        frappe.log_error(f"Model performance report failed: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def export_system_report():
    """Export comprehensive system report"""
    try:
        from frappe.utils.response import build_response
        
        # Gather system data
        system_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_forecasts": frappe.db.count("AI Financial Forecast"),
            "active_companies": frappe.db.count("Company"),
            "system_health": get_system_status(),
            "model_performance": get_model_performance_report()
        }
        
        # Create CSV content
        csv_content = "Metric,Value\n"
        csv_content += f"Report Generated,{system_data['generated_at']}\n"
        csv_content += f"Total Forecasts,{system_data['total_forecasts']}\n"
        csv_content += f"Active Companies,{system_data['active_companies']}\n"
        
        # Build response for file download
        filename = f"ai_financial_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        response = build_response(csv_content, content_type='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        frappe.log_error(f"System report export failed: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def get_system_status():
    """Get current system status for dashboard"""
    try:
        # Get basic metrics
        total_forecasts = frappe.db.count("AI Financial Forecast")
        active_companies = frappe.db.count("Company")
        
        # Get average confidence
        avg_confidence_result = frappe.db.sql("""
            SELECT AVG(confidence_score) as avg_conf
            FROM `tabAI Financial Forecast`
            WHERE docstatus != 2
        """)
        
        avg_confidence = 0
        if avg_confidence_result and avg_confidence_result[0][0]:
            avg_confidence = float(avg_confidence_result[0][0])
        
        # Calculate system health (simplified)
        system_health = 0
        if total_forecasts > 0:
            system_health = min(100, (avg_confidence + 
                                    (100 if total_forecasts > 0 else 0) + 
                                    (100 if active_companies > 0 else 0)) / 3)
        
        return {
            "total_forecasts": total_forecasts,
            "active_companies": active_companies,
            "avg_confidence": round(avg_confidence, 1),
            "system_health": round(system_health, 1)
        }
        
    except Exception as e:
        frappe.log_error(f"System status check failed: {str(e)}")
        return {
            "total_forecasts": 0,
            "active_companies": 0,
            "avg_confidence": 0,
            "system_health": 0
        }

@frappe.whitelist()
def generate_accuracy_tracking():
    """Generate accuracy tracking for all forecasts that don't have tracking records"""
    try:
        # Get all AI Financial Forecasts without accuracy tracking
        forecasts_without_tracking = frappe.db.sql("""
            SELECT aff.name, aff.company, aff.forecast_type, aff.predicted_amount, 
                   aff.forecast_start_date, aff.prediction_model, aff.confidence_score
            FROM `tabAI Financial Forecast` aff
            LEFT JOIN `tabAI Forecast Accuracy` afa ON afa.forecast_reference = aff.name
            WHERE afa.name IS NULL
            ORDER BY aff.creation DESC
            LIMIT 100
        """, as_dict=True)
        
        from ai_inventory.forecasting.sync_manager import create_accuracy_tracking
        
        results = {
            "success": True,
            "tracking_created": 0,
            "errors": 0,
            "status": "Completed"
        }
        
        for forecast in forecasts_without_tracking:
            try:
                # Create a mock forecast document for the function
                forecast_doc = frappe._dict(forecast)
                result = create_accuracy_tracking(forecast_doc)
                
                if result.get("success"):
                    results["tracking_created"] += 1
                else:
                    results["errors"] += 1
                    
            except Exception as e:
                results["errors"] += 1
                frappe.log_error(f"Accuracy tracking generation error for {forecast.name}: {str(e)}")
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Generate accuracy tracking failed: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_accuracy_summary(company=None, days=30):
    """Get accuracy summary and performance metrics"""
    try:
        filters = {}
        if company:
            filters["company"] = company
        
        # Add date filter
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))
        filters["measurement_date"] = [">=", from_date]
        
        # Get accuracy records
        accuracy_records = frappe.get_all("AI Forecast Accuracy",
                                        filters=filters,
                                        fields=["name", "forecast_type", "accuracy_percentage", 
                                               "performance_grade", "model_used", "predicted_value",
                                               "actual_value", "absolute_error"],
                                        order_by="measurement_date desc")
        
        summary = {
            "total_accuracy_records": len(accuracy_records),
            "avg_accuracy": 0,
            "accuracy_by_type": {},
            "accuracy_by_model": {},
            "performance_distribution": {
                "A+": 0, "A": 0, "B+": 0, "B": 0, "C+": 0, "C": 0, "D": 0, "F": 0
            },
            "top_performing_models": [],
            "improvement_areas": []
        }
        
        if accuracy_records:
            # Calculate average accuracy
            total_accuracy = sum(r.accuracy_percentage or 0 for r in accuracy_records)
            summary["avg_accuracy"] = total_accuracy / len(accuracy_records)
            
            # Accuracy by forecast type
            for record in accuracy_records:
                ftype = record.forecast_type
                if ftype not in summary["accuracy_by_type"]:
                    summary["accuracy_by_type"][ftype] = {"count": 0, "total_accuracy": 0}
                
                summary["accuracy_by_type"][ftype]["count"] += 1
                summary["accuracy_by_type"][ftype]["total_accuracy"] += (record.accuracy_percentage or 0)
            
            # Calculate averages for each type
            for ftype in summary["accuracy_by_type"]:
                data = summary["accuracy_by_type"][ftype]
                data["avg_accuracy"] = data["total_accuracy"] / data["count"]
            
            # Accuracy by model
            for record in accuracy_records:
                model = record.model_used or "Unknown"
                if model not in summary["accuracy_by_model"]:
                    summary["accuracy_by_model"][model] = {"count": 0, "total_accuracy": 0}
                
                summary["accuracy_by_model"][model]["count"] += 1
                summary["accuracy_by_model"][model]["total_accuracy"] += (record.accuracy_percentage or 0)
            
            # Calculate averages for each model
            for model in summary["accuracy_by_model"]:
                data = summary["accuracy_by_model"][model]
                data["avg_accuracy"] = data["total_accuracy"] / data["count"]
            
            # Performance grade distribution
            for record in accuracy_records:
                grade = record.performance_grade or "F"
                if grade in summary["performance_distribution"]:
                    summary["performance_distribution"][grade] += 1
            
            # Top performing models
            model_performance = []
            for model, data in summary["accuracy_by_model"].items():
                model_performance.append({
                    "model": model,
                    "avg_accuracy": data["avg_accuracy"],
                    "count": data["count"]
                })
            
            summary["top_performing_models"] = sorted(
                model_performance, 
                key=lambda x: x["avg_accuracy"], 
                reverse=True
            )[:5]
            
            # Identify improvement areas
            if summary["avg_accuracy"] < 70:
                summary["improvement_areas"].append("Overall accuracy below 70% - consider model optimization")
            
            worst_type = min(summary["accuracy_by_type"].items(), 
                           key=lambda x: x[1]["avg_accuracy"]) if summary["accuracy_by_type"] else None
            if worst_type and worst_type[1]["avg_accuracy"] < 60:
                summary["improvement_areas"].append(f"{worst_type[0]} forecasts need improvement (avg: {worst_type[1]['avg_accuracy']:.1f}%)")
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Get accuracy summary failed: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def update_accuracy_with_actuals(forecast_reference, actual_value):
    """Update accuracy record with actual values and recalculate metrics"""
    try:
        # Find the accuracy record
        accuracy_record = frappe.get_all("AI Forecast Accuracy",
                                       filters={"forecast_reference": forecast_reference},
                                       limit=1)
        
        if not accuracy_record:
            return {"success": False, "error": "No accuracy record found for this forecast"}
        
        # Get the accuracy document
        accuracy_doc = frappe.get_doc("AI Forecast Accuracy", accuracy_record[0].name)
        
        # Update actual value
        accuracy_doc.actual_value = float(actual_value)
        
        # Calculate accuracy metrics
        predicted = accuracy_doc.predicted_value or 0
        actual = float(actual_value)
        
        if actual != 0:
            # Calculate percentage error
            percentage_error = abs((predicted - actual) / actual) * 100
            accuracy_doc.percentage_error = percentage_error
            
            # Calculate accuracy percentage (100 - percentage_error, capped at 0)
            accuracy_doc.accuracy_percentage = max(0, 100 - percentage_error)
        else:
            accuracy_doc.percentage_error = 100 if predicted != 0 else 0
            accuracy_doc.accuracy_percentage = 0 if predicted != 0 else 100
        
        # Calculate absolute error
        accuracy_doc.absolute_error = abs(predicted - actual)
        
        # Calculate squared error
        accuracy_doc.squared_error = (predicted - actual) ** 2
        
        # Determine performance grade
        accuracy_pct = accuracy_doc.accuracy_percentage
        if accuracy_pct >= 95:
            accuracy_doc.performance_grade = "A+"
        elif accuracy_pct >= 90:
            accuracy_doc.performance_grade = "A"
        elif accuracy_pct >= 85:
            accuracy_doc.performance_grade = "B+"
        elif accuracy_pct >= 80:
            accuracy_doc.performance_grade = "B"
        elif accuracy_pct >= 75:
            accuracy_doc.performance_grade = "C+"
        elif accuracy_pct >= 70:
            accuracy_doc.performance_grade = "C"
        elif accuracy_pct >= 60:
            accuracy_doc.performance_grade = "D"
        else:
            accuracy_doc.performance_grade = "F"
        
        # Generate improvement suggestions
        suggestions = []
        if accuracy_pct < 70:
            suggestions.append("Consider using different prediction model")
            suggestions.append("Increase historical data for training")
            suggestions.append("Review external factors affecting forecasts")
        elif accuracy_pct < 85:
            suggestions.append("Fine-tune model parameters")
            suggestions.append("Consider seasonal adjustments")
        else:
            suggestions.append("Maintain current model configuration")
        
        accuracy_doc.improvement_suggestions = "\n".join(suggestions)
        
        # Save the document
        accuracy_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "accuracy_percentage": accuracy_doc.accuracy_percentage,
            "performance_grade": accuracy_doc.performance_grade,
            "absolute_error": accuracy_doc.absolute_error
        }
        
    except Exception as e:
        frappe.log_error(f"Update accuracy with actuals failed: {str(e)}")
        return {"success": False, "error": str(e)}
