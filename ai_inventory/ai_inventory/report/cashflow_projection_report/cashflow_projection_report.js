// ERPNext Cash Flow Projection Report
frappe.query_reports["Cashflow Projection Report"] = {
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
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), 12),
            "reqd": 0
        },
        {
            "fieldname": "months_ahead",
            "label": __("Months Ahead"),
            "fieldtype": "Int",
            "default": 12,
            "reqd": 1
        },
        {
            "fieldname": "include_scenarios",
            "label": __("Include Scenarios"),
            "fieldtype": "Check",
            "default": 1
        },
        {
            "fieldname": "forecast_type",
            "label": __("Forecast Type"),
            "fieldtype": "Select",
            "options": "\nRevenue\nExpense\nCash Flow",
            "default": ""
        },
        {
            "fieldname": "account_type",
            "label": __("Account Type"),
            "fieldtype": "Select",
            "options": "\nBank\nCash\nReceivable\nPayable\nRevenue\nExpense",
            "default": ""
        },
        {
            "fieldname": "confidence_threshold",
            "label": __("Min Confidence %"),
            "fieldtype": "Float",
            "default": 0,
            "description": "Show only forecasts with confidence above this threshold"
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "risk_level") {
            if (value == "High") {
                value = `<span class="indicator red">${value}</span>`;
            } else if (value == "Medium") {
                value = `<span class="indicator yellow">${value}</span>`;
            } else if (value == "Low") {
                value = `<span class="indicator green">${value}</span>`;
            }
        }
        
        if (column.fieldname == "net_cashflow" && data && data.net_cashflow < 0) {
            value = `<span style="color: red;">${value}</span>`;
        }
        
        if (column.fieldname == "closing_balance" && data && data.closing_balance < 0) {
            value = `<span style="color: red;">${value}</span>`;
        }
        
        return value;
    },

    "onload": function(report) {
        // Add custom buttons
        report.page.add_inner_button(__("Export to Excel"), function() {
            let filters = report.get_values();
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.cashflow_projection_report.cashflow_projection_report.export_report',
                args: {
                    filters: filters,
                    format: 'excel'
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__("Excel export initiated"));
                        // Download logic would go here
                    }
                }
            });
        });

        report.page.add_inner_button(__("Email Report"), function() {
            let filters = report.get_values();
            frappe.prompt([
                {
                    'fieldname': 'recipients',
                    'label': __('Recipients'),
                    'fieldtype': 'Data',
                    'reqd': 1,
                    'description': 'Comma separated email addresses'
                },
                {
                    'fieldname': 'subject',
                    'label': __('Subject'),
                    'fieldtype': 'Data',
                    'default': 'Cash Flow Projection Report'
                },
                {
                    'fieldname': 'message',
                    'label': __('Message'),
                    'fieldtype': 'Text',
                    'default': 'Please find attached the cash flow projection report.'
                }
            ], function(values) {
                frappe.call({
                    method: 'ai_inventory.ai_inventory.report.cashflow_projection_report.cashflow_projection_report.email_report',
                    args: {
                        filters: filters,
                        recipients: values.recipients,
                        subject: values.subject,
                        message: values.message
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__("Report emailed successfully"));
                        } else {
                            frappe.msgprint(__("Error sending email: ") + (r.message.error || "Unknown error"));
                        }
                    }
                });
            }, __('Email Report'), __('Send'));
        });

        report.page.add_inner_button(__("Generate Dashboard"), function() {
            let filters = report.get_values();
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.cashflow_projection_report.cashflow_projection_report.create_dashboard_charts',
                args: {
                    filters: filters
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__("Dashboard charts created successfully"));
                        // Show chart data in a dialog instead of redirecting
                        if (r.message.chart_data) {
                            show_dashboard_dialog(r.message.chart_data);
                        }
                    } else {
                        frappe.msgprint(__("Error creating dashboard: ") + (r.message ? r.message.error : "Unknown error"));
                    }
                },
                error: function(r) {
                    frappe.msgprint(__("Error creating dashboard: ") + (r.message || "Network error"));
                }
            });
        });

        report.page.add_inner_button(__("Scenario Analysis"), function() {
            let filters = report.get_values();
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.cashflow_projection_report.cashflow_projection_report.get_scenario_analysis_data',
                args: {
                    filters: filters
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        show_scenario_dialog(r.message.data);
                    } else {
                        frappe.msgprint(__("Error getting scenario data: ") + (r.message ? r.message.error : "Unknown error"));
                    }
                },
                error: function(r) {
                    frappe.msgprint(__("Error getting scenario data: ") + (r.message || "Network error"));
                }
            });
        });
    },

    "after_datatable_render": function(datatable_obj) {
        // Remove any existing summary to prevent duplication
        $(datatable_obj.wrapper).find('.report-summary').remove();
        
        // Add summary row calculations
        const data = datatable_obj.datamanager.data;
        if (data && data.length > 0) {
            let total_inflow = 0;
            let total_outflow = 0;
            let total_net = 0;
            
            data.forEach(row => {
                if (row.period !== 'Current') {
                    total_inflow += row.cash_inflow || 0;
                    total_outflow += row.cash_outflow || 0;
                    total_net += row.net_cashflow || 0;
                }
            });
            
            // Add summary information
            const summary_html = `
                <div class="report-summary" style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                    <h5>Projection Summary</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Total Projected Inflow:</strong><br>
                            <span style="color: green; font-size: 1.2em;">${format_currency(total_inflow)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Total Projected Outflow:</strong><br>
                            <span style="color: red; font-size: 1.2em;">${format_currency(total_outflow)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Net Projected Cash Flow:</strong><br>
                            <span style="color: ${total_net >= 0 ? 'green' : 'red'}; font-size: 1.2em;">${format_currency(total_net)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Projection Period:</strong><br>
                            <span>${data.length - 1} months</span>
                        </div>
                    </div>
                </div>
            `;
            
            $(datatable_obj.wrapper).find('.dt-scrollable').after(summary_html);
        }
    }
};

