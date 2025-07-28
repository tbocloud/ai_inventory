// ai_inventory/ai_inventory/report/forecast_accuracy_analysis/forecast_accuracy_analysis.js
// DEBUG-FIXED VERSION - Addresses JavaScript errors

frappe.query_reports["Forecast Accuracy Analysis"] = {
	"filters": [
		// Date Range Filters
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -30),
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "100px"
		},
		
		// Analysis Period
		{
			"fieldname": "analysis_period",
			"label": __("Analysis Period (Days)"),
			"fieldtype": "Select",
			"options": "7\n15\n30\n45\n60\n90",
			"default": "30",
			"reqd": 1,
			"width": "120px"
		},
		
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
				try {
					var company = frappe.query_report.get_filter_value('company');
					return {
						"doctype": "Warehouse",
						"filters": company ? {"company": company, "disabled": 0} : {"disabled": 0}
					};
				} catch (e) {
					console.log("Warehouse filter error:", e);
					return {"doctype": "Warehouse", "filters": {"disabled": 0}};
				}
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
			"fieldtype": "Select",
			"options": "\nCritical\nFast Moving\nSlow Moving\nNon Moving",
			"reqd": 0,
			"width": "150px"
		},
		
		// Accuracy Threshold Filter
		{
			"fieldname": "accuracy_threshold",
			"label": __("Accuracy Threshold %"),
			"fieldtype": "Float",
			"default": 80.0,
			"reqd": 0,
			"width": "130px"
		},
		
		// Confidence Filter
		{
			"fieldname": "min_confidence",
			"label": __("Min AI Confidence %"),
			"fieldtype": "Float",
			"reqd": 0,
			"default": 0,
			"width": "130px"
		},
		
		// Accuracy Category Filter
		{
			"fieldname": "accuracy_category",
			"label": __("Accuracy Category"),
			"fieldtype": "Select",
			"options": "\nExcellent (≥90%)\nGood (80-89%)\nFair (70-79%)\nAverage (60-69%)\nPoor (<60%)",
			"reqd": 0,
			"width": "140px"
		},
		
		// Quality Filters
		{
			"fieldname": "poor_accuracy_only",
			"label": __("Poor Accuracy Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "130px"
		},
		{
			"fieldname": "overconfident_only",
			"label": __("Overconfident Only"),
			"fieldtype": "Check",
			"default": 0,
			"width": "130px"
		}
	],
	
	// Enhanced formatter for accuracy visualization
	"formatter": function(value, row, column, data, default_formatter) {
		try {
			value = default_formatter(value, row, column, data);
			
			// Format accuracy percentage with color coding
			if (column.fieldname == "accuracy_percentage") {
				let color = "#28a745"; // Green for high accuracy
				let bgColor = "#e8f5e8";
				
				let numValue = parseFloat(value) || 0;
				if (numValue < 60) {
					color = "#dc3545"; // Red for poor accuracy
					bgColor = "#ffe6e6";
				} else if (numValue < 80) {
					color = "#ffc107"; // Yellow for fair accuracy
					bgColor = "#fff8e1";
				}
				
				value = `<span style="color: ${color}; font-weight: bold; background: ${bgColor}; padding: 2px 6px; border-radius: 3px;">${value}%</span>`;
			}
			
			// Format error percentage with inverse color coding
			if (column.fieldname == "error_percentage") {
				let color = "#28a745"; // Green for low error
				let bgColor = "#e8f5e8";
				
				let numValue = parseFloat(value) || 0;
				if (numValue > 50) {
					color = "#dc3545"; // Red for high error
					bgColor = "#ffe6e6";
				} else if (numValue > 25) {
					color = "#ffc107"; // Yellow for medium error
					bgColor = "#fff8e1";
				}
				
				value = `<span style="color: ${color}; font-weight: bold; background: ${bgColor}; padding: 2px 6px; border-radius: 3px;">${value}%</span>`;
			}
			
			// Format confidence vs accuracy gap
			if (column.fieldname == "confidence_accuracy_gap") {
				let color = "#28a745"; // Green for well calibrated
				let bgColor = "#e8f5e8";
				let icon = "⚖️";
				
				let gap = parseFloat(value) || 0;
				if (Math.abs(gap) <= 10) {
					color = "#28a745";
					bgColor = "#e8f5e8";
					icon = "⚖️"; // Well calibrated
				} else if (gap > 20) {
					color = "#dc3545";
					bgColor = "#ffe6e6";
					icon = "📉"; // Overconfident
				} else if (gap < -20) {
					color = "#17a2b8";
					bgColor = "#e6f3ff";
					icon = "📈"; // Underconfident
				} else {
					color = "#ffc107";
					bgColor = "#fff8e1";
					icon = "⚠️"; // Slightly off
				}
				
				value = `<span style="color: ${color}; font-weight: bold; background: ${bgColor}; padding: 2px 6px; border-radius: 3px;">${icon} ${value}%</span>`;
			}
			
			// Format bias direction with icons
			if (column.fieldname == "bias_direction") {
				if (value === "Over-forecast") {
					value = `<span style="color: #fd7e14; font-weight: bold;">📈 ${value}</span>`;
				} else if (value === "Under-forecast") {
					value = `<span style="color: #20c997; font-weight: bold;">📉 ${value}</span>`;
				} else if (value === "Perfect") {
					value = `<span style="color: #28a745; font-weight: bold;">🎯 ${value}</span>`;
				}
			}
			
			// Format error category
			if (column.fieldname == "error_category") {
				let color = "#28a745";
				if (value && (value.includes("Poor") || value.includes("Very Poor"))) {
					color = "#dc3545";
				} else if (value && value.includes("Fair")) {
					color = "#ffc107";
				}
				value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
			}
			
			// Format days since forecast with freshness indicators
			if (column.fieldname == "days_since_forecast") {
				let color = "#28a745";
				let icon = "🟢";
				
				let days = parseInt(value) || 0;
				if (days <= 7) {
					color = "#28a745";
					icon = "🟢"; // Fresh
				} else if (days <= 30) {
					color = "#ffc107";
					icon = "🟡"; // Recent
				} else {
					color = "#dc3545";
					icon = "🔴"; // Stale
				}
				
				value = `<span style="color: ${color}; font-weight: bold;">${icon} ${value}</span>`;
			}
			
			return value;
		} catch (e) {
			console.log("Formatter error:", e);
			return value;
		}
	},
	
	// Custom onload function with error handling
	"onload": function(report) {
		try {
			// Add action buttons with error handling
			if (report && report.page) {
				report.page.add_inner_button(__("Accuracy Analytics"), function() {
					show_accuracy_analytics_dialog(report);
				});
				
				report.page.add_inner_button(__("Improvement Recommendations"), function() {
					get_improvement_recommendations(report);
				});
				
				report.page.add_inner_button(__("Export Report"), function() {
					frappe.query_report.export_report();
				});
			}
			
			// Setup filter dependencies with error handling
			setup_filter_dependencies_safe(report);
			
		} catch (e) {
			console.log("Onload error:", e);
		}
	}
};

