# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

class AIFinancialForecast(Document):
    """Enhanced AI Financial Forecast Document Controller"""
    
    def validate(self):
        """Validate forecast data before saving"""
        self.validate_forecast_type()
        self.validate_dates()
        self.validate_confidence_score()
        self.validate_amounts()
        self.set_account_details()
        self.set_currency()
        
        # Add current balance validation
        self.validate_current_balance()
    
    def set_currency(self):
        """Set currency based on account, company, or system default"""
        if not self.currency:
            # Priority: Account Currency > Company Default Currency > System Default
            if self.account:
                account_currency = frappe.db.get_value("Account", self.account, "account_currency")
                if account_currency:
                    self.currency = account_currency
                    return
            
            if self.company:
                company_currency = frappe.db.get_value("Company", self.company, "default_currency")
                if company_currency:
                    self.currency = company_currency
                    return
            
            # Fallback to system default or INR
            try:
                from erpnext import get_default_currency
                self.currency = get_default_currency()
            except:
                # If ERPNext's get_default_currency is not available, use INR as fallback
                self.currency = frappe.db.get_single_value("System Settings", "currency") or "INR"
    
    @frappe.whitelist()
    def get_current_balance(self):
        """Get real-time current balance from account"""
        try:
            if not self.account:
                return {"success": False, "message": "No account specified"}
            
            # Method 1: Calculate from GL Entries
            balance_query = """
                SELECT 
                    COALESCE(SUM(CASE WHEN account_type IN ('Asset', 'Expense') 
                                     THEN debit - credit 
                                     ELSE credit - debit END), 0) as balance
                FROM `tabGL Entry` gl
                LEFT JOIN `tabAccount` acc ON gl.account = acc.name
                WHERE gl.account = %s 
                AND gl.is_cancelled = 0
                AND gl.docstatus = 1
            """
            
            balance_result = frappe.db.sql(balance_query, (self.account,), as_dict=True)
            calculated_balance = balance_result[0]["balance"] if balance_result else 0
            
            # Method 2: Try to get from Account Balance field if it exists
            account_balance = 0
            try:
                account_doc = frappe.get_doc("Account", self.account)
                if hasattr(account_doc, 'account_balance'):
                    account_balance = account_doc.account_balance or 0
            except:
                pass
            
            # Use the more recent/accurate balance
            current_balance = account_balance if account_balance != 0 else calculated_balance
            
            return {
                "success": True,
                "current_balance": float(current_balance),
                "calculated_balance": float(calculated_balance),
                "account_balance": float(account_balance),
                "account": self.account,
                "as_of_date": frappe.utils.now(),
                "currency": self.currency or frappe.db.get_value("Account", self.account, "account_currency") or "INR"
            }
            
        except Exception as e:
            frappe.log_error(f"Current balance retrieval error for {self.account}: {str(e)}")
            return {
                "success": False, 
                "error": str(e),
                "message": "Failed to retrieve current balance"
            }
    
    @frappe.whitelist()
    def update_current_balance_data(self):
        """Update current balance data in the forecast"""
        try:
            balance_info = self.get_current_balance()
            
            if balance_info.get("success"):
                self.current_balance = balance_info["current_balance"]
                self.balance_as_of_date = balance_info["as_of_date"]
                self.balance_currency = self.currency or balance_info["currency"]
                
                # Calculate balance-to-prediction ratio
                if self.predicted_amount and self.predicted_amount != 0:
                    self.balance_prediction_ratio = (self.current_balance / self.predicted_amount) * 100
                
                return {
                    "success": True,
                    "balance": self.current_balance,
                    "message": "Current balance updated successfully"
                }
            else:
                return balance_info
                
        except Exception as e:
            frappe.log_error(f"Balance update error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def validate_current_balance(self):
        """Validate current balance accuracy and reasonableness"""
        try:
            balance_info = self.get_current_balance()
            
            if not balance_info.get("success"):
                frappe.msgprint(
                    f"⚠️ Warning: Could not retrieve current balance for account {self.account}",
                    alert=True
                )
                return
            
            current_balance = balance_info["current_balance"]
            calculated_balance = balance_info["calculated_balance"]
            account_balance = balance_info["account_balance"]
            
            # Check for balance variance between sources
            if account_balance != 0 and calculated_balance != 0:
                variance = abs(account_balance - calculated_balance)
                variance_pct = (variance / abs(account_balance)) * 100 if account_balance != 0 else 0
                
                if variance > 1000 or variance_pct > 5:  # More than ₹1000 or 5% difference
                    frappe.msgprint(
                        f"💰 Balance Variance Detected: "
                        f"Account Balance=₹{account_balance:,.2f}, "
                        f"Calculated=₹{calculated_balance:,.2f}, "
                        f"Variance=₹{variance:,.2f} ({variance_pct:.1f}%)",
                        alert=True
                    )
            
            # Validate prediction vs current balance reasonableness
            if self.predicted_amount and current_balance != 0:
                prediction_variance = abs(self.predicted_amount - current_balance)
                prediction_variance_pct = (prediction_variance / abs(current_balance)) * 100
                
                # Flag if prediction is wildly different from current balance
                if prediction_variance_pct > 200:  # More than 200% difference
                    frappe.msgprint(
                        f"📊 Large Prediction Variance: "
                        f"Current=₹{current_balance:,.2f}, "
                        f"Predicted=₹{self.predicted_amount:,.2f}, "
                        f"Variance={prediction_variance_pct:.1f}%. "
                        f"Please verify forecast parameters.",
                        alert=True
                    )
            
            # Check for negative balances where inappropriate
            if current_balance < 0 and self.account_type in ["Bank", "Cash", "Asset"]:
                frappe.msgprint(
                    f"🚨 Negative balance detected for {self.account_type} account: "
                    f"₹{current_balance:,.2f}. This may indicate an overdraft or data error.",
                    alert=True
                )
            
            return {
                "validated": True,
                "current_balance": current_balance,
                "variance_check": "passed" if variance_pct <= 5 else "warning"
            }
            
        except Exception as e:
            frappe.log_error(f"Balance validation error: {str(e)}")
            return {"validated": False, "error": str(e)}
    
    @frappe.whitelist()
    def fetch_balance_from_external_api(self, api_provider="bank"):
        """Fetch current balance from external banking API"""
        try:
            # This is a placeholder for external API integration
            # You would integrate with Plaid, Open Banking, or bank-specific APIs
            
            api_config = frappe.get_single("Bank Integration Settings")
            
            if not api_config or not api_config.enabled:
                return {
                    "success": False,
                    "message": "External API integration not configured"
                }
            
            # Placeholder for actual API call
            # In real implementation, you would:
            # 1. Authenticate with the bank API
            # 2. Fetch account balance
            # 3. Handle rate limiting and errors
            # 4. Return standardized response
            
            return {
                "success": False,
                "message": "External API integration not yet implemented",
                "note": "This function is ready for bank API integration"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @frappe.whitelist()
    def track_balance_history(self):
        """Track balance changes over time for trend analysis"""
        try:
            balance_info = self.get_current_balance()
            
            if not balance_info.get("success"):
                return {"success": False, "message": "Could not retrieve current balance"}
            
            # Create balance history record
            history_record = {
                "doctype": "Balance History",  # You'd need to create this DocType
                "account": self.account,
                "company": self.company,
                "balance_amount": balance_info["current_balance"],
                "balance_date": frappe.utils.nowdate(),
                "balance_time": frappe.utils.nowtime(),
                "source": "AI Financial Forecast",
                "forecast_reference": self.name
            }
            
            # Check if Balance History DocType exists
            if "Balance History" in frappe.get_all("DocType", pluck="name"):
                balance_doc = frappe.get_doc(history_record)
                balance_doc.insert(ignore_permissions=True)
                frappe.db.commit()
                
                return {
                    "success": True,
                    "message": "Balance history recorded",
                    "balance": balance_info["current_balance"]
                }
            else:
                # Store in forecast log instead
                frappe.get_doc({
                    "doctype": "AI Forecast Log",
                    "forecast_id": self.name,
                    "action": "Balance Tracked",
                    "details": f"Balance: ₹{balance_info['current_balance']:,.2f} for {self.account}",
                    "user": frappe.session.user
                }).insert(ignore_permissions=True)
                
                return {
                    "success": True,
                    "message": "Balance logged in forecast history",
                    "balance": balance_info["current_balance"]
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @frappe.whitelist()
    def check_balance_alerts(self):
        """Check for low balance or unusual balance changes"""
        try:
            balance_info = self.get_current_balance()
            
            if not balance_info.get("success"):
                return {"success": False, "message": "Could not check balance"}
            
            current_balance = balance_info["current_balance"]
            alerts = []
            
            # Get alert thresholds from AI Financial Settings with safe fallbacks
            def _get_single_safe(doctype: str, field: str):
                try:
                    return frappe.db.get_single_value(doctype, field)
                except Exception:
                    return None

            # Read thresholds from AI Financial Settings; fallback to sane defaults only
            low_balance_threshold = (
                _get_single_safe("AI Financial Settings", "forecast_trigger_threshold")
                or 10000
            )
            critical_balance_threshold = (
                _get_single_safe("AI Financial Settings", "critical_threshold")
                or 1000
            )
            
            # Check for low balance
            if current_balance < critical_balance_threshold:
                alerts.append({
                    "type": "critical",
                    "message": f"Critical low balance: ₹{current_balance:,.2f} (threshold: ₹{critical_balance_threshold:,.2f})",
                    "action_required": True
                })
            elif current_balance < low_balance_threshold:
                alerts.append({
                    "type": "warning",
                    "message": f"Low balance warning: ₹{current_balance:,.2f} (threshold: ₹{low_balance_threshold:,.2f})",
                    "action_required": False
                })
            
            # Check for negative balance
            if current_balance < 0:
                alerts.append({
                    "type": "critical",
                    "message": f"Negative balance detected: ₹{current_balance:,.2f}",
                    "action_required": True
                })
            
            # Check for unusual balance changes (compared to prediction)
            if self.predicted_amount:
                variance = abs(current_balance - self.predicted_amount)
                variance_pct = (variance / abs(self.predicted_amount)) * 100 if self.predicted_amount != 0 else 0
                
                if variance_pct > 50:  # More than 50% variance
                    alerts.append({
                        "type": "info",
                        "message": f"Large variance from prediction: Current=₹{current_balance:,.2f}, Predicted=₹{self.predicted_amount:,.2f} ({variance_pct:.1f}% difference)",
                        "action_required": False
                    })
            
            # Send alerts if any
            alert_records_created = []
            if alerts:
                for alert in alerts:
                    # Show immediate message
                    if alert["type"] == "critical":
                        frappe.msgprint(f"🚨 {alert['message']}", alert=True)
                    elif alert["type"] == "warning":
                        frappe.msgprint(f"⚠️ {alert['message']}", alert=True)
                    else:
                        frappe.msgprint(f"ℹ️ {alert['message']}", alert=True)
                    
                    # Create AI Financial Alert record
                    try:
                        from ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert import create_financial_alert
                        
                        alert_data = {
                            "company": self.company,
                            "title": f"{alert['type'].title()} Balance Alert",
                            "message": alert['message'],
                            "priority": "Critical" if alert["type"] == "critical" else "High" if alert["type"] == "warning" else "Medium",
                            "alert_type": "Balance Monitoring",
                            "threshold_value": low_balance_threshold if alert["type"] in ["critical", "warning"] else None,
                            "actual_value": current_balance,
                            "related_forecast": self.name,
                            "forecast_type": self.forecast_type,
                            "confidence_level": self.confidence_score,
                            "recommended_action": "Review cash flow and take appropriate action" if alert.get("action_required") else "Monitor situation"
                        }
                        
                        alert_result = create_financial_alert(alert_data)
                        if alert_result.get("success"):
                            alert_records_created.append(alert_result.get("alert_id"))
                            
                    except Exception as e:
                        frappe.log_error(f"Failed to create alert record: {str(e)}")
            
            return {
                "success": True,
                "alerts": alerts,
                "current_balance": current_balance,
                "alert_count": len(alerts),
                "alert_records_created": alert_records_created
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_forecast_type(self):
        """Validate forecast type is in allowed list"""
        valid_types = ["Cash Flow", "Revenue", "Expense", "Balance Sheet", "P&L"]
        if self.forecast_type not in valid_types:
            frappe.throw(f"Invalid forecast type. Must be one of: {', '.join(valid_types)}")
    
    def validate_dates(self):
        """Validate forecast dates"""
        if self.forecast_end_date and self.forecast_start_date:
            if self.forecast_end_date <= self.forecast_start_date:
                frappe.throw("Forecast end date must be after start date")
        
        # Auto-calculate end date if not provided
        if self.forecast_start_date and self.forecast_period_days and not self.forecast_end_date:
            start_date = frappe.utils.getdate(self.forecast_start_date)
            self.forecast_end_date = start_date + timedelta(days=self.forecast_period_days)
    
    def validate_confidence_score(self):
        """Validate confidence score is within bounds"""
        if self.confidence_score and not (0 <= self.confidence_score <= 100):
            frappe.throw("Confidence score must be between 0 and 100")
    
    def validate_amounts(self):
        """Validate amount fields - Enhanced validation for critical bounds issue"""
        
        # Critical Issue Fix: Upper bound < Lower bound validation
        if self.upper_bound and self.lower_bound:
            if self.upper_bound <= self.lower_bound:
                frappe.throw(
                    f"🚨 CRITICAL ERROR: Upper bound (₹{self.upper_bound:,.2f}) "
                    f"must be greater than lower bound (₹{self.lower_bound:,.2f}). "
                    f"This indicates a calculation error in the forecasting algorithm."
                )
        
        # Enhanced prediction validation with detailed messages
        if self.predicted_amount:
            if self.upper_bound and self.predicted_amount > self.upper_bound:
                variance_pct = ((self.predicted_amount - self.upper_bound) / self.upper_bound) * 100
                frappe.msgprint(
                    f"⚠️ WARNING: Predicted amount (₹{self.predicted_amount:,.2f}) "
                    f"exceeds upper bound (₹{self.upper_bound:,.2f}) by {variance_pct:.1f}%. "
                    f"Consider reviewing model parameters.",
                    alert=True
                )
            
            if self.lower_bound and self.predicted_amount < self.lower_bound:
                variance_pct = ((self.lower_bound - self.predicted_amount) / self.lower_bound) * 100
                frappe.msgprint(
                    f"⚠️ WARNING: Predicted amount (₹{self.predicted_amount:,.2f}) "
                    f"is below lower bound (₹{self.lower_bound:,.2f}) by {variance_pct:.1f}%. "
                    f"Consider reviewing model parameters.",
                    alert=True
                )
        
        # Additional validation: Check for unrealistic bounds spread
        if self.upper_bound and self.lower_bound and self.predicted_amount:
            bounds_spread = self.upper_bound - self.lower_bound
            prediction_pct = (bounds_spread / abs(self.predicted_amount)) * 100
            
            if prediction_pct > 100:  # Bounds spread > 100% of prediction
                frappe.msgprint(
                    f"📊 NOTICE: Wide prediction range detected. "
                    f"Bounds spread: ₹{bounds_spread:,.2f} ({prediction_pct:.1f}% of prediction). "
                    f"This may indicate high uncertainty in the forecast.",
                    alert=True
                )
        
        # Validate minimum prediction amount
        if self.predicted_amount is not None and self.predicted_amount < 0 and self.forecast_type not in ["Expense", "Cash Flow"]:
            frappe.throw(f"Negative prediction amount not allowed for {self.forecast_type} forecasts")
    
    def set_account_details(self):
        """Set account name and type from linked account"""
        if self.account and not self.account_name:
            account_doc = frappe.get_doc("Account", self.account)
            self.account_name = account_doc.account_name
            self.account_type = account_doc.account_type
            
            # Also fetch and set current balance
            balance_info = self.get_current_balance()
            if balance_info.get("success"):
                self.current_balance = balance_info["current_balance"]
                self.balance_as_of_date = balance_info["as_of_date"]
    
    def before_save(self):
        """Actions before saving"""
        self.set_forecast_accuracy()
        self.set_risk_category()
        self.calculate_volatility_score()
        self.update_trend_direction()
        self.set_alert_status()
        self.calculate_data_quality_score()
        self.validate_forecast_logic()
        
        # Update current balance data
        self.update_current_balance_data()
    
    def set_forecast_accuracy(self):
        """Set forecast accuracy based on confidence score"""
        if not self.confidence_score:
            return
            
        if self.confidence_score >= 80:
            self.forecast_accuracy = "High"
        elif self.confidence_score >= 60:
            self.forecast_accuracy = "Medium"
        else:
            self.forecast_accuracy = "Low"
    
    def set_risk_category(self):
        """Set risk category based on various factors"""
        if not self.confidence_score:
            self.risk_category = "Unknown"
            return
        
        volatility = self.volatility_score or 0
        
        if self.confidence_score >= 75 and volatility <= 30:
            self.risk_category = "Low"
        elif self.confidence_score >= 60 and volatility <= 50:
            self.risk_category = "Medium"
        elif self.confidence_score >= 40:
            self.risk_category = "High"
        else:
            self.risk_category = "Critical"
    
    def calculate_volatility_score(self):
        """Calculate volatility score based on prediction bounds"""
        if not all([self.predicted_amount, self.upper_bound, self.lower_bound]):
            return
        
        if self.predicted_amount == 0:
            self.volatility_score = 100
            return
        
        # Calculate volatility as percentage of prediction range
        range_size = self.upper_bound - self.lower_bound
        volatility = (range_size / abs(self.predicted_amount)) * 100
        self.volatility_score = min(100, max(0, volatility))
    
    def update_trend_direction(self):
        """Update trend direction based on historical comparison"""
        if not self.account:
            return
        
        try:
            # Get last forecast for same account and type
            last_forecast = frappe.get_all("AI Financial Forecast",
                                         filters={
                                             "account": self.account,
                                             "forecast_type": self.forecast_type,
                                             "name": ["!=", self.name],
                                             "creation": ["<", self.creation or frappe.utils.now()]
                                         },
                                         fields=["predicted_amount"],
                                         order_by="creation desc",
                                         limit=1)
            
            if last_forecast and self.predicted_amount:
                last_amount = last_forecast[0].predicted_amount
                if last_amount:
                    change_pct = ((self.predicted_amount - last_amount) / abs(last_amount)) * 100
                    
                    if change_pct > 5:
                        self.trend_direction = "Increasing"
                    elif change_pct < -5:
                        self.trend_direction = "Decreasing"
                    elif abs(change_pct) > 2:
                        self.trend_direction = "Volatile"
                    else:
                        self.trend_direction = "Stable"
                else:
                    self.trend_direction = "Stable"
            else:
                self.trend_direction = "Stable"
                
        except Exception as e:
            frappe.log_error(f"Error updating trend direction: {str(e)}")
            self.trend_direction = "Stable"
    
    def set_alert_status(self):
        """Set forecast alert based on confidence and risk"""
        alert_conditions = [
            self.confidence_score and self.confidence_score < (self.confidence_threshold or 70),
            self.risk_category in ["High", "Critical"],
            self.volatility_score and self.volatility_score > 75
        ]
        
        self.forecast_alert = any(alert_conditions)
    
    def calculate_data_quality_score(self):
        """Calculate data quality score based on completeness and accuracy"""
        
        # Required fields for quality assessment
        required_fields = [
            'company', 'account', 'forecast_type', 'forecast_start_date',
            'predicted_amount', 'confidence_score', 'forecast_period_days'
        ]
        
        optional_fields = [
            'upper_bound', 'lower_bound', 'prediction_model', 
            'seasonal_adjustment', 'account_name', 'account_type'
        ]
        
        # Calculate completeness score
        required_filled = sum(1 for field in required_fields if getattr(self, field, None) is not None)
        optional_filled = sum(1 for field in optional_fields if getattr(self, field, None) is not None)
        
        required_score = (required_filled / len(required_fields)) * 70  # 70% weight for required
        optional_score = (optional_filled / len(optional_fields)) * 30  # 30% weight for optional
        
        base_quality = required_score + optional_score
        
        # Adjust for data accuracy indicators
        accuracy_adjustments = []
        
        # Check for logical consistency
        if self.upper_bound and self.lower_bound and self.upper_bound > self.lower_bound:
            accuracy_adjustments.append(5)  # Bonus for correct bounds
        elif self.upper_bound and self.lower_bound:
            accuracy_adjustments.append(-15)  # Penalty for incorrect bounds
        
        # Check confidence score reasonableness
        if self.confidence_score and 60 <= self.confidence_score <= 95:
            accuracy_adjustments.append(3)  # Bonus for reasonable confidence
        elif self.confidence_score and (self.confidence_score < 30 or self.confidence_score > 99):
            accuracy_adjustments.append(-10)  # Penalty for unreasonable confidence
        
        # Update current balance and check for accuracy
        if self.current_balance and self.predicted_amount:
            balance_variance = abs(self.current_balance - self.predicted_amount)
            balance_variance_pct = (balance_variance / abs(self.current_balance)) * 100 if self.current_balance != 0 else 0
            
            if balance_variance_pct <= 10:  # Within 10% is good
                accuracy_adjustments.append(5)  # Bonus for close prediction
            elif balance_variance_pct <= 25:  # Within 25% is acceptable
                accuracy_adjustments.append(2)
            elif balance_variance_pct > 100:  # More than 100% off
                accuracy_adjustments.append(-10)  # Penalty for way off prediction
        
        # Apply adjustments
        final_quality = base_quality + sum(accuracy_adjustments)
        self.data_quality_score = max(0, min(100, final_quality))
    
    def validate_forecast_logic(self):
        """Comprehensive forecast logic validation"""
        
        validation_issues = []
        
        # Check temporal logic
        if self.forecast_start_date and self.forecast_end_date:
            if frappe.utils.getdate(self.forecast_end_date) <= frappe.utils.getdate(self.forecast_start_date):
                validation_issues.append("Forecast end date must be after start date")
        
        # Check prediction bounds logic (already done in validate_amounts but double-check)
        if self.upper_bound and self.lower_bound and self.upper_bound <= self.lower_bound:
            validation_issues.append("Upper bound must be greater than lower bound")
        
        # Check confidence score logic
        if self.confidence_score:
            if self.confidence_score < 0 or self.confidence_score > 100:
                validation_issues.append("Confidence score must be between 0 and 100")
            elif self.confidence_score < 30:
                validation_issues.append("Extremely low confidence score indicates poor model performance")
        
        # Check forecast period reasonableness
        if self.forecast_period_days:
            if self.forecast_period_days < 1:
                validation_issues.append("Forecast period must be at least 1 day")
            elif self.forecast_period_days > 1825:  # 5 years
                validation_issues.append("Forecast period exceeds 5 years - may be unreliable")
        
        # Check account type consistency
        if self.account and self.forecast_type:
            account_type = frappe.db.get_value("Account", self.account, "account_type")
            if account_type:
                type_compatibility = {
                    "Cash Flow": ["Bank", "Cash", "Receivable", "Payable"],
                    "Revenue": ["Income", "Revenue"],
                    "Expense": ["Expense"],
                    "Balance Sheet": ["Asset", "Liability", "Equity"],
                    "P&L": ["Income", "Expense", "Revenue"]
                }
                
                compatible_types = type_compatibility.get(self.forecast_type, [])
                if compatible_types and account_type not in compatible_types:
                    validation_issues.append(
                        f"Account type '{account_type}' may not be suitable for {self.forecast_type} forecast"
                    )
        
        # Log validation issues but don't block save (use warnings instead)
        if validation_issues:
            self.validation_warnings = json.dumps(validation_issues)
            for issue in validation_issues[:3]:  # Show max 3 warnings
                frappe.msgprint(f"⚠️ Validation Warning: {issue}", alert=True)
    
    def after_insert(self):
        """Actions after inserting new forecast"""
        self.initiate_comprehensive_sync()
        self.log_forecast_creation()
        self.check_alerts()
    
    def on_update(self):
        """Actions on updating forecast"""
        # Only sync if important fields changed
        if self.has_value_changed("predicted_amount") or self.has_value_changed("confidence_score"):
            self.initiate_comprehensive_sync()
        self.check_alerts()
    
    def initiate_comprehensive_sync(self):
        """Initiate comprehensive sync using the sync manager"""
        try:
            # Import sync manager from correct path
            from ai_inventory.ai_inventory.utils.sync_manager import AIFinancialForecastSyncManager
            
            # Create sync manager instance
            sync_manager = AIFinancialForecastSyncManager(self)
            
            # Execute sync in background if enabled
            if self.auto_sync_enabled:
                if self.sync_frequency == "Manual":
                    # Set status to pending for manual sync
                    self.sync_status = "Pending"
                else:
                    # Queue background sync job
                    frappe.enqueue(
                        'ai_inventory.forecasting.sync_manager.trigger_manual_sync',
                        queue='long',
                        timeout=300,
                        forecast_name=self.name,
                        job_name=f"Financial Forecast Sync: {self.name}"
                    )
                    self.sync_status = "Syncing"
            else:
                self.sync_status = "Pending"
                
        except Exception as e:
            frappe.log_error(f"Sync initiation error for {self.name}: {str(e)}")
            self.sync_status = "Failed"
            
    @frappe.whitelist()
    def manual_sync(self):
        """Manually trigger sync operation"""
        try:
            from ai_inventory.forecasting.sync_manager import trigger_manual_sync
            result = trigger_manual_sync(self.name)
            
            # Reload the document to get updated sync status
            self.reload()
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @frappe.whitelist()
    def get_sync_details(self):
        """Get detailed sync information"""
        try:
            # Get sync logs
            sync_logs = frappe.get_all("AI Forecast Sync Log",
                                     filters={"forecast_reference": self.name},
                                     fields=["sync_status", "sync_message", "sync_timestamp", "sync_duration"],
                                     order_by="creation desc",
                                     limit=10)
            
            # Get related records - using safe queries with error handling
            related_records = {}
            
            # Safe query for AI Inventory Forecast
            try:
                related_records["inventory_forecasts"] = frappe.db.count("AI Inventory Forecast", 
                                                                        {"company": self.company})
            except Exception:
                related_records["inventory_forecasts"] = 0
            
            # Safe query for AI Forecast Accuracy
            try:
                related_records["accuracy_records"] = frappe.db.count("AI Forecast Accuracy", 
                                                                     {"forecast_reference": self.name})
            except Exception:
                related_records["accuracy_records"] = 0
            
            # Count other AI Financial Forecasts in same company
            try:
                related_records["other_forecasts"] = frappe.db.count("AI Financial Forecast", 
                                                                    {"company": self.company, 
                                                                     "name": ["!=", self.name]})
            except Exception:
                related_records["other_forecasts"] = 0
            
            # Count sync logs for this forecast
            try:
                related_records["total_sync_logs"] = frappe.db.count("AI Forecast Sync Log", 
                                                                   {"forecast_reference": self.name})
            except Exception:
                related_records["total_sync_logs"] = 0
            
            return {
                "success": True,
                "current_status": self.sync_status,
                "last_sync_date": self.last_sync_date,
                "auto_sync_enabled": self.auto_sync_enabled,
                "sync_frequency": self.sync_frequency,
                "sync_logs": sync_logs,
                "related_records": related_records,
                "sync_summary": {
                    "total_syncs": len(sync_logs),
                    "successful_syncs": len([log for log in sync_logs if log.sync_status == "Completed"]),
                    "failed_syncs": len([log for log in sync_logs if log.sync_status == "Failed"])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @frappe.whitelist()
    def validate_forecast(self):
        """Validate forecast data and provide recommendations"""
        try:
            warnings = []
            recommendations = []
            metrics = {}
            
            # Basic data validation
            if not self.predicted_amount or self.predicted_amount <= 0:
                warnings.append("Predicted amount is missing or invalid")
            
            if not self.confidence_score or self.confidence_score < 50:
                warnings.append("Confidence score is low (below 50%)")
                recommendations.append("Consider reviewing input data quality")
            
            if not self.forecast_start_date or not self.forecast_end_date:
                warnings.append("Forecast date range is incomplete")
            else:
                # Check if forecast period is reasonable
                from datetime import datetime
                start_date = datetime.strptime(str(self.forecast_start_date), "%Y-%m-%d")
                end_date = datetime.strptime(str(self.forecast_end_date), "%Y-%m-%d")
                days_diff = (end_date - start_date).days
                
                if days_diff <= 0:
                    warnings.append("Invalid forecast period: end date before start date")
                elif days_diff > 365:
                    recommendations.append("Long forecast periods may have reduced accuracy")
                elif days_diff < 7:
                    recommendations.append("Very short forecast periods may not capture trends")
            
            # Account validation
            if self.account:
                account_exists = frappe.db.exists("Account", self.account)
                if not account_exists:
                    warnings.append("Selected account does not exist")
                else:
                    # Check account type compatibility
                    account_type = frappe.db.get_value("Account", self.account, "account_type")
                    if self.forecast_type == "Revenue" and account_type not in ["Income Account", "Revenue"]:
                        recommendations.append("Account type may not be suitable for revenue forecasting")
                    elif self.forecast_type == "Expense" and account_type not in ["Expense Account", "Cost of Goods Sold"]:
                        recommendations.append("Account type may not be suitable for expense forecasting")
            
            # Currency validation
            if self.currency:
                currency_exists = frappe.db.exists("Currency", self.currency)
                if not currency_exists:
                    warnings.append("Selected currency is not valid")
            
            # Calculate metrics
            metrics["accuracy"] = f"{self.confidence_score}%"
            metrics["confidence"] = "High" if self.confidence_score > 80 else "Medium" if self.confidence_score > 60 else "Low"
            
            # Data quality assessment
            data_quality_score = 100
            if warnings:
                data_quality_score -= len(warnings) * 15
            if not self.forecast_details:
                data_quality_score -= 10
            if not self.current_balance:
                data_quality_score -= 5
                
            metrics["data_quality"] = f"{max(0, data_quality_score)}%"
            
            # Add recommendations based on data
            if not self.forecast_details:
                recommendations.append("Add forecast details for better analysis")
            
            if self.forecast_type and not self.sync_status:
                recommendations.append("Enable sync to integrate with related forecasts")
            
            return {
                "success": True,
                "warnings": warnings,
                "recommendations": recommendations,
                "metrics": metrics,
                "overall_score": max(0, data_quality_score)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def sync_to_cashflow_forecast(self):
        """Sync to AI Cashflow Forecast"""
        try:
            # Check if cashflow forecast exists
            existing = frappe.get_all("AI Cashflow Forecast",
                                    filters={
                                        "company": self.company,
                                        "forecast_date": self.forecast_start_date
                                    },
                                    limit=1)
            
            if existing:
                # Update existing
                cashflow_doc = frappe.get_doc("AI Cashflow Forecast", existing[0].name)
                cashflow_doc.net_cash_flow = self.predicted_amount
                cashflow_doc.confidence_score = self.confidence_score
                cashflow_doc.model_used = self.prediction_model
                cashflow_doc.last_updated = frappe.utils.now()
                
                # Update specific fields from forecast details if available
                if self.forecast_details:
                    try:
                        details = json.loads(self.forecast_details)
                        cashflow_breakdown = details.get("cashflow_breakdown", {})
                        
                        if "total_inflows" in cashflow_breakdown:
                            cashflow_doc.predicted_inflows = cashflow_breakdown["total_inflows"]
                        if "total_outflows" in cashflow_breakdown:
                            cashflow_doc.predicted_outflows = cashflow_breakdown["total_outflows"]
                        if "liquidity_ratio" in cashflow_breakdown:
                            cashflow_doc.liquidity_ratio = cashflow_breakdown["liquidity_ratio"]
                        if "surplus_deficit" in cashflow_breakdown:
                            cashflow_doc.surplus_deficit = cashflow_breakdown["surplus_deficit"]
                            
                    except json.JSONDecodeError:
                        pass
                
                cashflow_doc.save(ignore_permissions=True)
                frappe.db.commit()
                
            else:
                # Create new cashflow forecast
                cashflow_doc = frappe.get_doc({
                    "doctype": "AI Cashflow Forecast",
                    "company": self.company,
                    "forecast_date": self.forecast_start_date,
                    "forecast_period": "Monthly",
                    "forecast_type": "Operational",
                    "net_cash_flow": self.predicted_amount,
                    "confidence_score": self.confidence_score,
                    "model_used": self.prediction_model,
                    "last_updated": frappe.utils.now()
                })
                
                # Set additional fields from forecast details
                if self.forecast_details:
                    try:
                        details = json.loads(self.forecast_details)
                        cashflow_breakdown = details.get("cashflow_breakdown", {})
                        
                        cashflow_doc.predicted_inflows = cashflow_breakdown.get("total_inflows", 0)
                        cashflow_doc.predicted_outflows = cashflow_breakdown.get("total_outflows", 0)
                        cashflow_doc.liquidity_ratio = cashflow_breakdown.get("liquidity_ratio", 100)
                        cashflow_doc.surplus_deficit = cashflow_breakdown.get("surplus_deficit", 0)
                        
                    except json.JSONDecodeError:
                        pass
                
                cashflow_doc.flags.ignore_permissions = True
                cashflow_doc.insert()
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(f"Cashflow sync error: {str(e)}")
    
    def sync_to_revenue_forecast(self):
        """Sync to AI Revenue Forecast"""
        try:
            # Check if revenue forecast exists
            existing = frappe.get_all("AI Revenue Forecast",
                                    filters={
                                        "company": self.company,
                                        "forecast_date": self.forecast_start_date
                                    },
                                    limit=1)
            
            if existing:
                # Update existing
                revenue_doc = frappe.get_doc("AI Revenue Forecast", existing[0].name)
                revenue_doc.total_predicted_revenue = self.predicted_amount
                revenue_doc.confidence_score = self.confidence_score
                revenue_doc.model_used = self.prediction_model
                revenue_doc.last_updated = frappe.utils.now()
                
                # Update specific fields from forecast details if available
                if self.forecast_details:
                    try:
                        details = json.loads(self.forecast_details)
                        revenue_breakdown = details.get("revenue_breakdown", {})
                        
                        if "product_revenue" in revenue_breakdown:
                            revenue_doc.product_revenue = revenue_breakdown["product_revenue"]
                        if "service_revenue" in revenue_breakdown:
                            revenue_doc.service_revenue = revenue_breakdown["service_revenue"]
                        if "recurring_revenue" in revenue_breakdown:
                            revenue_doc.recurring_revenue = revenue_breakdown["recurring_revenue"]
                        if "growth_rate" in revenue_breakdown:
                            revenue_doc.growth_rate = revenue_breakdown["growth_rate"]
                        if "seasonal_factor" in revenue_breakdown:
                            revenue_doc.seasonal_factor = revenue_breakdown["seasonal_factor"]
                        if "market_factor" in revenue_breakdown:
                            revenue_doc.market_factor = revenue_breakdown["market_factor"]
                            
                    except json.JSONDecodeError:
                        pass
                
                revenue_doc.save(ignore_permissions=True)
                frappe.db.commit()
                
            else:
                # Create new revenue forecast
                revenue_doc = frappe.get_doc({
                    "doctype": "AI Revenue Forecast",
                    "company": self.company,
                    "forecast_date": self.forecast_start_date,
                    "forecast_period": "Monthly",
                    "total_predicted_revenue": self.predicted_amount,
                    "confidence_score": self.confidence_score,
                    "model_used": self.prediction_model,
                    "last_updated": frappe.utils.now()
                })
                
                # Set additional fields from forecast details
                if self.forecast_details:
                    try:
                        details = json.loads(self.forecast_details)
                        revenue_breakdown = details.get("revenue_breakdown", {})
                        
                        revenue_doc.product_revenue = revenue_breakdown.get("product_revenue", 0)
                        revenue_doc.service_revenue = revenue_breakdown.get("service_revenue", 0)
                        revenue_doc.recurring_revenue = revenue_breakdown.get("recurring_revenue", 0)
                        revenue_doc.growth_rate = revenue_breakdown.get("growth_rate", 0)
                        revenue_doc.seasonal_factor = revenue_breakdown.get("seasonal_factor", 1.0)
                        revenue_doc.market_factor = revenue_breakdown.get("market_factor", 1.0)
                        
                    except json.JSONDecodeError:
                        pass
                
                revenue_doc.flags.ignore_permissions = True
                revenue_doc.insert()
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(f"Revenue sync error: {str(e)}")
    
    def sync_to_expense_forecast(self):
        """Sync to AI Expense Forecast"""
        try:
            # Check if expense forecast exists
            existing = frappe.get_all("AI Expense Forecast",
                                    filters={
                                        "company": self.company,
                                        "forecast_date": self.forecast_start_date
                                    },
                                    limit=1)
            
            if existing:
                # Update existing
                expense_doc = frappe.get_doc("AI Expense Forecast", existing[0].name)
                
                # Set expense amount in available field
                if hasattr(expense_doc, 'total_predicted_expenses'):
                    expense_doc.total_predicted_expenses = self.predicted_amount
                elif hasattr(expense_doc, 'predicted_expenses'):
                    expense_doc.predicted_expenses = self.predicted_amount
                
                # Set confidence in available field
                if hasattr(expense_doc, 'confidence_score'):
                    expense_doc.confidence_score = self.confidence_score
                elif hasattr(expense_doc, 'prediction_confidence'):
                    expense_doc.prediction_confidence = self.confidence_score
                
                # Set model in available field
                if hasattr(expense_doc, 'model_used'):
                    expense_doc.model_used = self.prediction_model
                elif hasattr(expense_doc, 'prediction_model'):
                    expense_doc.prediction_model = self.prediction_model
                
                # Set last updated
                if hasattr(expense_doc, 'last_updated'):
                    expense_doc.last_updated = frappe.utils.now()
                
                expense_doc.save(ignore_permissions=True)
                frappe.db.commit()
                
            else:
                # Create new expense forecast
                expense_data = {
                    "doctype": "AI Expense Forecast",
                    "company": self.company,
                    "forecast_date": self.forecast_start_date
                }
                
                # Set expense amount in available field
                if frappe.db.has_column("AI Expense Forecast", "total_predicted_expenses"):
                    expense_data["total_predicted_expenses"] = self.predicted_amount
                elif frappe.db.has_column("AI Expense Forecast", "predicted_expenses"):
                    expense_data["predicted_expenses"] = self.predicted_amount
                
                # Set confidence in available field
                if frappe.db.has_column("AI Expense Forecast", "confidence_score"):
                    expense_data["confidence_score"] = self.confidence_score
                elif frappe.db.has_column("AI Expense Forecast", "prediction_confidence"):
                    expense_data["prediction_confidence"] = self.confidence_score
                
                # Set model in available field
                if frappe.db.has_column("AI Expense Forecast", "model_used"):
                    expense_data["model_used"] = self.prediction_model
                elif frappe.db.has_column("AI Expense Forecast", "prediction_model"):
                    expense_data["prediction_model"] = self.prediction_model
                
                expense_doc = frappe.get_doc(expense_data)
                expense_doc.flags.ignore_permissions = True
                expense_doc.insert()
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(f"Expense sync error: {str(e)}")
    
    def create_or_update_accuracy_tracking(self):
        """Create or update forecast accuracy tracking"""
        try:
            # Only create accuracy tracking for forecasts that can be evaluated
            if not self.forecast_start_date or frappe.utils.getdate(self.forecast_start_date) > frappe.utils.getdate():
                return  # Future forecasts can't be evaluated yet
            
            # Check if accuracy record exists
            existing = frappe.get_all("AI Forecast Accuracy",
                                    filters={
                                        "original_forecast_id": self.name,
                                        "forecast_date": self.forecast_start_date
                                    },
                                    limit=1)
            
            if not existing:
                # Create new accuracy tracking record (without actual value for now)
                accuracy_doc = frappe.get_doc({
                    "doctype": "AI Forecast Accuracy",
                    "original_forecast_id": self.name,
                    "company": self.company,
                    "forecast_type": self.forecast_type,
                    "forecast_date": self.forecast_start_date,
                    "evaluation_date": frappe.utils.nowdate(),
                    "predicted_value": self.predicted_amount,
                    "prediction_model": self.prediction_model,
                    "confidence_at_creation": self.confidence_score
                })
                
                accuracy_doc.flags.ignore_permissions = True
                accuracy_doc.insert()
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(f"Accuracy tracking error: {str(e)}")

    def update_sync_status(self):
        """Update sync status with inventory system"""
        if self.inventory_sync_enabled:
            try:
                # Check if related inventory forecast exists
                inventory_forecast = frappe.get_all("AI Inventory Forecast",
                                                   filters={"company": self.company},
                                                   limit=1)
                
                if inventory_forecast:
                    self.sync_status = "Completed"
                    self.last_sync_date = frappe.utils.now()
                else:
                    self.sync_status = "Pending"
                    
            except Exception as e:
                self.sync_status = "Failed"
                self.error_log = str(e)
                frappe.log_error(f"Sync error for {self.name}: {str(e)}")
    
    def log_forecast_creation(self):
        """Log forecast creation for audit trail"""
        try:
            frappe.get_doc({
                "doctype": "AI Forecast Log",
                "forecast_id": self.name,
                "action": "Created",
                "details": f"Forecast created for {self.account} ({self.forecast_type})",
                "confidence_score": self.confidence_score,
                "predicted_amount": self.predicted_amount,
                "user": frappe.session.user
            }).insert(ignore_permissions=True)
        except:
            pass  # Log creation shouldn't break main process
    
    def check_alerts(self):
        """Check and create alerts if needed"""
        if not self.forecast_alert:
            return
        
        try:
            # Create alert notification
            alert_message = self.get_alert_message()
            
            # Send to relevant users
            recipients = self.get_alert_recipients()
            
            if recipients and alert_message:
                frappe.sendmail(
                    recipients=recipients,
                    subject=f"Forecast Alert: {self.account}",
                    message=alert_message,
                    reference_doctype=self.doctype,
                    reference_name=self.name
                )
                
        except Exception as e:
            frappe.log_error(f"Alert notification error: {str(e)}")
    
    def get_alert_message(self):
        """Generate alert message based on conditions"""
        messages = []
        
        if self.confidence_score < (self.confidence_threshold or 70):
            messages.append(f"Low confidence score: {self.confidence_score}%")
        
        if self.risk_category in ["High", "Critical"]:
            messages.append(f"High risk category: {self.risk_category}")
        
        if self.volatility_score and self.volatility_score > 75:
            messages.append(f"High volatility: {self.volatility_score}%")
        
        if messages:
            return f"""
            <h3>Forecast Alert</h3>
            <p><strong>Account:</strong> {self.account}</p>
            <p><strong>Forecast Type:</strong> {self.forecast_type}</p>
            <p><strong>Predicted Amount:</strong> {frappe.utils.fmt_money(self.predicted_amount or 0)}</p>
            <h4>Alert Conditions:</h4>
            <ul>{''.join(f'<li>{msg}</li>' for msg in messages)}</ul>
            <p>Please review and take appropriate action.</p>
            """
        
        return ""
    
    def get_alert_recipients(self):
        """Get list of users to notify for alerts"""
        try:
            # Get users with AI Inventory Manager role
            managers = frappe.get_all("Has Role",
                                    filters={"role": "AI Inventory Manager"},
                                    fields=["parent"])
            
            recipients = [m.parent for m in managers]
            
            # Add company's default recipients if configured
            company_doc = frappe.get_doc("Company", self.company)
            if hasattr(company_doc, 'default_finance_email') and company_doc.default_finance_email:
                recipients.append(company_doc.default_finance_email)
            
            # Map usernames to their email addresses and filter invalid emails
            valid_emails = []
            for r in set(recipients):
                email = None
                if isinstance(r, str) and '@' in r:
                    email = r
                else:
                    # Look up the user's email
                    email = frappe.db.get_value("User", r, "email")
                if email and frappe.utils.validate_email_address(email, throw=False):
                    valid_emails.append(email)
            
            return list(set(valid_emails))  # unique valid emails only
            
        except:
            return []
    
    @frappe.whitelist()
    def run_validation_check(self):
        """Run comprehensive validation check on this forecast"""
        try:
            from ai_inventory.ai_inventory.validation.forecast_validation import validate_specific_forecast
            
            validation_result = validate_specific_forecast(self.name)
            
            # Update forecast with validation results
            if validation_result.get("overall_score"):
                self.validation_score = validation_result["overall_score"]["score"]
                self.validation_status = validation_result["overall_score"]["status"]
                self.validation_date = frappe.utils.now()
            
            # Store critical issues and warnings
            critical_issues = validation_result.get("critical_issues", [])
            warnings = validation_result.get("warnings", [])
            
            if critical_issues:
                self.validation_issues = json.dumps(critical_issues)
                frappe.msgprint(f"🚨 {len(critical_issues)} critical issues found", alert=True)
            
            if warnings:
                self.validation_warnings = json.dumps(warnings)
                frappe.msgprint(f"⚠️ {len(warnings)} warnings issued", alert=True)
            
            self.save()
            
            return {
                "success": True,
                "validation_result": validation_result,
                "message": f"Validation completed. Score: {validation_result.get('overall_score', {}).get('score', 'N/A')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Validation check failed"
            }
    
    @frappe.whitelist()
    def get_validation_summary(self):
        """Get validation summary for dashboard display"""
        try:
            summary = {
                "basic_info": {
                    "forecast_id": self.name,
                    "company": self.company,
                    "account": self.account,
                    "forecast_type": self.forecast_type,
                    "created_on": self.creation
                },
                "current_status": {
                    "confidence_score": self.confidence_score,
                    "data_quality_score": getattr(self, 'data_quality_score', None),
                    "validation_score": getattr(self, 'validation_score', None),
                    "risk_category": self.risk_category,
                    "forecast_alert": self.forecast_alert
                },
                "predictions": {
                    "predicted_amount": self.predicted_amount,
                    "upper_bound": self.upper_bound,
                    "lower_bound": self.lower_bound,
                    "volatility_score": self.volatility_score,
                    "current_balance": getattr(self, 'current_balance', None),
                    "balance_as_of_date": getattr(self, 'balance_as_of_date', None),
                    "balance_prediction_ratio": getattr(self, 'balance_prediction_ratio', None)
                },
                "validation_info": {
                    "last_validation": getattr(self, 'validation_date', None),
                    "validation_status": getattr(self, 'validation_status', 'Not Validated'),
                    "has_critical_issues": bool(getattr(self, 'validation_issues', None)),
                    "has_warnings": bool(getattr(self, 'validation_warnings', None))
                },
                "sync_info": {
                    "inventory_sync_enabled": self.inventory_sync_enabled,
                    "sync_status": self.sync_status,
                    "last_sync_date": self.last_sync_date
                }
            }
            
            # Add quick health indicators
            health_indicators = []
            
            # Check bounds logic
            if self.upper_bound and self.lower_bound:
                if self.upper_bound <= self.lower_bound:
                    health_indicators.append({"type": "critical", "message": "Forecast bounds error detected"})
                else:
                    health_indicators.append({"type": "success", "message": "Forecast bounds are valid"})
            
            # Check confidence
            if self.confidence_score:
                if self.confidence_score >= 80:
                    health_indicators.append({"type": "success", "message": f"High confidence ({self.confidence_score}%)"})
                elif self.confidence_score >= 70:
                    health_indicators.append({"type": "warning", "message": f"Moderate confidence ({self.confidence_score}%)"})
                else:
                    health_indicators.append({"type": "critical", "message": f"Low confidence ({self.confidence_score}%)"})
            
            # Check data quality
            data_quality = getattr(self, 'data_quality_score', None)
            if data_quality:
                if data_quality >= 80:
                    health_indicators.append({"type": "success", "message": f"Good data quality ({data_quality}%)"})
                elif data_quality >= 60:
                    health_indicators.append({"type": "warning", "message": f"Fair data quality ({data_quality}%)"})
                else:
                    health_indicators.append({"type": "critical", "message": f"Poor data quality ({data_quality}%)"})
            
            # Check current balance vs prediction accuracy
            current_balance = getattr(self, 'current_balance', None)
            if current_balance is not None and self.predicted_amount:
                balance_variance = abs(current_balance - self.predicted_amount)
                balance_variance_pct = (balance_variance / abs(current_balance)) * 100 if current_balance != 0 else 0
                
                if balance_variance_pct <= 10:
                    health_indicators.append({"type": "success", "message": f"Prediction accurate (±{balance_variance_pct:.1f}%)"})
                elif balance_variance_pct <= 25:
                    health_indicators.append({"type": "warning", "message": f"Prediction variance: ±{balance_variance_pct:.1f}%"})
                else:
                    health_indicators.append({"type": "critical", "message": f"Large prediction variance: ±{balance_variance_pct:.1f}%"})
            
            # Check for current balance availability
            if current_balance is not None:
                balance_date = getattr(self, 'balance_as_of_date', None)
                if balance_date:
                    health_indicators.append({"type": "info", "message": f"Current balance: ₹{current_balance:,.2f} (as of {frappe.utils.formatdate(balance_date)})"})
                else:
                    health_indicators.append({"type": "info", "message": f"Current balance: ₹{current_balance:,.2f}"})
            else:
                health_indicators.append({"type": "warning", "message": "Current balance not available"})
            summary["health_indicators"] = health_indicators
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
    
    @frappe.whitelist()
    def fix_bounds_issue(self):
        """Attempt to fix forecast bounds issue automatically"""
        try:
            if not self.upper_bound or not self.lower_bound:
                return {"success": False, "message": "No bounds to fix"}
            
            if self.upper_bound > self.lower_bound:
                return {"success": True, "message": "Bounds are already correct"}
            
            # Swap bounds if they're reversed
            if self.upper_bound < self.lower_bound:
                original_upper = self.upper_bound
                original_lower = self.lower_bound
                
                self.upper_bound = original_lower
                self.lower_bound = original_upper
                
                self.save()
                
                return {
                    "success": True,
                    "message": f"Bounds corrected: Upper bound set to ₹{self.upper_bound:,.2f}, Lower bound set to ₹{self.lower_bound:,.2f}",
                    "action_taken": "Swapped upper and lower bounds"
                }
            
            return {"success": False, "message": "Unable to automatically fix bounds"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @frappe.whitelist()
    def export_forecast_data(self):
        """Export forecast data for analysis"""
        try:
            export_data = {
                "basic_info": {
                    "forecast_id": self.name,
                    "company": self.company,
                    "account": self.account,
                    "account_name": self.account_name,
                    "forecast_type": self.forecast_type
                },
                "predictions": {
                    "predicted_amount": self.predicted_amount,
                    "confidence_score": self.confidence_score,
                    "upper_bound": self.upper_bound,
                    "lower_bound": self.lower_bound,
                    "forecast_accuracy": self.forecast_accuracy,
                    "current_balance": getattr(self, 'current_balance', None),
                    "balance_as_of_date": getattr(self, 'balance_as_of_date', None),
                    "balance_prediction_ratio": getattr(self, 'balance_prediction_ratio', None)
                },
                "risk_analysis": {
                    "risk_category": self.risk_category,
                    "volatility_score": self.volatility_score,
                    "trend_direction": self.trend_direction
                },
                "model_info": {
                    "prediction_model": self.prediction_model,
                    "forecast_period_days": self.forecast_period_days,
                    "seasonal_adjustment": self.seasonal_adjustment,
                    "forecast_version": self.forecast_version
                },
                "integration": {
                    "inventory_sync_enabled": self.inventory_sync_enabled,
                    "sync_status": self.sync_status,
                    "last_sync_date": self.last_sync_date
                },
                "metadata": {
                    "created_on": self.creation,
                    "last_modified": self.modified,
                    "last_forecast_date": self.last_forecast_date
                }
            }
            
            return {
                "success": True,
                "data": export_data,
                "filename": f"forecast_export_{self.name}.json"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# ============================================================================
# Utility Functions for Forecast Management
# ============================================================================

def get_forecast_summary(company=None, period_days=30):
    """Get summary of forecasts for dashboard"""
    
    filters = {}
    if company:
        filters["company"] = company
    
    if period_days:
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -period_days)
        filters["creation"] = [">=", from_date]
    
    forecasts = frappe.get_all("AI Financial Forecast",
                              filters=filters,
                              fields=["forecast_type", "confidence_score", "predicted_amount", 
                                     "risk_category", "company"])
    
    if not forecasts:
        return {"message": "No forecasts found"}
    
    summary = {
        "total_forecasts": len(forecasts),
        "average_confidence": sum(f.confidence_score for f in forecasts) / len(forecasts),
        "total_predicted_value": sum(f.predicted_amount or 0 for f in forecasts),
        "by_type": {},
        "by_risk": {},
        "by_company": {}
    }
    
    # Group by forecast type
    for f in forecasts:
        ftype = f.forecast_type
        if ftype not in summary["by_type"]:
            summary["by_type"][ftype] = {"count": 0, "total_predicted": 0, "avg_confidence": 0}
        
        summary["by_type"][ftype]["count"] += 1
        summary["by_type"][ftype]["total_predicted"] += f.predicted_amount or 0
        summary["by_type"][ftype]["avg_confidence"] += f.confidence_score or 0
    
    # Calculate averages
    for ftype in summary["by_type"]:
        count = summary["by_type"][ftype]["count"]
        summary["by_type"][ftype]["avg_confidence"] /= count
    
    return summary

    @frappe.whitelist()
    def validate_forecast(self):
        """Validate forecast data and provide recommendations"""
        try:
            warnings = []
            recommendations = []
            metrics = {}
            
            # Basic data validation
            if not self.predicted_amount or self.predicted_amount <= 0:
                warnings.append("Predicted amount is missing or invalid")
            
            if not self.confidence_score or self.confidence_score < 50:
                warnings.append("Confidence score is low (below 50%)")
                recommendations.append("Consider reviewing input data quality")
            
            if not self.forecast_start_date or not self.forecast_end_date:
                warnings.append("Forecast date range is incomplete")
            else:
                # Check if forecast period is reasonable
                from datetime import datetime
                start_date = datetime.strptime(str(self.forecast_start_date), "%Y-%m-%d")
                end_date = datetime.strptime(str(self.forecast_end_date), "%Y-%m-%d")
                days_diff = (end_date - start_date).days
                
                if days_diff <= 0:
                    warnings.append("Invalid forecast period: end date before start date")
                elif days_diff > 365:
                    recommendations.append("Long forecast periods may have reduced accuracy")
                elif days_diff < 7:
                    recommendations.append("Very short forecast periods may not capture trends")
            
            # Account validation
            if self.account:
                account_exists = frappe.db.exists("Account", self.account)
                if not account_exists:
                    warnings.append("Selected account does not exist")
                else:
                    # Check account type compatibility
                    account_type = frappe.db.get_value("Account", self.account, "account_type")
                    if self.forecast_type == "Revenue" and account_type not in ["Income Account", "Revenue"]:
                        recommendations.append("Account type may not be suitable for revenue forecasting")
                    elif self.forecast_type == "Expense" and account_type not in ["Expense Account", "Cost of Goods Sold"]:
                        recommendations.append("Account type may not be suitable for expense forecasting")
            
            # Currency validation
            if self.currency:
                currency_exists = frappe.db.exists("Currency", self.currency)
                if not currency_exists:
                    warnings.append("Selected currency is not valid")
            
            # Calculate metrics
            metrics["accuracy"] = f"{self.confidence_score}%"
            metrics["confidence"] = "High" if self.confidence_score > 80 else "Medium" if self.confidence_score > 60 else "Low"
            
            # Data quality assessment
            data_quality_score = 100
            if warnings:
                data_quality_score -= len(warnings) * 15
            if not self.forecast_details:
                data_quality_score -= 10
            if not self.current_balance:
                data_quality_score -= 5
                
            metrics["data_quality"] = f"{max(0, data_quality_score)}%"
            
            # Add recommendations based on data
            if not self.forecast_details:
                recommendations.append("Add forecast details for better analysis")
            
            if self.forecast_type and not self.sync_status:
                recommendations.append("Enable sync to integrate with related forecasts")
            
            return {
                "success": True,
                "warnings": warnings,
                "recommendations": recommendations,
                "metrics": metrics,
                "overall_score": max(0, data_quality_score)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
