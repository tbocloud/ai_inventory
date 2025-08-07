# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class AIForecastAccuracy(Document):
    """AI Forecast Accuracy tracking and analysis"""
    
    def validate(self):
        """Validate accuracy data"""
        self.calculate_accuracy_metrics()
        self.analyze_forecast_performance()
        self.update_related_forecasts()
    
    def calculate_accuracy_metrics(self):
        """Calculate various accuracy metrics"""
        if not all([self.predicted_value, self.actual_value]):
            return
        
        predicted = float(self.predicted_value)
        actual = float(self.actual_value)
        
        # Calculate accuracy percentage
        if actual != 0:
            self.accuracy_percentage = (1 - abs(predicted - actual) / abs(actual)) * 100
        else:
            self.accuracy_percentage = 100 if predicted == 0 else 0
        
        # Ensure accuracy is not negative
        self.accuracy_percentage = max(0, self.accuracy_percentage)
        
        # Calculate variance
        self.variance = predicted - actual
        self.variance_percentage = (self.variance / actual * 100) if actual != 0 else 0
        
        # Calculate absolute percentage error
        self.absolute_percentage_error = abs(self.variance_percentage)
        
        # Set accuracy rating
        self.set_accuracy_rating()
    
    def set_accuracy_rating(self):
        """Set accuracy rating based on percentage"""
        if not hasattr(self, 'accuracy_percentage') or self.accuracy_percentage is None:
            self.accuracy_rating = "Unknown"
            return
        
        if self.accuracy_percentage >= 95:
            self.accuracy_rating = "Excellent"
        elif self.accuracy_percentage >= 85:
            self.accuracy_rating = "Good"
        elif self.accuracy_percentage >= 70:
            self.accuracy_rating = "Fair"
        elif self.accuracy_percentage >= 50:
            self.accuracy_rating = "Poor"
        else:
            self.accuracy_rating = "Very Poor"
    
    def analyze_forecast_performance(self):
        """Analyze forecast performance and trends"""
        try:
            # Get historical accuracy for same forecast type and company
            historical_accuracy = frappe.get_all("AI Forecast Accuracy",
                                                filters={
                                                    "company": self.company,
                                                    "forecast_type": self.forecast_type,
                                                    "evaluation_date": ["<", self.evaluation_date],
                                                    "name": ["!=", self.name]
                                                },
                                                fields=["accuracy_percentage"],
                                                order_by="evaluation_date desc",
                                                limit=10)
            
            if historical_accuracy:
                accuracies = [acc.accuracy_percentage for acc in historical_accuracy if acc.accuracy_percentage]
                
                if accuracies:
                    self.historical_average_accuracy = sum(accuracies) / len(accuracies)
                    
                    # Calculate trend
                    if len(accuracies) >= 3:
                        recent_avg = sum(accuracies[:3]) / 3
                        older_avg = sum(accuracies[3:6]) / min(3, len(accuracies[3:6])) if len(accuracies) > 3 else recent_avg
                        
                        if recent_avg > older_avg + 5:
                            self.accuracy_trend = "Improving"
                        elif recent_avg < older_avg - 5:
                            self.accuracy_trend = "Declining"
                        else:
                            self.accuracy_trend = "Stable"
                    else:
                        self.accuracy_trend = "Stable"  # Default for insufficient data
                else:
                    self.historical_average_accuracy = 0
                    self.accuracy_trend = "Stable"  # Default for no historical data
            else:
                self.historical_average_accuracy = 0
                self.accuracy_trend = "Stable"  # Default for first evaluation
                
        except Exception as e:
            frappe.log_error(f"Error analyzing forecast performance: {str(e)}")
            self.accuracy_trend = "Stable"  # Default to Stable instead of Analysis Error
    
    def update_related_forecasts(self):
        """Update accuracy information in related forecasts"""
        if not self.forecast_reference:
            return
        
        try:
            # Update AI Financial Forecast
            financial_forecasts = frappe.get_all("AI Financial Forecast",
                                                filters={"name": self.forecast_reference},
                                                limit=1)
            
            if financial_forecasts:
                forecast_doc = frappe.get_doc("AI Financial Forecast", self.forecast_reference)
                forecast_doc.forecast_accuracy = self.accuracy_rating
                forecast_doc.accuracy_percentage = self.accuracy_percentage
                forecast_doc.last_accuracy_check = frappe.utils.now()
                forecast_doc.save(ignore_permissions=True)
            
            # Update specific forecast types
            self.update_specific_forecast_accuracy()
            
        except Exception as e:
            frappe.log_error(f"Error updating related forecasts: {str(e)}")
    
    def update_specific_forecast_accuracy(self):
        """Update accuracy in specific forecast type documents"""
        try:
            forecast_type_mapping = {
                "Cash Flow": "AI Cashflow Forecast",
                "Revenue": "AI Revenue Forecast", 
                "Expense": "AI Expense Forecast"
            }
            
            target_doctype = forecast_type_mapping.get(self.forecast_type)
            if not target_doctype:
                return
            
            # Find related forecast document
            related_forecasts = frappe.get_all(target_doctype,
                                             filters={
                                                 "company": self.company,
                                                 "forecast_date": self.forecast_date
                                             },
                                             limit=1)
            
            if related_forecasts:
                forecast_doc = frappe.get_doc(target_doctype, related_forecasts[0].name)
                
                # Update accuracy fields if they exist
                if hasattr(forecast_doc, 'historical_accuracy'):
                    forecast_doc.historical_accuracy = self.accuracy_percentage
                elif hasattr(forecast_doc, 'accuracy_score'):
                    forecast_doc.accuracy_score = self.accuracy_percentage
                elif hasattr(forecast_doc, 'forecast_accuracy'):
                    forecast_doc.forecast_accuracy = self.accuracy_rating
                
                # Update accuracy metadata
                if hasattr(forecast_doc, 'last_accuracy_update'):
                    forecast_doc.last_accuracy_update = frappe.utils.now()
                
                forecast_doc.save(ignore_permissions=True)
                
        except Exception as e:
            frappe.log_error(f"Error updating specific forecast accuracy: {str(e)}")
    
    def before_save(self):
        """Actions before saving"""
        self.set_performance_indicators()
        self.calculate_model_performance()
    
    def set_performance_indicators(self):
        """Set performance indicator flags"""
        if not self.accuracy_percentage:
            return
        
        # Set performance flags based on accuracy
        if hasattr(self, 'is_high_accuracy'):
            self.is_high_accuracy = self.accuracy_percentage >= 85
        
        if hasattr(self, 'needs_model_review'):
            self.needs_model_review = self.accuracy_percentage < 70
        
        if hasattr(self, 'is_reliable'):
            self.is_reliable = self.accuracy_percentage >= 75
    
    def calculate_model_performance(self):
        """Calculate model-specific performance metrics"""
        try:
            if not self.prediction_model:
                return
            
            # Get accuracy for same model across different forecasts
            model_accuracy = frappe.get_all("AI Forecast Accuracy",
                                          filters={
                                              "prediction_model": self.prediction_model,
                                              "evaluation_date": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -90)],
                                              "name": ["!=", self.name]
                                          },
                                          fields=["accuracy_percentage"],
                                          limit=20)
            
            if model_accuracy:
                accuracies = [acc.accuracy_percentage for acc in model_accuracy if acc.accuracy_percentage]
                
                if accuracies:
                    model_avg_accuracy = sum(accuracies) / len(accuracies)
                    
                    # Set model performance fields if they exist
                    if hasattr(self, 'model_average_accuracy'):
                        self.model_average_accuracy = model_avg_accuracy
                    
                    if hasattr(self, 'model_performance_rating'):
                        if model_avg_accuracy >= 85:
                            self.model_performance_rating = "Excellent"
                        elif model_avg_accuracy >= 75:
                            self.model_performance_rating = "Good"
                        elif model_avg_accuracy >= 65:
                            self.model_performance_rating = "Fair"
                        else:
                            self.model_performance_rating = "Poor"
                            
        except Exception as e:
            frappe.log_error(f"Error calculating model performance: {str(e)}")
    
    def after_insert(self):
        """Actions after inserting new accuracy record"""
        self.create_accuracy_alert_if_needed()
        self.update_accuracy_dashboard()
    
    def create_accuracy_alert_if_needed(self):
        """Create alert if accuracy is below threshold"""
        try:
            if not self.accuracy_percentage:
                return
            
            # Create alert for very low accuracy
            if self.accuracy_percentage < 50:
                alert_message = f"""
                <h3>Low Forecast Accuracy Alert</h3>
                <p><strong>Forecast Type:</strong> {self.forecast_type}</p>
                <p><strong>Company:</strong> {self.company}</p>
                <p><strong>Accuracy:</strong> {self.accuracy_percentage:.1f}%</p>
                <p><strong>Rating:</strong> {self.accuracy_rating}</p>
                <p>This forecast accuracy is below acceptable thresholds. Please review the prediction model and input data.</p>
                """
                
                # Get recipients
                recipients = self.get_alert_recipients()
                
                if recipients:
                    frappe.sendmail(
                        recipients=recipients,
                        subject=f"Low Forecast Accuracy Alert - {self.forecast_type}",
                        message=alert_message,
                        reference_doctype=self.doctype,
                        reference_name=self.name
                    )
                    
        except Exception as e:
            frappe.log_error(f"Error creating accuracy alert: {str(e)}")
    
    def get_alert_recipients(self):
        """Get list of users to notify for accuracy alerts"""
        try:
            # Get users with AI Inventory Manager role
            managers = frappe.get_all("Has Role",
                                    filters={"role": "AI Inventory Manager"},
                                    fields=["parent"])
            
            return [m.parent for m in managers]
            
        except:
            return []
    
    def update_accuracy_dashboard(self):
        """Update accuracy dashboard metrics"""
        try:
            # This would update a dashboard cache or summary table
            # For now, just log the update
            frappe.log_error(f"Accuracy dashboard updated for {self.forecast_type} - {self.accuracy_percentage}%", "Accuracy Update")
            
        except Exception as e:
            frappe.log_error(f"Error updating accuracy dashboard: {str(e)}")

