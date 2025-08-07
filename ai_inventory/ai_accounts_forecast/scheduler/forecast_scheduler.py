
# Background job scheduling and system monitoring
# Path: ai_inventory/ai_accounts_forecast/scheduler/forecast_scheduler.py
# ============================================================================

import frappe
from frappe.utils.background_jobs import enqueue
from frappe.utils import cstr, flt, getdate, nowdate, add_days, get_datetime
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

try:
    from ai_inventory.ai_accounts_forecast.models.account_forecast import create_financial_forecast, ForecastManager
except ImportError as e:
    frappe.log_error(f"Import error in forecast_scheduler: {str(e)}", "Forecast Scheduler Import")
    # Define fallback functions
    def create_financial_forecast(*args, **kwargs):
        return {"status": "error", "message": "ForecastManager not available"}
    
    class ForecastManager:
        def __init__(self, company):
            self.company = company
        
        def validate_system_health(self):
            return {"health_score": 0, "status": "Import Error", "message": "ForecastManager not available"}

# ============================================================================
# SCHEDULER SETUP AND CONFIGURATION
# ============================================================================

def setup_forecast_scheduler():
    """Setup automated forecast generation and monitoring"""
    
    print("🕐 Setting up AI Financial Forecast Scheduler...")
    
    # Schedule daily forecast updates
    try:
        frappe.enqueue(
            'ai_inventory.ai_accounts_forecast.scheduler.forecast_scheduler.daily_forecast_update',
            queue='daily',
            job_name='ai_forecast_daily_update',
            timeout=3600,  # 1 hour timeout
            is_async=True
        )
        print("✅ Daily forecast update scheduled")
    except Exception as e:
        print(f"❌ Failed to schedule daily updates: {str(e)}")
    
    # Schedule weekly system health check
    try:
        frappe.enqueue(
            'ai_inventory.ai_accounts_forecast.scheduler.forecast_scheduler.weekly_health_check',
            queue='weekly',
            job_name='ai_forecast_weekly_health',
            timeout=1800,  # 30 minutes timeout
            is_async=True
        )
        print("✅ Weekly health check scheduled")
    except Exception as e:
        print(f"❌ Failed to schedule health checks: {str(e)}")
    
    # Schedule monthly cleanup
    try:
        frappe.enqueue(
            'ai_inventory.ai_accounts_forecast.scheduler.forecast_scheduler.monthly_cleanup',
            queue='monthly',
            job_name='ai_forecast_monthly_cleanup',
            timeout=1800,
            is_async=True
        )
        print("✅ Monthly cleanup scheduled")
    except Exception as e:
        print(f"❌ Failed to schedule cleanup: {str(e)}")
    
    print("🎯 Scheduler setup complete!")

# ============================================================================
# DAILY AUTOMATED TASKS
# ============================================================================

def daily_forecast_update():
    """Daily automated forecast updates for all companies"""
    
    try:
        # Check if system is ready
        if not frappe.db.table_exists("AI Financial Forecast"):
            frappe.log_error("AI Financial Forecast table not found", "Forecast Scheduler")
            return
        
        print("🌅 Starting daily forecast update...")
        
        # Get all active companies
        companies = frappe.get_all('Company', 
                                  filters={'disabled': 0}, 
                                  pluck='name')
        
        total_created = 0
        total_failed = 0
        
        for company in companies:
            try:
                print(f"📊 Processing company: {company}")
                
                # Update forecasts for this company
                created, failed = update_company_forecasts(company)
                total_created += created
                total_failed += failed
                
                print(f"   ✅ {company}: {created} created, {failed} failed")
                
            except Exception as e:
                print(f"   ❌ Failed to update {company}: {str(e)}")
                frappe.log_error(f"Daily forecast update failed for {company}: {str(e)}", 
                               "AI Forecast Daily Update")
                total_failed += 1
        
        # Log summary
        summary_message = f"Daily update complete: {total_created} forecasts created, {total_failed} failed across {len(companies)} companies"
        print(f"🎯 {summary_message}")
        
        # Create system log
        create_scheduler_log("Daily Update", summary_message, {
            'companies_processed': len(companies),
            'forecasts_created': total_created,
            'forecasts_failed': total_failed
        })
        
    except Exception as e:
        error_msg = f"Daily forecast update system error: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "AI Forecast Daily Update System")

