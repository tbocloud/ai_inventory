// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

// ai_inventory/ai_inventory/report/stock_movement_prediction/stock_movement_prediction.js
// Enhanced JavaScript filters for Stock Movement Prediction

frappe.query_reports["Stock Movement Prediction"] = {
	"filters": [
		// Company Filter
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 0,
			"default": frappe.defaults.get_user_default("Company"),
			"width": "120px"
		},
		
		// Warehouse Filter
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"reqd": 0,
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {
					"doctype": "Warehouse",
					"filters": company ? {"company": company, "disabled": 0} : {"disabled": 0}
				};
			},
			"width": "120px"
		},
		
		// Supplier Filter
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
			"reqd": 0,
			"get_query": function() {
				return {
					"doctype": "Supplier",
					"filters": {"disabled": 0}
				};
			},
			"width": "120px"
		},
		
		// Item Group Filter
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			"reqd": 0,
			"width": "120px"
		},
		
		// Movement Type Filter
		{
			"fieldname": "movement_type",
			"label": __("Movement Type"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return [
					{value: "Critical", description: "Items requiring immediate attention"},
					{value: "Fast Moving", description: "High velocity items"},
					{value: "Slow Moving", description: "Low velocity items"},
					{value: "Non Moving", description: "No recent movement"}
				];
			},
			"reqd": 0,
			"width": "150px"
		},
		
		// Prediction Horizon
		{
			"fieldname": "prediction_horizon",
			"label": __("Prediction Horizon (Days)"),
			"fieldtype": "Select",
			"options": "7\n15\n30\n60\n90",
			"default": "30",
			"reqd": 0,
			"width": "120px"
		},
		
		// Risk Level Filter
		{
			"fieldname": "risk_level_filter",
			"label": __("Risk Level"),
			"fieldtype": "Select",
			"options": "\nCritical\nHigh\nMedium\nLow\nMinimal",
			"reqd": 0,
			"width": "100px"
		},
		
		// Confidence Filter
		{
			"fieldname": "min_confidence",
			"label": __("Min Confidence %"),
			"fieldtype": "Float",
			"reqd": 0,
			"default": 0,
			"width": "120px"
		},
		
		// ABC Class Filter
		{
			"fieldname": "abc_class_filter",
			"label": __("ABC Class"),
			"fieldtype": "Select",
			"options": "\nA\nB\nC",
			"reqd": 0,
			"width": "80px"
		},
		
		// Stockout Probability Filter
		{
			"fieldname": "min_stockout_probability",
			"label": __("Min Stockout Probability %"),
			"fieldtype": "Float",
			"reqd": 0,
			"width": "150px"
		},
		
		// Days to Stockout Filter
		{
			"fieldname": "max_days_to_stockout",
			"label": __("Max Days to Stockout"),
			"fieldtype": "Int",
			"reqd": 0,
			"width": "140px"
		},
		
		// Quick Filters
		{
			"fieldname": "critical_only",
			"label": __("Critical Items Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "120px"
		},
		{
			"fieldname": "high_velocity_only",
			"label": __("High Velocity Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "120px"
		},
		{
			"fieldname": "low_stock_only",
			"label": __("Low Stock Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "100px"
		}
	],
	
	// Enhanced formatter for better visualization
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Format risk level with colors and icons
		if (column.fieldname == "risk_level") {
			if (value && value.includes("🚨 Critical")) {
				value = `<span style="color: #dc3545; font-weight: bold; background: #ffe6e6; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else if (value && value.includes("🔴 High")) {
				value = `<span style="color: #fd7e14; font-weight: bold; background: #fff3e0; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else if (value && value.includes("🟡 Medium")) {
				value = `<span style="color: #ffc107; font-weight: bold; background: #fff8e1; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else if (value && value.includes("🟢 Low")) {
				value = `<span style="color: #28a745; font-weight: bold; background: #e8f5e8; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else if (value && value.includes("✅ Minimal")) {
				value = `<span style="color: #17a2b8; font-weight: bold; background: #e6f3ff; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			}
		}
		
		// Format stockout probability with colors
		if (column.fieldname == "stockout_probability") {
			let color = "#28a745"; // Green for low probability
			let bgColor = "#e8f5e8";
			
			if (parseFloat(value) > 70) {
				color = "#dc3545"; // Red for high probability
				bgColor = "#ffe6e6";
			} else if (parseFloat(value) > 40) {
				color = "#ffc107"; // Yellow for medium probability
				bgColor = "#fff8e1";
			}
			
			value = `<span style="color: ${color}; font-weight: bold; background: ${bgColor}; padding: 2px 6px; border-radius: 3px;">${value}%</span>`;
		}
		
		// Format days to stockout with urgency colors
		if (column.fieldname == "days_to_stockout") {
			let color = "#28a745"; // Green
			let bgColor = "#e8f5e8";
			
			if (parseInt(value) <= 3) {
				color = "#dc3545"; // Red for critical
				bgColor = "#ffe6e6";
			} else if (parseInt(value) <= 7) {
				color = "#fd7e14"; // Orange for urgent
				bgColor = "#fff3e0";
			} else if (parseInt(value) <= 15) {
				color = "#ffc107"; // Yellow for attention
				bgColor = "#fff8e1";
			}
			
			if (parseInt(value) === 999) {
				value = `<span style="color: #6c757d;">∞</span>`;
			} else {
				value = `<span style="color: ${color}; font-weight: bold; background: ${bgColor}; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			}
		}
		
		// Format prediction confidence
		if (column.fieldname == "prediction_confidence") {
			let color = "#28a745"; // Green for high confidence
			if (parseFloat(value) < 70) {
				color = "#dc3545"; // Red for low confidence
			} else if (parseFloat(value) < 85) {
				color = "#ffc107"; // Yellow for medium confidence
			}
			
			value = `<span style="color: ${color}; font-weight: bold;">${value}%</span>`;
		}
		
		// Format ABC class with colors
		if (column.fieldname == "abc_class") {
			let color = "#28a745"; // Green for A
			if (value === 'B') {
				color = "#ffc107"; // Yellow for B
			} else if (value === 'C') {
				color = "#6c757d"; // Gray for C
			}
			
			value = `<span style="color: ${color}; font-weight: bold; font-size: 14px;">${value}</span>`;
		}
		
		// Format velocity with trend indicators
		if (column.fieldname == "daily_velocity") {
			const acceleration = data.demand_acceleration || 0;
			let trend = "";
			
			if (acceleration > 0.1) {
				trend = " 📈";
			} else if (acceleration < -0.1) {
				trend = " 📉";
			} else {
				trend = " ➡️";
			}
			
			value = `<span>${value}${trend}</span>`;
		}
		
		// Format current stock with safety indicators
		if (column.fieldname == "current_stock") {
			const safety_stock = data.safety_stock_needed || 0;
			let indicator = "";
			
			if (parseFloat(value) < safety_stock) {
				indicator = " ⚠️";
				value = `<span style="color: #dc3545; font-weight: bold;">${value}${indicator}</span>`;
			} else if (parseFloat(value) < safety_stock * 1.5) {
				indicator = " ⚡";
				value = `<span style="color: #ffc107; font-weight: bold;">${value}${indicator}</span>`;
			} else {
				value = `<span style="color: #28a745;">${value}</span>`;
			}
		}
		
		// Format seasonality index
		if (column.fieldname == "seasonality_index") {
			if (parseFloat(value) > 1.2) {
				value = `<span style="color: #28a745; font-weight: bold;">📈 ${value}</span>`;
			} else if (parseFloat(value) < 0.8) {
				value = `<span style="color: #dc3545; font-weight: bold;">📉 ${value}</span>`;
			} else {
				value = `<span style="color: #6c757d;">➡️ ${value}</span>`;
			}
		}
		
		return value;
	},
	
	// Custom onload function for additional features
	"onload": function(report) {
		// Add action buttons
		report.page.add_inner_button(__("Run Emergency Forecast"), function() {
			let selected_items = [];
			
			// Get selected rows
			if (report.data && report.data.length > 0) {
				// For demo, take first 10 critical items
				selected_items = report.data
					.filter(item => item.risk_level && item.risk_level.includes('Critical'))
					.slice(0, 10)
					.map(item => item.item_code);
			}
			
			if (selected_items.length === 0) {
				frappe.msgprint(__("No critical items found for emergency forecast"));
				return;
			}
			
			frappe.call({
				method: "ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now",
				args: {
					company: frappe.query_report.get_filter_value('company')
				},
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint({
							title: __("Emergency Forecast Complete"),
							message: `Updated forecasts for ${r.message.successful} items`,
							indicator: "green"
						});
						frappe.query_report.refresh();
					}
				}
			});
		});
		
		report.page.add_inner_button(__("Create Safety Stock POs"), function() {
			let high_risk_items = [];
			
			if (report.data && report.data.length > 0) {
				high_risk_items = report.data
					.filter(item => 
						(item.risk_level && (item.risk_level.includes('Critical') || item.risk_level.includes('High'))) &&
						item.safety_stock_needed > 0
					)
					.slice(0, 20);
			}
			
			if (high_risk_items.length === 0) {
				frappe.msgprint(__("No high-risk items requiring safety stock found"));
				return;
			}
			
			frappe.call({
				method: "ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.bulk_create_purchase_orders",
				args: {
					company: frappe.query_report.get_filter_value('company'),
					movement_types: ['Critical', 'Fast Moving'],
					only_reorder_alerts: true
				},
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.msgprint({
							title: __("Safety Stock POs Created"),
							message: `Created ${r.message.pos_created} purchase orders for safety stock`,
							indicator: "green"
						});
					}
				}
			});
		});
		
		report.page.add_inner_button(__("Export Prediction Data"), function() {
			frappe.query_report.export_report();
		});
		
		report.page.add_inner_button(__("Prediction Analytics"), function() {
			// Open a dialog with advanced analytics
			show_prediction_analytics_dialog(report);
		});
		
		// Add filter dependencies
		setup_filter_dependencies(report);
	}
};

