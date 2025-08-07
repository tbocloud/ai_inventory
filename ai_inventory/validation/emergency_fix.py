#!/usr/bin/env python3
"""
AI Financial Forecast Emergency Fix Script
Addresses the critical bounds issue identified in AI-FIN-FCST-01319

CRITICAL ISSUE CONFIRMED:
- Upper Bound: ₹152,231.96
- Lower Bound: ₹154,663.20
- ERROR: Upper bound < Lower bound (violates basic logic)

Usage:
1. Run diagnostics: bench --site your-site-name execute ai_inventory.validation.emergency_fix.run_emergency_diagnostics
2. Fix specific forecast: bench --site your-site-name execute ai_inventory.validation.emergency_fix.fix_specific_forecast --args "['AI-FIN-FCST-01319']"
3. Fix all issues: bench --site your-site-name execute ai_inventory.validation.emergency_fix.fix_all_bounds_issues
"""

import frappe
import json
from datetime import datetime

class EmergencyForecastFix:
    """Emergency fix for critical forecast validation issues"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        self.errors_encountered = []
    
    def run_emergency_diagnostics(self):
        """Run emergency diagnostics on all forecasts"""
        
        print("🚨 EMERGENCY FORECAST DIAGNOSTICS")
        print("=" * 50)
        print("Checking for critical bounds logic errors...")
        print()
        
        try:
            # Get all forecasts with bounds data
            forecasts = frappe.db.sql("""
                SELECT 
                    name, company, account, forecast_type,
                    predicted_amount, upper_bound, lower_bound,
                    confidence_score, creation, modified
                FROM `tabAI Financial Forecast`
                WHERE upper_bound IS NOT NULL 
                AND lower_bound IS NOT NULL
                ORDER BY modified DESC
            """, as_dict=True)
            
            print(f"📊 Found {len(forecasts)} forecasts with bounds data")
            print()
            
            critical_count = 0
            warning_count = 0
            
            for forecast in forecasts:
                result = self.diagnose_forecast(forecast)
                
                if result["severity"] == "CRITICAL":
                    critical_count += 1
                    print(f"🚨 CRITICAL: {forecast.name}")
                    print(f"   {result['message']}")
                    print(f"   Created: {forecast.creation}")
                    print()
                elif result["severity"] == "WARNING":
                    warning_count += 1
                    print(f"⚠️ WARNING: {forecast.name} - {result['message']}")
            
            print("\n📋 DIAGNOSTIC SUMMARY:")
            print(f"Total Forecasts: {len(forecasts)}")
            print(f"🚨 Critical Issues: {critical_count}")
            print(f"⚠️ Warnings: {warning_count}")
            print(f"✅ Clean Forecasts: {len(forecasts) - critical_count - warning_count}")
            
            if critical_count > 0:
                print(f"\n🚨 IMMEDIATE ACTION REQUIRED for {critical_count} forecasts!")
                print("Run fix_all_bounds_issues() to automatically correct them.")
            
            return {
                "total_forecasts": len(forecasts),
                "critical_issues": critical_count,
                "warnings": warning_count,
                "issues_found": self.issues_found
            }
            
        except Exception as e:
            print(f"❌ Emergency diagnostics failed: {str(e)}")
            return {"error": str(e)}
    
    def diagnose_forecast(self, forecast):
        """Diagnose a single forecast for issues"""
        
        issues = []
        severity = "OK"
        
        # Critical Issue 1: Bounds Logic Error
        if forecast.upper_bound <= forecast.lower_bound:
            severity = "CRITICAL"
            difference = forecast.lower_bound - forecast.upper_bound
            issues.append(f"Upper bound (₹{forecast.upper_bound:,.2f}) ≤ Lower bound (₹{forecast.lower_bound:,.2f}). Difference: ₹{difference:,.2f}")
            
            self.issues_found.append({
                "forecast_id": forecast.name,
                "type": "bounds_logic_error",
                "severity": "CRITICAL",
                "upper_bound": forecast.upper_bound,
                "lower_bound": forecast.lower_bound,
                "difference": difference,
                "message": f"Bounds calculation error - upper < lower by ₹{difference:,.2f}"
            })
        
        # Check prediction vs bounds relationship
        if forecast.predicted_amount and severity != "CRITICAL":
            if forecast.predicted_amount < forecast.lower_bound or forecast.predicted_amount > forecast.upper_bound:
                if severity != "CRITICAL":
                    severity = "WARNING"
                issues.append(f"Prediction (₹{forecast.predicted_amount:,.2f}) outside bounds range")
        
        # Check confidence score
        if forecast.confidence_score and forecast.confidence_score < 50:
            if severity not in ["CRITICAL"]:
                severity = "WARNING"
            issues.append(f"Very low confidence: {forecast.confidence_score}%")
        
        message = "; ".join(issues) if issues else "No issues found"
        
        return {
            "forecast_id": forecast.name,
            "severity": severity,
            "message": message,
            "issues": issues
        }
    
    def fix_specific_forecast(self, forecast_id):
        """Fix a specific forecast by ID"""
        
        print(f"🔧 Fixing forecast: {forecast_id}")
        
        try:
            # Get the forecast document
            forecast = frappe.get_doc("AI Financial Forecast", forecast_id)
            
            print(f"   Company: {forecast.company}")
            print(f"   Account: {forecast.account}")
            print(f"   Type: {forecast.forecast_type}")
            
            fixes_applied = []
            
            # Fix bounds logic error
            if forecast.upper_bound and forecast.lower_bound:
                if forecast.upper_bound <= forecast.lower_bound:
                    print(f"   🚨 Found bounds error:")
                    print(f"      Current Upper: ₹{forecast.upper_bound:,.2f}")
                    print(f"      Current Lower: ₹{forecast.lower_bound:,.2f}")
                    
                    # Swap the values
                    original_upper = forecast.upper_bound
                    original_lower = forecast.lower_bound
                    
                    forecast.upper_bound = original_lower
                    forecast.lower_bound = original_upper
                    
                    print(f"   ✅ Corrected bounds:")
                    print(f"      New Upper: ₹{forecast.upper_bound:,.2f}")
                    print(f"      New Lower: ₹{forecast.lower_bound:,.2f}")
                    
                    fixes_applied.append("swapped_bounds")
            
            # Add validation note
            validation_note = {
                "timestamp": frappe.utils.now(),
                "action": "emergency_validation_fix",
                "fixes_applied": fixes_applied,
                "validator": "emergency_fix_script",
                "original_bounds": {
                    "upper": original_upper if 'original_upper' in locals() else None,
                    "lower": original_lower if 'original_lower' in locals() else None
                }
            }
            
            # Store validation history
            existing_notes = forecast.get("validation_notes") or "[]"
            try:
                notes_list = json.loads(existing_notes)
            except:
                notes_list = []
            
            notes_list.append(validation_note)
            forecast.validation_notes = json.dumps(notes_list)
            
            # Set validation status
            forecast.validation_status = "Emergency Fixed"
            forecast.validation_date = frappe.utils.now()
            
            # Save the changes
            forecast.flags.ignore_validate = True  # Skip validation to avoid recursion
            forecast.save()
            
            print(f"   ✅ Forecast {forecast_id} fixed successfully!")
            
            self.fixes_applied.append({
                "forecast_id": forecast_id,
                "fixes": fixes_applied,
                "timestamp": frappe.utils.now()
            })
            
            return {
                "success": True,
                "forecast_id": forecast_id,
                "fixes_applied": fixes_applied,
                "message": "Forecast fixed successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to fix forecast {forecast_id}: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            self.errors_encountered.append({
                "forecast_id": forecast_id,
                "error": str(e),
                "timestamp": frappe.utils.now()
            })
            
            return {
                "success": False,
                "forecast_id": forecast_id,
                "error": str(e),
                "message": error_msg
            }
    
    def fix_all_bounds_issues(self):
        """Fix all forecasts with bounds logic errors"""
        
        print("🔧 MASS FIX: Correcting all bounds logic errors...")
        print("=" * 50)
        
        try:
            # Find all forecasts with bounds issues
            problem_forecasts = frappe.db.sql("""
                SELECT name, upper_bound, lower_bound
                FROM `tabAI Financial Forecast`
                WHERE upper_bound IS NOT NULL 
                AND lower_bound IS NOT NULL
                AND upper_bound <= lower_bound
            """, as_dict=True)
            
            print(f"📊 Found {len(problem_forecasts)} forecasts with bounds issues")
            
            if len(problem_forecasts) == 0:
                print("✅ No bounds issues found - all forecasts are clean!")
                return {"fixed": 0, "errors": 0, "message": "No issues to fix"}
            
            print()
            
            fixed_count = 0
            error_count = 0
            
            for forecast_data in problem_forecasts:
                result = self.fix_specific_forecast(forecast_data.name)
                
                if result["success"]:
                    fixed_count += 1
                else:
                    error_count += 1
            
            print(f"\n📊 MASS FIX SUMMARY:")
            print(f"✅ Successfully Fixed: {fixed_count}")
            print(f"❌ Errors Encountered: {error_count}")
            print(f"📈 Success Rate: {(fixed_count/(fixed_count+error_count)*100):.1f}%" if (fixed_count+error_count) > 0 else "N/A")
            
            # Create summary log
            self.create_fix_summary_log(fixed_count, error_count)
            
            return {
                "fixed": fixed_count,
                "errors": error_count,
                "total_issues": len(problem_forecasts),
                "fixes_applied": self.fixes_applied,
                "errors_encountered": self.errors_encountered
            }
            
        except Exception as e:
            print(f"❌ Mass fix operation failed: {str(e)}")
            return {"error": str(e)}
    
    def create_fix_summary_log(self, fixed_count, error_count):
        """Create a summary log of the fix operation"""
        
        try:
            log_doc = frappe.get_doc({
                "doctype": "AI Forecast Log",
                "forecast_id": "MASS_FIX_OPERATION",
                "action": "Emergency Bounds Fix",
                "details": f"Mass fix operation: {fixed_count} fixed, {error_count} errors",
                "user": frappe.session.user,
                "additional_data": json.dumps({
                    "fixes_applied": self.fixes_applied,
                    "errors_encountered": self.errors_encountered,
                    "operation_timestamp": frappe.utils.now()
                })
            })
            
            log_doc.flags.ignore_permissions = True
            log_doc.insert()
            
            print(f"📝 Fix summary logged successfully")
            
        except Exception as e:
            print(f"⚠️ Could not create summary log: {str(e)}")
    
    def validate_fix_success(self):
        """Validate that all fixes were applied correctly"""
        
        print("🔍 Validating fix success...")
        
        try:
            # Check if any bounds issues remain
            remaining_issues = frappe.db.sql("""
                SELECT name, upper_bound, lower_bound
                FROM `tabAI Financial Forecast`
                WHERE upper_bound IS NOT NULL 
                AND lower_bound IS NOT NULL
                AND upper_bound <= lower_bound
            """, as_dict=True)
            
            if len(remaining_issues) == 0:
                print("✅ SUCCESS: All bounds issues have been resolved!")
                return True
            else:
                print(f"⚠️ WARNING: {len(remaining_issues)} bounds issues still remain:")
                for issue in remaining_issues:
                    print(f"   - {issue.name}: Upper=₹{issue.upper_bound:,.2f}, Lower=₹{issue.lower_bound:,.2f}")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {str(e)}")
            return False

# ============================================================================
# Quick Access Functions
# ============================================================================

def run_emergency_diagnostics():
    """Quick function to run emergency diagnostics"""
    fixer = EmergencyForecastFix()
    return fixer.run_emergency_diagnostics()

def fix_specific_forecast(forecast_id):
    """Quick function to fix a specific forecast"""
    fixer = EmergencyForecastFix()
    return fixer.fix_specific_forecast(forecast_id)

def fix_all_bounds_issues():
    """Quick function to fix all bounds issues"""
    fixer = EmergencyForecastFix()
    result = fixer.fix_all_bounds_issues()
    
    # Validate the fixes
    fixer.validate_fix_success()
    
    return result

def check_ai_fin_fcst_01319():
    """Check the specific forecast mentioned in the validation checklist"""
    
    print("🔍 Checking AI-FIN-FCST-01319 (from validation checklist)")
    print("=" * 55)
    
    try:
        forecast = frappe.get_doc("AI Financial Forecast", "AI-FIN-FCST-01319")
        
        print(f"✅ Forecast found!")
        print(f"   Company: {forecast.company}")
        print(f"   Account: {forecast.account}")
        print(f"   Type: {forecast.forecast_type}")
        print(f"   Created: {forecast.creation}")
        print()
        
        print("📊 Current Values:")
        print(f"   Predicted Amount: ₹{forecast.predicted_amount:,.2f}")
        print(f"   Upper Bound: ₹{forecast.upper_bound:,.2f}")
        print(f"   Lower Bound: ₹{forecast.lower_bound:,.2f}")
        print(f"   Confidence: {forecast.confidence_score}%")
        print()
        
        # Check the specific issue
        if forecast.upper_bound <= forecast.lower_bound:
            print("🚨 CONFIRMED: Critical bounds issue exists!")
            print(f"   Upper (₹{forecast.upper_bound:,.2f}) ≤ Lower (₹{forecast.lower_bound:,.2f})")
            print(f"   Error margin: ₹{forecast.lower_bound - forecast.upper_bound:,.2f}")
            print()
            print("💡 Ready to fix? Run: fix_specific_forecast('AI-FIN-FCST-01319')")
        else:
            print("✅ Bounds are correct - issue may have been fixed already")
        
        return True
        
    except frappe.DoesNotExistError:
        print("❌ Forecast AI-FIN-FCST-01319 not found")
        print("   It may have been deleted or renamed")
        return False
    except Exception as e:
        print(f"❌ Error checking forecast: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚨 AI Financial Forecast Emergency Fix Script")
    print("=" * 50)
    print()
    print("Available functions:")
    print("• run_emergency_diagnostics() - Check all forecasts")
    print("• fix_specific_forecast(id) - Fix one forecast")
    print("• fix_all_bounds_issues() - Fix all bounds errors")
    print("• check_ai_fin_fcst_01319() - Check the specific issue")
    print()
    print("Example usage:")
    print("bench --site your-site execute ai_inventory.validation.emergency_fix.run_emergency_diagnostics")
