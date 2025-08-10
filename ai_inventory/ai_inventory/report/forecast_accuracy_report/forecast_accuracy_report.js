// Copyright (c) 2024, tbocloud and contributors
// For license information, please see license.txt

frappe.query_reports["Forecast Accuracy Report"] = {
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
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        },
        {
            "fieldname": "model_type",
            "label": __("Model Type"),
            "fieldtype": "Select",
            "options": "\nAll\nARIMA\nProphet\nLinear Regression\nRandom Forest\nEnsemble",
            "default": "All",
            "reqd": 0
        }
    ],
    
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "accuracy_percentage" && data && data.accuracy_percentage) {
            if (data.accuracy_percentage >= 90) {
                value = "<span style='color:green'>" + value + "</span>";
            } else if (data.accuracy_percentage >= 70) {
                value = "<span style='color:orange'>" + value + "</span>";
            } else {
                value = "<span style='color:red'>" + value + "</span>";
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons
        report.page.add_menu_item(__("Export to Excel"), function() {
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.forecast_accuracy_report.forecast_accuracy_report.export_accuracy_report',
                args: {
                    company: frappe.query_report.get_filter_value('company'),
                    period_days: 90,
                    format: 'excel'
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__("Export completed successfully"));
                    }
                }
            });
        });
        
        report.page.add_menu_item(__("View Detailed Analysis"), function() {
            // Open detailed analysis in a dialog
            show_detailed_analysis(report);
        });
    }
};

function show_detailed_analysis(report) {
    let filters = report.get_values();
    
    frappe.call({
        method: 'ai_inventory.ai_inventory.report.forecast_accuracy_report.forecast_accuracy_report.generate_forecast_accuracy_report',
        args: {
            company: filters.company,
            period_days: 90,
            model_type: filters.model_type || 'all'
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                let data = r.message.data;
                
                let dialog = new frappe.ui.Dialog({
                    title: __('Detailed Forecast Accuracy Analysis'),
                    size: 'extra-large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'analysis_html'
                        }
                    ]
                });
                
                let html = generate_analysis_html(data);
                dialog.fields_dict.analysis_html.$wrapper.html(html);
                dialog.show();
            }
        }
    });
}

function generate_analysis_html(data) {
    let html = `
        <div class="forecast-analysis">
            <h3>${data.report_title}</h3>
            <p><strong>Generated:</strong> ${data.generated_at}</p>
            <p><strong>Company:</strong> ${data.company || 'All Companies'}</p>
            <p><strong>Analysis Period:</strong> ${data.analysis_period}</p>
            
            <div class="row">
                <div class="col-md-6">
                    <h4>Summary</h4>
                    <div class="alert alert-info">
                        ${data.summary}
                    </div>
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
        .forecast-analysis {
            padding: 20px;
        }
        .forecast-analysis h3 {
            color: #5e72e4;
            margin-bottom: 20px;
        }
        .forecast-analysis h4 {
            color: #32325d;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        </style>
    `;
    
    return html;
}
