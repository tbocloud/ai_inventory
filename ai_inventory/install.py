# ai_inventory/install.py
# COMPLETE FIXED VERSION - Replace your entire existing file with this

import frappe
import subprocess
import sys
import os
import importlib.util

def before_install():
    """Install packages BEFORE app installation starts"""
    try:
        print("🚀 AI Inventory: Installing required packages before app installation...")
        
        # Install packages before any DocType processing
        install_required_packages()
        
        print("✅ Pre-installation package setup completed!")
        
    except Exception as e:
        print(f"❌ Pre-installation failed: {str(e)}")
        frappe.log_error(f"AI Inventory pre-installation failed: {str(e)}")
        # Don't raise exception here to allow installation to continue

def after_install():
    """Run after app installation - COMPLETE VERSION"""
    try:
        print("Starting AI Inventory post-installation setup...")
        
        # Verify packages are installed (reinstall if needed)
        verify_and_reinstall_packages()
        
        # Create necessary custom fields
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
    """Install required Python packages with better error handling"""
    packages = [
        'numpy>=1.21.0',
        'pandas>=1.3.0', 
        'scikit-learn>=1.0.0'
    ]
    
    print("Installing required Python packages...")
    
    # Check if we're in a virtual environment
    virtual_env = os.environ.get('VIRTUAL_ENV')
    if virtual_env:
        print(f"✓ Using virtual environment: {virtual_env}")
    
    failed_packages = []
    
    for package in packages:
        package_name = package.split('>=')[0].split('==')[0]  # Extract package name
        try:
            # First check if package is already installed
            if is_package_installed(package_name):
                print(f"✓ {package_name} already installed")
                continue
                
            print(f"Installing {package}...")
            
            # Use the same Python executable that's running Frappe
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--upgrade", "--quiet"
            ], capture_output=True, text=True, check=True, timeout=300)
            
            print(f"✓ {package} installed successfully")
            
            # Verify installation immediately
            if not is_package_installed(package_name):
                raise Exception(f"Package {package_name} installation verification failed")
                
        except subprocess.TimeoutExpired:
            error_msg = f"Installation timeout for {package}"
            print(f"✗ {error_msg}")
            failed_packages.append(package_name)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install {package}: {e.stderr if e.stderr else str(e)}"
            print(f"✗ {error_msg}")
            failed_packages.append(package_name)
            frappe.log_error(f"Package installation failed: {package} - {error_msg}")
            
        except Exception as e:
            error_msg = f"Error installing {package}: {str(e)}"
            print(f"✗ {error_msg}")
            failed_packages.append(package_name)
            frappe.log_error(error_msg)
    
    if failed_packages:
        print(f"\n⚠️  Warning: Failed to install packages: {', '.join(failed_packages)}")
        print("Manual installation commands:")
        for pkg in failed_packages:
            print(f"  ./env/bin/pip install {pkg} --upgrade")

def verify_and_reinstall_packages():
    """Verify packages and reinstall if needed"""
    print("Verifying package installations...")
    
    packages_to_check = {
        'numpy': 'np',
        'pandas': 'pd', 
        'scikit-learn': 'sklearn'
    }
    
    missing_packages = []
    
    for package, import_name in packages_to_check.items():
        try:
            if import_name == 'sklearn':
                import sklearn
                print(f"✓ {package} verified (version: {sklearn.__version__})")
            elif import_name == 'np':
                import numpy as np
                print(f"✓ {package} verified (version: {np.__version__})")
            elif import_name == 'pd':
                import pandas as pd
                print(f"✓ {package} verified (version: {pd.__version__})")
        except ImportError:
            print(f"✗ {package} not available")
            missing_packages.append(package)
        except Exception as e:
            print(f"✗ {package} verification error: {str(e)}")
            missing_packages.append(package)
    
    # Reinstall missing packages
    if missing_packages:
        print(f"Reinstalling missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package, "--upgrade", "--force-reinstall"
                ], check=True, timeout=180)
                print(f"✓ {package} reinstalled")
            except Exception as e:
                print(f"✗ Failed to reinstall {package}: {str(e)}")

def is_package_installed(package_name):
    """Check if a Python package is installed and importable"""
    try:
        # Handle package name variations
        if package_name == 'scikit-learn':
            import sklearn
            return True
        else:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
    except ImportError:
        return False
    except Exception:
        return False

def create_custom_fields():
    """Create custom fields for enhanced functionality"""
    try:
        print("Creating custom fields...")
        
        # Set flag to indicate we're in installation
        frappe.flags.in_install = True
        
        # Custom fields for AI Inventory Forecast
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
            },
            {
                "fieldname": "analysis_method",
                "label": "Analysis Method",
                "fieldtype": "Data",
                "insert_after": "confidence_score",
                "read_only": 1,
                "description": "Method used for forecast analysis"
            }
        ]
        
        # Create AI Inventory Forecast fields
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
        
        # Clear installation flag
        frappe.flags.in_install = False
        
        # Clear cache after creating fields
        frappe.clear_cache()
        
    except Exception as e:
        frappe.flags.in_install = False
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
            frappe.db.commit()
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
        remove_custom_fields()
        print("✓ AI Inventory cleanup completed")
        
    except Exception as e:
        print(f"✗ Cleanup failed: {str(e)}")
        frappe.log_error(f"AI Inventory cleanup failed: {str(e)}")

def remove_custom_fields():
    """Remove custom fields created by the app"""
    try:
        custom_fields = frappe.get_all("Custom Field", 
            filters={
                "dt": ["in", ["Purchase Order Item", "Supplier", "AI Inventory Forecast"]],
                "fieldname": ["in", [
                    "predicted_price", "price_confidence", 
                    "supplier_segment", "risk_score", "deal_score", 
                    "supplier_lifetime_value", "last_ml_update",
                    "auto_create_purchase_order", "preferred_supplier",
                    "analysis_method"
                ]]
            })
        
        for field in custom_fields:
            frappe.delete_doc("Custom Field", field.name)
            
        print("✓ Custom fields removed")
        
    except Exception as e:
        print(f"✗ Custom fields removal failed: {str(e)}")

# Utility functions
@frappe.whitelist()
def check_installation_status():
    """Check the installation status of AI Inventory"""
    try:
        # Check ML packages
        np_available = is_package_installed('numpy')
        pd_available = is_package_installed('pandas')
        sklearn_available = is_package_installed('scikit-learn')
        
        # Check custom fields
        forecast_fields = frappe.get_all("Custom Field", 
            filters={"dt": "AI Inventory Forecast"}, 
            pluck="fieldname")
        
        supplier_fields = frappe.get_all("Custom Field", 
            filters={"dt": "Supplier"}, 
            pluck="fieldname")
        
        return {
            "status": "success",
            "ml_packages": {
                "numpy": np_available,
                "pandas": pd_available,
                "scikit-learn": sklearn_available,
                "all_available": np_available and pd_available and sklearn_available
            },
            "custom_fields": {
                "forecast_fields": forecast_fields,
                "supplier_fields": supplier_fields
            },
            "installation_complete": (
                np_available and pd_available and sklearn_available and
                len(forecast_fields) > 0 and len(supplier_fields) > 0
            )
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def check_ml_dependencies():
    """Check if all ML dependencies are available"""
    try:
        import numpy as np
        import pandas as pd
        import sklearn
        
        return {
            "status": "success",
            "message": "All ML dependencies are available",
            "versions": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit-learn": sklearn.__version__
            }
        }
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Missing ML dependency: {str(e)}",
            "suggestion": "Run: ./env/bin/pip install numpy pandas scikit-learn"
        }

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
            },
            {
                "fieldname": "analysis_method",
                "label": "Analysis Method",
                "fieldtype": "Data",
                "insert_after": "confidence_score",
                "read_only": 1,
                "description": "Method used for forecast analysis"
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