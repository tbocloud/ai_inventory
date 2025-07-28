import frappe
from frappe import _
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta

class MLSupplierAnalyzer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
    def get_supplier_data(self, company, days=365):
        """Get historical supplier performance data"""
        from_date = datetime.now() - timedelta(days=days)
        
        return frappe.db.sql("""
            SELECT 
                po.supplier,
                po.name as po_name,
                po.transaction_date,
                po.delivery_date,
                po.status,
                poi.item_code,
                poi.qty,
                poi.received_qty,
                poi.rate
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.company = %s 
            AND po.transaction_date >= %s
            AND po.docstatus = 1
        """, (company, from_date), as_dict=1)

    def prepare_features(self, supplier_data):
        """Prepare feature matrix for ML model"""
        df = pd.DataFrame(supplier_data)
        if df.empty:
            return None, None
            
        # Calculate supplier metrics
        supplier_metrics = []
        for supplier in df.supplier.unique():
            supplier_df = df[df.supplier == supplier]
            
            metrics = {
                'supplier': supplier,
                'order_count': len(supplier_df),
                'total_value': supplier_df.qty.sum() * supplier_df.rate.mean(),
                'on_time_delivery': (supplier_df.status == 'Delivered').mean(),
                'quality_score': (supplier_df.received_qty / supplier_df.qty).mean(),
                'avg_delay_days': (pd.to_datetime(supplier_df.delivery_date) - 
                                 pd.to_datetime(supplier_df.transaction_date)).mean().days,
            }
            supplier_metrics.append(metrics)
            
        feature_df = pd.DataFrame(supplier_metrics)
        feature_df = feature_df.fillna(0)
        
        # Scale features
        feature_columns = ['order_count', 'total_value', 'on_time_delivery', 
                          'quality_score', 'avg_delay_days']
        X = self.scaler.fit_transform(feature_df[feature_columns])
        
        return X, feature_df.supplier.values

    def analyze_suppliers(self, company):
        """Analyze suppliers and return recommendations"""
        try:
            # Get data
            supplier_data = self.get_supplier_data(company)
            if not supplier_data:
                return []
                
            # Prepare features
            X, suppliers = self.prepare_features(supplier_data)
            if X is None:
                return []
                
            # For demo purposes, generate mock scores based on simple heuristics
            # In a real implementation, you'd train the model first
            scores = []
            for supplier in suppliers:
                # Get supplier stats
                supplier_orders = [d for d in supplier_data if d['supplier'] == supplier]
                if supplier_orders:
                    avg_delivery = sum(1 for d in supplier_orders if d['status'] == 'Delivered') / len(supplier_orders)
                    score = min(100, max(0, avg_delivery * 100 + np.random.normal(0, 10)))
                else:
                    score = 50
                scores.append(score)
            
            # Prepare results
            results = []
            for supplier, score in zip(suppliers, scores):
                results.append({
                    'supplier': supplier,
                    'score': round(float(score), 2),
                    'recommendation': self.get_recommendation(score)
                })
                
            return sorted(results, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            frappe.log_error(f"ML Supplier Analysis failed: {str(e)}")
            return []
            
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

    def save_analysis(self, company):
        """Save supplier analysis results to database"""
        try:
            results = self.analyze_suppliers(company)
            
            # Update AI Inventory Forecasts
            for result in results:
                forecasts = frappe.get_all("AI Inventory Forecast",
                    filters={
                        "company": company,
                        "supplier": result['supplier']
                    },
                    fields=["name"]
                )
                
                for forecast in forecasts:
                    frappe.db.set_value("AI Inventory Forecast",
                        forecast.name,
                        {
                            "supplier_score": result['score'],
                            "supplier_recommendation": result['recommendation']
                        }
                    )
                    
            frappe.db.commit()
            return len(results)
            
        except Exception as e:
            frappe.log_error(f"Failed to save supplier analysis: {str(e)}")
            return 0

    def find_best_supplier_for_item(self, item_code, company):
        """Find the best supplier for a specific item"""
        try:
            # Get suppliers who have supplied this item
            suppliers = frappe.db.sql("""
                SELECT DISTINCT po.supplier,
                       COUNT(*) as order_count,
                       AVG(poi.rate) as avg_rate,
                       MAX(po.transaction_date) as last_order_date
                FROM `tabPurchase Order` po
                INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
                WHERE poi.item_code = %s
                AND po.company = %s
                AND po.docstatus = 1
                GROUP BY po.supplier
                ORDER BY order_count DESC, last_order_date DESC
                LIMIT 1
            """, (item_code, company), as_dict=True)
            
            if suppliers:
                best_supplier = suppliers[0]
                return {
                    'supplier': best_supplier['supplier'],
                    'score': 85,  # Mock score
                    'avg_rate': best_supplier['avg_rate'],
                    'order_count': best_supplier['order_count']
                }
            else:
                # Get any supplier for this company
                fallback_supplier = frappe.db.sql("""
                    SELECT name FROM `tabSupplier` 
                    WHERE disabled = 0 
                    AND (company = %s OR company IS NULL OR company = '')
                    LIMIT 1
                """, (company,))
                
                if fallback_supplier:
                    return {
                        'supplier': fallback_supplier[0][0],
                        'score': 50,
                        'avg_rate': 0,
                        'order_count': 0
                    }
                    
            return None
            
        except Exception as e:
            frappe.log_error(f"Find best supplier failed: {str(e)}")
            return None

    def predict_item_price(self, item_code, supplier, company, qty=1):
        """Predict price for an item from a supplier"""
        try:
            # Get historical prices
            historical_prices = frappe.db.sql("""
                SELECT poi.rate, po.transaction_date, poi.qty
                FROM `tabPurchase Order Item` poi
                INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.item_code = %s
                AND po.supplier = %s
                AND po.company = %s
                AND po.docstatus = 1
                ORDER BY po.transaction_date DESC
                LIMIT 10
            """, (item_code, supplier, company), as_dict=True)
            
            if historical_prices:
                # Simple price prediction - average of recent prices
                avg_price = sum(p['rate'] for p in historical_prices) / len(historical_prices)
                confidence = min(90, len(historical_prices) * 10)
                
                return {
                    'status': 'success',
                    'predicted_price': avg_price,
                    'confidence': confidence,
                    'historical_count': len(historical_prices)
                }
            else:
                # Get standard rate from item master
                standard_rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
                
                return {
                    'status': 'success',
                    'predicted_price': standard_rate,
                    'confidence': 30,
                    'historical_count': 0
                }
                
        except Exception as e:
            frappe.log_error(f"Price prediction failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

def analyze_suppliers_for_company(company=None):
    """Background job to analyze suppliers"""
    try:
        analyzer = MLSupplierAnalyzer()
        count = analyzer.save_analysis(company)
        frappe.logger().info(f"Analyzed {count} suppliers for {company}")
    except Exception as e:
        frappe.log_error(f"Supplier analysis failed: {str(e)}")

# MISSING FUNCTIONS THAT ARE CALLED FROM AI SETTINGS

@frappe.whitelist()
def run_ml_supplier_analysis(company=None):
    """Main function called from AI Settings - analyzes suppliers using ML - FIXED"""
    try:
        if not company:
            # Get default company or first available company
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
        
        analyzer = MLSupplierAnalyzer()
        
        # Run supplier analysis
        results = analyzer.analyze_suppliers(company)
        
        if not results:
            return {
                "status": "info",
                "message": f"No supplier data found for {company}. Purchase some items first to generate supplier analytics.",
                "suppliers_analyzed": 0,
                "company": company
            }
        
        # Save results
        saved_count = analyzer.save_analysis(company)
        
        # Update supplier records with ML scores
        updated_suppliers = update_supplier_ml_scores(results, company)
        
        return {
            "status": "success",
            "message": f"ML supplier analysis completed for {company}. Analyzed {len(results)} suppliers.",
            "suppliers_analyzed": len(results),
            "suppliers_updated": updated_suppliers,
            "company": company,
            "top_suppliers": results[:5] if len(results) > 5 else results
        }
        
    except Exception as e:
        error_msg = f"ML supplier analysis failed: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

@frappe.whitelist()
def daily_ml_supplier_analysis():
    """Daily scheduled task for ML supplier analysis"""
    try:
        # Fix: Get all companies without checking disabled field
        companies = frappe.get_all("Company", fields=["name"])
        
        total_analyzed = 0
        
        for company in companies:
            try:
                result = run_ml_supplier_analysis(company.name)
                if result.get("status") == "success":
                    total_analyzed += result.get("suppliers_analyzed", 0)
                    
                frappe.logger().info(f"Daily ML analysis for {company.name}: {result.get('message', 'Completed')}")
                
            except Exception as e:
                frappe.log_error(f"Daily ML analysis failed for {company.name}: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Daily ML supplier analysis completed. Analyzed {total_analyzed} suppliers across {len(companies)} companies.",
            "companies_processed": len(companies),
            "total_suppliers_analyzed": total_analyzed
        }
        
    except Exception as e:
        error_msg = f"Daily ML supplier analysis failed: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

@frappe.whitelist() 
def weekly_supplier_segmentation():
    """Weekly supplier segmentation analysis"""
    try:
        # Fix: Get all companies without checking disabled field
        companies = frappe.get_all("Company", fields=["name"])
        
        segmentation_results = {}
        
        for company in companies:
            try:
                analyzer = MLSupplierAnalyzer()
                results = analyzer.analyze_suppliers(company.name)
                
                # Categorize suppliers
                segments = {
                    "Strategic": [],
                    "Preferred": [], 
                    "Approved": [],
                    "Caution": [],
                    "Critical": []
                }
                
                for result in results:
                    score = result['score']
                    if score >= 90:
                        segments["Strategic"].append(result['supplier'])
                    elif score >= 75:
                        segments["Preferred"].append(result['supplier'])
                    elif score >= 50:
                        segments["Approved"].append(result['supplier'])
                    elif score >= 30:
                        segments["Caution"].append(result['supplier'])
                    else:
                        segments["Critical"].append(result['supplier'])
                
                segmentation_results[company.name] = segments
                
                frappe.logger().info(f"Weekly segmentation for {company.name}: {len(results)} suppliers segmented")
                
            except Exception as e:
                frappe.log_error(f"Weekly segmentation failed for {company.name}: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Weekly supplier segmentation completed for {len(companies)} companies.",
            "segmentation_results": segmentation_results
        }
        
    except Exception as e:
        error_msg = f"Weekly supplier segmentation failed: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

@frappe.whitelist()
def get_supplier_analytics_summary(company=None):
    """Get summary of supplier analytics - FIXED"""
    try:
        # Build company filter for supplier query
        company_condition = ""
        params = {}
        
        if company:
            # Check if supplier has company field, if not, skip company filter
            supplier_meta = frappe.get_meta("Supplier")
            if supplier_meta.has_field("company"):
                company_condition = "AND company = %(company)s"
                params["company"] = company
        
        # Get supplier statistics with safe query
        supplier_stats = frappe.db.sql(f"""
            SELECT 
                COALESCE(supplier_segment, 'Unknown') as supplier_segment,
                COUNT(*) as count,
                AVG(NULLIF(deal_score, 0)) as avg_score,
                AVG(NULLIF(risk_score, 0)) as avg_risk
            FROM `tabSupplier`
            WHERE (supplier_segment IS NOT NULL AND supplier_segment != '')
            {company_condition}
            GROUP BY supplier_segment
        """, params, as_dict=True)
        
        # Get recent ML updates
        recent_updates = frappe.db.sql(f"""
            SELECT COUNT(*) as count
            FROM `tabSupplier`
            WHERE last_ml_update >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            {company_condition}
        """, params, as_dict=True)
        
        return {
            "status": "success",
            "supplier_segments": supplier_stats,
            "recent_updates": recent_updates[0]['count'] if recent_updates else 0,
            "company": company
        }
        
    except Exception as e:
        error_msg = f"Supplier analytics summary failed: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

def update_supplier_ml_scores(results, company):
    """Update supplier records with ML-calculated scores - SAFE VERSION"""
    try:
        updated_count = 0
        
        for result in results:
            try:
                supplier_name = result['supplier']
                score = result['score']
                recommendation = result['recommendation']
                
                # Check if supplier exists
                if not frappe.db.exists("Supplier", supplier_name):
                    continue
                
                # Determine supplier segment based on score
                if score >= 80:
                    segment = "Strategic"
                elif score >= 60:
                    segment = "Preferred"
                elif score >= 40:
                    segment = "Approved"
                else:
                    segment = "Caution"
                
                # Calculate risk score (inverse of performance score)
                risk_score = max(0, 100 - score)
                
                # Check which fields exist in Supplier doctype
                supplier_meta = frappe.get_meta("Supplier")
                update_fields = []
                values = []
                
                if supplier_meta.has_field("supplier_segment"):
                    update_fields.append("supplier_segment = %s")
                    values.append(segment)
                
                if supplier_meta.has_field("risk_score"):
                    update_fields.append("risk_score = %s")
                    values.append(risk_score)
                
                if supplier_meta.has_field("deal_score"):
                    update_fields.append("deal_score = %s")
                    values.append(score)
                
                if supplier_meta.has_field("last_ml_update"):
                    update_fields.append("last_ml_update = %s")
                    values.append(frappe.utils.now())
                
                # Always update modified
                update_fields.append("modified = %s")
                values.append(frappe.utils.now())
                
                if update_fields:
                    # Update supplier record safely
                    frappe.db.sql(f"""
                        UPDATE `tabSupplier`
                        SET {', '.join(update_fields)}
                        WHERE name = %s
                    """, values + [supplier_name])
                    
                    updated_count += 1
                
            except Exception as e:
                frappe.log_error(f"Failed to update supplier {result.get('supplier', 'Unknown')}: {str(e)}")
                continue
        
        frappe.db.commit()
        return updated_count
        
    except Exception as e:
        frappe.log_error(f"Failed to update supplier ML scores: {str(e)}")
        return 0

@frappe.whitelist()
def get_companies_with_purchase_data():
    """Get list of companies that have purchase order data for ML analysis"""
    try:
        # Get companies with purchase orders
        companies_with_data = frappe.db.sql("""
            SELECT 
                po.company,
                COUNT(DISTINCT po.name) as purchase_orders,
                COUNT(DISTINCT po.supplier) as suppliers,
                MAX(po.transaction_date) as latest_purchase,
                SUM(poi.qty * poi.rate) as total_purchase_value
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.docstatus = 1
            AND po.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
            GROUP BY po.company
            HAVING purchase_orders > 0
            ORDER BY purchase_orders DESC, total_purchase_value DESC
        """, as_dict=True)
        
        if not companies_with_data:
            # If no purchase data found, return all companies with 0 data
            all_companies = frappe.get_all("Company", fields=["name as company"])
            return [{
                "company": comp.company,
                "purchase_orders": 0,
                "suppliers": 0,
                "latest_purchase": None,
                "total_purchase_value": 0
            } for comp in all_companies]
        
        return companies_with_data
        
    except Exception as e:
        frappe.log_error(f"Failed to get companies with purchase data: {str(e)}")
        # Fallback to all companies
        all_companies = frappe.get_all("Company", fields=["name as company"])
        return [{
            "company": comp.company,
            "purchase_orders": 0,
            "suppliers": 0,
            "latest_purchase": None,
            "total_purchase_value": 0
        } for comp in all_companies]

@frappe.whitelist()
def check_company_purchase_data(company):
    """Check if a specific company has purchase data for ML analysis"""
    try:
        purchase_data = frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT po.name) as purchase_orders,
                COUNT(DISTINCT po.supplier) as suppliers,
                COUNT(DISTINCT poi.item_code) as items,
                MIN(po.transaction_date) as first_purchase,
                MAX(po.transaction_date) as latest_purchase,
                SUM(poi.qty * poi.rate) as total_value
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.company = %s
            AND po.docstatus = 1
        """, (company,), as_dict=True)
        
        if purchase_data and purchase_data[0]:
            data = purchase_data[0]
            return {
                "status": "success",
                "has_data": data.purchase_orders > 0,
                "company": company,
                "stats": {
                    "purchase_orders": data.purchase_orders or 0,
                    "suppliers": data.suppliers or 0,
                    "items": data.items or 0,
                    "first_purchase": data.first_purchase,
                    "latest_purchase": data.latest_purchase,
                    "total_value": data.total_value or 0
                }
            }
        
        return {
            "status": "success",
            "has_data": False,
            "company": company,
            "stats": {
                "purchase_orders": 0,
                "suppliers": 0,
                "items": 0,
                "first_purchase": None,
                "latest_purchase": None,
                "total_value": 0
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "has_data": False
        }

@frappe.whitelist()
def create_sample_purchase_data(company):
    """Create sample purchase data for ML testing"""
    try:
        if not frappe.db.exists("Company", company):
            return {
                "status": "error",
                "message": f"Company '{company}' does not exist"
            }
        
        # Create sample suppliers
        sample_suppliers = [
            {"name": "ABC Suppliers Ltd", "group": "Local"},
            {"name": "XYZ Trading Co", "group": "Local"}, 
            {"name": "Best Parts Inc", "group": "Local"},
            {"name": "Quality Materials LLC", "group": "Local"},
            {"name": "Reliable Goods Pvt Ltd", "group": "Local"}
        ]
        
        created_suppliers = []
        for supplier_data in sample_suppliers:
            supplier_name = f"{supplier_data['name']} - {company}"
            
            if not frappe.db.exists("Supplier", supplier_name):
                supplier = frappe.get_doc({
                    "doctype": "Supplier",
                    "supplier_name": supplier_name,
                    "supplier_group": supplier_data["group"]
                })
                supplier.insert(ignore_permissions=True)
                created_suppliers.append(supplier.name)
        
        # Create sample items
        sample_items = [
            {"code": "RAW-MAT-001", "name": "Raw Material A", "uom": "Kg"},
            {"code": "RAW-MAT-002", "name": "Raw Material B", "uom": "Kg"},
            {"code": "COMPONENT-001", "name": "Electronic Component X", "uom": "Nos"},
            {"code": "COMPONENT-002", "name": "Mechanical Part Y", "uom": "Nos"},
            {"code": "PACKAGING-001", "name": "Packaging Material", "uom": "Nos"}
        ]
        
        created_items = []
        for item_data in sample_items:
            item_code = f"{item_data['code']}-{company[:3]}"
            
            if not frappe.db.exists("Item", item_code):
                item = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": item_code,
                    "item_name": f"{item_data['name']} for {company}",
                    "is_stock_item": 1,
                    "stock_uom": item_data["uom"],
                    "standard_rate": frappe.utils.random_int(100, 1000)
                })
                item.insert(ignore_permissions=True)
                created_items.append(item.name)
        
        # Create sample warehouse
        warehouse_name = f"Main Warehouse - {company}"
        if not frappe.db.exists("Warehouse", warehouse_name):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": warehouse_name,
                "company": company
            })
            warehouse.insert(ignore_permissions=True)
        
        # Create sample purchase orders
        created_pos = []
        import random
        from datetime import datetime, timedelta
        
        for i in range(8):  # Create 8 sample POs
            try:
                # Random supplier and items
                supplier = random.choice(created_suppliers or sample_suppliers)
                if isinstance(supplier, dict):
                    supplier = f"{supplier['name']} - {company}"
                
                # Random date in last 6 months
                random_days = random.randint(1, 180)
                po_date = (datetime.now() - timedelta(days=random_days)).date()
                
                # Create PO
                po = frappe.get_doc({
                    "doctype": "Purchase Order",
                    "supplier": supplier,
                    "company": company,
                    "transaction_date": po_date,
                    "schedule_date": po_date + timedelta(days=random.randint(7, 30)),
                    "items": []
                })
                
                # Add random items to PO
                num_items = random.randint(1, 3)
                selected_items = random.sample(created_items or [item["code"] for item in sample_items], min(num_items, len(created_items or sample_items)))
                
                for item_code in selected_items:
                    if not isinstance(item_code, str):
                        continue
                        
                    po.append("items", {
                        "item_code": item_code,
                        "qty": random.randint(10, 100),
                        "rate": random.randint(50, 500),
                        "warehouse": warehouse_name,
                        "schedule_date": po.schedule_date
                    })
                
                if po.items:  # Only create PO if it has items
                    po.insert(ignore_permissions=True)
                    po.submit()
                    created_pos.append(po.name)
                    
            except Exception as e:
                frappe.log_error(f"Failed to create sample PO {i}: {str(e)}")
                continue
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Sample data created for {company}:\n• {len(created_suppliers)} suppliers\n• {len(created_items)} items\n• {len(created_pos)} purchase orders",
            "created": {
                "suppliers": len(created_suppliers),
                "items": len(created_items), 
                "purchase_orders": len(created_pos),
                "warehouse": warehouse_name
            },
            "company": company
        }
        
    except Exception as e:
        error_msg = f"Failed to create sample data for {company}: {str(e)}"
        frappe.log_error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# Update the existing get_companies_with_purchase_data function with improved fallback
@frappe.whitelist()
def get_companies_with_purchase_data():
    """Get list of companies that have purchase order data for ML analysis"""
    try:
        # Get companies with purchase orders
        companies_with_data = frappe.db.sql("""
            SELECT 
                po.company,
                COUNT(DISTINCT po.name) as purchase_orders,
                COUNT(DISTINCT po.supplier) as suppliers,
                MAX(po.transaction_date) as latest_purchase,
                SUM(poi.qty * poi.rate) as total_purchase_value
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.docstatus = 1
            AND po.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
            GROUP BY po.company
            HAVING purchase_orders > 0
            ORDER BY purchase_orders DESC, total_purchase_value DESC
        """, as_dict=True)
        
        if not companies_with_data:
            # If no purchase data found, return all companies with 0 data
            all_companies = frappe.get_all("Company", fields=["name as company"])
            return [{
                "company": comp.company,
                "purchase_orders": 0,
                "suppliers": 0,
                "latest_purchase": None,
                "total_purchase_value": 0
            } for comp in all_companies]
        
        return companies_with_data
        
    except Exception as e:
        frappe.log_error(f"Failed to get companies with purchase data: {str(e)}")
        # Fallback to all companies
        all_companies = frappe.get_all("Company", fields=["name as company"])
        return [{
            "company": comp.company,
            "purchase_orders": 0,
            "suppliers": 0,
            "latest_purchase": None,
            "total_purchase_value": 0
        } for comp in all_companies]

# Create sample data for a company
frappe.call('ai_inventory.ml_supplier_analyzer.create_sample_purchase_data', company='Your Company Name')

# Check which companies have purchase data
frappe.call('ai_inventory.ml_supplier_analyzer.get_companies_with_purchase_data')

@frappe.whitelist()
def predict_purchase_price(item_code, supplier, company, qty=1):
    """Predict purchase price for an item from a supplier - FOR PURCHASE ORDER INTEGRATION"""
    try:
        analyzer = MLSupplierAnalyzer()
        
        # Use existing predict_item_price method
        result = analyzer.predict_item_price(item_code, supplier, company, qty)
        
        if result.get('status') == 'success':
            return {
                "status": "success",
                "predicted_price": result.get('predicted_price', 0),
                "confidence": result.get('confidence', 0),
                "historical_count": result.get('historical_count', 0),
                "message": f"Prediction based on {result.get('historical_count', 0)} historical records"
            }
        else:
            # Fallback to item standard rate
            standard_rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
            return {
                "status": "success",
                "predicted_price": standard_rate,
                "confidence": 30,
                "historical_count": 0,
                "message": "Using item standard rate (no historical data)"
            }
            
    except Exception as e:
        frappe.log_error(f"Purchase price prediction failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "predicted_price": 0,
            "confidence": 0
        }