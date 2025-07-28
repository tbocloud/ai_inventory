# ai_inventory/ai_inventory/doctype/ai_inventory_forecast/ai_inventory_forecast.py
# COMPLETE SAFE VERSION - Replace your entire existing file with this

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, now, add_days, getdate, flt, cint
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
import threading

# Safe imports for ML packages - only import when actually needed
def safe_import_ml_packages():
    """Safely import ML packages with error handling"""
    try:
        import numpy as np
        import pandas as pd
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        return np, pd, LinearRegression, StandardScaler, True
    except ImportError as e:
        frappe.log_error(f"ML packages not available: {str(e)}")
        return None, None, None, None, False

class AIInventoryForecast(Document):
    def validate(self):
        """Validate the document before saving"""
        try:
            # Basic validation that doesn't require ML packages
            if not self.item_code:
                frappe.throw("Item Code is required")
            
            if not self.warehouse:
                frappe.throw("Warehouse is required")
                
            # Set company from warehouse if not set
            if not self.company and self.warehouse:
                self.company = frappe.db.get_value("Warehouse", self.warehouse, "company")
            
            # Validate warehouse belongs to the same company
            if self.warehouse and self.company:
                warehouse_company = frappe.db.get_value("Warehouse", self.warehouse, "company")
                if warehouse_company != self.company:
                    frappe.throw(f"Warehouse {self.warehouse} does not belong to company {self.company}")
            
            # Update current stock safely
            self.update_current_stock_safe()
            
            # Set preferred supplier if not set - with safety check for field existence
            try:
                if hasattr(self, 'preferred_supplier') and not getattr(self, 'preferred_supplier', None):
                    self.set_preferred_supplier_safe()
                elif not hasattr(self, 'preferred_supplier'):
                    # Field doesn't exist yet, create it and set supplier
                    self.set_preferred_supplier_safe()
            except Exception as e:
                # If preferred_supplier field doesn't exist, skip this step
                frappe.log_error(f"Preferred supplier field not found: {str(e)}")
                
        except Exception as e:
            frappe.log_error(f"AI Inventory Forecast validation error: {str(e)}")
            # Don't throw during installation - just log
            if not frappe.flags.in_install:
                frappe.throw(f"Validation failed: {str(e)}")
    
    def before_save(self):
        """Run AI forecast before saving if auto-run is enabled"""
        try:
            if (self.item_code and self.warehouse and self.company and 
                not self.flags.skip_forecast and not self.flags.in_update):
                # Use queue for forecast to avoid blocking
                self.queue_forecast_update()
        except Exception as e:
            frappe.log_error(f"AI Inventory Forecast before_save error: {str(e)}")
    
    def after_save(self):
        """Handle auto purchase order creation after save"""
        try:
            # Check if auto_create_purchase_order field exists and is enabled
            auto_create_po = getattr(self, 'auto_create_purchase_order', False)
            preferred_supplier = getattr(self, 'preferred_supplier', None)
            
            if (self.reorder_alert and 
                auto_create_po and 
                preferred_supplier and 
                not self.flags.skip_auto_po and
                not self.flags.in_update):
                
                try:
                    self.flags.skip_auto_po = True  # Prevent recursion
                    # Queue PO creation to avoid blocking
                    self.queue_auto_po_creation()
                except Exception as e:
                    frappe.log_error(f"Auto PO queue failed for {self.item_code}: {str(e)}")
                finally:
                    self.flags.skip_auto_po = False
        except Exception as e:
            frappe.log_error(f"AI Inventory Forecast after_save error: {str(e)}")
    
    def update_current_stock_safe(self):
        """Thread-safe update of current stock"""
        if not self.item_code or not self.warehouse or not self.company:
            return
            
        try:
            current_stock = frappe.db.sql("""
                SELECT b.actual_qty 
                FROM `tabBin` b
                INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
                WHERE b.item_code = %s 
                AND b.warehouse = %s
                AND w.company = %s
            """, (self.item_code, self.warehouse, self.company))
            
            self.current_stock = flt(current_stock[0][0]) if current_stock else 0.0
            
            # Get last purchase date for this company
            last_purchase = frappe.db.sql("""
                SELECT sle.posting_date 
                FROM `tabStock Ledger Entry` sle
                INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
                WHERE sle.item_code = %s 
                AND sle.warehouse = %s
                AND w.company = %s
                AND sle.voucher_type = 'Purchase Receipt'
                ORDER BY sle.posting_date DESC 
                LIMIT 1
            """, (self.item_code, self.warehouse, self.company))
            
            self.last_purchase_date = last_purchase[0][0] if last_purchase else None
            
        except Exception as e:
            frappe.log_error(f"Safe stock update failed: {str(e)}")

    def set_preferred_supplier_safe(self):
        """Thread-safe preferred supplier setting"""
        try:
            # Try importing ML analyzer, fallback to basic supplier selection
            try:
                from ai_inventory.ml_supplier_analyzer import MLSupplierAnalyzer
                
                analyzer = MLSupplierAnalyzer()
                best_supplier = analyzer.find_best_supplier_for_item(self.item_code, self.company)
                
                if best_supplier:
                    # Check if preferred_supplier field exists before setting it
                    if hasattr(self, 'preferred_supplier'):
                        self.preferred_supplier = best_supplier['supplier']
                        
                    # Always set the main supplier field
                    if not self.supplier:
                        self.supplier = best_supplier['supplier']
            except ImportError:
                # Fallback to simple supplier selection if ML analyzer not available
                self.set_basic_supplier()
                    
        except Exception as e:
            frappe.log_error(f"Safe supplier setting failed for {self.item_code}: {str(e)}")

    def set_basic_supplier(self):
        """Basic supplier setting without ML"""
        try:
            # Get most recent supplier for this item
            recent_supplier = frappe.db.sql("""
                SELECT poi.supplier 
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.item_code = %s 
                AND po.company = %s
                AND po.docstatus = 1
                ORDER BY po.transaction_date DESC 
                LIMIT 1
            """, (self.item_code, self.company))
            
            if recent_supplier:
                supplier = recent_supplier[0][0]
                if hasattr(self, 'preferred_supplier'):
                    self.preferred_supplier = supplier
                if not self.supplier:
                    self.supplier = supplier
                    
        except Exception as e:
            frappe.log_error(f"Basic supplier setting failed: {str(e)}")

    def queue_forecast_update(self):
        """Queue forecast update to avoid blocking main transaction"""
        try:
            frappe.enqueue(
                'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.run_forecast_background',
                forecast_name=self.name,
                queue='short',
                timeout=300,
                is_async=True
            )
        except Exception as e:
            frappe.log_error(f"Forecast queue failed: {str(e)}")
    
    def queue_auto_po_creation(self):
        """Queue auto PO creation to avoid blocking main transaction"""
        try:
            frappe.enqueue(
                'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.create_auto_po_background',
                forecast_name=self.name,
                queue='short',
                timeout=300,
                is_async=True
            )
        except Exception as e:
            frappe.log_error(f"Auto PO queue failed: {str(e)}")

    @frappe.whitelist()
    def run_ai_forecast(self):
        """Main AI forecasting function with company-specific data and concurrency protection"""
        try:
            # Check if already processing
            if self.flags.get('processing_forecast'):
                return {"status": "error", "message": "Forecast already processing"}

            self.flags.processing_forecast = True

            if not self.company:
                self.company = frappe.db.get_value("Warehouse", self.warehouse, "company")
                
            # Get historical data for this specific company
            historical_data = self.get_historical_consumption_data()
            
            if not historical_data:
                self.set_no_data_defaults()
                return {"status": "success", "message": "No data - using defaults"}
            
            # Use enhanced forecasting with ML insights (if available)
            forecast_result = self.enhanced_forecast(historical_data)
            
            # Update forecast fields using thread-safe method
            self.update_forecast_fields_safe(forecast_result)
            
            # Get ML price prediction if preferred supplier is set
            preferred_supplier = getattr(self, 'preferred_supplier', None)
            if preferred_supplier:
                self.get_ml_price_prediction()
            
            return {
                "status": "success", 
                "message": f"AI Forecast completed successfully for {self.company}",
                "data": {
                    "movement_type": self.movement_type,
                    "predicted_consumption": self.predicted_consumption,
                    "confidence_score": self.confidence_score,
                    "reorder_alert": self.reorder_alert,
                    "company": self.company
                }
            }
                
        except Exception as e:
            error_msg = f"AI Forecast Error for {self.item_code} in {self.company}: {str(e)}"
            frappe.log_error(error_msg)
            self.set_error_defaults(str(e))
            return {"status": "error", "message": str(e)}
        finally:
            self.flags.processing_forecast = False

    def get_historical_consumption_data(self):
        """Get historical stock movement data for specific company"""
        if not self.company:
            return []
            
        from_date = add_days(nowdate(), -90)
        
        try:
            return frappe.db.sql("""
                SELECT 
                    sle.posting_date,
                    sle.actual_qty,
                    sle.qty_after_transaction,
                    sle.voucher_type,
                    sle.voucher_no
                FROM `tabStock Ledger Entry` sle
                INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
                WHERE sle.item_code = %s 
                AND sle.warehouse = %s
                AND w.company = %s
                AND sle.posting_date >= %s
                ORDER BY sle.posting_date, sle.creation
            """, (self.item_code, self.warehouse, self.company, from_date), as_dict=True)
        except Exception as e:
            frappe.log_error(f"Historical data query failed: {str(e)}")
            return []

    def set_no_data_defaults(self):
        """Set default values when no data is available"""
        self.predicted_consumption = 0
        self.movement_type = "Non Moving"
        self.confidence_score = 0
        self.reorder_level = 0
        self.suggested_qty = 0
        self.reorder_alert = False
        self.forecast_details = f"No historical data available for {self.item_code}"

    def set_error_defaults(self, error_message):
        """Set default values when forecast encounters an error"""
        self.predicted_consumption = 0
        self.movement_type = "Critical"
        self.confidence_score = 0
        self.reorder_level = 10
        self.suggested_qty = 10
        self.reorder_alert = True
        self.forecast_details = f"Forecast error: {error_message[:200]}..."

    def enhanced_forecast(self, historical_data):
        """Enhanced forecasting - uses ML if available, falls back to basic"""
        try:
            # Try ML forecast first
            np, pd, LinearRegression, StandardScaler, ml_available = safe_import_ml_packages()
            
            if ml_available and len(historical_data) >= 10:
                return self.ml_forecast(historical_data, np, pd, LinearRegression, StandardScaler)
            else:
                return self.basic_forecast(historical_data)
                
        except Exception as e:
            frappe.log_error(f"Enhanced forecast failed, using basic: {str(e)}")
            return self.basic_forecast(historical_data)

    def ml_forecast(self, historical_data, np, pd, LinearRegression, StandardScaler):
        """ML-based forecast using numpy and pandas"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # Analyze consumption records (negative quantities)
            consumption_records = df[df['actual_qty'] < 0].copy()
            
            if len(consumption_records) < 5:
                return self.basic_forecast(historical_data)
            
            # Prepare data for ML
            consumption_records['consumption'] = consumption_records['actual_qty'].abs()
            consumption_records['days_from_start'] = (
                pd.to_datetime(consumption_records['posting_date']) - 
                pd.to_datetime(consumption_records['posting_date'].min())
            ).dt.days
            
            # Linear regression on time series
            X = consumption_records[['days_from_start']].values
            y = consumption_records['consumption'].values
            
            if len(X) >= 3:
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict future consumption
                future_days = self.forecast_period_days or 30
                prediction = model.predict([[X.max()[0] + future_days]])[0]
                predicted_consumption = max(0, prediction)
                
                # Calculate confidence based on R² score
                r2_score = model.score(X, y)
                confidence_score = max(50, min(95, r2_score * 100))
                
                # Determine movement type
                daily_avg = y.mean() / max(1, (X.max()[0] - X.min()[0]) / len(y))
                if daily_avg > 2:
                    movement_type = "Fast Moving"
                elif daily_avg > 0.5:
                    movement_type = "Slow Moving"
                else:
                    movement_type = "Non Moving"
                
                # Calculate reorder parameters
                lead_time = self.lead_time_days or 14
                safety_factor = 1.5 if movement_type == "Fast Moving" else 1.2
                reorder_level = (daily_avg * lead_time) * safety_factor
                suggested_qty = max(1, int(daily_avg * (future_days + lead_time)))
                
                current_stock = self.current_stock or 0
                reorder_alert = current_stock <= reorder_level
                
                forecast_explanation = f"""📊 ML FORECAST ANALYSIS for {self.item_code}

