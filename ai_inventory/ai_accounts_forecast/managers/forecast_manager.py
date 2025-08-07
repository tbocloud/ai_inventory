"""
Forecast Manager - Complete system management utilities
Enhanced management system for AI Financial Forecasting
"""

import frappe
from frappe.model.document import Document
from collections import defaultdict
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

class ForecastManager:
    """Complete forecast management system with enhanced capabilities"""
    
    def __init__(self, company: str):
        self.company = company
        
    def create_comprehensive_forecasts(self, accounts: List[str], forecast_types: List[str] = None) -> Dict:
        """Create comprehensive forecasts for multiple accounts"""
        
        if forecast_types is None:
            forecast_types = ["Cash Flow", "Revenue", "Expense", "Balance Sheet", "P&L"]
        
        results = {
            'created': [],
            'failed': [],
            'summary': {},
            'performance_metrics': {}
        }
        
        total_attempts = len(accounts) * len(forecast_types)
        processed = 0
        
        for account in accounts:
            account_results = {'account': account, 'forecasts': []}
            
            for forecast_type in forecast_types:
                try:
                    from ai_inventory.ai_accounts_forecast.models.account_forecast import create_financial_forecast
                    
                    # Create forecast
                    result = create_financial_forecast(
                        company=self.company, 
                        account=account, 
                        forecast_type=forecast_type,
                        forecast_period_days=90,  # Standard 3-month forecast
                        confidence_threshold=70.0
                    )
                    
                    account_results['forecasts'].append({
                        'forecast_type': forecast_type,
                        'forecast_id': result.get('forecast_id'),
                        'confidence_score': result.get('confidence_score'),
                        'status': 'success'
                    })
                    
                    results['created'].append(result)
                    processed += 1
                    
                except Exception as e:
                    error_info = {
                        'account': account,
                        'forecast_type': forecast_type,
                        'error': str(e)
                    }
                    
                    account_results['forecasts'].append({
                        'forecast_type': forecast_type,
                        'status': 'failed',
                        'error': str(e)
                    })
                    
                    results['failed'].append(error_info)
                    frappe.log_error(f"Forecast creation failed: {str(e)}", "AI Forecast Manager")
                    processed += 1
                
                # Update progress
                if processed % 5 == 0:  # Log progress every 5 forecasts
                    frappe.publish_realtime(
                        "forecast_progress",
                        {"progress": (processed / total_attempts) * 100, "message": f"Processing {account}..."},
                        user=frappe.session.user
                    )
        
        # Calculate summary metrics
        results['summary'] = {
            'total_created': len(results['created']),
            'total_failed': len(results['failed']),
            'success_rate': (len(results['created']) / max(total_attempts, 1)) * 100,
            'accounts_processed': len(accounts),
            'forecast_types_used': len(forecast_types),
            'processing_time': datetime.now().isoformat()
        }
        
        # Calculate performance metrics
        results['performance_metrics'] = self.calculate_batch_performance_metrics(results['created'])
        
        return results
    
    def get_system_dashboard(self) -> Dict:
        """Generate comprehensive system dashboard with enhanced metrics"""
        
        forecasts = frappe.get_all('AI Financial Forecast',
                                  filters={'company': self.company},
                                  fields=['name', 'account', 'forecast_type', 'confidence_score', 
                                         'predicted_amount', 'creation', 'risk_category', 
                                         'volatility_score', 'trend_direction'])
        
        if not forecasts:
            return {
                'message': 'No forecasts found for this company',
                'company': self.company,
                'status': 'empty'
            }
        
        dashboard = {
            'summary': {
                'total_forecasts': len(forecasts),
                'avg_confidence': sum(f.confidence_score for f in forecasts) / len(forecasts),
                'total_predicted_value': sum(f.predicted_amount for f in forecasts if f.predicted_amount),
                'company': self.company,
                'last_updated': datetime.now().isoformat()
            },
            'by_type': {},
            'by_account': {},
            'by_risk': {},
            'by_trend': {},
            'performance_metrics': {},
            'recent_activity': self.get_recent_activity()
        }
        
        # Group by forecast type
        by_type = defaultdict(list)
        for f in forecasts:
            by_type[f.forecast_type].append(f)
        
        for ftype, type_forecasts in by_type.items():
            avg_confidence = sum(tf.confidence_score for tf in type_forecasts) / len(type_forecasts)
            total_predicted = sum(tf.predicted_amount for tf in type_forecasts if tf.predicted_amount)
            
            dashboard['by_type'][ftype] = {
                'count': len(type_forecasts),
                'avg_confidence': round(avg_confidence, 1),
                'total_predicted': total_predicted,
                'confidence_grade': self.get_confidence_grade(avg_confidence)
            }
        
        # Group by account
        by_account = defaultdict(list)
        for f in forecasts:
            by_account[f.account].append(f)
        
        for account, acc_forecasts in by_account.items():
            avg_confidence = sum(af.confidence_score for af in acc_forecasts) / len(acc_forecasts)
            
            dashboard['by_account'][account] = {
                'count': len(acc_forecasts),
                'types': len(set(af.forecast_type for af in acc_forecasts)),
                'avg_confidence': round(avg_confidence, 1),
                'total_predicted': sum(af.predicted_amount for af in acc_forecasts if af.predicted_amount)
            }
        
        # Group by risk category
        by_risk = defaultdict(int)
        for f in forecasts:
            risk = f.risk_category or 'Unknown'
            by_risk[risk] += 1
        
        dashboard['by_risk'] = dict(by_risk)
        
        # Group by trend direction
        by_trend = defaultdict(int)
        for f in forecasts:
            trend = f.trend_direction or 'Stable'
            by_trend[trend] += 1
        
        dashboard['by_trend'] = dict(by_trend)
        
        # Calculate performance metrics
        dashboard['performance_metrics'] = self.calculate_performance_metrics(forecasts)
        
        return dashboard
    
    def validate_system_health(self) -> Dict:
        """Enhanced system health validation with detailed analysis"""
        
        forecasts = frappe.get_all('AI Financial Forecast', 
                                  filters={'company': self.company},
                                  fields=['confidence_score', 'forecast_type', 'risk_category',
                                         'creation', 'volatility_score', 'sync_status'])
        
        if not forecasts:
            return {
                'status': 'No forecasts found', 
                'health_score': 0,
                'company': self.company,
                'recommendations': ['Create initial forecasts for key accounts']
            }
        
        # Basic health metrics
        avg_confidence = sum(f.confidence_score for f in forecasts) / len(forecasts)
        high_confidence_count = len([f for f in forecasts if f.confidence_score >= 80])
        unique_types = len(set(f.forecast_type for f in forecasts))
        
        # Advanced health metrics
        recent_forecasts = [f for f in forecasts if self.is_recent(f.creation, days=7)]
        sync_success_rate = len([f for f in forecasts if f.sync_status == "Completed"]) / len(forecasts)
        low_risk_ratio = len([f for f in forecasts if f.risk_category == "Low"]) / len(forecasts)
        
        # Calculate weighted health score
        confidence_score = (avg_confidence / 100) * 0.3
        diversity_score = (min(unique_types / 5, 1)) * 0.2
        activity_score = (len(recent_forecasts) / max(len(forecasts), 1)) * 0.2
        sync_score = sync_success_rate * 0.15
        risk_score = low_risk_ratio * 0.15
        
        health_score = (confidence_score + diversity_score + activity_score + sync_score + risk_score) * 100
        
        # Generate recommendations
        recommendations = self.generate_health_recommendations(forecasts, avg_confidence, unique_types)
        
        # Health status categorization
        if health_score >= 85:
            status = "Excellent"
        elif health_score >= 75:
            status = "Good"
        elif health_score >= 60:
            status = "Fair"
        elif health_score >= 40:
            status = "Poor"
        else:
            status = "Critical"
        
        return {
            'status': status,
            'health_score': round(health_score, 1),
            'company': self.company,
            'metrics': {
                'avg_confidence': round(avg_confidence, 1),
                'high_confidence_ratio': round((high_confidence_count / len(forecasts)) * 100, 1),
                'forecast_types_active': unique_types,
                'recent_activity_ratio': round((len(recent_forecasts) / len(forecasts)) * 100, 1),
                'sync_success_rate': round(sync_success_rate * 100, 1),
                'low_risk_ratio': round(low_risk_ratio * 100, 1)
            },
            'recommendations': recommendations,
            'total_forecasts': len(forecasts),
            'assessment_date': datetime.now().isoformat()
        }
    
    def get_forecast_recommendations(self, account: str = None) -> Dict:
        """Get AI-powered recommendations for forecast improvement"""
        
        filters = {'company': self.company}
        if account:
            filters['account'] = account
        
        forecasts = frappe.get_all('AI Financial Forecast',
                                  filters=filters,
                                  fields=['account', 'forecast_type', 'confidence_score', 
                                         'risk_category', 'prediction_model', 'volatility_score'])
        
        recommendations = {
            'optimization': [],
            'risk_mitigation': [],
            'model_improvements': [],
            'coverage_expansion': [],
            'priority_actions': []
        }
        
        for forecast in forecasts:
            # Optimization recommendations
            if forecast.confidence_score < 70:
                recommendations['optimization'].append({
                    'account': forecast.account,
                    'current_confidence': forecast.confidence_score,
                    'suggestion': 'Consider using Ensemble model for better accuracy',
                    'priority': 'high',
                    'expected_improvement': '10-15% confidence increase'
                })
            
            # Risk mitigation
            if forecast.risk_category in ['High', 'Critical']:
                recommendations['risk_mitigation'].append({
                    'account': forecast.account,
                    'risk_level': forecast.risk_category,
                    'suggestion': 'Increase monitoring frequency and set up alerts',
                    'priority': 'critical',
                    'action': 'immediate'
                })
            
            # Model improvements
            if forecast.volatility_score and forecast.volatility_score > 60:
                recommendations['model_improvements'].append({
                    'account': forecast.account,
                    'current_model': forecast.prediction_model,
                    'suggestion': 'Switch to ARIMA model for volatile data',
                    'priority': 'medium',
                    'volatility': forecast.volatility_score
                })
        
        # Coverage expansion recommendations
        total_accounts = frappe.db.count('Account', {'company': self.company, 'is_group': 0})
        forecasted_accounts = len(set(f.account for f in forecasts))
        
        if forecasted_accounts < total_accounts * 0.3:  # Less than 30% coverage
            recommendations['coverage_expansion'].append({
                'current_coverage': f"{forecasted_accounts}/{total_accounts} accounts",
                'suggestion': 'Expand forecasting to key Asset and Income accounts',
                'priority': 'medium',
                'potential_accounts': self.get_recommended_accounts_for_expansion()
            })
        
        # Priority actions based on overall analysis
        recommendations['priority_actions'] = self.get_priority_actions(forecasts)
        
        return {
            'account_specific': account is not None,
            'total_recommendations': sum(len(rec) for rec in recommendations.values()),
            'recommendations': recommendations,
            'generated_on': datetime.now().isoformat()
        }
    
    def bulk_update_forecasts(self, filters: Dict, updates: Dict) -> Dict:
        """Bulk update multiple forecasts"""
        
        try:
            # Get forecasts to update
            forecast_filters = {'company': self.company}
            forecast_filters.update(filters)
            
            forecasts_to_update = frappe.get_all('AI Financial Forecast',
                                                filters=forecast_filters,
                                                pluck='name')
            
            updated = []
            failed = []
            
            for forecast_name in forecasts_to_update:
                try:
                    doc = frappe.get_doc('AI Financial Forecast', forecast_name)
                    
                    # Apply updates
                    for field, value in updates.items():
                        if hasattr(doc, field):
                            setattr(doc, field, value)
                    
                    doc.save()
                    updated.append(forecast_name)
                    
                except Exception as e:
                    failed.append({'forecast': forecast_name, 'error': str(e)})
            
            return {
                'success': True,
                'updated_count': len(updated),
                'failed_count': len(failed),
                'updated_forecasts': updated,
                'failed_updates': failed
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Utility methods
    def is_recent(self, date_obj, days=7):
        """Check if date is within recent days"""
        if not date_obj:
            return False
        cutoff = datetime.now() - timedelta(days=days)
        return date_obj >= cutoff
    
    def get_confidence_grade(self, confidence):
        """Get confidence grade (A-F)"""
        if confidence >= 90:
            return "A+"
        elif confidence >= 80:
            return "A"
        elif confidence >= 70:
            return "B"
        elif confidence >= 60:
            return "C"
        elif confidence >= 50:
            return "D"
        else:
            return "F"
    
    def calculate_performance_metrics(self, forecasts):
        """Calculate detailed performance metrics"""
        if not forecasts:
            return {}
        
        total = len(forecasts)
        high_performance = len([f for f in forecasts if f.confidence_score >= 80])
        medium_performance = len([f for f in forecasts if 60 <= f.confidence_score < 80])
        low_performance = total - high_performance - medium_performance
        
        return {
            'total_forecasts': total,
            'high_performance_count': high_performance,
            'medium_performance_count': medium_performance,
            'low_performance_count': low_performance,
            'high_performance_ratio': round((high_performance / total) * 100, 1),
            'medium_performance_ratio': round((medium_performance / total) * 100, 1),
            'low_performance_ratio': round((low_performance / total) * 100, 1),
            'overall_grade': self.get_confidence_grade(sum(f.confidence_score for f in forecasts) / total)
        }
    
    def calculate_batch_performance_metrics(self, created_forecasts):
        """Calculate performance metrics for batch creation"""
        if not created_forecasts:
            return {}
        
        total_confidence = sum(f.get('confidence_score', 0) for f in created_forecasts)
        avg_confidence = total_confidence / len(created_forecasts)
        
        return {
            'batch_size': len(created_forecasts),
            'average_confidence': round(avg_confidence, 1),
            'confidence_grade': self.get_confidence_grade(avg_confidence),
            'batch_quality': 'Excellent' if avg_confidence >= 80 else 'Good' if avg_confidence >= 70 else 'Fair'
        }
    
    def get_recent_activity(self, days=7):
        """Get recent forecast activity"""
        from_date = datetime.now() - timedelta(days=days)
        
        recent_forecasts = frappe.get_all('AI Financial Forecast',
                                        filters={
                                            'company': self.company,
                                            'creation': ['>=', from_date.strftime('%Y-%m-%d')]
                                        },
                                        fields=['name', 'account', 'forecast_type', 'creation'],
                                        order_by='creation desc',
                                        limit=10)
        
        return [
            {
                'forecast_id': f.name,
                'account': f.account,
                'type': f.forecast_type,
                'created': f.creation.strftime('%Y-%m-%d %H:%M') if f.creation else ''
            }
            for f in recent_forecasts
        ]
    
    def generate_health_recommendations(self, forecasts, avg_confidence, unique_types):
        """Generate health improvement recommendations"""
        recommendations = []
        
        if avg_confidence < 70:
            recommendations.append("Improve model accuracy by using Ensemble methods")
        
        if unique_types < 3:
            recommendations.append("Expand forecast coverage to include more forecast types")
        
        low_confidence_count = len([f for f in forecasts if f.confidence_score < 60])
        if low_confidence_count > len(forecasts) * 0.3:
            recommendations.append("Review and retrain models for low-confidence forecasts")
        
        recent_count = len([f for f in forecasts if self.is_recent(f.creation, 30)])
        if recent_count < len(forecasts) * 0.5:
            recommendations.append("Update forecasts more frequently - consider automated scheduling")
        
        return recommendations
    
    def get_recommended_accounts_for_expansion(self):
        """Get recommended accounts for forecast expansion"""
        try:
            # Get accounts not yet forecasted
            forecasted_accounts = frappe.get_all('AI Financial Forecast',
                                               filters={'company': self.company},
                                               pluck='account')
            
            all_accounts = frappe.get_all('Account',
                                        filters={
                                            'company': self.company,
                                            'is_group': 0,
                                            'name': ['not in', forecasted_accounts] if forecasted_accounts else []
                                        },
                                        fields=['name', 'account_type'],
                                        limit=5)
            
            # Prioritize key account types
            priority_types = ['Asset', 'Income', 'Expense']
            recommended = []
            
            for acc in all_accounts:
                if acc.account_type in priority_types:
                    recommended.append({
                        'account': acc.name,
                        'type': acc.account_type,
                        'priority': 'High' if acc.account_type in ['Asset', 'Income'] else 'Medium'
                    })
            
            return recommended[:5]  # Return top 5 recommendations
            
        except Exception as e:
            frappe.log_error(f"Error getting recommended accounts: {str(e)}")
            return []
    
    def get_priority_actions(self, forecasts):
        """Get priority actions based on forecast analysis"""
        actions = []
        
        # Critical issues
        critical_forecasts = [f for f in forecasts if f.risk_category == 'Critical']
        if critical_forecasts:
            actions.append({
                'priority': 'critical',
                'action': f"Review {len(critical_forecasts)} critical risk forecasts immediately",
                'urgency': 'immediate',
                'impact': 'high'
            })
        
        # Low confidence issues
        low_confidence = [f for f in forecasts if f.confidence_score < 50]
        if low_confidence:
            actions.append({
                'priority': 'high',
                'action': f"Improve {len(low_confidence)} low-confidence forecasts",
                'urgency': 'this_week',
                'impact': 'medium'
            })
        
        # Coverage gaps
        forecast_types_count = len(set(f.forecast_type for f in forecasts))
        if forecast_types_count < 4:
            actions.append({
                'priority': 'medium',
                'action': "Expand forecast types coverage",
                'urgency': 'this_month',
                'impact': 'medium'
            })
        
        return actions
