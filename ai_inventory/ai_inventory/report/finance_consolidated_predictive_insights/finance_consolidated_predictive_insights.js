// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Finance Consolidated Predictive Insights"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_default("company"),
			"reqd": 0,
			"width": "200px",
			"on_change": () => frappe.query_report.refresh(),
		},
		{
			"fieldname": "forecast_horizon",
			"label": __("Forecast Horizon (months)"),
			"fieldtype": "Select",
			"options": ["1","3","6","9","12","18","24","36"].join("\n"),
			"default": "12",
			"reqd": 0,
			"description": __("Choose forecast horizon (months)"),
			"on_change": () => frappe.query_report.refresh(),
		},
		{
			"fieldname": "confidence_threshold",
			"label": __("Confidence Threshold (%)"),
			"fieldtype": "Select",
			"options": ["50","60","70","75","80","85","90","95"].join("\n"),
			"default": "75",
			"reqd": 0,
			"description": __("Hide insights below this confidence level"),
			"on_change": () => frappe.query_report.refresh(),
		},
	],
};
