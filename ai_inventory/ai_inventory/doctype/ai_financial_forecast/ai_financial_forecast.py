# ============================================================================
# FILE 2: ai_accounts_forecast/doctype/ai_financial_forecast/ai_financial_forecast.py
# DocType controller
# ============================================================================

import frappe
from frappe.model.document import Document

class AIFinancialForecast(Document):
    """AI Financial Forecast Document Controller"""
    
    def validate(self):
        """Validate forecast data before saving"""
        self.validate_forecast_type()
        self.validate_dates()
        self.validate_confidence_score()
    
    def validate_forecast_type(self):
        """Validate forecast type is in allowed list"""
        valid_types = ["Cash Flow", "Revenue", "Expense", "Balance Sheet", "P&L"]
        if self.forecast_type not in valid_types:
            frappe.throw(f"Invalid forecast type. Must be one of: {', '.join(valid_types)}")
    
    def validate_dates(self):
        """Validate forecast dates"""
        if self.forecast_end_date <= self.forecast_start_date:
            frappe.throw("Forecast end date must be after start date")
    
    def validate_confidence_score(self):
        """Validate confidence score is within bounds"""
        if not (0 <= self.confidence_score <= 100):
            frappe.throw("Confidence score must be between 0 and 100")
    
    def before_save(self):
        """Actions before saving"""
        self.set_forecast_accuracy()
        self.set_risk_category()
    
    def set_forecast_accuracy(self):
        """Set forecast accuracy based on confidence score"""
        if self.confidence_score >= 80:
            self.forecast_accuracy = "High"
        elif self.confidence_score >= 60:
            self.forecast_accuracy = "Medium"
        else:
            self.forecast_accuracy = "Low"
    
    def set_risk_category(self):
        """Set risk category based on various factors"""
        if self.confidence_score >= 75 and self.volatility_score <= 0.3:
            self.risk_category = "Low"
        elif self.confidence_score >= 60:
            self.risk_category = "Medium"
        else:
            self.risk_category = "High"

# ============================================================================
# FILE 3: Management and Utility Functions
# Complete system management utilities
# ============================================================================

from collections import defaultdict
import json
from datetime import datetime

class ForecastManager:
    """Complete forecast management system"""
    
    def __init__(self, company: str):
        self.company = company
    
    def create_comprehensive_forecasts(self, accounts: List[str], forecast_types: List[str] = None) -> Dict:
        """Create comprehensive forecasts for multiple accounts"""
        
        if forecast_types is None:
            forecast_types = ["Cash Flow", "Revenue", "Expense", "Balance Sheet", "P&L"]
        
        results = {
            'created': [],
            'failed': [],
            'summary': {}
        }
        
        for account in accounts:
            for forecast_type in forecast_types:
                try:
                    result = create_financial_forecast(self.company, account, forecast_type)
                    results['created'].append(result)
                except Exception as e:
                    results['failed'].append({
                        'account': account,
                        'forecast_type': forecast_type,
                        'error': str(e)
                    })
        
        results['summary'] = {
            'total_created': len(results['created']),
            'total_failed': len(results['failed']),
            'success_rate': len(results['created']) / (len(results['created']) + len(results['failed'])) * 100
        }
        
        return results
    
    def get_system_dashboard(self) -> Dict:
        """Generate comprehensive system dashboard"""
        
        forecasts = frappe.get_all('AI Financial Forecast',
                                  filters={'company': self.company},
                                  fields=['name', 'account', 'forecast_type', 'confidence_score', 
                                         'predicted_amount', 'creation'])
        
        dashboard = {
            'summary': {
                'total_forecasts': len(forecasts),
                'avg_confidence': sum(f.confidence_score for f in forecasts) / len(forecasts) if forecasts else 0,
                'total_predicted_value': sum(f.predicted_amount for f in forecasts if f.predicted_amount) 
            },
            'by_type': {},
            'by_account': {},
            'performance_metrics': {}
        }
        
        # Group by type
        by_type = defaultdict(list)
        for f in forecasts:
            by_type[f.forecast_type].append(f)
        
        for ftype, type_forecasts in by_type.items():
            dashboard['by_type'][ftype] = {
                'count': len(type_forecasts),
                'avg_confidence': sum(tf.confidence_score for tf in type_forecasts) / len(type_forecasts),
                'total_predicted': sum(tf.predicted_amount for tf in type_forecasts if tf.predicted_amount)
            }
        
        # Group by account
        by_account = defaultdict(list)
        for f in forecasts:
            by_account[f.account].append(f)
        
        for account, acc_forecasts in by_account.items():
            dashboard['by_account'][account] = {
                'count': len(acc_forecasts),
                'types': len(set(af.forecast_type for af in acc_forecasts)),
                'avg_confidence': sum(af.confidence_score for af in acc_forecasts) / len(acc_forecasts)
            }
        
        return dashboard
    
    def validate_system_health(self) -> Dict:
        """Validate overall system health"""
        
        forecasts = frappe.get_all('AI Financial Forecast', 
                                  filters={'company': self.company},
                                  fields=['confidence_score', 'forecast_type'])
        
        if not forecasts:
            return {'status': 'No forecasts found', 'health_score': 0}
        
        avg_confidence = sum(f.confidence_score for f in forecasts) / len(forecasts)
        high_confidence_count = len([f for f in forecasts if f.confidence_score >= 80])
        unique_types = len(set(f.forecast_type for f in forecasts))
        
        health_score = (
            (avg_confidence / 100) * 0.5 +  # 50% weight on confidence
            (high_confidence_count / len(forecasts)) * 0.3 +  # 30% weight on high confidence ratio
            (min(unique_types / 5, 1)) * 0.2  # 20% weight on type diversity
        ) * 100
        
        return {
            'status': 'Healthy' if health_score >= 75 else 'Needs Attention',
            'health_score': round(health_score, 1),
            'avg_confidence': round(avg_confidence, 1),
            'high_confidence_ratio': round(high_confidence_count / len(forecasts) * 100, 1),
            'forecast_types_active': unique_types
        }
