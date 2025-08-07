# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class AICashflowForecast(Document):
    """AI Cashflow Forecast with sync to AI Financial Forecast"""
    
    def validate(self):
        """Validate cashflow forecast data"""
        self.calculate_totals()
        self.validate_cash_requirements()
        # Skip sync during validation to avoid circular dependency
        # self.sync_with_financial_forecast()
    
    def calculate_totals(self):
        """Calculate total inflows and outflows"""
        # Calculate total inflows
        inflow_fields = ['receivables_collection', 'sales_forecast_amount', 'other_income', 
                        'investment_returns', 'loan_proceeds']
        total_inflows = sum(getattr(self, field, 0) or 0 for field in inflow_fields)
        self.predicted_inflows = total_inflows
        
        # Calculate total outflows
        outflow_fields = ['payables_payment', 'inventory_purchases', 'operating_expenses',
                         'capital_expenditure', 'loan_payments']
        total_outflows = sum(getattr(self, field, 0) or 0 for field in outflow_fields)
        self.predicted_outflows = total_outflows
        
        # Calculate net cash flow
        self.net_cash_flow = total_inflows - total_outflows
        
        # Calculate closing balance
        opening_balance = self.opening_balance or 0
        self.closing_balance = opening_balance + self.net_cash_flow
        
        # Calculate surplus/deficit
        minimum_required = self.minimum_cash_required or 0
        self.surplus_deficit = self.closing_balance - minimum_required
        
        # Calculate liquidity ratio
        if total_outflows > 0:
            self.liquidity_ratio = (total_inflows / total_outflows) * 100
        else:
            self.liquidity_ratio = 100
    
    def validate_cash_requirements(self):
        """Validate cash requirements and set alerts"""
        if self.surplus_deficit and self.surplus_deficit < 0:
            self.alert_status = "Critical"
        elif self.liquidity_ratio and self.liquidity_ratio < 110:
            self.alert_status = "Warning"
        else:
            self.alert_status = "Normal"
    
    def sync_with_financial_forecast(self):
        """Sync data with AI Financial Forecast"""
        if not self.company:
            return
        
        try:
            # Find or create corresponding AI Financial Forecast
            existing_forecast = frappe.get_all("AI Financial Forecast",
                                             filters={
                                                 "company": self.company,
                                                 "forecast_type": "Cash Flow",
                                                 "forecast_date": self.forecast_date
                                             },
                                             limit=1)
            
            if existing_forecast:
                # Update existing forecast
                forecast_doc = frappe.get_doc("AI Financial Forecast", existing_forecast[0].name)
                self.update_financial_forecast(forecast_doc)
            else:
                # Create new financial forecast
                self.create_financial_forecast()
                
        except Exception as e:
            frappe.log_error(f"Cashflow sync error: {str(e)}")
    
    def update_financial_forecast(self, forecast_doc):
        """Update AI Financial Forecast with cashflow data"""
        forecast_doc.predicted_amount = self.net_cash_flow
        forecast_doc.confidence_score = self.confidence_score
        forecast_doc.risk_score = self.risk_score
        forecast_doc.forecast_details = json.dumps({
            "cashflow_breakdown": {
                "total_inflows": self.predicted_inflows,
                "total_outflows": self.predicted_outflows,
                "net_cash_flow": self.net_cash_flow,
                "liquidity_ratio": self.liquidity_ratio,
                "surplus_deficit": self.surplus_deficit
            },
            "source": "AI Cashflow Forecast",
            "source_id": self.name
        })
        forecast_doc.last_updated = frappe.utils.now()
        forecast_doc.save(ignore_permissions=True)
    
    def create_financial_forecast(self):
        """Create new AI Financial Forecast from cashflow data"""
        try:
            forecast_doc = frappe.get_doc({
                "doctype": "AI Financial Forecast",
                "company": self.company,
                "forecast_type": "Cash Flow",
                "forecast_date": self.forecast_date,
                "forecast_period": self.forecast_period,
                "predicted_amount": self.net_cash_flow,
                "confidence_score": self.confidence_score or 75,
                "forecast_details": json.dumps({
                    "cashflow_breakdown": {
                        "total_inflows": self.predicted_inflows,
                        "total_outflows": self.predicted_outflows,
                        "net_cash_flow": self.net_cash_flow,
                        "liquidity_ratio": self.liquidity_ratio,
                        "surplus_deficit": self.surplus_deficit
                    },
                    "source": "AI Cashflow Forecast",
                    "source_id": self.name
                }),
                "prediction_model": self.model_used or "Cash Flow Model",
                "last_updated": frappe.utils.now()
            })
            forecast_doc.insert(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error creating financial forecast from cashflow: {str(e)}")
    
    def before_save(self):
        """Actions before saving"""
        self.set_ai_predictions()
        self.last_updated = frappe.utils.now()
    
    def set_ai_predictions(self):
        """Set AI prediction values"""
        # Set confidence based on data completeness and ratios
        completeness_score = self.calculate_data_completeness()
        ratio_score = self.calculate_ratio_health()
        
        self.confidence_score = (completeness_score + ratio_score) / 2
        
        # Set risk score based on liquidity and volatility
        if self.liquidity_ratio:
            if self.liquidity_ratio < 100:
                self.risk_score = 90
            elif self.liquidity_ratio < 110:
                self.risk_score = 70
            elif self.liquidity_ratio < 130:
                self.risk_score = 40
            else:
                self.risk_score = 20
        else:
            self.risk_score = 50
        
        # Set seasonal factor based on period
        self.seasonal_factor = self.calculate_seasonal_factor()
    
    def calculate_data_completeness(self):
        """Calculate data completeness score"""
        required_fields = ['receivables_collection', 'payables_payment', 'operating_expenses']
        completed_fields = sum(1 for field in required_fields if getattr(self, field, 0))
        return (completed_fields / len(required_fields)) * 100
    
    def calculate_ratio_health(self):
        """Calculate health score based on financial ratios"""
        if not self.liquidity_ratio:
            return 50
        
        if self.liquidity_ratio >= 120:
            return 90
        elif self.liquidity_ratio >= 110:
            return 80
        elif self.liquidity_ratio >= 100:
            return 70
        elif self.liquidity_ratio >= 90:
            return 60
        else:
            return 40
    
    def calculate_seasonal_factor(self):
        """Calculate seasonal adjustment factor"""
        if not self.forecast_date:
            return 1.0
        
        # Simple seasonal adjustment based on month
        month = frappe.utils.getdate(self.forecast_date).month
        
        # Peak business months (Oct-Dec)
        if month in [10, 11, 12]:
            return 1.2
        # Slow months (Jan-Feb)
        elif month in [1, 2]:
            return 0.8
        # Summer months
        elif month in [6, 7, 8]:
            return 0.9
        else:
            return 1.0

@frappe.whitelist()
def create_cashflow_forecast_from_financial(financial_forecast_name):
    """Create cashflow forecast from AI Financial Forecast"""
    try:
        financial_doc = frappe.get_doc("AI Financial Forecast", financial_forecast_name)
        
        if financial_doc.forecast_type != "Cash Flow":
            return {"success": False, "error": "Source forecast must be Cash Flow type"}
        
        # Check if cashflow forecast already exists
        existing = frappe.get_all("AI Cashflow Forecast",
                                filters={
                                    "company": financial_doc.company,
                                    "forecast_date": financial_doc.forecast_date
                                },
                                limit=1)
        
        if existing:
            return {"success": False, "error": "Cashflow forecast already exists for this date"}
        
        # Create new cashflow forecast
        cashflow_doc = frappe.get_doc({
            "doctype": "AI Cashflow Forecast",
            "company": financial_doc.company,
            "forecast_date": financial_doc.forecast_date,
            "forecast_period": "Monthly",
            "forecast_type": "Operational",
            "net_cash_flow": financial_doc.predicted_amount,
            "confidence_score": financial_doc.confidence_score,
            "model_used": financial_doc.prediction_model,
            "last_updated": frappe.utils.now()
        })
        
        cashflow_doc.insert()
        
        return {
            "success": True,
            "cashflow_forecast_id": cashflow_doc.name,
            "message": "Cashflow forecast created successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
