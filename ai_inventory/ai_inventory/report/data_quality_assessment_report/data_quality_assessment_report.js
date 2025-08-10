// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Data Quality Assessment Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 0
		},
		{
			"fieldname": "assessment_days",
			"label": __("Assessment Period (Days)"),
			"fieldtype": "Select",
			"options": [
				{"label": __("Last 30 Days"), "value": 30},
				{"label": __("Last 60 Days"), "value": 60},
				{"label": __("Last 90 Days"), "value": 90},
				{"label": __("Last 180 Days"), "value": 180},
				{"label": __("Last 365 Days"), "value": 365}
			],
			"default": 90,
			"reqd": 1
		},
		{
			"fieldname": "quality_threshold",
			"label": __("Quality Threshold (%)"),
			"fieldtype": "Int",
			"default": 80,
			"description": __("Minimum quality score to be considered 'Good'")
		}
	],
	
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "score") {
			// Color code scores
			const score = parseFloat(data.score);
			if (score >= 90) {
				value = `<span style="color: #27ae60; font-weight: bold;">${value}</span>`;
			} else if (score >= 80) {
				value = `<span style="color: #f39c12; font-weight: bold;">${value}</span>`;
			} else if (score >= 60) {
				value = `<span style="color: #e67e22; font-weight: bold;">${value}</span>`;
			} else {
				value = `<span style="color: #e74c3c; font-weight: bold;">${value}</span>`;
			}
		}

		if (column.fieldname == "grade") {
			// Color code grades
			const grade = data.grade;
			if (grade === "A") {
				value = `<span style="color: #27ae60; font-weight: bold; background: #d5f4e6; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else if (grade === "B") {
				value = `<span style="color: #f39c12; font-weight: bold; background: #fef9e7; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else if (grade === "C") {
				value = `<span style="color: #e67e22; font-weight: bold; background: #fdf2e9; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			} else {
				value = `<span style="color: #e74c3c; font-weight: bold; background: #fdedec; padding: 2px 6px; border-radius: 3px;">${value}</span>`;
			}
		}

		if (column.fieldname == "status") {
			// Color code status
			if (data.status === "Good") {
				value = `<span style="color: #27ae60;">✓ ${value}</span>`;
			} else {
				value = `<span style="color: #e74c3c;">⚠ ${value}</span>`;
			}
		}

		if (column.fieldname == "metric") {
			// Add icons for different metrics
			if (data.metric.includes("Overall")) {
				value = `<span style="font-weight: bold;">🎯 ${value}</span>`;
			} else if (data.metric.includes("Completeness")) {
				value = `📋 ${value}`;
			} else if (data.metric.includes("Accuracy")) {
				value = `🎯 ${value}`;
			} else if (data.metric.includes("Consistency")) {
				value = `⚖️ ${value}`;
			} else if (data.metric.includes("Timeliness")) {
				value = `⏰ ${value}`;
			}
		}

		return value;
	},

	"onload": function(report) {
		// Add refresh button
		report.page.add_inner_button(__("Refresh Data"), function() {
			report.refresh();
		});

		// Add export quality report button
		report.page.add_inner_button(__("Export Quality Report"), function() {
			const filters = report.get_values();
			frappe.msgprint({
				title: __("Export Quality Report"),
				message: __("Quality assessment data for {0} days will be exported.", [filters.assessment_days || 90]),
				indicator: "blue"
			});
		});

		// Show quality insights
		report.page.add_inner_button(__("Quality Insights"), function() {
			show_quality_insights(report);
		});
	}
};

function show_quality_insights(report) {
	const data = report.data;
	if (!data || data.length === 0) {
		frappe.msgprint(__("No data available to show insights."));
		return;
	}

	let insights_html = `
		<div style="padding: 15px;">
			<h4>📊 Data Quality Insights</h4>
			<div style="margin-top: 10px;">
	`;

	// Generate insights based on the data
	data.forEach(row => {
		const score = parseFloat(row.score);
		let insight_color = "#27ae60";
		let insight_icon = "✅";
		
		if (score < 60) {
			insight_color = "#e74c3c";
			insight_icon = "⚠️";
		} else if (score < 80) {
			insight_color = "#f39c12";
			insight_icon = "⚡";
		}

		insights_html += `
			<div style="margin-bottom: 10px; padding: 8px; border-left: 3px solid ${insight_color}; background: #f8f9fa;">
				<strong>${insight_icon} ${row.metric}</strong><br>
				<span style="color: ${insight_color};">Score: ${score}% (${row.grade})</span><br>
				<small style="color: #6c757d;">${row.details}</small>
			</div>
		`;
	});

	insights_html += `
			</div>
			<div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 5px;">
				<strong>💡 Recommendations:</strong><br>
				<small>
					• Focus on metrics with scores below 80%<br>
					• Implement data validation rules for consistency<br>
					• Set up automated data quality monitoring<br>
					• Review data entry processes for accuracy
				</small>
			</div>
		</div>
	`;

	frappe.msgprint({
		title: __("Data Quality Insights"),
		message: insights_html,
		wide: true
	});
}
