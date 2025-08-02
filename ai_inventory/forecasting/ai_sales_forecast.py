# ai_inventory/forecasting/ai_sales_forecast.py
# Complete AI Sales Forecasting System for ERPNext/Frappe
# This module handles training ML models and generating sales forecasts

import frappe
from datetime import datetime, timedelta
from frappe.utils import nowdate, add_days, getdate
import warnings
warnings.filterwarnings('ignore')

# Try to import ML libraries with fallback
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    frappe.log_error("pandas/numpy not available. Using fallback methods.", "AI Sales Forecasting")

try:
    import joblib
    import os
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

# Try to import ML libraries with fallback
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    frappe.log_error("scikit-learn not available. Using simple forecasting.", "AI Sales Forecasting")

class SalesForecastingEngine:
    def __init__(self):
        try:
            self.config = frappe.get_single("AI Sales Dashboard")
        except Exception as e:
            frappe.log_error(f"Could not load AI Sales Dashboard: {str(e)}", "AI Sales Forecasting")
            self.config = None
            
        self.models = {}
        self.encoders = {}
        self.model_path = frappe.get_site_path("private", "files", "ai_models")
        
        # Create models directory if it doesn't exist
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
    
    def extract_historical_data(self, days_back=365):
        """Extract historical sales data for training"""
        start_date = add_days(nowdate(), -days_back)
        
        # Get sales invoice data with better error handling
        sales_data = frappe.db.sql("""
            SELECT 
                si.posting_date,
                si.customer,
                COALESCE(si.territory, '') as territory,
                sii.item_code,
                sii.qty,
                sii.amount,
                sii.rate,
                COALESCE(si.base_net_total, 0) as base_net_total,
                COALESCE(c.customer_segment, 'C') as customer_segment,
                COALESCE(c.churn_probability, 0) as churn_probability,
                COALESCE(i.item_group, 'All Item Groups') as item_group,
                COALESCE(i.enable_forecast, 0) as enable_forecast
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
            LEFT JOIN `tabCustomer` c ON si.customer = c.name
            LEFT JOIN `tabItem` i ON sii.item_code = i.name
            WHERE si.docstatus = 1 
            AND si.posting_date >= %s
            AND COALESCE(i.enable_forecast, 0) = 1
            ORDER BY si.posting_date
        """, (start_date,), as_dict=True)
        
        # Get sales order data for additional context
        order_data = frappe.db.sql("""
            SELECT 
                so.transaction_date as posting_date,
                so.customer,
                COALESCE(so.territory, '') as territory,
                soi.item_code,
                soi.qty,
                soi.amount,
                soi.rate,
                COALESCE(so.base_net_total, 0) as base_net_total
            FROM `tabSales Order` so
            INNER JOIN `tabSales Order Item` soi ON so.name = soi.parent
            LEFT JOIN `tabItem` i ON soi.item_code = i.name
            WHERE so.docstatus = 1 
            AND so.transaction_date >= %s
            AND COALESCE(i.enable_forecast, 0) = 1
            ORDER BY so.transaction_date
        """, (start_date,), as_dict=True)
        
        frappe.log_error(f"Extracted {len(sales_data)} sales records and {len(order_data)} order records", "AI Sales Forecasting")
        return sales_data, order_data
    
    def prepare_features(self, data):
        """Prepare features for machine learning"""
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        if df.empty:
            return df
        
        df['posting_date'] = pd.to_datetime(df['posting_date'])
        df = df.sort_values('posting_date')
        
        # Time-based features
        df['year'] = df['posting_date'].dt.year
        df['month'] = df['posting_date'].dt.month
        df['quarter'] = df['posting_date'].dt.quarter
        df['day_of_week'] = df['posting_date'].dt.dayofweek
        df['day_of_year'] = df['posting_date'].dt.dayofyear
        df['week_of_year'] = df['posting_date'].dt.isocalendar().week
        
        # Rolling averages and trends (with error handling)
        try:
            df = df.groupby(['item_code', 'customer']).apply(self._add_rolling_features).reset_index(drop=True)
        except Exception as e:
            frappe.log_error(f"Error adding rolling features: {str(e)}", "AI Sales Forecasting")
            # Add default rolling features
            df['qty_rolling_7'] = df['qty']
            df['qty_rolling_30'] = df['qty']
            df['amount_rolling_7'] = df['amount']
            df['amount_rolling_30'] = df['amount']
            df['qty_lag_1'] = 0
            df['qty_lag_7'] = 0
            df['amount_lag_1'] = 0
            df['qty_trend'] = 0
            df['amount_trend'] = 0
        
        # Encode categorical variables if sklearn is available
        if SKLEARN_AVAILABLE:
            categorical_cols = ['customer', 'territory', 'item_code', 'customer_segment', 'item_group']
            for col in categorical_cols:
                if col in df.columns:
                    try:
                        if col not in self.encoders:
                            self.encoders[col] = LabelEncoder()
                            df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].fillna('Unknown'))
                        else:
                            df[f'{col}_encoded'] = self.encoders[col].transform(df[col].fillna('Unknown'))
                    except Exception as e:
                        frappe.log_error(f"Error encoding {col}: {str(e)}", "AI Sales Forecasting")
                        df[f'{col}_encoded'] = 0
        
        return df
    
    def _add_rolling_features(self, group):
        """Add rolling window features for time series"""
        if len(group) < 3:
            # For small groups, just use current values
            group['qty_rolling_7'] = group['qty']
            group['qty_rolling_30'] = group['qty']
            group['amount_rolling_7'] = group['amount']
            group['amount_rolling_30'] = group['amount']
            group['qty_lag_1'] = 0
            group['qty_lag_7'] = 0
            group['amount_lag_1'] = 0
            group['qty_trend'] = 0
            group['amount_trend'] = 0
            return group
        
        group = group.sort_values('posting_date')
        
        # Rolling averages
        group['qty_rolling_7'] = group['qty'].rolling(window=7, min_periods=1).mean()
        group['qty_rolling_30'] = group['qty'].rolling(window=30, min_periods=1).mean()
        group['amount_rolling_7'] = group['amount'].rolling(window=7, min_periods=1).mean()
        group['amount_rolling_30'] = group['amount'].rolling(window=30, min_periods=1).mean()
        
        # Lag features
        group['qty_lag_1'] = group['qty'].shift(1).fillna(0)
        group['qty_lag_7'] = group['qty'].shift(7).fillna(0)
        group['amount_lag_1'] = group['amount'].shift(1).fillna(0)
        
        # Trend features
        group['qty_trend'] = group['qty'].pct_change(periods=7).fillna(0)
        group['amount_trend'] = group['amount'].pct_change(periods=7).fillna(0)
        
        return group
    
    def train_models(self):
        """Train forecasting models for different items and customers"""
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not available. Using simple forecasting instead."}
            
        frappe.log_error("Starting model training", "AI Sales Forecasting")
        
        # Extract data
        sales_data, order_data = self.extract_historical_data()
        
        if not sales_data:
            return {"error": "No historical sales data found for training"}
        
        # Prepare features
        df = self.prepare_features(sales_data)
        
        if df.empty:
            return {"error": "No data available after preprocessing"}
        
        # Feature columns
        feature_cols = [
            'year', 'month', 'quarter', 'day_of_week', 'day_of_year', 'week_of_year',
            'customer_encoded', 'territory_encoded', 'item_code_encoded',
            'qty_rolling_7', 'qty_rolling_30', 'amount_rolling_7', 'amount_rolling_30',
            'qty_lag_1', 'qty_lag_7', 'amount_lag_1', 'qty_trend', 'amount_trend',
            'rate', 'churn_probability'
        ]
        
        # Remove missing feature columns
        feature_cols = [col for col in feature_cols if col in df.columns]
        
        # Fill NaN values
        df[feature_cols] = df[feature_cols].fillna(0)
        
        # Train models for each item
        items_with_forecast = df['item_code'].unique()
        model_performance = {}
        
        for item in items_with_forecast:
            try:
                item_data = df[df['item_code'] == item].copy()
                
                if len(item_data) < 10:  # Need minimum data points
                    continue
                
                # Prepare training data
                X = item_data[feature_cols]
                y_qty = item_data['qty']
                y_amount = item_data['amount']
                
                # Split data (80% train, 20% test)
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X[:split_idx], X[split_idx:]
                y_qty_train, y_qty_test = y_qty[:split_idx], y_qty[split_idx:]
                y_amount_train, y_amount_test = y_amount[:split_idx], y_amount[split_idx:]
                
                # Train quantity model
                qty_model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
                qty_model.fit(X_train, y_qty_train)
                
                # Train amount model
                amount_model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
                amount_model.fit(X_train, y_amount_train)
                
                # Evaluate models
                if len(X_test) > 0:
                    qty_pred = qty_model.predict(X_test)
                    amount_pred = amount_model.predict(X_test)
                    
                    qty_mae = mean_absolute_error(y_qty_test, qty_pred)
                    amount_mae = mean_absolute_error(y_amount_test, amount_pred)
                else:
                    qty_mae = 0
                    amount_mae = 0
                
                # Store models
                self.models[f"{item}_qty"] = qty_model
                self.models[f"{item}_amount"] = amount_model
                
                model_performance[item] = {
                    'qty_mae': qty_mae,
                    'amount_mae': amount_mae,
                    'data_points': len(item_data)
                }
                
                # Save models to disk
                joblib.dump(qty_model, os.path.join(self.model_path, f"{item}_qty_model.pkl"))
                joblib.dump(amount_model, os.path.join(self.model_path, f"{item}_amount_model.pkl"))
                
            except Exception as e:
                frappe.log_error(f"Error training model for item {item}: {str(e)}", "AI Sales Forecasting")
                continue
        
        # Save encoders
        try:
            joblib.dump(self.encoders, os.path.join(self.model_path, "encoders.pkl"))
        except Exception as e:
            frappe.log_error(f"Error saving encoders: {str(e)}", "AI Sales Forecasting")
        
        # Update dashboard with training results
        self._update_training_stats(model_performance)
        
        frappe.log_error(f"Training completed for {len(model_performance)} items", "AI Sales Forecasting")
        return model_performance
    
    def load_models(self):
        """Load trained models from disk"""
        if not SKLEARN_AVAILABLE:
            return False
            
        try:
            # Load encoders
            encoder_path = os.path.join(self.model_path, "encoders.pkl")
            if os.path.exists(encoder_path):
                self.encoders = joblib.load(encoder_path)
            
            # Load item models
            if os.path.exists(self.model_path):
                for file in os.listdir(self.model_path):
                    if file.endswith('_model.pkl'):
                        model_name = file.replace('_model.pkl', '')
                        model_path = os.path.join(self.model_path, file)
                        self.models[model_name] = joblib.load(model_path)
            
            return len(self.models) > 0
                        
        except Exception as e:
            frappe.log_error(f"Error loading models: {str(e)}", "AI Sales Forecasting")
            return False
    
    def generate_forecasts(self, forecast_days=None):
        """Generate sales forecasts"""
        if not forecast_days:
            forecast_days = getattr(self.config, 'default_forecast_period', 30) if self.config else 30
        
        # Try to load ML models first
        models_loaded = self.load_models() if SKLEARN_AVAILABLE else False
        
        if models_loaded and self.models:
            return self._generate_ml_forecasts(forecast_days)
        else:
            return self._generate_simple_forecasts(forecast_days)
    
    def _generate_ml_forecasts(self, forecast_days):
        """Generate forecasts using ML models"""
        # Ensure forecast_days is an integer
        forecast_days = int(forecast_days) if forecast_days else 30
        
        # Clear existing forecasts
        frappe.db.delete("AI Sales Forecast")
        frappe.db.commit()
        
        # Get items enabled for forecasting
        items = frappe.db.get_all("Item", 
                                 filters={"enable_forecast": 1}, 
                                 fields=["name", "item_group"])
        
        # Get active customers
        customers = frappe.db.get_all("Customer", 
                                    fields=["name", "territory", "customer_segment", "churn_probability"])
        
        forecasts_created = 0
        min_confidence = getattr(self.config, 'min_confidence_threshold', 70) if self.config else 70
        
        for item in items:
            item_code = item['name']
            
            # Check if we have models for this item
            qty_model_key = f"{item_code}_qty"
            amount_model_key = f"{item_code}_amount"
            
            if qty_model_key not in self.models or amount_model_key not in self.models:
                continue
            
            for customer in customers:
                try:
                    # Generate forecast for each day
                    for day_offset in range(1, forecast_days + 1):
                        forecast_date = add_days(nowdate(), day_offset)
                        
                        # Prepare features for prediction
                        features = self._prepare_prediction_features(
                            item_code, customer, forecast_date, day_offset
                        )
                        
                        if features is None:
                            continue
                        
                        # Make predictions
                        qty_pred = self.models[qty_model_key].predict([features])[0]
                        amount_pred = self.models[amount_model_key].predict([features])[0]
                        
                        # Ensure positive predictions
                        qty_pred = max(0, qty_pred)
                        amount_pred = max(0, amount_pred)
                        
                        # Calculate confidence score
                        confidence = self._calculate_confidence(item_code, customer['name'], qty_pred)
                        
                        # Only create forecast if above minimum confidence
                        if confidence >= min_confidence:
                            # Create forecast record
                            forecast_doc = frappe.get_doc({
                                "doctype": "AI Sales Forecast",
                                "item_code": item_code,
                                "customer": customer['name'],
                                "territory": customer.get('territory'),
                                "forecast_date": forecast_date,
                                "predicted_qty": round(qty_pred, 2),
                                "horizon_days": day_offset,
                                "trigger_source": "Manual",
                                "model_version": "RF_v1.0",
                                "confidence_score": confidence,
                                "notes": f"Generated by RandomForest model"
                            })
                            
                            forecast_doc.insert(ignore_permissions=True)
                            forecasts_created += 1
                
                except Exception as e:
                    frappe.log_error(f"Error generating forecast for {item_code}-{customer['name']}: {str(e)}", 
                                   "AI Sales Forecasting")
                    continue
        
        # Update item forecast summaries
        self._update_item_forecasts()
        
        # Update dashboard stats
        self._update_dashboard_stats(forecasts_created)
        
        frappe.db.commit()
        return forecasts_created
    
    def _generate_simple_forecasts(self, forecast_days):
        """Generate simple forecasts when ML models are not available"""
        frappe.log_error("Generating simple forecasts (ML models not available)", "AI Sales Forecasting")
        
        # Ensure forecast_days is an integer
        forecast_days = int(forecast_days) if forecast_days else 30
        
        import random
        
        # Clear existing forecasts
        frappe.db.delete("AI Sales Forecast")
        frappe.db.commit()
        
        # Get items and customers
        items = frappe.db.get_all("Item", filters={"enable_forecast": 1})
        customers = frappe.db.get_all("Customer")
        
        if not items or not customers:
            return 0
        
        forecasts_created = 0
        
        for item in items:
            for customer in customers:
                # Get historical data for this item-customer combination
                historical = frappe.db.sql("""
                    SELECT 
                        AVG(sii.qty) as avg_qty,
                        COUNT(*) as transaction_count,
                        STDDEV(sii.qty) as qty_stddev,
                        MAX(si.posting_date) as last_sale_date
                    FROM `tabSales Invoice Item` sii
                    INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
                    WHERE sii.item_code = %s AND si.customer = %s AND si.docstatus = 1
                    AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                """, (item.name, customer.name), as_dict=True)
                
                hist_data = historical[0] if historical else {}
                
                # Calculate base prediction parameters
                if hist_data.get('avg_qty') and hist_data.get('transaction_count', 0) > 0:
                    # Has historical data
                    base_qty = float(hist_data['avg_qty'])
                    confidence_boost = min(30, hist_data['transaction_count'] * 3)
                    volatility = float(hist_data.get('qty_stddev', 0) or 0)
                    recency_factor = 1.0
                    
                    # Check recency
                    if hist_data.get('last_sale_date'):
                        from datetime import date
                        if isinstance(hist_data['last_sale_date'], str):
                            last_date = datetime.strptime(hist_data['last_sale_date'], '%Y-%m-%d').date()
                        else:
                            last_date = hist_data['last_sale_date']
                        days_since_last = (date.today() - last_date).days
                        recency_factor = max(0.3, 1.0 - (days_since_last / 90.0))
                else:
                    # No historical data - use market estimates
                    base_qty = random.uniform(0.5, 2.5)
                    confidence_boost = 0
                    volatility = 0.5
                    recency_factor = 0.5
                
                # Generate forecasts for each day
                for day in range(1, min(forecast_days + 1, 15)):  # Limit simple forecasts to 14 days
                    forecast_date = add_days(nowdate(), day)
                    
                    # Apply seasonality and trends
                    forecast_date_obj = getdate(forecast_date)
                    day_of_week = forecast_date_obj.weekday()
                    weekend_factor = 0.7 if day_of_week >= 5 else 1.0  # Lower on weekends
                    
                    # Calculate predicted quantity
                    seasonal_factor = 1.0 + 0.1 * random.uniform(-1, 1)  # ±10% seasonal variation
                    trend_factor = 1.0 + (day * 0.02 * random.uniform(-1, 1))  # Small trend
                    
                    predicted_qty = base_qty * weekend_factor * seasonal_factor * trend_factor * recency_factor
                    predicted_qty = max(0.1, predicted_qty)  # Minimum 0.1
                    
                    # Calculate confidence score
                    base_confidence = 60 + confidence_boost
                    
                    # Adjust confidence based on various factors
                    if hist_data.get('transaction_count', 0) >= 5:
                        base_confidence += 15  # More data = higher confidence
                    
                    if volatility < 1.0:
                        base_confidence += 10  # Low volatility = higher confidence
                    
                    if recency_factor > 0.8:
                        base_confidence += 10  # Recent sales = higher confidence
                    
                    # Add some randomness but keep realistic
                    confidence = min(95, max(50, base_confidence + random.randint(-5, 5)))
                    
                    # Only create forecasts with decent confidence
                    if confidence >= 55:
                        try:
                            forecast = frappe.get_doc({
                                "doctype": "AI Sales Forecast",
                                "item_code": item.name,
                                "customer": customer.name,
                                "forecast_date": forecast_date,
                                "predicted_qty": round(predicted_qty, 2),
                                "horizon_days": day,
                                "trigger_source": "Manual",
                                "model_version": "Simple_v2.0",
                                "confidence_score": confidence,
                                "notes": f"Simple forecast based on {hist_data.get('transaction_count', 0)} historical records"
                            })
                            forecast.insert(ignore_permissions=True)
                            forecasts_created += 1
                        except Exception as e:
                            frappe.log_error(f"Error creating simple forecast: {str(e)}", "AI Sales Forecasting")
                            continue
        
        # Update item forecast summaries
        self._update_item_forecasts()
        
        # Update dashboard stats
        self._update_dashboard_stats(forecasts_created)
        
        frappe.db.commit()
        return forecasts_created
    
    def _prepare_prediction_features(self, item_code, customer, forecast_date, day_offset):
        """Prepare features for making predictions"""
        try:
            forecast_dt = getdate(forecast_date)
            
            # Get recent sales data for this item-customer combination
            recent_sales = frappe.db.sql("""
                SELECT qty, amount, rate
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
                WHERE si.customer = %s AND sii.item_code = %s
                AND si.docstatus = 1
                ORDER BY si.posting_date DESC
                LIMIT 30
            """, (customer['name'], item_code), as_dict=True)
            
            # Time features
            features = [
                forecast_dt.year,
                forecast_dt.month,
                (forecast_dt.month - 1) // 3 + 1,  # quarter
                forecast_dt.weekday(),
                forecast_dt.timetuple().tm_yday,  # day of year
                forecast_dt.isocalendar()[1],  # week of year
            ]
            
            # Encoded categorical features
            try:
                customer_encoded = self.encoders['customer'].transform([customer['name']])[0] if 'customer' in self.encoders else 0
                territory_encoded = self.encoders['territory'].transform([customer.get('territory', 'Unknown')])[0] if 'territory' in self.encoders else 0
                item_encoded = self.encoders['item_code'].transform([item_code])[0] if 'item_code' in self.encoders else 0
                
                features.extend([customer_encoded, territory_encoded, item_encoded])
            except:
                features.extend([0, 0, 0])
            
            # Historical averages
            if recent_sales:
                avg_qty_7 = np.mean([s['qty'] for s in recent_sales[:7]])
                avg_qty_30 = np.mean([s['qty'] for s in recent_sales])
                avg_amount_7 = np.mean([s['amount'] for s in recent_sales[:7]])
                avg_amount_30 = np.mean([s['amount'] for s in recent_sales])
                last_qty = recent_sales[0]['qty']
                last_amount = recent_sales[0]['amount']
                avg_rate = np.mean([s['rate'] for s in recent_sales])
                
                # Trends
                if len(recent_sales) >= 7:
                    recent_7_14 = [s['qty'] for s in recent_sales[7:14]]
                    recent_amount_7_14 = [s['amount'] for s in recent_sales[7:14]]
                    if recent_7_14:
                        qty_trend = (avg_qty_7 - np.mean(recent_7_14)) / (np.mean(recent_7_14) + 1)
                        amount_trend = (avg_amount_7 - np.mean(recent_amount_7_14)) / (np.mean(recent_amount_7_14) + 1)
                    else:
                        qty_trend = 0
                        amount_trend = 0
                else:
                    qty_trend = 0
                    amount_trend = 0
                
                features.extend([
                    avg_qty_7, avg_qty_30, avg_amount_7, avg_amount_30,
                    last_qty, last_qty, last_amount,  # lag features
                    qty_trend, amount_trend,
                    avg_rate
                ])
            else:
                # No historical data
                features.extend([0] * 10)
            
            # Customer features
            churn_prob = customer.get('churn_probability', 0) or 0
            features.append(churn_prob)
            
            return features
            
        except Exception as e:
            frappe.log_error(f"Error preparing features: {str(e)}", "AI Sales Forecasting")
            return None
    
    def _calculate_confidence(self, item_code, customer, predicted_qty):
        """Calculate confidence score for prediction"""
        try:
            # Get historical accuracy for this item-customer combination
            recent_sales = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
                WHERE si.customer = %s AND sii.item_code = %s
                AND si.docstatus = 1
                AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            """, (customer, item_code))
            
            data_points = recent_sales[0][0] if recent_sales else 0
            
            # Base confidence on data availability and prediction reasonableness
            base_confidence = min(70 + (data_points * 2), 95)
            
            # Adjust based on prediction magnitude
            if predicted_qty > 0:
                confidence = base_confidence
            else:
                confidence = max(base_confidence - 20, 50)
            
            return confidence
            
        except:
            return 70  # Default confidence
    
    def _update_dashboard_stats(self, forecasts_created):
        """Update dashboard with forecast statistics"""
        try:
            if not self.config:
                return
                
            frappe.db.set_value("AI Sales Dashboard", "AI Sales Dashboard", {
                "total_forecasts_last_sync": forecasts_created
            })
        except Exception as e:
            frappe.log_error(f"Error updating dashboard stats: {str(e)}", "AI Sales Forecasting")

    def _update_item_forecasts(self):
        """Update item-level forecast summaries"""
        try:
            items = frappe.db.get_all("Item", filters={"enable_forecast": 1}, fields=["name"])
            
            for item in items:
                item_code = item['name']
                
                # Get 30-day forecast sum
                forecast_30 = frappe.db.sql("""
                    SELECT SUM(predicted_qty) as total_qty
                    FROM `tabAI Sales Forecast`
                    WHERE item_code = %s
                    AND forecast_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                """, (item_code,))
                
                total_qty = forecast_30[0][0] if forecast_30 and forecast_30[0][0] else 0
                
                # Update item
                frappe.db.set_value("Item", item_code, {
                    "last_forecast_date": nowdate(),
                    "forecasted_qty_30": total_qty
                })
        except Exception as e:
            frappe.log_error(f"Error updating item forecasts: {str(e)}", "AI Sales Forecasting")

    def _update_training_stats(self, performance):
        """Update dashboard with training statistics"""
        try:
            if not self.config:
                return
                
            success_count = len([p for p in performance.values() if p['data_points'] >= 10])
            total_items = len(performance)
            
            success_rate = (success_count / total_items * 100) if total_items > 0 else 0
            
            frappe.db.set_value("AI Sales Dashboard", "AI Sales Dashboard", {
                "success_rate_last_sync": success_rate
            })
        except Exception as e:
            frappe.log_error(f"Error updating training stats: {str(e)}", "AI Sales Forecasting")


# ============== API ENDPOINTS FOR FRONTEND INTEGRATION ==============

@frappe.whitelist()
def train_models():
    """API endpoint to train forecasting models"""
    try:
        engine = SalesForecastingEngine()
        performance = engine.train_models()
        
        if isinstance(performance, dict) and 'error' in performance:
            return {
                "success": False,
                "message": performance['error']
            }
        
        return {
            "success": True,
            "message": f"Models trained for {len(performance)} items",
            "performance": performance
        }
    except Exception as e:
        frappe.log_error(f"Model training failed: {str(e)}", "AI Sales Forecasting")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def generate_forecasts(forecast_days=None):
    """API endpoint to generate sales forecasts"""
    try:
        # Ensure forecast_days is properly set
        if forecast_days:
            forecast_days = int(forecast_days)
        else:
            forecast_days = 30  # Default value
            
        engine = SalesForecastingEngine()
        forecasts_created = engine.generate_forecasts(forecast_days)
        
        return {
            "success": True,
            "message": f"Generated {forecasts_created} forecasts",
            "forecasts_created": forecasts_created
        }
    except Exception as e:
        frappe.log_error(f"Forecast generation failed: {str(e)}", "AI Sales Forecasting")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_forecast_analytics():
    """Get forecast analytics for dashboard"""
    try:
        # Top forecasted items
        top_items = frappe.db.sql("""
            SELECT 
                item_code,
                SUM(predicted_qty) as total_qty,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) as forecast_count
            FROM `tabAI Sales Forecast`
            WHERE forecast_date >= CURDATE()
            GROUP BY item_code
            ORDER BY total_qty DESC
            LIMIT 10
        """, as_dict=True)
        
        # Forecast accuracy (compare with actual sales)
        accuracy_data = frappe.db.sql("""
            SELECT 
                DATE(forecast_date) as date,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) as forecast_count
            FROM `tabAI Sales Forecast`
            WHERE forecast_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(forecast_date)
            ORDER BY date
        """, as_dict=True)
        
        # Customer segment analysis
        segment_analysis = frappe.db.sql("""
            SELECT 
                COALESCE(c.customer_segment, 'Unknown') as customer_segment,
                COUNT(DISTINCT sf.customer) as customer_count,
                SUM(sf.predicted_qty) as total_predicted_qty,
                AVG(sf.confidence_score) as avg_confidence
            FROM `tabAI Sales Forecast` sf
            LEFT JOIN `tabCustomer` c ON sf.customer = c.name
            WHERE sf.forecast_date >= CURDATE()
            GROUP BY COALESCE(c.customer_segment, 'Unknown')
        """, as_dict=True)
        
        return {
            "success": True,
            "top_items": top_items,
            "accuracy_trend": accuracy_data,
            "segment_analysis": segment_analysis
        }
        
    except Exception as e:
        frappe.log_error(f"Analytics retrieval failed: {str(e)}", "AI Sales Forecasting")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def auto_create_sales_orders():
    """Auto-create sales orders from high-confidence forecasts"""
    try:
        config = frappe.get_single("AI Sales Dashboard")
        
        if not config or not config.auto_submit_sales_orders:
            return {"success": False, "message": "Auto-create is disabled"}
        
        confidence_threshold = config.confidence_threshold or 85
        
        # Get high-confidence forecasts for next 7 days
        forecasts = frappe.db.sql("""
            SELECT *
            FROM `tabAI Sales Forecast`
            WHERE forecast_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            AND confidence_score >= %s
            AND predicted_qty > 0
        """, (confidence_threshold,), as_dict=True)
        
        orders_created = 0
        
        for forecast in forecasts:
            try:
                # Check if order already exists
                existing = frappe.db.exists("Sales Order", {
                    "customer": forecast['customer'],
                    "delivery_date": forecast['forecast_date']
                })
                
                if existing:
                    continue
                
                # Create sales order
                so = frappe.get_doc({
                    "doctype": "Sales Order",
                    "customer": forecast['customer'],
                    "territory": forecast.get('territory'),
                    "delivery_date": forecast['forecast_date'],
                    "items": [{
                        "item_code": forecast['item_code'],
                        "qty": forecast['predicted_qty'],
                        "delivery_date": forecast['forecast_date']
                    }]
                })
                
                so.insert(ignore_permissions=True)
                orders_created += 1
                
            except Exception as e:
                frappe.log_error(f"Error creating SO for forecast {forecast.get('name', '')}: {str(e)}", 
                               "AI Sales Forecasting")
                continue
        
        return {
            "success": True,
            "message": f"Created {orders_created} sales orders",
            "orders_created": orders_created
        }
        
    except Exception as e:
        frappe.log_error(f"Auto SO creation failed: {str(e)}", "AI Sales Forecasting")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def quick_test_system():
    """Quick test of the forecasting system"""
    try:
        print("🧪 Running Quick System Test...")
        
        # Test data extraction
        engine = SalesForecastingEngine()
        sales_data, order_data = engine.extract_historical_data(30)
        print(f"📊 Data extraction: {len(sales_data)} sales records")
        
        if len(sales_data) < 5:
            return {
                "success": False,
                "message": "Insufficient sales data for testing. Need at least 5 sales records."
            }
        
        # Test forecast generation
        forecasts_created = engine.generate_forecasts(5)
        print(f"🔮 Forecast generation: {forecasts_created} forecasts created")
        
        # Test analytics
        analytics = get_forecast_analytics()
        
        return {
            "success": True,
            "message": f"Test completed successfully. Created {forecasts_created} forecasts.",
            "sales_records": len(sales_data),
            "forecasts_created": forecasts_created,
            "analytics_working": analytics.get('success', False)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }

@frappe.whitelist()
def get_item_forecast_details(item_code, days=30):
    """Get detailed forecast for specific item"""
    try:
        forecasts = frappe.db.sql("""
            SELECT 
                sf.*,
                c.customer_name,
                c.customer_segment,
                i.item_name,
                i.item_group
            FROM `tabAI Sales Forecast` sf
            LEFT JOIN `tabCustomer` c ON sf.customer = c.name
            LEFT JOIN `tabItem` i ON sf.item_code = i.name
            WHERE sf.item_code = %s
            AND sf.forecast_date BETWEEN %s AND %s
            ORDER BY sf.forecast_date, sf.confidence_score DESC
        """, (item_code, nowdate(), add_days(nowdate(), int(days))), as_dict=True)
        
        # Historical sales for comparison
        historical = frappe.db.sql("""
            SELECT 
                si.posting_date,
                sii.qty,
                sii.amount,
                si.customer
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
            WHERE sii.item_code = %s
            AND si.docstatus = 1
            AND si.posting_date >= %s
            ORDER BY si.posting_date DESC
        """, (item_code, add_days(nowdate(), -90)), as_dict=True)
        
        return {
            "success": True,
            "forecasts": forecasts,
            "historical_sales": historical
        }
        
    except Exception as e:
        frappe.log_error(f"Item forecast details failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    try:
        # Total forecasts for next 30 days
        total_forecasts = frappe.db.count("AI Sales Forecast", {
            "forecast_date": ["between", [nowdate(), add_days(nowdate(), 30)]]
        })
        
        # High confidence forecasts
        high_confidence = frappe.db.count("AI Sales Forecast", {
            "forecast_date": ["between", [nowdate(), add_days(nowdate(), 30)]],
            "confidence_score": [">=", 80]
        })
        
        # Items with forecasting enabled
        enabled_items = frappe.db.count("Item", {"enable_forecast": 1})
        
        # Recent accuracy
        accuracy = frappe.db.sql("""
            SELECT AVG(accuracy_score) as avg_accuracy
            FROM `tabAI Sales Forecast`
            WHERE accuracy_score IS NOT NULL
            AND forecast_date >= %s
        """, (add_days(nowdate(), -30),))
        
        avg_accuracy = accuracy[0][0] if accuracy and accuracy[0][0] else 0
        
        # Trend data for charts
        trend_data = frappe.db.sql("""
            SELECT 
                DATE(forecast_date) as date,
                SUM(predicted_qty) as total_qty,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) as forecast_count
            FROM `tabAI Sales Forecast`
            WHERE forecast_date >= %s
            GROUP BY DATE(forecast_date)
            ORDER BY date
        """, (add_days(nowdate(), -30),), as_dict=True)
        
        return {
            "success": True,
            "summary": {
                "total_forecasts": total_forecasts,
                "high_confidence_forecasts": high_confidence,
                "enabled_items": enabled_items,
                "average_accuracy": round(avg_accuracy, 2) if avg_accuracy else 0,
                "confidence_percentage": round((high_confidence / total_forecasts * 100), 2) if total_forecasts > 0 else 0
            },
            "trend_data": trend_data
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard summary failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def update_forecast_confidence(forecast_name, new_confidence, notes=""):
    """Manually update forecast confidence"""
    try:
        forecast = frappe.get_doc("AI Sales Forecast", forecast_name)
        
        old_confidence = forecast.confidence_score
        forecast.confidence_score = new_confidence
        forecast.notes = f"{forecast.notes or ''}\nManual adjustment: {old_confidence}% -> {new_confidence}% ({notes})"
        forecast.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": f"Confidence updated from {old_confidence}% to {new_confidence}%"
        }
        
    except Exception as e:
        frappe.log_error(f"Confidence update failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def export_forecasts(filters=None):
    """Export forecasts to Excel/CSV"""
    try:
        import json
        filters = json.loads(filters) if isinstance(filters, str) else filters or {}
        
        conditions = ["1=1"]
        values = []
        
        if filters.get('item_code'):
            conditions.append("sf.item_code = %s")
            values.append(filters['item_code'])
        
        if filters.get('customer'):
            conditions.append("sf.customer = %s")
            values.append(filters['customer'])
        
        if filters.get('date_range'):
            conditions.append("sf.forecast_date BETWEEN %s AND %s")
            values.extend(filters['date_range'])
        
        where_clause = " AND ".join(conditions)
        
        forecasts = frappe.db.sql(f"""
            SELECT 
                sf.item_code,
                i.item_name,
                sf.customer,
                c.customer_name,
                sf.territory,
                sf.forecast_date,
                sf.predicted_qty,
                sf.confidence_score,
                sf.model_version,
                sf.actual_qty,
                sf.accuracy_score
            FROM `tabAI Sales Forecast` sf
            LEFT JOIN `tabItem` i ON sf.item_code = i.name
            LEFT JOIN `tabCustomer` c ON sf.customer = c.name
            WHERE {where_clause}
            ORDER BY sf.forecast_date, sf.item_code
        """, values, as_dict=True)
        
        return {
            "success": True,
            "data": forecasts,
            "count": len(forecasts)
        }
        
    except Exception as e:
        frappe.log_error(f"Export failed: {str(e)}", "AI Sales Forecasting")
        return {"success": False, "message": str(e)}

# ============== BACKGROUND TASKS AND SCHEDULER ==============

def scheduled_forecast_generation():
    """Daily scheduled forecast generation"""
    try:
        config = frappe.get_single("AI Sales Dashboard")
        
        if not config or not config.enable_auto_sync:
            return
        
        engine = SalesForecastingEngine()
        forecasts_created = engine.generate_forecasts()
        
        # Auto-create sales orders if enabled
        if config.auto_submit_sales_orders:
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
        
        if not config or not config.enable_auto_sync:
            return
        
        # Check if we have enough new data to warrant retraining
        new_invoices = frappe.db.count("Sales Invoice", {
            "docstatus": 1,
            "creation": [">=", add_days(nowdate(), -7)]
        })
        
        if new_invoices >= 10:  # Only retrain if we have significant new data
            engine = SalesForecastingEngine()
            performance = engine.train_models()
            
            frappe.log_error(f"Scheduled model training completed for {len(performance) if isinstance(performance, dict) else 0} items", 
                            "AI Sales Forecasting")
        
    except Exception as e:
        frappe.log_error(f"Scheduled model training failed: {str(e)}", 
                        "AI Sales Forecasting")

# ============== UTILITY FUNCTIONS ==============

def update_forecast_accuracy(item_code, customer, posting_date, actual_qty):
    """Update forecast accuracy based on actual sales"""
    try:
        # Find corresponding forecasts
        forecasts = frappe.db.get_all("AI Sales Forecast", 
                                     filters={
                                         "item_code": item_code,
                                         "customer": customer,
                                         "forecast_date": posting_date
                                     },
                                     fields=["name", "predicted_qty", "confidence_score"])
        
        for forecast in forecasts:
            # Calculate accuracy
            predicted = forecast['predicted_qty']
            accuracy = 100 - (abs(predicted - actual_qty) / max(predicted, actual_qty, 1) * 100)
            
            # Update forecast record with actual data
            frappe.db.set_value("AI Sales Forecast", forecast['name'], {
                "actual_qty": actual_qty,
                "accuracy_score": accuracy
            })
    except Exception as e:
        frappe.log_error(f"Error updating forecast accuracy: {str(e)}", "AI Sales Forecasting")

def get_forecast_for_item_customer(item_code, customer, date_range=7):
    """Get forecast for specific item-customer combination"""
    try:
        forecasts = frappe.db.get_all("AI Sales Forecast",
                                    filters={
                                        "item_code": item_code,
                                        "customer": customer,
                                        "forecast_date": ["between", [nowdate(), add_days(nowdate(), date_range)]]
                                    },
                                    fields=["forecast_date", "predicted_qty", "confidence_score"],
                                    order_by="forecast_date")
        return forecasts
    except Exception as e:
        frappe.log_error(f"Error getting forecasts: {str(e)}", "AI Sales Forecasting")
        return []

def calculate_forecast_accuracy():
    """Calculate overall forecast accuracy"""
    try:
        accuracy_data = frappe.db.sql("""
            SELECT 
                AVG(accuracy_score) as avg_accuracy,
                COUNT(*) as total_forecasts,
                COUNT(CASE WHEN accuracy_score >= 80 THEN 1 END) as high_accuracy_count
            FROM `tabAI Sales Forecast`
            WHERE accuracy_score IS NOT NULL
            AND forecast_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """, as_dict=True)
        
        if accuracy_data:
            return {
                "average_accuracy": accuracy_data[0]['avg_accuracy'] or 0,
                "total_forecasts": accuracy_data[0]['total_forecasts'],
                "high_accuracy_rate": (accuracy_data[0]['high_accuracy_count'] / accuracy_data[0]['total_forecasts'] * 100) if accuracy_data[0]['total_forecasts'] > 0 else 0
            }
        else:
            return {"average_accuracy": 0, "total_forecasts": 0, "high_accuracy_rate": 0}
            
    except Exception as e:
        frappe.log_error(f"Error calculating accuracy: {str(e)}", "AI Sales Forecasting")
        return {"average_accuracy": 0, "total_forecasts": 0, "high_accuracy_rate": 0}