// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Manufacturing Dashboard Report"] = {
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
            "fieldname": "period_months",
            "label": __("Analysis Period (Months)"),
            "fieldtype": "Select",
            "options": "3\n6\n12\n18\n24",
            "default": "6",
            "reqd": 0
        },
        {
            "fieldname": "metric_type",
            "label": __("Metric Type"),
            "fieldtype": "Select",
            "options": "\nAll\nProduction\nCost\nKPI\nInventory\nCapacity",
            "default": "All",
            "reqd": 0
        }
    ],
    
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "status" && data && data.status) {
            if (data.status == "Excellent") {
                value = "<span style='color:green; font-weight:bold'>" + value + "</span>";
            } else if (data.status == "Good") {
                value = "<span style='color:green'>" + value + "</span>";
            } else if (data.status == "Attention") {
                value = "<span style='color:orange'>" + value + "</span>";
            } else if (data.status == "Critical") {
                value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
            }
        }
        
        if (column.fieldname == "trend" && data && data.trend) {
            if (data.trend == "Up") {
                value = "<span style='color:green'>↗ " + value + "</span>";
            } else if (data.trend == "Down") {
                value = "<span style='color:red'>↘ " + value + "</span>";
            } else {
                value = "<span style='color:gray'>→ " + value + "</span>";
            }
        }
        
        if (column.fieldname == "variance_percentage" && data && data.variance_percentage) {
            if (data.variance_percentage > 0) {
                value = "<span style='color:green'>+" + value + "</span>";
            } else if (data.variance_percentage < 0) {
                value = "<span style='color:red'>" + value + "</span>";
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons for detailed analysis
        report.page.add_menu_item(__("Detailed Dashboard"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.manufacturing_dashboard_report.manufacturing_dashboard_report.generate_manufacturing_dashboard_report',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 6
                },
                callback: function(r) {
                    if (r.message) {
                        show_dashboard_dialog(r.message);
                    }
                }
            });
        });
        
        report.page.add_menu_item(__("Export Dashboard"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.manufacturing_dashboard_report.manufacturing_dashboard_report.export_manufacturing_dashboard',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 6,
                    format: 'excel'
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__("Dashboard exported successfully"));
                    }
                }
            });
        });
    }
};

function show_dashboard_dialog(dashboard_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Manufacturing Dashboard Analysis'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'dashboard_html'
            }
        ]
    });
    
    let html = generate_dashboard_html(dashboard_data);
    dialog.fields_dict.dashboard_html.$wrapper.html(html);
    dialog.show();
}

function generate_dashboard_html(data) {
    let html = `
        <div class="manufacturing-dashboard">
            <h3>${data.report_title}</h3>
            <p><strong>Generated:</strong> ${data.generated_at}</p>
            <p><strong>Company:</strong> ${data.company}</p>
            <p><strong>Analysis Period:</strong> ${data.analysis_period}</p>
            
            <div class="row">
                <div class="col-md-6">
                    <h4>Summary</h4>
                    <table class="table table-bordered">
                        <tr><td>Total Production Forecast</td><td>${data.summary.total_production_forecast}</td></tr>
                        <tr><td>Total Cost Forecast</td><td>${data.summary.total_cost_forecast}</td></tr>
                        <tr><td>Inventory Turnover</td><td>${data.summary.inventory_turnover}</td></tr>
                        <tr><td>Capacity Utilization</td><td>${data.summary.capacity_utilization}%</td></tr>
                        <tr><td>Cost Efficiency</td><td>${data.summary.cost_efficiency}%</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h4>Key Insights</h4>
                    <ul>`;
    
    if (data.insights && data.insights.length > 0) {
        data.insights.forEach(insight => {
            html += `<li>${insight}</li>`;
        });
    }
    
    html += `
                    </ul>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <h4>Recommendations</h4>
                    <ul>`;
    
    if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
    }
    
    html += `
                    </ul>
                </div>
            </div>
        </div>
        
        <style>
        .manufacturing-dashboard {
            padding: 20px;
        }
        .manufacturing-dashboard h3 {
            color: #5e72e4;
            margin-bottom: 20px;
        }
        .manufacturing-dashboard h4 {
            color: #32325d;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .manufacturing-dashboard table {
            font-size: 14px;
        }
        </style>
    `;
    
    return html;
}
