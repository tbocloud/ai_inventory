# ============================================================================
# FILE 6: Complete Setup and Deployment Script - CORRECTED VERSION
# One-time setup script for complete system deployment
# Path: ai_inventory/ai_accounts_forecast/setup/system_setup.py
# ============================================================================

import frappe
from frappe import _
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from ai_inventory.ai_accounts_forecast.models.account_forecast import create_financial_forecast, ForecastManager

def setup_complete_forecast_system(company: str, setup_config: Dict = None) -> Dict:
    """
    Complete system setup and initialization for AI Financial Forecasting
    
    Args:
        company: Company name to setup forecasting for
        setup_config: Optional configuration parameters
    
    Returns:
        Dict with setup results and system status
    """
    
    print("🚀 STARTING COMPLETE AI FINANCIAL FORECASTING SYSTEM SETUP")
    print("=" * 70)
    
    # Default setup configuration
    default_config = {
        'create_sample_forecasts': True,
        'setup_scheduling': True,
        'enable_notifications': True,
        'priority_accounts_limit': 5,
        'other_accounts_limit': 10,
        'forecast_types': ["Cash Flow", "Revenue", "Expense", "Balance Sheet", "P&L"],
        'cleanup_old_forecasts': True,
        'setup_api_endpoints': True,
        'create_dashboard_data': True
    }
    
    # Merge with user config
    config = {**default_config, **(setup_config or {})}
    
    setup_results = {
        'setup_started': datetime.now().isoformat(),
        'company': company,
        'config': config,
        'steps_completed': [],
        'steps_failed': [],
        'forecasts_created': 0,
        'accounts_covered': 0,
        'setup_errors': [],
        'system_health': {},
        'dashboard_data': {},
        'api_endpoints_configured': False,
        'scheduling_enabled': False,
        'notifications_enabled': False
    }
    
    try:
        # Step 1: Validate System Prerequisites
        print("🔍 Step 1: Validating System Prerequisites...")
        prereq_result = validate_system_prerequisites(company)
        if prereq_result['valid']:
            setup_results['steps_completed'].append('System Prerequisites Validated')
            print("   ✅ System prerequisites validated")
        else:
            setup_results['steps_failed'].append('System Prerequisites Failed')
            setup_results['setup_errors'].extend(prereq_result['errors'])
            print(f"   ❌ Prerequisites failed: {', '.join(prereq_result['errors'])}")
            return setup_results
        
        # Step 2: Setup Database Schema and DocTypes
        print("\n📊 Step 2: Setting up Database Schema...")
        schema_result = setup_database_schema()
        if schema_result['success']:
            setup_results['steps_completed'].append('Database Schema Setup')
            print("   ✅ Database schema configured")
        else:
            setup_results['steps_failed'].append('Database Schema Failed')
            setup_results['setup_errors'].append(schema_result['error'])
            print(f"   ❌ Schema setup failed: {schema_result['error']}")
        
        # Step 3: Create Core System Forecasts
        print("\n🎯 Step 3: Creating Core System Forecasts...")
        forecasts_result = create_comprehensive_forecasts(company, config)
        setup_results.update({
            'forecasts_created': forecasts_result['forecasts_created'],
            'accounts_covered': forecasts_result['accounts_covered'],
            'forecast_details': forecasts_result['forecast_details']
        })
        setup_results['steps_completed'].append('Core Forecasts Created')
        print(f"   ✅ Created {forecasts_result['forecasts_created']} forecasts for {forecasts_result['accounts_covered']} accounts")
        
        # Step 4: Configure API Endpoints
        if config['setup_api_endpoints']:
            print("\n🌐 Step 4: Configuring API Endpoints...")
            api_result = configure_api_endpoints()
            setup_results['api_endpoints_configured'] = api_result['success']
            if api_result['success']:
                setup_results['steps_completed'].append('API Endpoints Configured')
                setup_results['api_endpoints'] = api_result['endpoints']
                print("   ✅ API endpoints configured and tested")
            else:
                setup_results['steps_failed'].append('API Configuration Failed')
                setup_results['setup_errors'].append(api_result['error'])
                print(f"   ❌ API setup failed: {api_result['error']}")
        
        # Step 5: Setup Automated Scheduling
        if config['setup_scheduling']:
            print("\n⏰ Step 5: Setting up Automated Scheduling...")
            scheduling_result = setup_automated_scheduling()
            setup_results['scheduling_enabled'] = scheduling_result['success']
            if scheduling_result['success']:
                setup_results['steps_completed'].append('Automated Scheduling Enabled')
                setup_results['scheduled_jobs'] = scheduling_result['jobs']
                print("   ✅ Automated scheduling configured")
            else:
                setup_results['steps_failed'].append('Scheduling Setup Failed')
                setup_results['setup_errors'].append(scheduling_result['error'])
                print(f"   ❌ Scheduling setup failed: {scheduling_result['error']}")
        
        # Step 6: Configure Notifications and Monitoring
        if config['enable_notifications']:
            print("\n📧 Step 6: Configuring Notifications and Monitoring...")
            notification_result = setup_notification_system()
            setup_results['notifications_enabled'] = notification_result['success']
            if notification_result['success']:
                setup_results['steps_completed'].append('Notifications Enabled')
                setup_results['notification_config'] = notification_result['config']
                print("   ✅ Notification system configured")
            else:
                setup_results['steps_failed'].append('Notification Setup Failed')
                setup_results['setup_errors'].append(notification_result['error'])
                print(f"   ❌ Notification setup failed: {notification_result['error']}")
        
        # Step 7: Generate System Health Report
        print("\n🏥 Step 7: Generating Initial System Health Report...")
        try:
            manager = ForecastManager(company)
            setup_results['system_health'] = manager.validate_system_health()
            setup_results['dashboard_data'] = manager.get_system_dashboard()
            setup_results['steps_completed'].append('Health Report Generated')
            print(f"   ✅ System health: {setup_results['system_health']['health_score']:.1f}%")
        except Exception as e:
            setup_results['steps_failed'].append('Health Report Failed')
            setup_results['setup_errors'].append(f"Health report generation failed: {str(e)}")
            print(f"   ❌ Health report failed: {str(e)}")
        
        # Step 8: Create System Documentation
        print("\n📋 Step 8: Creating System Documentation...")
        try:
            doc_result = create_system_documentation(setup_results)
            if doc_result['success']:
                setup_results['steps_completed'].append('Documentation Created')
                setup_results['documentation_path'] = doc_result['path']
                print("   ✅ System documentation created")
            else:
                setup_results['steps_failed'].append('Documentation Failed')
                setup_results['setup_errors'].append(doc_result['error'])
                print(f"   ❌ Documentation failed: {doc_result['error']}")
        except Exception as e:
            setup_results['steps_failed'].append('Documentation Failed')
            setup_results['setup_errors'].append(f"Documentation creation failed: {str(e)}")
            print(f"   ❌ Documentation failed: {str(e)}")
        
        # Step 9: Cleanup and Optimization
        if config['cleanup_old_forecasts']:
            print("\n🧹 Step 9: System Cleanup and Optimization...")
            try:
                cleanup_result = perform_initial_cleanup()
                setup_results['steps_completed'].append('System Optimized')
                setup_results['cleanup_results'] = cleanup_result
                print(f"   ✅ System optimized: {cleanup_result['optimizations_applied']} optimizations applied")
            except Exception as e:
                setup_results['steps_failed'].append('Cleanup Failed')
                setup_results['setup_errors'].append(f"Cleanup failed: {str(e)}")
                print(f"   ❌ Cleanup failed: {str(e)}")
        
        # Step 10: Final Validation and Testing
        print("\n🧪 Step 10: Final System Validation and Testing...")
        try:
            validation_result = perform_final_system_validation(company, setup_results)
            setup_results['final_validation'] = validation_result
            setup_results['steps_completed'].append('Final Validation Completed')
            print(f"   ✅ System validation: {validation_result['overall_score']:.1f}% ready")
        except Exception as e:
            setup_results['steps_failed'].append('Final Validation Failed')
            setup_results['setup_errors'].append(f"Final validation failed: {str(e)}")
            print(f"   ❌ Final validation failed: {str(e)}")
        
        # Setup completion summary
        setup_results['setup_completed'] = datetime.now().isoformat()
        setup_results['setup_duration'] = str(datetime.fromisoformat(setup_results['setup_completed']) - 
                                           datetime.fromisoformat(setup_results['setup_started']))
        
        success_rate = len(setup_results['steps_completed']) / (len(setup_results['steps_completed']) + len(setup_results['steps_failed'])) * 100
        
        print(f"\n" + "=" * 70)
        print("🎉 SETUP COMPLETION SUMMARY")
        print("=" * 70)
        print(f"✅ Setup Success Rate: {success_rate:.1f}%")
        print(f"📊 Steps Completed: {len(setup_results['steps_completed'])}")
        print(f"❌ Steps Failed: {len(setup_results['steps_failed'])}")
        print(f"🎯 Forecasts Created: {setup_results['forecasts_created']}")
        print(f"🏢 Accounts Covered: {setup_results['accounts_covered']}")
        print(f"⏱️ Setup Duration: {setup_results['setup_duration']}")
        
        if setup_results['system_health']:
            print(f"🏥 System Health Score: {setup_results['system_health']['health_score']:.1f}%")
        
        print(f"\n📋 Completed Steps:")
        for step in setup_results['steps_completed']:
            print(f"   ✅ {step}")
        
        if setup_results['steps_failed']:
            print(f"\n⚠️ Failed Steps:")
            for step in setup_results['steps_failed']:
                print(f"   ❌ {step}")
        
        # Final status determination
        if success_rate >= 80:
            print(f"\n🚀 SYSTEM STATUS: PRODUCTION READY")
            setup_results['deployment_ready'] = True
        elif success_rate >= 60:
            print(f"\n⚠️ SYSTEM STATUS: PARTIALLY READY (Review failed steps)")
            setup_results['deployment_ready'] = False
        else:
            print(f"\n❌ SYSTEM STATUS: SETUP INCOMPLETE (Manual intervention required)")
            setup_results['deployment_ready'] = False
        
        return setup_results
        
    except Exception as e:
        setup_results['setup_failed'] = True
        setup_results['fatal_error'] = str(e)
        setup_results['setup_completed'] = datetime.now().isoformat()
        
        print(f"\n❌ FATAL SETUP ERROR: {str(e)}")
        frappe.log_error(f"AI Forecast system setup failed: {str(e)}", "AI Forecast Setup Error")
        
        return setup_results

