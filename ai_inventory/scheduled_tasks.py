# ai_inventory/scheduled_tasks.py
# CREATE THIS NEW FILE

import frappe
from frappe.utils import now, nowdate, add_days

def real_time_stock_monitor():
    """Real-time stock monitoring (every 5 minutes)"""
    try:
        # Get critical alerts
        critical_alerts = frappe.db.sql("""
            SELECT 
                item_code, warehouse, company, current_stock, reorder_level
            FROM `tabAI Inventory Forecast`
            WHERE reorder_alert = 1 
            AND movement_type IN ('Fast Moving', 'Critical')
            AND current_stock <= reorder_level * 0.5
            LIMIT 10
        """, as_dict=True)
        
        if critical_alerts:
            # Send real-time notifications
            for alert in critical_alerts:
                try:
                    frappe.publish_realtime(
                        event="critical_stock_alert",
                        message={
                            "item_code": alert.item_code,
                            "warehouse": alert.warehouse,
                            "company": alert.company,
                            "current_stock": alert.current_stock,
                            "reorder_level": alert.reorder_level
                        },
                        room="stock_managers"
                    )
                except:
                    pass  # Skip if realtime fails
        
        frappe.logger().info(f"Real-time monitor: {len(critical_alerts)} critical alerts")
        
    except Exception as e:
        frappe.log_error(f"Real-time stock monitor failed: {str(e)}")

def hourly_critical_stock_check():
    """Hourly critical stock check"""
    try:
        # Update stock levels for critical items
        critical_forecasts = frappe.get_all("AI Inventory Forecast",
            filters={
                "reorder_alert": 1,
                "movement_type": ["in", ["Fast Moving", "Critical"]]
            },
            fields=["name", "item_code", "warehouse", "company"],
            limit=50
        )
        
        updated_count = 0
        for forecast in critical_forecasts:
            try:
                doc = frappe.get_doc("AI Inventory Forecast", forecast.name)
                doc.update_current_stock_safe()
                updated_count += 1
            except:
                pass
        
        frappe.logger().info(f"Hourly check: Updated {updated_count} critical stock items")
        
    except Exception as e:
        frappe.log_error(f"Hourly critical stock check failed: {str(e)}")

def daily_ai_forecast():
    """Daily AI forecast update"""
    try:
        # Get all companies
        companies = frappe.get_all("Company", filters={}, pluck="name")
        
        for company in companies:
            try:
                # Queue sync for each company
                frappe.enqueue(
                    'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now',
                    company=company,
                    queue='long',
                    timeout=3600,  # 1 hour timeout per company
                    is_async=True
                )
                
                frappe.logger().info(f"Queued daily AI forecast sync for company: {company}")
                
            except Exception as e:
                frappe.log_error(f"Failed to queue daily forecast sync for {company}: {str(e)}")
        
        return {"status": "success", "message": f"Queued daily AI forecast sync for {len(companies)} companies"}
        
    except Exception as e:
        frappe.log_error(f"Daily AI forecast failed: {str(e)}")
        return {"status": "error", "message": str(e)}

def weekly_forecast_analysis():
    """Weekly forecast analysis and optimization"""
    try:
        # Get forecast accuracy metrics
        accuracy_stats = frappe.db.sql("""
            SELECT 
                company,
                COUNT(*) as total_forecasts,
                AVG(confidence_score) as avg_confidence,
                COUNT(CASE WHEN reorder_alert = 1 THEN 1 END) as total_alerts
            FROM `tabAI Inventory Forecast`
            WHERE last_forecast_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY company
        """, as_dict=True)
        
        # Log weekly summary
        for stat in accuracy_stats:
            frappe.logger().info(
                f"Weekly forecast summary for {stat.company}: "
                f"{stat.total_forecasts} forecasts, "
                f"{stat.avg_confidence:.1f}% avg confidence, "
                f"{stat.total_alerts} alerts"
            )
        
        return {"status": "success", "companies_analyzed": len(accuracy_stats)}
        
    except Exception as e:
        frappe.log_error(f"Weekly forecast analysis failed: {str(e)}")
        return {"status": "error", "message": str(e)}

def optimize_forecast_performance():
    """Monthly forecast performance optimization"""
    try:
        # Archive old forecast details to improve performance
        cutoff_date = add_days(nowdate(), -90)
        
        archived_count = frappe.db.sql("""
            UPDATE `tabAI Inventory Forecast`
            SET forecast_details = 'Archived - details cleared for performance'
            WHERE last_forecast_date < %s
            AND LENGTH(forecast_details) > 1000
        """, (cutoff_date,))
        
        frappe.db.commit()
        
        frappe.logger().info(f"Monthly optimization: Archived details for performance")
        
        return {"status": "success", "message": "Monthly optimization completed"}
        
    except Exception as e:
        frappe.log_error(f"Monthly optimization failed: {str(e)}")
        return {"status": "error", "message": str(e)}

def cleanup_old_forecast_data():
    """Monthly cleanup of old forecast data"""
    try:
        # Clean up very old error logs related to AI Inventory
        old_date = add_days(nowdate(), -30)
        
        frappe.db.sql("""
            DELETE FROM `tabError Log`
            WHERE creation < %s
            AND error LIKE '%AI Inventory%'
        """, (old_date,))
        
        frappe.db.commit()
        
        frappe.logger().info("Monthly cleanup: Removed old AI Inventory error logs")
        
        return {"status": "success", "message": "Monthly cleanup completed"}
        
    except Exception as e:
        frappe.log_error(f"Monthly cleanup failed: {str(e)}")
        return {"status": "error", "message": str(e)}