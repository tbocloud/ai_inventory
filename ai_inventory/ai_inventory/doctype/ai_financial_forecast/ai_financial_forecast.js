// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Financial Forecast", {
    refresh: function(frm) {
        // Add custom buttons and functionality
        add_custom_buttons(frm);
        
        // Setup field watchers
        setup_field_watchers(frm);
        
        // Load dashboard if forecast exists
        if (!frm.is_new()) {
            load_forecast_dashboard(frm);
        }
    },
    
    company: function(frm) {
        // Filter accounts based on company
        frm.set_query("account", function() {
            return {
                filters: {
                    "company": frm.doc.company,
                    "is_group": 0
                }
            };
        });
    },
    
    account: function(frm) {
        if (frm.doc.account) {
            // Auto-populate account details
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Account",
                    name: frm.doc.account
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("account_name", r.message.account_name);
                        frm.set_value("account_type", r.message.account_type);
                    }
                }
            });
        }
    },
    
    forecast_type: function(frm) {
        // Adjust parameters based on forecast type
        adjust_forecast_parameters(frm);
    },
    
    forecast_period_days: function(frm) {
        // Calculate end date
        if (frm.doc.forecast_start_date && frm.doc.forecast_period_days) {
            let end_date = frappe.datetime.add_days(frm.doc.forecast_start_date, frm.doc.forecast_period_days);
            frm.set_value("forecast_end_date", end_date);
        }
    }
});

function add_custom_buttons(frm) {
    if (!frm.is_new()) {
        // Generate Forecast button
        frm.add_custom_button(__("Generate New Forecast"), function() {
            generate_new_forecast(frm);
        }, __("Actions"));
        
        // View Analytics button
        frm.add_custom_button(__("View Analytics"), function() {
            view_forecast_analytics(frm);
        }, __("Reports"));
        
        // Sync with Inventory button
        frm.add_custom_button(__("Sync with Inventory"), function() {
            sync_with_inventory(frm);
        }, __("Integration"));
        
        // Export Forecast Data button
        frm.add_custom_button(__("Export Data"), function() {
            export_forecast_data(frm);
        }, __("Reports"));
        
        // Validate System Health button
        frm.add_custom_button(__("System Health Check"), function() {
            check_system_health(frm);
        }, __("System"));
    }
    
    if (frm.is_new()) {
        // Quick Setup button for new forecasts
        frm.add_custom_button(__("Quick Setup"), function() {
            quick_forecast_setup(frm);
        });
    }
}

function setup_field_watchers(frm) {
    // Watch for changes in key fields and show indicators
    
    // Confidence Score Indicator
    frm.fields_dict.confidence_score.$wrapper.append(`
        <div class="confidence-indicator" style="margin-top: 5px;">
            <div class="confidence-bar" style="height: 8px; background: #f0f0f0; border-radius: 4px;">
                <div class="confidence-fill" style="height: 100%; background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60); border-radius: 4px; width: ${frm.doc.confidence_score || 0}%;"></div>
            </div>
            <small class="text-muted">Confidence Level: ${get_confidence_label(frm.doc.confidence_score)}</small>
        </div>
    `);
    
    // Risk Category Indicator
    if (frm.doc.risk_category) {
        let color = get_risk_color(frm.doc.risk_category);
        frm.get_field('risk_category').$wrapper.find('.control-input').css('color', color);
    }
}

function generate_new_forecast(frm) {
    frappe.confirm(
        __("Generate new forecast? This will update the current predictions."),
        function() {
            frappe.call({
                method: "ai_inventory.ai_accounts_forecast.api.forecast_api.api_create_forecast",
                args: {
                    company: frm.doc.company,
                    account: frm.doc.account,
                    forecast_type: frm.doc.forecast_type,
                    forecast_period_days: frm.doc.forecast_period_days,
                    confidence_threshold: frm.doc.confidence_threshold
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Forecast generated successfully!"),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __("Forecast Generation Failed"),
                            message: r.message.error || __("Unknown error occurred"),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function view_forecast_analytics(frm) {
    // Create analytics dialog
    let dialog = new frappe.ui.Dialog({
        title: __("Forecast Analytics"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "analytics_html"
            }
        ]
    });
    
    // Load analytics data
    frappe.call({
        method: "ai_inventory.ai_accounts_forecast.api.forecast_api.get_forecast_analytics",
        args: {
            forecast_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let analytics_html = generate_analytics_html(r.message);
                dialog.fields_dict.analytics_html.$wrapper.html(analytics_html);
                dialog.show();
            }
        }
    });
}

function sync_with_inventory(frm) {
    frappe.call({
        method: "ai_inventory.ai_accounts_forecast.api.forecast_api.sync_with_inventory",
        args: {
            company: frm.doc.company,
            account: frm.doc.account
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Inventory sync completed"),
                    indicator: 'green'
                });
                frm.reload_doc();
            }
        }
    });
}

function export_forecast_data(frm) {
    let url = `/api/method/ai_inventory.ai_accounts_forecast.api.forecast_api.export_forecast_data?forecast_id=${frm.doc.name}`;
    window.open(url, '_blank');
}

function check_system_health(frm) {
    frappe.call({
        method: "ai_inventory.ai_accounts_forecast.api.forecast_api.get_system_health",
        args: {
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message) {
                show_health_report(r.message);
            }
        }
    });
}

function quick_forecast_setup(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Quick Forecast Setup"),
        fields: [
            {
                fieldtype: "Select",
                label: __("Setup Type"),
                fieldname: "setup_type",
                options: ["Cash Flow Only", "Revenue Focus", "Expense Focus", "Complete Analysis"],
                reqd: 1
            },
            {
                fieldtype: "Check",
                label: __("Include Inventory Integration"),
                fieldname: "include_inventory",
                default: 1
            },
            {
                fieldtype: "Check", 
                label: __("Enable Auto Sync"),
                fieldname: "auto_sync",
                default: 1
            }
        ],
        primary_action: function(values) {
            apply_quick_setup(frm, values);
            dialog.hide();
        },
        primary_action_label: __("Apply Setup")
    });
    
    dialog.show();
}

