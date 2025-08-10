#!/usr/bin/env python3

import frappe
import random
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample data for the forecast accuracy report"""
    
    # Check existing data
    existing_forecasts = frappe.db.count('AI Financial Forecast')
    print(f'Existing forecasts: {existing_forecasts}')
    
    if existing_forecasts == 0:
        print('Creating sample AI Financial Forecast records...')
        
        # Create 5 sample forecast records
        model_types = ['ARIMA', 'LSTM', 'Prophet', 'Linear Regression', 'Random Forest']
        
        for i in range(5):
            forecast_doc = frappe.new_doc('AI Financial Forecast')
            forecast_doc.company = 'EXTRA APPAREL STORE'
            forecast_doc.forecast_type = 'Revenue'
            forecast_doc.model_type = model_types[i]
            forecast_doc.forecast_start_date = frappe.utils.add_days(frappe.utils.today(), -60 + (i * 10))
            forecast_doc.forecast_end_date = frappe.utils.add_days(forecast_doc.forecast_start_date, 30)
            forecast_doc.forecast_amount = 50000 + (i * 10000)
            forecast_doc.confidence_score = 0.75 + (i * 0.05)
            forecast_doc.status = 'Completed'
            forecast_doc.insert(ignore_permissions=True)
            print(f'Created forecast: {forecast_doc.name}')
        
        frappe.db.commit()
        print('Sample forecasts created successfully')
    
    # Check accuracy data
    existing_accuracy = frappe.db.count('AI Forecast Accuracy')
    print(f'Existing accuracy records: {existing_accuracy}')
    
    if existing_accuracy == 0:
        print('Creating sample AI Forecast Accuracy records...')
        
        # Get the forecast records
        forecasts = frappe.get_all('AI Financial Forecast', 
                                 fields=['name', 'forecast_amount'], 
                                 limit=10)
        
        for forecast in forecasts:
            # Create 3 accuracy records per forecast
            for j in range(3):
                accuracy_doc = frappe.new_doc('AI Forecast Accuracy')
                accuracy_doc.forecast_id = forecast.name
                
                # Generate realistic accuracy data
                predicted_value = forecast.forecast_amount
                actual_value = predicted_value * (0.8 + random.random() * 0.4)  # 80-120% of predicted
                accuracy_percentage = max(0, 100 - abs((predicted_value - actual_value) / predicted_value * 100))
                
                accuracy_doc.predicted_value = predicted_value
                accuracy_doc.actual_value = actual_value
                accuracy_doc.accuracy_percentage = round(accuracy_percentage, 2)
                accuracy_doc.evaluation_date = frappe.utils.add_days(frappe.utils.today(), -30 + (j * 10))
                accuracy_doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        print(f'Created accuracy records for {len(forecasts)} forecasts')
    
    # Test the report
    print('\nTesting the report with sample data...')
    from ai_inventory.ai_inventory.report.forecast_accuracy_report.forecast_accuracy_report import execute
    
    filters = {
        'company': 'EXTRA APPAREL STORE',
        'from_date': '2025-01-01',
        'to_date': '2025-12-31',
        'model_type': 'All'
    }
    
    columns, data = execute(filters)
    print(f'Report returns: {len(columns)} columns, {len(data)} rows')
    
    if len(data) > 0:
        print('\nSample report data (first 3 rows):')
        for i, row in enumerate(data[:3]):
            print(f'Row {i+1}: {row}')
    
    print('\nSample data creation completed!')
    return True

if __name__ == '__main__':
    create_sample_data()
