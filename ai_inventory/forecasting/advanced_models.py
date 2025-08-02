# ==========================================
# ai_inventory/forecasting/advanced_models.py
# Advanced forecasting models (Prophet, LSTM, etc.)

import frappe
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    frappe.log_error("Prophet library not available. Install with: pip install prophet", "AI Sales Forecasting")

class AdvancedForecastingModels:
    
    def __init__(self):
        self.models = {}
    
    def prophet_forecast(self, item_code, days_ahead=30):
        """Generate forecasts using Facebook Prophet"""
        if not PROPHET_AVAILABLE:
            return None
        
        try:
            # Get historical data
            historical = frappe.db.sql("""
                SELECT 
                    si.posting_date as ds,
                    SUM(sii.qty) as y
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
                WHERE sii.item_code = %s
                AND si.docstatus = 1
                AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
                GROUP BY si.posting_date
                ORDER BY si.posting_date
            """, (item_code,), as_dict=True)
            
            if len(historical) < 30:  # Need minimum data points
                return None
            
            df = pd.DataFrame(historical)
            df['ds'] = pd.to_datetime(df['ds'])
            
            # Initialize and fit Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future)
            
            # Extract future predictions
            future_forecast = forecast[forecast['ds'] > df['ds'].max()].copy()
            
            return {
                'dates': future_forecast['ds'].dt.date.tolist(),
                'predictions': future_forecast['yhat'].tolist(),
                'lower_bound': future_forecast['yhat_lower'].tolist(),
                'upper_bound': future_forecast['yhat_upper'].tolist()
            }
            
        except Exception as e:
            frappe.log_error(f"Prophet forecast failed for {item_code}: {str(e)}", "AI Sales Forecasting")
            return None
    
    def seasonal_naive_forecast(self, item_code, days_ahead=30):
        """Simple seasonal naive forecasting"""
        try:
            # Get same day of week/month from previous periods
            historical = frappe.db.sql("""
                SELECT 
                    si.posting_date,
                    SUM(sii.qty) as qty,
                    DAYOFWEEK(si.posting_date) as dow,
                    DAY(si.posting_date) as dom
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
                WHERE sii.item_code = %s
                AND si.docstatus = 1
                AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
                GROUP BY si.posting_date
                ORDER BY si.posting_date
            """, (item_code,), as_dict=True)
            
            if not historical:
                return None
            
            df = pd.DataFrame(historical)
            
            forecasts = []
            base_date = datetime.now().date()
            
            for i in range(1, days_ahead + 1):
                forecast_date = base_date + timedelta(days=i)
                dow = forecast_date.weekday() + 1  # Monday = 1
                dom = forecast_date.day
                
                # Find similar historical days
                similar_days = df[
                    (df['dow'] == dow) | (df['dom'] == dom)
                ]['qty'].tolist()
                
                if similar_days:
                    predicted_qty = np.mean(similar_days)
                else:
                    predicted_qty = df['qty'].mean()
                
                forecasts.append({
                    'date': forecast_date,
                    'predicted_qty': max(0, predicted_qty)
                })
            
            return forecasts
            
        except Exception as e:
            frappe.log_error(f"Seasonal naive forecast failed for {item_code}: {str(e)}", "AI Sales Forecasting")
            return None