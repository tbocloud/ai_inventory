#!/usr/bin/env python3
"""
Current Balance Manager for AI Financial Forecast
================================================

This module provides comprehensive current balance management functions
including real-time balance retrieval, validation, and monitoring.

Usage:
    python current_balance_manager.py --forecast-id AI-FIN-FCST-01319
    python current_balance_manager.py --account "Cash - ABC" --company "ABC Company"
    python current_balance_manager.py --all-forecasts
"""

import frappe
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CurrentBalanceManager:
    """Manages current balance operations for AI Financial Forecasts"""
    
    def __init__(self):
        self.setup_frappe()
    
    def setup_frappe(self):
        """Initialize Frappe context"""
        try:
            if not frappe.db:
                frappe.init(site="your-site-name")  # Replace with your site
                frappe.connect()
        except:
            pass
    
    def get_account_balance(self, account: str, company: str = None) -> Dict:
        """
        Get current balance for a specific account
        
        Args:
            account: Account name
            company: Company filter (optional)
            
        Returns:
            Dict with balance information
        """
        try:
            # Build GL Entry query
            conditions = ["gl.account = %(account)s", "gl.is_cancelled = 0", "gl.docstatus = 1"]
            values = {"account": account}
            
            if company:
                conditions.append("gl.company = %(company)s")
                values["company"] = company
            
            # Get account type for proper balance calculation
            account_info = frappe.db.get_value("Account", account, 
                                              ["account_type", "root_type", "account_currency"], 
                                              as_dict=True)
            
            if not account_info:
                return {"success": False, "error": f"Account {account} not found"}
            
            # Calculate balance based on account type
            balance_query = f"""
                SELECT 
                    COALESCE(SUM(CASE 
                        WHEN acc.root_type IN ('Asset', 'Expense') 
                        THEN gl.debit - gl.credit 
                        ELSE gl.credit - gl.debit 
                    END), 0) as balance,
                    COUNT(*) as entry_count,
                    MAX(gl.posting_date) as last_transaction_date
                FROM `tabGL Entry` gl
                LEFT JOIN `tabAccount` acc ON gl.account = acc.name
                WHERE {' AND '.join(conditions)}
            """
            
            result = frappe.db.sql(balance_query, values, as_dict=True)[0]
            
            return {
                "success": True,
                "account": account,
                "company": company,
                "current_balance": float(result["balance"]),
                "account_type": account_info["account_type"],
                "root_type": account_info["root_type"],
                "currency": account_info["account_currency"] or "INR",
                "entry_count": result["entry_count"],
                "last_transaction_date": result["last_transaction_date"],
                "as_of_date": frappe.utils.now(),
                "calculation_method": "GL Entry Aggregation"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "account": account,
                "company": company
            }
    
    def get_forecast_balance_summary(self, forecast_id: str) -> Dict:
        """Get balance summary for a specific forecast"""
        try:
            # Get forecast document
            forecast = frappe.get_doc("AI Financial Forecast", forecast_id)
            
            # Get current balance
            balance_info = self.get_account_balance(forecast.account, forecast.company)
            
            if not balance_info["success"]:
                return balance_info
            
            current_balance = balance_info["current_balance"]
            
            # Calculate metrics
            summary = {
                "forecast_info": {
                    "forecast_id": forecast_id,
                    "account": forecast.account,
                    "company": forecast.company,
                    "forecast_type": forecast.forecast_type,
                    "predicted_amount": forecast.predicted_amount,
                    "confidence_score": forecast.confidence_score
                },
                "balance_info": balance_info,
                "variance_analysis": {},
                "alerts": [],
                "recommendations": []
            }
            
            # Calculate variance
            if forecast.predicted_amount:
                variance = current_balance - forecast.predicted_amount
                variance_pct = (variance / abs(forecast.predicted_amount)) * 100 if forecast.predicted_amount != 0 else 0
                
                summary["variance_analysis"] = {
                    "absolute_variance": variance,
                    "percentage_variance": variance_pct,
                    "variance_category": self.categorize_variance(variance_pct),
                    "accuracy_score": max(0, 100 - abs(variance_pct))
                }
                
                # Generate alerts based on variance
                if abs(variance_pct) > 50:
                    summary["alerts"].append({
                        "type": "critical",
                        "message": f"Large variance: {variance_pct:.1f}% difference from prediction"
                    })
                elif abs(variance_pct) > 25:
                    summary["alerts"].append({
                        "type": "warning",
                        "message": f"Moderate variance: {variance_pct:.1f}% difference from prediction"
                    })
                
                # Generate recommendations
                if abs(variance_pct) > 30:
                    summary["recommendations"].append("Review forecasting model parameters")
                    summary["recommendations"].append("Check for recent unusual transactions")
                
                if current_balance < 0 and forecast.account_type in ["Bank", "Cash"]:
                    summary["alerts"].append({
                        "type": "critical",
                        "message": "Negative balance detected for cash/bank account"
                    })
                    summary["recommendations"].append("Review overdraft limits and cash flow")
            
            return summary
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def categorize_variance(self, variance_pct: float) -> str:
        """Categorize variance percentage"""
        abs_variance = abs(variance_pct)
        
        if abs_variance <= 5:
            return "Excellent"
        elif abs_variance <= 15:
            return "Good"
        elif abs_variance <= 30:
            return "Acceptable"
        elif abs_variance <= 50:
            return "Poor"
        else:
            return "Critical"
    
    def update_all_forecast_balances(self, company: str = None) -> Dict:
        """Update current balances for all forecasts"""
        try:
            filters = {}
            if company:
                filters["company"] = company
            
            # Get all active forecasts
            forecasts = frappe.get_all("AI Financial Forecast",
                                     filters=filters,
                                     fields=["name", "account", "company"])
            
            results = {
                "total_processed": 0,
                "successful_updates": 0,
                "failed_updates": 0,
                "errors": [],
                "summary": []
            }
            
            for forecast in forecasts:
                try:
                    # Get current balance
                    balance_info = self.get_account_balance(forecast.account, forecast.company)
                    
                    if balance_info["success"]:
                        # Update forecast document
                        forecast_doc = frappe.get_doc("AI Financial Forecast", forecast.name)
                        forecast_doc.current_balance = balance_info["current_balance"]
                        forecast_doc.balance_as_of_date = balance_info["as_of_date"]
                        forecast_doc.balance_currency = balance_info["currency"]
                        
                        # Calculate balance-to-prediction ratio
                        if forecast_doc.predicted_amount and forecast_doc.predicted_amount != 0:
                            forecast_doc.balance_prediction_ratio = (
                                balance_info["current_balance"] / forecast_doc.predicted_amount
                            ) * 100
                        
                        forecast_doc.save(ignore_permissions=True)
                        results["successful_updates"] += 1
                        
                        results["summary"].append({
                            "forecast_id": forecast.name,
                            "account": forecast.account,
                            "balance": balance_info["current_balance"],
                            "status": "updated"
                        })
                    else:
                        results["failed_updates"] += 1
                        results["errors"].append({
                            "forecast_id": forecast.name,
                            "error": balance_info.get("error", "Unknown error")
                        })
                        
                    results["total_processed"] += 1
                    
                except Exception as e:
                    results["failed_updates"] += 1
                    results["errors"].append({
                        "forecast_id": forecast.name,
                        "error": str(e)
                    })
                    results["total_processed"] += 1
            
            frappe.db.commit()
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_balance_alert_report(self, company: str = None) -> Dict:
        """Generate comprehensive balance alert report"""
        try:
            filters = {"forecast_alert": 1}
            if company:
                filters["company"] = company
            
            # Get forecasts with alerts
            forecasts = frappe.get_all("AI Financial Forecast",
                                     filters=filters,
                                     fields=["name", "account", "company", "predicted_amount", 
                                           "confidence_score", "risk_category"])
            
            report = {
                "summary": {
                    "total_alerts": len(forecasts),
                    "critical_alerts": 0,
                    "warning_alerts": 0,
                    "companies_affected": set(),
                    "total_exposure": 0
                },
                "alerts": [],
                "recommendations": {
                    "immediate_actions": [],
                    "monitoring_suggestions": [],
                    "process_improvements": []
                }
            }
            
            for forecast in forecasts:
                try:
                    # Get current balance and analysis
                    balance_summary = self.get_forecast_balance_summary(forecast.name)
                    
                    if balance_summary.get("balance_info", {}).get("success"):
                        alert_info = {
                            "forecast_id": forecast.name,
                            "account": forecast.account,
                            "company": forecast.company,
                            "current_balance": balance_summary["balance_info"]["current_balance"],
                            "predicted_amount": forecast.predicted_amount,
                            "variance_analysis": balance_summary.get("variance_analysis", {}),
                            "alerts": balance_summary.get("alerts", []),
                            "risk_category": forecast.risk_category
                        }
                        
                        report["alerts"].append(alert_info)
                        report["summary"]["companies_affected"].add(forecast.company)
                        report["summary"]["total_exposure"] += abs(balance_summary["balance_info"]["current_balance"])
                        
                        # Count alert types
                        for alert in balance_summary.get("alerts", []):
                            if alert["type"] == "critical":
                                report["summary"]["critical_alerts"] += 1
                            else:
                                report["summary"]["warning_alerts"] += 1
                
                except Exception as e:
                    continue
            
            # Convert set to list for JSON serialization
            report["summary"]["companies_affected"] = list(report["summary"]["companies_affected"])
            
            # Generate recommendations
            if report["summary"]["critical_alerts"] > 0:
                report["recommendations"]["immediate_actions"].append(
                    f"Review {report['summary']['critical_alerts']} critical balance alerts"
                )
                report["recommendations"]["immediate_actions"].append(
                    "Verify negative balances and overdraft situations"
                )
            
            if report["summary"]["warning_alerts"] > 3:
                report["recommendations"]["monitoring_suggestions"].append(
                    "Increase balance monitoring frequency"
                )
                report["recommendations"]["process_improvements"].append(
                    "Review forecasting model accuracy"
                )
            
            return report
            
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Main CLI function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Current Balance Manager for AI Financial Forecasts")
    parser.add_argument("--forecast-id", help="Specific forecast ID to check")
    parser.add_argument("--account", help="Account name to check balance")
    parser.add_argument("--company", help="Company filter")
    parser.add_argument("--all-forecasts", action="store_true", help="Update all forecast balances")
    parser.add_argument("--alert-report", action="store_true", help="Generate balance alert report")
    
    args = parser.parse_args()
    
    manager = CurrentBalanceManager()
    
    if args.forecast_id:
        print(f"\n🔍 Checking balance for forecast: {args.forecast_id}")
        result = manager.get_forecast_balance_summary(args.forecast_id)
        print(json.dumps(result, indent=2, default=str))
        
    elif args.account:
        print(f"\n💰 Getting current balance for account: {args.account}")
        result = manager.get_account_balance(args.account, args.company)
        print(json.dumps(result, indent=2, default=str))
        
    elif args.all_forecasts:
        print(f"\n🔄 Updating all forecast balances...")
        result = manager.update_all_forecast_balances(args.company)
        print(f"✅ Processed: {result['total_processed']}")
        print(f"✅ Successful: {result['successful_updates']}")
        print(f"❌ Failed: {result['failed_updates']}")
        
        if result['errors']:
            print("\n❌ Errors:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  - {error['forecast_id']}: {error['error']}")
                
    elif args.alert_report:
        print(f"\n📊 Generating balance alert report...")
        result = manager.generate_balance_alert_report(args.company)
        print(json.dumps(result, indent=2, default=str))
        
    else:
        print("❌ Please specify an action. Use --help for options.")

@frappe.whitelist()
def update_balance(company, account):
    """
    Update balance for a specific account - callable from web interface
    
    Args:
        company: Company name
        account: Account name
        
    Returns:
        Dict with update result
    """
    try:
        manager = CurrentBalanceManager()
        result = manager.get_account_balance(account, company)
        
        if result.get("success"):
            # Get current balance
            new_balance = result.get("current_balance", 0)
            
            # Update any related forecasts
            forecasts = frappe.get_all("AI Financial Forecast",
                                     filters={
                                         "company": company,
                                         "account": account,
                                         "docstatus": ["!=", 2]
                                     },
                                     fields=["name"])
            
            updated_count = 0
            for forecast in forecasts:
                try:
                    frappe.db.set_value("AI Financial Forecast", 
                                      forecast.name, 
                                      "current_balance", 
                                      new_balance)
                    updated_count += 1
                except Exception:
                    pass
            
            frappe.db.commit()
            
            return {
                "success": True,
                "new_balance": new_balance,
                "updated_forecasts": updated_count,
                "message": f"Balance updated successfully for {account}"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to get account balance")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    main()