function apply_quick_setup(frm, values) {
    // Apply quick setup based on selected type
    switch(values.setup_type) {
        case "Cash Flow Only":
            frm.set_value("forecast_type", "Cash Flow");
            frm.set_value("prediction_model", "ARIMA");
            break;
        case "Revenue Focus":
            frm.set_value("forecast_type", "Revenue");
            frm.set_value("prediction_model", "Prophet");
            break;
        case "Expense Focus":
            frm.set_value("forecast_type", "Expense");
            frm.set_value("prediction_model", "Linear Regression");
            break;
        case "Complete Analysis":
            frm.set_value("prediction_model", "Ensemble");
            break;
    }
    
    if (values.include_inventory) {
        frm.set_value("inventory_sync_enabled", 1);
        frm.set_value("integration_mode", "Inventory Integrated");
    }
    
    if (values.auto_sync) {
        frm.set_value("auto_sync_enabled", 1);
        frm.set_value("sync_frequency", "Daily");
    }
    
    // Set reasonable defaults
    frm.set_value("forecast_period_days", 90);
    frm.set_value("confidence_threshold", 70);
    frm.set_value("seasonal_adjustment", 1);
    frm.set_value("forecast_start_date", frappe.datetime.get_today());
}

function adjust_forecast_parameters(frm) {
    // Adjust parameters based on forecast type
    let forecast_type = frm.doc.forecast_type;
    
    switch(forecast_type) {
        case "Cash Flow":
            frm.set_value("prediction_model", "ARIMA");
            frm.set_value("confidence_threshold", 75);
            break;
        case "Revenue":
            frm.set_value("prediction_model", "Prophet");
            frm.set_value("confidence_threshold", 70);
            break;
        case "Expense":
            frm.set_value("prediction_model", "Linear Regression");
            frm.set_value("confidence_threshold", 80);
            break;
        case "Balance Sheet":
            frm.set_value("prediction_model", "Ensemble");
            frm.set_value("confidence_threshold", 65);
            break;
        case "P&L":
            frm.set_value("prediction_model", "Random Forest");
            frm.set_value("confidence_threshold", 70);
            break;
    }
}

function load_forecast_dashboard(frm) {
    // Create dashboard section
    if (!frm.dashboard_added) {
        frm.dashboard.add_section(`
            <div class="forecast-dashboard">
                <div class="row">
                    <div class="col-md-3">
                        <div class="forecast-metric">
                            <h4>${format_currency(frm.doc.predicted_amount || 0)}</h4>
                            <small>Predicted Amount</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="forecast-metric">
                            <h4>${frm.doc.confidence_score || 0}%</h4>
                            <small>Confidence Score</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="forecast-metric">
                            <h4>${frm.doc.risk_category || "Unknown"}</h4>
                            <small>Risk Category</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="forecast-metric">
                            <h4>${frm.doc.forecast_accuracy || "N/A"}</h4>
                            <small>Accuracy</small>
                        </div>
                    </div>
                </div>
            </div>
        `, __("Forecast Overview"));
        
        frm.dashboard_added = true;
    }
}

// Utility functions
function get_confidence_label(score) {
    if (score >= 80) return "High";
    if (score >= 60) return "Medium";
    if (score >= 40) return "Low";
    return "Very Low";
}

function get_risk_color(risk_category) {
    switch(risk_category) {
        case "Low": return "#27ae60";
        case "Medium": return "#f39c12";
        case "High": return "#e74c3c";
        case "Critical": return "#8e44ad";
        default: return "#95a5a6";
    }
}

function generate_analytics_html(data) {
    return `
        <div class="analytics-container">
            <h4>Forecast Analytics</h4>
            <div class="row">
                <div class="col-md-6">
                    <h5>Prediction Details</h5>
                    <table class="table table-bordered">
                        <tr><td>Model Used</td><td>${data.model_type || "N/A"}</td></tr>
                        <tr><td>Confidence Score</td><td>${data.confidence || 0}%</td></tr>
                        <tr><td>Prediction Range</td><td>${format_currency(data.lower_bound || 0)} - ${format_currency(data.upper_bound || 0)}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Model Performance</h5>
                    <table class="table table-bordered">
                        <tr><td>R² Score</td><td>${data.r2_score || "N/A"}</td></tr>
                        <tr><td>MAE</td><td>${data.mae || "N/A"}</td></tr>
                        <tr><td>RMSE</td><td>${data.rmse || "N/A"}</td></tr>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function show_health_report(health_data) {
    let dialog = new frappe.ui.Dialog({
        title: __("System Health Report"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "health_html"
            }
        ]
    });
    
    let health_html = `
        <div class="health-report">
            <h4>System Health: ${health_data.status}</h4>
            <div class="health-score" style="font-size: 24px; color: ${health_data.health_score >= 75 ? '#27ae60' : '#e74c3c'}">
                ${health_data.health_score}%
            </div>
            <hr>
            <div class="row">
                <div class="col-md-6">
                    <h5>Metrics</h5>
                    <ul>
                        <li>Average Confidence: ${health_data.avg_confidence}%</li>
                        <li>High Confidence Ratio: ${health_data.high_confidence_ratio}%</li>
                        <li>Active Forecast Types: ${health_data.forecast_types_active}</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.health_html.$wrapper.html(health_html);
    dialog.show();
}

// Format currency helper
function format_currency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}
