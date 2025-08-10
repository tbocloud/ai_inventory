// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Risk Assessment Dashboard"] = {
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
            "label": __("Assessment Period (Months)"),
            "fieldtype": "Select",
            "options": "3\n6\n12\n18\n24",
            "default": "6",
            "reqd": 0
        },
        {
            "fieldname": "risk_category",
            "label": __("Risk Category"),
            "fieldtype": "Select",
            "options": "\nAll\nFinancial\nOperational\nMarket\nCompliance",
            "default": "All",
            "reqd": 0
        },
        {
            "fieldname": "risk_level",
            "label": __("Risk Level"),
            "fieldtype": "Select",
            "options": "\nAll\nCritical\nHigh\nMedium\nLow",
            "default": "All",
            "reqd": 0
        }
    ],
    
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "risk_level" && data && data.risk_level) {
            if (data.risk_level == "Critical") {
                value = "<span style='color:red; font-weight:bold; background-color:#ffebee; padding:2px 6px; border-radius:3px'>" + value + "</span>";
            } else if (data.risk_level == "High") {
                value = "<span style='color:orange; font-weight:bold; background-color:#fff3e0; padding:2px 6px; border-radius:3px'>" + value + "</span>";
            } else if (data.risk_level == "Medium") {
                value = "<span style='color:#f57c00; background-color:#fffde7; padding:2px 6px; border-radius:3px'>" + value + "</span>";
            } else if (data.risk_level == "Low") {
                value = "<span style='color:green; background-color:#e8f5e8; padding:2px 6px; border-radius:3px'>" + value + "</span>";
            }
        }
        
        if (column.fieldname == "mitigation_status" && data && data.mitigation_status) {
            if (data.mitigation_status == "Active") {
                value = "<span style='color:blue; font-weight:bold'>🔧 " + value + "</span>";
            } else if (data.mitigation_status == "Controlled") {
                value = "<span style='color:green'>✅ " + value + "</span>";
            } else if (data.mitigation_status == "Under Review") {
                value = "<span style='color:orange'>⏳ " + value + "</span>";
            } else if (data.mitigation_status == "Monitoring") {
                value = "<span style='color:gray'>👁 " + value + "</span>";
            }
        }
        
        if (column.fieldname == "trend" && data && data.trend) {
            if (data.trend == "Increasing") {
                value = "<span style='color:red'>📈 " + value + "</span>";
            } else if (data.trend == "Decreasing") {
                value = "<span style='color:green'>📉 " + value + "</span>";
            } else {
                value = "<span style='color:gray'>➡ " + value + "</span>";
            }
        }
        
        if (column.fieldname == "risk_score" && data && data.risk_score) {
            if (data.risk_score >= 7) {
                value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
            } else if (data.risk_score >= 5) {
                value = "<span style='color:orange; font-weight:bold'>" + value + "</span>";
            } else if (data.risk_score >= 3) {
                value = "<span style='color:#f57c00'>" + value + "</span>";
            } else {
                value = "<span style='color:green'>" + value + "</span>";
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons for risk management
        report.page.add_menu_item(__("Risk Matrix"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.risk_assessment_dashboard.risk_assessment_dashboard.generate_risk_assessment_dashboard',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 6
                },
                callback: function(r) {
                    if (r.message) {
                        show_risk_matrix_dialog(r.message);
                    }
                }
            });
        });
        
        report.page.add_menu_item(__("Mitigation Plan"), function() {
            let filters = report.get_values();
            show_mitigation_plan_dialog(filters);
        });
        
        report.page.add_menu_item(__("Export Risk Report"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.risk_assessment_dashboard.risk_assessment_dashboard.export_risk_assessment',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 6,
                    format: 'excel'
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__("Risk assessment exported successfully"));
                    }
                }
            });
        });
    }
};

function show_risk_matrix_dialog(risk_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Risk Assessment Matrix'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'risk_matrix_html'
            }
        ]
    });
    
    let html = generate_risk_matrix_html(risk_data);
    dialog.fields_dict.risk_matrix_html.$wrapper.html(html);
    dialog.show();
}