function setup_filter_dependencies_safe(report) {
	try {
		// Safe filter dependency setup
		setTimeout(function() {
			try {
				// Company filter change handler
				var company_filter = frappe.query_report.get_filter('company');
				if (company_filter) {
					company_filter.on('change', function() {
						try {
							var company = this.get_value();
							var warehouse_filter = frappe.query_report.get_filter('warehouse');
							
							if (warehouse_filter && company) {
								warehouse_filter.df.get_query = function() {
									return {
										"doctype": "Warehouse",
										"filters": {"company": company, "disabled": 0}
									};
								};
								warehouse_filter.set_value('');
							}
							
							// Auto-refresh after delay
							setTimeout(() => {
								if (frappe.query_report && frappe.query_report.refresh) {
									frappe.query_report.refresh();
								}
							}, 500);
						} catch (e) {
							console.log("Company filter change error:", e);
						}
					});
				}
				
				// Date filter change handlers
				['from_date', 'to_date', 'analysis_period'].forEach(function(filter_name) {
					try {
						var filter = frappe.query_report.get_filter(filter_name);
						if (filter) {
							filter.on('change', function() {
								setTimeout(() => {
									if (frappe.query_report && frappe.query_report.refresh) {
										frappe.query_report.refresh();
									}
								}, 500);
							});
						}
					} catch (e) {
						console.log(`Filter ${filter_name} setup error:`, e);
					}
				});
				
				// Quick filter logic with error handling
				var poor_accuracy_filter = frappe.query_report.get_filter('poor_accuracy_only');
				if (poor_accuracy_filter) {
					poor_accuracy_filter.on('change', function() {
						try {
							if (this.get_value()) {
								var accuracy_filter = frappe.query_report.get_filter('accuracy_category');
								if (accuracy_filter) {
									accuracy_filter.set_value('Poor (<60%)');
								}
							}
						} catch (e) {
							console.log("Poor accuracy filter error:", e);
						}
					});
				}
				
			} catch (e) {
				console.log("Filter setup error:", e);
			}
		}, 1000);
		
	} catch (e) {
		console.log("Setup dependencies error:", e);
	}
}

