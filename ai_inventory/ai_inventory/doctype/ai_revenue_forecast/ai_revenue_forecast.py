# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class AIRevenueForecast(Document):
    """AI Revenue Forecast with sync to AI Financial Forecast"""
    
    def validate(self):
        """Validate revenue forecast data"""
        self.calculate_revenue_totals()
        self.analyze_growth_trends()
        # Skip sync during validation to avoid circular dependency
        # self.sync_with_financial_forecast()
    
    @frappe.whitelist()
    def calculate_revenue_totals(self):
        """Calculate totals from top-level category fields and set predictions."""
        try:
            # Sum category fields from the DocType
            categories = [
                'product_revenue', 'service_revenue', 'recurring_revenue',
                'one_time_revenue', 'commission_revenue', 'other_revenue'
            ]
            total_revenue = sum((getattr(self, f, 0) or 0) for f in categories)

            # Basic growth rate heuristic vs previous period
            self.total_predicted_revenue = total_revenue
            self.calculate_growth_rate()
            growth_rate = getattr(self, 'growth_rate', 0) or 0

            # Confidence heuristic
            confidence_score = min(95, max(50, 80 + (growth_rate * 0.3)))
            self.confidence_score = confidence_score

            return {
                'status': 'success',
                'totals': {
                    'total_revenue': total_revenue,
                    'growth_rate': growth_rate,
                    'confidence': confidence_score,
                }
            }
        except Exception as e:
            frappe.log_error(f"Error calculating revenue totals: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @frappe.whitelist()
    def analyze_growth_trends(self):
        """Analyze revenue growth trends and compute trend fields."""
        # Delegate to compute_prediction_factors for scoring-related fields
        try:
            self.compute_prediction_factors()
            # Set simple trend direction/strength using growth_rate
            gr = self.growth_rate or 0
            if gr > 5:
                self.trend_direction = "increasing"
                self.trend_strength = min(100, abs(gr))
            elif gr < -5:
                self.trend_direction = "decreasing"
                self.trend_strength = min(100, abs(gr))
            else:
                self.trend_direction = "stable"
                self.trend_strength = max(0, 5 - abs(gr)) * 10
            return {
                'status': 'success',
                'trend': {
                    'direction': self.trend_direction,
                    'strength': self.trend_strength,
                }
            }
        except Exception as e:
            frappe.log_error(f"Error analyzing growth trends: {str(e)}")
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
    def get_ai_insights(self):
        """Generate AI-powered insights for revenue forecast"""
        try:
            insights = []
            
            # Revenue growth analysis
            if hasattr(self, 'revenue_growth_rate') and self.revenue_growth_rate:
                if self.revenue_growth_rate > 10:
                    insights.append({
                        'type': 'positive',
                        'title': 'Strong Growth Projected',
                        'message': f'Revenue growth rate of {self.revenue_growth_rate:.1f}% indicates strong business expansion'
                    })
                elif self.revenue_growth_rate < -5:
                    insights.append({
                        'type': 'warning',
                        'title': 'Revenue Decline Alert',
                        'message': f'Negative growth rate of {self.revenue_growth_rate:.1f}% requires attention'
                    })
            
            # Confidence score analysis
            if hasattr(self, 'ai_confidence_score') and self.ai_confidence_score:
                if self.ai_confidence_score < 70:
                    insights.append({
                        'type': 'info',
                        'title': 'Low Confidence Score',
                        'message': f'Confidence at {self.ai_confidence_score:.1f}% - consider additional data validation'
                    })
                elif self.ai_confidence_score > 90:
                    insights.append({
                        'type': 'positive',
                        'title': 'High Confidence Forecast',
                        'message': f'Strong confidence at {self.ai_confidence_score:.1f}% indicates reliable predictions'
                    })
            
            # Variance analysis
            if hasattr(self, 'forecast_variance') and self.forecast_variance:
                if abs(self.forecast_variance) > 15:
                    insights.append({
                        'type': 'warning',
                        'title': 'High Forecast Variance',
                        'message': f'Variance of {self.forecast_variance:.1f}% suggests forecast accuracy needs improvement'
                    })
            
            return {
                'status': 'success',
                'insights': insights,
                'total_insights': len(insights)
            }
            
        except Exception as e:
            frappe.log_error(f"Error generating AI insights: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @frappe.whitelist()
    def run_revenue_analytics(self):
        """Run comprehensive revenue analytics"""
        try:
            # Get period comparison data
            period_data = frappe.get_all(
                'AI Revenue Forecast',
                filters={'company': self.company},
                fields=['total_forecasted_revenue', 'total_actual_revenue', 'forecast_period_start'],
                order_by='forecast_period_start desc',
                limit=12
            )
            
            analytics = {
                'total_periods': len(period_data),
                'average_forecast': sum([d.total_forecasted_revenue or 0 for d in period_data]) / max(1, len(period_data)),
                'average_actual': sum([d.total_actual_revenue or 0 for d in period_data]) / max(1, len(period_data)),
                'accuracy_rate': 0,
                'best_month': None,
                'worst_month': None
            }
            
            # Calculate accuracy
            accurate_forecasts = 0
            for period in period_data:
                if period.total_forecasted_revenue and period.total_actual_revenue:
                    variance = abs(period.total_actual_revenue - period.total_forecasted_revenue) / period.total_forecasted_revenue
                    if variance <= 0.1:  # Within 10%
                        accurate_forecasts += 1
            
            if period_data:
                analytics['accuracy_rate'] = (accurate_forecasts / len(period_data)) * 100
            
            # Find best and worst performing periods
            if period_data:
                sorted_by_actual = sorted(period_data, key=lambda x: x.total_actual_revenue or 0, reverse=True)
                analytics['best_month'] = sorted_by_actual[0].forecast_period_start if sorted_by_actual else None
                analytics['worst_month'] = sorted_by_actual[-1].forecast_period_start if sorted_by_actual else None
            
            return {
                'status': 'success',
                'analytics': analytics
            }
            
        except Exception as e:
            frappe.log_error(f"Error running revenue analytics: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def calculate_growth_rate(self):
        """Calculate growth rate compared to previous forecast"""
        try:
            if not self.total_predicted_revenue:
                return
            
            # Get previous forecast
            previous = frappe.get_all("AI Revenue Forecast",
                                    filters={
                                        "company": self.company,
                                        "forecast_date": ["<", self.forecast_date],
                                        "name": ["!=", self.name]
                                    },
                                    fields=["total_predicted_revenue"],
                                    order_by="forecast_date desc",
                                    limit=1)
            
            if previous and previous[0].total_predicted_revenue:
                prev_revenue = previous[0].total_predicted_revenue
                self.growth_rate = ((self.total_predicted_revenue - prev_revenue) / prev_revenue) * 100
            else:
                self.growth_rate = 0
                
        except Exception as e:
            frappe.log_error(f"Growth rate calculation error: {str(e)}")
            self.growth_rate = 0
    
    # analyze_growth_trends implemented earlier in class
    
    def calculate_data_completeness(self):
        """Calculate data completeness score"""
        revenue_fields = ['product_revenue', 'service_revenue', 'recurring_revenue']
        completed_fields = sum(1 for field in revenue_fields if getattr(self, field, 0))
        return (completed_fields / len(revenue_fields)) * 100
    
    def calculate_stability_factor(self):
        """Calculate stability factor based on growth rate"""
        if not hasattr(self, 'growth_rate') or self.growth_rate is None:
            return 70
        
        abs_growth = abs(self.growth_rate)
        
        if abs_growth <= 5:  # Very stable
            return 90
        elif abs_growth <= 15:  # Moderate stability
            return 80
        elif abs_growth <= 30:  # Some volatility
            return 70
        else:  # High volatility
            return 60
    
    def calculate_seasonal_factor(self):
        """Calculate seasonal adjustment factor"""
        if not self.forecast_date:
            return 1.0
        
        month = frappe.utils.getdate(self.forecast_date).month
        
        # Holiday season boost
        if month in [11, 12]:
            return 1.3
        # Post-holiday drop
        elif month in [1, 2]:
            return 0.7
        # Summer months
        elif month in [6, 7, 8]:
            return 0.9
        # Back-to-school/business season
        elif month in [9, 10]:
            return 1.1
        else:
            return 1.0
    
    def calculate_market_factor(self):
        """Calculate market adjustment factor"""
        # Simplified market factor based on industry trends
        # In real implementation, this would use external market data
        
        if self.growth_rate and self.growth_rate > 10:
            return 1.2  # Growing market
        elif self.growth_rate and self.growth_rate < -5:
            return 0.8  # Declining market
        else:
            return 1.0  # Stable market
    
    def calculate_risk_adjustment(self):
        """Calculate risk adjustment percentage"""
        risk_factors = []
        
        # High growth rate indicates higher risk
        if self.growth_rate and abs(self.growth_rate) > 20:
            risk_factors.append(10)
        
        # Low confidence indicates higher risk
        if self.confidence_score and self.confidence_score < 70:
            risk_factors.append(15)
        
        # Heavy dependence on single revenue stream
        total_revenue = self.total_predicted_revenue or 1
        max_category = max([
            self.product_revenue or 0,
            self.service_revenue or 0,
            self.recurring_revenue or 0
        ])
        
        if max_category / total_revenue > 0.8:  # 80% from single source
            risk_factors.append(10)
        
        return sum(risk_factors)

    # --- Revenue Account Resolution for Financial Sync ---
    def resolve_revenue_account(self):
        """Resolve a revenue account for the company to use in AI Financial Forecast.

        Priority:
        1) Revenue account field on this document (if present and set)
        2) Company's default income account
        3) First non-group Income root_type account in the company
        4) Any non-group account in company
        """
        try:
            # If doc has a revenue_account field, prefer it
            if hasattr(self, "revenue_account") and getattr(self, "revenue_account"):
                return self.revenue_account

            # Company default income account
            default_income = frappe.db.get_value("Company", self.company, "default_income_account")
            if default_income:
                return default_income

            # Any Income leaf account
            income_account = frappe.db.get_value(
                "Account",
                filters={
                    "company": self.company,
                    "is_group": 0,
                    "root_type": "Income",
                },
                fieldname="name",
            )
            if income_account:
                return income_account

            # Try by account_type label
            income_type_account = frappe.db.get_value(
                "Account",
                filters={
                    "company": self.company,
                    "is_group": 0,
                    "account_type": "Income Account",
                },
                fieldname="name",
            )
            if income_type_account:
                return income_type_account

            # Fallback: any leaf account for the company
            any_account = frappe.db.get_value(
                "Account",
                filters={"company": self.company, "is_group": 0},
                fieldname="name",
            )
            return any_account
        except Exception:
            return None
    
    @frappe.whitelist()
    def sync_with_financial_forecast(self):
        """Sync data with AI Financial Forecast"""
        if not self.company:
            return {"success": False, "message": "Company not specified"}
        
        try:
            account = self.resolve_revenue_account()
            if not account:
                return {
                    "success": False,
                    "error": "No Revenue Account could be determined. Please set the 'Revenue Account' on this Revenue Forecast or set a Default Income Account in the Company.",
                }
            # Find or create corresponding AI Financial Forecast
            existing_forecast = frappe.get_all("AI Financial Forecast",
                                             filters={
                                                 "company": self.company,
                                                 "forecast_type": "Revenue",
                                                 "forecast_start_date": self.forecast_date
                                             },
                                             limit=1)
            
            if existing_forecast:
                # Update existing forecast
                forecast_doc = frappe.get_doc("AI Financial Forecast", existing_forecast[0].name)
                if account:
                    forecast_doc.account = account
                result = self.update_financial_forecast(forecast_doc)
                return {"success": True, "action": "updated", "forecast_id": forecast_doc.name}
            else:
                # Create new financial forecast
                result = self.create_financial_forecast()
                return {"success": True, "action": "created", "forecast_id": result.get("forecast_id")}
                
        except Exception as e:
            frappe.log_error(f"Revenue sync error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def update_financial_forecast(self, forecast_doc):
        """Update AI Financial Forecast with revenue data"""
        forecast_doc.predicted_amount = self.total_predicted_revenue
        forecast_doc.confidence_score = self.confidence_score
        forecast_doc.forecast_details = json.dumps({
            "revenue_breakdown": {
                "product_revenue": self.product_revenue,
                "service_revenue": self.service_revenue,
                "recurring_revenue": self.recurring_revenue,
                "total_revenue": self.total_predicted_revenue,
                "growth_rate": self.growth_rate,
                "seasonal_factor": self.seasonal_factor,
                "market_factor": self.market_factor,
                "risk_adjustment": self.risk_adjustment
            },
            "source": "AI Revenue Forecast",
            "source_id": self.name
        })
        forecast_doc.last_updated = frappe.utils.now()
        forecast_doc.save(ignore_permissions=True)
    
    def create_financial_forecast(self):
        """Create new AI Financial Forecast from revenue data"""
        try:
            account = self.resolve_revenue_account()
            forecast_doc = frappe.get_doc({
                "doctype": "AI Financial Forecast",
                "company": self.company,
                "forecast_type": "Revenue",
                "forecast_start_date": self.forecast_date,
                "account": account,
                "forecast_period": self.forecast_period,
                "predicted_amount": self.total_predicted_revenue,
                "confidence_score": self.confidence_score or 75,
                "forecast_details": json.dumps({
                    "revenue_breakdown": {
                        "product_revenue": self.product_revenue,
                        "service_revenue": self.service_revenue,
                        "recurring_revenue": self.recurring_revenue,
                        "total_revenue": self.total_predicted_revenue,
                        "growth_rate": self.growth_rate,
                        "seasonal_factor": self.seasonal_factor,
                        "market_factor": self.market_factor,
                        "risk_adjustment": self.risk_adjustment
                    },
                    "source": "AI Revenue Forecast",
                    "source_id": self.name
                }),
                "prediction_model": self.model_used or "Revenue Forecast Model",
                "last_updated": frappe.utils.now()
            })
            forecast_doc.insert(ignore_permissions=True)
            return {"forecast_id": forecast_doc.name}
            
        except Exception as e:
            frappe.log_error(f"Error creating financial forecast from revenue: {str(e)}")
    
    def before_save(self):
        """Actions before saving"""
        # Auto-populate from Sales if empty and we have company+date
        try:
            if not self.total_predicted_revenue and self.company and self.forecast_date:
                self.populate_from_sales()
        except Exception as e:
            frappe.log_error(f"Revenue populate_from_sales failed: {str(e)}")

        self.calculate_revenue_totals()
        # Derive growth-related and predictive factors
        self.calculate_growth_rate()
        # Seasonal/market/risk factors are derived below in compute_prediction_factors
        self.compute_prediction_factors()
        self.set_inventory_integration()
        self.calculate_historical_accuracy()
        self.last_updated = frappe.utils.now()
        
        # Enable sync after calculation
        self.sync_with_financial_forecast()

    def compute_prediction_factors(self):
        """Analyze revenue trend-related confidence and factors."""
        if not self.total_predicted_revenue:
            self.confidence_score = 50
            return
        completeness = self.calculate_data_completeness()
        stability_factor = self.calculate_stability_factor()
        self.confidence_score = min(95, (completeness + stability_factor) / 2)
        self.seasonal_factor = self.calculate_seasonal_factor()
        self.market_factor = self.calculate_market_factor()
        self.risk_adjustment = self.calculate_risk_adjustment()

    def set_inventory_integration(self, enabled: bool = True):
        """Derive inventory-related revenue signals.

        When enabled=False, clears inventory-derived fields.
        """
        try:
            fields = [
                "inventory_based_sales",
                "fast_moving_items_revenue",
                "slow_moving_items_revenue",
                "reorder_impact_revenue",
                "stockout_risk_revenue",
            ]
            if not enabled:
                for f in fields:
                    setattr(self, f, 0)
                return {"status": "success", "message": "Inventory integration disabled"}

            inventory_items = frappe.get_all(
                "Item",
                filters={"is_sales_item": 1},
                fields=["item_code", "standard_rate"],
            )

            if not inventory_items:
                for f in fields:
                    setattr(self, f, 0)
                return {"status": "success", "message": "No inventory items found"}

            fast_moving_value = 0.0
            slow_moving_value = 0.0
            for item in inventory_items[:10]:  # Simplified: top 10 items
                rate = float(item.get("standard_rate") or 0)
                fast_moving_value += rate * 10  # Assume 10 units
                slow_moving_value += rate * 3   # Assume 3 units

            self.fast_moving_items_revenue = fast_moving_value
            self.slow_moving_items_revenue = slow_moving_value
            self.inventory_based_sales = fast_moving_value + slow_moving_value
            self.reorder_impact_revenue = fast_moving_value * 0.1  # 10% boost
            self.stockout_risk_revenue = fast_moving_value * 0.05  # 5% at risk

            return {
                "status": "success",
                "fast_moving": fast_moving_value,
                "slow_moving": slow_moving_value,
                "inventory_based_sales": self.inventory_based_sales,
            }
        except Exception as e:
            frappe.log_error(f"Inventory integration error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def calculate_historical_accuracy(self):
        """Calculate historical forecast accuracy (simplified)."""
        try:
            past_forecasts = frappe.get_all(
                "AI Revenue Forecast",
                filters={
                    "company": self.company,
                    "forecast_date": ["<", frappe.utils.nowdate()],
                    "docstatus": 1,
                },
                fields=["total_predicted_revenue", "forecast_date"],
                limit=5,
            )

            if not past_forecasts:
                self.historical_accuracy = 0
                return {"status": "success", "historical_accuracy": 0}

            accuracy_scores = []
            for forecast in past_forecasts:
                predicted = forecast.total_predicted_revenue or 0
                if predicted > 0:
                    accuracy = min(
                        95,
                        60 + (40 * (1 / (1 + abs(self.growth_rate or 0) / 100))),
                    )
                    accuracy_scores.append(accuracy)

            self.historical_accuracy = (
                sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
            )
            return {"status": "success", "historical_accuracy": self.historical_accuracy}
        except Exception as e:
            frappe.log_error(f"Historical accuracy calculation error: {str(e)}")
            self.historical_accuracy = 0
            return {"status": "error", "message": str(e)}

    def populate_from_sales(self):
        """Populate revenue fields from Sales Invoice totals for the month."""
        if not (self.company and self.forecast_date):
            return
        from frappe.utils import get_first_day, get_last_day
        month_start = get_first_day(self.forecast_date)
        month_end = get_last_day(self.forecast_date)
        rows = frappe.db.sql(
            """
            SELECT COALESCE(SUM(base_net_total), 0) AS total_sales
            FROM `tabSales Invoice`
            WHERE company = %s
              AND docstatus = 1
              AND is_return = 0
              AND posting_date BETWEEN %s AND %s
            """,
            (self.company, month_start, month_end),
            as_dict=True,
        )
        total_sales = float((rows[0] or {}).get("total_sales", 0)) if rows else 0.0
        if total_sales:
            self.product_revenue = total_sales
            self.total_predicted_revenue = total_sales
            self.model_used = self.model_used or "Sales Monthly Auto"
            self.last_updated = frappe.utils.now()

@frappe.whitelist()
def populate_from_sales(revenue_name: str):
    """Module-level wrapper to populate a Revenue Forecast from Sales."""
    try:
        doc = frappe.get_doc("AI Revenue Forecast", revenue_name)
        doc.populate_from_sales()
        doc.calculate_revenue_totals()
        doc.compute_prediction_factors()
        doc.save()
        return {"success": True, "message": "Populated from Sales and recalculated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def create_revenue_forecast_from_financial(financial_forecast_name):
    """Create revenue forecast from AI Financial Forecast"""
    try:
        financial_doc = frappe.get_doc("AI Financial Forecast", financial_forecast_name)
        
        if financial_doc.forecast_type != "Revenue":
            return {"success": False, "error": "Source forecast must be Revenue type"}
        
        # Check if revenue forecast already exists
        existing = frappe.get_all("AI Revenue Forecast",
                                filters={
                                    "company": financial_doc.company,
                                    "forecast_date": financial_doc.forecast_start_date
                                },
                                limit=1)
        
        if existing:
            return {"success": False, "error": "Revenue forecast already exists for this date"}
        
        # Create new revenue forecast
        revenue_doc = frappe.get_doc({
            "doctype": "AI Revenue Forecast",
            "company": financial_doc.company,
            "forecast_date": financial_doc.forecast_start_date,
            "forecast_period": "Monthly",
            "total_predicted_revenue": financial_doc.predicted_amount,
            "confidence_score": financial_doc.confidence_score,
            "model_used": financial_doc.prediction_model,
            "last_updated": frappe.utils.now()
        })
        
        revenue_doc.insert()
        
        return {
            "success": True,
            "revenue_forecast_id": revenue_doc.name,
            "message": "Revenue forecast created successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# Module-level wrapper functions for API access
@frappe.whitelist()
def sync_with_financial_forecast(revenue_name: str):
    """Sync a specific Revenue Forecast to its Financial Forecast and return the target id."""
    try:
        revenue_doc = frappe.get_doc("AI Revenue Forecast", revenue_name)
        result = revenue_doc.sync_with_financial_forecast()
        return {
            "success": True,
            "message": "Sync completed successfully",
            "result": result,
        }
    except Exception as e:
        frappe.log_error(f"Error in sync_with_financial_forecast: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def analyze_growth_trends(revenue_name: str):
    """Analyze growth trends for a specific Revenue Forecast."""
    try:
        revenue_doc = frappe.get_doc("AI Revenue Forecast", revenue_name)
        result = revenue_doc.analyze_growth_trends()
        return {"success": True, "message": "Growth trends analyzed successfully", "result": result}
    except Exception as e:
        frappe.log_error(f"Error in analyze_growth_trends: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def calculate_historical_accuracy(revenue_name: str):
    """Calculate historical accuracy for a specific Revenue Forecast."""
    try:
        revenue_doc = frappe.get_doc("AI Revenue Forecast", revenue_name)
        result = revenue_doc.calculate_historical_accuracy()
        return {
            "success": True,
            "message": "Historical accuracy calculated successfully",
            "result": result,
            "accuracy": result.get("historical_accuracy", 0) if isinstance(result, dict) else 0,
        }
    except Exception as e:
        frappe.log_error(f"Error in calculate_historical_accuracy: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def set_inventory_integration(revenue_name: str, enabled: bool = True):
    """Toggle/compute inventory-derived metrics for a specific Revenue Forecast."""
    try:
        revenue_doc = frappe.get_doc("AI Revenue Forecast", revenue_name)
        result = revenue_doc.set_inventory_integration(enabled)
        revenue_doc.calculate_revenue_totals()
        revenue_doc.compute_prediction_factors()
        revenue_doc.save()
        return {"success": True, "message": "Inventory integration updated successfully", "result": result}
    except Exception as e:
        frappe.log_error(f"Error in set_inventory_integration: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def calculate_revenue_totals(revenue_name: str):
    """Recalculate totals for a specific Revenue Forecast."""
    try:
        revenue_doc = frappe.get_doc("AI Revenue Forecast", revenue_name)
        result = revenue_doc.calculate_revenue_totals()
        revenue_doc.compute_prediction_factors()
        revenue_doc.save()
        return {"success": True, "message": "Revenue totals calculated successfully", "result": result}
    except Exception as e:
        frappe.log_error(f"Error in calculate_revenue_totals: {str(e)}")
        return {"success": False, "error": str(e)}