🤖 MACHINE LEARNING INSIGHTS:
• Algorithm: Linear Regression
• Training Data: {len(consumption_records)} consumption events
• Model Accuracy (R²): {r2_score:.3f}
• Daily Consumption Rate: {daily_avg:.2f} units/day

🔮 PREDICTIONS:
• Predicted Consumption ({future_days} days): {predicted_consumption:.2f} units
• Movement Classification: {movement_type}
• Confidence Level: {confidence_score:.1f}%

📦 RECOMMENDATIONS:
• Current Stock: {current_stock} units
• Reorder Level: {reorder_level:.2f} units
• Suggested Order Qty: {suggested_qty} units
• Reorder Alert: {'🚨 YES' if reorder_alert else '✅ NO'}

🏢 Company: {self.company}
📦 Warehouse: {self.warehouse}
📅 Analysis Date: {nowdate()}"""

                return {
                    'predicted_consumption': predicted_consumption,
                    'movement_type': movement_type,
                    'confidence_score': confidence_score,
                    'reorder_level': reorder_level,
                    'suggested_qty': suggested_qty,
                    'reorder_alert': reorder_alert,
                    'forecast_explanation': forecast_explanation
                }
            else:
                return self.basic_forecast(historical_data)
                
        except Exception as e:
            frappe.log_error(f"ML forecast calculation failed: {str(e)}")
            return self.basic_forecast(historical_data)

    def basic_forecast(self, historical_data):
        """Enhanced basic forecast with detailed analysis"""
        try:
            # Analyze historical data
            consumption_records = [d for d in historical_data if d['actual_qty'] < 0]
            receipt_records = [d for d in historical_data if d['actual_qty'] > 0]
            
            if not consumption_records:
                return {
                    'predicted_consumption': 0,
                    'movement_type': 'Non Moving',
                    'confidence_score': 30,
                    'reorder_level': 0,
                    'suggested_qty': 0,
                    'reorder_alert': False,
                    'forecast_explanation': f"""📊 BASIC FORECAST ANALYSIS for {self.item_code}

