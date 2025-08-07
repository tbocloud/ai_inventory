#!/usr/bin/env python3
"""
AI Financial Forecast Critical Issue Validation Script
Quick validation for the bounds error: Upper bound < Lower bound

Usage:
bench --site your-site-name execute ai_inventory.validation.quick_forecast_check.run_critical_validation

Or run specific checks:
bench --site your-site-name execute ai_inventory.validation.quick_forecast_check.check_forecast_bounds --args "['AI-FIN-FCST-01319']"
"""

import frappe
import json
from datetime import datetime

def run_critical_validation():
    """Run critical validation checks for all AI Financial Forecasts"""
    
    print("🔍 Running Critical Validation for AI Financial Forecasts...")
    print("=" * 60)
    
    # Get all forecasts
    forecasts = frappe.get_all("AI Financial Forecast", 
                              fields=["name", "company", "account", "forecast_type", 
                                     "predicted_amount", "upper_bound", "lower_bound", 
                                     "confidence_score", "creation"])
    
    if not forecasts:
        print("❌ No AI Financial Forecasts found")
        return
    
    print(f"📊 Found {len(forecasts)} forecasts to validate")
    print()
    
    critical_issues = []
    warnings = []
    passed_checks = []
    
    for forecast in forecasts:
        print(f"🔍 Checking: {forecast.name}")
        
        # Critical Issue 1: Bounds Logic Error
        bounds_result = check_forecast_bounds_logic(forecast)
        if bounds_result["status"] == "CRITICAL":
            critical_issues.append(bounds_result)
            print(f"  🚨 CRITICAL: {bounds_result['message']}")
        elif bounds_result["status"] == "WARNING":
            warnings.append(bounds_result)
            print(f"  ⚠️ WARNING: {bounds_result['message']}")
        else:
            passed_checks.append(bounds_result)
            print(f"  ✅ PASSED: {bounds_result['message']}")
        
        # Critical Issue 2: Data Quality Check
        quality_result = check_data_quality(forecast)
        if quality_result["status"] == "CRITICAL":
            critical_issues.append(quality_result)
            print(f"  🚨 CRITICAL: {quality_result['message']}")
        elif quality_result["status"] == "WARNING":
            warnings.append(quality_result)
            print(f"  ⚠️ WARNING: {quality_result['message']}")
        
        # Critical Issue 3: Confidence Score Check
        confidence_result = check_confidence_score(forecast)
        if confidence_result["status"] == "CRITICAL":
            critical_issues.append(confidence_result)
            print(f"  🚨 CRITICAL: {confidence_result['message']}")
        elif confidence_result["status"] == "WARNING":
            warnings.append(confidence_result)
            print(f"  ⚠️ WARNING: {confidence_result['message']}")
        
        print()
    
    # Summary Report
    print("📋 VALIDATION SUMMARY")
    print("=" * 40)
    print(f"Total Forecasts Checked: {len(forecasts)}")
    print(f"🚨 Critical Issues: {len(critical_issues)}")
    print(f"⚠️ Warnings: {len(warnings)}")
    print(f"✅ Passed Checks: {len(passed_checks)}")
    print()
    
    if critical_issues:
        print("🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
        print("-" * 50)
        for issue in critical_issues:
            print(f"• {issue['forecast_id']}: {issue['message']}")
        print()
    
    if warnings:
        print("⚠️ WARNINGS NEEDING REVIEW:")
        print("-" * 30)
        for warning in warnings[:5]:  # Show first 5 warnings
            print(f"• {warning['forecast_id']}: {warning['message']}")
        if len(warnings) > 5:
            print(f"... and {len(warnings) - 5} more warnings")
        print()
    
    # Recommendations
    generate_recommendations(critical_issues, warnings)
    
    return {
        "total_forecasts": len(forecasts),
        "critical_issues": len(critical_issues),
        "warnings": len(warnings),
        "passed_checks": len(passed_checks),
        "critical_details": critical_issues,
        "warning_details": warnings
    }

def check_forecast_bounds_logic(forecast):
    """Check for the critical bounds logic error"""
    
    forecast_id = forecast.name
    upper_bound = forecast.upper_bound
    lower_bound = forecast.lower_bound
    
    if not upper_bound or not lower_bound:
        return {
            "forecast_id": forecast_id,
            "check": "bounds_logic",
            "status": "SKIPPED",
            "message": "No bounds set - cannot validate"
        }
    
    if upper_bound <= lower_bound:
        return {
            "forecast_id": forecast_id,
            "check": "bounds_logic",
            "status": "CRITICAL",
            "message": f"Upper bound (₹{upper_bound:,.2f}) ≤ Lower bound (₹{lower_bound:,.2f}) - CALCULATION ERROR!",
            "details": {
                "upper_bound": upper_bound,
                "lower_bound": lower_bound,
                "difference": lower_bound - upper_bound
            }
        }
    
    # Check for unreasonably wide bounds
    predicted_amount = forecast.predicted_amount
    if predicted_amount and predicted_amount != 0:
        bounds_spread = upper_bound - lower_bound
        spread_percentage = (bounds_spread / abs(predicted_amount)) * 100
        
        if spread_percentage > 100:
            return {
                "forecast_id": forecast_id,
                "check": "bounds_logic",
                "status": "WARNING",
                "message": f"Very wide prediction range ({spread_percentage:.1f}% of prediction)",
                "details": {
                    "bounds_spread": bounds_spread,
                    "spread_percentage": spread_percentage
                }
            }
    
    return {
        "forecast_id": forecast_id,
        "check": "bounds_logic",
        "status": "PASSED",
        "message": f"Bounds are valid (₹{lower_bound:,.2f} < ₹{upper_bound:,.2f})"
    }

def check_data_quality(forecast):
    """Check data quality indicators"""
    
    forecast_id = forecast.name
    
    # Get additional data quality info from document if available
    try:
        doc = frappe.get_doc("AI Financial Forecast", forecast_id)
        data_quality_score = getattr(doc, 'data_quality_score', None)
    except:
        data_quality_score = None
    
    if data_quality_score is not None:
        if data_quality_score < 50:
            return {
                "forecast_id": forecast_id,
                "check": "data_quality",
                "status": "CRITICAL",
                "message": f"Data quality critically low: {data_quality_score}%"
            }
        elif data_quality_score < 70:
            return {
                "forecast_id": forecast_id,
                "check": "data_quality",
                "status": "WARNING",
                "message": f"Data quality below recommended: {data_quality_score}% (Target: 80%+)"
            }
    
    # Check basic data completeness
    required_fields = ['company', 'account', 'forecast_type', 'predicted_amount']
    missing_fields = [field for field in required_fields if not getattr(forecast, field, None)]
    
    if missing_fields:
        return {
            "forecast_id": forecast_id,
            "check": "data_quality",
            "status": "CRITICAL",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    return {
        "forecast_id": forecast_id,
        "check": "data_quality",
        "status": "PASSED",
        "message": "Basic data quality checks passed"
    }

def check_confidence_score(forecast):
    """Check confidence score validity"""
    
    forecast_id = forecast.name
    confidence_score = forecast.confidence_score
    
    if not confidence_score:
        return {
            "forecast_id": forecast_id,
            "check": "confidence",
            "status": "WARNING",
            "message": "No confidence score set"
        }
    
    if confidence_score < 0 or confidence_score > 100:
        return {
            "forecast_id": forecast_id,
            "check": "confidence",
            "status": "CRITICAL",
            "message": f"Invalid confidence score: {confidence_score}% (must be 0-100%)"
        }
    
    if confidence_score < 50:
        return {
            "forecast_id": forecast_id,
            "check": "confidence",
            "status": "CRITICAL",
            "message": f"Confidence score critically low: {confidence_score}%"
        }
    
    if confidence_score < 70:
        return {
            "forecast_id": forecast_id,
            "check": "confidence",
            "status": "WARNING",
            "message": f"Confidence score below recommended: {confidence_score}% (Target: 70%+)"
        }
    
    return {
        "forecast_id": forecast_id,
        "check": "confidence",
        "status": "PASSED",
        "message": f"Confidence score acceptable: {confidence_score}%"
    }

def generate_recommendations(critical_issues, warnings):
    """Generate actionable recommendations"""
    
    print("💡 RECOMMENDATIONS:")
    print("-" * 20)
    
    if critical_issues:
        print("🚨 IMMEDIATE ACTIONS REQUIRED:")
        
        # Check for bounds issues
        bounds_issues = [issue for issue in critical_issues if issue["check"] == "bounds_logic"]
        if bounds_issues:
            print("  1. Fix forecast bounds calculation errors:")
            print("     - Review forecasting algorithm logic")
            print("     - Check data input validation")
            print("     - Verify model parameter settings")
            
        # Check for data quality issues
        data_issues = [issue for issue in critical_issues if issue["check"] == "data_quality"]
        if data_issues:
            print("  2. Address data quality problems:")
            print("     - Complete missing required fields")
            print("     - Improve data source connections")
            print("     - Implement data validation rules")
        
        # Check for confidence issues
        confidence_issues = [issue for issue in critical_issues if issue["check"] == "confidence"]
        if confidence_issues:
            print("  3. Improve model confidence:")
            print("     - Retrain prediction models")
            print("     - Increase historical data volume")
            print("     - Review model parameters")
    
    if warnings:
        print("\n⚠️ RECOMMENDED IMPROVEMENTS:")
        print("  • Monitor and improve data quality scores")
        print("  • Review prediction ranges for reasonableness")
        print("  • Set up automated validation alerts")
        print("  • Implement regular forecast accuracy tracking")
    
    print("\n📅 NEXT STEPS:")
    print("  1. Fix all critical issues immediately")
    print("  2. Set up weekly validation monitoring")
    print("  3. Implement automated quality checks")
    print("  4. Schedule monthly forecast accuracy reviews")

def check_specific_forecast(forecast_id):
    """Check a specific forecast by ID"""
    
    try:
        forecast = frappe.get_doc("AI Financial Forecast", forecast_id)
        
        print(f"🔍 Detailed Check for: {forecast_id}")
        print("=" * 50)
        print(f"Company: {forecast.company}")
        print(f"Account: {forecast.account}")
        print(f"Forecast Type: {forecast.forecast_type}")
        print(f"Created: {forecast.creation}")
        print()
        
        # Check bounds
        print("📊 BOUNDS CHECK:")
        if forecast.upper_bound and forecast.lower_bound:
            print(f"  Upper Bound: ₹{forecast.upper_bound:,.2f}")
            print(f"  Lower Bound: ₹{forecast.lower_bound:,.2f}")
            print(f"  Predicted:   ₹{forecast.predicted_amount:,.2f}")
            
            if forecast.upper_bound <= forecast.lower_bound:
                print("  🚨 CRITICAL ERROR: Upper bound ≤ Lower bound!")
                
                # Suggest fix
                print("\n💡 SUGGESTED FIX:")
                print(f"  Swap values: Upper = ₹{forecast.lower_bound:,.2f}, Lower = ₹{forecast.upper_bound:,.2f}")
                
                # Offer to fix automatically
                fix_response = input("  Would you like to fix this automatically? (y/n): ")
                if fix_response.lower() == 'y':
                    try:
                        forecast.upper_bound, forecast.lower_bound = forecast.lower_bound, forecast.upper_bound
                        forecast.save()
                        print("  ✅ Bounds fixed successfully!")
                    except Exception as e:
                        print(f"  ❌ Failed to fix: {str(e)}")
            else:
                print("  ✅ Bounds are logically correct")
        else:
            print("  ⚠️ Bounds not set")
        
        print()
        
        # Check confidence
        print("🎯 CONFIDENCE CHECK:")
        if forecast.confidence_score:
            print(f"  Confidence Score: {forecast.confidence_score}%")
            if forecast.confidence_score >= 80:
                print("  ✅ Excellent confidence")
            elif forecast.confidence_score >= 70:
                print("  ✅ Good confidence")
            elif forecast.confidence_score >= 60:
                print("  ⚠️ Fair confidence")
            else:
                print("  ❌ Poor confidence")
        else:
            print("  ⚠️ No confidence score set")
        
        print()
        
        # Additional checks
        print("📋 ADDITIONAL CHECKS:")
        
        # Data quality
        data_quality = getattr(forecast, 'data_quality_score', None)
        if data_quality:
            print(f"  Data Quality: {data_quality}%")
        else:
            print("  Data Quality: Not calculated")
        
        # Risk category
        print(f"  Risk Category: {forecast.risk_category}")
        
        # Volatility
        if forecast.volatility_score:
            print(f"  Volatility: {forecast.volatility_score}%")
        
        # Sync status
        print(f"  Sync Status: {forecast.sync_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking forecast {forecast_id}: {str(e)}")
        return False

def fix_all_bounds_issues():
    """Automatically fix all bounds issues found"""
    
    print("🔧 Attempting to fix all bounds issues...")
    
    # Find forecasts with bounds issues
    forecasts = frappe.get_all("AI Financial Forecast", 
                              fields=["name", "upper_bound", "lower_bound"],
                              filters={
                                  "upper_bound": ["is", "set"],
                                  "lower_bound": ["is", "set"]
                              })
    
    fixed_count = 0
    error_count = 0
    
    for forecast_data in forecasts:
        if forecast_data.upper_bound <= forecast_data.lower_bound:
            try:
                forecast = frappe.get_doc("AI Financial Forecast", forecast_data.name)
                
                # Swap bounds
                original_upper = forecast.upper_bound
                original_lower = forecast.lower_bound
                
                forecast.upper_bound = original_lower
                forecast.lower_bound = original_upper
                
                forecast.save()
                
                print(f"✅ Fixed {forecast_data.name}: Swapped bounds")
                fixed_count += 1
                
            except Exception as e:
                print(f"❌ Failed to fix {forecast_data.name}: {str(e)}")
                error_count += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"  Fixed: {fixed_count} forecasts")
    print(f"  Errors: {error_count} forecasts")
    
    return {"fixed": fixed_count, "errors": error_count}

if __name__ == "__main__":
    # Quick test when run directly
    print("🧪 Quick Bounds Logic Test")
    print("=" * 30)
    
    # Test data from your validation checklist
    test_cases = [
        {
            "name": "Your Critical Issue",
            "upper": 152231.96,
            "lower": 154663.20,
            "expected_result": "CRITICAL"
        },
        {
            "name": "Valid Bounds",
            "upper": 200000,
            "lower": 150000,
            "expected_result": "PASSED"
        },
        {
            "name": "Equal Bounds",
            "upper": 150000,
            "lower": 150000,
            "expected_result": "CRITICAL"
        }
    ]
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  Upper: ₹{test['upper']:,.2f}")
        print(f"  Lower: ₹{test['lower']:,.2f}")
        
        if test['upper'] <= test['lower']:
            result = "CRITICAL"
            print(f"  Result: 🚨 {result} - Upper bound ≤ Lower bound!")
        else:
            result = "PASSED"
            print(f"  Result: ✅ {result} - Bounds are valid")
        
        if result == test['expected_result']:
            print(f"  ✅ Test PASSED")
        else:
            print(f"  ❌ Test FAILED (Expected: {test['expected_result']})")
