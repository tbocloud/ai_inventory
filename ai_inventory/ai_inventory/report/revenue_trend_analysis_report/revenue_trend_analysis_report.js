// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Revenue Trend Analysis Report"] = {
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
            "options": "6\n12\n18\n24\n36",
            "default": "18",
            "reqd": 0
        },
        {
            "fieldname": "include_breakdown",
            "label": __("Include Revenue Breakdown"),
            "fieldtype": "Check",
            "default": 1,
            "reqd": 0
        }
    ],
    
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "mom_growth_rate" && data && data.mom_growth_rate) {
            if (data.mom_growth_rate > 5) {
                value = "<span style='color:green; font-weight:bold'>📈 " + value + "</span>";
            } else if (data.mom_growth_rate > 0) {
                value = "<span style='color:green'>⬆ " + value + "</span>";
            } else if (data.mom_growth_rate < -5) {
                value = "<span style='color:red; font-weight:bold'>📉 " + value + "</span>";
            } else if (data.mom_growth_rate < 0) {
                value = "<span style='color:red'>⬇ " + value + "</span>";
            } else {
                value = "<span style='color:gray'>➡ " + value + "</span>";
            }
        }
        
        if (column.fieldname == "trend_direction" && data && data.trend_direction) {
            if (data.trend_direction == "Strong Growth") {
                value = "<span style='color:green; font-weight:bold; background-color:#e8f5e8; padding:2px 6px; border-radius:3px'>🚀 " + value + "</span>";
            } else if (data.trend_direction == "Growth") {
                value = "<span style='color:green; background-color:#e8f5e8; padding:2px 6px; border-radius:3px'>📈 " + value + "</span>";
            } else if (data.trend_direction == "Declining") {
                value = "<span style='color:red; background-color:#ffebee; padding:2px 6px; border-radius:3px'>📉 " + value + "</span>";
            } else {
                value = "<span style='color:gray; background-color:#f5f5f5; padding:2px 6px; border-radius:3px'>➡ " + value + "</span>";
            }
        }
        
        if (column.fieldname == "volatility" && data && data.volatility) {
            if (data.volatility > 20) {
                value = "<span style='color:red; font-weight:bold'>⚠ " + value + "</span>";
            } else if (data.volatility > 10) {
                value = "<span style='color:orange'>⚡ " + value + "</span>";
            } else {
                value = "<span style='color:green'>✅ " + value + "</span>";
            }
        }
        
        if (column.fieldname == "avg_confidence" && data && data.avg_confidence) {
            if (data.avg_confidence >= 90) {
                value = "<span style='color:green; font-weight:bold'>🎯 " + value + "</span>";
            } else if (data.avg_confidence >= 70) {
                value = "<span style='color:green'>✅ " + value + "</span>";
            } else if (data.avg_confidence >= 50) {
                value = "<span style='color:orange'>⚠ " + value + "</span>";
            } else {
                value = "<span style='color:red'>❌ " + value + "</span>";
            }
        }
        
        if (column.fieldname == "seasonal_factor" && data && data.seasonal_factor) {
            if (data.seasonal_factor > 1.2) {
                value = "<span style='color:green; font-weight:bold'>🔥 " + value + "</span>";
            } else if (data.seasonal_factor > 1.0) {
                value = "<span style='color:green'>⬆ " + value + "</span>";
            } else if (data.seasonal_factor < 0.8) {
                value = "<span style='color:red'>⬇ " + value + "</span>";
            } else {
                value = "<span style='color:gray'>➡ " + value + "</span>";
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons for revenue analysis
        report.page.add_menu_item(__("Revenue Breakdown"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.revenue_trend_analysis_report.revenue_trend_analysis_report.get_revenue_breakdown',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 18
                },
                callback: function(r) {
                    if (r.message) {
                        show_revenue_breakdown_dialog(r.message);
                    }
                }
            });
        });
        
        report.page.add_menu_item(__("Growth Analysis"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.revenue_trend_analysis_report.revenue_trend_analysis_report.get_growth_analysis',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 18
                },
                callback: function(r) {
                    if (r.message) {
                        show_growth_analysis_dialog(r.message);
                    }
                }
            });
        });
        
        report.page.add_menu_item(__("Seasonal Analysis"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.revenue_trend_analysis_report.revenue_trend_analysis_report.get_seasonal_analysis',
                args: {
                    company: filters.company
                },
                callback: function(r) {
                    if (r.message) {
                        show_seasonal_analysis_dialog(r.message);
                    }
                }
            });
        });
        
        report.page.add_menu_item(__("Export Report"), function() {
            let filters = report.get_values();
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.report.revenue_trend_analysis_report.revenue_trend_analysis_report.export_revenue_trend_report',
                args: {
                    company: filters.company,
                    period_months: parseInt(filters.period_months) || 18,
                    format: 'excel'
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__("Revenue trend analysis exported successfully"));
                    }
                }
            });
        });
    }
};

