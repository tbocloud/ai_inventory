#!/usr/bin/env python3

"""
AI Forecast System Comprehensive Review Script
This script checks all forecast types and their alignment with AI Financial Forecast
"""

import frappe
import json
from datetime import datetime

def comprehensive_forecast_review():
    """Perform comprehensive review of AI forecast system"""
    
    print("="*80)
    print("AI FORECAST SYSTEM COMPREHENSIVE REVIEW")
    print("="*80)
    
    # Check system tables and data
    review_data_integrity()
    review_forecast_alignment()
    review_sync_functionality()
    review_accuracy_tracking()
    review_field_mappings()
    
    print("\n" + "="*80)
    print("REVIEW COMPLETE")
    print("="*80)

def review_data_integrity():
    """Review data integrity across all forecast types"""
    print("\n📊 DATA INTEGRITY REVIEW")
    print("-" * 40)
    
    forecast_types = [
        'AI Financial Forecast',
        'AI Cashflow Forecast', 
        'AI Revenue Forecast',
        'AI Expense Forecast',
        'AI Forecast Accuracy'
    ]
    
    for doctype in forecast_types:
        try:
            count = len(frappe.get_all(doctype))
            print(f"✅ {doctype}: {count} records")
            
            # Get sample record for structure check
            if count > 0:
                sample = frappe.get_all(doctype, limit=1, fields=['name', 'company', 'forecast_date'])[0]
                print(f"   Sample: {sample.name} | Company: {sample.company}")
                
        except Exception as e:
            print(f"❌ {doctype}: Error - {str(e)}")

def review_forecast_alignment():
    """Review alignment between specific forecasts and AI Financial Forecast"""
    print("\n🔗 FORECAST ALIGNMENT REVIEW")
    print("-" * 40)
    
    # Check AI Financial Forecast types
    financial_forecasts = frappe.get_all('AI Financial Forecast', 
                                       fields=['name', 'forecast_type', 'company', 'predicted_amount'],
                                       limit=10)
    
    forecast_types = {}
    for forecast in financial_forecasts:
        ftype = forecast.forecast_type
        if ftype not in forecast_types:
            forecast_types[ftype] = 0
        forecast_types[ftype] += 1
    
    print("📈 AI Financial Forecast Types:")
    for ftype, count in forecast_types.items():
        print(f"   {ftype}: {count} records")
    
    # Check alignment with specific forecast types
    alignment_check = {
        'Cash Flow': 'AI Cashflow Forecast',
        'Revenue': 'AI Revenue Forecast', 
        'Expense': 'AI Expense Forecast'
    }
    
    print("\n🔍 Type Alignment Check:")
    for fin_type, specific_doctype in alignment_check.items():
        fin_count = len(frappe.get_all('AI Financial Forecast', filters={'forecast_type': fin_type}))
        specific_count = len(frappe.get_all(specific_doctype))
        
        status = "✅ Aligned" if abs(fin_count - specific_count) <= 1 else "⚠️  Misaligned"
        print(f"   {fin_type}: Financial({fin_count}) vs {specific_doctype.split()[-1]}({specific_count}) - {status}")

def review_sync_functionality():
    """Review sync functionality between forecast types"""
    print("\n🔄 SYNC FUNCTIONALITY REVIEW")
    print("-" * 40)
    
    # Check for sync methods in each forecast type
    sync_methods = {
        'AI Cashflow Forecast': 'sync_with_financial_forecast',
        'AI Revenue Forecast': 'sync_with_financial_forecast',
        'AI Expense Forecast': 'sync_with_financial_forecast'
    }
    
    for doctype, method in sync_methods.items():
        try:
            # Try to get the controller class
            controller = frappe.get_doc(doctype, frappe.get_all(doctype, limit=1)[0].name)
            
            if hasattr(controller, method):
                print(f"✅ {doctype}: {method} method exists")
            else:
                print(f"❌ {doctype}: {method} method missing")
                
        except Exception as e:
            print(f"⚠️  {doctype}: Could not verify sync method - {str(e)}")

def review_accuracy_tracking():
    """Review accuracy tracking system"""
    print("\n📊 ACCURACY TRACKING REVIEW")
    print("-" * 40)
    
    try:
        accuracy_records = frappe.get_all('AI Forecast Accuracy', 
                                        fields=['name', 'forecast_type', 'accuracy_percentage', 'accuracy_rating'],
                                        limit=5)
        
        if accuracy_records:
            print(f"✅ Found {len(accuracy_records)} accuracy records")
            
            # Show accuracy distribution
            ratings = {}
            for record in accuracy_records:
                rating = record.accuracy_rating or 'Unknown'
                ratings[rating] = ratings.get(rating, 0) + 1
            
            print("📊 Accuracy Distribution:")
            for rating, count in ratings.items():
                print(f"   {rating}: {count} records")
                
        else:
            print("⚠️  No accuracy records found")
            
    except Exception as e:
        print(f"❌ Accuracy tracking error: {str(e)}")

def review_field_mappings():
    """Review field mappings and data structure consistency"""
    print("\n🗂️  FIELD MAPPING REVIEW")
    print("-" * 40)
    
    # Key field mappings to check
    field_mappings = {
        'AI Cashflow Forecast': {
            'amount_field': 'net_cash_flow',
            'confidence_field': 'confidence_score',
            'required_fields': ['company', 'forecast_date', 'predicted_inflows', 'predicted_outflows']
        },
        'AI Revenue Forecast': {
            'amount_field': 'total_predicted_revenue', 
            'confidence_field': 'confidence_score',
            'required_fields': ['company', 'forecast_date', 'total_predicted_revenue']
        },
        'AI Expense Forecast': {
            'amount_field': 'total_predicted_expense',  # Note: might be 'total_predicted_expenses'
            'confidence_field': 'confidence_score',
            'required_fields': ['company', 'forecast_date']
        }
    }
    
    for doctype, mapping in field_mappings.items():
        try:
            # Get field list for doctype
            meta = frappe.get_meta(doctype)
            field_names = [f.fieldname for f in meta.fields]
            
            print(f"\n📋 {doctype} Fields:")
            
            # Check amount field
            amount_field = mapping['amount_field']
            if amount_field in field_names:
                print(f"   ✅ Amount field: {amount_field}")
            else:
                # Check alternative spellings
                alternatives = [f for f in field_names if 'expense' in f and ('total' in f or 'predicted' in f)]
                if alternatives:
                    print(f"   ⚠️  Amount field '{amount_field}' not found, but found: {alternatives}")
                else:
                    print(f"   ❌ Amount field '{amount_field}' not found")
            
            # Check confidence field
            confidence_field = mapping['confidence_field']
            if confidence_field in field_names:
                print(f"   ✅ Confidence field: {confidence_field}")
            else:
                alternatives = [f for f in field_names if 'confidence' in f]
                if alternatives:
                    print(f"   ⚠️  Confidence field alternatives: {alternatives}")
                else:
                    print(f"   ❌ Confidence field '{confidence_field}' not found")
            
            # Check required fields
            missing_fields = [f for f in mapping['required_fields'] if f not in field_names]
            if not missing_fields:
                print(f"   ✅ All required fields present")
            else:
                print(f"   ⚠️  Missing required fields: {missing_fields}")
                
        except Exception as e:
            print(f"   ❌ Error checking {doctype}: {str(e)}")

if __name__ == "__main__":
    frappe.init(site='extra.com')
    frappe.connect()
    comprehensive_forecast_review()