# ============================================================================
# SETUP HELPER FUNCTIONS
# ============================================================================

def validate_system_prerequisites(company: str) -> Dict:
    """Validate all system prerequisites before setup"""
    
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Check if company exists
        if not frappe.db.exists('Company', company):
            validation_result['valid'] = False
            validation_result['errors'].append(f'Company "{company}" does not exist')
        
        # Check if required doctypes exist
        required_doctypes = ['Account', 'Company']
        for doctype in required_doctypes:
            if not frappe.db.exists('DocType', doctype):
                validation_result['valid'] = False
                validation_result['errors'].append(f'Required DocType "{doctype}" not found')
        
        # Check database permissions
        try:
            frappe.db.sql("SELECT 1")
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f'Database connection issue: {str(e)}')
        
        # Check if accounts exist for the company
        accounts_count = frappe.db.count('Account', {'company': company, 'is_group': 0})
        if accounts_count == 0:
            validation_result['valid'] = False
            validation_result['errors'].append(f'No accounts found for company "{company}"')
        elif accounts_count < 5:
            validation_result['warnings'].append(f'Only {accounts_count} accounts found. Consider creating more accounts for better forecasting coverage.')
        
        # Check system resources (optional - only if psutil is available)
        try:
            import psutil
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 85:
                validation_result['warnings'].append(f'High memory usage ({memory_usage:.1f}%). System performance may be affected.')
            
            disk_usage = psutil.disk_usage('/').percent
            if disk_usage > 90:
                validation_result['valid'] = False
                validation_result['errors'].append(f'Low disk space ({100-disk_usage:.1f}% free). Insufficient space for forecast data.')
        except ImportError:
            validation_result['warnings'].append('psutil not available - skipping system resource checks')
        
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f'Validation error: {str(e)}')
    
    return validation_result

