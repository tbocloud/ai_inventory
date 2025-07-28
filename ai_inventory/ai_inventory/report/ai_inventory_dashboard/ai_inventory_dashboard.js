// ai_inventory/ai_inventory/report/ai_inventory_dashboard/ai_inventory_dashboard.js
// Enhanced JavaScript filters for AI Inventory Dashboard

frappe.query_reports["AI Inventory Dashboard"] = {
	"filters": [
		// Date Range Filters
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -90),
			"reqd": 0,
			"width": "100px"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 0,
			"width": "100px"
		},
		
		// Company and Location Filters
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 0,
			"default": frappe.defaults.get_user_default("Company"),
			"width": "120px"
		},
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
					"filters": company ? {"company": company} : {}
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
		
		// Item Classification
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group",
			"reqd": 0,
			"width": "120px"
		},
		
		// Movement Type Filter with Multi-Select
		{
			"fieldname": "movement_type",
			"label": __("Movement Type"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return [
					{value: "Fast Moving", description: "High velocity items"},
					{value: "Slow Moving", description: "Low velocity items"},
					{value: "Non Moving", description: "No recent movement"},
					{value: "Critical", description: "Critical shortage items"}
				];
			},
			"reqd": 0,
			"width": "150px"
		},
		
		// Quick Filter Checkboxes
		{
			"fieldname": "reorder_alert",
			"label": __("Reorder Alerts Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "80px"
		},
		{
			"fieldname": "low_confidence",
			"label": __("Low Confidence (<70%)"),
			"fieldtype": "Check",
			"default": 0,
			"width": "80px"
		},
		{
			"fieldname": "critical_items_only",
			"label": __("Critical Items Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "80px"
		},
		
		// Movement Specific Filters
		{
			"fieldname": "non_moving_only",
			"label": __("Non Moving Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "80px"
		},
		{
			"fieldname": "slow_moving_only",
			"label": __("Slow Moving Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "80px"
		},
		
		// Advanced Filters
		{
			"fieldname": "high_value_items",
			"label": __("High Value Items"),
			"fieldtype": "Check",
			"default": 0,
			"width": "80px"
		},
		
		// Stock Level Filters
		{
			"fieldname": "min_stock",
			"label": __("Min Stock Level"),
			"fieldtype": "Float",
			"reqd": 0,
			"width": "100px"
		},
		{
			"fieldname": "max_stock",
			"label": __("Max Stock Level"),
			"fieldtype": "Float",
			"reqd": 0,
			"width": "100px"
		},
		
		// Confidence and Risk Filters
		{
			"fieldname": "min_confidence",
			"label": __("Min Confidence %"),
			"fieldtype": "Float",
			"reqd": 0,
			"default": 0,
			"width": "100px"
		},
		{
			"fieldname": "max_risk_score",
			"label": __("Max Risk Score"),
			"fieldtype": "Float",
			"reqd": 0,
			"width": "100px"
		}
	],
	
	// Custom formatter for enhanced display
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Format movement type with colors and icons
		if (column.fieldname == "movement_type") {
			if (value == "Critical") {
				value = `<span style="color: #dc3545; font-weight: bold;">🚨 ${value}</span>`;
			} else if (value == "Fast Moving") {
				value = `<span style="color: #28a745; font-weight: bold;">🚀 ${value}</span>`;
			} else if (value == "Slow Moving") {
				value = `<span style="color: #ffc107; font-weight: bold;">🐌 ${value}</span>`;
			} else if (value == "Non Moving") {
				value = `<span style="color: #6c757d; font-weight: bold;">⏸️ ${value}</span>`;
			}
		}
		
		// Format reorder alerts
		if (column.fieldname == "reorder_alert" && value == 1) {
			value = `<span style="color: #dc3545; font-weight: bold;">🔔 ALERT</span>`;
		}
		
		// Format confidence score with colors
		if (column.fieldname == "confidence_score") {
			let color = "#28a745"; // Green for high confidence
			if (value < 70) color = "#dc3545"; // Red for low confidence
			else if (value < 85) color = "#ffc107"; // Yellow for medium confidence
			
			value = `<span style="color: ${color}; font-weight: bold;">${value}%</span>`;
		}
		
		// Format risk score
		if (column.fieldname == "risk_score") {
			let color = "#28a745"; // Green for low risk
			if (value > 70) color = "#dc3545"; // Red for high risk
			else if (value > 40) color = "#ffc107"; // Yellow for medium risk
			
			value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
		}
		
		// Format demand trend with icons
		if (column.fieldname == "demand_trend") {
			if (value && value.includes("Increasing")) {
				value = `<span style="color: #28a745;">📈 Increasing</span>`;
			} else if (value && value.includes("Decreasing")) {
				value = `<span style="color: #dc3545;">📉 Decreasing</span>`;
			} else if (value && value.includes("Stable")) {
				value = `<span style="color: #6c757d;">➡️ Stable</span>`;
			}
		}
		
		// Format stock days with urgency colors
		if (column.fieldname == "stock_days") {
			let color = "#28a745"; // Green
			if (value < 7) color = "#dc3545"; // Red for urgent
			else if (value < 30) color = "#ffc107"; // Yellow for attention
			
			value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
		}
		
		// Format current stock with reorder level context
		if (column.fieldname == "current_stock") {
			const reorder_level = data.reorder_level || 0;
			let color = "#000"; // Default black
			
			if (reorder_level > 0) {
				if (value <= reorder_level * 0.5) {
					color = "#dc3545"; // Red for critical
				} else if (value <= reorder_level) {
					color = "#ffc107"; // Yellow for low
				} else if (value <= reorder_level * 1.5) {
					color = "#28a745"; // Green for healthy
				}
			}
			
			value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
		}
		
		return value;
	},
	
	// Custom onload function for additional features
	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Sync All Forecasts"), function() {
			frappe.call({
				method: "ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now",
				args: {
					company: frappe.query_report.get_filter_value('company')
				},
				callback: function(r) {
					if (r.message) {
						frappe.msgprint({
							title: __("Sync Results"),
							message: r.message.message,
							indicator: r.message.status === "success" ? "green" : "red"
						});
						
						if (r.message.status === "success") {
							frappe.query_report.refresh();
						}
					}
				}
			});
		});
		
		report.page.add_inner_button(__("Create Bulk POs"), function() {
			frappe.call({
				method: "ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.bulk_create_purchase_orders",
				args: {
					company: frappe.query_report.get_filter_value('company'),
					movement_types: frappe.query_report.get_filter_value('movement_type'),
					only_reorder_alerts: true
				},
				callback: function(r) {
					if (r.message) {
						frappe.msgprint({
							title: __("Bulk PO Creation"),
							message: `${r.message.message}<br><br>
								<strong>POs Created:</strong> ${r.message.pos_created}<br>
								<strong>Items Processed:</strong> ${r.message.items_processed}`,
							indicator: r.message.status === "success" ? "green" : "red"
						});
						
						if (r.message.status === "success") {
							frappe.query_report.refresh();
						}
					}
				}
			});
		});
		
		report.page.add_inner_button(__("Export Analytics"), function() {
			frappe.query_report.export_report();
		});
		
		// Add filter dependency logic
		frappe.query_report.add_filter_dependency();
	},
	
	// Filter dependency management
	add_filter_dependency: function() {
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
		});
		
		// Auto-refresh when key filters change
		['company', 'warehouse', 'from_date', 'to_date'].forEach(function(filter_name) {
			frappe.query_report.get_filter(filter_name).on('change', function() {
				setTimeout(function() {
					frappe.query_report.refresh();
				}, 500);
			});
		});
		
		// Mutual exclusivity for movement type checkboxes
		frappe.query_report.get_filter('non_moving_only').on('change', function() {
			if (this.get_value()) {
				frappe.query_report.get_filter('slow_moving_only').set_value(0);
			}
		});
		
		frappe.query_report.get_filter('slow_moving_only').on('change', function() {
			if (this.get_value()) {
				frappe.query_report.get_filter('non_moving_only').set_value(0);
			}
		});
	},
	
	// Tree view for hierarchical data
	"tree": false,
	
	// Enable/disable features
	"disable_prepared_report": false,
	"is_std": "Yes"
};