# AI Financial Forecast Validation System
# Copyright (c) 2025, sammish and contributors

import frappe
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

class ForecastValidationSystem:
    """Comprehensive validation system for AI Financial Forecasts"""
    
    def __init__(self, forecast_id: str = None, company: str = None):
        self.forecast_id = forecast_id
        self.company = company
        self.validation_results = {}
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
    
    def run_comprehensive_validation(self) -> Dict:
        """Run all validation checks and return comprehensive report"""
        
        print("🔍 Starting Comprehensive Forecast Validation...")
        
        # 1. Data Accuracy Validation
        self.validate_data_accuracy()
        
        # 2. System Health Indicators
        self.validate_system_health()
        
        # 3. Model Performance Validation
        self.validate_model_performance()
        
        # 4. Integration & Sync Validation
        self.validate_integration_sync()
        
        # 5. Critical Issues Check
        self.check_critical_issues()
        
        # 6. Generate Report
        return self.generate_validation_report()
    
    def validate_data_accuracy(self):
        """Validate data accuracy and balance verification"""
        print("📊 Validating Data Accuracy...")
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Check forecast bounds logic
                bounds_valid = self.validate_forecast_bounds(forecast)
                
                # Check balance accuracy
                balance_accuracy = self.validate_balance_accuracy(forecast)
                
                # Check data completeness
                data_completeness = self.validate_data_completeness(forecast)
                
                self.validation_results["data_accuracy"] = {
                    "forecast_bounds_valid": bounds_valid,
                    "balance_accuracy": balance_accuracy,
                    "data_completeness": data_completeness,
                    "status": "PASSED" if bounds_valid and balance_accuracy["valid"] else "FAILED"
                }
                
        except Exception as e:
            self.critical_issues.append(f"Data accuracy validation failed: {str(e)}")
            self.validation_results["data_accuracy"] = {"status": "ERROR", "error": str(e)}
    
    def validate_forecast_bounds(self, forecast) -> bool:
        """Validate forecast bounds logic - Critical Issue Fix"""
        
        if not forecast.upper_bound or not forecast.lower_bound:
            self.warnings.append("Missing upper bound or lower bound values")
            return True  # Not critical if bounds not set
        
        if forecast.upper_bound <= forecast.lower_bound:
            self.critical_issues.append(
                f"🚨 CRITICAL: Upper bound (₹{forecast.upper_bound:,.2f}) "
                f"is less than or equal to lower bound (₹{forecast.lower_bound:,.2f})"
            )
            return False
        
        # Additional validation - predicted amount should be within bounds
        if forecast.predicted_amount:
            if forecast.predicted_amount > forecast.upper_bound:
                self.warnings.append(
                    f"Predicted amount (₹{forecast.predicted_amount:,.2f}) exceeds upper bound"
                )
            elif forecast.predicted_amount < forecast.lower_bound:
                self.warnings.append(
                    f"Predicted amount (₹{forecast.predicted_amount:,.2f}) is below lower bound"
                )
        
        return True
    
    def validate_balance_accuracy(self, forecast) -> Dict:
        """Validate current balance accuracy"""
        
        try:
            # Get current balance from account
            if forecast.account:
                current_balance = frappe.db.get_value("Account", forecast.account, "account_balance") or 0
                
                # Compare with forecast's current balance if available
                forecast_balance = getattr(forecast, 'current_balance', None)
                
                if forecast_balance:
                    difference = abs(current_balance - forecast_balance)
                    tolerance = 1.0  # ₹1 tolerance
                    
                    return {
                        "valid": difference <= tolerance,
                        "system_balance": current_balance,
                        "forecast_balance": forecast_balance,
                        "difference": difference,
                        "tolerance": tolerance
                    }
                else:
                    return {"valid": True, "note": "No current balance field in forecast"}
            
            return {"valid": True, "note": "No account linked to forecast"}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def validate_data_completeness(self, forecast) -> Dict:
        """Validate data completeness and quality"""
        
        required_fields = [
            'company', 'account', 'forecast_type', 'forecast_start_date',
            'predicted_amount', 'confidence_score'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(forecast, field, None):
                missing_fields.append(field)
        
        # Check data quality score if available
        data_quality_score = getattr(forecast, 'data_quality_score', None)
        if data_quality_score and data_quality_score < 80:
            self.warnings.append(f"Data quality score low: {data_quality_score}% (Target: >80%)")
        
        completeness_score = ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100
        
        return {
            "completeness_score": completeness_score,
            "missing_fields": missing_fields,
            "data_quality_score": data_quality_score,
            "status": "GOOD" if completeness_score >= 90 else "NEEDS_IMPROVEMENT"
        }
    
    def validate_system_health(self):
        """Validate system health indicators"""
        print("🏥 Validating System Health...")
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Check data quality score
                data_quality = self.check_data_quality_score(forecast)
                
                # Check volatility score
                volatility_check = self.check_volatility_score(forecast)
                
                # Check risk category
                risk_assessment = self.check_risk_category(forecast)
                
                self.validation_results["system_health"] = {
                    "data_quality": data_quality,
                    "volatility": volatility_check,
                    "risk_assessment": risk_assessment,
                    "overall_health": self.calculate_system_health_score(data_quality, volatility_check, risk_assessment)
                }
                
        except Exception as e:
            self.critical_issues.append(f"System health validation failed: {str(e)}")
    
    def check_data_quality_score(self, forecast) -> Dict:
        """Check and evaluate data quality score"""
        
        data_quality = getattr(forecast, 'data_quality_score', None)
        
        if not data_quality:
            return {"score": None, "status": "UNKNOWN", "recommendation": "Enable data quality tracking"}
        
        if data_quality >= 80:
            status = "EXCELLENT"
        elif data_quality >= 70:
            status = "GOOD"
        elif data_quality >= 60:
            status = "FAIR"
        else:
            status = "POOR"
            self.critical_issues.append(f"Data quality score critically low: {data_quality}%")
        
        return {
            "score": data_quality,
            "status": status,
            "target": 80,
            "recommendation": "Improve data sources and completeness" if data_quality < 80 else "Maintain current quality"
        }
    
    def check_volatility_score(self, forecast) -> Dict:
        """Check volatility score and assess risk"""
        
        volatility = getattr(forecast, 'volatility_score', None)
        
        if not volatility:
            return {"score": None, "status": "UNKNOWN"}
        
        if volatility <= 20:
            status = "LOW"
            risk_level = "Stable and predictable"
        elif volatility <= 40:
            status = "MODERATE"
            risk_level = "Some variability expected"
        elif volatility <= 70:
            status = "HIGH"
            risk_level = "Significant variability"
        else:
            status = "VERY_HIGH"
            risk_level = "Highly unpredictable"
            self.warnings.append(f"Very high volatility detected: {volatility}%")
        
        return {
            "score": volatility,
            "status": status,
            "risk_level": risk_level,
            "recommendation": "Monitor closely" if volatility > 50 else "Continue monitoring"
        }
    
    def check_risk_category(self, forecast) -> Dict:
        """Check risk category assessment"""
        
        risk_category = getattr(forecast, 'risk_category', 'Unknown')
        
        risk_mapping = {
            "Low": {"level": 1, "action": "Routine monitoring"},
            "Medium": {"level": 2, "action": "Regular review"},
            "High": {"level": 3, "action": "Increased attention"},
            "Critical": {"level": 4, "action": "Immediate action required"}
        }
        
        risk_info = risk_mapping.get(risk_category, {"level": 0, "action": "Assessment needed"})
        
        if risk_category in ["High", "Critical"]:
            self.warnings.append(f"High risk category detected: {risk_category}")
        
        return {
            "category": risk_category,
            "level": risk_info["level"],
            "recommended_action": risk_info["action"]
        }
    
    def calculate_system_health_score(self, data_quality, volatility, risk_assessment) -> Dict:
        """Calculate overall system health score"""
        
        scores = []
        
        # Data quality component (40% weight)
        if data_quality["score"]:
            scores.append(data_quality["score"] * 0.4)
        
        # Volatility component (30% weight) - inverted (low volatility = high score)
        if volatility["score"]:
            volatility_score = max(0, 100 - volatility["score"])
            scores.append(volatility_score * 0.3)
        
        # Risk component (30% weight) - inverted (low risk = high score)
        risk_scores = {"Low": 100, "Medium": 75, "High": 50, "Critical": 25}
        risk_score = risk_scores.get(risk_assessment["category"], 50)
        scores.append(risk_score * 0.3)
        
        if scores:
            overall_score = sum(scores) / len(scores) if len(scores) == 3 else sum(scores)
            
            if overall_score >= 85:
                health_status = "EXCELLENT"
            elif overall_score >= 75:
                health_status = "GOOD"
            elif overall_score >= 65:
                health_status = "FAIR"
            else:
                health_status = "POOR"
            
            return {
                "overall_score": round(overall_score, 2),
                "health_status": health_status,
                "components_evaluated": len(scores)
            }
        
        return {"overall_score": None, "health_status": "INSUFFICIENT_DATA"}
    
    def validate_model_performance(self):
        """Validate model performance metrics"""
        print("📊 Validating Model Performance...")
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Check confidence score
                confidence_check = self.check_confidence_score(forecast)
                
                # Check prediction model
                model_check = self.check_prediction_model(forecast)
                
                # Check forecast accuracy
                accuracy_check = self.check_forecast_accuracy(forecast)
                
                self.validation_results["model_performance"] = {
                    "confidence": confidence_check,
                    "model": model_check,
                    "accuracy": accuracy_check,
                    "overall_performance": self.calculate_model_performance_score(confidence_check, accuracy_check)
                }
                
        except Exception as e:
            self.critical_issues.append(f"Model performance validation failed: {str(e)}")
    
    def check_confidence_score(self, forecast) -> Dict:
        """Check model confidence score"""
        
        confidence = getattr(forecast, 'confidence_score', None)
        threshold = getattr(forecast, 'confidence_threshold', 70)
        
        if not confidence:
            return {"score": None, "status": "MISSING", "threshold": threshold}
        
        if confidence >= 80:
            status = "EXCELLENT"
        elif confidence >= threshold:
            status = "ACCEPTABLE"
        elif confidence >= 60:
            status = "LOW"
            self.warnings.append(f"Confidence score below threshold: {confidence}% (Target: {threshold}%)")
        else:
            status = "CRITICAL"
            self.critical_issues.append(f"Confidence score critically low: {confidence}%")
        
        return {
            "score": confidence,
            "status": status,
            "threshold": threshold,
            "meets_threshold": confidence >= threshold if confidence else False
        }
    
    def check_prediction_model(self, forecast) -> Dict:
        """Check prediction model suitability"""
        
        model = getattr(forecast, 'prediction_model', 'Unknown')
        
        model_suitability = {
            "Linear Regression": {
                "suitable_for": ["Linear trends", "Simple patterns"],
                "limitations": ["Non-linear patterns", "Seasonality"],
                "recommendation": "Good for stable, linear financial trends"
            },
            "ARIMA": {
                "suitable_for": ["Time series", "Seasonality", "Trends"],
                "limitations": ["Non-stationary data", "Complex patterns"],
                "recommendation": "Excellent for financial time series"
            },
            "LSTM": {
                "suitable_for": ["Complex patterns", "Long-term dependencies"],
                "limitations": ["Requires large datasets", "Computationally intensive"],
                "recommendation": "Best for complex financial forecasting"
            }
        }
        
        model_info = model_suitability.get(model, {
            "suitable_for": ["Unknown"],
            "limitations": ["Unknown"],
            "recommendation": "Verify model suitability for financial data"
        })
        
        return {
            "current_model": model,
            "model_info": model_info,
            "recommendation": model_info["recommendation"]
        }
    
    def check_forecast_accuracy(self, forecast) -> Dict:
        """Check historical forecast accuracy"""
        
        try:
            # Get accuracy records for this forecast
            accuracy_records = frappe.get_all("AI Forecast Accuracy",
                                            filters={"forecast_reference": forecast.name},
                                            fields=["accuracy_score", "prediction_error", "evaluation_date"],
                                            order_by="evaluation_date desc",
                                            limit=5)
            
            if accuracy_records:
                avg_accuracy = sum(r.accuracy_score for r in accuracy_records if r.accuracy_score) / len(accuracy_records)
                latest_accuracy = accuracy_records[0].accuracy_score if accuracy_records[0].accuracy_score else None
                
                return {
                    "has_history": True,
                    "records_count": len(accuracy_records),
                    "average_accuracy": round(avg_accuracy, 2) if avg_accuracy else None,
                    "latest_accuracy": latest_accuracy,
                    "status": "GOOD" if avg_accuracy and avg_accuracy >= 80 else "NEEDS_IMPROVEMENT"
                }
            else:
                return {
                    "has_history": False,
                    "records_count": 0,
                    "status": "NO_DATA",
                    "recommendation": "Enable accuracy tracking"
                }
                
        except Exception as e:
            return {"has_history": False, "error": str(e)}
    
    def calculate_model_performance_score(self, confidence_check, accuracy_check) -> Dict:
        """Calculate overall model performance score"""
        
        score_components = []
        
        # Confidence component (60% weight)
        if confidence_check["score"]:
            score_components.append(confidence_check["score"] * 0.6)
        
        # Accuracy component (40% weight)
        if accuracy_check.get("average_accuracy"):
            score_components.append(accuracy_check["average_accuracy"] * 0.4)
        
        if score_components:
            overall_score = sum(score_components)
            
            if overall_score >= 85:
                performance_status = "EXCELLENT"
            elif overall_score >= 75:
                performance_status = "GOOD"
            elif overall_score >= 65:
                performance_status = "FAIR"
            else:
                performance_status = "POOR"
            
            return {
                "overall_score": round(overall_score, 2),
                "performance_status": performance_status
            }
        
        return {"overall_score": None, "performance_status": "INSUFFICIENT_DATA"}
    
    def validate_integration_sync(self):
        """Validate integration and sync status"""
        print("🔄 Validating Integration & Sync...")
        
        try:
            if self.forecast_id:
                forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
                
                # Check sync status
                sync_status = self.check_sync_status(forecast)
                
                # Check integration health
                integration_health = self.check_integration_health(forecast)
                
                self.validation_results["integration_sync"] = {
                    "sync_status": sync_status,
                    "integration_health": integration_health,
                    "overall_sync_health": "HEALTHY" if sync_status["status"] == "ACTIVE" else "NEEDS_ATTENTION"
                }
                
        except Exception as e:
            self.critical_issues.append(f"Integration validation failed: {str(e)}")
    
    def check_sync_status(self, forecast) -> Dict:
        """Check auto sync status and health"""
        
        auto_sync = getattr(forecast, 'inventory_sync_enabled', False)
        sync_status = getattr(forecast, 'sync_status', 'Unknown')
        last_sync = getattr(forecast, 'last_sync_date', None)
        
        # Check if sync is recent (within last 2 days)
        sync_current = False
        if last_sync:
            last_sync_date = frappe.utils.get_datetime(last_sync)
            days_since_sync = (frappe.utils.now_datetime() - last_sync_date).days
            sync_current = days_since_sync <= 2
        
        if auto_sync and sync_status == "Completed" and sync_current:
            status = "ACTIVE"
        elif auto_sync and sync_status in ["Pending", "Running"]:
            status = "IN_PROGRESS"
        elif not auto_sync:
            status = "DISABLED"
        else:
            status = "FAILED"
            self.warnings.append("Sync appears to have failed or is outdated")
        
        return {
            "auto_sync_enabled": auto_sync,
            "sync_status": sync_status,
            "last_sync_date": last_sync,
            "sync_current": sync_current,
            "status": status
        }
    
    def check_integration_health(self, forecast) -> Dict:
        """Check integration with other systems"""
        
        integrations = {}
        
        # Check inventory integration
        if getattr(forecast, 'inventory_sync_enabled', False):
            inventory_forecasts = frappe.db.count("AI Inventory Forecast", 
                                                {"company": forecast.company})
            integrations["inventory"] = {
                "enabled": True,
                "forecast_count": inventory_forecasts,
                "status": "ACTIVE" if inventory_forecasts > 0 else "NO_DATA"
            }
        
        # Check related forecast types
        related_forecasts = frappe.db.count("AI Financial Forecast", 
                                          {"company": forecast.company, 
                                           "name": ["!=", forecast.name]})
        
        integrations["financial"] = {
            "related_forecasts": related_forecasts,
            "status": "MULTI_FORECAST" if related_forecasts > 0 else "SINGLE_FORECAST"
        }
        
        return integrations
    
    def check_critical_issues(self):
        """Run critical issue detection"""
        print("⚠️ Checking for Critical Issues...")
        
        if self.forecast_id:
            forecast = frappe.get_doc("AI Financial Forecast", self.forecast_id)
            
            # Critical Issue 1: Forecast bounds error (already checked)
            # Critical Issue 2: Data quality extremely low
            data_quality = getattr(forecast, 'data_quality_score', None)
            if data_quality and data_quality < 50:
                self.critical_issues.append(f"Data quality critically low: {data_quality}%")
            
            # Critical Issue 3: Confidence score extremely low
            confidence = getattr(forecast, 'confidence_score', None)
            if confidence and confidence < 50:
                self.critical_issues.append(f"Model confidence critically low: {confidence}%")
            
            # Critical Issue 4: Sync failures
            sync_status = getattr(forecast, 'sync_status', None)
            if sync_status == "Failed":
                self.critical_issues.append("Sync operations are failing")
            
            # Critical Issue 5: Missing critical data
            if not forecast.company or not forecast.account:
                self.critical_issues.append("Missing critical reference data (company/account)")
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        
        # Calculate overall system score
        overall_score = self.calculate_overall_score()
        
        # Generate recommendations
        self.generate_recommendations()
        
        report = {
            "validation_timestamp": frappe.utils.now(),
            "forecast_id": self.forecast_id,
            "company": self.company,
            "overall_score": overall_score,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "detailed_results": self.validation_results,
            "summary": self.generate_summary()
        }
        
        return report
    
    def calculate_overall_score(self) -> Dict:
        """Calculate overall validation score"""
        
        scores = []
        weights = []
        
        # Data accuracy (25% weight)
        if "data_accuracy" in self.validation_results:
            data_result = self.validation_results["data_accuracy"]
            if data_result.get("status") == "PASSED":
                scores.append(85)
                weights.append(25)
            elif data_result.get("status") == "FAILED":
                scores.append(30)
                weights.append(25)
        
        # System health (25% weight)
        if "system_health" in self.validation_results:
            health_result = self.validation_results["system_health"]
            overall_health = health_result.get("overall_health", {})
            if overall_health.get("overall_score"):
                scores.append(overall_health["overall_score"])
                weights.append(25)
        
        # Model performance (30% weight)
        if "model_performance" in self.validation_results:
            model_result = self.validation_results["model_performance"]
            overall_performance = model_result.get("overall_performance", {})
            if overall_performance.get("overall_score"):
                scores.append(overall_performance["overall_score"])
                weights.append(30)
        
        # Integration sync (20% weight)
        if "integration_sync" in self.validation_results:
            sync_result = self.validation_results["integration_sync"]
            if sync_result.get("overall_sync_health") == "HEALTHY":
                scores.append(90)
                weights.append(20)
            else:
                scores.append(60)
                weights.append(20)
        
        if scores and weights:
            weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
            
            if weighted_score >= 85:
                grade = "A"
                status = "EXCELLENT"
            elif weighted_score >= 75:
                grade = "B"
                status = "GOOD"
            elif weighted_score >= 65:
                grade = "C"
                status = "FAIR"
            elif weighted_score >= 50:
                grade = "D"
                status = "POOR"
            else:
                grade = "F"
                status = "CRITICAL"
            
            return {
                "score": round(weighted_score, 2),
                "grade": grade,
                "status": status,
                "critical_issues_count": len(self.critical_issues),
                "warnings_count": len(self.warnings)
            }
        
        return {
            "score": None,
            "grade": "N/A",
            "status": "INSUFFICIENT_DATA",
            "critical_issues_count": len(self.critical_issues),
            "warnings_count": len(self.warnings)
        }
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        
        # Recommendations based on critical issues
        if len(self.critical_issues) > 0:
            self.recommendations.append("🚨 Address all critical issues immediately")
        
        # Recommendations based on warnings
        if len(self.warnings) > 3:
            self.recommendations.append("⚠️ Review and address multiple system warnings")
        
        # Data quality recommendations
        if "data_accuracy" in self.validation_results:
            data_result = self.validation_results["data_accuracy"]
            if data_result.get("data_completeness", {}).get("completeness_score", 100) < 90:
                self.recommendations.append("📊 Improve data completeness by connecting missing data sources")
        
        # Model performance recommendations
        if "model_performance" in self.validation_results:
            model_result = self.validation_results["model_performance"]
            confidence = model_result.get("confidence", {})
            if confidence.get("score", 100) < 80:
                self.recommendations.append("🎯 Consider model retraining or algorithm optimization")
        
        # Sync recommendations
        if "integration_sync" in self.validation_results:
            sync_result = self.validation_results["integration_sync"]
            if sync_result.get("overall_sync_health") != "HEALTHY":
                self.recommendations.append("🔄 Fix sync issues and enable automated monitoring")
        
        # General recommendations
        if not self.recommendations:
            self.recommendations.append("✅ System appears healthy - continue regular monitoring")
    
    def generate_summary(self) -> Dict:
        """Generate executive summary"""
        
        return {
            "validation_status": "COMPLETED",
            "total_checks_performed": len(self.validation_results),
            "critical_issues_found": len(self.critical_issues),
            "warnings_issued": len(self.warnings),
            "recommendations_provided": len(self.recommendations),
            "next_validation_recommended": frappe.utils.add_days(frappe.utils.nowdate(), 7)
        }

# ============================================================================
# Utility Functions for Easy Validation
# ============================================================================

@frappe.whitelist()
def validate_specific_forecast(forecast_id: str) -> Dict:
    """Validate a specific forecast and return report"""
    
    validator = ForecastValidationSystem(forecast_id=forecast_id)
    return validator.run_comprehensive_validation()

@frappe.whitelist()
def validate_company_forecasts(company: str) -> Dict:
    """Validate all forecasts for a company"""
    
    forecasts = frappe.get_all("AI Financial Forecast", 
                              filters={"company": company}, 
                              fields=["name"])
    
    results = {}
    for forecast in forecasts:
        validator = ForecastValidationSystem(forecast_id=forecast.name, company=company)
        results[forecast.name] = validator.run_comprehensive_validation()
    
    return {
        "company": company,
        "total_forecasts": len(forecasts),
        "validation_results": results,
        "summary": generate_company_validation_summary(results)
    }

def generate_company_validation_summary(results: Dict) -> Dict:
    """Generate summary for company-wide validation"""
    
    total_forecasts = len(results)
    critical_issues = sum(len(r.get("critical_issues", [])) for r in results.values())
    warnings = sum(len(r.get("warnings", [])) for r in results.values())
    
    scores = [r.get("overall_score", {}).get("score") for r in results.values() if r.get("overall_score", {}).get("score")]
    avg_score = sum(scores) / len(scores) if scores else None
    
    return {
        "total_forecasts_validated": total_forecasts,
        "total_critical_issues": critical_issues,
        "total_warnings": warnings,
        "average_score": round(avg_score, 2) if avg_score else None,
        "health_status": "HEALTHY" if critical_issues == 0 and avg_score and avg_score >= 75 else "NEEDS_ATTENTION"
    }

# ============================================================================
# Quick Validation Script for Testing
# ============================================================================

def run_quick_validation_test():
    """Quick validation test script"""
    
    print("🧪 Running Quick Validation Test...")
    
    # Test forecast bounds logic
    test_data = [
        {"upper": 152231.96, "lower": 154663.20, "expected": False},  # Your critical issue
        {"upper": 200000, "lower": 150000, "expected": True},        # Valid bounds
        {"upper": 100000, "lower": 100000, "expected": False},       # Equal bounds
    ]
    
    print("\n📊 Testing Forecast Bounds Logic:")
    for i, test in enumerate(test_data, 1):
        result = test["upper"] > test["lower"]
        status = "✅ PASS" if result == test["expected"] else "❌ FAIL"
        print(f"Test {i}: Upper={test['upper']}, Lower={test['lower']} → {status}")
    
    # Test data quality thresholds
    print("\n📈 Testing Data Quality Thresholds:")
    quality_scores = [67.50, 85.0, 45.0, 75.0]
    for score in quality_scores:
        if score >= 80:
            status = "✅ EXCELLENT"
        elif score >= 70:
            status = "✅ GOOD"
        elif score >= 60:
            status = "⚠️ FAIR"
        else:
            status = "❌ POOR"
        print(f"Quality Score {score}%: {status}")
    
    # Test confidence thresholds
    print("\n🎯 Testing Confidence Thresholds:")
    confidence_scores = [81, 65, 90, 45]
    for confidence in confidence_scores:
        if confidence >= 80:
            status = "✅ EXCELLENT"
        elif confidence >= 70:
            status = "✅ ACCEPTABLE"
        else:
            status = "⚠️ LOW"
        print(f"Confidence {confidence}%: {status}")
    
    print("\n✅ Quick validation test completed!")

if __name__ == "__main__":
    run_quick_validation_test()