function setup_filter_dependencies(report) {
	// Update warehouse options when company changes
	frappe.query_report.get_filter('company').on('change', function() {
		var company = this.get_value();
		var warehouse_filter = frappe.query_report.get_filter('warehouse');
		
		if (company) {
			warehouse_filter.df.get_query = function() {
				return {
					"doctype": "Warehouse",
					"filters": {"company": company, "disabled": 0}
				};
			};
		}
		
		warehouse_filter.set_value('');
		setTimeout(() => frappe.query_report.refresh(), 500);
	});
	
	// Quick filter logic
	frappe.query_report.get_filter('critical_only').on('change', function() {
		if (this.get_value()) {
			frappe.query_report.get_filter('risk_level_filter').set_value('Critical');
		}
	});
	
	frappe.query_report.get_filter('high_velocity_only').on('change', function() {
		if (this.get_value()) {
			frappe.query_report.get_filter('movement_type').set_value(['Fast Moving']);
		}
	});
	
	frappe.query_report.get_filter('low_stock_only').on('change', function() {
		if (this.get_value()) {
			frappe.query_report.get_filter('max_days_to_stockout').set_value(15);
		}
	});
}

function show_prediction_analytics_dialog(report) {
	let d = new frappe.ui.Dialog({
		title: __('Prediction Analytics'),
		fields: [{
			fieldtype: 'HTML',
			fieldname: 'analytics_html'
		}],
		size: 'large'
	});
	
	// Calculate analytics from current data
	if (report.data && report.data.length > 0) {
		let analytics = calculate_prediction_analytics(report.data);
		
		let html = `
			<div class="prediction-analytics">
				<h4>📊 Advanced Prediction Analytics</h4>
				
				<div class="row">
					<div class="col-md-6">
						<h5>🎯 Accuracy Metrics</h5>
						<p><strong>Average Prediction Confidence:</strong> ${analytics.avg_confidence.toFixed(1)}%</p>
						<p><strong>High Confidence Items (>80%):</strong> ${analytics.high_confidence_count}</p>
						<p><strong>Low Confidence Items (<60%):</strong> ${analytics.low_confidence_count}</p>
					</div>
					<div class="col-md-6">
						<h5>⚡ Velocity Analysis</h5>
						<p><strong>Average Daily Velocity:</strong> ${analytics.avg_velocity.toFixed(2)} units/day</p>
						<p><strong>Highest Velocity Item:</strong> ${analytics.max_velocity.toFixed(2)} units/day</p>
						<p><strong>Items with Acceleration:</strong> ${analytics.accelerating_items}</p>
					</div>
				</div>
				
				<div class="row">
					<div class="col-md-6">
						<h5>🚨 Risk Distribution</h5>
						<p><strong>Critical Risk:</strong> ${analytics.risk_distribution.critical}</p>
						<p><strong>High Risk:</strong> ${analytics.risk_distribution.high}</p>
						<p><strong>Medium Risk:</strong> ${analytics.risk_distribution.medium}</p>
						<p><strong>Low Risk:</strong> ${analytics.risk_distribution.low}</p>
					</div>
					<div class="col-md-6">
						<h5>📈 Stockout Analysis</h5>
						<p><strong>Items at High Stockout Risk (>70%):</strong> ${analytics.high_stockout_risk}</p>
						<p><strong>Average Days to Stockout:</strong> ${analytics.avg_days_to_stockout.toFixed(0)} days</p>
						<p><strong>Items Stocking Out This Week:</strong> ${analytics.stockout_this_week}</p>
					</div>
				</div>
				
				<div class="row">
					<div class="col-md-12">
						<h5>💰 ABC Analysis</h5>
						<p><strong>Class A Items:</strong> ${analytics.abc_distribution.A} (High Value)</p>
						<p><strong>Class B Items:</strong> ${analytics.abc_distribution.B} (Medium Value)</p>
						<p><strong>Class C Items:</strong> ${analytics.abc_distribution.C} (Low Value)</p>
					</div>
				</div>
				
				<div class="alert alert-info">
					<strong>💡 Key Recommendations:</strong>
					<ul>
						${analytics.recommendations.map(rec => `<li>${rec}</li>`).join('')}
					</ul>
				</div>
			</div>
		`;
		
		d.fields_dict.analytics_html.$wrapper.html(html);
	}
	
	d.show();
}

function calculate_prediction_analytics(data) {
	let analytics = {
		avg_confidence: 0,
		high_confidence_count: 0,
		low_confidence_count: 0,
		avg_velocity: 0,
		max_velocity: 0,
		accelerating_items: 0,
		risk_distribution: {critical: 0, high: 0, medium: 0, low: 0},
		high_stockout_risk: 0,
		avg_days_to_stockout: 0,
		stockout_this_week: 0,
		abc_distribution: {A: 0, B: 0, C: 0},
		recommendations: []
	};
	
	let confidences = [];
	let velocities = [];
	let valid_stockout_days = [];
	
	data.forEach(item => {
		// Confidence analysis
		let confidence = item.prediction_confidence || 0;
		confidences.push(confidence);
		if (confidence > 80) analytics.high_confidence_count++;
		if (confidence < 60) analytics.low_confidence_count++;
		
		// Velocity analysis
		let velocity = item.daily_velocity || 0;
		if (velocity > 0) velocities.push(velocity);
		
		// Acceleration
		if ((item.demand_acceleration || 0) > 0.1) {
			analytics.accelerating_items++;
		}
		
		// Risk distribution
		let risk = item.risk_level || '';
		if (risk.includes('Critical')) analytics.risk_distribution.critical++;
		else if (risk.includes('High')) analytics.risk_distribution.high++;
		else if (risk.includes('Medium')) analytics.risk_distribution.medium++;
		else if (risk.includes('Low')) analytics.risk_distribution.low++;
		
		// Stockout analysis
		if ((item.stockout_probability || 0) > 70) {
			analytics.high_stockout_risk++;
		}
		
		let days_to_stockout = item.days_to_stockout || 999;
		if (days_to_stockout < 999) {
			valid_stockout_days.push(days_to_stockout);
			if (days_to_stockout <= 7) {
				analytics.stockout_this_week++;
			}
		}
		
		// ABC distribution
		let abc_class = item.abc_class || 'C';
		analytics.abc_distribution[abc_class]++;
	});
	
	// Calculate averages
	analytics.avg_confidence = confidences.length > 0 ? 
		confidences.reduce((a, b) => a + b, 0) / confidences.length : 0;
	
	analytics.avg_velocity = velocities.length > 0 ? 
		velocities.reduce((a, b) => a + b, 0) / velocities.length : 0;
	
	analytics.max_velocity = velocities.length > 0 ? Math.max(...velocities) : 0;
	
	analytics.avg_days_to_stockout = valid_stockout_days.length > 0 ? 
		valid_stockout_days.reduce((a, b) => a + b, 0) / valid_stockout_days.length : 0;
	
	// Generate recommendations
	if (analytics.risk_distribution.critical > 0) {
		analytics.recommendations.push(`🚨 ${analytics.risk_distribution.critical} items need immediate attention`);
	}
	if (analytics.stockout_this_week > 0) {
		analytics.recommendations.push(`⏰ ${analytics.stockout_this_week} items may stock out this week`);
	}
	if (analytics.low_confidence_count > data.length * 0.3) {
		analytics.recommendations.push(`📈 Consider improving data quality - ${analytics.low_confidence_count} items have low confidence`);
	}
	if (analytics.accelerating_items > 0) {
		analytics.recommendations.push(`📈 ${analytics.accelerating_items} items showing demand acceleration - monitor closely`);
	}
	
	return analytics;
}