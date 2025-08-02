# ==========================================
# ai_inventory/forecasting/core.py
# Core forecasting engine

import frappe
from frappe.utils import flt, add_days, nowdate
from datetime import datetime, timedelta
import json

class SalesForecastingEngine:
    """Core sales forecasting engine"""
    
    def __init__(self):
        self.config = frappe.get_single("AI Sales Dashboard") if frappe.db.exists("DocType", "AI Sales Dashboard") else None
    
    def generate_forecasts(self):
        """Generate sales forecasts for all active items"""
        try:
            forecasts_created = 0
            
            # Get all active items
            items = frappe.get_all("Item", 
                                 filters={"disabled": 0, "is_sales_item": 1},
                                 fields=["name", "item_name", "item_group"])
            
            for item in items:
                try:
                    forecast_data = self.generate_item_forecast(item.name)
                    if forecast_data:
                        self.create_forecast_record(forecast_data)
                        forecasts_created += 1
                except Exception as e:
                    frappe.log_error(f"Failed to generate forecast for item {item.name}: {str(e)}")
                    continue
            
            return forecasts_created
            
        except Exception as e:
            frappe.log_error(f"Sales forecast generation failed: {str(e)}")
            return 0
    
    def generate_item_forecast(self, item_code):
        """Generate forecast for a specific item"""
        try:
            # Get historical sales data
            sales_data = self.get_historical_sales(item_code)
            
            if not sales_data or len(sales_data) < 3:
                return None
            
            # Simple forecast calculation (can be enhanced with ML)
            recent_sales = sales_data[-3:]  # Last 3 months
            avg_qty = sum([s.get('total_qty', 0) for s in recent_sales]) / len(recent_sales)
            
            # Apply growth trend
            growth_factor = 1.1 if len(sales_data) > 6 else 1.0
            predicted_qty = flt(avg_qty * growth_factor, 2)
            
            # Calculate confidence based on data consistency
            confidence = min(95, max(60, 70 + (len(sales_data) * 2)))
            
            forecast_data = {
                'item_code': item_code,
                'item_name': frappe.db.get_value("Item", item_code, "item_name"),
                'predicted_qty': predicted_qty,
                'confidence_score': confidence,
                'forecast_date': add_days(nowdate(), 30),
                'horizon_days': 30,
                'model_version': 'basic_v1.0',
                'trigger_source': 'scheduled_task',
                'sales_trend': self.calculate_trend(sales_data),
                'accuracy_score': flt(confidence * 0.9, 2),
                'demand_pattern': self.classify_demand_pattern(sales_data),
                'revenue_potential': predicted_qty * flt(frappe.db.get_value("Item", item_code, "standard_rate") or 100),
                'customer_score': 50.0,
                'market_potential': 60.0,
                'seasonality_index': 1.0,
                'cross_sell_score': 40.0,
                'churn_risk': 'Low',
                'sales_velocity': predicted_qty / 30.0
            }
            
            return forecast_data
            
        except Exception as e:
            frappe.log_error(f"Item forecast generation failed for {item_code}: {str(e)}")
            return None
    
    def get_historical_sales(self, item_code, months=12):
        """Get historical sales data for an item"""
        try:
            from_date = add_days(nowdate(), -30 * months)
            
            sales_data = frappe.db.sql("""
                SELECT 
                    MONTH(si.posting_date) as month,
                    YEAR(si.posting_date) as year,
                    SUM(sii.qty) as total_qty,
                    SUM(sii.amount) as total_amount,
                    COUNT(DISTINCT si.customer) as customer_count
                FROM `tabSales Invoice` si
                INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
                WHERE si.docstatus = 1 
                AND sii.item_code = %s
                AND si.posting_date >= %s
                GROUP BY YEAR(si.posting_date), MONTH(si.posting_date)
                ORDER BY si.posting_date
            """, (item_code, from_date), as_dict=True)
            
            return sales_data
            
        except Exception as e:
            frappe.log_error(f"Historical sales data fetch failed for {item_code}: {str(e)}")
            return []
    
    def calculate_trend(self, sales_data):
        """Calculate sales trend from historical data"""
        if len(sales_data) < 2:
            return "Stable"
        
        recent_avg = sum([s.get('total_qty', 0) for s in sales_data[-3:]]) / min(3, len(sales_data))
        older_avg = sum([s.get('total_qty', 0) for s in sales_data[:-3]]) / max(1, len(sales_data) - 3)
        
        if recent_avg > older_avg * 1.2:
            return "Increasing"
        elif recent_avg < older_avg * 0.8:
            return "Decreasing"
        else:
            return "Stable"
    
    def classify_demand_pattern(self, sales_data):
        """Classify demand pattern"""
        if not sales_data:
            return "Unknown"
        
        # Calculate coefficient of variation
        quantities = [s.get('total_qty', 0) for s in sales_data]
        if len(quantities) < 2:
            return "Unknown"
        
        mean_qty = sum(quantities) / len(quantities)
        if mean_qty == 0:
            return "No Demand"
        
        variance = sum([(q - mean_qty) ** 2 for q in quantities]) / len(quantities)
        cv = (variance ** 0.5) / mean_qty
        
        if cv < 0.3:
            return "Regular"
        elif cv < 0.7:
            return "Variable"
        else:
            return "Sporadic"
    
    def create_forecast_record(self, forecast_data):
        """Create AI Sales Forecast record"""
        try:
            # Check if forecast already exists for this item and date
            existing = frappe.db.exists("AI Sales Forecast", {
                "item_code": forecast_data['item_code'],
                "forecast_date": forecast_data['forecast_date']
            })
            
            if existing:
                # Update existing record
                doc = frappe.get_doc("AI Sales Forecast", existing)
                for key, value in forecast_data.items():
                    if hasattr(doc, key):
                        setattr(doc, key, value)
                doc.save()
            else:
                # Create new record
                doc = frappe.new_doc("AI Sales Forecast")
                for key, value in forecast_data.items():
                    if hasattr(doc, key):
                        setattr(doc, key, value)
                doc.insert()
            
            return doc.name
            
        except Exception as e:
            frappe.log_error(f"Forecast record creation failed: {str(e)}")
            return None
    
    def train_models(self):
        """Train ML models (placeholder for advanced ML implementation)"""
        try:
            # Get all items with sufficient historical data
            items_with_data = frappe.db.sql("""
                SELECT DISTINCT sii.item_code, COUNT(*) as sales_count
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                WHERE si.docstatus = 1
                AND si.posting_date >= %s
                GROUP BY sii.item_code
                HAVING COUNT(*) >= 10
            """, (add_days(nowdate(), -365),), as_dict=True)
            
            performance_metrics = {}
            
            for item_data in items_with_data:
                item_code = item_data['item_code']
                
                # Simple performance calculation (placeholder)
                performance_metrics[item_code] = {
                    'accuracy': 85.0 + (item_data['sales_count'] * 0.1),
                    'data_points': item_data['sales_count'],
                    'last_trained': nowdate()
                }
            
            return performance_metrics
            
        except Exception as e:
            frappe.log_error(f"Model training failed: {str(e)}")
            return {}

def auto_create_sales_orders():
    """Auto-create sales orders based on forecasts"""
    try:
        # Get high-confidence forecasts
        forecasts = frappe.get_all("AI Sales Forecast",
                                 filters={
                                     "confidence_score": [">", 80],
                                     "predicted_qty": [">", 0],
                                     "auto_create_sales_order": 1
                                 },
                                 fields=["name", "item_code", "predicted_qty", "customer", "company"])
        
        orders_created = 0
        
        for forecast in forecasts:
            try:
                # Create sales order
                so = frappe.new_doc("Sales Order")
                so.customer = forecast.customer or "Default Customer"
                so.company = forecast.company or frappe.defaults.get_user_default("Company")
                so.delivery_date = add_days(nowdate(), 30)
                
                # Add item
                so.append("items", {
                    "item_code": forecast.item_code,
                    "qty": forecast.predicted_qty,
                    "rate": frappe.db.get_value("Item", forecast.item_code, "standard_rate") or 100
                })
                
                so.insert()
                orders_created += 1
                
                # Mark forecast as processed
                frappe.db.set_value("AI Sales Forecast", forecast.name, "auto_create_sales_order", 0)
                
            except Exception as e:
                frappe.log_error(f"Sales order creation failed for forecast {forecast.name}: {str(e)}")
                continue
        
        return orders_created
        
    except Exception as e:
        frappe.log_error(f"Auto sales order creation failed: {str(e)}")
        return 0
