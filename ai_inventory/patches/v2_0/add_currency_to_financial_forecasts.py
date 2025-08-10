"""
Patch to add currency field to existing AI Financial Forecast records
"""
import frappe

def execute():
    """Set currency for existing AI Financial Forecast records"""
    
    # Get all existing AI Financial Forecast records without currency
    forecasts = frappe.get_all("AI Financial Forecast", 
                              filters={"currency": ["in", [None, ""]]},
                              fields=["name", "account", "company"])
    
    if not forecasts:
        print("No forecasts found without currency")
        return
    
    updated_count = 0
    
    for forecast in forecasts:
        try:
            currency = None
            
            # Try to get currency from account
            if forecast.account:
                currency = frappe.db.get_value("Account", forecast.account, "account_currency")
            
            # Fallback to company default currency
            if not currency and forecast.company:
                currency = frappe.db.get_value("Company", forecast.company, "default_currency")
            
            # Final fallback to INR
            if not currency:
                currency = "INR"
            
            # Update the forecast
            frappe.db.set_value("AI Financial Forecast", forecast.name, "currency", currency)
            updated_count += 1
            
        except Exception as e:
            print(f"Error updating forecast {forecast.name}: {e}")
            continue
    
    print(f"Updated currency for {updated_count} forecasts")
    frappe.db.commit()
