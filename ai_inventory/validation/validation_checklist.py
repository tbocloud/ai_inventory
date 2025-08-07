"""
AI Financial Forecast Validation Checklist Implementation
Based on the validation checklist for AI-FIN-FCST-01319

This script implements all the validation points from your comprehensive checklist:
1. Data Accuracy Validation
2. System Health Indicators  
3. Model Performance Validation
4. Integration & Sync Validation
5. Critical Issues Check
6. Automated Monitoring
"""

import frappe
import json
from datetime import datetime, timedelta

class ValidationChecklistImplementation:
    """Implementation of the comprehensive validation checklist"""
    
    def __init__(self, forecast_id=None):
        self.forecast_id = forecast_id
        self.checklist_results = {}
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
    
    def run_complete_validation_checklist(self):
        """Run the complete validation checklist"""
        
        print("🔍 VALIDATION CHECKLIST FOR AI FINANCIAL FORECASTS")
        print("=" * 60)
        print("Based on AI-FIN-FCST-01319 validation requirements")
        print()
        
        # Section 1: Data Accuracy Validation
        self.validate_data_accuracy()
        
        # Section 2: System Health Indicators
        self.validate_system_health_indicators()
        
        # Section 3: Model Performance Validation
        self.validate_model_performance()
        
        # Section 4: Integration & Sync Validation
        self.validate_integration_sync()
        
        # Section 5: Critical Issues Check
        self.check_critical_issues()
        
        # Section 6: Generate Weekly Validation Routine
        self.setup_weekly_validation_routine()
        
        # Section 7: Red Flags Monitoring
        self.monitor_red_flags()
        
        # Section 8: Generate Success Metrics
        self.generate_success_metrics()
        
        return self.generate_checklist_report()
    
    def validate_data_accuracy(self):
        """Section 1: Data Accuracy Validation 🔍"""
        
        print("1️⃣ DATA ACCURACY VALIDATION 🔍")
        print("-" * 40)
        
        results = {
            "current_balance_verification": self.check_current_balance_verification(),
            "forecast_accuracy_check": self.check_forecast_accuracy_bounds(),
            "data_completeness": self.check_data_completeness(),
            "temporal_consistency": self.check_temporal_consistency()
        }
        
        self.checklist_results["data_accuracy"] = results
        
        # Print results
        for check, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"   {status_icon} {check.replace('_', ' ').title()}: {result['message']}")
        
        print()
    
    def check_current_balance_verification(self):
        """Current Balance Verification"""
        
        if not self.forecast_id:
            return {"status": "SKIP", "message": "No specific forecast to check"}
        
        try:
            forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
            
            # Get actual account balance
            if forecast.account:
                actual_balance = frappe.db.get_value("Account", forecast.account, "account_balance") or 0
                forecast_balance = getattr(forecast, 'current_balance', forecast.predicted_amount)
                
                if forecast_balance:
                    difference = abs(actual_balance - forecast_balance)
                    tolerance = 1.0  # ₹1 tolerance as per checklist
                    
                    if difference <= tolerance:
                        return {"status": "PASS", "message": f"Balance accurate (₹{difference:.2f} diff)", "difference": difference}
                    else:
                        self.critical_issues.append(f"Balance variance: ₹{difference:,.2f} (exceeds ₹{tolerance} tolerance)")
                        return {"status": "FAIL", "message": f"Balance variance: ₹{difference:,.2f}", "difference": difference}
                
            return {"status": "SKIP", "message": "No balance data to verify"}
            
        except Exception as e:
            return {"status": "ERROR", "message": f"Balance check failed: {str(e)}"}
    
    def check_forecast_accuracy_bounds(self):
        """Forecast Accuracy Check - The Critical Issue"""
        
        if not self.forecast_id:
            # Check all forecasts for bounds issues
            try:
                bounds_issues = frappe.db.sql("""
                    SELECT name, upper_bound, lower_bound
                    FROM `tabAI Financial Forecast`
                    WHERE upper_bound IS NOT NULL 
                    AND lower_bound IS NOT NULL
                    AND upper_bound <= lower_bound
                """, as_dict=True)
                
                if bounds_issues:
                    self.critical_issues.append(f"Found {len(bounds_issues)} forecasts with bounds logic errors")
                    return {"status": "FAIL", "message": f"{len(bounds_issues)} forecasts have bounds errors", "count": len(bounds_issues)}
                else:
                    return {"status": "PASS", "message": "All forecast bounds are logically correct"}
                    
            except Exception as e:
                return {"status": "ERROR", "message": f"Bounds check failed: {str(e)}"}
        
        try:
            forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
            
            if forecast.upper_bound and forecast.lower_bound:
                if forecast.upper_bound <= forecast.lower_bound:
                    error_msg = f"Upper bound (₹{forecast.upper_bound:,.2f}) ≤ Lower bound (₹{forecast.lower_bound:,.2f})"
                    self.critical_issues.append(f"CRITICAL BOUNDS ERROR: {error_msg}")
                    return {"status": "FAIL", "message": error_msg, "upper": forecast.upper_bound, "lower": forecast.lower_bound}
                else:
                    return {"status": "PASS", "message": f"Bounds correct: ₹{forecast.lower_bound:,.2f} < ₹{forecast.upper_bound:,.2f}"}
            else:
                return {"status": "SKIP", "message": "No bounds set"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Bounds check failed: {str(e)}"}
    
    def check_data_completeness(self):
        """Data Completeness Check"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                required_fields = ['company', 'account', 'forecast_type', 'predicted_amount', 'confidence_score']
                missing_fields = [field for field in required_fields if not getattr(forecast, field, None)]
                
                completeness = ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100
                
                if completeness == 100:
                    return {"status": "PASS", "message": f"Complete data ({completeness}%)", "completeness": completeness}
                elif completeness >= 80:
                    return {"status": "WARN", "message": f"Mostly complete ({completeness}%)", "completeness": completeness, "missing": missing_fields}
                else:
                    self.critical_issues.append(f"Data incomplete: missing {missing_fields}")
                    return {"status": "FAIL", "message": f"Incomplete data ({completeness}%)", "completeness": completeness, "missing": missing_fields}
            else:
                # Check overall data completeness across all forecasts
                total_forecasts = frappe.db.count("AI Financial Forecast")
                forecasts_with_key_data = frappe.db.sql("""
                    SELECT COUNT(*) as count 
                    FROM `tabAI Financial Forecast`
                    WHERE company IS NOT NULL 
                    AND account IS NOT NULL 
                    AND predicted_amount IS NOT NULL
                    AND confidence_score IS NOT NULL
                """)[0][0]
                
                if total_forecasts > 0:
                    completeness = (forecasts_with_key_data / total_forecasts) * 100
                    return {"status": "PASS" if completeness >= 90 else "WARN", "message": f"Overall completeness: {completeness:.1f}%", "completeness": completeness}
                else:
                    return {"status": "SKIP", "message": "No forecasts to check"}
                    
        except Exception as e:
            return {"status": "ERROR", "message": f"Completeness check failed: {str(e)}"}
    
    def check_temporal_consistency(self):
        """Check temporal consistency of forecasts"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                issues = []
                
                # Check date logic
                if forecast.forecast_start_date and forecast.forecast_end_date:
                    if frappe.utils.getdate(forecast.forecast_end_date) <= frappe.utils.getdate(forecast.forecast_start_date):
                        issues.append("End date not after start date")
                
                # Check if forecast is too old
                if forecast.creation:
                    days_old = (frappe.utils.now_datetime() - frappe.utils.get_datetime(forecast.creation)).days
                    if days_old > 30:
                        issues.append(f"Forecast is {days_old} days old")
                
                if issues:
                    return {"status": "WARN", "message": f"Temporal issues: {'; '.join(issues)}", "issues": issues}
                else:
                    return {"status": "PASS", "message": "Temporal consistency good"}
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Temporal check failed: {str(e)}"}
    
    def validate_system_health_indicators(self):
        """Section 2: System Health Indicators 🏥"""
        
        print("2️⃣ SYSTEM HEALTH INDICATORS 🏥")
        print("-" * 40)
        
        results = {
            "data_quality_score": self.check_data_quality_score(),
            "volatility_assessment": self.check_volatility_score(),
            "risk_category_validation": self.check_risk_category(),
            "performance_metrics": self.check_performance_metrics()
        }
        
        self.checklist_results["system_health"] = results
        
        for check, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"   {status_icon} {check.replace('_', ' ').title()}: {result['message']}")
        
        print()
    
    def check_data_quality_score(self):
        """Data Quality Score Check - Target >80%"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                quality_score = getattr(forecast, 'data_quality_score', None)
                
                if quality_score is None:
                    return {"status": "WARN", "message": "No data quality score available"}
                
                if quality_score >= 80:
                    return {"status": "PASS", "message": f"Excellent quality ({quality_score}%)", "score": quality_score}
                elif quality_score >= 67.5:  # Your current score from checklist
                    self.warnings.append(f"Data quality below target: {quality_score}% (Target: 80%+)")
                    return {"status": "WARN", "message": f"Below target ({quality_score}%)", "score": quality_score}
                else:
                    self.critical_issues.append(f"Data quality critically low: {quality_score}%")
                    return {"status": "FAIL", "message": f"Critical quality ({quality_score}%)", "score": quality_score}
            else:
                # Calculate average data quality across all forecasts
                avg_quality = frappe.db.sql("""
                    SELECT AVG(data_quality_score) as avg_score
                    FROM `tabAI Financial Forecast`
                    WHERE data_quality_score IS NOT NULL
                """)[0][0]
                
                if avg_quality:
                    return {"status": "PASS" if avg_quality >= 80 else "WARN", "message": f"Average quality: {avg_quality:.1f}%", "score": avg_quality}
                else:
                    return {"status": "SKIP", "message": "No quality scores available"}
                    
        except Exception as e:
            return {"status": "ERROR", "message": f"Quality check failed: {str(e)}"}
    
    def check_volatility_score(self):
        """Volatility Score Assessment - Your current: 30%"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                volatility = getattr(forecast, 'volatility_score', None)
                
                if volatility is None:
                    return {"status": "SKIP", "message": "No volatility score"}
                
                # Based on your checklist: 30% is considered good (low volatility)
                if volatility <= 30:
                    return {"status": "PASS", "message": f"Low volatility ({volatility}%) - Good predictability", "score": volatility}
                elif volatility <= 50:
                    return {"status": "WARN", "message": f"Moderate volatility ({volatility}%)", "score": volatility}
                else:
                    self.warnings.append(f"High volatility detected: {volatility}%")
                    return {"status": "WARN", "message": f"High volatility ({volatility}%)", "score": volatility}
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Volatility check failed: {str(e)}"}
    
    def check_risk_category(self):
        """Risk Category Validation - Your current: Low"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                risk_category = getattr(forecast, 'risk_category', 'Unknown')
                
                # Based on your checklist: "Low" is good
                if risk_category == "Low":
                    return {"status": "PASS", "message": f"Risk category: {risk_category} ✅", "category": risk_category}
                elif risk_category == "Medium":
                    return {"status": "WARN", "message": f"Risk category: {risk_category}", "category": risk_category}
                elif risk_category in ["High", "Critical"]:
                    self.warnings.append(f"High risk category: {risk_category}")
                    return {"status": "WARN", "message": f"Risk category: {risk_category} ⚠️", "category": risk_category}
                else:
                    return {"status": "SKIP", "message": f"Risk category: {risk_category}"}
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Risk check failed: {str(e)}"}
    
    def check_performance_metrics(self):
        """Overall Performance Metrics Check"""
        
        try:
            # Get system-wide performance metrics
            metrics = frappe.db.sql("""
                SELECT 
                    COUNT(*) as total_forecasts,
                    AVG(confidence_score) as avg_confidence,
                    AVG(data_quality_score) as avg_quality,
                    COUNT(CASE WHEN forecast_alert = 1 THEN 1 END) as alert_count
                FROM `tabAI Financial Forecast`
                WHERE confidence_score IS NOT NULL
            """, as_dict=True)[0]
            
            issues = []
            
            if metrics.avg_confidence and metrics.avg_confidence < 70:
                issues.append(f"Low average confidence: {metrics.avg_confidence:.1f}%")
            
            if metrics.alert_count and metrics.total_forecasts:
                alert_rate = (metrics.alert_count / metrics.total_forecasts) * 100
                if alert_rate > 20:  # More than 20% of forecasts have alerts
                    issues.append(f"High alert rate: {alert_rate:.1f}%")
            
            if issues:
                return {"status": "WARN", "message": f"Performance issues: {'; '.join(issues)}", "metrics": metrics}
            else:
                return {"status": "PASS", "message": f"Good performance ({metrics.total_forecasts} forecasts)", "metrics": metrics}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Performance check failed: {str(e)}"}
    
    def validate_model_performance(self):
        """Section 3: Model Performance Validation 📊"""
        
        print("3️⃣ MODEL PERFORMANCE VALIDATION 📊")
        print("-" * 40)
        
        results = {
            "confidence_score_check": self.check_confidence_score_thresholds(),
            "prediction_model_assessment": self.check_prediction_model_suitability(),
            "accuracy_tracking": self.check_accuracy_tracking(),
            "model_consistency": self.check_model_consistency()
        }
        
        self.checklist_results["model_performance"] = results
        
        for check, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"   {status_icon} {check.replace('_', ' ').title()}: {result['message']}")
        
        print()
    
    def check_confidence_score_thresholds(self):
        """Confidence Score Check - Your current: 81%"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                confidence = forecast.confidence_score
                threshold = getattr(forecast, 'confidence_threshold', 70)
                
                if confidence is None:
                    return {"status": "FAIL", "message": "No confidence score"}
                
                # Based on your checklist: 81% is good (above 80% threshold)
                if confidence >= 80:
                    return {"status": "PASS", "message": f"High confidence ({confidence}%) ✅", "score": confidence}
                elif confidence >= threshold:
                    return {"status": "PASS", "message": f"Acceptable confidence ({confidence}%)", "score": confidence}
                elif confidence >= 60:
                    self.warnings.append(f"Confidence below threshold: {confidence}%")
                    return {"status": "WARN", "message": f"Low confidence ({confidence}%)", "score": confidence}
                else:
                    self.critical_issues.append(f"Confidence critically low: {confidence}%")
                    return {"status": "FAIL", "message": f"Critical confidence ({confidence}%)", "score": confidence}
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Confidence check failed: {str(e)}"}
    
    def check_prediction_model_suitability(self):
        """Prediction Model Assessment - Your current: Linear Regression"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                model = getattr(forecast, 'prediction_model', 'Unknown')
                
                # Based on your checklist feedback about Linear Regression
                model_assessments = {
                    "Linear Regression": {
                        "status": "WARN",
                        "message": "Linear Regression - Good for stable trends, consider ARIMA for seasonality",
                        "recommendation": "Evaluate if seasonality/trends need advanced models"
                    },
                    "ARIMA": {
                        "status": "PASS", 
                        "message": "ARIMA - Excellent for financial time series",
                        "recommendation": "Good choice for financial forecasting"
                    },
                    "LSTM": {
                        "status": "PASS",
                        "message": "LSTM - Advanced model for complex patterns",
                        "recommendation": "Suitable for complex financial patterns"
                    }
                }
                
                assessment = model_assessments.get(model, {
                    "status": "WARN",
                    "message": f"Unknown model: {model}",
                    "recommendation": "Verify model suitability"
                })
                
                return {
                    "status": assessment["status"],
                    "message": assessment["message"],
                    "model": model,
                    "recommendation": assessment["recommendation"]
                }
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Model check failed: {str(e)}"}
    
    def check_accuracy_tracking(self):
        """Accuracy Tracking Check"""
        
        try:
            if self.forecast_id:
                # Check if accuracy tracking exists for this forecast
                accuracy_records = frappe.get_all("AI Forecast Accuracy",
                                                filters={"forecast_reference": self.forecast_id},
                                                limit=1)
                
                if accuracy_records:
                    return {"status": "PASS", "message": "Accuracy tracking enabled", "tracking": True}
                else:
                    self.recommendations.append("Enable accuracy tracking for forecast performance monitoring")
                    return {"status": "WARN", "message": "No accuracy tracking", "tracking": False}
            else:
                # Check overall accuracy tracking
                total_forecasts = frappe.db.count("AI Financial Forecast")
                tracked_forecasts = frappe.db.count("AI Forecast Accuracy")
                
                if total_forecasts > 0:
                    tracking_rate = (tracked_forecasts / total_forecasts) * 100
                    return {"status": "PASS" if tracking_rate >= 50 else "WARN", "message": f"Tracking rate: {tracking_rate:.1f}%", "rate": tracking_rate}
                else:
                    return {"status": "SKIP", "message": "No forecasts to track"}
                    
        except Exception as e:
            return {"status": "ERROR", "message": f"Accuracy tracking check failed: {str(e)}"}
    
    def check_model_consistency(self):
        """Model Consistency Check"""
        
        try:
            # Check if predictions are consistent over time
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Look for similar forecasts to compare
                similar_forecasts = frappe.get_all("AI Financial Forecast",
                                                 filters={
                                                     "account": forecast.account,
                                                     "forecast_type": forecast.forecast_type,
                                                     "name": ["!=", forecast.name]
                                                 },
                                                 fields=["predicted_amount", "confidence_score"],
                                                 order_by="creation desc",
                                                 limit=3)
                
                if similar_forecasts and forecast.predicted_amount:
                    # Check variance in predictions
                    predictions = [f.predicted_amount for f in similar_forecasts if f.predicted_amount]
                    if predictions:
                        avg_prediction = sum(predictions) / len(predictions)
                        variance = abs(forecast.predicted_amount - avg_prediction) / avg_prediction * 100
                        
                        if variance <= 20:
                            return {"status": "PASS", "message": f"Consistent predictions ({variance:.1f}% variance)", "variance": variance}
                        else:
                            return {"status": "WARN", "message": f"High prediction variance ({variance:.1f}%)", "variance": variance}
                    
                return {"status": "SKIP", "message": "Insufficient data for consistency check"}
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Consistency check failed: {str(e)}"}
    
    def validate_integration_sync(self):
        """Section 4: Integration & Sync Validation 🔄"""
        
        print("4️⃣ INTEGRATION & SYNC VALIDATION 🔄")
        print("-" * 40)
        
        results = {
            "auto_sync_status": self.check_auto_sync_status(),
            "sync_frequency_check": self.check_sync_frequency(),
            "last_sync_verification": self.check_last_sync(),
            "inventory_integration": self.check_inventory_integration()
        }
        
        self.checklist_results["integration_sync"] = results
        
        for check, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"   {status_icon} {check.replace('_', ' ').title()}: {result['message']}")
        
        print()
    
    def check_auto_sync_status(self):
        """Auto Sync Status Check - Your checklist shows: Enabled ✅"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                auto_sync = getattr(forecast, 'inventory_sync_enabled', False)
                
                if auto_sync:
                    return {"status": "PASS", "message": "Auto sync enabled ✅", "enabled": True}
                else:
                    return {"status": "WARN", "message": "Auto sync disabled", "enabled": False}
            else:
                # Check overall sync status
                total_forecasts = frappe.db.count("AI Financial Forecast")
                sync_enabled = frappe.db.count("AI Financial Forecast", {"inventory_sync_enabled": 1})
                
                if total_forecasts > 0:
                    sync_rate = (sync_enabled / total_forecasts) * 100
                    return {"status": "PASS" if sync_rate >= 80 else "WARN", "message": f"Sync enabled: {sync_rate:.1f}%", "rate": sync_rate}
                else:
                    return {"status": "SKIP", "message": "No forecasts to check"}
                    
        except Exception as e:
            return {"status": "ERROR", "message": f"Sync status check failed: {str(e)}"}
    
    def check_sync_frequency(self):
        """Sync Frequency Check - Your checklist shows: Daily ✅"""
        
        try:
            # Check if daily sync is configured and running
            # This would typically be in scheduler events or settings
            
            # For now, check if syncs are happening regularly
            recent_syncs = frappe.get_all("AI Forecast Sync Log",
                                        filters={
                                            "sync_time": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
                                        },
                                        fields=["sync_time"],
                                        order_by="sync_time desc")
            
            if len(recent_syncs) >= 5:  # At least 5 syncs in past week for daily frequency
                return {"status": "PASS", "message": f"Regular syncing ({len(recent_syncs)} syncs this week)", "frequency": "Good"}
            elif len(recent_syncs) >= 1:
                return {"status": "WARN", "message": f"Infrequent syncing ({len(recent_syncs)} syncs this week)", "frequency": "Low"}
            else:
                self.critical_issues.append("No recent sync activity detected")
                return {"status": "FAIL", "message": "No recent sync activity", "frequency": "None"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Sync frequency check failed: {str(e)}"}
    
    def check_last_sync(self):
        """Last Sync Verification - Your checklist shows: 06-08-2023 00:00:00"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                last_sync = getattr(forecast, 'last_sync_date', None)
                
                if last_sync:
                    last_sync_date = frappe.utils.get_datetime(last_sync)
                    hours_since_sync = (frappe.utils.now_datetime() - last_sync_date).total_seconds() / 3600
                    
                    if hours_since_sync <= 25:  # Within last day for daily sync
                        return {"status": "PASS", "message": f"Recent sync ({hours_since_sync:.1f}h ago)", "hours_ago": hours_since_sync}
                    elif hours_since_sync <= 48:
                        return {"status": "WARN", "message": f"Sync outdated ({hours_since_sync:.1f}h ago)", "hours_ago": hours_since_sync}
                    else:
                        self.warnings.append(f"Last sync very outdated: {hours_since_sync:.1f} hours ago")
                        return {"status": "FAIL", "message": f"Sync very outdated ({hours_since_sync:.1f}h ago)", "hours_ago": hours_since_sync}
                else:
                    return {"status": "WARN", "message": "No sync date recorded", "synced": False}
            else:
                return {"status": "SKIP", "message": "No specific forecast to check"}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Last sync check failed: {str(e)}"}
    
    def check_inventory_integration(self):
        """Inventory Integration Check - Your checklist shows: Enabled ✅"""
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Check if inventory integration is relevant for this company
                inventory_forecasts = frappe.db.count("AI Inventory Forecast", {"company": forecast.company})
                
                if inventory_forecasts > 0:
                    return {"status": "PASS", "message": f"Inventory integration active ({inventory_forecasts} forecasts)", "forecasts": inventory_forecasts}
                else:
                    return {"status": "WARN", "message": "No inventory forecasts found", "forecasts": 0}
            else:
                # Check overall inventory integration
                financial_companies = set(frappe.db.sql_list("SELECT DISTINCT company FROM `tabAI Financial Forecast`"))
                inventory_companies = set(frappe.db.sql_list("SELECT DISTINCT company FROM `tabAI Inventory Forecast`"))
                
                integration_rate = len(financial_companies.intersection(inventory_companies)) / len(financial_companies) * 100 if financial_companies else 0
                
                return {"status": "PASS" if integration_rate >= 80 else "WARN", "message": f"Integration rate: {integration_rate:.1f}%", "rate": integration_rate}
                
        except Exception as e:
            return {"status": "ERROR", "message": f"Integration check failed: {str(e)}"}
    
    def check_critical_issues(self):
        """Section 5: Critical Issues Check ⚠️"""
        
        print("5️⃣ CRITICAL ISSUES CHECK ⚠️")
        print("-" * 40)
        
        # Critical issues are collected throughout the validation process
        critical_issues_found = len(self.critical_issues)
        
        if critical_issues_found == 0:
            print("   ✅ No critical issues found")
            self.checklist_results["critical_issues"] = {"status": "PASS", "count": 0, "issues": []}
        else:
            print(f"   🚨 {critical_issues_found} critical issues found:")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"      {i}. {issue}")
            self.checklist_results["critical_issues"] = {"status": "FAIL", "count": critical_issues_found, "issues": self.critical_issues}
        
        print()
    
    def setup_weekly_validation_routine(self):
        """Section 6: Weekly Validation Routine 📅"""
        
        print("6️⃣ WEEKLY VALIDATION ROUTINE SETUP 📅")
        print("-" * 40)
        
        routine_tasks = {
            "Monday": "Data Sync Check",
            "Wednesday": "Accuracy Review", 
            "Friday": "Weekly Performance Report"
        }
        
        for day, task in routine_tasks.items():
            print(f"   📅 {day}: {task}")
        
        self.recommendations.append("Implement automated weekly validation routine")
        self.checklist_results["weekly_routine"] = {"status": "PLANNED", "tasks": routine_tasks}
        
        print()
    
    def monitor_red_flags(self):
        """Section 7: Red Flags Monitoring 🚩"""
        
        print("7️⃣ RED FLAGS MONITORING 🚩")
        print("-" * 40)
        
        red_flags = []
        
        # Check for red flag conditions based on your checklist
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Red Flag 1: Confidence Score Drops Below 70%
                if forecast.confidence_score and forecast.confidence_score < 70:
                    red_flags.append(f"Confidence below 70%: {forecast.confidence_score}%")
                
                # Red Flag 2: Data Quality Score Below 60%
                quality_score = getattr(forecast, 'data_quality_score', None)
                if quality_score and quality_score < 60:
                    red_flags.append(f"Data quality below 60%: {quality_score}%")
                
                # Red Flag 3: Bounds Logic Errors
                if forecast.upper_bound and forecast.lower_bound and forecast.upper_bound <= forecast.lower_bound:
                    red_flags.append("Upper/Lower bound logic error")
                
                # Red Flag 4: Very old last sync
                last_sync = getattr(forecast, 'last_sync_date', None)
                if last_sync:
                    days_since_sync = (frappe.utils.now_datetime() - frappe.utils.get_datetime(last_sync)).days
                    if days_since_sync >= 2:
                        red_flags.append(f"Sync failures for {days_since_sync} days")
        
        except Exception as e:
            red_flags.append(f"Error checking red flags: {str(e)}")
        
        if red_flags:
            print(f"   🚩 {len(red_flags)} red flags detected:")
            for flag in red_flags:
                print(f"      • {flag}")
        else:
            print("   ✅ No red flags detected")
        
        self.checklist_results["red_flags"] = {"count": len(red_flags), "flags": red_flags}
        
        print()
    
    def generate_success_metrics(self):
        """Section 8: Success Metrics Dashboard"""
        
        print("8️⃣ SUCCESS METRICS DASHBOARD 📊")
        print("-" * 40)
        
        try:
            metrics = {
                "total_forecasts": frappe.db.count("AI Financial Forecast"),
                "avg_confidence": frappe.db.sql("SELECT AVG(confidence_score) FROM `tabAI Financial Forecast` WHERE confidence_score IS NOT NULL")[0][0] or 0,
                "avg_data_quality": frappe.db.sql("SELECT AVG(data_quality_score) FROM `tabAI Financial Forecast` WHERE data_quality_score IS NOT NULL")[0][0] or 0,
                "bounds_errors": frappe.db.count("AI Financial Forecast", "upper_bound <= lower_bound"),
                "recent_syncs": frappe.db.count("AI Forecast Sync Log", {"sync_time": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]}),
                "forecasts_with_alerts": frappe.db.count("AI Financial Forecast", {"forecast_alert": 1})
            }
            
            print(f"   📊 Total Forecasts: {metrics['total_forecasts']}")
            print(f"   🎯 Average Confidence: {metrics['avg_confidence']:.1f}%")
            print(f"   📈 Average Data Quality: {metrics['avg_data_quality']:.1f}%")
            print(f"   🚨 Bounds Errors: {metrics['bounds_errors']}")
            print(f"   🔄 Recent Syncs (7 days): {metrics['recent_syncs']}")
            print(f"   ⚠️ Active Alerts: {metrics['forecasts_with_alerts']}")
            
            self.checklist_results["success_metrics"] = metrics
            
        except Exception as e:
            print(f"   ❌ Error generating metrics: {str(e)}")
            self.checklist_results["success_metrics"] = {"error": str(e)}
        
        print()
    
    def generate_checklist_report(self):
        """Generate comprehensive checklist report"""
        
        print("📋 VALIDATION CHECKLIST SUMMARY")
        print("=" * 50)
        
        # Count results by status
        all_results = []
        for section, results in self.checklist_results.items():
            if isinstance(results, dict) and "status" in results:
                all_results.append(results["status"])
            elif isinstance(results, dict):
                for check, result in results.items():
                    if isinstance(result, dict) and "status" in result:
                        all_results.append(result["status"])
        
        status_counts = {
            "PASS": all_results.count("PASS"),
            "WARN": all_results.count("WARN"),
            "FAIL": all_results.count("FAIL"),
            "ERROR": all_results.count("ERROR"),
            "SKIP": all_results.count("SKIP")
        }
        
        print(f"✅ Passed: {status_counts['PASS']}")
        print(f"⚠️ Warnings: {status_counts['WARN']}")
        print(f"❌ Failed: {status_counts['FAIL']}")
        print(f"🔧 Errors: {status_counts['ERROR']}")
        print(f"⏭️ Skipped: {status_counts['SKIP']}")
        print()
        
        # Overall health score
        total_meaningful = status_counts['PASS'] + status_counts['WARN'] + status_counts['FAIL']
        if total_meaningful > 0:
            health_score = (status_counts['PASS'] / total_meaningful) * 100
            
            if health_score >= 90:
                health_status = "EXCELLENT"
                health_icon = "🟢"
            elif health_score >= 75:
                health_status = "GOOD"
                health_icon = "🟡"
            elif health_score >= 60:
                health_status = "FAIR"
                health_icon = "🟠"
            else:
                health_status = "POOR"
                health_icon = "🔴"
            
            print(f"{health_icon} OVERALL HEALTH: {health_status} ({health_score:.1f}%)")
        else:
            health_score = None
            health_status = "INSUFFICIENT_DATA"
            print("❓ OVERALL HEALTH: Insufficient data")
        
        print()
        
        # Critical actions needed
        if self.critical_issues:
            print("🚨 IMMEDIATE ACTIONS REQUIRED:")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"   {i}. {issue}")
            print()
        
        # Recommendations
        if self.recommendations:
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"   {i}. {rec}")
            print()
        
        # Next validation
        next_validation = frappe.utils.add_days(frappe.utils.nowdate(), 7)
        print(f"📅 NEXT VALIDATION RECOMMENDED: {next_validation}")
        
        return {
            "validation_timestamp": frappe.utils.now(),
            "forecast_id": self.forecast_id,
            "overall_health_score": health_score,
            "overall_health_status": health_status,
            "status_counts": status_counts,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "detailed_results": self.checklist_results,
            "next_validation_date": next_validation
        }

# ============================================================================
# Quick Access Functions
# ============================================================================

def run_validation_checklist_for_forecast(forecast_id):
    """Run validation checklist for specific forecast"""
    validator = ValidationChecklistImplementation(forecast_id)
    return validator.run_complete_validation_checklist()

def run_system_wide_validation_checklist():
    """Run validation checklist for entire system"""
    validator = ValidationChecklistImplementation()
    return validator.run_complete_validation_checklist()

def validate_ai_fin_fcst_01319():
    """Validate the specific forecast from your checklist"""
    return run_validation_checklist_for_forecast("AI-FIN-FCST-01319")

if __name__ == "__main__":
    print("🔍 AI Financial Forecast Validation Checklist")
    print("=" * 50)
    print()
    print("Available functions:")
    print("• run_validation_checklist_for_forecast(id)")
    print("• run_system_wide_validation_checklist()")
    print("• validate_ai_fin_fcst_01319()")
    print()
    print("Example:")
    print("bench --site your-site execute ai_inventory.validation.validation_checklist.validate_ai_fin_fcst_01319")
