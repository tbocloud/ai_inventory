"""
Expense Forecasting Module
Integrates with inventory carrying costs and operational expenses
"""

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
import json

# Try to import ML libraries with fallback
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    frappe.log_error("pandas/numpy not available. Using fallback methods.", "Expense Forecasting")

class ExpenseForecaster:
    """
    Expense forecasting with inventory cost integration
    """
    
    def __init__(self, company):
        self.company = company
        
    def predict_expenses(self, forecast_period="Monthly"):
        """
        Main expense prediction method
        """
        # Get historical expense data
        historical_expenses = self.get_historical_expense_data()
        
        # Get inventory-related expense forecasts
        inventory_expenses = self.get_inventory_related_expenses()
        
        # Get fixed and variable expense patterns
        expense_patterns = self.analyze_expense_patterns()
        
        # Get budget data for comparison
        budget_data = self.get_budget_data()
        
        # Integrate all expense data
        integrated_data = self.integrate_expense_data(
            historical_expenses, inventory_expenses, 
            expense_patterns, budget_data
        )
        
        # Run expense prediction model
        prediction = self.run_expense_model(integrated_data, forecast_period)
        
        return prediction
    
    def get_inventory_related_expenses(self):
        """
        Calculate inventory-related expenses from forecasts (optimized)
        """
        # Use SQL to get data more efficiently
        inventory_data = frappe.db.sql("""
            SELECT 
                aif.item_code,
                aif.current_stock,
                aif.predicted_consumption,
                aif.reorder_alert,
                aif.suggested_qty,
                aif.warehouse,
                COALESCE(i.valuation_rate, 0) as valuation_rate
            FROM `tabAI Inventory Forecast` aif
            LEFT JOIN `tabItem` i ON aif.item_code = i.name
            WHERE aif.company = %s
            LIMIT 1000
        """, (self.company,), as_dict=True)
        
        inventory_expenses = {
            "carrying_costs": 0,
            "storage_costs": 0,
            "handling_costs": 0,
            "reorder_costs": 0,
            "obsolescence_costs": 0
        }
        
        # Process in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(inventory_data), batch_size):
            batch = inventory_data[i:i+batch_size]
            
            for forecast in batch:
                try:
                    current_stock = forecast.get("current_stock", 0) or 0
                    valuation_rate = forecast.get("valuation_rate", 0) or 0
                    current_stock_value = current_stock * valuation_rate
                    
                    # Calculate carrying costs (optimized calculation)
                    if current_stock_value > 0:
                        monthly_carrying_cost = current_stock_value * 0.020833  # 25%/12 pre-calculated
                        inventory_expenses["carrying_costs"] += monthly_carrying_cost
                    
                    # Calculate storage costs (cached lookup)
                    warehouse = forecast.get("warehouse")
                    if warehouse:
                        storage_cost = self._get_cached_storage_cost(warehouse)
                        inventory_expenses["storage_costs"] += storage_cost
                    
                    # Calculate handling costs
                    predicted_consumption = forecast.get("predicted_consumption", 0) or 0
                    if predicted_consumption > 0:
                        handling_cost = predicted_consumption * 0.05
                        inventory_expenses["handling_costs"] += handling_cost
                    
                    # Calculate reorder costs
                    if forecast.get("reorder_alert"):
                        inventory_expenses["reorder_costs"] += 50
                    
                    # Calculate obsolescence costs for zero consumption
                    if predicted_consumption == 0 and current_stock_value > 0:
                        obsolescence_cost = current_stock_value * 0.10
                        inventory_expenses["obsolescence_costs"] += obsolescence_cost
                        
                except Exception as e:
                    frappe.log_error(f"Error processing forecast {forecast.get('item_code', 'Unknown')}: {str(e)}")
                    continue
        
        return inventory_expenses
    
    def analyze_expense_patterns(self):
        """
        Analyze historical expense patterns to identify fixed, variable, and semi-variable costs
        """
        # Get expense accounts
        expense_accounts = frappe.get_all("Account",
            filters={
                "company": self.company,
                "account_type": ["in", ["Expense Account", "Cost of Goods Sold"]],
                "is_group": 0
            },
            fields=["name", "account_name", "parent_account"]
        )
        
        expense_patterns = {}
        
        for account in expense_accounts:
            # Get monthly expense data for the account
            monthly_data = frappe.db.sql("""
                SELECT 
                    YEAR(posting_date) as year,
                    MONTH(posting_date) as month,
                    SUM(debit - credit) as expense_amount
                FROM `tabGL Entry`
                WHERE account = %s AND company = %s
                AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 24 MONTH)
                GROUP BY YEAR(posting_date), MONTH(posting_date)
                ORDER BY year, month
            """, (account["name"], self.company), as_dict=True)
            
            if monthly_data:
                # Classify expense type based on variance
                expenses = [d["expense_amount"] for d in monthly_data]
                mean_expense = np.mean(expenses)
                std_expense = np.std(expenses)
                cv = std_expense / mean_expense if mean_expense > 0 else 0
                
                # Classify based on coefficient of variation
                if cv < 0.1:
                    expense_type = "Fixed"
                elif cv > 0.3:
                    expense_type = "Variable"
                else:
                    expense_type = "Semi-Variable"
                
                expense_patterns[account["name"]] = {
                    "account_name": account["account_name"],
                    "expense_type": expense_type,
                    "mean_monthly": mean_expense,
                    "std_dev": std_expense,
                    "coefficient_variation": cv,
                    "historical_data": monthly_data
                }
        
        return expense_patterns
    
    def get_budget_data(self):
        """
        Get budget data for comparison and variance analysis
        """
        current_year = datetime.now().year
        
        budget_data = frappe.db.sql("""
            SELECT 
                account, SUM(budget_amount) as budget_amount,
                fiscal_year
            FROM `tabBudget Account`
            WHERE parent IN (
                SELECT name FROM `tabBudget`
                WHERE company = %s AND fiscal_year = %s
            )
            GROUP BY account
        """, (self.company, str(current_year)), as_dict=True)
        
        return {item["account"]: item["budget_amount"] for item in budget_data}
    
    def integrate_expense_data(self, historical, inventory, patterns, budget):
        """
        Integrate all expense data sources
        """
        return {
            "historical_expenses": historical,
            "inventory_expenses": inventory,
            "expense_patterns": patterns,
            "budget_data": budget,
            "integration_timestamp": datetime.now()
        }
    
    def run_expense_model(self, integrated_data, forecast_period):
        """
        Run AI model for expense prediction
        """
        from ai_inventory.ai_accounts_forecast.algorithms.time_series_models import ExpenseTimeSeriesModel
        
        model = ExpenseTimeSeriesModel()
        
        # Prepare data for model
        model_data = self.prepare_expense_model_data(integrated_data)
        
        # Run prediction
        prediction = model.predict(model_data, forecast_period)
        
        # Add inventory-specific adjustments
        inventory_adjusted_prediction = self.apply_inventory_adjustments(
            prediction, integrated_data["inventory_expenses"]
        )
        
        return inventory_adjusted_prediction
    
    def get_warehouse_storage_cost(self, warehouse):
        """Get storage cost for a specific warehouse"""
        if not warehouse:
            return 10  # Default monthly storage cost per item
        
        # This could be enhanced with actual warehouse cost data
        warehouse_costs = {
            "Main Store - Company": 15,
            "Finished Goods - Company": 20,
            "Raw Materials - Company": 10
        }
        
        return warehouse_costs.get(warehouse, 10)
    
    def apply_inventory_adjustments(self, base_prediction, inventory_expenses):
        """Apply inventory-specific adjustments to expense predictions"""
        adjusted_prediction = base_prediction.copy()
        
        # Add inventory expenses to the prediction
        for expense_type, amount in inventory_expenses.items():
            if expense_type in adjusted_prediction:
                adjusted_prediction[expense_type] += amount
            else:
                adjusted_prediction[expense_type] = amount
        
        # Recalculate totals
        adjusted_prediction["total_expenses"] = sum([
            v for k, v in adjusted_prediction.items() 
            if k.endswith("_expenses") or k.endswith("_costs")
        ])
        
        return adjusted_prediction