def update_company_forecasts(company: str) -> tuple:
    """Update forecasts for a specific company"""
    
    created_count = 0
    failed_count = 0
    
    try:
        # Get priority accounts for daily updates
        priority_accounts = get_priority_accounts_for_updates(company)
        
        # Update Cash Flow forecasts for priority accounts
        for account in priority_accounts[:10]:  # Limit to top 10 daily
            try:
                result = create_financial_forecast(company, account, 'Cash Flow')
                created_count += 1
                
                # Also update Revenue forecast for high-priority accounts
                if any(keyword in account.lower() for keyword in ['cash', 'bank', 'revenue']):
                    revenue_result = create_financial_forecast(company, account, 'Revenue')
                    created_count += 1
                    
            except Exception as e:
                failed_count += 1
                frappe.log_error(f"Failed to update forecast for {account}: {str(e)}", 
                               "AI Forecast Account Update")
    
    except Exception as e:
        frappe.log_error(f"Error updating company forecasts for {company}: {str(e)}", 
                        "AI Forecast Company Update")
        failed_count += 1
    
    return created_count, failed_count

def get_priority_accounts_for_updates(company: str) -> List[str]:
    """Get priority accounts that need daily forecast updates"""
    
    try:
        # Get accounts with specific keywords (high-priority for daily updates)
        priority_keywords = ['cash', 'bank', 'revenue', 'income', 'sales', 'debtor', 'receivable']
        
        all_accounts = frappe.get_all('Account',
                                    filters={'company': company, 'is_group': 0, 'disabled': 0},
                                    fields=['name', 'account_type'],
                                    order_by='name')
        
        priority_accounts = []
        
        for account in all_accounts:
            account_name_lower = account.name.lower()
            
            # Add if matches priority keywords
            if any(keyword in account_name_lower for keyword in priority_keywords):
                priority_accounts.append(account.name)
            
            # Add Asset and Income accounts
            elif account.account_type in ['Asset', 'Income']:
                priority_accounts.append(account.name)
        
        return priority_accounts
        
    except Exception as e:
        frappe.log_error(f"Error getting priority accounts for {company}: {str(e)}", 
                        "AI Forecast Priority Accounts")
        return []

# ============================================================================
# WEEKLY SYSTEM MONITORING
# ============================================================================

def weekly_health_check():
    """Weekly comprehensive system health monitoring"""
    
    try:
        # Check if system is ready
        if not frappe.db.table_exists("AI Financial Forecast"):
            frappe.log_error("AI Financial Forecast table not found", "Forecast Scheduler Health")
            return
        
        print("🏥 Starting weekly system health check...")
        
        companies = frappe.get_all('Company', filters={'disabled': 0}, pluck='name')
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'companies': {},
            'system_summary': {
                'total_companies': len(companies),
                'healthy_companies': 0,
                'companies_needing_attention': 0,
                'total_forecasts': 0,
                'average_system_health': 0
            }
        }
        
        total_health_scores = []
        
        for company in companies:
            try:
                # Get company health metrics
                manager = ForecastManager(company)
                company_health = manager.validate_system_health()
                
                # Enhanced health analysis
                enhanced_health = perform_enhanced_health_check(company)
                
                # Combine metrics
                combined_health = {
                    **company_health,
                    **enhanced_health,
                    'company': company,
                    'check_timestamp': datetime.now().isoformat()
                }
                
                health_report['companies'][company] = combined_health
                
                # Track overall metrics
                health_score = combined_health.get('health_score', 0)
                total_health_scores.append(health_score)
                
                if health_score >= 75:
                    health_report['system_summary']['healthy_companies'] += 1
                else:
                    health_report['system_summary']['companies_needing_attention'] += 1
                
                # Send alerts if needed
                if health_score < 60:
                    send_critical_health_alert(company, combined_health)
                elif health_score < 75:
                    send_warning_health_alert(company, combined_health)
                
                print(f"   📊 {company}: Health Score {health_score}%")
                
            except Exception as e:
                print(f"   ❌ Health check failed for {company}: {str(e)}")
                frappe.log_error(f"Weekly health check failed for {company}: {str(e)}", 
                               "AI Forecast Weekly Health")
        
        # Calculate system summary
        if total_health_scores:
            health_report['system_summary']['average_system_health'] = sum(total_health_scores) / len(total_health_scores)
            health_report['system_summary']['total_forecasts'] = frappe.db.count('AI Financial Forecast')
        
        # Save health report
        save_health_report(health_report)
        
        # Send weekly summary
        send_weekly_health_summary(health_report)
        
        print(f"🎯 Weekly health check complete. Average system health: {health_report['system_summary']['average_system_health']:.1f}%")
        
    except Exception as e:
        error_msg = f"Weekly health check system error: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "AI Forecast Weekly Health System")

