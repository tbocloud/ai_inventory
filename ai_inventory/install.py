# ai_inventory/install.py
# UPDATED VERSION - Replace your existing install.py

import frappe
import subprocess
import sys
import os

def after_install():
    """Run after app installation - FIXED VERSION"""
    try:
        print("Starting AI Inventory post-installation setup...")
        
        # Install required Python packages
        install_required_packages()
        
        # Create necessary custom fields FIRST
        create_custom_fields()
        
        # Setup scheduler
        setup_scheduler()
        
        # Create sample AI Settings if not exists
        create_ai_settings()
        
        print("AI Inventory installation completed successfully!")
        
    except Exception as e:
        frappe.log_error(f"AI Inventory installation failed: {str(e)}")
        print(f"Installation failed: {str(e)}")

def install_required_packages():
    """Install required Python packages"""
    packages = [
        'numpy',
        'pandas', 
        'scikit-learn'
    ]
    
    print("Installing required Python packages...")
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {str(e)}")
            frappe.log_error(f"Package installation failed: {package} - {str(e)}")
        except Exception as e:
            print(f"✗ Error installing {package}: {str(e)}")

def create_custom_fields():
    """Create custom fields for enhanced functionality - FIXED"""
    try:
        print("Creating custom fields...")
        
        # Custom fields for AI Inventory Forecast - THE MOST IMPORTANT ONES
        ai_forecast_fields = [
            {
                "fieldname": "preferred_supplier",
                "label": "Preferred Supplier",
                "fieldtype": "Link",
                "options": "Supplier",
                "insert_after": "supplier",
                "read_only": 1,
                "description": "ML-analyzed preferred supplier based on purchase history"
            },
            {
                "fieldname": "auto_create_purchase_order",
                "label": "Auto Create Purchase Order",
                "fieldtype": "Check",
                "insert_after": "reorder_alert",
                "default": 0,
                "description": "Automatically create purchase order when reorder alert is triggered"
            }
        ]
        
        # Create AI Inventory Forecast fields first (most critical)
        for field in ai_forecast_fields:
            create_single_custom_field("AI Inventory Forecast", field)
        
        # Custom fields for Supplier
        supplier_fields = [
            {
                "fieldname": "supplier_segment",
                "label": "ML Supplier Segment",
                "fieldtype": "Select",
                "options": "\nStrategic\nPreferred\nApproved\nCaution\nCritical",
                "insert_after": "supplier_group",
                "read_only": 1,
                "description": "ML-determined supplier classification"
            },
            {
                "fieldname": "risk_score",
                "label": "Risk Score",
                "fieldtype": "Int",
                "insert_after": "supplier_segment",
                "read_only": 1,
                "description": "Credit risk score calculated by ML (0-100, lower is better)"
            },
            {
                "fieldname": "deal_score",
                "label": "Deal Score",
                "fieldtype": "Int",
                "insert_after": "risk_score",
                "read_only": 1,
                "description": "Deal quality score calculated by ML (0-100, higher is better)"
            },
            {
                "fieldname": "supplier_lifetime_value",
                "label": "Supplier Lifetime Value",
                "fieldtype": "Currency",
                "insert_after": "deal_score",
                "read_only": 1,
                "description": "ML-calculated long-term value of supplier relationship"
            },
            {
                "fieldname": "last_ml_update",
                "label": "Last ML Update",
                "fieldtype": "Datetime",
                "insert_after": "supplier_lifetime_value",
                "read_only": 1,
                "description": "Timestamp of most recent ML score calculation"
            }
        ]
        
        # Create Supplier fields
        for field in supplier_fields:
            create_single_custom_field("Supplier", field)
        
        print("✓ Custom fields created successfully")
        
        # Clear cache after creating fields
        frappe.clear_cache()
        
    except Exception as e:
        print(f"✗ Custom fields creation failed: {str(e)}")
        frappe.log_error(f"Custom fields creation failed: {str(e)}")

def create_single_custom_field(doctype, field_data):
    """Create a single custom field with error handling"""
    try:
        # Check if field already exists
        existing_field = frappe.db.exists("Custom Field", {
            "dt": doctype,
            "fieldname": field_data["fieldname"]
        })
        
        if not existing_field:
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                "fieldname": field_data["fieldname"],
                "label": field_data["label"],
                "fieldtype": field_data["fieldtype"],
                "insert_after": field_data.get("insert_after"),
                "options": field_data.get("options"),
                "read_only": field_data.get("read_only", 0),
                "default": field_data.get("default"),
                "description": field_data.get("description")
            })
            custom_field.insert()
            frappe.db.commit()  # Commit immediately after each field
            print(f"✓ Created custom field: {doctype}.{field_data['fieldname']}")
        else:
            print(f"✓ Custom field already exists: {doctype}.{field_data['fieldname']}")
            
    except Exception as e:
        print(f"✗ Failed to create custom field {doctype}.{field_data['fieldname']}: {str(e)}")
        frappe.log_error(f"Custom field creation failed: {doctype}.{field_data['fieldname']} - {str(e)}")

