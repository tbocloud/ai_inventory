# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class AIExpenseForecast(Document):
    """AI Expense Forecast with sync to AI Financial Forecast"""
    
    def validate(self):
        """Validate expense forecast data"""
        self.calculate_totals()
        self.analyze_expense_trends()
        # Skip sync during validation to avoid circular dependency
        # self.sync_with_financial_forecast()
    
    def calculate_totals(self):
        """Calculate total predicted expenses"""
        # Get all expense fields dynamically
        expense_fields = []
        for field in self.meta.fields:
            if field.fieldtype == "Currency" and "expense" in field.fieldname.lower():
                expense_fields.append(field.fieldname)
        
        total_expenses = sum(getattr(self, field, 0) or 0 for field in expense_fields)
        
        # Set total predicted expenses field if exists
        if hasattr(self, 'total_predicted_expenses'):
            self.total_predicted_expenses = total_expenses
        elif hasattr(self, 'predicted_expenses'):
            self.predicted_expenses = total_expenses
        
        # Calculate expense growth rate
        self.calculate_expense_growth()
    
    def calculate_expense_growth(self):
        """Calculate expense growth rate compared to previous forecast"""
        try:
            current_total = getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
            
            if not current_total:
                return
            
            # Get previous forecast
            previous = frappe.get_all("AI Expense Forecast",
                                    filters={
                                        "company": self.company,
                                        "forecast_date": ["<", self.forecast_date],
                                        "name": ["!=", self.name]
                                    },
                                    fields=["total_predicted_expenses", "predicted_expenses"],
                                    order_by="forecast_date desc",
                                    limit=1)
            
            if previous:
                prev_total = previous[0].get('total_predicted_expenses') or previous[0].get('predicted_expenses')
                if prev_total:
                    growth_rate = ((current_total - prev_total) / prev_total) * 100
                    if hasattr(self, 'expense_growth_rate'):
                        self.expense_growth_rate = growth_rate
                    elif hasattr(self, 'growth_rate'):
                        self.growth_rate = growth_rate
                
        except Exception as e:
            frappe.log_error(f"Expense growth calculation error: {str(e)}")
    
    def analyze_expense_trends(self):
        """Analyze expense trends and set confidence"""
        current_total = getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
        
        if not current_total:
            confidence = 50
        else:
            # Base confidence on data completeness
            completeness = self.calculate_data_completeness()
            
            # Adjust based on expense stability
            stability_factor = self.calculate_expense_stability()
            
            # Calculate final confidence score
            confidence = min(95, (completeness + stability_factor) / 2)
        
        # Set confidence score in available field
        if hasattr(self, 'confidence_score'):
            self.confidence_score = confidence
        elif hasattr(self, 'prediction_confidence'):
            self.prediction_confidence = confidence
        
        # Calculate risk factors
        self.calculate_expense_risks()
    
    def calculate_data_completeness(self):
        """Calculate data completeness score"""
        # Count non-zero expense fields
        expense_fields = []
        for field in self.meta.fields:
            if field.fieldtype == "Currency" and "expense" in field.fieldname.lower():
                expense_fields.append(field.fieldname)
        
        if not expense_fields:
            return 50
        
        completed_fields = sum(1 for field in expense_fields if getattr(self, field, 0))
        return (completed_fields / len(expense_fields)) * 100
    
    def calculate_expense_stability(self):
        """Calculate stability factor based on expense growth"""
        growth_rate = getattr(self, 'expense_growth_rate', 0) or getattr(self, 'growth_rate', 0)
        
        if growth_rate is None:
            return 70
        
        abs_growth = abs(growth_rate)
        
        if abs_growth <= 10:  # Very stable expenses
            return 90
        elif abs_growth <= 25:  # Moderate expense changes
            return 80
        elif abs_growth <= 50:  # Some expense volatility
            return 70
        else:  # High expense volatility
            return 60
    
    def calculate_expense_risks(self):
        """Calculate expense risk factors"""
        risk_score = 0
        
        # High growth in expenses increases risk
        growth_rate = getattr(self, 'expense_growth_rate', 0) or getattr(self, 'growth_rate', 0)
        if growth_rate and growth_rate > 20:
            risk_score += 20
        
        # Large expense amounts indicate higher risk
        current_total = getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
        if current_total and current_total > 1000000:  # Over 1M
            risk_score += 15
        
        # Set risk score in available field
        if hasattr(self, 'risk_score'):
            self.risk_score = min(100, risk_score)
        elif hasattr(self, 'expense_risk'):
            self.expense_risk = min(100, risk_score)
    
    def sync_with_financial_forecast(self):
        """Sync data with AI Financial Forecast"""
        if not self.company:
            return
        
        try:
            current_total = getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
            
            # Find or create corresponding AI Financial Forecast
            existing_forecast = frappe.get_all("AI Financial Forecast",
                                             filters={
                                                 "company": self.company,
                                                 "forecast_type": "Expense",
                                                 "forecast_date": self.forecast_date
                                             },
                                             limit=1)
            
            if existing_forecast:
                # Update existing forecast
                forecast_doc = frappe.get_doc("AI Financial Forecast", existing_forecast[0].name)
                self.update_financial_forecast(forecast_doc, current_total)
            else:
                # Create new financial forecast
                self.create_financial_forecast(current_total)
                
        except Exception as e:
            frappe.log_error(f"Expense sync error: {str(e)}")
    
    def update_financial_forecast(self, forecast_doc, total_expenses):
        """Update AI Financial Forecast with expense data"""
        forecast_doc.predicted_amount = total_expenses
        
        confidence = getattr(self, 'confidence_score', 0) or getattr(self, 'prediction_confidence', 75)
        forecast_doc.confidence_score = confidence
        
        # Build expense breakdown
        expense_breakdown = {}
        for field in self.meta.fields:
            if field.fieldtype == "Currency" and "expense" in field.fieldname.lower():
                value = getattr(self, field.fieldname, 0)
                if value:
                    expense_breakdown[field.fieldname] = value
        
        forecast_doc.forecast_details = json.dumps({
            "expense_breakdown": expense_breakdown,
            "total_expenses": total_expenses,
            "expense_growth_rate": getattr(self, 'expense_growth_rate', 0) or getattr(self, 'growth_rate', 0),
            "risk_factors": self.get_risk_factors(),
            "source": "AI Expense Forecast",
            "source_id": self.name
        })
        forecast_doc.last_updated = frappe.utils.now()
        forecast_doc.save(ignore_permissions=True)
    
    def create_financial_forecast(self, total_expenses):
        """Create new AI Financial Forecast from expense data"""
        try:
            confidence = getattr(self, 'confidence_score', 0) or getattr(self, 'prediction_confidence', 75)
            model_used = getattr(self, 'model_used', None) or getattr(self, 'prediction_model', 'Expense Forecast Model')
            
            # Build expense breakdown
            expense_breakdown = {}
            for field in self.meta.fields:
                if field.fieldtype == "Currency" and "expense" in field.fieldname.lower():
                    value = getattr(self, field.fieldname, 0)
                    if value:
                        expense_breakdown[field.fieldname] = value
            
            forecast_doc = frappe.get_doc({
                "doctype": "AI Financial Forecast",
                "company": self.company,
                "forecast_type": "Expense",
                "forecast_date": self.forecast_date,
                "forecast_period": getattr(self, 'forecast_period', 'Monthly'),
                "predicted_amount": total_expenses,
                "confidence_score": confidence,
                "forecast_details": json.dumps({
                    "expense_breakdown": expense_breakdown,
                    "total_expenses": total_expenses,
                    "expense_growth_rate": getattr(self, 'expense_growth_rate', 0) or getattr(self, 'growth_rate', 0),
                    "risk_factors": self.get_risk_factors(),
                    "source": "AI Expense Forecast",
                    "source_id": self.name
                }),
                "prediction_model": model_used,
                "last_updated": frappe.utils.now()
            })
            forecast_doc.insert(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error creating financial forecast from expense: {str(e)}")
    
    def get_risk_factors(self):
        """Get list of risk factors for this expense forecast"""
        risk_factors = []
        
        growth_rate = getattr(self, 'expense_growth_rate', 0) or getattr(self, 'growth_rate', 0)
        if growth_rate and growth_rate > 20:
            risk_factors.append(f"High expense growth rate: {growth_rate:.1f}%")
        
        current_total = getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
        if current_total and current_total > 1000000:
            risk_factors.append(f"Large expense amount: {frappe.utils.fmt_money(current_total)}")
        
        confidence = getattr(self, 'confidence_score', 0) or getattr(self, 'prediction_confidence', 75)
        if confidence < 70:
            risk_factors.append(f"Low prediction confidence: {confidence}%")
        
        return risk_factors
    
    def before_save(self):
        """Actions before saving"""
        self.set_calculation_metadata()
    
    def set_calculation_metadata(self):
        """Set metadata about calculations"""
        # Set last updated timestamp
        if hasattr(self, 'last_updated'):
            self.last_updated = frappe.utils.now()
        elif hasattr(self, 'calculation_date'):
            self.calculation_date = frappe.utils.now()
        
        # Set model information
        if hasattr(self, 'model_used') and not self.model_used:
            self.model_used = "AI Expense Analysis Model"
        elif hasattr(self, 'prediction_model') and not getattr(self, 'prediction_model', None):
            self.prediction_model = "AI Expense Analysis Model"

@frappe.whitelist()
def create_expense_forecast_from_financial(financial_forecast_name):
    """Create expense forecast from AI Financial Forecast"""
    try:
        financial_doc = frappe.get_doc("AI Financial Forecast", financial_forecast_name)
        
        if financial_doc.forecast_type != "Expense":
            return {"success": False, "error": "Source forecast must be Expense type"}
        
        # Check if expense forecast already exists
        existing = frappe.get_all("AI Expense Forecast",
                                filters={
                                    "company": financial_doc.company,
                                    "forecast_date": financial_doc.forecast_date
                                },
                                limit=1)
        
        if existing:
            return {"success": False, "error": "Expense forecast already exists for this date"}
        
        # Create new expense forecast
        expense_data = {
            "doctype": "AI Expense Forecast",
            "company": financial_doc.company,
            "forecast_date": financial_doc.forecast_date
        }
        
        # Set expense amount in available field
        if frappe.db.has_column("AI Expense Forecast", "total_predicted_expenses"):
            expense_data["total_predicted_expenses"] = financial_doc.predicted_amount
        elif frappe.db.has_column("AI Expense Forecast", "predicted_expenses"):
            expense_data["predicted_expenses"] = financial_doc.predicted_amount
        
        # Set confidence in available field
        if frappe.db.has_column("AI Expense Forecast", "confidence_score"):
            expense_data["confidence_score"] = financial_doc.confidence_score
        elif frappe.db.has_column("AI Expense Forecast", "prediction_confidence"):
            expense_data["prediction_confidence"] = financial_doc.confidence_score
        
        # Set model in available field
        if frappe.db.has_column("AI Expense Forecast", "model_used"):
            expense_data["model_used"] = financial_doc.prediction_model
        elif frappe.db.has_column("AI Expense Forecast", "prediction_model"):
            expense_data["prediction_model"] = financial_doc.prediction_model
        
        expense_doc = frappe.get_doc(expense_data)
        expense_doc.insert()
        
        return {
            "success": True,
            "expense_forecast_id": expense_doc.name,
            "message": "Expense forecast created successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