def perform_enhanced_health_check(company: str) -> Dict:
    """Perform enhanced health analysis for a company"""
    
    try:
        # Get recent forecast activity
        recent_forecasts = frappe.get_all('AI Financial Forecast',
                                        filters={
                                            'company': company,
                                            'creation': ['>', add_days(nowdate(), -7)]
                                        },
                                        fields=['confidence_score', 'forecast_type'])
        
        # Get forecast age distribution
        old_forecasts = frappe.get_all('AI Financial Forecast',
                                     filters={
                                         'company': company,
                                         'creation': ['<', add_days(nowdate(), -30)]
                                     })
        
        # Calculate metrics
        total_forecasts = frappe.db.count('AI Financial Forecast', {'company': company})
        recent_activity_score = min(100, (len(recent_forecasts) / 10) * 100) if recent_forecasts else 0
        data_freshness_score = max(0, 100 - (len(old_forecasts) / max(1, total_forecasts)) * 100)
        
        # Check forecast distribution
        forecast_types = set(f.forecast_type for f in recent_forecasts)
        type_diversity_score = (len(forecast_types) / 5) * 100  # 5 possible types
        
        # Overall enhanced score
        enhanced_score = (recent_activity_score * 0.4 + data_freshness_score * 0.4 + type_diversity_score * 0.2)
        
        return {
            'enhanced_health_score': round(enhanced_score, 1),
            'recent_activity_score': round(recent_activity_score, 1),
            'data_freshness_score': round(data_freshness_score, 1),
            'type_diversity_score': round(type_diversity_score, 1),
            'recent_forecasts_count': len(recent_forecasts),
            'old_forecasts_count': len(old_forecasts),
            'active_forecast_types': len(forecast_types)
        }
        
    except Exception as e:
        frappe.log_error(f"Enhanced health check failed for {company}: {str(e)}", 
                        "AI Forecast Enhanced Health")
        return {'enhanced_health_score': 0, 'error': str(e)}

# ============================================================================
# MONTHLY MAINTENANCE TASKS
# ============================================================================

def monthly_cleanup():
    """Monthly cleanup and maintenance tasks"""
    
    try:
        # Check if system is ready
        if not frappe.db.table_exists("AI Financial Forecast"):
            frappe.log_error("AI Financial Forecast table not found", "Forecast Scheduler Cleanup")
            return
        
        print("🧹 Starting monthly cleanup and maintenance...")
        
        cleanup_results = {
            'old_forecasts_deleted': 0,
            'duplicate_forecasts_removed': 0,
            'orphaned_records_cleaned': 0,
            'performance_optimizations': 0
        }
        
        # Cleanup old forecasts (older than 6 months)
        old_forecasts_deleted = cleanup_old_forecasts(180)  # 6 months
        cleanup_results['old_forecasts_deleted'] = old_forecasts_deleted
        
        # Remove duplicate forecasts
        duplicates_removed = cleanup_duplicate_forecasts()
        cleanup_results['duplicate_forecasts_removed'] = duplicates_removed
        
        # Optimize database indexes
        optimize_database_performance()
        cleanup_results['performance_optimizations'] = 1
        
        # Generate monthly report
        generate_monthly_report()
        
        # Log cleanup results
        summary_message = f"Monthly cleanup complete: {old_forecasts_deleted} old forecasts deleted, {duplicates_removed} duplicates removed"
        print(f"🎯 {summary_message}")
        
        create_scheduler_log("Monthly Cleanup", summary_message, cleanup_results)
        
    except Exception as e:
        error_msg = f"Monthly cleanup system error: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "AI Forecast Monthly Cleanup")

def cleanup_old_forecasts(days_old: int = 180) -> int:
    """Remove forecasts older than specified days"""
    
    try:
        cutoff_date = add_days(nowdate(), -days_old)
        
        old_forecasts = frappe.get_all('AI Financial Forecast',
                                     filters={'creation': ['<', cutoff_date]},
                                     pluck='name')
        
        deleted_count = 0
        for forecast_name in old_forecasts:
            try:
                frappe.delete_doc('AI Financial Forecast', forecast_name, ignore_permissions=True)
                deleted_count += 1
            except:
                continue
        
        if deleted_count > 0:
            frappe.db.commit()
        
        return deleted_count
        
    except Exception as e:
        frappe.log_error(f"Cleanup old forecasts failed: {str(e)}", "AI Forecast Cleanup")
        return 0