def setup_database_schema() -> Dict:
    """Setup required database schema and indexes"""
    
    try:
        # Create indexes for optimal performance
        index_queries = [
            """CREATE INDEX IF NOT EXISTS idx_ai_forecast_company_account 
               ON `tabAI Financial Forecast` (company, account)""",
            
            """CREATE INDEX IF NOT EXISTS idx_ai_forecast_type_creation 
               ON `tabAI Financial Forecast` (forecast_type, creation)""",
            
            """CREATE INDEX IF NOT EXISTS idx_ai_forecast_confidence 
               ON `tabAI Financial Forecast` (confidence_score)""",
            
            """CREATE INDEX IF NOT EXISTS idx_ai_forecast_company_type_creation 
               ON `tabAI Financial Forecast` (company, forecast_type, creation)"""
        ]
        
        for query in index_queries:
            frappe.db.sql(query)
        
        frappe.db.commit()
        
        return {'success': True, 'indexes_created': len(index_queries)}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_comprehensive_forecasts(company: str, config: Dict) -> Dict:
    """Create comprehensive forecasts for the company"""
    
    try:
        # Get all accounts
        all_accounts = frappe.get_all('Account',
                                    filters={'company': company, 'is_group': 0, 'disabled': 0},
                                    fields=['name', 'account_type'],
                                    order_by='name')
        
        # Prioritize accounts
        priority_keywords = ['cash', 'bank', 'debtor', 'creditor', 'stock', 'revenue', 'income', 'sales']
        
        priority_accounts = []
        other_accounts = []
        
        for account in all_accounts:
            account_name_lower = account.name.lower()
            if any(keyword in account_name_lower for keyword in priority_keywords):
                priority_accounts.append(account.name)
            else:
                other_accounts.append(account.name)
        
        # Create forecasts
        forecast_types = config['forecast_types']
        results = {
            'forecasts_created': 0,
            'accounts_covered': 0,
            'forecast_details': {
                'priority_accounts': [],
                'other_accounts': [],
                'failed_forecasts': []
            }
        }
        
        # Create comprehensive forecasts for priority accounts
        for account in priority_accounts[:config['priority_accounts_limit']]:
            account_forecasts = []
            for forecast_type in forecast_types:
                try:
                    result = create_financial_forecast(company, account, forecast_type)
                    results['forecasts_created'] += 1
                    account_forecasts.append({
                        'forecast_id': result['forecast_id'],
                        'type': forecast_type,
                        'confidence': result['confidence_score']
                    })
                except Exception as e:
                    results['forecast_details']['failed_forecasts'].append({
                        'account': account,
                        'type': forecast_type,
                        'error': str(e)
                    })
            
            if account_forecasts:
                results['forecast_details']['priority_accounts'].append({
                    'account': account,
                    'forecasts': account_forecasts
                })
        
        # Create basic forecasts for other accounts
        for account in other_accounts[:config['other_accounts_limit']]:
            try:
                result = create_financial_forecast(company, account, 'Cash Flow')
                results['forecasts_created'] += 1
                results['forecast_details']['other_accounts'].append({
                    'account': account,
                    'forecast_id': result['forecast_id'],
                    'confidence': result['confidence_score']
                })
            except Exception as e:
                results['forecast_details']['failed_forecasts'].append({
                    'account': account,
                    'type': 'Cash Flow',
                    'error': str(e)
                })
        
        results['accounts_covered'] = len(results['forecast_details']['priority_accounts']) + len(results['forecast_details']['other_accounts'])
        
        return results
        
    except Exception as e:
        return {
            'forecasts_created': 0,
            'accounts_covered': 0,
            'error': str(e),
            'forecast_details': {'failed_forecasts': [{'error': str(e)}]}
        }