🔍 DATA ANALYSIS:
• Historical Period: {len(historical_data)} transactions in last 90 days
• Consumption Records: {len(consumption_records)} (no outbound movement detected)
• Receipt Records: {len(receipt_records)} 
• Movement Pattern: Non-Moving Item

📈 FORECAST RESULTS:
• Predicted Consumption (30 days): 0 units
• Movement Classification: Non Moving
• Confidence Level: 30% (Low - based on no movement pattern)

⚡ RECOMMENDATIONS:
• No reorder needed - item shows no consumption
• Monitor for any future demand changes
• Consider if item is still active in business

🏢 Company: {self.company}
📦 Warehouse: {self.warehouse}
📅 Analysis Date: {nowdate()}"""
                }
            
            # Calculate consumption metrics
            total_consumption = sum(abs(d['actual_qty']) for d in consumption_records)
            total_receipts = sum(d['actual_qty'] for d in receipt_records)
            days_with_consumption = len(consumption_records)
            avg_consumption_per_transaction = total_consumption / days_with_consumption if days_with_consumption > 0 else 0
            
            # Calculate daily consumption rate
            days_span = max(30, len(set(d['posting_date'] for d in historical_data)))
            daily_consumption = total_consumption / days_span
            predicted_consumption = daily_consumption * (self.forecast_period_days or 30)
            
            # Determine movement type based on consumption frequency and volume
            if daily_consumption > 5 or days_with_consumption > 15:
                movement_type = "Fast Moving"
                confidence_score = 85
            elif daily_consumption > 1 or days_with_consumption > 5:
                movement_type = "Slow Moving"
                confidence_score = 70
            elif daily_consumption > 0.1:
                movement_type = "Non Moving"
                confidence_score = 50
            else:
                movement_type = "Critical"
                confidence_score = 40
            
            # Calculate reorder parameters
            lead_time = self.lead_time_days or 14
            safety_stock_multiplier = 1.5 if movement_type == "Fast Moving" else 1.2
            reorder_level = (daily_consumption * lead_time) * safety_stock_multiplier
            
            # Suggested quantity calculation
            if movement_type == "Fast Moving":
                suggested_qty = max(10, int(daily_consumption * 45))  # 1.5 months supply
            elif movement_type == "Slow Moving":
                suggested_qty = max(5, int(daily_consumption * 60))   # 2 months supply
            else:
                suggested_qty = max(1, int(daily_consumption * 30))   # 1 month supply
            
            # Determine if reorder alert is needed
            current_stock = self.current_stock or 0
            reorder_alert = current_stock <= reorder_level
            
            # Create detailed analysis
            forecast_explanation = f"""📊 BASIC FORECAST ANALYSIS for {self.item_code}

