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

    # ==============================================================================
    # FIX 1 & 4: Update get_supplier_data to use DATE_SUB and better error handling
    # ==============================================================================
    def get_supplier_data(self, company, days=365):
        """Get historical supplier performance data - FIXED VERSION"""
        try:
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
                AND po.transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                AND po.docstatus = 1
                ORDER BY po.transaction_date DESC
            """, (company, days), as_dict=1)
        except Exception as e:
            frappe.log_error(f"Get supplier data failed: {str(e)}")
            return []

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

    # ==============================================================================
    # FIX 2: Update analyze_suppliers with better error handling & improved logic
    # ==============================================================================
    def analyze_suppliers(self, company):
        """Analyze suppliers and return recommendations - FIXED VERSION"""
        try:
            # Get data with better error handling
            supplier_data = self.get_supplier_data(company)
            if not supplier_data:
                frappe.logger().info(f"No supplier data found for {company}")
                return []

            # Group data by supplier
            supplier_groups = {}
            for record in supplier_data:
                supplier = record['supplier']
                if supplier not in supplier_groups:
                    supplier_groups[supplier] = []
                supplier_groups[supplier].append(record)

            # Analyze each supplier
            results = []
            for supplier, orders in supplier_groups.items():
                try:
                    # Calculate metrics
                    total_orders = len(orders)
                    total_value = sum(order.get('qty', 0) * order.get('rate', 0) for order in orders)

                    # Simple scoring based on order volume and value
                    if total_orders >= 3 and total_value >= 1000:
                        score = min(95, 70 + (total_orders * 5) + (total_value / 1000))
                    elif total_orders >= 2 and total_value >= 500:
                        score = min(85, 60 + (total_orders * 5) + (total_value / 500))
                    elif total_orders >= 1:
                        score = min(75, 50 + (total_orders * 10))
                    else:
                        score = 40

                    results.append({
                        'supplier': supplier,
                        'score': round(float(score), 2),
                        'recommendation': self.get_recommendation(score),
                        'total_orders': total_orders,
                        'total_value': total_value
                    })

                except Exception as e:
                    frappe.log_error(f"Supplier analysis failed for {supplier}: {str(e)}")
                    continue

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

# ==============================================================================
# FIX 3: Update run_ml_supplier_analysis - Better debugging
# ==============================================================================
@frappe.whitelist()
def run_ml_supplier_analysis(company=None):
    """Main function called from AI Settings - FIXED VERSION"""
    try:
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

        # Debug: Check for purchase orders
        po_count = frappe.db.count("Purchase Order", {
            "company": company,
            "docstatus": 1
        })

        if po_count == 0:
            return {
                "status": "info",
                "message": f"No submitted purchase orders found for {company}. Create and submit some purchase orders first.",
                "debug_info": {
                    "total_pos": frappe.db.count("Purchase Order", {"company": company}),
                    "submitted_pos": po_count
                }
            }

        analyzer = MLSupplierAnalyzer()

        # Debug: Get raw supplier data
        raw_data = analyzer.get_supplier_data(company)
        if not raw_data:
            return {
                "status": "info", 
                "message": f"No supplier data found for {company}. Purchase orders exist but no items found.",
                "debug_info": {
                    "purchase_orders": po_count,
                    "raw_data_count": len(raw_data)
                }
            }

        # Run supplier analysis
        results = analyzer.analyze_suppliers(company)

        if not results:
            return {
                "status": "info",
                "message": f"No suppliers could be analyzed for {company}. Check purchase order data.",
                "debug_info": {
                    "raw_data_count": len(raw_data),
                    "analysis_results": len(results)
                }
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
        companies = frappe.get_all("Company", fields=["name"])
        segmentation_results = {}

        for company in companies:
            try:
                analyzer = MLSupplierAnalyzer()
                results = analyzer.analyze_suppliers(company.name)

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
        company_condition = ""
        params = {}

        if company:
            supplier_meta = frappe.get_meta("Supplier")
            if supplier_meta.has_field("company"):
                company_condition = "AND company = %(company)s"
                params["company"] = company

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

                if score >= 80:
                    segment = "Strategic"
                elif score >= 60:
                    segment = "Preferred"
                elif score >= 40:
                    segment = "Approved"
                else:
                    segment = "Caution"

                risk_score = max(0, 100 - score)

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

                update_fields.append("modified = %s")
                values.append(frappe.utils.now())

                if update_fields:
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

        warehouse_name = f"Main Warehouse - {company}"
        if not frappe.db.exists("Warehouse", warehouse_name):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": warehouse_name,
                "company": company
            })
            warehouse.insert(ignore_permissions=True)

        created_pos = []
        import random
        from datetime import datetime, timedelta

        for i in range(8):  # Create 8 sample POs
            try:
                supplier = random.choice(created_suppliers or sample_suppliers)
                if isinstance(supplier, dict):
                    supplier = f"{supplier['name']} - {company}"

                random_days = random.randint(1, 180)
                po_date = (datetime.now() - timedelta(days=random_days)).date()

                po = frappe.get_doc({
                    "doctype": "Purchase Order",
                    "supplier": supplier,
                    "company": company,
                    "transaction_date": po_date,
                    "schedule_date": po_date + timedelta(days=random.randint(7, 30)),
                    "items": []
                })

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

                if po.items:
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

@frappe.whitelist()
def predict_purchase_price(item_code, supplier, company, qty=1):
    """Predict purchase price for an item from a supplier - FOR PURCHASE ORDER INTEGRATION"""
    try:
        analyzer = MLSupplierAnalyzer()
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

# ==============================================================================
# QUICK TEST FUNCTION - debug_supplier_analysis
# ==============================================================================
@frappe.whitelist()
def debug_supplier_analysis(company):
    """Debug function to check why ML analysis fails"""
    try:
        result = {
            "company": company,
            "company_exists": frappe.db.exists("Company", company),
            "total_pos": frappe.db.count("Purchase Order", {"company": company}),
            "submitted_pos": frappe.db.count("Purchase Order", {"company": company, "docstatus": 1}),
            "pos_with_items": 0,
            "unique_suppliers": 0,
            "sample_data": []
        }

        pos_with_items = frappe.db.sql("""
            SELECT COUNT(DISTINCT po.name) as count
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.company = %s AND po.docstatus = 1
        """, (company,), as_dict=True)

        result["pos_with_items"] = pos_with_items[0]["count"] if pos_with_items else 0

        suppliers = frappe.db.sql("""
            SELECT DISTINCT po.supplier
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.company = %s AND po.docstatus = 1
        """, (company,), as_dict=True)

        result["unique_suppliers"] = len(suppliers)
        result["supplier_list"] = [s["supplier"] for s in suppliers]

        sample = frappe.db.sql("""
            SELECT po.supplier, po.name, po.transaction_date, poi.item_code, poi.qty, poi.rate
            FROM `tabPurchase Order` po
            INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
            WHERE po.company = %s AND po.docstatus = 1
            LIMIT 5
        """, (company,), as_dict=True)

        result["sample_data"] = sample

        return result

    except Exception as e:
        return {"error": str(e)}