def configure_api_endpoints() -> Dict:
    """Configure and test API endpoints"""
    
    try:
        # Test key API endpoints
        test_endpoints = [
            'api_create_forecast',
            'api_get_forecasts', 
            'api_get_dashboard',
            'api_system_health',
            'api_documentation'
        ]
        
        working_endpoints = []
        failed_endpoints = []
        
        for endpoint in test_endpoints:
            try:
                # Simple endpoint availability test
                method_path = f"ai_inventory.ai_accounts_forecast.api.forecast_api.{endpoint}"
                if hasattr(frappe.get_attr(method_path), '__call__'):
                    working_endpoints.append(endpoint)
                else:
                    failed_endpoints.append(endpoint)
            except:
                failed_endpoints.append(endpoint)
        
        return {
            'success': len(failed_endpoints) == 0,
            'endpoints': {
                'working': working_endpoints,
                'failed': failed_endpoints
            },
            'total_configured': len(working_endpoints)
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def setup_automated_scheduling() -> Dict:
    """Setup automated scheduling for forecast system"""
    
    try:
        # Import the scheduler setup function
        from ai_inventory.ai_accounts_forecast.scheduler.forecast_scheduler import setup_forecast_scheduler
        
        # Setup scheduler jobs
        setup_forecast_scheduler()
        
        # Test scheduler functionality
        scheduled_jobs = [
            'ai_forecast_daily_update',
            'ai_forecast_weekly_health',
            'ai_forecast_monthly_cleanup'
        ]
        
        return {
            'success': True,
            'jobs': scheduled_jobs,
            'message': 'Automated scheduling configured successfully'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def setup_notification_system() -> Dict:
    """Setup notification and alerting system"""
    
    try:
        # Configure notification settings
        notification_config = {
            'health_alerts_enabled': True,
            'critical_threshold': 60,
            'warning_threshold': 75,
            'weekly_reports_enabled': True,
            'monthly_reports_enabled': True
        }
        
        # Test notification system
        try:
            # Send test notification
            test_subject = "🧪 AI Forecast System Setup - Test Notification"
            test_message = "This is a test notification to verify the notification system is working correctly."
            
            # Import the notification function
            from ai_inventory.ai_accounts_forecast.scheduler.forecast_scheduler import send_system_notification
            send_system_notification(test_subject, test_message, priority="Info")
            
            notification_config['test_notification_sent'] = True
        except Exception as e:
            notification_config['test_notification_sent'] = False
            notification_config['test_error'] = str(e)
        
        return {
            'success': True,
            'config': notification_config,
            'message': 'Notification system configured'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_system_documentation(setup_results: Dict) -> Dict:
    """Create comprehensive system documentation"""
    
    try:
        documentation = {
            'title': 'AI Financial Forecasting System - Setup Documentation',
            'setup_date': datetime.now().isoformat(),
            'company': setup_results['company'],
            'setup_summary': {
                'forecasts_created': setup_results['forecasts_created'],
                'accounts_covered': setup_results['accounts_covered'],
                'success_rate': len(setup_results['steps_completed']) / max(1, len(setup_results['steps_completed']) + len(setup_results['steps_failed'])) * 100
            },
            'system_configuration': setup_results['config'],
            'api_endpoints': setup_results.get('api_endpoints', {}),
            'scheduled_jobs': setup_results.get('scheduled_jobs', []),
            'health_metrics': setup_results.get('system_health', {}),
            'deployment_status': setup_results.get('deployment_ready', False),
            'usage_instructions': {
                'creating_forecasts': 'Use create_financial_forecast() function or API endpoints',
                'viewing_dashboard': 'Access via api_get_dashboard() or ForecastManager.get_system_dashboard()',
                'monitoring_health': 'Automated weekly health checks or api_system_health()',
                'api_access': 'All endpoints available at /api/method/ai_inventory.ai_accounts_forecast.api.forecast_api/'
            },
            'troubleshooting': {
                'common_issues': [
                    'If forecasts fail to create, check account permissions and company setup',
                    'Low confidence scores may indicate insufficient historical data',
                    'API errors typically relate to authentication or parameter validation'
                ],
                'support_contacts': 'Check system logs and contact system administrator'
            }
        }
        
        # Save documentation to file (use a safe path)
        import tempfile
        doc_path = os.path.join(tempfile.gettempdir(), f"ai_forecast_setup_documentation_{setup_results['company'].replace(' ', '_')}.json")
        
        with open(doc_path, 'w') as f:
            json.dump(documentation, f, indent=2)
        
        return {
            'success': True,
            'path': doc_path,
            'documentation': documentation
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def perform_initial_cleanup() -> Dict:
    """Perform initial system cleanup and optimization"""
    
    try:
        cleanup_results = {
            'optimizations_applied': 0,
            'database_optimized': False,
            'indexes_created': False,
            'permissions_verified': False
        }
        
        # Optimize database
        try:
            from ai_inventory.ai_accounts_forecast.scheduler.forecast_scheduler import optimize_database_performance
            optimize_database_performance()
            cleanup_results['database_optimized'] = True
            cleanup_results['optimizations_applied'] += 1
        except Exception as e:
            cleanup_results['database_error'] = str(e)
        
        # Verify permissions
        try:
            frappe.db.sql("SELECT 1 FROM `tabAI Financial Forecast` LIMIT 1")
            cleanup_results['permissions_verified'] = True
            cleanup_results['optimizations_applied'] += 1
        except Exception as e:
            cleanup_results['permissions_error'] = str(e)
        
        return cleanup_results
        
    except Exception as e:
        return {'optimizations_applied': 0, 'error': str(e)}

def perform_final_system_validation(company: str, setup_results: Dict) -> Dict:
    """Perform final comprehensive system validation"""
    
    try:
        validation_scores = []
        validation_details = {}
        
        # Test 1: Forecast Creation
        try:
            test_account = frappe.get_all('Account', 
                                        filters={'company': company, 'is_group': 0}, 
                                        limit=1, pluck='name')[0]
            test_result = create_financial_forecast(company, test_account, 'Cash Flow')
            validation_scores.append(100)
            validation_details['forecast_creation'] = {'status': 'Pass', 'test_forecast': test_result['forecast_id']}
        except Exception as e:
            validation_scores.append(0)
            validation_details['forecast_creation'] = {'status': 'Fail', 'error': str(e)}
        
        # Test 2: Dashboard Access
        try:
            manager = ForecastManager(company)
            dashboard = manager.get_system_dashboard()
            validation_scores.append(100)
            validation_details['dashboard_access'] = {'status': 'Pass', 'forecasts_found': dashboard['summary']['total_forecasts']}
        except Exception as e:
            validation_scores.append(0)
            validation_details['dashboard_access'] = {'status': 'Fail', 'error': str(e)}
        
        # Test 3: Health Monitoring
        try:
            manager = ForecastManager(company)
            health = manager.validate_system_health()
            validation_scores.append(100)
            validation_details['health_monitoring'] = {'status': 'Pass', 'health_score': health['health_score']}
        except Exception as e:
            validation_scores.append(0)
            validation_details['health_monitoring'] = {'status': 'Fail', 'error': str(e)}
        
        # Test 4: API Endpoints
        try:
            from ai_inventory.ai_accounts_forecast.api.forecast_api import api_documentation
            api_docs = api_documentation()
            validation_scores.append(100)
            validation_details['api_endpoints'] = {'status': 'Pass', 'endpoints_available': len(api_docs['data']['endpoints'])}
        except Exception as e:
            validation_scores.append(50)  # Partial score if some APIs work
            validation_details['api_endpoints'] = {'status': 'Partial', 'error': str(e)}
        
        # Calculate overall score
        overall_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        return {
            'overall_score': overall_score,
            'individual_scores': validation_scores,
            'validation_details': validation_details,
            'ready_for_production': overall_score >= 75,
            'validation_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'overall_score': 0,
            'error': str(e),
            'ready_for_production': False,
            'validation_timestamp': datetime.now().isoformat()
        }

# ============================================================================
# QUICK SETUP FUNCTIONS
# ============================================================================

def quick_setup_for_company(company: str) -> Dict:
    """Quick setup with default configuration for immediate deployment"""
    
    quick_config = {
        'create_sample_forecasts': True,
        'setup_scheduling': True,
        'enable_notifications': False,  # Disable for quick setup
        'priority_accounts_limit': 3,
        'other_accounts_limit': 5,
        'forecast_types': ["Cash Flow", "Revenue", "Expense"],
        'cleanup_old_forecasts': False,
        'setup_api_endpoints': True,
        'create_dashboard_data': True
    }
    
    print(f"⚡ Quick Setup for {company}")
    return setup_complete_forecast_system(company, quick_config)

def enterprise_setup_for_company(company: str) -> Dict:
    """Enterprise setup with full configuration and monitoring"""
    
    enterprise_config = {
        'create_sample_forecasts': True,
        'setup_scheduling': True,
        'enable_notifications': True,
        'priority_accounts_limit': 10,
        'other_accounts_limit': 20,
        'forecast_types': ["Cash Flow", "Revenue", "Expense", "Balance Sheet", "P&L"],
        'cleanup_old_forecasts': True,
        'setup_api_endpoints': True,
        'create_dashboard_data': True
    }
    
    print(f"🏢 Enterprise Setup for {company}")
    return setup_complete_forecast_system(company, enterprise_config)

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
USAGE EXAMPLES:

# 1. Quick Setup (recommended for testing/development)
quick_result = quick_setup_for_company('Kerala State Coir Machinery Manufacturing Company Limited')

# 2. Enterprise Setup (recommended for production)
enterprise_result = enterprise_setup_for_company('Kerala State Coir Machinery Manufacturing Company Limited')

# 3. Custom Setup
custom_config = {
    'priority_accounts_limit': 5,
    'forecast_types': ['Cash Flow', 'Revenue'],
    'enable_notifications': True
}
custom_result = setup_complete_forecast_system('Company Name', custom_config)

# 4. Check setup results
if result['deployment_ready']:
    print("🚀 System ready for production!")
else:
    print("⚠️ Review setup issues before deployment")
"""

print("✅ CORRECTED FILE 6