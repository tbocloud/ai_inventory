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
        # Use the implemented totals calculator
        self.calculate_expense_totals()
        self.analyze_expense_trends()
        # Skip sync during validation to avoid circular dependency
        # self.sync_with_financial_forecast()
    
    @frappe.whitelist()
    def calculate_expense_totals(self):
        """Calculate all expense totals and AI predictions"""
        try:
            # Sum flat category/integration fields to compute total predicted expense
            category_fields = [
                'fixed_expenses',
                'variable_expenses',
                'semi_variable_expenses',
                'inventory_related_expenses',
                'operational_expenses',
                'administrative_expenses',
            ]
            integration_fields = [
                'storage_costs',
                'handling_costs',
                'purchase_related_expenses',
                'reorder_costs',
                'carrying_costs',
                'stockout_costs',
            ]

            def val(fieldname):
                return float(getattr(self, fieldname, 0) or 0)

            categories_total = sum(val(f) for f in category_fields)
            integration_total = sum(val(f) for f in integration_fields)
            total_forecasted = categories_total + integration_total

            # Without explicit actuals, keep 0 unless set elsewhere
            total_actual = float(getattr(self, 'total_actual_expenses', 0) or 0)
            variance_percentage = ((total_actual - total_forecasted) / total_forecasted * 100) if total_forecasted else 0

            # AI predictions and base confidence
            risk_factor = self.calculate_risk_adjustment()
            ai_prediction = total_forecasted * (1 + (risk_factor or 0) / 100.0)
            base_confidence = 85.0
            confidence_score = min(95.0, max(50.0, base_confidence - abs(variance_percentage) * 0.3))

            # Seasonal/efficiency placeholders
            try:
                month = frappe.utils.getdate(self.forecast_date or frappe.utils.today()).month
            except Exception:
                month = None
            self.seasonal_adjustment = 2.5 if month in (11, 12) else 0.0
            self.inflation_factor = 0.0
            self.efficiency_factor = 0.0
            if total_forecasted:
                op_share = (val('operational_expenses') / total_forecasted) if total_forecasted else 0
                self.efficiency_factor = max(0.0, round((0.3 - op_share) * 10, 2))

            # Persist to DocType fields visible in UI
            self.total_predicted_expense = total_forecasted
            self.confidence_score = confidence_score

            # Maintain compatibility fields (if present in DB)
            self.total_forecasted_expenses = total_forecasted
            self.total_actual_expenses = total_actual
            self.expense_variance = variance_percentage
            self.ai_predicted_expenses = ai_prediction
            # Map variance to budget_variance field in Analysis section if present
            if hasattr(self, 'budget_variance'):
                self.budget_variance = variance_percentage

            # Store a JSON breakdown for transparency
            breakdown = {
                'categories': {f: val(f) for f in category_fields},
                'inventory_integration': {f: val(f) for f in integration_fields},
                'totals': {
                    'categories_total': categories_total,
                    'integration_total': integration_total,
                    'grand_total': total_forecasted,
                },
            }
            try:
                self.expense_breakdown = frappe.as_json(breakdown)
            except Exception:
                pass
            
            return {
                'status': 'success',
                'totals': {
                    'forecasted': total_forecasted,
                    'actual': total_actual,
                    'variance': variance_percentage,
                    'ai_prediction': ai_prediction,
                    'confidence': confidence_score,
                    'risk_factor': risk_factor
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error calculating expense totals: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def calculate_risk_adjustment(self):
        """Calculate risk adjustment factor"""
        try:
            base_risk = 5  # 5% base risk
            
            # Historical variance impact
            if hasattr(self, 'expense_variance') and self.expense_variance:
                variance_risk = abs(self.expense_variance) * 0.2
                base_risk += variance_risk
            
            # Market volatility (simplified)
            market_risk = 3  # Assume 3% market risk
            base_risk += market_risk
            
            return min(20, base_risk)  # Cap at 20%
            
        except Exception as e:
            frappe.log_error(f"Error calculating risk adjustment: {str(e)}")
            return 5
    
    @frappe.whitelist()
    def generate_optimization_suggestions(self):
        """Generate expense optimization suggestions"""
        try:
            suggestions = []
            
            # Analyze expense patterns
            high_variance_items = []
            items = getattr(self, 'expense_items', []) or []
            for item in items:
                forecasted = getattr(item, 'forecasted_amount', None)
                actual = getattr(item, 'actual_amount', None)
                if forecasted and actual:
                    try:
                        variance = abs(actual - forecasted) / forecasted * 100
                    except Exception:
                        variance = 0
                    if variance > 20:
                        high_variance_items.append({
                            'category': getattr(item, 'expense_category', None),
                            'variance': variance,
                            'amount': actual
                        })
            
            # Generate suggestions based on analysis
            if high_variance_items:
                suggestions.append({
                    'type': 'cost_control',
                    'title': 'High Variance Categories',
                    'description': f'Monitor {len(high_variance_items)} categories with >20% variance',
                    'priority': 'high',
                    'categories': [item['category'] for item in high_variance_items]
                })
            
            # Budget efficiency suggestions
            if hasattr(self, 'total_actual_expenses') and hasattr(self, 'total_forecasted_expenses'):
                if (self.total_actual_expenses or 0) > (self.total_forecasted_expenses or 0) * 1.1:
                    suggestions.append({
                        'type': 'budget_control',
                        'title': 'Budget Overrun Alert',
                        'description': 'Actual expenses exceed forecast by >10%',
                        'priority': 'high',
                        'action': 'Review and adjust spending controls'
                    })
                elif (self.total_actual_expenses or 0) < (self.total_forecasted_expenses or 0) * 0.9:
                    suggestions.append({
                        'type': 'opportunity',
                        'title': 'Budget Underutilization',
                        'description': 'Actual expenses under forecast by >10%',
                        'priority': 'medium',
                        'action': 'Consider reallocating budget or increasing investments'
                    })
            
            # Store suggestions in custom field if available
            if hasattr(self, 'optimization_suggestions'):
                self.optimization_suggestions = frappe.as_json(suggestions)
            
            return {
                'status': 'success',
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
            
        except Exception as e:
            frappe.log_error(f"Error generating optimization suggestions: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @frappe.whitelist()
    def calculate_risk_factors(self):
        """Calculate comprehensive risk factors"""
        try:
            risk_factors = {
                'variance_risk': 0,
                'category_risk': 0,
                'trend_risk': 0,
                'overall_risk': 0
            }
            
            # Variance-based risk
            if hasattr(self, 'expense_variance') and self.expense_variance:
                risk_factors['variance_risk'] = min(50, abs(self.expense_variance))
            
            # Category concentration risk
            category_totals = {}
            total_expenses = (getattr(self, 'total_forecasted_expenses', 0) or getattr(self, 'total_predicted_expense', 0) or 0)
            
            items = getattr(self, 'expense_items', []) or []
            for item in items:
                category = getattr(item, 'expense_category', None) or 'Other'
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += getattr(item, 'forecasted_amount', 0) or 0
            
            # Check for concentration (>50% in single category)
            if total_expenses > 0:
                max_category_pct = max([amount/total_expenses*100 for amount in category_totals.values()]) if category_totals else 0
                if max_category_pct > 50:
                    risk_factors['category_risk'] = (max_category_pct - 50) * 0.5
            
            # Historical trend risk
            historical_data = frappe.get_all(
                'AI Expense Forecast',
                filters={
                    'company': self.company,
                    'creation': ['<', self.creation or frappe.utils.now()]
                },
                fields=['total_actual_expenses'],
                order_by='creation desc',
                limit=3
            )
            
            if len(historical_data) >= 2:
                recent_trend = historical_data[0].total_actual_expenses or 0
                previous_trend = historical_data[1].total_actual_expenses or 0
                if previous_trend > 0:
                    trend_change = ((recent_trend - previous_trend) / previous_trend) * 100
                    if abs(trend_change) > 15:
                        risk_factors['trend_risk'] = min(30, abs(trend_change) - 15)
            
            # Calculate overall risk
            risk_factors['overall_risk'] = (
                risk_factors['variance_risk'] * 0.4 +
                risk_factors['category_risk'] * 0.3 +
                risk_factors['trend_risk'] * 0.3
            )
            
            # Update risk score field if available
            if hasattr(self, 'risk_score'):
                self.risk_score = risk_factors['overall_risk']
            
            return {
                'status': 'success',
                'risk_factors': risk_factors
            }
            
        except Exception as e:
            frappe.log_error(f"Error calculating risk factors: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @frappe.whitelist()
    def sync_to_financial_forecast(self):
        """Manually trigger sync to AI Financial Forecast"""
        try:
            self.sync_with_financial_forecast()
            return {'status': 'success', 'message': 'Sync completed successfully'}
        except Exception as e:
            frappe.log_error(f"Manual sync error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @frappe.whitelist()
    def get_expense_analytics(self):
        """Generate comprehensive expense analytics"""
        try:
            # Build analysis from flat fields on the DocType
            field_map = {
                'Fixed': getattr(self, 'fixed_expenses', 0) or 0,
                'Variable': getattr(self, 'variable_expenses', 0) or 0,
                'Semi Variable': getattr(self, 'semi_variable_expenses', 0) or 0,
                'Inventory Related': getattr(self, 'inventory_related_expenses', 0) or 0,
                'Operational': getattr(self, 'operational_expenses', 0) or 0,
                'Administrative': getattr(self, 'administrative_expenses', 0) or 0,
            }
            total_forecasted = sum(field_map.values())
            category_analysis = {}
            for name, amount in field_map.items():
                category_analysis[name] = {
                    'forecasted': amount,
                    'actual': 0,
                    'count': 1,
                    'percentage': (amount / total_forecasted * 100) if total_forecasted else 0,
                }
            
            # Performance metrics
            accuracy_metrics = {
                'forecast_accuracy': 0,
                'budget_utilization': 0,
                'category_count': len(category_analysis),
                'highest_category': None,
                'optimization_potential': 0
            }
            
            if getattr(self, 'total_actual_expenses', 0) and (getattr(self, 'total_forecasted_expenses', 0) or getattr(self, 'total_predicted_expense', 0)):
                accuracy_metrics['forecast_accuracy'] = (
                    100 - abs((self.total_actual_expenses or 0) - (self.total_predicted_expense or self.total_forecasted_expenses or 0)) /
                    (self.total_predicted_expense or self.total_forecasted_expenses or 1) * 100
                )
                accuracy_metrics['budget_utilization'] = (
                    (self.total_actual_expenses or 0) / (self.total_predicted_expense or self.total_forecasted_expenses or 1) * 100
                )
            
            # Find highest expense category
            if category_analysis:
                highest_cat = max(category_analysis, key=lambda x: category_analysis[x]['forecasted'])
                accuracy_metrics['highest_category'] = {
                    'name': highest_cat,
                    'amount': category_analysis[highest_cat]['forecasted'],
                    'percentage': category_analysis[highest_cat]['percentage']
                }
            
            # Calculate optimization potential
            optimization_potential = 0
            for category, data in category_analysis.items():
                if data['actual'] > data['forecasted'] * 1.2:  # 20% over budget
                    optimization_potential += (data['actual'] - data['forecasted'])
            
            accuracy_metrics['optimization_potential'] = optimization_potential
            
            return {
                'status': 'success',
                'analytics': {
                    'category_analysis': category_analysis,
                    'accuracy_metrics': accuracy_metrics,
                    'total_categories': len(category_analysis)
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error generating expense analytics: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def calculate_expense_growth(self):
        """Calculate expense growth rate compared to previous forecast"""
        try:
            current_total = (
                getattr(self, 'total_predicted_expense', 0)
                or getattr(self, 'total_predicted_expenses', 0)
                or getattr(self, 'predicted_expenses', 0)
            )
            
            if not current_total:
                return
            
            # Get previous forecast
            previous = frappe.get_all(
                "AI Expense Forecast",
                filters={
                    "company": self.company,
                    "forecast_date": ["<", self.forecast_date],
                    "name": ["!=", self.name]
                },
                fields=["total_predicted_expense", "total_predicted_expenses", "predicted_expenses"],
                order_by="forecast_date desc",
                limit=1
            )
            
            if previous:
                prev_total = (
                    previous[0].get('total_predicted_expense')
                    or previous[0].get('total_predicted_expenses')
                    or previous[0].get('predicted_expenses')
                )
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
        # Get current total from the correct field
        current_total = getattr(self, 'total_predicted_expense', 0) or getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
        
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
        current_total = (
            getattr(self, 'total_predicted_expense', 0)
            or getattr(self, 'total_predicted_expenses', 0)
            or getattr(self, 'predicted_expenses', 0)
        )
        if current_total and current_total > 1000000:  # Over 1M
            risk_score += 15
        
        # Set risk score in available field
        if hasattr(self, 'risk_score'):
            self.risk_score = min(100, risk_score)
        elif hasattr(self, 'expense_risk'):
            self.expense_risk = min(100, risk_score)
    
    @frappe.whitelist()
    def sync_with_financial_forecast(self):
        """Sync data with AI Financial Forecast"""
        if not self.company:
            return {"success": False, "message": "Company not specified"}
        
        try:
            # Get the current total expense amount from the correct field
            current_total = getattr(self, 'total_predicted_expense', 0) or getattr(self, 'total_predicted_expenses', 0) or getattr(self, 'predicted_expenses', 0)
            
            # Find or create corresponding AI Financial Forecast
            existing_forecast = frappe.get_all(
                "AI Financial Forecast",
                filters={
                    "company": self.company,
                    "forecast_type": "Expense",
                    "forecast_start_date": self.forecast_date,
                },
                limit=1,
            )
            
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
        
        # Build expense breakdown including integration fields
        expense_breakdown = {}
        integration_fields = {"storage_costs", "handling_costs", "purchase_related_expenses", "reorder_costs", "carrying_costs", "stockout_costs"}
        for field in self.meta.fields:
            if field.fieldtype == "Currency":
                fname = field.fieldname
                if ("expense" in fname.lower()) or (fname in integration_fields):
                    value = getattr(self, fname, 0)
                    if value:
                        expense_breakdown[fname] = value
        
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
            
            # Build expense breakdown including integration fields
            expense_breakdown = {}
            integration_fields = {"storage_costs", "handling_costs", "purchase_related_expenses", "reorder_costs", "carrying_costs", "stockout_costs"}
            for field in self.meta.fields:
                if field.fieldtype == "Currency":
                    fname = field.fieldname
                    if ("expense" in fname.lower()) or (fname in integration_fields):
                        value = getattr(self, fname, 0)
                        if value:
                            expense_breakdown[fname] = value
            
            forecast_doc = frappe.get_doc({
                "doctype": "AI Financial Forecast",
                "company": self.company,
                "forecast_type": "Expense",
                "forecast_start_date": self.forecast_date,
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
        
        current_total = (
            getattr(self, 'total_predicted_expense', 0)
            or getattr(self, 'total_predicted_expenses', 0)
            or getattr(self, 'predicted_expenses', 0)
        )
        if current_total and current_total > 1000000:
            risk_factors.append(f"Large expense amount: {frappe.utils.fmt_money(current_total)}")
        
        confidence = getattr(self, 'confidence_score', 0) or getattr(self, 'prediction_confidence', 75)
        if confidence < 70:
            risk_factors.append(f"Low prediction confidence: {confidence}%")
        
        return risk_factors
    
    def before_save(self):
        """Actions before saving"""
        # Ensure totals and analytics are up to date before save
        self.calculate_expense_totals()
        self.generate_optimization_suggestions()
        self.calculate_risk_factors()
        # Safe no-ops if not needed
        self.set_inventory_integration()
        self.calculate_historical_accuracy()
        self.last_updated = frappe.utils.now()

        # Enable sync after calculation
        self.sync_with_financial_forecast()

        # Set alert status based on risk score if available
        risk_score = getattr(self, 'risk_score', None) or getattr(self, 'expense_risk', None)
        if risk_score is not None:
            if risk_score >= 70:
                self.alert_status = 'Critical'
            elif risk_score >= 40:
                self.alert_status = 'Warning'
            else:
                self.alert_status = 'Normal'
        # Update growth rate based on prior record
        self.calculate_expense_growth()
    
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

    # --- Minimal, safe helpers to avoid missing method errors ---
    def set_inventory_integration(self):
        """Placeholder for inventory integration hooks (safe no-op)."""
        return

    def calculate_historical_accuracy(self):
        """Placeholder to compute historical accuracy metrics (safe no-op)."""
        return

@frappe.whitelist()
def create_expense_forecast_from_financial(financial_forecast_name):
    """Create expense forecast from AI Financial Forecast"""
    try:
        financial_doc = frappe.get_doc("AI Financial Forecast", financial_forecast_name)
        
        if financial_doc.forecast_type != "Expense":
            return {"success": False, "error": "Source forecast must be Expense type"}
        
        # Check if expense forecast already exists
        existing = frappe.get_all(
            "AI Expense Forecast",
            filters={
                "company": financial_doc.company,
                "forecast_date": financial_doc.forecast_start_date
            },
            limit=1
        )
        
        if existing:
            return {"success": False, "error": "Expense forecast already exists for this date"}
        
        # Create new expense forecast
        expense_data = {
            "doctype": "AI Expense Forecast",
            "company": financial_doc.company,
            "forecast_date": financial_doc.forecast_start_date
        }
        
        # Set expense amount in available field
        # Set total predicted expenses in available field
        if frappe.db.has_column("AI Expense Forecast", "total_predicted_expense"):
            expense_data["total_predicted_expense"] = financial_doc.predicted_amount
        elif frappe.db.has_column("AI Expense Forecast", "total_predicted_expenses"):
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

# --------------------------------------------------------------------------------------
# Module-level wrappers for UI calls (expected by client JS)
# --------------------------------------------------------------------------------------

@frappe.whitelist()
def sync_with_financial_forecast(expense_name: str):
    """Wrapper to sync an expense forecast to AI Financial Forecast and return a routeable id."""
    try:
        doc = frappe.get_doc("AI Expense Forecast", expense_name)
        doc.sync_with_financial_forecast()

        # Find the corresponding AI Financial Forecast for this expense forecast/date
        ff = frappe.get_all(
            "AI Financial Forecast",
            filters={
                "company": doc.company,
                "forecast_type": "Expense",
                "forecast_start_date": doc.forecast_date,
            },
            fields=["name"],
            limit=1,
        )
        ff_name = ff[0].name if ff else None
        return {"success": True, "financial_forecast_name": ff_name}
    except Exception as e:
        frappe.log_error(f"Expense sync wrapper error: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def analyze_expense_trends(expense_name: str):
    """Wrapper to analyze expense trends on a specific document."""
    try:
        doc = frappe.get_doc("AI Expense Forecast", expense_name)
        doc.analyze_expense_trends()
        doc.save(ignore_permissions=True)
        return {"success": True}
    except Exception as e:
        frappe.log_error(f"Expense trend analysis error: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def calculate_expense_risks(expense_name: str):
    """Wrapper to calculate risk factors and risk score for an expense forecast."""
    try:
        doc = frappe.get_doc("AI Expense Forecast", expense_name)
        # Compute both granular factors and aggregate risk score
        risk_factors_result = doc.calculate_risk_factors()
        doc.calculate_expense_risks()
        doc.save(ignore_permissions=True)

        # Derive a simple risk level for UI feedback
        risk_score = getattr(doc, "risk_score", None) or getattr(doc, "expense_risk", None) or 0
        level = "Low"
        if risk_score >= 70:
            level = "High"
        elif risk_score >= 40:
            level = "Medium"

        return {"success": True, "risk_level": level, "message": "Risk factors updated", "details": risk_factors_result}
    except Exception as e:
        frappe.log_error(f"Expense risk calc error: {str(e)}")
        return {"success": False, "error": str(e)}