🔍 DATA ANALYSIS:
• Historical Period: {days_span} days (Last 90 days)
• Total Transactions: {len(historical_data)}
• Consumption Events: {len(consumption_records)} transactions
• Receipt Events: {len(receipt_records)} transactions
• Total Consumed: {total_consumption:.2f} units
• Total Received: {total_receipts:.2f} units

📈 CONSUMPTION PATTERN:
• Daily Consumption Rate: {daily_consumption:.2f} units/day
• Avg per Transaction: {avg_consumption_per_transaction:.2f} units
• Movement Classification: {movement_type}
• Consumption Frequency: {(days_with_consumption/days_span)*100:.1f}% of days

🔮 FORECAST RESULTS:
• Predicted Consumption ({self.forecast_period_days or 30} days): {predicted_consumption:.2f} units
• Confidence Level: {confidence_score}% ({
    'High' if confidence_score > 80 else 
    'Medium' if confidence_score > 60 else 
    'Low'
})

📦 INVENTORY RECOMMENDATIONS:
• Current Stock: {current_stock} units
• Reorder Level: {reorder_level:.2f} units
• Suggested Order Qty: {suggested_qty} units
• Lead Time: {lead_time} days
• Safety Stock Factor: {safety_stock_multiplier}x

⚡ STATUS: {
    '🚨 REORDER NOW - Stock below reorder level!' if reorder_alert else 
    '✅ Stock levels adequate'
}

