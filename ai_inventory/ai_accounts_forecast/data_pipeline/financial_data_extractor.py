"""
Financial Data Extractor
Extracts and processes financial data from ERPNext for forecasting
"""

import frappe
import pandas as pd
from datetime import datetime, timedelta
import json

class FinancialDataExtractor:
    """Extract financial data from ERPNext for AI forecasting"""
    
    def __init__(self, company=None):
        self.company = company
    
    def extract_gl_data(self, account=None, months_back=36):
        """Extract General Ledger data"""
        filters = {"company": self.company} if self.company else {}
        
        if account:
            filters["account"] = account
        
        # Date filter
        from_date = datetime.now() - timedelta(days=months_back * 30)
        filters["posting_date"] = [">=", from_date.strftime("%Y-%m-%d")]
        
        gl_entries = frappe.db.sql("""
            SELECT 
                posting_date, account, debit, credit, 
                (debit - credit) as net_amount,
                voucher_type, voucher_no, party_type, party
            FROM `tabGL Entry`
            WHERE company = %(company)s
            AND posting_date >= %(from_date)s
            {account_filter}
            ORDER BY posting_date DESC
        """.format(
            account_filter="AND account = %(account)s" if account else ""
        ), {
            "company": self.company,
            "from_date": from_date.strftime("%Y-%m-%d"),
            "account": account
        }, as_dict=True)
        
        return gl_entries
    
    def extract_cash_flow_data(self, months_back=24):
        """Extract cash flow related data"""
        from_date = datetime.now() - timedelta(days=months_back * 30)
        
        # Cash and bank accounts
        cash_accounts = frappe.get_all("Account", 
            filters={
                "company": self.company,
                "account_type": ["in", ["Cash", "Bank"]]
            },
            pluck="name"
        )
        
        cash_flow_data = []
        
        for account in cash_accounts:
            account_data = self.extract_gl_data(account, months_back)
            cash_flow_data.extend(account_data)
        
        return cash_flow_data
    
    def extract_revenue_data(self, months_back=24):
        """Extract revenue data from sales invoices"""
        from_date = datetime.now() - timedelta(days=months_back * 30)
        
        revenue_data = frappe.db.sql("""
            SELECT 
                posting_date, customer, territory, sales_person,
                grand_total, outstanding_amount,
                (grand_total - outstanding_amount) as collected_amount
            FROM `tabSales Invoice`
            WHERE company = %(company)s
            AND posting_date >= %(from_date)s
            AND docstatus = 1
            ORDER BY posting_date DESC
        """, {
            "company": self.company,
            "from_date": from_date.strftime("%Y-%m-%d")
        }, as_dict=True)
        
        return revenue_data
    
    def extract_expense_data(self, months_back=24):
        """Extract expense data"""
        from_date = datetime.now() - timedelta(days=months_back * 30)
        
        expense_accounts = frappe.get_all("Account",
            filters={
                "company": self.company,
                "account_type": ["in", ["Expense Account", "Cost of Goods Sold"]]
            },
            pluck="name"
        )
        
        expense_data = []
        
        for account in expense_accounts:
            account_data = self.extract_gl_data(account, months_back)
            expense_data.extend(account_data)
        
        return expense_data
    
    def extract_inventory_financial_impact(self):
        """Extract inventory data that impacts finances"""
        inventory_forecasts = frappe.get_all("AI Inventory Forecast",
            filters={"company": self.company} if self.company else {},
            fields=["*"]
        )
        
        financial_impact = {
            "total_inventory_value": 0,
            "reorder_cash_impact": 0,
            "carrying_cost_monthly": 0,
            "forecasts": inventory_forecasts
        }
        
        for forecast in inventory_forecasts:
            # Calculate inventory value
            current_value = (forecast.get("current_stock", 0) * 
                           forecast.get("valuation_rate", 0))
            financial_impact["total_inventory_value"] += current_value
            
            # Calculate reorder cash impact
            if forecast.get("reorder_alert"):
                reorder_cost = (forecast.get("suggested_qty", 0) * 
                              forecast.get("valuation_rate", 0))
                financial_impact["reorder_cash_impact"] += reorder_cost
            
            # Calculate carrying costs (25% annually)
            carrying_cost = current_value * 0.25 / 12
            financial_impact["carrying_cost_monthly"] += carrying_cost
        
        return financial_impact

class DataQualityValidator:
    """Validate quality of extracted financial data"""
    
    def __init__(self):
        pass
    
    def validate_gl_data(self, gl_data):
        """Validate GL data quality"""
        if not gl_data:
            return {"valid": False, "reason": "No data found"}
        
        df = pd.DataFrame(gl_data)
        
        # Check for required columns
        required_cols = ["posting_date", "debit", "credit", "net_amount"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return {"valid": False, "reason": f"Missing columns: {missing_cols}"}
        
        # Check for null values in critical columns
        null_counts = df[required_cols].isnull().sum()
        if null_counts.sum() > len(df) * 0.1:  # More than 10% nulls
            return {"valid": False, "reason": "Too many null values"}
        
        # Check date range
        df["posting_date"] = pd.to_datetime(df["posting_date"])
        date_range = (df["posting_date"].max() - df["posting_date"].min()).days
        
        if date_range < 30:  # Less than 30 days of data
            return {"valid": False, "reason": "Insufficient date range"}
        
        return {
            "valid": True,
            "data_points": len(df),
            "date_range_days": date_range,
            "null_percentage": (null_counts.sum() / (len(df) * len(required_cols))) * 100
        }
    
    def validate_forecast_data(self, forecast_data):
        """Validate forecast input data"""
        validation_results = {}
        
        if "historical_data" in forecast_data:
            validation_results["historical"] = self.validate_gl_data(
                forecast_data["historical_data"]
            )
        
        if "inventory_impact" in forecast_data:
            inv_data = forecast_data["inventory_impact"]
            validation_results["inventory"] = {
                "valid": True,
                "total_value": inv_data.get("total_inventory_value", 0),
                "reorder_impact": inv_data.get("reorder_cash_impact", 0)
            }
        
        return validation_results

# API functions for data extraction
@frappe.whitelist()
def extract_financial_data_for_forecast(company, data_type="all", months_back=24):
    """
    API function to extract financial data for forecasting
    """
    try:
        extractor = FinancialDataExtractor(company)
        
        result = {}
        
        if data_type in ["all", "gl"]:
            result["gl_data"] = extractor.extract_gl_data(months_back=months_back)
        
        if data_type in ["all", "cash_flow"]:
            result["cash_flow_data"] = extractor.extract_cash_flow_data(months_back)
        
        if data_type in ["all", "revenue"]:
            result["revenue_data"] = extractor.extract_revenue_data(months_back)
        
        if data_type in ["all", "expense"]:
            result["expense_data"] = extractor.extract_expense_data(months_back)
        
        if data_type in ["all", "inventory"]:
            result["inventory_impact"] = extractor.extract_inventory_financial_impact()
        
        # Validate data quality
        validator = DataQualityValidator()
        result["data_quality"] = validator.validate_forecast_data(result)
        
        return {
            "status": "success",
            "data": result,
            "extraction_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        frappe.log_error(f"Financial data extraction error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }