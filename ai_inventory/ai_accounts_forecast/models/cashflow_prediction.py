"""
Cash Flow Prediction Module
Integrates with inventory system for comprehensive cash flow forecasting
"""

import frappe
from frappe.model.document import Document
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class CashFlowPredictor:
    """
    Cash flow prediction with inventory integration
    """
    
    def __init__(self, company):
        self.company = company
        
    def predict_cash_flow(self, forecast_period_days=90):
        """
        Main cash flow prediction method
        """
        # Get historical cash flow data
        historical_data = self.get_historical_cash_data()
        
        # Get inventory impact on cash flow
        inventory_impact = self.get_inventory_cash_impact()
        
        # Get receivables and payables forecast
        receivables_forecast = self.predict_receivables_collection()
        payables_forecast = self.predict_payables_payment()
        
        # Combine all data sources
        integrated_data = self.integrate_cash_flow_data(
            historical_data, inventory_impact, 
            receivables_forecast, payables_forecast
        )
        
        # Run prediction model
        prediction = self.run_cash_flow_model(integrated_data, forecast_period_days)
        
        return prediction
    
    def get_inventory_cash_impact(self):
        """
        Calculate cash impact from inventory forecasts
        """
        # Get inventory forecasts with reorder alerts
        reorder_forecasts = frappe.get_all("AI Inventory Forecast",
            filters={
                "company": self.company,
                "reorder_alert": 1
            },
            fields=["item_code", "suggested_qty", "supplier", "reorder_level", 
                   "last_purchase_date", "forecast_details"]
        )
        
        cash_outflows = []
        
        for forecast in reorder_forecasts:
            # Calculate expected purchase amount
            item_doc = frappe.get_doc("Item", forecast["item_code"])
            purchase_amount = forecast["suggested_qty"] * (item_doc.valuation_rate or 0)
            
            # Estimate purchase timing based on lead time
            lead_time = self.get_supplier_lead_time(forecast["supplier"])
            expected_purchase_date = datetime.now() + timedelta(days=lead_time)
            
            cash_outflows.append({
                "date": expected_purchase_date,
                "amount": purchase_amount,
                "type": "inventory_purchase",
                "item_code": forecast["item_code"],
                "confidence": self.get_forecast_confidence(forecast)
            })
        
        return {
            "outflows": cash_outflows,
            "total_expected_outflow": sum([cf["amount"] for cf in cash_outflows])
        }
    
    def predict_receivables_collection(self):
        """
        Predict when receivables will be collected
        """
        outstanding_invoices = frappe.db.sql("""
            SELECT 
                name, customer, outstanding_amount, posting_date,
                due_date, customer_group, territory
            FROM `tabSales Invoice`
            WHERE company = %s AND outstanding_amount > 0
            AND docstatus = 1
        """, self.company, as_dict=True)
        
        collections = []
        
        for invoice in outstanding_invoices:
            # Calculate collection probability based on customer payment history
            payment_history = self.get_customer_payment_pattern(invoice["customer"])
            
            # Predict collection date and probability
            collection_prediction = self.predict_invoice_collection(invoice, payment_history)
            
            collections.append({
                "date": collection_prediction["expected_collection_date"],
                "amount": invoice["outstanding_amount"],
                "probability": collection_prediction["collection_probability"],
                "customer": invoice["customer"],
                "invoice": invoice["name"]
            })
        
        return collections
    
    def predict_payables_payment(self):
        """
        Predict when payables will be paid
        """
        outstanding_bills = frappe.db.sql("""
            SELECT 
                name, supplier, outstanding_amount, posting_date,
                due_date, supplier_group
            FROM `tabPurchase Invoice`
            WHERE company = %s AND outstanding_amount > 0
            AND docstatus = 1
        """, self.company, as_dict=True)
        
        payments = []
        
        for bill in outstanding_bills:
            # Get supplier payment terms
            payment_terms = self.get_supplier_payment_terms(bill["supplier"])
            
            # Predict payment timing
            payment_prediction = self.predict_bill_payment(bill, payment_terms)
            
            payments.append({
                "date": payment_prediction["expected_payment_date"],
                "amount": bill["outstanding_amount"],
                "supplier": bill["supplier"],
                "bill": bill["name"]
            })
        
        return payments
    
    def integrate_cash_flow_data(self, historical, inventory, receivables, payables):
        """
        Integrate all cash flow data sources
        """
        # Create comprehensive cash flow dataset
        cash_flow_data = {
            "historical": historical,
            "projected_inflows": receivables,
            "projected_outflows": payables + inventory["outflows"],
            "inventory_impact": inventory
        }
        
        return cash_flow_data
    
    def run_cash_flow_model(self, data, forecast_days):
        """
        Run AI model for cash flow prediction
        """
        # Use time series model for cash flow prediction
        from ai_inventory.ai_accounts_forecast.algorithms.time_series_models import CashFlowTimeSeriesModel
        
        model = CashFlowTimeSeriesModel()
        
        # Prepare data for model
        model_data = self.prepare_model_data(data)
        
        # Train and predict
        prediction = model.predict(model_data, forecast_days)
        
        return {
            "daily_cash_flow": prediction["daily_forecast"],
            "cumulative_cash_flow": prediction["cumulative_forecast"],
            "confidence_intervals": prediction["confidence_bands"],
            "key_insights": prediction["insights"],
            "risk_factors": prediction["risks"]
        }
    
    def get_supplier_lead_time(self, supplier):
        """Get supplier lead time for purchase timing"""
        if not supplier:
            return 14  # Default 2 weeks
            
        supplier_doc = frappe.get_doc("Supplier", supplier)
        return getattr(supplier_doc, 'lead_time_days', 14)
    
    def get_customer_payment_pattern(self, customer):
        """Analyze customer payment patterns"""
        payment_history = frappe.db.sql("""
            SELECT 
                si.posting_date, si.due_date, pe.posting_date as payment_date,
                DATEDIFF(pe.posting_date, si.due_date) as days_overdue,
                pe.paid_amount
            FROM `tabSales Invoice` si
            LEFT JOIN `tabPayment Entry Reference` per ON per.reference_name = si.name
            LEFT JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE si.customer = %s AND si.company = %s
            AND si.docstatus = 1 AND pe.docstatus = 1
            ORDER BY si.posting_date DESC
            LIMIT 50
        """, (customer, self.company), as_dict=True)
        
        if not payment_history:
            return {"avg_days_overdue": 0, "payment_reliability": 0.5}
        
        # Calculate payment patterns
        total_payments = len(payment_history)
        on_time_payments = len([p for p in payment_history if p["days_overdue"] <= 0])
        avg_days_overdue = sum([p["days_overdue"] for p in payment_history]) / total_payments
        
        return {
            "avg_days_overdue": avg_days_overdue,
            "payment_reliability": on_time_payments / total_payments,
            "total_transactions": total_payments
        }