def cleanup_duplicate_forecasts() -> int:
    """Remove duplicate forecasts keeping the most recent"""
    
    try:
        # Find duplicates
        duplicates = frappe.db.sql("""
            SELECT company, account, forecast_type, 
                   GROUP_CONCAT(name ORDER BY creation DESC) as forecast_names,
                   COUNT(*) as count
            FROM `tabAI Financial Forecast`
            GROUP BY company, account, forecast_type
            HAVING COUNT(*) > 1
        """, as_dict=True)
        
        deleted_count = 0
        
        for dup in duplicates:
            forecast_names = dup.forecast_names.split(',')
            # Keep the first (most recent), delete the rest
            to_delete = forecast_names[1:]
            
            for forecast_name in to_delete:
                try:
                    frappe.delete_doc('AI Financial Forecast', forecast_name, ignore_permissions=True)
                    deleted_count += 1
                except:
                    continue
        
        if deleted_count > 0:
            frappe.db.commit()
        
        return deleted_count
        
    except Exception as e:
        frappe.log_error(f"Cleanup duplicates failed: {str(e)}", "AI Forecast Cleanup")
        return 0

def optimize_database_performance():
    """Optimize database indexes and performance"""
    
    try:
        # Add indexes for common queries
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_ai_forecast_company_account 
            ON `tabAI Financial Forecast` (company, account)
        """)
        
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_ai_forecast_type_creation 
            ON `tabAI Financial Forecast` (forecast_type, creation)
        """)
        
        frappe.db.sql("""
            CREATE INDEX IF NOT EXISTS idx_ai_forecast_confidence 
            ON `tabAI Financial Forecast` (confidence_score)
        """)
        
        print("✅ Database indexes optimized")
        
    except Exception as e:
        frappe.log_error(f"Database optimization failed: {str(e)}", "AI Forecast Optimization")

# ============================================================================
# NOTIFICATION AND ALERTING SYSTEM
# ============================================================================

def send_critical_health_alert(company: str, health_data: Dict):
    """Send critical health alert for companies with health score < 60%"""
    
    try:
        subject = f"🚨 CRITICAL: AI Forecast System Health Alert - {company}"
        
        message = f"""
        <h2>Critical System Health Alert</h2>
        <p><strong>Company:</strong> {company}</p>
        <p><strong>Health Score:</strong> <span style="color: red;">{health_data.get('health_score', 0):.1f}%</span></p>
        <p><strong>Status:</strong> {health_data.get('status', 'Unknown')}</p>
        
        <h3>Metrics:</h3>
        <ul>
            <li>Average Confidence: {health_data.get('avg_confidence', 0):.1f}%</li>
            <li>High Confidence Ratio: {health_data.get('high_confidence_ratio', 0):.1f}%</li>
            <li>Active Forecast Types: {health_data.get('forecast_types_active', 0)}</li>
            <li>Recent Activity Score: {health_data.get('recent_activity_score', 0):.1f}%</li>
        </ul>
        
        <p><strong>Action Required:</strong> Immediate attention needed for forecast system performance.</p>
        """
        
        send_system_notification(subject, message, priority="Critical")
        
    except Exception as e:
        frappe.log_error(f"Failed to send critical health alert: {str(e)}", "AI Forecast Alerts")

def send_warning_health_alert(company: str, health_data: Dict):
    """Send warning health alert for companies with health score 60-75%"""
    
    try:
        subject = f"⚠️ WARNING: AI Forecast System Health - {company}"
        
        message = f"""
        <h2>System Health Warning</h2>
        <p><strong>Company:</strong> {company}</p>
        <p><strong>Health Score:</strong> <span style="color: orange;">{health_data.get('health_score', 0):.1f}%</span></p>
        <p><strong>Status:</strong> {health_data.get('status', 'Unknown')}</p>
        
        <p>System performance is below optimal levels. Consider reviewing forecast generation processes.</p>
        """
        
        send_system_notification(subject, message, priority="Warning")
        
    except Exception as e:
        frappe.log_error(f"Failed to send warning health alert: {str(e)}", "AI Forecast Alerts")

def send_weekly_health_summary(health_report: Dict):
    """Send weekly health summary to administrators"""
    
    try:
        subject = "📊 Weekly AI Forecast System Health Summary"
        
        summary = health_report['system_summary']
        
        message = f"""
        <h2>Weekly System Health Summary</h2>
        <p><strong>Report Period:</strong> {health_report['timestamp']}</p>
        
        <h3>System Overview:</h3>
        <ul>
            <li>Total Companies: {summary['total_companies']}</li>
            <li>Healthy Companies: {summary['healthy_companies']}</li>
            <li>Companies Needing Attention: {summary['companies_needing_attention']}</li>
            <li>Total Forecasts: {summary['total_forecasts']}</li>
            <li>Average System Health: {summary['average_system_health']:.1f}%</li>
        </ul>
        
        <h3>Company Details:</h3>
        """
        
        for company, health in health_report['companies'].items():
            status_color = "green" if health.get('health_score', 0) >= 75 else "orange" if health.get('health_score', 0) >= 60 else "red"
            message += f'<p><strong>{company}:</strong> <span style="color: {status_color};">{health.get("health_score", 0):.1f}%</span></p>'
        
        send_system_notification(subject, message, priority="Info")
        
    except Exception as e:
        frappe.log_error(f"Failed to send weekly health summary: {str(e)}", "AI Forecast Alerts")

