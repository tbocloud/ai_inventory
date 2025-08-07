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
        self.calculate_totals()
        self.analyze_growth_trends()
        # Skip sync during validation to avoid circular dependency
        # self.sync_with_financial_forecast()
    
    def calculate_totals(self):
        """Calculate total predicted revenue"""
        revenue_fields = ['product_revenue', 'service_revenue', 'recurring_revenue',
                         'one_time_revenue', 'commission_revenue', 'other_revenue']
        
        total_revenue = sum(getattr(self, field, 0) or 0 for field in revenue_fields)
        self.total_predicted_revenue = total_revenue
        
        # Calculate growth rate if previous forecast exists
        self.calculate_growth_rate()
    
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
    
    def analyze_growth_trends(self):
        """Analyze revenue growth trends and set confidence"""
        if not self.total_predicted_revenue:
            self.confidence_score = 50
            return
        
        # Base confidence on data completeness
        completeness = self.calculate_data_completeness()
        
        # Adjust based on growth rate stability
        stability_factor = self.calculate_stability_factor()
        
        # Calculate final confidence score
        self.confidence_score = min(95, (completeness + stability_factor) / 2)
        
        # Set seasonal and market factors
        self.seasonal_factor = self.calculate_seasonal_factor()
        self.market_factor = self.calculate_market_factor()
        
        # Calculate risk adjustment
        self.risk_adjustment = self.calculate_risk_adjustment()
    
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
    
    def sync_with_financial_forecast(self):
        """Sync data with AI Financial Forecast"""
        if not self.company:
            return
        
        try:
            # Find or create corresponding AI Financial Forecast
            existing_forecast = frappe.get_all("AI Financial Forecast",
                                             filters={
                                                 "company": self.company,
                                                 "forecast_type": "Revenue",
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
            frappe.log_error(f"Revenue sync error: {str(e)}")
    
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
            forecast_doc = frappe.get_doc({
                "doctype": "AI Financial Forecast",
                "company": self.company,
                "forecast_type": "Revenue",
                "forecast_date": self.forecast_date,
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
            
        except Exception as e:
            frappe.log_error(f"Error creating financial forecast from revenue: {str(e)}")
    
    def before_save(self):
        """Actions before saving"""
        self.set_inventory_integration()
        self.calculate_historical_accuracy()
        self.last_updated = frappe.utils.now()
    
    def set_inventory_integration(self):
        """Set inventory-based revenue calculations"""
        try:
            # Get inventory data for revenue prediction
            inventory_items = frappe.get_all("Item",
                                           filters={"is_sales_item": 1},
                                           fields=["item_code", "standard_rate"])
            
            if inventory_items:
                # Calculate inventory-based sales potential
                fast_moving_value = 0
                slow_moving_value = 0
                
                for item in inventory_items[:10]:  # Top 10 items for simplification
                    rate = item.standard_rate or 0
                    # Simplified calculation - in real implementation, use velocity data
                    fast_moving_value += rate * 10  # Assume 10 units
                    slow_moving_value += rate * 3   # Assume 3 units
                
                self.inventory_based_sales = fast_moving_value + slow_moving_value
                self.fast_moving_items_revenue = fast_moving_value
                self.slow_moving_items_revenue = slow_moving_value
                
                # Calculate reorder impact (simplified)
                self.reorder_impact_revenue = fast_moving_value * 0.1  # 10% boost from restocking
                
                # Stockout risk (revenue at risk)
                self.stockout_risk_revenue = fast_moving_value * 0.05  # 5% at risk
                
        except Exception as e:
            frappe.log_error(f"Inventory integration error: {str(e)}")
    
    def calculate_historical_accuracy(self):
        """Calculate historical forecast accuracy"""
        try:
            # Get actual vs predicted from previous forecasts
            past_forecasts = frappe.get_all("AI Revenue Forecast",
                                          filters={
                                              "company": self.company,
                                              "forecast_date": ["<", frappe.utils.nowdate()],
                                              "docstatus": 1
                                          },
                                          fields=["total_predicted_revenue", "forecast_date"],
                                          limit=5)
            
            if not past_forecasts:
                self.historical_accuracy = 0
                return
            
            # Simplified accuracy calculation
            # In real implementation, compare with actual sales data
            accuracy_scores = []
            
            for forecast in past_forecasts:
                # Mock accuracy based on prediction reasonableness
                predicted = forecast.total_predicted_revenue or 0
                if predicted > 0:
                    # Assume accuracy based on prediction stability
                    accuracy = min(95, 60 + (40 * (1 / (1 + abs(self.growth_rate or 0) / 100))))
                    accuracy_scores.append(accuracy)
            
            if accuracy_scores:
                self.historical_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            else:
                self.historical_accuracy = 0
                
        except Exception as e:
            frappe.log_error(f"Historical accuracy calculation error: {str(e)}")
            self.historical_accuracy = 0

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
                                    "forecast_date": financial_doc.forecast_date
                                },
                                limit=1)
        
        if existing:
            return {"success": False, "error": "Revenue forecast already exists for this date"}
        
        # Create new revenue forecast
        revenue_doc = frappe.get_doc({
            "doctype": "AI Revenue Forecast",
            "company": financial_doc.company,
            "forecast_date": financial_doc.forecast_date,
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
