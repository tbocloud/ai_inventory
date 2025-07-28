# ai_inventory/ai_inventory/utils/inventory_analytics.py
# Advanced Data Science Helper Module for Inventory Analytics

import frappe
from frappe.utils import flt, nowdate, add_days, getdate, cint
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import math
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class InventoryAnalytics:
    """Advanced inventory analytics with machine learning capabilities"""
    
    def __init__(self, company=None):
        self.company = company
        self.scaler = StandardScaler()
    
    def perform_abc_analysis(self, items_data):
        """Perform ABC analysis based on consumption value and frequency"""
        try:
            if not items_data:
                return items_data
            
            df = pd.DataFrame(items_data)
            
            # Calculate annual consumption value
            df['annual_consumption_value'] = (
                df['predicted_consumption'] * 12 * df['predicted_price']
            )
            
            # Sort by consumption value
            df = df.sort_values('annual_consumption_value', ascending=False)
            
            # Calculate cumulative percentage
            df['cumulative_value'] = df['annual_consumption_value'].cumsum()
            total_value = df['annual_consumption_value'].sum()
            
            if total_value > 0:
                df['cumulative_percentage'] = (df['cumulative_value'] / total_value) * 100
                
                # Assign ABC classes
                df['abc_class'] = df['cumulative_percentage'].apply(
                    lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C')
                )
            else:
                df['abc_class'] = 'C'
            
            return df.to_dict('records')
            
        except Exception as e:
            frappe.log_error(f"ABC analysis failed: {str(e)}")
            return items_data
    
    def calculate_demand_variability(self, item_code, warehouse, company):
        """Calculate demand variability and coefficient of variation"""
        try:
            # Get daily consumption for last 90 days
            daily_consumption = frappe.db.sql("""
                SELECT 
                    DATE(sle.posting_date) as date,
                    SUM(ABS(sle.actual_qty)) as daily_qty
                FROM `tabStock Ledger Entry` sle
                INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
                WHERE sle.item_code = %s 
                AND sle.warehouse = %s
                AND w.company = %s
                AND sle.actual_qty < 0
                AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                GROUP BY DATE(sle.posting_date)
                ORDER BY date
            """, (item_code, warehouse, company), as_dict=True)
            
            if len(daily_consumption) < 7:
                return {
                    'coefficient_of_variation': 1.0,
                    'demand_variability': 'High',
                    'forecast_accuracy': 'Low'
                }
            
            quantities = [d['daily_qty'] for d in daily_consumption]
            mean_qty = np.mean(quantities)
            std_qty = np.std(quantities)
            
            cv = std_qty / mean_qty if mean_qty > 0 else 1.0
            
            # Classify variability
            if cv < 0.3:
                variability = 'Low'
                accuracy = 'High'
            elif cv < 0.7:
                variability = 'Medium'
                accuracy = 'Medium'
            else:
                variability = 'High'
                accuracy = 'Low'
            
            return {
                'coefficient_of_variation': round(cv, 3),
                'demand_variability': variability,
                'forecast_accuracy': accuracy
            }
            
        except Exception as e:
            frappe.log_error(f"Demand variability calculation failed: {str(e)}")
            return {
                'coefficient_of_variation': 1.0,
                'demand_variability': 'Unknown',
                'forecast_accuracy': 'Unknown'
            }
    
    def detect_seasonal_patterns(self, item_code, warehouse, company):
        """Detect seasonal patterns using Fourier analysis"""
        try:
            # Get monthly consumption for 24 months
            monthly_data = frappe.db.sql("""
                SELECT 
                    YEAR(sle.posting_date) as year,
                    MONTH(sle.posting_date) as month,
                    SUM(ABS(sle.actual_qty)) as monthly_qty
                FROM `tabStock Ledger Entry` sle
                INNER JOIN `tabWarehouse` w ON w.name = sle.warehouse
                WHERE sle.item_code = %s 
                AND sle.warehouse = %s
                AND w.company = %s
                AND sle.actual_qty < 0
                AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 24 MONTH)
                GROUP BY YEAR(sle.posting_date), MONTH(sle.posting_date)
                ORDER BY year, month
            """, (item_code, warehouse, company), as_dict=True)
            
            if len(monthly_data) < 12:
                return {
                    'seasonality_detected': False,
                    'seasonal_strength': 0,
                    'peak_months': [],
                    'low_months': []
                }
            
            quantities = [d['monthly_qty'] for d in monthly_data]
            
            # Simple seasonality detection using coefficient of variation
            mean_qty = np.mean(quantities)
            cv = np.std(quantities) / mean_qty if mean_qty > 0 else 0
            
            seasonality_detected = cv > 0.5
            seasonal_strength = min(cv, 1.0)
            
            # Identify peak and low months
            if seasonality_detected and len(monthly_data) >= 12:
                # Group by month across years
                month_averages = defaultdict(list)
                for d in monthly_data:
                    month_averages[d['month']].append(d['monthly_qty'])
                
                month_stats = {}
                for month, quantities in month_averages.items():
                    month_stats[month] = np.mean(quantities)
                
                overall_mean = np.mean(list(month_stats.values()))
                
                peak_months = [month for month, avg in month_stats.items() 
                              if avg > overall_mean * 1.2]
                low_months = [month for month, avg in month_stats.items() 
                             if avg < overall_mean * 0.8]
            else:
                peak_months = []
                low_months = []
            
            return {
                'seasonality_detected': seasonality_detected,
                'seasonal_strength': round(seasonal_strength, 3),
                'peak_months': peak_months,
                'low_months': low_months
            }
            
        except Exception as e:
            frappe.log_error(f"Seasonal pattern detection failed: {str(e)}")
            return {
                'seasonality_detected': False,
                'seasonal_strength': 0,
                'peak_months': [],
                'low_months': []
            }
    
    def cluster_items_by_behavior(self, items_data):
        """Cluster items based on consumption behavior using K-means"""
        try:
            if len(items_data) < 5:
                return items_data
            
            df = pd.DataFrame(items_data)
            
            # Prepare features for clustering
            features = []
            feature_names = []
            
            if 'predicted_consumption' in df.columns:
                features.append(df['predicted_consumption'].fillna(0))
                feature_names.append('consumption')
            
            if 'volatility_index' in df.columns:
                features.append(df['volatility_index'].fillna(1))
                feature_names.append('volatility')
            
            if 'confidence_score' in df.columns:
                features.append(df['confidence_score'].fillna(50))
                feature_names.append('confidence')
            
            if 'current_stock' in df.columns:
                features.append(df['current_stock'].fillna(0))
                feature_names.append('stock')
            
            if len(features) < 2:
                return items_data
            
            # Create feature matrix
            X = np.column_stack(features)
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Determine optimal number of clusters (3-6)
            n_clusters = min(6, max(3, len(items_data) // 10))
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Assign cluster labels
            cluster_names = {
                0: 'High Volume/Low Risk',
                1: 'Medium Volume/Medium Risk', 
                2: 'Low Volume/High Risk',
                3: 'Critical/Volatile',
                4: 'Stable/Predictable',
                5: 'Irregular/Seasonal'
            }
            
            df['behavior_cluster'] = [cluster_names.get(c, f'Cluster {c}') for c in clusters]
            
            return df.to_dict('records')
            
        except Exception as e:
            frappe.log_error(f"Item clustering failed: {str(e)}")
            return items_data
    
    def calculate_inventory_health_score(self, item_data):
        """Calculate overall inventory health score (0-100)"""
        try:
            score = 50  # Base score
            
            # Stock level health (25 points)
            current_stock = item_data.get('current_stock', 0)
            reorder_level = item_data.get('reorder_level', 0)
            
            if reorder_level > 0:
                stock_ratio = current_stock / reorder_level
                if stock_ratio >= 1.5:
                    score += 25  # Healthy stock
                elif stock_ratio >= 1.0:
                    score += 15  # Adequate stock
                elif stock_ratio >= 0.5:
                    score += 5   # Low stock
                else:
                    score -= 10  # Critical stock
            
            # Forecast confidence (25 points) 
            confidence = item_data.get('confidence_score', 0)
            confidence_points = (confidence / 100) * 25
            score += confidence_points
            
            # Movement type health (20 points)
            movement_type = item_data.get('movement_type', '')
            movement_scores = {
                'Fast Moving': 20,
                'Slow Moving': 10,
                'Non Moving': 0,
                'Critical': -5
            }
            score += movement_scores.get(movement_type, 5)
            
            # Demand stability (15 points)
            volatility = item_data.get('volatility_index', 1.0)
            if volatility <= 0.5:
                score += 15  # Very stable
            elif volatility <= 1.0:
                score += 10  # Stable
            elif volatility <= 1.5:
                score += 5   # Moderate
            else:
                score -= 5   # Volatile
            
            # Recent forecast accuracy (15 points)
            last_forecast_date = item_data.get('last_forecast_date')
            if last_forecast_date:
                days_since_forecast = (datetime.now() - getdate(last_forecast_date)).days
                if days_since_forecast <= 7:
                    score += 15  # Very recent
                elif days_since_forecast <= 30:
                    score += 10  # Recent
                elif days_since_forecast <= 90:
                    score += 5   # Somewhat recent
                else:
                    score -= 5   # Outdated
            
            return max(0, min(100, round(score, 1)))
            
        except Exception as e:
            frappe.log_error(f"Health score calculation failed: {str(e)}")
            return 50
    
    def generate_procurement_recommendations(self, items_data):
        """Generate intelligent procurement recommendations"""
        recommendations = []
        
        try:
            for item in items_data:
                item_code = item.get('item_code')
                current_stock = item.get('current_stock', 0)
                reorder_level = item.get('reorder_level', 0)
                suggested_qty = item.get('suggested_qty', 0)
                movement_type = item.get('movement_type', '')
                confidence_score = item.get('confidence_score', 0)
                
                # Generate specific recommendations
                if item.get('reorder_alert'):
                    if movement_type == 'Critical':
                        priority = 'URGENT'
                        action = f"Immediate procurement needed for {item_code}"
                        reason = "Critical item with stock below reorder level"
                    elif movement_type == 'Fast Moving':
                        priority = 'HIGH'
                        action = f"Fast-track procurement for {item_code}"
                        reason = "High-velocity item approaching stockout"
                    else:
                        priority = 'MEDIUM'
                        action = f"Schedule procurement for {item_code}"
                        reason = "Stock below reorder level"
                    
                    recommendations.append({
                        'item_code': item_code,
                        'priority': priority,
                        'action': action,
                        'reason': reason,
                        'suggested_qty': suggested_qty,
                        'current_stock': current_stock,
                        'confidence': confidence_score
                    })
                
                elif movement_type == 'Non Moving' and current_stock > reorder_level * 2:
                    recommendations.append({
                        'item_code': item_code,
                        'priority': 'LOW',
                        'action': f"Consider reducing stock for {item_code}",
                        'reason': "Non-moving item with excess stock",
                        'suggested_qty': 0,
                        'current_stock': current_stock,
                        'confidence': confidence_score
                    })
            
            # Sort by priority
            priority_order = {'URGENT': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
            
            return recommendations[:50]  # Return top 50 recommendations
            
        except Exception as e:
            frappe.log_error(f"Procurement recommendations failed: {str(e)}")
            return []
    
    def perform_supplier_performance_analysis(self, supplier, company=None):
        """Analyze supplier performance metrics"""
        try:
            # Get supplier performance data
            performance_data = frappe.db.sql("""
                SELECT 
                    po.supplier,
                    COUNT(DISTINCT po.name) as total_orders,
                    AVG(DATEDIFF(pr.posting_date, po.schedule_date)) as avg_delivery_delay,
                    COUNT(DISTINCT CASE WHEN pr.posting_date <= po.schedule_date THEN po.name END) as on_time_deliveries,
                    AVG(poi.rate) as avg_price,
                    COUNT(DISTINCT poi.item_code) as unique_items,
                    AVG(po.grand_total) as avg_order_value
                FROM `tabPurchase Order` po
                LEFT JOIN `tabPurchase Receipt` pr ON pr.purchase_order = po.name
                LEFT JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
                WHERE po.supplier = %s
                AND po.docstatus = 1
                AND po.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                {}
                GROUP BY po.supplier
            """.format("AND po.company = %(company)s" if company else ""), 
            (supplier, company) if company else (supplier,), as_dict=True)
            
            if not performance_data:
                return {
                    'supplier': supplier,
                    'performance_score': 50,
                    'on_time_delivery_rate': 0,
                    'avg_delivery_delay': 0,
                    'price_consistency': 0,
                    'recommendation': 'Insufficient data'
                }
            
            data = performance_data[0]
            
            # Calculate performance score
            on_time_rate = (data.get('on_time_deliveries', 0) / 
                           max(data.get('total_orders', 1), 1)) * 100
            
            avg_delay = abs(data.get('avg_delivery_delay', 0))
            
            # Performance scoring
            score = 50  # Base score
            
            # On-time delivery (40 points)
            if on_time_rate >= 95:
                score += 40
            elif on_time_rate >= 85:
                score += 30
            elif on_time_rate >= 75:
                score += 20
            elif on_time_rate >= 60:
                score += 10
            
            # Delivery delay penalty (20 points)
            if avg_delay <= 1:
                score += 20
            elif avg_delay <= 3:
                score += 15
            elif avg_delay <= 7:
                score += 10
            
            # Order consistency (10 points)
            if data.get('total_orders', 0) >= 10:
                score += 10
            elif data.get('total_orders', 0) >= 5:
                score += 5
            
            # Generate recommendation
            if score >= 80:
                recommendation = 'Preferred Supplier'
            elif score >= 60:
                recommendation = 'Good Supplier'
            elif score >= 40:
                recommendation = 'Average Supplier'
            else:
                recommendation = 'Review Required'
            
            return {
                'supplier': supplier,
                'performance_score': round(score, 1),
                'on_time_delivery_rate': round(on_time_rate, 1),
                'avg_delivery_delay': round(avg_delay, 1),
                'total_orders': data.get('total_orders', 0),
                'avg_order_value': data.get('avg_order_value', 0),
                'unique_items': data.get('unique_items', 0),
                'recommendation': recommendation
            }
            
        except Exception as e:
            frappe.log_error(f"Supplier performance analysis failed: {str(e)}")
            return {
                'supplier': supplier,
                'performance_score': 50,
                'recommendation': 'Analysis failed'
            }

# Utility functions for the main report
def get_advanced_analytics_data(items_data, filters=None):
    """Get advanced analytics for the dashboard"""
    try:
        company = filters.get('company') if filters else None
        analytics = InventoryAnalytics(company)
        
        # Perform ABC analysis
        items_data = analytics.perform_abc_analysis(items_data)
        
        # Add health scores
        for item in items_data:
            item['health_score'] = analytics.calculate_inventory_health_score(item)
        
        # Cluster items by behavior
        items_data = analytics.cluster_items_by_behavior(items_data)
        
        # Generate recommendations
        recommendations = analytics.generate_procurement_recommendations(items_data)
        
        return {
            'items_data': items_data,
            'recommendations': recommendations
        }
        
    except Exception as e:
        frappe.log_error(f"Advanced analytics failed: {str(e)}")
        return {
            'items_data': items_data,
            'recommendations': []
        }

@frappe.whitelist()
def get_supplier_analytics(supplier, company=None):
    """Get supplier performance analytics"""
    analytics = InventoryAnalytics(company)
    return analytics.perform_supplier_performance_analysis(supplier, company)

@frappe.whitelist()
def get_item_demand_analysis(item_code, warehouse, company):
    """Get detailed demand analysis for an item"""
    analytics = InventoryAnalytics(company)
    
    variability = analytics.calculate_demand_variability(item_code, warehouse, company)
    seasonality = analytics.detect_seasonal_patterns(item_code, warehouse, company)
    
    return {
        'item_code': item_code,
        'demand_variability': variability,
        'seasonality': seasonality
    }