def setup_scheduler():
    """Enable scheduler for AI Inventory tasks"""
    try:
        print("Setting up scheduler...")
        
        # Enable scheduler if not already enabled
        scheduler_enabled = frappe.db.get_single_value("System Settings", "enable_scheduler")
        if not scheduler_enabled:
            frappe.db.set_value("System Settings", "System Settings", "enable_scheduler", 1)
            print("✓ Scheduler enabled")
        else:
            print("✓ Scheduler already enabled")
            
    except Exception as e:
        print(f"✗ Scheduler setup failed: {str(e)}")
        frappe.log_error(f"Scheduler setup failed: {str(e)}")

def create_ai_settings():
    """Create AI Settings single doctype if not exists"""
    try:
        print("Creating AI Settings...")
        
        # Check if AI Settings already exists
        if not frappe.db.exists("AI Settings", "AI Settings"):
            ai_settings = frappe.get_doc({
                "doctype": "AI Settings",
                "auto_sync_enabled": 1,
                "sync_frequency": "Daily",
                "auto_refresh_status": 1,
                "forecast_period_days": 30,
                "default_lead_time_days": 14,
                "confidence_threshold": 70,
                "auto_create_po_threshold": 85,
                "performance_notes": "AI Inventory Forecast system initialized"
            })
            ai_settings.insert()
            print("✓ AI Settings created successfully")
        else:
            print("✓ AI Settings already exists")
            
    except Exception as e:
        print(f"✗ AI Settings creation failed: {str(e)}")
        frappe.log_error(f"AI Settings creation failed: {str(e)}")

def before_uninstall():
    """Clean up before app uninstallation"""
    try:
        print("Cleaning up AI Inventory data...")
        
        # Remove custom fields
        remove_custom_fields()
        
        print("✓ AI Inventory cleanup completed")
        
    except Exception as e:
        print(f"✗ Cleanup failed: {str(e)}")
        frappe.log_error(f"AI Inventory cleanup failed: {str(e)}")

def remove_custom_fields():
    """Remove custom fields created by the app"""
    try:
        # Remove custom fields for Purchase Order Item, Supplier, and AI Inventory Forecast
        custom_fields = frappe.get_all("Custom Field", 
            filters={
                "dt": ["in", ["Purchase Order Item", "Supplier", "AI Inventory Forecast"]],
                "fieldname": ["in", [
                    "predicted_price", "price_confidence", 
                    "supplier_segment", "risk_score", "deal_score", 
                    "supplier_lifetime_value", "last_ml_update",
                    "auto_create_purchase_order", "preferred_supplier"
                ]]
            })
        
        for field in custom_fields:
            frappe.delete_doc("Custom Field", field.name)
            
        print("✓ Custom fields removed")
        
    except Exception as e:
        print(f"✗ Custom fields removal failed: {str(e)}")

# Manual field creation function that can be called separately
@frappe.whitelist()
def create_missing_fields_manually():
    """Create missing fields manually - can be called from console"""
    try:
        print("🔧 Manually creating missing AI Inventory Forecast fields...")
        
        # Critical fields for AI Inventory Forecast
        critical_fields = [
            {
                "fieldname": "preferred_supplier",
                "label": "Preferred Supplier", 
                "fieldtype": "Link",
                "options": "Supplier",
                "insert_after": "supplier",
                "read_only": 1,
                "description": "ML-analyzed preferred supplier"
            },
            {
                "fieldname": "auto_create_purchase_order",
                "label": "Auto Create Purchase Order",
                "fieldtype": "Check", 
                "insert_after": "reorder_alert",
                "default": 0,
                "description": "Auto-create PO when reorder alert triggers"
            }
        ]
        
        created_count = 0
        for field in critical_fields:
            try:
                existing = frappe.db.exists("Custom Field", {
                    "dt": "AI Inventory Forecast",
                    "fieldname": field["fieldname"]
                })
                
                if not existing:
                    custom_field = frappe.get_doc({
                        "doctype": "Custom Field",
                        "dt": "AI Inventory Forecast",
                        **field
                    })
                    custom_field.insert()
                    created_count += 1
                    print(f"✅ Created field: {field['fieldname']}")
                else:
                    print(f"✅ Field already exists: {field['fieldname']}")
                    
            except Exception as e:
                print(f"❌ Failed to create {field['fieldname']}: {str(e)}")
        
        frappe.db.commit()
        frappe.clear_cache(doctype="AI Inventory Forecast")
        
        return {
            "status": "success",
            "created": created_count,
            "message": f"Created {created_count} fields successfully"
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }