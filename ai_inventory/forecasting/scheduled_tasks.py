# ==========================================
# ai_inventory/forecasting/scheduled_tasks.py
# Scheduled background tasks

import frappe
from frappe.utils import flt, add_days, nowdate
from ai_inventory.forecasting.core import SalesForecastingEngine

@frappe.whitelist()
def scheduled_forecast_generation():
    """Daily scheduled forecast generation"""
    try:
        config = frappe.get_single("AI Sales Dashboard")
        
        if not config.enable_auto_sync:
            return
        
        engine = SalesForecastingEngine()
        forecasts_created = engine.generate_forecasts()
        
        # Auto-create sales orders if enabled
        if config.auto_submit_sales_orders:
            from ai_inventory.forecasting.core import auto_create_sales_orders
            auto_create_sales_orders()
        
        frappe.log_error(f"Scheduled forecast generation completed: {forecasts_created} forecasts", 
                        "AI Sales Forecasting")
        
    except Exception as e:
        frappe.log_error(f"Scheduled forecast generation failed: {str(e)}", 
                        "AI Sales Forecasting")

def scheduled_model_training():
    """Weekly scheduled model training"""
    try:
        config = frappe.get_single("AI Sales Dashboard")
        
        if not config.enable_auto_sync:
            return
        
        # Check if we have enough new data to warrant retraining
        new_invoices = frappe.db.count("Sales Invoice", {
            "docstatus": 1,
            "creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
        })
        
        if new_invoices >= 10:  # Only retrain if we have significant new data
            engine = SalesForecastingEngine()
            performance = engine.train_models()
            
            frappe.log_error(f"Scheduled model training completed for {len(performance)} items", 
                            "AI Sales Forecasting")
        
    except Exception as e:
        frappe.log_error(f"Scheduled model training failed: {str(e)}", 
                        "AI Sales Forecasting")

@frappe.whitelist()
def get_quick_recorder_analysis():
    """Get quick analysis for recorder dashboard"""
    try:
        # Get top items that need attention with safe field references
        items_analysis = frappe.db.sql("""
            SELECT 
                asf.item_code,
                asf.item_name,
                asf.predicted_qty,
                COALESCE(asf.accuracy_score, 70) as confidence_score,
                COALESCE(asf.sales_trend, 'Unknown') as sales_trend,
                0 as revenue_potential,
                CASE 
                    WHEN asf.predicted_qty > 50 THEN 'High Priority'
                    WHEN asf.predicted_qty > 20 THEN 'Medium Priority'
                    ELSE 'Low Priority'
                END as priority
            FROM `tabAI Sales Forecast` asf
            WHERE asf.predicted_qty > 0
            ORDER BY asf.predicted_qty DESC, COALESCE(asf.accuracy_score, 70) DESC
            LIMIT 10
        """, as_dict=True)
        
        return {
            "status": "success",
            "data": items_analysis,
            "summary": {
                "total_items": len(items_analysis),
                "high_priority": len([i for i in items_analysis if i.priority == 'High Priority']),
                "total_revenue_potential": sum([i.revenue_potential for i in items_analysis])
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Quick recorder analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_revenue_opportunities():
    """Get revenue opportunities analysis"""
    try:
        opportunities = frappe.db.sql("""
            SELECT 
                asf.item_code,
                asf.item_name,
                asf.customer,
                0 as revenue_potential,
                asf.predicted_qty,
                50 as cross_sell_score,
                60 as market_potential,
                CASE 
                    WHEN asf.predicted_qty > 50 THEN 'High Value'
                    WHEN asf.predicted_qty > 20 THEN 'Medium Value'
                    ELSE 'Low Value'
                END as opportunity_level
            FROM `tabAI Sales Forecast` asf
            WHERE asf.predicted_qty > 0
            ORDER BY asf.predicted_qty DESC
            LIMIT 15
        """, as_dict=True)
        
        return {
            "status": "success",
            "data": opportunities,
            "summary": {
                "total_opportunities": len(opportunities),
                "total_potential": sum([o.revenue_potential for o in opportunities]),
                "high_value_count": len([o for o in opportunities if o.opportunity_level == 'High Value'])
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Revenue opportunities analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_risk_assessment():
    """Get risk assessment analysis"""
    try:
        # Get items with risk indicators using available fields
        risk_items = frappe.db.sql("""
            SELECT 
                asf.item_code,
                asf.item_name,
                'Medium' as churn_risk,
                COALESCE(asf.accuracy_score, 70) as confidence_score,
                COALESCE(asf.sales_trend, 'Unknown') as sales_trend,
                CASE 
                    WHEN COALESCE(asf.accuracy_score, 70) < 60 THEN 'High Risk'
                    WHEN COALESCE(asf.accuracy_score, 70) < 75 THEN 'Medium Risk'
                    ELSE 'Low Risk'
                END as risk_level,
                CASE 
                    WHEN asf.sales_trend = 'Decreasing' THEN 'Declining Sales'
                    WHEN COALESCE(asf.accuracy_score, 70) < 60 THEN 'Low Prediction Confidence'
                    ELSE 'Stable'
                END as risk_factor
            FROM `tabAI Sales Forecast` asf
            ORDER BY COALESCE(asf.accuracy_score, 70) ASC
            LIMIT 15
        """, as_dict=True)
        
        return {
            "status": "success",
            "data": risk_items,
            "summary": {
                "total_items": len(risk_items),
                "high_risk": len([r for r in risk_items if r.risk_level == 'High Risk']),
                "medium_risk": len([r for r in risk_items if r.risk_level == 'Medium Risk']),
                "low_risk": len([r for r in risk_items if r.risk_level == 'Low Risk'])
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Risk assessment analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_demand_forecasting():
    """Get demand forecasting analysis"""
    try:
        # Get demand forecast data using available fields
        demand_forecast = frappe.db.sql("""
            SELECT 
                asf.item_code,
                asf.item_name,
                asf.predicted_qty,
                'Unknown' as demand_pattern,
                1.0 as seasonality_index,
                0 as sales_velocity,
                COALESCE(aif.current_stock, 0) as current_stock,
                COALESCE(aif.predicted_consumption, 0) as predicted_consumption,
                CASE 
                    WHEN asf.predicted_qty > COALESCE(aif.current_stock, 0) * 2 THEN 'High Demand Expected'
                    WHEN asf.predicted_qty > COALESCE(aif.current_stock, 0) THEN 'Moderate Demand Expected'
                    ELSE 'Low Demand Expected'
                END as demand_forecast_level
            FROM `tabAI Sales Forecast` asf
            LEFT JOIN `tabAI Inventory Forecast` aif ON asf.item_code = aif.item_code
            WHERE asf.predicted_qty > 0
            ORDER BY asf.predicted_qty DESC
            LIMIT 15
        """, as_dict=True)
        
        return {
            "status": "success",
            "data": demand_forecast,
            "summary": {
                "total_items": len(demand_forecast),
                "high_demand": len([d for d in demand_forecast if d.demand_forecast_level == 'High Demand Expected']),
                "total_predicted_qty": sum([d.predicted_qty for d in demand_forecast])
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Demand forecasting analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_ai_purchase_orders(items=None):
    """Create AI-powered purchase orders based on forecast data"""
    try:
        if not items:
            # Get items that need reordering based on forecasts
            items_to_order = frappe.db.sql("""
                SELECT DISTINCT
                    aif.item_code,
                    aif.item_name,
                    aif.current_stock,
                    aif.predicted_consumption,
                    aif.reorder_level,
                    aif.company,
                    COALESCE(aif.predicted_consumption * 2, 10) as suggested_qty,
                    CASE 
                        WHEN aif.current_stock <= aif.reorder_level THEN 'Critical'
                        WHEN aif.current_stock <= aif.reorder_level * 1.5 THEN 'Medium'
                        ELSE 'Low'
                    END as priority
                FROM `tabAI Inventory Forecast` aif
                WHERE aif.current_stock <= aif.reorder_level * 2
                OR aif.predicted_consumption > aif.current_stock
                ORDER BY 
                    CASE 
                        WHEN aif.current_stock <= aif.reorder_level THEN 1
                        WHEN aif.current_stock <= aif.reorder_level * 1.5 THEN 2
                        ELSE 3
                    END,
                    aif.predicted_consumption DESC
                LIMIT 20
            """, as_dict=True)
        else:
            items_to_order = items
        
        if not items_to_order:
            return {
                "status": "info",
                "message": "No items require purchase orders at this time",
                "data": []
            }
        
        # Group items by company and supplier
        purchase_orders = {}
        
        for item in items_to_order:
            # Get default supplier for the item
            supplier = frappe.db.get_value("Item Default", 
                                         {"parent": item["item_code"]}, 
                                         "default_supplier") or "Default Supplier"
            
            company = item.get("company", "Default Company")
            key = f"{company}_{supplier}"
            
            if key not in purchase_orders:
                purchase_orders[key] = {
                    "company": company,
                    "supplier": supplier,
                    "items": []
                }
            
            purchase_orders[key]["items"].append({
                "item_code": item["item_code"],
                "item_name": item["item_name"],
                "qty": item["suggested_qty"],
                "current_stock": item["current_stock"],
                "predicted_consumption": item["predicted_consumption"],
                "priority": item["priority"]
            })
        
        return {
            "status": "success",
            "message": f"Found {len(items_to_order)} items for purchase orders",
            "data": purchase_orders,
            "summary": {
                "total_items": len(items_to_order),
                "purchase_orders": len(purchase_orders),
                "critical_items": len([i for i in items_to_order if i.get("priority") == "Critical"])
            }
        }
        
    except Exception as e:
        frappe.log_error(f"AI purchase order creation failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_purchase_order(company, supplier, items):
    """Create actual purchase order document"""
    try:
        import json
        if isinstance(items, str):
            items = json.loads(items)
        
        # Create Purchase Order
        po = frappe.new_doc("Purchase Order")
        po.supplier = supplier
        po.company = company
        po.schedule_date = add_days(nowdate(), 7)  # Default delivery in 7 days
        
        total_amount = 0
        
        for item in items:
            # Get item rate from last purchase or standard rate
            rate = frappe.db.get_value("Item", item["item_code"], "standard_rate") or 100
            
            po.append("items", {
                "item_code": item["item_code"],
                "item_name": item.get("item_name", item["item_code"]),
                "qty": item["qty"],
                "rate": rate,
                "amount": item["qty"] * rate,
                "schedule_date": add_days(nowdate(), 7)
            })
            
            total_amount += item["qty"] * rate
        
        po.insert()
        
        return {
            "status": "success",
            "message": f"Purchase Order {po.name} created successfully",
            "purchase_order": po.name,
            "total_amount": total_amount
        }
        
    except Exception as e:
        frappe.log_error(f"Purchase order creation failed: {str(e)}")
        return {"status": "error", "message": str(e)}