function show_accuracy_analytics_dialog(report) {
	try {
		var d = new frappe.ui.Dialog({
			title: __('Advanced Accuracy Analytics'),
			fields: [{
				fieldtype: 'HTML',
				fieldname: 'analytics_html'
			}],
			size: 'large'
		});
		
		if (report && report.data && report.data.length > 0) {
			var analytics = calculate_basic_analytics(report.data);
			
			var html = `
				<div class="accuracy-analytics">
					<h4>🎯 Accuracy Analysis Summary</h4>
					
					<div class="row">
						<div class="col-md-6">
							<h5>📊 Overall Performance</h5>
							<table class="table table-condensed">
								<tr><td><strong>Total Forecasts:</strong></td><td>${analytics.total_forecasts}</td></tr>
								<tr><td><strong>Average Accuracy:</strong></td><td><span class="text-success">${analytics.avg_accuracy.toFixed(1)}%</span></td></tr>
								<tr><td><strong>Average Error:</strong></td><td><span class="text-warning">${analytics.avg_error.toFixed(1)}%</span></td></tr>
							</table>
						</div>
						<div class="col-md-6">
							<h5>🎪 Distribution</h5>
							<table class="table table-condensed">
								<tr><td><strong>🌟 Excellent (≥90%):</strong></td><td><span class="text-success">${analytics.excellent_count}</span></td></tr>
								<tr><td><strong>✅ Good (80-89%):</strong></td><td><span class="text-success">${analytics.good_count}</span></td></tr>
								<tr><td><strong>💥 Poor (<60%):</strong></td><td><span class="text-danger">${analytics.poor_count}</span></td></tr>
							</table>
						</div>
					</div>
					
					<div class="alert alert-info">
						<h5>💡 Key Insights</h5>
						<ul>
							${analytics.insights.map(insight => `<li>${insight}</li>`).join('')}
						</ul>
					</div>
				</div>
			`;
			
			d.fields_dict.analytics_html.$wrapper.html(html);
		} else {
			d.fields_dict.analytics_html.$wrapper.html('<div class="text-muted">No data available for analysis</div>');
		}
		
		d.show();
		
	} catch (e) {
		console.log("Analytics dialog error:", e);
		frappe.msgprint(__("Unable to load analytics. Please check console for details."));
	}
}