# API Methods for Expense Forecasting

@frappe.whitelist()
def create_expense_forecast(company, forecast_period="Monthly"):
    """Create expense forecast for a company"""
    try:
        forecaster = ExpenseForecaster(company)
        forecast_data = forecaster.predict_expenses(forecast_period)
        
        # Create expense forecast document
        expense_doc = frappe.get_doc({
            "doctype": "AI Expense Forecast",
            "company": company,
            "forecast_date": datetime.now().date(),
            "forecast_period": forecast_period,
            "total_predicted_expense": forecast_data.get("total_expenses", 0),
            "inventory_related_expenses": forecast_data.get("inventory_total", 0),
            "fixed_expenses": forecast_data.get("fixed_expenses", 0),
            "variable_expenses": forecast_data.get("variable_expenses", 0),
            "confidence_score": forecast_data.get("confidence", 0),
            "storage_costs": forecast_data.get("storage_costs", 0),
            "carrying_costs": forecast_data.get("carrying_costs", 0),
            "expense_breakdown": json.dumps(forecast_data.get("breakdown", {}))
        })
        
        expense_doc.save()
        
        return {
            "status": "success",
            "forecast_id": expense_doc.name,
            "predicted_expenses": expense_doc.total_predicted_expense,
            "confidence": expense_doc.confidence_score
        }
        
    except Exception as e:
        frappe.log_error(f"Expense Forecast Error: {str(e)}")
        return {"status": "error", "message": str(e)}