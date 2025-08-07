#!/usr/bin/env python3
"""
Quick Balance Check for AI-FIN-FCST-01319
=========================================

This script performs a quick balance validation for the specific forecast
mentioned in your validation checklist.
"""

import frappe
import json
from datetime import datetime

def quick_balance_check():
    """Quick balance check for AI-FIN-FCST-01319"""
    
    forecast_id = "AI-FIN-FCST-01319"
    
    print(f"\n🔍 Quick Balance Check for {forecast_id}")
    print("=" * 50)
    
    try:
        # Get the forecast
        forecast = frappe.get_doc("AI Financial Forecast", forecast_id)
        
        print(f"📋 Forecast Details:")
        print(f"   Company: {forecast.company}")
        print(f"   Account: {forecast.account}")
        print(f"   Type: {forecast.forecast_type}")
        print(f"   Predicted Amount: ₹{forecast.predicted_amount:,.2f}")
        print(f"   Confidence: {forecast.confidence_score}%")
        
        # Check current balance
        print(f"\n💰 Balance Analysis:")
        
        # Method 1: Get from GL Entries
        gl_balance_query = """
            SELECT 
                COALESCE(SUM(CASE 
                    WHEN acc.root_type IN ('Asset', 'Expense') 
                    THEN gl.debit - gl.credit 
                    ELSE gl.credit - gl.debit 
                END), 0) as balance,
                COUNT(*) as entries,
                MAX(gl.posting_date) as last_date
            FROM `tabGL Entry` gl
            LEFT JOIN `tabAccount` acc ON gl.account = acc.name
            WHERE gl.account = %s 
            AND gl.is_cancelled = 0 
            AND gl.docstatus = 1
        """
        
        gl_result = frappe.db.sql(gl_balance_query, (forecast.account,), as_dict=True)[0]
        calculated_balance = gl_result["balance"]
        
        print(f"   Calculated Balance (GL): ₹{calculated_balance:,.2f}")
        print(f"   GL Entries Count: {gl_result['entries']}")
        print(f"   Last Transaction: {gl_result['last_date']}")
        
        # Check if forecast has current_balance field
        current_balance = getattr(forecast, 'current_balance', None)
        if current_balance:
            print(f"   Stored Balance: ₹{current_balance:,.2f}")
            balance_as_of = getattr(forecast, 'balance_as_of_date', None)
            if balance_as_of:
                print(f"   Balance As Of: {balance_as_of}")
        else:
            print(f"   Stored Balance: Not available")
            
        # Use calculated balance as primary
        primary_balance = current_balance if current_balance else calculated_balance
        
        # Variance Analysis
        print(f"\n📊 Variance Analysis:")
        
        if forecast.predicted_amount:
            variance = primary_balance - forecast.predicted_amount
            variance_pct = (variance / abs(forecast.predicted_amount)) * 100 if forecast.predicted_amount != 0 else 0
            
            print(f"   Absolute Variance: ₹{variance:,.2f}")
            print(f"   Percentage Variance: {variance_pct:.1f}%")
            
            # Categorize variance
            if abs(variance_pct) <= 5:
                variance_status = "✅ Excellent"
            elif abs(variance_pct) <= 15:
                variance_status = "✅ Good"
            elif abs(variance_pct) <= 30:
                variance_status = "⚠️ Acceptable"
            elif abs(variance_pct) <= 50:
                variance_status = "⚠️ Poor"
            else:
                variance_status = "🚨 Critical"
                
            print(f"   Variance Status: {variance_status}")
        
        # Bounds Check
        print(f"\n🎯 Bounds Validation:")
        
        if forecast.upper_bound and forecast.lower_bound:
            if forecast.upper_bound > forecast.lower_bound:
                print(f"   ✅ Bounds Logic: VALID")
                print(f"   Upper Bound: ₹{forecast.upper_bound:,.2f}")
                print(f"   Lower Bound: ₹{forecast.lower_bound:,.2f}")
                
                # Check if current balance falls within bounds
                if forecast.lower_bound <= primary_balance <= forecast.upper_bound:
                    print(f"   ✅ Current balance within bounds")
                else:
                    print(f"   ⚠️ Current balance outside bounds")
            else:
                print(f"   🚨 Bounds Logic: INVALID (Upper ≤ Lower)")
                print(f"   Upper Bound: ₹{forecast.upper_bound:,.2f}")
                print(f"   Lower Bound: ₹{forecast.lower_bound:,.2f}")
        else:
            print(f"   ⚠️ Bounds not set")
        
        # Data Quality Check
        print(f"\n📈 Data Quality Assessment:")
        
        quality_score = getattr(forecast, 'data_quality_score', None)
        if quality_score:
            print(f"   Quality Score: {quality_score}%")
            if quality_score >= 80:
                print(f"   Quality Status: ✅ Good")
            elif quality_score >= 60:
                print(f"   Quality Status: ⚠️ Fair")
            else:
                print(f"   Quality Status: 🚨 Poor")
        else:
            print(f"   Quality Score: Not calculated")
        
        # Alert Status
        print(f"\n🚨 Alert Status:")
        
        if forecast.forecast_alert:
            print(f"   Alert Active: 🚨 YES")
            print(f"   Risk Category: {forecast.risk_category}")
            if forecast.volatility_score:
                print(f"   Volatility Score: {forecast.volatility_score}%")
        else:
            print(f"   Alert Active: ✅ NO")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        recommendations = []
        
        if current_balance is None:
            recommendations.append("Update current balance field")
            
        if forecast.upper_bound and forecast.lower_bound and forecast.upper_bound <= forecast.lower_bound:
            recommendations.append("🚨 CRITICAL: Fix bounds calculation error")
            
        if abs(variance_pct) > 30:
            recommendations.append("Review forecasting model parameters")
            
        if primary_balance < 0 and forecast.account_type in ["Bank", "Cash"]:
            recommendations.append("🚨 Check negative balance situation")
            
        if not recommendations:
            recommendations.append("✅ No critical issues found")
            
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Summary
        print(f"\n📝 Summary:")
        print(f"   Forecast ID: {forecast_id}")
        print(f"   Current Balance: ₹{primary_balance:,.2f}")
        print(f"   Predicted Amount: ₹{forecast.predicted_amount:,.2f}")
        print(f"   Confidence Score: {forecast.confidence_score}%")
        if forecast.predicted_amount:
            print(f"   Accuracy: {variance_status}")
        print(f"   Status: {'🚨 Needs Attention' if recommendations and '🚨' in str(recommendations) else '✅ Good'}")
        
        return {
            "forecast_id": forecast_id,
            "current_balance": float(primary_balance),
            "predicted_amount": forecast.predicted_amount,
            "variance_percentage": variance_pct if 'variance_pct' in locals() else None,
            "bounds_valid": forecast.upper_bound > forecast.lower_bound if forecast.upper_bound and forecast.lower_bound else None,
            "recommendations": recommendations,
            "status": "needs_attention" if recommendations and any("🚨" in str(r) for r in recommendations) else "good"
        }
        
    except Exception as e:
        print(f"❌ Error checking forecast: {str(e)}")
        return {"success": False, "error": str(e)}

def update_forecast_balance():
    """Update the current balance for AI-FIN-FCST-01319"""
    
    forecast_id = "AI-FIN-FCST-01319"
    
    try:
        forecast = frappe.get_doc("AI Financial Forecast", forecast_id)
        
        # Call the new balance update method
        if hasattr(forecast, 'update_current_balance_data'):
            result = forecast.update_current_balance_data()
            
            if result.get("success"):
                forecast.save()
                print(f"✅ Balance updated: ₹{result['balance']:,.2f}")
                return result
            else:
                print(f"❌ Balance update failed: {result.get('message', 'Unknown error')}")
                return result
        else:
            print(f"❌ Balance update method not available")
            return {"success": False, "message": "Method not available"}
            
    except Exception as e:
        print(f"❌ Error updating balance: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Run the balance check
    result = quick_balance_check()
    
    # Ask if user wants to update balance
    if result.get("status") != "good":
        print(f"\n🔄 Would you like to update the current balance? (This will call the new balance update function)")
        print(f"   Running balance update...")
        update_result = update_forecast_balance()
        
        if update_result.get("success"):
            print(f"\n✅ Balance update completed. Running check again...")
            quick_balance_check()
        else:
            print(f"\n❌ Balance update failed: {update_result.get('message', 'Unknown error')}")