function show_revenue_breakdown_dialog(breakdown_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Revenue Breakdown Analysis'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'breakdown_html'
            }
        ]
    });
    
    let html = generate_breakdown_html(breakdown_data);
    dialog.fields_dict.breakdown_html.$wrapper.html(html);
    dialog.show();
}

function show_growth_analysis_dialog(growth_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Revenue Growth Analysis'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'growth_html'
            }
        ]
    });
    
    let html = generate_growth_html(growth_data);
    dialog.fields_dict.growth_html.$wrapper.html(html);
    dialog.show();
}

function show_seasonal_analysis_dialog(seasonal_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Seasonal Revenue Analysis'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'seasonal_html'
            }
        ]
    });
    
    let html = generate_seasonal_html(seasonal_data);
    dialog.fields_dict.seasonal_html.$wrapper.html(html);
    dialog.show();
}

function generate_breakdown_html(data) {
    let html = `
        <div class="revenue-breakdown">
            <h4>Revenue Sources</h4>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Account</th>
                        <th>Revenue</th>
                        <th>Percentage</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>`;
    
    if (data.account_breakdown && data.account_breakdown.length > 0) {
        data.account_breakdown.slice(0, 10).forEach(account => {
            html += `
                <tr>
                    <td>${account.account_name}</td>
                    <td>₹${account.total_revenue.toLocaleString()}</td>
                    <td>${account.percentage}%</td>
                    <td>${account.avg_confidence}%</td>
                </tr>`;
        });
    } else {
        html += '<tr><td colspan="4">No breakdown data available</td></tr>';
    }
    
    html += `
                </tbody>
            </table>
            <p><strong>Total Revenue:</strong> ₹${data.total_revenue ? data.total_revenue.toLocaleString() : 0}</p>
        </div>
        
        <style>
        .revenue-breakdown {
            padding: 20px;
        }
        .revenue-breakdown table {
            font-size: 14px;
        }
        .revenue-breakdown h4 {
            color: #32325d;
            margin-bottom: 15px;
        }
        </style>
    `;
    
    return html;
}

function generate_growth_html(data) {
    let html = `
        <div class="growth-analysis">
            <h4>Growth Metrics</h4>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Current Growth Rate:</strong> <span class="${data.current_growth_rate > 0 ? 'text-success' : 'text-danger'}">${data.current_growth_rate}%</span></p>
                    <p><strong>CAGR:</strong> ${data.cagr}%</p>
                    <p><strong>Growth Consistency:</strong> ${data.growth_consistency}</p>
                    <p><strong>Trend Direction:</strong> ${data.trend_direction}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Growth Volatility:</strong> ${data.growth_volatility}%</p>
                </div>
            </div>
        </div>
        
        <style>
        .growth-analysis {
            padding: 20px;
        }
        .growth-analysis h4 {
            color: #32325d;
            margin-bottom: 15px;
        }
        </style>
    `;
    
    return html;
}

function generate_seasonal_html(data) {
    let html = `
        <div class="seasonal-analysis">
            <h4>Seasonal Patterns</h4>`;
    
    if (data.available) {
        html += `
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Seasonality Strength:</strong> ${data.seasonal_intensity}</p>
                    <p><strong>Peak Months:</strong> ${data.peak_months.join(', ')}</p>
                    <p><strong>Low Months:</strong> ${data.low_months.join(', ')}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Peak Season Boost:</strong> +${data.peak_season_boost}%</p>
                    <p><strong>Low Season Impact:</strong> -${data.low_season_impact}%</p>
                    <p><strong>Current Seasonal Factor:</strong> ${data.current_seasonal_factor.toFixed(3)}</p>
                </div>
            </div>`;
    } else {
        html += '<p>No seasonal data available for analysis.</p>';
    }
    
    html += `
        </div>
        
        <style>
        .seasonal-analysis {
            padding: 20px;
        }
        .seasonal-analysis h4 {
            color: #32325d;
            margin-bottom: 15px;
        }
        </style>
    `;
    
    return html;
}
