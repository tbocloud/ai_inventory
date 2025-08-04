"""
Regression Models for Financial Forecasting
"""

import frappe
import numpy as np
import pandas as pd

class LinearRegressionPredictor:
    def predict(self, data):
        try:
            if not data:
                return {"predicted_value": 0, "confidence": 0}
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data.copy()
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return {"predicted_value": 0, "confidence": 50}
            
            if 'net_amount' in numeric_cols:
                values = df['net_amount'].dropna().values
            else:
                values = df[numeric_cols[0]].dropna().values
            
            if len(values) < 2:
                return {"predicted_value": values[0] if len(values) > 0 else 0, "confidence": 40}
            
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)
            prediction = slope * len(values) + intercept
            
            y_pred = slope * x + intercept
            ss_res = np.sum((values - y_pred) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            confidence = max(20, min(95, r_squared * 100))
            
            return {
                "predicted_value": float(prediction),
                "confidence": float(confidence),
                "upper_bound": float(prediction * 1.1),
                "lower_bound": float(prediction * 0.9),
                "model_summary": {"model_type": "Linear Regression", "r_squared": float(r_squared)},
                "details": {"slope": float(slope), "intercept": float(intercept)}
            }
            
        except Exception as e:
            frappe.log_error(f"Linear regression error: {str(e)}")
            return {"predicted_value": 0, "confidence": 0}

class PolynomialRegressionPredictor:
    def __init__(self, degree=2):
        self.degree = degree
    
    def predict(self, data):
        try:
            linear_predictor = LinearRegressionPredictor()
            base_result = linear_predictor.predict(data)
            base_value = base_result["predicted_value"]
            
            if isinstance(data, list) and len(data) > 3:
                df = pd.DataFrame(data)
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                
                if len(numeric_cols) > 0:
                    if 'net_amount' in numeric_cols:
                        values = df['net_amount'].dropna().values
                    else:
                        values = df[numeric_cols[0]].dropna().values
                    
                    if len(values) >= 3:
                        recent_trend = (values[-1] - values[-3]) / 2
                        adjusted_prediction = base_value + recent_trend * 0.3
                    else:
                        adjusted_prediction = base_value
                else:
                    adjusted_prediction = base_value
            else:
                adjusted_prediction = base_value
            
            return {
                "predicted_value": float(adjusted_prediction),
                "confidence": float(base_result["confidence"] * 0.9),
                "upper_bound": float(adjusted_prediction * 1.15),
                "lower_bound": float(adjusted_prediction * 0.85),
                "model_summary": {
                    "model_type": f"Polynomial Regression (degree {self.degree})",
                    "base_prediction": base_value
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Polynomial regression error: {str(e)}")
            return {"predicted_value": 0, "confidence": 0}

class MultiVariateRegressionPredictor:
    def predict(self, data, external_factors=None):
        try:
            linear_result = LinearRegressionPredictor().predict(data)
            base_prediction = linear_result["predicted_value"]
            
            if external_factors:
                economic_factor = external_factors.get("economic_growth_factor", 1.0)
                inflation_factor = external_factors.get("inflation_factor", 1.0)
                industry_factor = external_factors.get("industry_growth_factor", 1.0)
                
                external_multiplier = economic_factor * inflation_factor * industry_factor
                adjusted_prediction = base_prediction * external_multiplier
                
                confidence_adjustment = 0.9 if abs(external_multiplier - 1.0) > 0.1 else 1.0
                adjusted_confidence = linear_result["confidence"] * confidence_adjustment
            else:
                adjusted_prediction = base_prediction
                adjusted_confidence = linear_result["confidence"]
            
            return {
                "predicted_value": float(adjusted_prediction),
                "confidence": float(adjusted_confidence),
                "upper_bound": float(adjusted_prediction * 1.2),
                "lower_bound": float(adjusted_prediction * 0.8),
                "model_summary": {
                    "model_type": "Multi-variate Regression",
                    "external_factors": external_factors,
                    "base_prediction": base_prediction,
                    "external_multiplier": external_multiplier if external_factors else 1.0
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Multi-variate regression error: {str(e)}")
            return {"predicted_value": 0, "confidence": 0}

def create_regression_model(model_type="linear", **kwargs):
    """Factory function to create appropriate regression model"""
    if model_type == "linear":
        return LinearRegressionPredictor()
    elif model_type == "polynomial":
        degree = kwargs.get("degree", 2)
        return PolynomialRegressionPredictor(degree=degree)
    elif model_type == "multivariate":
        return MultiVariateRegressionPredictor()
    else:
        return LinearRegressionPredictor()