function calculate_basic_analytics(data) {
	try {
		var analytics = {
			total_forecasts: data.length,
			avg_accuracy: 0,
			avg_error: 0,
			excellent_count: 0,
			good_count: 0,
			poor_count: 0,
			insights: []
		};
		
		var accuracies = [];
		var errors = [];
		
		data.forEach(function(item) {
			var accuracy = parseFloat(item.accuracy_percentage) || 0;
			var error = parseFloat(item.error_percentage) || 0;
			
			accuracies.push(accuracy);
			errors.push(error);
			
			if (accuracy >= 90) analytics.excellent_count++;
			else if (accuracy >= 80) analytics.good_count++;
			else if (accuracy < 60) analytics.poor_count++;
		});
		
		if (accuracies.length > 0) {
			analytics.avg_accuracy = accuracies.reduce((a, b) => a + b, 0) / accuracies.length;
			analytics.avg_error = errors.reduce((a, b) => a + b, 0) / errors.length;
		}
		
		// Generate insights
		if (analytics.avg_accuracy >= 85) {
			analytics.insights.push('🎉 Overall forecast accuracy is excellent');
		} else if (analytics.avg_accuracy < 65) {
			analytics.insights.push('🚨 Overall forecast accuracy needs improvement');
		}
		
		if (analytics.poor_count > analytics.total_forecasts * 0.3) {
			analytics.insights.push('⚠️ High number of poor-performing forecasts detected');
		}
		
		if (analytics.excellent_count > analytics.total_forecasts * 0.5) {
			analytics.insights.push('🌟 Majority of forecasts are performing excellently');
		}
		
		return analytics;
		
	} catch (e) {
		console.log("Analytics calculation error:", e);
		return {
			total_forecasts: 0,
			avg_accuracy: 0,
			avg_error: 0,
			excellent_count: 0,
			good_count: 0,
			poor_count: 0,
			insights: ['Error calculating analytics']
		};
	}
}

function get_improvement_recommendations(report) {
	try {
		var company = null;
		try {
			company = frappe.query_report.get_filter_value('company');
		} catch (e) {
			console.log("Could not get company filter:", e);
		}
		
		frappe.call({
			method: "ai_inventory.ai_inventory.report.forecast_accuracy_analysis.forecast_accuracy_analysis.generate_accuracy_improvement_recommendations",
			args: {
				company: company,
				min_accuracy: 80
			},
			callback: function(r) {
				try {
					if (r.message && r.message.status === "success") {
						show_improvement_recommendations_dialog(r.message);
					} else {
						frappe.msgprint(__("No recommendations available or failed to generate recommendations"));
					}
				} catch (e) {
					console.log("Recommendations callback error:", e);
					frappe.msgprint(__("Error processing recommendations"));
				}
			},
			error: function(r) {
				console.log("Recommendations API error:", r);
				frappe.msgprint(__("Failed to get recommendations from server"));
			}
		});
		
	} catch (e) {
		console.log("Get recommendations error:", e);
		frappe.msgprint(__("Unable to load recommendations"));
	}
}

function show_improvement_recommendations_dialog(data) {
	try {
		var d = new frappe.ui.Dialog({
			title: __('Improvement Recommendations'),
			fields: [{
				fieldtype: 'HTML',
				fieldname: 'recommendations_html'
			}],
			size: 'large'
		});
		
		var html = `
			<div class="improvement-recommendations">
				<h4>🤖 AI-Generated Recommendations</h4>
				<p><strong>Analysis Based On:</strong> ${data.total_analyzed || 0} forecasts</p>
				<p><strong>Overall Accuracy:</strong> <span class="text-${data.overall_accuracy >= 80 ? 'success' : data.overall_accuracy >= 60 ? 'warning' : 'danger'}">${data.overall_accuracy || 0}%</span></p>
				
				<div class="recommendations-list">
					${(data.recommendations || []).map(rec => `
						<div class="alert alert-${rec.priority === 'High' ? 'danger' : rec.priority === 'Medium' ? 'warning' : 'info'}">
							<h5>
								<span class="badge badge-${rec.priority === 'High' ? 'danger' : rec.priority === 'Medium' ? 'warning' : 'info'}">
									${rec.priority} Priority
								</span>
								${rec.category}
							</h5>
							<p><strong>Issue:</strong> ${rec.recommendation}</p>
							<p><strong>Affected Items:</strong> ${rec.affected_items}</p>
							<p><strong>Action:</strong> ${rec.action}</p>
						</div>
					`).join('')}
				</div>
				
				${(data.recommendations || []).length === 0 ? 
					'<div class="alert alert-success"><h5>🎉 No Critical Issues Found</h5><p>Your forecasting system is performing well!</p></div>' 
					: ''
				}
			</div>
		`;
		
		d.fields_dict.recommendations_html.$wrapper.html(html);
		d.show();
		
	} catch (e) {
		console.log("Recommendations dialog error:", e);
		frappe.msgprint(__("Error displaying recommendations"));
	}
}