// Helper functions
function show_scenario_dialog(scenario_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Scenario Analysis'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'scenario_html'
            }
        ],
        size: 'large'
    });
    
    let html = '<div class="scenario-analysis">';
    
    if (scenario_data.optimistic) {
        html += `
            <div class="scenario-card" style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                <h5 style="color: green;">Optimistic Scenario</h5>
                <p><strong>Projected Net Cash Flow:</strong> ${format_currency(scenario_data.optimistic.net_cashflow)}</p>
                <p><strong>Probability:</strong> ${scenario_data.optimistic.probability}%</p>
                <p><strong>Key Assumptions:</strong> ${scenario_data.optimistic.assumptions}</p>
            </div>
        `;
    }
    
    if (scenario_data.realistic) {
        html += `
            <div class="scenario-card" style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                <h5 style="color: blue;">Realistic Scenario</h5>
                <p><strong>Projected Net Cash Flow:</strong> ${format_currency(scenario_data.realistic.net_cashflow)}</p>
                <p><strong>Probability:</strong> ${scenario_data.realistic.probability}%</p>
                <p><strong>Key Assumptions:</strong> ${scenario_data.realistic.assumptions}</p>
            </div>
        `;
    }
    
    if (scenario_data.pessimistic) {
        html += `
            <div class="scenario-card" style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                <h5 style="color: red;">Pessimistic Scenario</h5>
                <p><strong>Projected Net Cash Flow:</strong> ${format_currency(scenario_data.pessimistic.net_cashflow)}</p>
                <p><strong>Probability:</strong> ${scenario_data.pessimistic.probability}%</p>
                <p><strong>Key Assumptions:</strong> ${scenario_data.pessimistic.assumptions}</p>
            </div>
        `;
    }
    
    html += '</div>';
    
    dialog.fields_dict.scenario_html.$wrapper.html(html);
    dialog.show();
}

function format_currency(value) {
    if (!value) return "₹0.00";
    
    // Get company from current report filters
    let report = frappe.query_report;
    let company = report ? report.get_values().company : null;
    
    // Get company-specific currency or fallback to system default
    var currency = "INR"; // Default to INR
    if (company && frappe.get_doc && frappe.get_doc("Company", company)) {
        currency = frappe.get_doc("Company", company).default_currency || "INR";
    } else {
        currency = frappe.defaults.get_default("currency") || frappe.boot.sysdefaults.currency || "INR";
    }
    
    // Format based on currency
    if (currency === "INR") {
        // Indian Rupee formatting with ₹ symbol
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(value);
    } else if (currency === "USD") {
        // US Dollar formatting
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    } else {
        // Generic formatting for other currencies
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(value);
    }
}

function show_dashboard_dialog(chart_data) {
    let dialog_content = `
        <div class="dashboard-charts">
            <div class="row">
                <div class="col-md-12">
                    <h6>Cash Flow Overview</h6>
                    <div class="alert alert-info">
                        <strong>Dashboard Charts Created Successfully!</strong><br>
                        Chart data has been generated and is ready for visualization.
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6">
                    <h6>Summary Metrics</h6>
                    <table class="table table-sm">
                        <tr>
                            <td><strong>Total Projected Inflow:</strong></td>
                            <td class="text-success">${format_currency(chart_data.total_inflow || 0)}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Projected Outflow:</strong></td>
                            <td class="text-danger">${format_currency(chart_data.total_outflow || 0)}</td>
                        </tr>
                        <tr>
                            <td><strong>Net Cash Flow:</strong></td>
                            <td class="${(chart_data.net_flow || 0) >= 0 ? 'text-success' : 'text-danger'}">${format_currency(chart_data.net_flow || 0)}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Period Analysis</h6>
                    <p><strong>Analysis Period:</strong> ${chart_data.period || 'Next 12 months'}</p>
                    <p><strong>Data Points:</strong> ${chart_data.data_points || 'N/A'}</p>
                    <p><strong>Confidence Level:</strong> ${chart_data.confidence || 'Medium'}</p>
                </div>
            </div>
        </div>
    `;

    let d = new frappe.ui.Dialog({
        title: __("Cash Flow Dashboard"),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'dashboard_html',
                options: dialog_content
            }
        ],
        size: 'large'
    });
    d.show();
}