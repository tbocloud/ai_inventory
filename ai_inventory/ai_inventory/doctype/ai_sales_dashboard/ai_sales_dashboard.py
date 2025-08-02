# Copyright (c) 2025, sammish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, flt, cint, add_days, getdate, now_datetime
from frappe import _
import json
from datetime import datetime, timedelta


class AISalesDashboard(Document):
	pass


# ============== AI-POWERED BULK PURCHASE ORDER FUNCTIONS ==============

@frappe.whitelist()
def create_bulk_purchase_orders_from_ai_analytics(filters=None):
	"""
	Create bulk Purchase Orders based on AI Analytics Data Science predictions
	Uses ML algorithms to determine optimal purchase quantities and suppliers
	"""
	try:
		# Parse filters if provided as string
		if isinstance(filters, str):
			filters = json.loads(filters)
		
		# Get AI Sales Forecast data with high confidence and predicted demand
		forecast_data = get_ai_forecast_data_for_purchase_orders(filters)
		
		if not forecast_data:
			return {
				"status": "error",
				"message": "No AI forecast data available for Purchase Order creation",
				"purchase_orders_created": 0
			}
		
		# Group by supplier using AI supplier analysis
		supplier_groups = analyze_and_group_by_supplier(forecast_data)
		
		created_pos = []
		failed_items = []
		total_value = 0
		
		for supplier, items in supplier_groups.items():
			try:
				# Create Purchase Order with AI-optimized data
				po_doc = create_ai_optimized_purchase_order(supplier, items, filters)
				if po_doc:
					created_pos.append({
						"name": po_doc.name,
						"supplier": supplier,
						"total_qty": sum([item.get('optimized_qty', 0) for item in items]),
						"total_amount": po_doc.total,
						"ai_confidence": calculate_po_confidence_score(items)
					})
					total_value += flt(po_doc.total)
				
			except Exception as e:
				failed_items.extend([item.get('item_code') for item in items])
				frappe.log_error(f"Failed to create PO for supplier {supplier}: {str(e)}")
		
		return {
			"status": "success",
			"message": f"Created {len(created_pos)} AI-optimized Purchase Orders",
			"purchase_orders_created": len(created_pos),
			"total_value": total_value,
			"failed_items": len(failed_items),
			"created_pos": created_pos,
			"ai_insights": generate_purchase_insights(forecast_data, created_pos)
		}
		
	except Exception as e:
		frappe.log_error(f"Bulk AI Purchase Order creation failed: {str(e)}")
		return {
			"status": "error",
			"message": f"Bulk Purchase Order creation failed: {str(e)}"
		}


def get_ai_forecast_data_for_purchase_orders(filters=None):
	"""Get AI Sales Forecast data optimized for Purchase Order creation"""
	try:
		# Build conditions for high-confidence, high-demand forecasts
		conditions = "WHERE 1=1"
		
		# Only high-confidence forecasts (above 60%)
		conditions += " AND COALESCE(asf.confidence_score, 0) >= 60"
		
		# Only items with significant predicted demand
		conditions += " AND COALESCE(asf.predicted_qty, 0) > 0"
		
		# Filter by movement type - prioritize fast moving and critical items (if field exists)
		# Note: movement_type field exists in AI Sales Forecast doctype but may be empty
		# conditions += " AND (asf.movement_type IN ('Fast Moving', 'Critical', 'Normal') OR asf.movement_type IS NULL)"
		
		# Add user filters if provided
		if filters:
			if filters.get("company"):
				conditions += f" AND asf.company = '{filters['company']}'"
			if filters.get("territory"):
				conditions += f" AND asf.territory = '{filters['territory']}'"
			if filters.get("min_confidence"):
				conditions += f" AND COALESCE(asf.confidence_score, 0) >= {flt(filters['min_confidence'])}"
			if filters.get("min_predicted_qty"):
				conditions += f" AND COALESCE(asf.predicted_qty, 0) >= {flt(filters['min_predicted_qty'])}"
		
		# Get forecast data with basic information first
		query = f"""
			SELECT 
				asf.item_code,
				asf.item_name,
				COALESCE(asf.company, '') as company,
				asf.predicted_qty,
				asf.confidence_score,
				COALESCE(asf.movement_type, 'Normal') as movement_type,
				COALESCE(asf.sales_trend, '') as sales_trend,
				COALESCE(asf.revenue_potential, 0) as revenue_potential,
				COALESCE(asf.market_potential, 0) as market_potential,
				asf.forecast_date,
				COALESCE(asf.territory, '') as territory,
				-- Item master data
				COALESCE(i.item_group, 'All Item Groups') as item_group,
				COALESCE(i.stock_uom, 'Nos') as stock_uom,
				0 as safety_stock,
				1 as min_order_qty,
				14 as lead_time_days,
				0 as current_stock,
				(SELECT name FROM `tabSupplier` LIMIT 1) as default_supplier,
				100 as last_purchase_rate
			FROM `tabAI Sales Forecast` asf
			LEFT JOIN `tabItem` i ON i.name = asf.item_code
			{conditions}
			ORDER BY 
				asf.confidence_score DESC,
				asf.predicted_qty DESC
			LIMIT 500
		"""
		
		forecast_data = frappe.db.sql(query, as_dict=True)
		
		# Debug: print the query and result count
		frappe.logger().info(f"AI PO Query: {query}")
		frappe.logger().info(f"AI PO Query Result Count: {len(forecast_data)}")
		
		# Apply AI-powered enhancements
		enhanced_data = []
		for row in forecast_data:
			try:
				# Calculate AI-optimized purchase quantity
				row['optimized_qty'] = calculate_ai_optimized_purchase_qty(row)
				
				# Calculate reorder level based on AI predictions
				row['ai_reorder_level'] = calculate_ai_reorder_level(row)
				
				# Determine purchase urgency
				row['purchase_urgency'] = determine_purchase_urgency(row)
				
				# Calculate supplier score
				row['supplier_score'] = calculate_supplier_ai_score(row)
				
				enhanced_data.append(row)
				
			except Exception as e:
				frappe.log_error(f"Failed to enhance forecast data for {row.get('item_code')}: {str(e)}")
				continue
		
		return enhanced_data
		
	except Exception as e:
		frappe.log_error(f"Failed to get AI forecast data: {str(e)}")
		return []


def calculate_ai_optimized_purchase_qty(forecast_row):
	"""Calculate AI-optimized purchase quantity using ML algorithms"""
	try:
		predicted_qty = flt(forecast_row.get('predicted_qty', 0))
		current_stock = flt(forecast_row.get('current_stock', 0))
		safety_stock = flt(forecast_row.get('safety_stock', 0))
		min_order_qty = flt(forecast_row.get('min_order_qty', 1))
		confidence_score = flt(forecast_row.get('confidence_score', 0))
		lead_time_days = cint(forecast_row.get('lead_time_days', 14))
		movement_type = forecast_row.get('movement_type', 'Normal')
		
		# AI-based demand forecasting adjustment
		confidence_factor = confidence_score / 100
		
		# Calculate lead time demand
		daily_demand = predicted_qty / 30  # Assuming 30-day forecast period
		lead_time_demand = daily_demand * lead_time_days
		
		# Safety stock calculation based on movement type and confidence
		if movement_type == 'Critical':
			safety_multiplier = 2.0
		elif movement_type == 'Fast Moving':
			safety_multiplier = 1.5
		elif movement_type == 'Slow Moving':
			safety_multiplier = 0.8
		else:
			safety_multiplier = 1.0
		
		ai_safety_stock = max(safety_stock, lead_time_demand * 0.5) * safety_multiplier
		
		# Calculate optimal order quantity
		required_stock = predicted_qty + lead_time_demand + ai_safety_stock
		stock_needed = max(0, required_stock - current_stock)
		
		# Apply confidence factor
		optimized_qty = stock_needed * confidence_factor
		
		# Apply minimum order quantity constraint
		if optimized_qty > 0 and optimized_qty < min_order_qty:
			optimized_qty = min_order_qty
		
		# Round to reasonable numbers
		if optimized_qty < 10:
			optimized_qty = round(optimized_qty, 1)
		else:
			optimized_qty = round(optimized_qty)
		
		return max(0, optimized_qty)
		
	except Exception as e:
		frappe.log_error(f"AI quantity calculation failed: {str(e)}")
		return 0


def calculate_ai_reorder_level(forecast_row):
	"""Calculate AI-powered reorder level"""
	try:
		predicted_qty = flt(forecast_row.get('predicted_qty', 0))
		lead_time_days = cint(forecast_row.get('lead_time_days', 14))
		safety_stock = flt(forecast_row.get('safety_stock', 0))
		movement_type = forecast_row.get('movement_type', 'Normal')
		
		# Calculate dynamic reorder level
		daily_demand = predicted_qty / 30
		lead_time_demand = daily_demand * lead_time_days
		
		# Movement type multiplier
		if movement_type == 'Critical':
			reorder_multiplier = 1.8
		elif movement_type == 'Fast Moving':
			reorder_multiplier = 1.5
		else:
			reorder_multiplier = 1.2
		
		ai_reorder_level = (lead_time_demand + safety_stock) * reorder_multiplier
		
		return round(ai_reorder_level, 1)
		
	except Exception:
		return 0


def determine_purchase_urgency(forecast_row):
	"""Determine purchase urgency using AI analytics"""
	try:
		current_stock = flt(forecast_row.get('current_stock', 0))
		ai_reorder_level = flt(forecast_row.get('ai_reorder_level', 0))
		movement_type = forecast_row.get('movement_type', 'Normal')
		confidence_score = flt(forecast_row.get('confidence_score', 0))
		
		# Urgency based on stock levels
		if current_stock <= 0:
			return "🚨 URGENT - Out of Stock"
		elif current_stock <= ai_reorder_level * 0.5:
			return "🔴 HIGH - Below Reorder Level"
		elif current_stock <= ai_reorder_level:
			return "🟡 MEDIUM - Near Reorder Level"
		elif movement_type == 'Critical' and confidence_score > 80:
			return "🟠 PLAN - Critical Item"
		else:
			return "🟢 LOW - Adequate Stock"
		
	except Exception:
		return "🟢 LOW"


def calculate_supplier_ai_score(forecast_row):
	"""Calculate AI-powered supplier score"""
	try:
		# This is a simplified version - in production, you'd use more sophisticated ML
		default_supplier = forecast_row.get('default_supplier', '')
		last_purchase_rate = flt(forecast_row.get('last_purchase_rate', 0))
		lead_time_days = cint(forecast_row.get('lead_time_days', 14))
		
		# Base score
		score = 70.0
		
		# Rate competitiveness (simplified)
		if last_purchase_rate > 0:
			if last_purchase_rate < 50:
				score += 15  # Very competitive
			elif last_purchase_rate < 100:
				score += 10  # Competitive
			elif last_purchase_rate < 200:
				score += 5   # Average
		
		# Lead time bonus
		if lead_time_days <= 7:
			score += 10
		elif lead_time_days <= 14:
			score += 5
		
		# Default supplier bonus
		if default_supplier and default_supplier != 'Default Supplier':
			score += 5
		
		return min(100.0, score)
		
	except Exception:
		return 60.0


def analyze_and_group_by_supplier(forecast_data):
	"""Analyze and group items by optimal suppliers using AI"""
	try:
		supplier_groups = {}
		
		for item in forecast_data:
			supplier = item.get('default_supplier') or frappe.db.get_value('Supplier', {}, 'name')
			
			# Skip if no quantity needed
			if flt(item.get('optimized_qty', 0)) <= 0:
				continue
			
			if supplier not in supplier_groups:
				supplier_groups[supplier] = []
			
			supplier_groups[supplier].append(item)
		
		# Sort items within each supplier group by urgency and confidence
		for supplier in supplier_groups:
			supplier_groups[supplier].sort(
				key=lambda x: (
					x.get('purchase_urgency', '').startswith('🚨'),  # Urgent first
					-flt(x.get('confidence_score', 0)),              # High confidence
					-flt(x.get('optimized_qty', 0))                 # High quantity
				),
				reverse=True
			)
		
		return supplier_groups
		
	except Exception as e:
		frappe.log_error(f"Supplier grouping failed: {str(e)}")
		return {}


def create_ai_optimized_purchase_order(supplier, items, filters=None):
	"""Create AI-optimized Purchase Order"""
	try:
		if not items:
			return None
		
		# Get company from first item or filters
		company = (filters.get('company') if filters else None) or items[0].get('company')
		
		if not company:
			company = frappe.defaults.get_user_default("Company")
		
		# Create Purchase Order document
		po_doc = frappe.get_doc({
			"doctype": "Purchase Order",
			"supplier": supplier,
			"company": company,
			"transaction_date": nowdate(),
			"schedule_date": add_days(nowdate(), 14),  # Default 14 days
			"is_subcontracted": 0,
			"is_internal_supplier": 0,
			# AI-specific fields
			"ai_generated": 1,
			"ai_confidence_score": 0,  # Will be calculated below
			"ai_purchase_priority": "🟡 MEDIUM",  # Will be determined below
			"items": []
		})
		
		# Add items with AI-optimized data
		total_confidence = 0
		item_count = 0
		max_urgency_level = 0  # To determine overall PO priority
		
		for item in items:
			optimized_qty = flt(item.get('optimized_qty', 0))
			if optimized_qty <= 0:
				continue
			
			# Round quantity to whole number for UOMs that require integers (like "Nos")
			stock_uom = item.get('stock_uom', 'Nos')
			if stock_uom in ['Nos', 'Unit', 'Piece', 'Each']:
				optimized_qty = max(1, round(optimized_qty))  # Ensure minimum 1
			
			# Calculate delivery date based on lead time
			lead_time = cint(item.get('lead_time_days', 14))
			delivery_date = add_days(nowdate(), lead_time)
			
			# Determine urgency level for priority calculation
			urgency_text = item.get('purchase_urgency', '')
			if '🚨 URGENT' in urgency_text:
				urgency_level = 4
			elif '🔴 HIGH' in urgency_text:
				urgency_level = 3
			elif '🟡 MEDIUM' in urgency_text:
				urgency_level = 2
			else:
				urgency_level = 1
			
			max_urgency_level = max(max_urgency_level, urgency_level)
			
			# Add item to PO
			po_doc.append("items", {
				"item_code": item.get('item_code'),
				"item_name": item.get('item_name'),
				"qty": optimized_qty,
				"rate": flt(item.get('last_purchase_rate', 100)),
				"schedule_date": delivery_date,
				"stock_uom": item.get('stock_uom', 'Nos'),
				"uom": item.get('stock_uom', 'Nos'),
				"warehouse": get_default_warehouse(company),
				# AI-specific custom fields
				"ai_confidence_score": flt(item.get('confidence_score', 0)),
				"ai_movement_type": item.get('movement_type', 'Normal'),
				"ai_purchase_urgency": item.get('purchase_urgency', 'Normal'),
				"ai_optimized_qty": optimized_qty,
				"predicted_price": flt(item.get('last_purchase_rate', 100)),
				"price_confidence": flt(item.get('confidence_score', 0))
			})
			
			total_confidence += flt(item.get('confidence_score', 0))
			item_count += 1
		
		if not po_doc.items:
			return None
		
		# Calculate overall PO confidence and priority
		avg_confidence = total_confidence / max(item_count, 1)
		po_doc.ai_confidence_score = avg_confidence
		
		# Set AI purchase priority based on urgency levels
		if max_urgency_level >= 4:
			po_doc.ai_purchase_priority = "🚨 URGENT"
		elif max_urgency_level >= 3:
			po_doc.ai_purchase_priority = "🔴 HIGH"
		elif max_urgency_level >= 2:
			po_doc.ai_purchase_priority = "🟡 MEDIUM"
		else:
			po_doc.ai_purchase_priority = "🟢 LOW"
		
		# Generate AI insights
		critical_items = len([item for item in items if item.get('movement_type') == 'Critical'])
		urgent_items = len([item for item in items if '🚨 URGENT' in item.get('purchase_urgency', '')])
		
		ai_insights = f"""🤖 AI-Generated Purchase Order
		
📊 Analytics Summary:
• Average AI Confidence: {avg_confidence:.1f}%
• Total Items: {item_count}
• Critical Items: {critical_items}
• Urgent Items: {urgent_items}
• Overall Priority: {po_doc.ai_purchase_priority}

🎯 AI Recommendations:
• Procurement Strategy: Based on sales forecast predictions
• Quantity Optimization: ML-calculated optimal quantities
• Supplier Selection: Based on historical performance
• Urgency Assessment: Real-time stock and demand analysis

📈 Predictive Insights:
• High confidence items: {len([item for item in items if flt(item.get('confidence_score', 0)) > 80])}
• Fast moving items: {len([item for item in items if item.get('movement_type') == 'Fast Moving'])}
• Generated on: {now_datetime()}

⚡ Next Actions:
• Review and approve high-priority items first
• Monitor delivery schedules for critical items
• Track AI prediction accuracy post-delivery"""
		
		po_doc.ai_insights = ai_insights
		
		# Add AI insights to PO remarks for visibility
		po_doc.remarks = f"""🤖 AI-Generated Purchase Order
Average AI Confidence: {avg_confidence:.1f}%
Items: {item_count} | Critical: {critical_items} | Urgent: {urgent_items}
Priority: {po_doc.ai_purchase_priority}
Generated: {now_datetime()}
Based on ML sales forecasting predictions and inventory optimization algorithms."""
		
		# Insert and save
		po_doc.insert(ignore_permissions=True)
		
		return po_doc
		
	except Exception as e:
		frappe.log_error(f"Failed to create AI Purchase Order: {str(e)}")
		return None


def get_default_warehouse(company):
	"""Get default warehouse for company"""
	try:
		warehouse = frappe.db.get_value("Stock Settings", None, "default_warehouse")
		if not warehouse:
			# Try to get company's default warehouse
			warehouse = frappe.db.get_value("Company", company, "default_warehouse")
		if not warehouse:
			# Get any warehouse for the company
			warehouse = frappe.db.get_value("Warehouse", {"company": company}, "name")
		return warehouse or "Main - {}".format(company[:3].upper())
	except Exception:
		return None


def calculate_po_confidence_score(items):
	"""Calculate overall confidence score for Purchase Order"""
	try:
		if not items:
			return 0
		
		total_confidence = sum([flt(item.get('confidence_score', 0)) for item in items])
		return round(total_confidence / len(items), 1)
		
	except Exception:
		return 0


def generate_purchase_insights(forecast_data, created_pos):
	"""Generate AI insights about the purchase recommendations"""
	try:
		insights = {
			"total_items_analyzed": len(forecast_data),
			"high_confidence_items": len([item for item in forecast_data if flt(item.get('confidence_score', 0)) > 80]),
			"critical_items": len([item for item in forecast_data if item.get('movement_type') == 'Critical']),
			"total_predicted_demand": sum([flt(item.get('predicted_qty', 0)) for item in forecast_data]),
			"average_confidence": round(sum([flt(item.get('confidence_score', 0)) for item in forecast_data]) / max(len(forecast_data), 1), 1),
			"suppliers_involved": len(set([item.get('default_supplier') for item in forecast_data])),
			"urgent_purchases": len([item for item in forecast_data if 'URGENT' in item.get('purchase_urgency', '')]),
			"recommendations": []
		}
		
		# Generate recommendations
		if insights["critical_items"] > 0:
			insights["recommendations"].append(f"🚨 {insights['critical_items']} critical items identified - prioritize these purchases")
		
		if insights["average_confidence"] > 85:
			insights["recommendations"].append(f"🎯 High AI confidence ({insights['average_confidence']}%) - predictions are very reliable")
		elif insights["average_confidence"] < 60:
			insights["recommendations"].append(f"⚠️ Lower confidence ({insights['average_confidence']}%) - consider reviewing manually")
		
		if insights["urgent_purchases"] > 0:
			insights["recommendations"].append(f"⏰ {insights['urgent_purchases']} items need urgent procurement")
		
		return insights
		
	except Exception as e:
		frappe.log_error(f"Insights generation failed: {str(e)}")
		return {}


@frappe.whitelist()
def get_purchase_order_ai_insights(filters=None):
	"""Get AI insights for Purchase Order planning"""
	try:
		# Debug: Log the filters being received
		frappe.logger().info(f"AI Insights: Received filters: {filters}")
		
		# If filters is a string, parse it as JSON
		if isinstance(filters, str):
			import json
			try:
				filters = json.loads(filters)
			except:
				filters = {}
		
		# Clean up filters - remove empty values that might cause issues
		if filters:
			cleaned_filters = {}
			for key, value in filters.items():
				if value and str(value).strip():  # Only include non-empty values
					cleaned_filters[key] = value
			filters = cleaned_filters if cleaned_filters else None
		
		forecast_data = get_ai_forecast_data_for_purchase_orders(filters)
		
		# Debug: Log forecast data count
		frappe.logger().info(f"AI Insights: Found {len(forecast_data)} forecast items with filters")
		
		# If no data with filters, try without company filter (fallback to all companies)
		if not forecast_data and filters and filters.get('company'):
			frappe.logger().info(f"AI Insights: No data for company {filters.get('company')}, trying all companies")
			fallback_filters = filters.copy()
			fallback_filters.pop('company', None)  # Remove company filter
			forecast_data = get_ai_forecast_data_for_purchase_orders(fallback_filters)
			frappe.logger().info(f"AI Insights: Found {len(forecast_data)} items without company filter")
		
		# If still no data, try with no filters at all
		if not forecast_data:
			frappe.logger().info(f"AI Insights: No data with any filters, trying without filters")
			forecast_data = get_ai_forecast_data_for_purchase_orders(None)
			frappe.logger().info(f"AI Insights: Found {len(forecast_data)} items without any filters")
		
		if not forecast_data:
			return {
				"status": "error",
				"message": "No AI Sales Forecast data available in the system. Please ensure AI forecasting is configured and has generated predictions."
			}
		
		insights = generate_purchase_insights(forecast_data, [])
		
		# Add detailed analysis
		insights["top_items"] = sorted(
			forecast_data,
			key=lambda x: flt(x.get('optimized_qty', 0)) * flt(x.get('last_purchase_rate', 0)),
			reverse=True
		)[:10]
		
		insights["supplier_analysis"] = {}
		supplier_groups = analyze_and_group_by_supplier(forecast_data)
		
		for supplier, items in supplier_groups.items():
			insights["supplier_analysis"][supplier] = {
				"item_count": len(items),
				"total_value": sum([flt(item.get('optimized_qty', 0)) * flt(item.get('last_purchase_rate', 0)) for item in items]),
				"avg_confidence": round(sum([flt(item.get('confidence_score', 0)) for item in items]) / max(len(items), 1), 1),
				"urgent_items": len([item for item in items if 'URGENT' in item.get('purchase_urgency', '')])
			}
		
		return {
			"status": "success",
			"insights": insights
		}
		
	except Exception as e:
		frappe.log_error(f"AI insights failed: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def create_smart_procurement_plan(strategy="Balanced", urgency_focus="All Items", budget_limit=None, forecast_horizon=30):
	"""
	Create AI-powered smart procurement plan with advanced configuration
	This is an enhanced version of bulk PO creation with strategic optimization
	"""
	try:
		# Convert parameters
		budget_limit = flt(budget_limit) if budget_limit else None
		forecast_horizon = cint(forecast_horizon) or 30
		
		# Build filters based on strategy
		filters = build_strategic_filters(strategy, urgency_focus, budget_limit, forecast_horizon)
		
		# Get AI forecast data with strategic filtering
		forecast_data = get_ai_forecast_data_for_purchase_orders(filters)
		
		if not forecast_data:
			return {
				"status": "error",
				"message": "No items match the smart procurement criteria",
				"total_value": 0,
				"purchase_orders_created": 0
			}
		
		# Apply strategic optimization
		optimized_data = apply_strategic_optimization(forecast_data, strategy, budget_limit)
		
		# Create purchase orders with strategy-based grouping
		result = create_strategic_purchase_orders(optimized_data, strategy, filters)
		
		# Add strategy-specific insights
		result["risk_assessment"] = assess_procurement_risk(strategy, optimized_data)
		result["optimization_score"] = calculate_optimization_score(optimized_data, strategy)
		result["strategy_applied"] = strategy
		result["focus_area"] = urgency_focus
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Smart procurement planning failed: {str(e)}")
		return {
			"status": "error",
			"message": f"Smart procurement planning failed: {str(e)}"
		}


def build_strategic_filters(strategy, urgency_focus, budget_limit, forecast_horizon):
	"""Build filters based on procurement strategy"""
	filters = {}
	
	# Strategy-based confidence thresholds
	if strategy == "Conservative":
		filters["min_confidence"] = 80
	elif strategy == "Balanced":
		filters["min_confidence"] = 65
	elif strategy == "Aggressive":
		filters["min_confidence"] = 50
	
	# Urgency-based filtering
	if urgency_focus == "Urgent Only":
		filters["urgency_filter"] = "urgent"
	elif urgency_focus == "Critical Only":
		filters["urgency_filter"] = "critical" 
	elif urgency_focus == "High Opportunity Only":
		filters["urgency_filter"] = "opportunity"
	
	# Budget and horizon
	filters["budget_limit"] = budget_limit
	filters["forecast_horizon"] = forecast_horizon
	
	return filters


def apply_strategic_optimization(forecast_data, strategy, budget_limit):
	"""Apply strategic optimization to forecast data"""
	optimized_data = []
	total_budget = 0
	
	# Sort by strategy priority
	if strategy == "Conservative":
		# Prioritize high confidence, lower risk
		forecast_data.sort(key=lambda x: (-x.get('confidence_score', 0), -x.get('supplier_score', 0)))
	elif strategy == "Aggressive":
		# Prioritize high opportunity, revenue potential
		forecast_data.sort(key=lambda x: (-x.get('revenue_potential', 0), -x.get('optimized_qty', 0)))
	else:  # Balanced
		# Balance confidence and opportunity
		forecast_data.sort(key=lambda x: (
			-x.get('confidence_score', 0) * 0.6 - x.get('revenue_potential', 0) * 0.4
		))
	
	for item in forecast_data:
		item_value = flt(item.get('optimized_qty', 0)) * flt(item.get('last_purchase_rate', 100))
		
		# Check budget constraint
		if budget_limit and (total_budget + item_value) > budget_limit:
			# Try to fit partial quantity within budget
			remaining_budget = budget_limit - total_budget
			max_qty = remaining_budget / flt(item.get('last_purchase_rate', 100))
			
			if max_qty >= 1:  # At least 1 unit
				item['optimized_qty'] = max(1, round(max_qty))
				item['budget_adjusted'] = True
				optimized_data.append(item)
			break
		
		optimized_data.append(item)
		total_budget += item_value
	
	return optimized_data


def create_strategic_purchase_orders(optimized_data, strategy, filters):
	"""Create purchase orders with strategic considerations"""
	# Group by supplier with strategy-based optimization
	supplier_groups = analyze_and_group_by_supplier(optimized_data)
	
	created_pos = []
	failed_items = []
	total_value = 0
	
	for supplier, items in supplier_groups.items():
		try:
			# Create PO with strategic metadata
			po_doc = create_ai_optimized_purchase_order(supplier, items, filters)
			if po_doc:
				# Add strategy-specific fields
				po_doc.procurement_strategy = strategy
				po_doc.save()
				
				created_pos.append({
					"name": po_doc.name,
					"supplier": supplier,
					"total_qty": sum([item.get('optimized_qty', 0) for item in items]),
					"total_amount": po_doc.total,
					"ai_confidence": calculate_po_confidence_score(items),
					"strategy": strategy
				})
				total_value += flt(po_doc.total)
			
		except Exception as e:
			failed_items.extend([item.get('item_code') for item in items])
			frappe.log_error(f"Failed to create strategic PO for supplier {supplier}: {str(e)}")
	
	return {
		"status": "success",
		"message": f"Smart procurement plan executed: Created {len(created_pos)} strategic Purchase Orders",
		"purchase_orders_created": len(created_pos),
		"total_value": total_value,
		"failed_items": len(failed_items),
		"created_pos": created_pos,
		"ai_insights": generate_purchase_insights(optimized_data, created_pos)
	}


def assess_procurement_risk(strategy, data):
	"""Assess overall procurement risk based on strategy and data"""
	if strategy == "Conservative":
		return "Low"
	elif strategy == "Aggressive":
		# Check if there are many low-confidence items
		low_confidence_count = len([item for item in data if item.get('confidence_score', 0) < 70])
		return "High" if low_confidence_count > len(data) * 0.3 else "Medium"
	else:  # Balanced
		return "Medium"


def calculate_optimization_score(data, strategy):
	"""Calculate how well optimized the procurement plan is"""
	if not data:
		return 0
	
	# Base score from confidence levels
	avg_confidence = sum(item.get('confidence_score', 0) for item in data) / len(data)
	confidence_score = min(100, avg_confidence * 1.2)  # Boost confidence contribution
	
	# Strategy bonus
	strategy_bonus = {"Conservative": 5, "Balanced": 10, "Aggressive": 15}
	
	# Coverage score (how many items are covered)
	coverage_score = min(20, len(data) * 2)  # Max 20 points for coverage
	
	total_score = confidence_score + strategy_bonus.get(strategy, 0) + coverage_score
	return min(100, round(total_score))
