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
        # Proceed even when values are 0; only skip if either is None
        if self.predicted_value is None or self.actual_value is None:
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
                                                    "measurement_date": ["<", self.measurement_date],
                                                    "name": ["!=", self.name]
                                                },
                                                fields=["accuracy_percentage"],
                                                order_by="measurement_date desc",
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
                self.accuracy_trend = "Stable"  # Default for no historical data
        except Exception as e:
            frappe.log_error(f"Error analyzing forecast performance: {str(e)}")
            self.accuracy_trend = "Stable"

    def update_related_forecasts(self):
        """Optionally push accuracy rating/percentage back to the referenced forecast.

        This is a no-op if no forecast_reference is present. When present, we add a comment
        or update a standard JSON field if available.
        """
        try:
            if not getattr(self, "forecast_reference", None):
                return
            # Leverage the module-level updater for consistency
            update_source_forecast(self.name, self.forecast_reference)
        except Exception as e:
            frappe.log_error(f"update_related_forecasts error: {str(e)}")
    
@frappe.whitelist()
def calculate_metrics(predicted, actual):
        """Calculate accuracy metrics for given values"""
        try:
            predicted = float(predicted)
            actual = float(actual)
            
            # Calculate accuracy percentage
            if actual != 0:
                accuracy_percentage = (1 - abs(predicted - actual) / abs(actual)) * 100
            else:
                accuracy_percentage = 100 if predicted == 0 else 0
            
            # Ensure accuracy is not negative
            accuracy_percentage = max(0, accuracy_percentage)
            
            # Calculate variance
            variance = predicted - actual
            variance_percentage = (variance / actual * 100) if actual != 0 else 0
            
            # Calculate absolute percentage error
            absolute_percentage_error = abs(variance_percentage)
            
            # Set accuracy rating
            if accuracy_percentage >= 90:
                accuracy_rating = "Excellent"
            elif accuracy_percentage >= 80:
                accuracy_rating = "Good"
            elif accuracy_percentage >= 70:
                accuracy_rating = "Fair"
            elif accuracy_percentage >= 60:
                accuracy_rating = "Average"
            else:
                accuracy_rating = "Poor"
            
            return {
                'status': 'success',
                'metrics': {
                    'accuracy_percentage': accuracy_percentage,
                    'variance': variance,
                    'variance_percentage': variance_percentage,
                    'absolute_percentage_error': absolute_percentage_error,
                    'accuracy_rating': accuracy_rating
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error calculating metrics: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
@frappe.whitelist()
def recalculate_accuracy(accuracy_name):
        """Recalculate accuracy for a specific record"""
        try:
            doc = frappe.get_doc("AI Forecast Accuracy", accuracy_name)
            doc.calculate_accuracy_metrics()
            doc.save()
            
            return {
                'status': 'success',
                'accuracy_percentage': doc.accuracy_percentage,
                'accuracy_rating': doc.accuracy_rating
            }
            
        except Exception as e:
            frappe.log_error(f"Error recalculating accuracy: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
@frappe.whitelist()
def generate_accuracy_report(forecast_type, company, from_date, to_date):
    """Generate comprehensive accuracy report"""
    try:
        # Get accuracy records for the period
        accuracy_records = frappe.get_all(
            'AI Forecast Accuracy',
            filters={
                'forecast_type': forecast_type,
                'company': company,
                'measurement_date': ['between', [from_date, to_date]]
            },
            fields=['accuracy_percentage', 'measurement_date', 'accuracy_rating'],
            order_by='measurement_date desc'
        )

        if not accuracy_records:
            return {
                'status': 'error',
                'message': 'No accuracy records found for the specified period'
            }

        # Calculate statistics
        accuracies = [r.accuracy_percentage for r in accuracy_records if r.accuracy_percentage is not None]
        total_forecasts = len(accuracies)
        average_accuracy = (sum(accuracies) / total_forecasts) if total_forecasts else 0
        best_accuracy = max(accuracies) if accuracies else 0
        worst_accuracy = min(accuracies) if accuracies else 0

        # Count performance categories
        excellent_count = len([a for a in accuracies if a >= 90])
        good_count = len([a for a in accuracies if 80 <= a < 90])
        fair_count = len([a for a in accuracies if 70 <= a < 80])
        poor_count = len([a for a in accuracies if a < 70])

        # Trend analysis
        if len(accuracy_records) >= 3 and len(accuracies) >= 3:
            recent_avg = sum(accuracies[:3]) / 3
            older_avg = sum(accuracies[-3:]) / 3
            if recent_avg > older_avg + 5:
                trend_analysis = "Performance is improving over time"
            elif recent_avg < older_avg - 5:
                trend_analysis = "Performance is declining, attention needed"
            else:
                trend_analysis = "Performance is stable"
        else:
            trend_analysis = "Insufficient data for trend analysis"

        return {
            'status': 'success',
            'report': {
                'total_forecasts': total_forecasts,
                'average_accuracy': average_accuracy,
                'best_accuracy': best_accuracy,
                'worst_accuracy': worst_accuracy,
                'excellent_count': excellent_count,
                'good_count': good_count,
                'fair_count': fair_count,
                'poor_count': poor_count,
                'trend_analysis': trend_analysis
            }
        }

    except Exception as e:
        frappe.log_error(f"Error generating accuracy report: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    
@frappe.whitelist()
def compare_forecasts(company, current_forecast=None):
    """Compare forecast performance across different types over the recent period"""
    try:
        forecast_types = ['Cash Flow', 'Revenue', 'Expense', 'Financial']
        comparison_data = []
        cutoff = frappe.utils.add_days(frappe.utils.nowdate(), -90)

        for forecast_type in forecast_types:
            # Get recent accuracy records
            records = frappe.get_all(
                'AI Forecast Accuracy',
                filters={
                    'forecast_type': forecast_type,
                    'company': company,
                    'measurement_date': ['>=', cutoff]
                },
                fields=['accuracy_percentage', 'measurement_date'],
                order_by='measurement_date desc',
                limit=50
            )

            if records:
                accuracies = [r.accuracy_percentage for r in records if r.accuracy_percentage is not None]
                if accuracies:
                    avg_accuracy = sum(accuracies) / len(accuracies)
                    best_accuracy = max(accuracies)

                    # Consistency score (lower std dev -> higher score)
                    mean_acc = avg_accuracy
                    variance = sum([(x - mean_acc) ** 2 for x in accuracies]) / len(accuracies)
                    std_dev = variance ** 0.5
                    consistency_score = max(0, 100 - std_dev)

                    # Determine trend using recent vs older subset
                    if len(accuracies) >= 6:
                        recent_avg = sum(accuracies[:3]) / 3
                        older_avg = sum(accuracies[-3:]) / 3
                        if recent_avg > older_avg + 3:
                            trend = "improving"
                        elif recent_avg < older_avg - 3:
                            trend = "declining"
                        else:
                            trend = "stable"
                    else:
                        trend = "insufficient data"

                    comparison_data.append({
                        'forecast_type': forecast_type,
                        'avg_accuracy': avg_accuracy,
                        'best_accuracy': best_accuracy,
                        'consistency_score': consistency_score,
                        'trend': trend,
                        'total_records': len(accuracies)
                    })
                else:
                    comparison_data.append({
                        'forecast_type': forecast_type,
                        'avg_accuracy': 0,
                        'best_accuracy': 0,
                        'consistency_score': 0,
                        'trend': 'no data',
                        'total_records': 0
                    })
            else:
                comparison_data.append({
                    'forecast_type': forecast_type,
                    'avg_accuracy': 0,
                    'best_accuracy': 0,
                    'consistency_score': 0,
                    'trend': 'no data',
                    'total_records': 0
                })

        return {
            'status': 'success',
            'comparison': comparison_data
        }
    except Exception as e:
        frappe.log_error(f"Error comparing forecasts: {str(e)}")
        return {'status': 'error', 'message': str(e)}
@frappe.whitelist()
def update_source_forecast(accuracy_name: str, forecast_reference: str = None):
    """Write back key accuracy fields to the source forecast, if supported.

    Supports AI Financial Forecast (via name), AI Cashflow Forecast, AI Revenue Forecast.
    """
    try:
        acc = frappe.get_doc("AI Forecast Accuracy", accuracy_name)
        source = forecast_reference or acc.forecast_reference
        if not source:
            return {"status": "error", "message": "No forecast reference provided"}

        # Try to resolve by name across supported doctypes
        supported = [
            ("AI Financial Forecast", "AI Financial Forecast"),
            ("AI Cashflow Forecast", "AI Cashflow Forecast"),
            ("AI Revenue Forecast", "AI Revenue Forecast"),
        ]
        target_doc = None
        for doctype, _ in supported:
            try:
                target_doc = frappe.get_doc(doctype, source)
                break
            except Exception:
                continue

        if not target_doc:
            return {"status": "error", "message": f"Could not resolve source forecast {source}"}

        # Write back a concise snapshot into target's forecast_details or a note field
        snapshot = {
            "accuracy_percentage": acc.accuracy_percentage,
            "variance": acc.variance,
            "variance_percentage": acc.variance_percentage,
            "absolute_percentage_error": acc.absolute_percentage_error,
            "accuracy_rating": acc.accuracy_rating,
            "updated_from_accuracy": acc.name,
        }

        if hasattr(target_doc, "forecast_details"):
            try:
                details = json.loads(target_doc.forecast_details) if target_doc.forecast_details else {}
            except Exception:
                details = {}
            details["accuracy_snapshot"] = snapshot
            target_doc.forecast_details = json.dumps(details)
        else:
            # Fallback: attach as a comment
            target_doc.add_comment("Info", f"Accuracy Update: {json.dumps(snapshot)}")

        target_doc.save(ignore_permissions=True)
        return {"status": "success", "message": "Source forecast updated"}
    except Exception as e:
        frappe.log_error(f"update_source_forecast error: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    def update_specific_forecast_accuracy(self):
        """Update accuracy in specific forecast type documents (disabled).

        Left intentionally minimal; we now push back via update_source_forecast() which
        writes a snapshot into the source forecast's details or as a comment.
        """
        try:
            return
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
            if not getattr(self, 'model_used', None):
                return
            
            # Get accuracy for same model across different forecasts
            model_accuracy = frappe.get_all("AI Forecast Accuracy",
                                          filters={
                                              "model_used": self.model_used,
                                              "measurement_date": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -90)],
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
            
            # Convert to email addresses and validate
            valid_emails = []
            for m in managers:
                user = m.parent
                email = None
                if isinstance(user, str) and '@' in user:
                    email = user
                else:
                    email = frappe.db.get_value("User", user, "email")
                if email and frappe.utils.validate_email_address(email, throw=False):
                    valid_emails.append(email)
            return list(set(valid_emails))
            
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
                                    "measurement_date": evaluation_date
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
            "measurement_date": evaluation_date,
            "predicted_value": forecast_doc.predicted_amount,
            "actual_value": actual_value,
            "model_used": getattr(forecast_doc, 'prediction_model', None)
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
        filters["measurement_date"] = [">=", from_date]

        accuracy_records = frappe.get_all(
            "AI Forecast Accuracy",
            filters=filters,
            fields=["accuracy_percentage", "forecast_type", "accuracy_rating"],
            order_by="measurement_date desc",
        )

        if not accuracy_records:
            return {"message": "No accuracy records found"}

        # Calculate summary statistics
        accuracies = [r.accuracy_percentage for r in accuracy_records if r.accuracy_percentage]

        summary = {
            "total_evaluations": len(accuracy_records),
            "average_accuracy": (sum(accuracies) / len(accuracies)) if accuracies else 0,
            "highest_accuracy": max(accuracies) if accuracies else 0,
            "lowest_accuracy": min(accuracies) if accuracies else 0,
            "by_type": {},
            "by_rating": {},
        }

        # Group by forecast type
        for record in accuracy_records:
            ftype = record.forecast_type
            if ftype not in summary["by_type"]:
                summary["by_type"][ftype] = {"count": 0, "avg_accuracy": 0, "total_accuracy": 0}
            summary["by_type"][ftype]["count"] += 1
            summary["by_type"][ftype]["total_accuracy"] += record.accuracy_percentage or 0

        # Calculate averages per type
        for ftype in summary["by_type"]:
            count = summary["by_type"][ftype]["count"]
            total = summary["by_type"][ftype]["total_accuracy"]
            summary["by_type"][ftype]["avg_accuracy"] = (total / count) if count else 0

        # Group by rating
        for record in accuracy_records:
            rating = record.accuracy_rating or "Unknown"
            summary["by_rating"][rating] = summary["by_rating"].get(rating, 0) + 1

        return summary

    except Exception as e:
        return {"error": str(e)}
