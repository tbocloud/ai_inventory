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
        # If component inflows are zero but a predicted_inflows value already exists, keep it
        if total_inflows == 0 and (getattr(self, 'predicted_inflows', None) not in (None, 0)):
            total_inflows = self.predicted_inflows or 0
        self.predicted_inflows = total_inflows
        
        # Calculate total outflows
        outflow_fields = ['payables_payment', 'inventory_purchases', 'operating_expenses',
                         'capital_expenditure', 'loan_payments']
        total_outflows = sum(getattr(self, field, 0) or 0 for field in outflow_fields)
        # If component outflows are zero but a predicted_outflows value already exists, keep it
        if total_outflows == 0 and (getattr(self, 'predicted_outflows', None) not in (None, 0)):
            total_outflows = self.predicted_outflows or 0
        self.predicted_outflows = total_outflows
        
        # Calculate net cash flow; if both totals are zero and a net_cash_flow exists, preserve it
        computed_net = total_inflows - total_outflows
        if total_inflows == 0 and total_outflows == 0 and (getattr(self, 'net_cash_flow', None) not in (None, 0)):
            pass  # keep existing net_cash_flow
        else:
            self.net_cash_flow = computed_net
        
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
    def sync_with_financial_forecast(self):
        """Sync data with AI Financial Forecast"""
        if not self.company:
            return {"success": False, "message": "Company not specified"}
        
        try:
            # Find or create corresponding AI Financial Forecast
            existing_forecast = frappe.get_all("AI Financial Forecast",
                                             filters={
                                                 "company": self.company,
                                                 "forecast_type": "Cash Flow",
                                                 "forecast_start_date": self.forecast_date
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
                "forecast_start_date": self.forecast_date,
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
        # Auto-populate from GL if nothing entered but we have a company and date
        try:
            if (not (self.predicted_inflows or self.predicted_outflows) and self.company and self.forecast_date):
                self.populate_from_gl()
        except Exception as e:
            frappe.log_error(f"Cashflow GL populate failed: {str(e)}")

        self.calculate_totals()
        self.validate_cash_requirements()
        self.set_ai_predictions()
        
        # Enable sync after calculation
        self.sync_with_financial_forecast()

    def populate_from_gl(self):
        """Populate predicted inflows/outflows from GL entries for the month."""
        if not (self.company and self.forecast_date):
            return
        from frappe.utils import get_first_day, get_last_day
        month_start = get_first_day(self.forecast_date)
        month_end = get_last_day(self.forecast_date)
        # Collect cash/bank accounts
        accounts = frappe.get_all(
            "Account",
            filters={"company": self.company, "is_group": 0, "account_type": ["in", ["Cash", "Bank"]]},
            pluck="name",
        )
        if not accounts:
            return
        placeholders = ", ".join(["%s"] * len(accounts))
        q = f"""
            SELECT COALESCE(SUM(debit), 0) AS total_debit,
                   COALESCE(SUM(credit), 0) AS total_credit
            FROM `tabGL Entry`
            WHERE company = %s
              AND posting_date BETWEEN %s AND %s
              AND account IN ({placeholders})
        """
        params = [self.company, month_start, month_end] + accounts
        row = frappe.db.sql(q, params, as_dict=True)
        totals = row[0] if row else {"total_debit": 0, "total_credit": 0}
        inflows = float(totals.get("total_debit") or 0)
        outflows = float(totals.get("total_credit") or 0)
        # Only set if there is movement; otherwise leave fields as-is
        if inflows or outflows:
            self.predicted_inflows = inflows
            self.predicted_outflows = outflows
            self.net_cash_flow = inflows - outflows
            self.model_used = self.model_used or "GL Monthly Auto"
            self.last_updated = frappe.utils.now()

@frappe.whitelist()
def sync_with_financial_forecast(cashflow_name):
    """Whitelist method for manual sync trigger"""
    try:
        doc = frappe.get_doc("AI Cashflow Forecast", cashflow_name)
        doc.sync_with_financial_forecast()
        # Try to fetch the linked financial forecast for routing
        linked = frappe.get_all(
            "AI Financial Forecast",
            filters={
                "company": doc.company,
                "forecast_type": "Cash Flow",
                "forecast_start_date": doc.forecast_date,
            },
            fields=["name"],
            order_by="modified desc",
            limit=1,
        )
        ff_name = linked[0].name if linked else None
        return {"success": True, "message": "Sync completed successfully", "financial_forecast_name": ff_name}
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def set_ai_predictions(cashflow_name):
    """Whitelist method for AI prediction calculation"""
    try:
        doc = frappe.get_doc("AI Cashflow Forecast", cashflow_name)
        doc.set_ai_predictions()
        doc.save()
        return {"success": True, "message": "AI predictions calculated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def validate_cash_requirements(cashflow_name):
    """Whitelist method for cash requirement validation"""
    try:
        doc = frappe.get_doc("AI Cashflow Forecast", cashflow_name)
        doc.validate_cash_requirements()
        
        # Determine status based on surplus/deficit
        status = "Healthy"
        message = "Cash requirements are adequate"
        
        if hasattr(doc, 'surplus_deficit') and doc.surplus_deficit:
            if doc.surplus_deficit < 0:
                status = "Critical"
                message = f"Cash deficit of {abs(doc.surplus_deficit):,.2f}"
            elif doc.surplus_deficit < doc.minimum_cash_required * 0.1:
                status = "Warning" 
                message = "Cash reserves are low"
        
        return {"status": status, "message": message}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

@frappe.whitelist()
def populate_from_gl(cashflow_name):
    """Whitelist method to populate a cashflow doc from GL for its month."""
    try:
        doc = frappe.get_doc("AI Cashflow Forecast", cashflow_name)
        doc.populate_from_gl()
        doc.calculate_totals()
        doc.set_ai_predictions()
        doc.save()
        return {"success": True, "message": "Populated from GL and recalculated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def create_cashflow_forecast_from_financial(financial_forecast_name):
    """Create a new AI Cashflow Forecast from a Cash Flow type AI Financial Forecast."""
    try:
        financial_doc = frappe.get_doc("AI Financial Forecast", financial_forecast_name)

        if financial_doc.forecast_type != "Cash Flow":
            return {"success": False, "error": "Source forecast must be Cash Flow type"}

        # Check if a cashflow forecast already exists for the same date and company
        existing = frappe.get_all(
            "AI Cashflow Forecast",
            filters={
                "company": financial_doc.company,
                "forecast_date": financial_doc.forecast_start_date,
            },
            limit=1,
        )
        if existing:
            return {"success": False, "error": "Cashflow forecast already exists for this date"}

        # Create cashflow forecast
        cashflow_doc = frappe.get_doc({
            "doctype": "AI Cashflow Forecast",
            "company": financial_doc.company,
            "forecast_date": financial_doc.forecast_start_date,
            "forecast_period": "Monthly",
            "forecast_type": "Operational",
            "net_cash_flow": financial_doc.predicted_amount,
            "confidence_score": financial_doc.confidence_score,
            "model_used": financial_doc.prediction_model,
            "last_updated": frappe.utils.now(),
        })
        cashflow_doc.insert()

        return {
            "success": True,
            "cashflow_forecast_id": cashflow_doc.name,
            "message": "Cashflow forecast created successfully",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