@frappe.whitelist()
def calculate_forecast_accuracy(original_forecast_id, actual_value, evaluation_date=None):
    """Calculate accuracy for a specific forecast"""
    try:
        # Get the original forecast
        forecast_doc = frappe.get_doc("AI Financial Forecast", original_forecast_id)
        
        if not evaluation_date:
            evaluation_date = frappe.utils.nowdate()
        
        # Check if accuracy record already exists
        existing = frappe.get_all("AI Forecast Accuracy",
                                filters={
                                    "forecast_reference": original_forecast_id,
                                    "evaluation_date": evaluation_date
                                },
                                limit=1)
        
        if existing:
            return {"success": False, "error": "Accuracy record already exists for this forecast and date"}
        
        # Create accuracy record
        accuracy_doc = frappe.get_doc({
            "doctype": "AI Forecast Accuracy",
            "forecast_reference": original_forecast_id,
            "company": forecast_doc.company,
            "forecast_type": forecast_doc.forecast_type,
            "forecast_date": forecast_doc.forecast_date,
            "evaluation_date": evaluation_date,
            "predicted_value": forecast_doc.predicted_amount,
            "actual_value": actual_value,
            "prediction_model": forecast_doc.prediction_model
        })
        
        accuracy_doc.insert()
        
        return {
            "success": True,
            "accuracy_id": accuracy_doc.name,
            "accuracy_percentage": accuracy_doc.accuracy_percentage,
            "accuracy_rating": accuracy_doc.accuracy_rating
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_accuracy_summary(company=None, forecast_type=None, days=30):
    """Get accuracy summary for dashboard"""
    try:
        filters = {}
        if company:
            filters["company"] = company
        if forecast_type:
            filters["forecast_type"] = forecast_type
        
        # Get recent accuracy records
        from_date = frappe.utils.add_days(frappe.utils.nowdate(), -int(days))
        filters["evaluation_date"] = [">=", from_date]
        
        accuracy_records = frappe.get_all("AI Forecast Accuracy",
                                        filters=filters,
                                        fields=["accuracy_percentage", "forecast_type", "accuracy_rating"],
                                        order_by="evaluation_date desc")
        
        if not accuracy_records:
            return {"message": "No accuracy records found"}
        
        # Calculate summary statistics
        accuracies = [r.accuracy_percentage for r in accuracy_records if r.accuracy_percentage]
        
        summary = {
            "total_evaluations": len(accuracy_records),
            "average_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
            "highest_accuracy": max(accuracies) if accuracies else 0,
            "lowest_accuracy": min(accuracies) if accuracies else 0,
            "by_type": {},
            "by_rating": {}
        }
        
        # Group by forecast type
        for record in accuracy_records:
            ftype = record.forecast_type
            if ftype not in summary["by_type"]:
                summary["by_type"][ftype] = {"count": 0, "avg_accuracy": 0, "total_accuracy": 0}
            
            summary["by_type"][ftype]["count"] += 1
            summary["by_type"][ftype]["total_accuracy"] += record.accuracy_percentage or 0
        
        # Calculate averages
        for ftype in summary["by_type"]:
            count = summary["by_type"][ftype]["count"]
            summary["by_type"][ftype]["avg_accuracy"] = summary["by_type"][ftype]["total_accuracy"] / count
        
        # Group by rating
        for record in accuracy_records:
            rating = record.accuracy_rating or "Unknown"
            summary["by_rating"][rating] = summary["by_rating"].get(rating, 0) + 1
        
        return summary
        
    except Exception as e:
        return {"error": str(e)}
