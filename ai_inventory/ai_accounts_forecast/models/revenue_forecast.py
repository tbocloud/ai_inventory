"""
Revenue Forecasting Module
Integrates with inventory demand forecasting for accurate revenue predictions
"""

import frappe
from frappe.model.document import Document
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class RevenueForecaster:
    """
    Revenue forecasting with inventory demand integration
    """
    
    def __init__(self, company):
        self.company = company
        
    def predict_revenue(self, forecast_period="Monthly"):
        """
        Main revenue prediction method combining sales history and inventory forecasts
        """
        # Get historical sales data
        historical_sales = self.get_historical_sales_data()
        
        # Get inventory-based sales predictions
        inventory_sales_forecast = self.get_inventory_based_sales_forecast()
        
        # Get customer-based revenue forecasts
        customer_forecasts = self.get_customer_revenue_forecasts()
        
        # Combine seasonal and market factors
        seasonal_factors = self.calculate_seasonal_factors()
        market_factors = self.get_market_factors()
        
        # Integrate all data sources
        integrated_data = self.integrate_revenue_data(
            historical_sales, inventory_sales_forecast, 
            customer_forecasts, seasonal_factors, market_factors
        )
        
        # Run revenue prediction model
        prediction = self.run_revenue_model(integrated_data, forecast_period)
        
        return prediction
    
    def get_inventory_based_sales_forecast(self):
        """
        Convert inventory consumption forecasts to revenue forecasts
        """
        inventory_forecasts = frappe.get_all("AI Inventory Forecast",
            filters={"company": self.company},
            fields=["item_code", "predicted_consumption", "confidence_score", 
                   "movement_type", "forecast_details"]
        )
        
        revenue_forecasts = []
        
        for forecast in inventory_forecasts:
            # Get item pricing information
            item_price = self.get_item_selling_price(forecast["item_code"])
            
            if item_price:
                # Calculate predicted revenue from consumption
                predicted_revenue = forecast["predicted_consumption"] * item_price["rate"]
                
                # Adjust based on movement type
                movement_multiplier = self.get_movement_type_multiplier(forecast["movement_type"])
                adjusted_revenue = predicted_revenue * movement_multiplier
                
                revenue_forecasts.append({
                    "item_code": forecast["item_code"],
                    "predicted_quantity": forecast["predicted_consumption"],
                    "unit_price": item_price["rate"],
                    "predicted_revenue": adjusted_revenue,
                    "confidence": forecast["confidence_score"],
                    "movement_type": forecast["movement_type"]
                })
        
        return revenue_forecasts
    
    def get_customer_revenue_forecasts(self):
        """
        Predict revenue by customer based on historical patterns
        """
        customers = frappe.get_all("Customer", 
                                 filters={"disabled": 0}, 
                                 fields=["name", "customer_group", "territory"])
        
        customer_forecasts = []
        
        for customer in customers:
            # Get customer's historical sales
            historical_sales = self.get_customer_historical_sales(customer["name"])
            
            if historical_sales:
                # Predict future sales for this customer
                customer_prediction = self.predict_customer_sales(customer, historical_sales)
                customer_forecasts.append(customer_prediction)
        
        return customer_forecasts
    
    def calculate_seasonal_factors(self):
        """
        Calculate seasonal factors from historical sales data
        """
        # Get monthly sales data for the last 3 years
        monthly_sales = frappe.db.sql("""
            SELECT 
                MONTH(posting_date) as month,
                YEAR(posting_date) as year,
                SUM(grand_total) as total_sales
            FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 36 MONTH)
            GROUP BY YEAR(posting_date), MONTH(posting_date)
            ORDER BY year, month
        """, self.company, as_dict=True)
        
        if not monthly_sales:
            return {month: 1.0 for month in range(1, 13)}  # No seasonal adjustment
        
        # Calculate seasonal indices
        df = pd.DataFrame(monthly_sales)
        df['month_year'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
        
        # Calculate average sales per month across years
        monthly_avg = df.groupby('month')['total_sales'].mean()
        overall_avg = monthly_avg.mean()
        
        # Calculate seasonal factors
        seasonal_factors = {}
        for month in range(1, 13):
            if month in monthly_avg.index:
                seasonal_factors[month] = monthly_avg[month] / overall_avg
            else:
                seasonal_factors[month] = 1.0
        
        return seasonal_factors
    
    def get_market_factors(self):
        """
        Get external market factors that might affect revenue
        """
        # This could integrate with external APIs for economic indicators
        # For now, return default factors
        return {
            "economic_growth_factor": 1.02,  # 2% growth assumption
            "inflation_factor": 1.03,        # 3% inflation
            "industry_growth_factor": 1.05,  # 5% industry growth
            "competitive_factor": 0.98       # 2% competitive pressure
        }
    
    def integrate_revenue_data(self, historical, inventory, customers, seasonal, market):
        """
        Integrate all revenue data sources into comprehensive dataset
        """
        return {
            "historical_sales": historical,
            "inventory_based_forecast": inventory,
            "customer_forecasts": customers,
            "seasonal_factors": seasonal,
            "market_factors": market,
            "integration_timestamp": datetime.now()
        }
    
    def run_revenue_model(self, integrated_data, forecast_period):
        """
        Run AI model for revenue prediction
        """
        from ai_inventory.ai_accounts_forecast.algorithms.time_series_models import RevenueTimeSeriesModel
        
        model = RevenueTimeSeriesModel()
        
        # Prepare data for model
        model_data = self.prepare_revenue_model_data(integrated_data)
        
        # Run prediction
        prediction = model.predict(model_data, forecast_period)
        
        # Apply seasonal and market adjustments
        adjusted_prediction = self.apply_adjustments(
            prediction, 
            integrated_data["seasonal_factors"], 
            integrated_data["market_factors"]
        )
        
        return adjusted_prediction
    
    def get_item_selling_price(self, item_code):
        """Get current selling price for an item"""
        price = frappe.db.get_value("Item Price", 
                                   {"item_code": item_code, "selling": 1}, 
                                   ["price_list_rate", "valid_from", "valid_upto"], 
                                   as_dict=True)
        return price
    
    def get_movement_type_multiplier(self, movement_type):
        """Get multiplier based on item movement type"""
        multipliers = {
            "Fast Moving": 1.1,
            "Slow Moving": 0.8,
            "Non Moving": 0.3,
            "Critical": 1.2
        }
        return multipliers.get(movement_type, 1.0)

# API Methods for Revenue Forecasting

@frappe.whitelist()
def create_revenue_forecast(company, forecast_period="Monthly"):
    """Create revenue forecast for a company"""
    try:
        forecaster = RevenueForecaster(company)
        forecast_data = forecaster.predict_revenue(forecast_period)
        
        # Create revenue forecast document
        revenue_doc = frappe.get_doc({
            "doctype": "AI Revenue Forecast",
            "company": company,
            "forecast_date": datetime.now().date(),
            "forecast_period": forecast_period,
            "total_predicted_revenue": forecast_data.get("total_revenue", 0),
            "growth_rate": forecast_data.get("growth_rate", 0),
            "confidence_score": forecast_data.get("confidence", 0),
            "inventory_based_sales": forecast_data.get("inventory_revenue", 0),
            "seasonal_factor": forecast_data.get("seasonal_adjustment", 1.0),
            "forecast_breakdown": json.dumps(forecast_data.get("breakdown", {}))
        })
        
        revenue_doc.save()
        
        return {
            "status": "success",
            "forecast_id": revenue_doc.name,
            "predicted_revenue": revenue_doc.total_predicted_revenue,
            "confidence": revenue_doc.confidence_score
        }
        
    except Exception as e:
        frappe.log_error(f"Revenue Forecast Error: {str(e)}")
        return {"status": "error", "message": str(e)}