def send_system_notification(subject: str, message: str, priority: str = "Info"):
    """Send system notification email"""
    
    try:
        # Get system administrators
        administrators = frappe.get_all('User', 
                                      filters={'role_profile_name': 'System Manager'}, 
                                      pluck='email')
        
        if not administrators:
            administrators = ['administrator@example.com']  # Fallback
        
        frappe.sendmail(
            recipients=administrators,
            subject=subject,
            message=message,
            priority=priority
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send system notification: {str(e)}", "AI Forecast Notifications")

# ============================================================================
# LOGGING AND REPORTING
# ============================================================================

def create_scheduler_log(task_type: str, message: str, data: Dict = None):
    """Create log entry for scheduler activities"""
    
    try:
        # Check if the log DocType exists
        if not frappe.db.table_exists('AI Forecast Scheduler Log'):
            # Just log to standard error log if DocType doesn't exist
            frappe.log_error(f"Scheduler Log ({task_type}): {message}", "AI Forecast Scheduler")
            return
        
        log_doc = frappe.get_doc({
            'doctype': 'AI Forecast Scheduler Log',
            'task_type': task_type,
            'message': message,
            'task_data': json.dumps(data) if data else None,
            'execution_time': datetime.now(),
            'status': 'Completed'
        })
        
        log_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Failed to create scheduler log: {str(e)}", "AI Forecast Scheduler Log")

def save_health_report(health_report: Dict):
    """Save weekly health report to database"""
    
    try:
        # Check if the health report DocType exists
        if not frappe.db.table_exists('AI Forecast Health Report'):
            # Just log to standard error log if DocType doesn't exist
            frappe.log_error(f"Health Report: {json.dumps(health_report['system_summary'])}", "AI Forecast Health")
            return
        
        report_doc = frappe.get_doc({
            'doctype': 'AI Forecast Health Report',
            'report_date': nowdate(),
            'report_data': json.dumps(health_report),
            'total_companies': health_report['system_summary']['total_companies'],
            'average_health_score': health_report['system_summary']['average_system_health'],
            'healthy_companies': health_report['system_summary']['healthy_companies'],
            'companies_needing_attention': health_report['system_summary']['companies_needing_attention']
        })
        
        report_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Failed to save health report: {str(e)}", "AI Forecast Health Report")

def generate_monthly_report():
    """Generate comprehensive monthly system report"""
    
    try:
        # Check if the monthly report DocType exists
        if not frappe.db.table_exists('AI Forecast Monthly Report'):
            # Just log to standard error log if DocType doesn't exist
            frappe.log_error("Monthly report generated (DocType not found)", "AI Forecast Monthly")
            return
        
        # Calculate monthly metrics
        start_date = add_days(nowdate(), -30)
        
        monthly_metrics = {
            'forecasts_created': frappe.db.count('AI Financial Forecast', {'creation': ['>', start_date]}),
            'companies_active': len(frappe.get_all('AI Financial Forecast', 
                                                  filters={'creation': ['>', start_date]}, 
                                                  group_by='company')),
            'average_confidence': frappe.db.sql("""
                SELECT AVG(confidence_score) 
                FROM `tabAI Financial Forecast` 
                WHERE creation > %s
            """, (start_date,))[0][0] or 0,
            'report_date': nowdate()
        }
        
        # Save monthly report
        report_doc = frappe.get_doc({
            'doctype': 'AI Forecast Monthly Report',
            'report_date': nowdate(),
            'forecasts_created': monthly_metrics['forecasts_created'],
            'companies_active': monthly_metrics['companies_active'],
            'average_confidence': monthly_metrics['average_confidence'],
            'report_data': json.dumps(monthly_metrics)
        })
        
        report_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"📊 Monthly report generated: {monthly_metrics['forecasts_created']} forecasts created")
        
    except Exception as e:
        frappe.log_error(f"Failed to generate monthly report: {str(e)}", "AI Forecast Monthly Report")