function show_mitigation_plan_dialog(filters) {
    let dialog = new frappe.ui.Dialog({
        title: __('Risk Mitigation Plan'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'mitigation_html'
            }
        ]
    });
    
    let html = `
        <div class="risk-mitigation-plan">
            <h4>Priority Actions</h4>
            <ul>
                <li><strong>Critical Risks:</strong> Immediate action required within 24-48 hours</li>
                <li><strong>High Risks:</strong> Action plan to be implemented within 1 week</li>
                <li><strong>Medium Risks:</strong> Review and monitor quarterly</li>
                <li><strong>Low Risks:</strong> Annual review sufficient</li>
            </ul>
            
            <h4>Mitigation Strategies</h4>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Risk Level</th>
                        <th>Strategy</th>
                        <th>Responsibility</th>
                        <th>Timeline</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span style="color:red">Critical</span></td>
                        <td>Crisis management, immediate containment</td>
                        <td>Executive Team</td>
                        <td>24-48 hours</td>
                    </tr>
                    <tr>
                        <td><span style="color:orange">High</span></td>
                        <td>Active mitigation, contingency planning</td>
                        <td>Department Heads</td>
                        <td>1 week</td>
                    </tr>
                    <tr>
                        <td><span style="color:#f57c00">Medium</span></td>
                        <td>Risk monitoring, preventive measures</td>
                        <td>Risk Managers</td>
                        <td>1 month</td>
                    </tr>
                    <tr>
                        <td><span style="color:green">Low</span></td>
                        <td>Periodic review, documentation</td>
                        <td>Risk Committee</td>
                        <td>Quarterly</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <style>
        .risk-mitigation-plan {
            padding: 20px;
        }
        .risk-mitigation-plan h4 {
            color: #32325d;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .risk-mitigation-plan table {
            font-size: 14px;
        }
        </style>
    `;
    
    dialog.fields_dict.mitigation_html.$wrapper.html(html);
    dialog.show();
}

function generate_risk_matrix_html(data) {
    let html = `
        <div class="risk-matrix">
            <h3>${data.report_title}</h3>
            <p><strong>Overall Risk Score:</strong> <span class="risk-score-${data.risk_level.toLowerCase()}">${data.overall_risk_score}</span></p>
            <p><strong>Risk Level:</strong> <span class="risk-level-${data.risk_level.toLowerCase()}">${data.risk_level}</span></p>
            
            <div class="row">
                <div class="col-md-6">
                    <h4>Risk Summary</h4>
                    <table class="table table-bordered">
                        <tr><td>Financial Risks</td><td>${data.financial_risks ? data.financial_risks.length : 0}</td></tr>
                        <tr><td>Operational Risks</td><td>${data.operational_risks ? data.operational_risks.length : 0}</td></tr>
                        <tr><td>Market Risks</td><td>${data.market_risks ? data.market_risks.length : 0}</td></tr>
                        <tr><td>Risk Trend</td><td>${data.risk_trend || 'Stable'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h4>Key Insights</h4>
                    <ul>`;
    
    if (data.risk_insights && data.risk_insights.length > 0) {
        data.risk_insights.forEach(insight => {
            html += `<li>${insight}</li>`;
        });
    } else {
        html += `<li>Regular monitoring recommended</li>
                <li>Focus on high-probability risks</li>
                <li>Maintain mitigation strategies</li>`;
    }
    
    html += `
                    </ul>
                </div>
            </div>
        </div>
        
        <style>
        .risk-matrix {
            padding: 20px;
        }
        .risk-matrix h3 {
            color: #5e72e4;
            margin-bottom: 20px;
        }
        .risk-matrix h4 {
            color: #32325d;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .risk-level-critical { color: red; font-weight: bold; }
        .risk-level-high { color: orange; font-weight: bold; }
        .risk-level-medium { color: #f57c00; }
        .risk-level-low { color: green; }
        </style>
    `;
    
    return html;
}