🏢 Company: {self.company}
📦 Warehouse: {self.warehouse}
📅 Analysis Date: {nowdate()}
🤖 AI Confidence: Based on {len(historical_data)} data points"""
            
            return {
                'predicted_consumption': predicted_consumption,
                'movement_type': movement_type,
                'confidence_score': confidence_score,
                'reorder_level': reorder_level,
                'suggested_qty': suggested_qty,
                'reorder_alert': reorder_alert,
                'forecast_explanation': forecast_explanation
            }
            
        except Exception as e:
            frappe.log_error(f"Basic forecast calculation failed: {str(e)}")
            return {
                'predicted_consumption': 0,
                'movement_type': 'Critical',
                'confidence_score': 0,
                'reorder_level': 10,
                'suggested_qty': 10,
                'reorder_alert': True,
                'forecast_explanation': f"""📊 FORECAST ERROR for {self.item_code}

❌ ERROR: {str(e)[:200]}

🔧 FALLBACK SETTINGS APPLIED:
• Movement Type: Critical (due to error)
• Suggested Reorder: 10 units
• Recommended Action: Manual review required

🏢 Company: {self.company}
📦 Warehouse: {self.warehouse}
📅 Analysis Date: {nowdate()}"""
            }

    def update_forecast_fields_safe(self, forecast_result):
        """Thread-safe update of forecast fields"""
        try:
            frappe.db.sql("""
                UPDATE `tabAI Inventory Forecast`
                SET 
                    predicted_consumption = %s,
                    movement_type = %s,
                    confidence_score = %s,
                    reorder_level = %s,
                    suggested_qty = %s,
                    reorder_alert = %s,
                    last_forecast_date = %s,
                    forecast_details = %s,
                    modified = %s
                WHERE name = %s
            """, (
                forecast_result['predicted_consumption'],
                forecast_result['movement_type'],
                forecast_result['confidence_score'],
                forecast_result['reorder_level'],
                forecast_result['suggested_qty'],
                forecast_result['reorder_alert'],
                now(),
                forecast_result['forecast_explanation'],
                now(),
                self.name
            ))
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Forecast field update failed: {str(e)}")

    def get_ml_price_prediction(self):
        """Get ML price prediction for the preferred supplier"""
        try:
            if not getattr(self, 'preferred_supplier', None):
                return
            
            # Try importing ML analyzer
            try:
                from ai_inventory.ml_supplier_analyzer import MLSupplierAnalyzer
                analyzer = MLSupplierAnalyzer()
                
                price_result = analyzer.predict_item_price(
                    self.item_code, 
                    self.preferred_supplier, 
                    self.company,
                    self.suggested_qty or 1
                )
                
                if price_result.get('status') == 'success':
                    predicted_price = price_result.get('predicted_price', 0)
                    confidence = price_result.get('confidence', 0)
                    
                    if predicted_price > 0:
                        price_note = f"\n\n💰 ML Price Prediction: ₹{predicted_price:.2f} (Confidence: {confidence}%)"
                        self.forecast_details = (self.forecast_details or "") + price_note
            except ImportError:
                # ML analyzer not available, skip price prediction
                pass
                    
        except Exception as e:
            frappe.log_error(f"ML price prediction failed for {self.item_code}: {str(e)}")

    @frappe.whitelist()
    def create_purchase_order(self):
        """Create purchase order for this forecast"""
        try:
            if not self.supplier and not getattr(self, 'preferred_supplier', None):
                return {"status": "error", "message": "No supplier specified"}
            
            supplier = getattr(self, 'preferred_supplier', None) or self.supplier
            
            if not self.suggested_qty or self.suggested_qty <= 0:
                return {"status": "error", "message": "No suggested quantity available"}
            
            # Create Purchase Order
            po = frappe.get_doc({
                "doctype": "Purchase Order",
                "supplier": supplier,
                "company": self.company,
                "schedule_date": add_days(nowdate(), self.lead_time_days or 14),
                "items": [{
                    "item_code": self.item_code,
                    "qty": self.suggested_qty,
                    "warehouse": self.warehouse,
                    "schedule_date": add_days(nowdate(), self.lead_time_days or 14)
                }]
            })
            
            po.insert()
            
            # Update forecast with PO reference
            po_note = f"\n\n📋 Purchase Order {po.name} created on {nowdate()} for {self.suggested_qty} units"
            self.forecast_details = (self.forecast_details or "") + po_note
            self.save()
            
            return {
                "status": "success",
                "message": f"Purchase Order {po.name} created successfully",
                "po_name": po.name
            }
            
        except Exception as e:
            error_msg = f"PO creation failed: {str(e)}"
            frappe.log_error(error_msg)
            return {"status": "error", "message": error_msg}

    @frappe.whitelist()
    def create_automatic_purchase_order(self):
        """Create automatic purchase order if conditions are met"""
        try:
            if not self.reorder_alert:
                return {"status": "info", "message": "No reorder alert - PO not needed"}
            
            preferred_supplier = getattr(self, 'preferred_supplier', None)
            if not preferred_supplier:
                return {"status": "error", "message": "No preferred supplier set"}
            
            if not self.suggested_qty or self.suggested_qty <= 0:
                return {"status": "error", "message": "No suggested quantity"}
            
            # Check if PO already exists for this item recently
            recent_po = frappe.db.exists("Purchase Order Item", {
                "item_code": self.item_code,
                "parent": ["like", "%"],
                "creation": [">=", add_days(nowdate(), -7)]
            })
            
            if recent_po:
                return {"status": "info", "message": "Recent PO already exists for this item"}
            
            # Create Purchase Order
            po = frappe.get_doc({
                "doctype": "Purchase Order",
                "supplier": preferred_supplier,
                "company": self.company,
                "schedule_date": add_days(nowdate(), self.lead_time_days or 14),
                "items": [{
                    "item_code": self.item_code,
                    "qty": self.suggested_qty,
                    "warehouse": self.warehouse,
                    "schedule_date": add_days(nowdate(), self.lead_time_days or 14)
                }]
            })
            
            po.insert()
            
            # Update forecast with PO reference
            po_note = f"\n\n🤖 Auto-created Purchase Order {po.name} on {nowdate()} for {self.suggested_qty} units"
            self.forecast_details = (self.forecast_details or "") + po_note
            self.save()
            
            return {
                "status": "success",
                "message": f"Auto Purchase Order {po.name} created successfully",
                "po_name": po.name
            }
            
        except Exception as e:
            error_msg = f"Auto PO creation failed: {str(e)}"
            frappe.log_error(error_msg)
            return {"status": "error", "message": error_msg}


# Background job functions to handle async operations
@frappe.whitelist()
def run_forecast_background(forecast_name):
    """Run forecast in background to avoid blocking main transaction"""
    try:
        # Add small delay to avoid immediate conflicts
        time.sleep(0.5)
        
        # Get fresh document
        doc = frappe.get_doc("AI Inventory Forecast", forecast_name)
        
        # Set flag to prevent recursive calls
        doc.flags.skip_forecast = True
        doc.flags.in_update = True
        
        # Run forecast
        result = doc.run_ai_forecast()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Background forecast failed for {forecast_name}: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_auto_po_background(forecast_name):
    """Create auto PO in background"""
    try:
        # Add small delay to avoid conflicts
        time.sleep(1)
        
        # Get fresh document
        doc = frappe.get_doc("AI Inventory Forecast", forecast_name)
        
        # Set flags to prevent recursive calls
        doc.flags.skip_auto_po = True
        doc.flags.in_update = True
        
        # Create PO
        result = doc.create_automatic_purchase_order()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Background auto PO creation failed for {forecast_name}: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def sync_ai_forecasts_now(company=None):
    """Sync AI forecasts immediately with company filter"""
    try:
        # Set bulk operation flag to prevent recursive hooks
        frappe.flags.in_bulk_operation = True
        
        # Build filters
        filters = {}
        if company:
            filters["company"] = company
        
        # Get forecasts to sync
        forecasts = frappe.get_all("AI Inventory Forecast",
            filters=filters,
            fields=["name", "item_code", "warehouse", "company"],
            limit=200  # Limit to prevent timeout
        )
        
        if not forecasts:
            return {
                "status": "info",
                "message": f"No forecasts found{' for ' + company if company else ''}",
                "total_items": 0,
                "successful": 0,
                "failed": 0
            }
        
        successful = 0
        failed = 0
        reorder_alerts_count = 0
        critical_items = []
        
        for forecast_data in forecasts:
            try:
                # Get the document and run forecast
                doc = frappe.get_doc("AI Inventory Forecast", forecast_data.name)
                
                # Skip forecast run to avoid recursive calls
                doc.flags.skip_forecast = True
                
                # Update current stock safely
                doc.update_current_stock_safe()
                
                # Run AI forecast
                result = doc.run_ai_forecast()
                
                if result.get("status") == "success":
                    successful += 1
                    
                    # Check for reorder alerts
                    doc.reload()  # Reload to get updated values
                    if doc.reorder_alert:
                        reorder_alerts_count += 1
                        if doc.movement_type in ["Fast Moving", "Critical"]:
                            critical_items.append({
                                "item_code": doc.item_code,
                                "warehouse": doc.warehouse,
                                "company": doc.company,
                                "movement_type": doc.movement_type,
                                "current_stock": doc.current_stock,
                                "reorder_level": doc.reorder_level
                            })
                else:
                    failed += 1
                    
                # Commit every 50 items to avoid timeout
                if (successful + failed) % 50 == 0:
                    frappe.db.commit()
                    
            except Exception as e:
                failed += 1
                frappe.log_error(f"Sync failed for {forecast_data.item_code}: {str(e)}")
        
        # Final commit
        frappe.db.commit()
        
        # Calculate success rate
        total_items = len(forecasts)
        success_rate = (successful / total_items * 100) if total_items > 0 else 0
        
        return {
            "status": "success",
            "message": f"Sync completed{' for ' + company if company else ''}: {successful} successful, {failed} failed",
            "total_items": total_items,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 1),
            "reorder_alerts_count": reorder_alerts_count,
            "critical_items": critical_items[:10],  # Limit to top 10 critical items
            "company": company
        }
        
    except Exception as e:
        error_msg = f"Sync failed{' for ' + company if company else ''}: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    finally:
        frappe.flags.in_bulk_operation = False

@frappe.whitelist()
def check_ml_dependencies():
    """Check if ML dependencies are available"""
    np, pd, LinearRegression, StandardScaler, ml_available = safe_import_ml_packages()
    
    if ml_available:
        return {
            "status": "available",
            "message": "All ML dependencies are installed and working",
            "packages": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "sklearn": "available"
            }
        }
    else:
        return {
            "status": "missing",
            "message": "ML packages are not available",
            "instruction": "Install with: ./env/bin/pip install numpy pandas scikit-learn"
        }

@frappe.whitelist()
def create_forecasts_for_all_existing_items():
    """Create AI Inventory Forecasts for all existing items that don't have them"""
    try:
        # Get all stock items
        items = frappe.get_all("Item", 
            filters={"is_stock_item": 1, "disabled": 0}, 
            fields=["name", "item_name"]
        )
        
        # Get all active warehouses
        warehouses = frappe.get_all("Warehouse", 
            filters={"disabled": 0}, 
            fields=["name", "company"]
        )
        
        total_created = 0
        total_processed = 0
        company_breakdown = {}
        
        frappe.logger().info(f"Starting forecast creation for {len(items)} items across {len(warehouses)} warehouses")
        
        for item in items:
            for warehouse in warehouses:
                try:
                    # Check if forecast already exists
                    existing = frappe.db.exists("AI Inventory Forecast", {
                        "item_code": item.name,
                        "warehouse": warehouse.name,
                        "company": warehouse.company
                    })
                    
                    if not existing:
                        # Get current stock
                        current_stock = frappe.db.get_value("Bin", {
                            "item_code": item.name,
                            "warehouse": warehouse.name
                        }, "actual_qty") or 0
                        
                        # Create forecast
                        forecast = frappe.get_doc({
                            "doctype": "AI Inventory Forecast",
                            "item_code": item.name,
                            "warehouse": warehouse.name,
                            "company": warehouse.company,
                            "forecast_period_days": 30,
                            "lead_time_days": 14,
                            "current_stock": current_stock,
                            "predicted_consumption": 0,
                            "movement_type": "New Item",
                            "confidence_score": 0,
                            "forecast_details": f"Auto-created forecast for existing item {item.name}"
                        })
                        
                        forecast.flags.skip_forecast = True
                        forecast.insert(ignore_permissions=True)
                        total_created += 1
                        
                        company_breakdown[warehouse.company] = company_breakdown.get(warehouse.company, 0) + 1
                    
                    total_processed += 1
                    
                    if total_processed % 50 == 0:
                        frappe.db.commit()
                        frappe.logger().info(f"Processed {total_processed} combinations, created {total_created} forecasts")
                        
                except Exception as e:
                    frappe.log_error(f"Failed to create forecast for {item.name} in {warehouse.name}: {str(e)}")
                    continue
        
        frappe.db.commit()
        
        company_summary = ", ".join([f"{comp}: {count}" for comp, count in company_breakdown.items()])
        
        return {
            "status": "success",
            "message": f"Created {total_created} AI Inventory Forecasts for existing items",
            "total_items": len(items),
            "total_warehouses": len(warehouses),
            "total_processed": total_processed,
            "forecasts_created": total_created,
            "company_breakdown": company_breakdown,
            "company_summary": company_summary
        }
        
    except Exception as e:
        error_msg = f"Failed to create forecasts for existing items: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "forecasts_created": 0
        }