# API Methods for Cash Flow Forecasting

@frappe.whitelist()
def create_cashflow_forecast(company, forecast_period=90):
    """Create cash flow forecast for a company"""
    try:
        predictor = CashFlowPredictor(company)
        forecast_data = predictor.predict_cash_flow(forecast_period)
        
        # Create cash flow forecast document
        cashflow_doc = frappe.get_doc({
            "doctype": "AI Cashflow Forecast",
            "company": company,
            "forecast_date": datetime.now().date(),
            "forecast_period": "Monthly",
            "predicted_inflows": forecast_data.get("total_inflows", 0),
            "predicted_outflows": forecast_data.get("total_outflows", 0),
            "net_cash_flow": forecast_data.get("net_cash_flow", 0),
            "confidence_score": forecast_data.get("confidence", 0),
            "inventory_integration_data": json.dumps(forecast_data.get("inventory_impact", {}))
        })
        
        cashflow_doc.save()
        
        return {
            "status": "success",
            "forecast_id": cashflow_doc.name,
            "net_cash_flow": cashflow_doc.net_cash_flow,
            "confidence": cashflow_doc.confidence_score
        }
        
    except Exception as e:
        frappe.log_error(f"Cash Flow Forecast Error: {str(e)}")
        return {"status": "error", "message": str(e)}