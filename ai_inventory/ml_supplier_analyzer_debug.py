import frappe
from frappe import _
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MLSupplierAnalyzer:
    def __init__(self):
        try:
            from sklearn.preprocessing import StandardScaler
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
        except ImportError:
            self.model = None
            self.scaler = None

    def get_supplier_data(self, company, days=365):
        """Get historical supplier performance data - COMPLETELY REWRITTEN FOR DEBUGGING"""
        print(f"🔍 get_supplier_data called with company: {company}")
        
        # Test the exact query step by step
        try:
            print("📋 Step 1: Testing basic query...")
            
            # First, let's test without the try-catch to see the real error
            query = """
                SELECT 
                    po.supplier,
                    po.name as po_name,
                    po.transaction_date,
                    po.status,
                    poi.item_code,
                    poi.qty,
                    poi.rate
                FROM `tabPurchase Order` po
                INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
                WHERE po.company = %s 
                AND po.docstatus = 1
                ORDER BY po.transaction_date DESC
            """
            
            print(f"📋 Step 2: Executing query with company: '{company}'")
            print(f"📋 Query: {query}")
            
            # Execute the query directly
            data = frappe.db.sql(query, (company,), as_dict=1)
            
            print(f"📋 Step 3: Query executed successfully!")
            print(f"📋 Results: {len(data)} records returned")
            
            if data:
                print("📋 Sample data:")
                for i, record in enumerate(data[:2]):
                    print(f"  {i+1}. {record}")
            else:
                print("📋 No data returned from query")
                
                # Let's test why
                print("🔍 Debugging why no data...")
                
                # Test 1: Check company parameter
                print(f"🔍 Company parameter: '{company}' (type: {type(company)})")
                
                # Test 2: Check if company exists in PO table
                company_check = frappe.db.sql("""
                    SELECT DISTINCT company FROM `tabPurchase Order` LIMIT 10
                """, as_dict=1)
                print(f"🔍 Available companies in PO table: {[c['company'] for c in company_check]}")
                
                # Test 3: Check POs for this company without docstatus filter
                po_check = frappe.db.sql("""
                    SELECT name, company, docstatus, status
                    FROM `tabPurchase Order`
                    WHERE company = %s
                    LIMIT 5
                """, (company,), as_dict=1)
                print(f"🔍 POs for company (any docstatus): {len(po_check)}")
                for po in po_check:
                    print(f"  - {po}")
                
                # Test 4: Check submitted POs for this company
                submitted_po_check = frappe.db.sql("""
                    SELECT name, company, docstatus, status
                    FROM `tabPurchase Order`
                    WHERE company = %s AND docstatus = 1
                    LIMIT 5
                """, (company,), as_dict=1)
                print(f"🔍 Submitted POs for company: {len(submitted_po_check)}")
                for po in submitted_po_check:
                    print(f"  - {po}")
                
                # Test 5: Check if these POs have items
                if submitted_po_check:
                    for po in submitted_po_check[:2]:
                        items_check = frappe.db.sql("""
                            SELECT item_code, qty, rate, parent
                            FROM `tabPurchase Order Item`
                            WHERE parent = %s
                        """, (po['name'],), as_dict=1)
                        print(f"🔍 Items for PO {po['name']}: {len(items_check)}")
                        for item in items_check:
                            print(f"    - {item}")
            
            return data
            
        except Exception as e:
            print(f"❌ EXCEPTION in get_supplier_data: {str(e)}")
            print(f"❌ Exception type: {type(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            raise e

    def analyze_suppliers(self, company):
        """Analyze suppliers and return recommendations - WITH DEBUGGING"""
        try:
            print(f"🔍 Starting supplier analysis for: {company}")
            
            # Get data using the fixed method
            supplier_data = self.get_supplier_data(company)
            print(f"📊 Retrieved {len(supplier_data)} supplier records from get_supplier_data")
            
            if not supplier_data:
                print(f"❌ No supplier data found for {company}")
                return []
                
            # Group data by supplier
            supplier_groups = {}
            for record in supplier_data:
                supplier = record['supplier']
                if supplier not in supplier_groups:
                    supplier_groups[supplier] = []
                supplier_groups[supplier].append(record)
            
            print(f"👥 Found {len(supplier_groups)} unique suppliers")
            
            # Analyze each supplier
            results = []
            for supplier, orders in supplier_groups.items():
                try:
                    print(f"🔬 Analyzing supplier: {supplier}")
                    
                    # Calculate metrics
                    total_orders = len(orders)
                    total_value = sum(float(order.get('qty', 0)) * float(order.get('rate', 0)) for order in orders)
                    
                    # Enhanced scoring algorithm
                    base_score = 50
                    
                    # Order count bonus (max 30 points)
                    order_bonus = min(30, total_orders * 10)
                    
                    # Value bonus (max 20 points)
                    if total_value >= 10000:
                        value_bonus = 20
                    elif total_value >= 5000:
                        value_bonus = 15
                    elif total_value >= 1000:
                        value_bonus = 10
                    else:
                        value_bonus = 5
                    
                    # Calculate final score
                    score = min(95, base_score + order_bonus + value_bonus)
                    
                    result = {
                        'supplier': supplier,
                        'score': round(float(score), 2),
                        'recommendation': self.get_recommendation(score),
                        'total_orders': total_orders,
                        'total_value': total_value
                    }
                    
                    results.append(result)
                    print(f"✅ {supplier}: Score {score}, Orders {total_orders}, Value {total_value}")
                    
                except Exception as e:
                    error_msg = f"Supplier analysis failed for {supplier}: {str(e)}"
                    frappe.log_error(error_msg)
                    print(f"❌ {error_msg}")
                    continue
            
            print(f"🎯 Analysis complete: {len(results)} suppliers analyzed")
            return sorted(results, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            error_msg = f"ML Supplier Analysis failed for {company}: {str(e)}"
            frappe.log_error(error_msg)
            print(f"❌ {error_msg}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            raise e

    def get_recommendation(self, score):
        """Get recommendation based on score"""
        if score >= 80:
            return _("Preferred supplier - Highly recommended")
        elif score >= 60:
            return _("Good supplier - Consider for regular orders")
        elif score >= 40:
            return _("Average supplier - Monitor performance")
        else:
            return _("Poor performer - Review relationship")

@frappe.whitelist()
def run_ml_supplier_analysis_debug(company=None):
    """Debug version of the main function"""
    try:
        print(f"🚀 DEBUG: Starting ML Supplier Analysis for: {company}")
        
        if not company:
            companies = frappe.get_all("Company", limit=1)
            if companies:
                company = companies[0].name
            else:
                return {
                    "status": "error",
                    "message": "No company found. Please create a company first."
                }

        # Verify company exists
        if not frappe.db.exists("Company", company):
            return {
                "status": "error",
                "message": f"Company '{company}' does not exist."
            }

        print(f"📋 Using company: {company}")
        analyzer = MLSupplierAnalyzer()

        # Get raw supplier data using the fixed method
        print("📊 Getting supplier data...")
        raw_data = analyzer.get_supplier_data(company)
        print(f"📈 Retrieved {len(raw_data)} raw data records")
        
        if not raw_data:
            # Check if there are any POs at all
            po_count = frappe.db.count("Purchase Order", {
                "company": company,
                "docstatus": 1
            })
            
            print(f"📋 Found {po_count} submitted purchase orders")
            
            return {
                "status": "debug_info",
                "message": f"DEBUG: No supplier data returned from get_supplier_data for {company}",
                "debug_info": {
                    "purchase_orders": po_count,
                    "raw_data_count": len(raw_data),
                    "company": company
                }
            }

        # Run supplier analysis
        print("🔬 Running supplier analysis...")
        results = analyzer.analyze_suppliers(company)
        print(f"✅ Analysis complete: {len(results)} suppliers")

        return {
            "status": "success",
            "message": f"DEBUG: ML supplier analysis completed for {company}. Analyzed {len(results)} suppliers.",
            "suppliers_analyzed": len(results),
            "company": company,
            "top_suppliers": results[:5] if len(results) > 5 else results
        }

    except Exception as e:
        error_msg = f"DEBUG: ML supplier analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": error_msg
        }

# Quick test function
@frappe.whitelist()
def quick_debug_test():
    """Quick debug test"""
    print("🧪 QUICK DEBUG TEST")
    company = "AI Inventory Forecast Company"
    
    try:
        analyzer = MLSupplierAnalyzer()
        print("✅ Analyzer created")
        
        data = analyzer.get_supplier_data(company)
        print(f"✅ get_supplier_data returned: {len(data)} records")
        
        return {"status": "success", "data_count": len(data)}
    except Exception as e:
        print(f"❌ Quick test failed: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}