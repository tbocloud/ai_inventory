// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Financial Settings", {
    refresh(frm) {
        // Add manual forecast buttons
        add_manual_forecast_buttons(frm);
        
        // Add system management buttons
        add_system_management_buttons(frm);
        
        // Show system status
        display_system_status(frm);
    },
    
    enable_financial_forecasting(frm) {
        // Toggle forecast-related fields based on main setting
        toggle_forecast_fields(frm);
    },
    
    auto_sync_enabled(frm) {
        // Show/hide sync frequency based on auto sync setting
        frm.toggle_display('sync_frequency', frm.doc.auto_sync_enabled);
    }
});

function add_manual_forecast_buttons(frm) {
    // Manual Forecast Generation Section
    frm.add_custom_button(__("Generate Forecasts for All Companies"), function() {
        generate_bulk_forecasts(frm, 'all_companies');
    }, __("Manual Forecasting"));
    
    frm.add_custom_button(__("Generate by Company"), function() {
        generate_forecasts_by_company(frm);
    }, __("Manual Forecasting"));
    
    frm.add_custom_button(__("Generate by Account Type"), function() {
        generate_forecasts_by_account_type(frm);
    }, __("Manual Forecasting"));
    
    frm.add_custom_button(__("Quick Cash Flow Forecast"), function() {
        generate_quick_cash_flow_forecast(frm);
    }, __("Manual Forecasting"));
    
    frm.add_custom_button(__("Revenue Forecast"), function() {
        generate_revenue_forecast(frm);
    }, __("Manual Forecasting"));
    
    frm.add_custom_button(__("Expense Forecast"), function() {
        generate_expense_forecast(frm);
    }, __("Manual Forecasting"));
}

function add_system_management_buttons(frm) {
    // System Management Section
    frm.add_custom_button(__("System Health Check"), function() {
        run_system_health_check(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("Sync All Forecasts"), function() {
        sync_all_forecasts(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("Check Sync Status"), function() {
        check_sync_status(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("Force Sync Specific"), function() {
        force_sync_specific_forecast(frm);
    }, __("System Management"));
    
    // Debug/Test button for sync troubleshooting
    frm.add_custom_button(__("Test Sync (Debug)"), function() {
        test_sync_functionality(frm);
    }, __("System Management"));
    
    // Accuracy Tracking Section
    frm.add_custom_button(__("Generate Accuracy Tracking"), function() {
        generate_accuracy_tracking(frm);
    }, __("Accuracy Management"));
    
    frm.add_custom_button(__("View Accuracy Summary"), function() {
        view_accuracy_summary(frm);
    }, __("Accuracy Management"));
    
    frm.add_custom_button(__("Update Forecast Accuracy"), function() {
        update_forecast_accuracy(frm);
    }, __("Accuracy Management"));
    
    frm.add_custom_button(__("Cleanup Old Data"), function() {
        cleanup_old_forecast_data(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("Model Performance Report"), function() {
        show_model_performance_report(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("Export System Report"), function() {
        export_system_report(frm);
    }, __("System Management"));
}

function generate_bulk_forecasts(frm, scope = 'all_companies') {
    frappe.confirm(
        __("Generate financial forecasts for all companies? This may take several minutes."),
        function() {
            frappe.show_alert({
                message: __("Starting bulk forecast generation..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_bulk_forecasts",
                args: {
                    scope: scope,
                    settings: frm.doc
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Bulk forecast generation completed successfully!"),
                            indicator: 'green'
                        });
                        
                        show_bulk_forecast_results(r.message);
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

function generate_forecasts_by_company(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Generate Forecasts by Company"),
        fields: [
            {
                fieldtype: "Link",
                label: __("Company"),
                fieldname: "company",
                options: "Company",
                reqd: 1
            },
            {
                fieldtype: "Section Break"
            },
            {
                fieldtype: "Check",
                label: __("Cash Flow"),
                fieldname: "cash_flow",
                default: 1
            },
            {
                fieldtype: "Check",
                label: __("Revenue"),
                fieldname: "revenue",
                default: 1
            },
            {
                fieldtype: "Check",
                label: __("Expense"),
                fieldname: "expense",
                default: 1
            },
            {
                fieldtype: "Column Break"
            },
            {
                fieldtype: "Check",
                label: __("Balance Sheet"),
                fieldname: "balance_sheet",
                default: 0
            },
            {
                fieldtype: "Check",
                label: __("P&L"),
                fieldname: "pnl",
                default: 0
            },
            {
                fieldtype: "Section Break"
            },
            {
                fieldtype: "Int",
                label: __("Forecast Period (Days)"),
                fieldname: "forecast_period",
                default: frm.doc.default_forecast_period || 90
            }
        ],
        primary_action: function(values) {
            if (!values.company) {
                frappe.msgprint(__("Please select a company"));
                return;
            }
            
            let forecast_types = [];
            if (values.cash_flow) forecast_types.push("Cash Flow");
            if (values.revenue) forecast_types.push("Revenue");
            if (values.expense) forecast_types.push("Expense");
            if (values.balance_sheet) forecast_types.push("Balance Sheet");
            if (values.pnl) forecast_types.push("P&L");
            
            if (forecast_types.length === 0) {
                frappe.msgprint(__("Please select at least one forecast type"));
                return;
            }
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_company_forecasts",
                args: {
                    company: values.company,
                    forecast_types: forecast_types,
                    forecast_period: values.forecast_period,
                    settings: frm.doc
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Company forecasts generated successfully!"),
                            indicator: 'green'
                        });
                        
                        show_forecast_results_dialog(r.message);
                    }
                }
            });
            
            dialog.hide();
        },
        primary_action_label: __("Generate Forecasts")
    });
    
    dialog.show();
}

function generate_forecasts_by_account_type(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Generate Forecasts by Account Type"),
        fields: [
            {
                fieldtype: "Select",
                label: __("Account Type"),
                fieldname: "account_type",
                options: "Asset\nLiability\nEquity\nIncome\nExpense",
                reqd: 1
            },
            {
                fieldtype: "Link",
                label: __("Company (Optional)"),
                fieldname: "company",
                options: "Company"
            },
            {
                fieldtype: "Section Break"
            },
            {
                fieldtype: "Select",
                label: __("Forecast Type"),
                fieldname: "forecast_type",
                options: "Cash Flow\nRevenue\nExpense\nBalance Sheet\nP&L",
                reqd: 1,
                default: "Cash Flow"
            },
            {
                fieldtype: "Int",
                label: __("Forecast Period (Days)"),
                fieldname: "forecast_period",
                default: frm.doc.default_forecast_period || 90
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_account_type_forecasts",
                args: {
                    account_type: values.account_type,
                    company: values.company,
                    forecast_type: values.forecast_type,
                    forecast_period: values.forecast_period,
                    settings: frm.doc
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Account type forecasts generated successfully!"),
                            indicator: 'green'
                        });
                        
                        show_forecast_results_dialog(r.message);
                    }
                }
            });
            
            dialog.hide();
        },
        primary_action_label: __("Generate Forecasts")
    });
    
    dialog.show();
}

function generate_quick_cash_flow_forecast(frm) {
    frappe.confirm(
        __("Generate quick cash flow forecasts for all companies?"),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_quick_cash_flow",
                args: {
                    settings: frm.doc
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Quick cash flow forecasts generated!"),
                            indicator: 'green'
                        });
                        
                        show_forecast_results_dialog(r.message);
                    }
                }
            });
        }
    );
}

function generate_revenue_forecast(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_revenue_forecasts",
        args: {
            settings: frm.doc
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Revenue forecasts generated!"),
                    indicator: 'green'
                });
                
                show_forecast_results_dialog(r.message);
            }
        }
    });
}

function generate_expense_forecast(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_expense_forecasts",
        args: {
            settings: frm.doc
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Expense forecasts generated!"),
                    indicator: 'green'
                });
                
                show_forecast_results_dialog(r.message);
            }
        }
    });
}

function run_system_health_check(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.run_system_health_check",
        callback: function(r) {
            if (r.message) {
                show_health_report_dialog(r.message);
            }
        }
    });
}

function sync_all_forecasts(frm) {
    frappe.confirm(
        __("Sync all existing forecasts? This will update all forecast data."),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.sync_all_forecasts",
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("All forecasts synchronized successfully!"),
                            indicator: 'green'
                        });
                        
                        show_sync_results_dialog(r.message);
                    }
                }
            });
        }
    );
}

function cleanup_old_forecast_data(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Cleanup Old Forecast Data"),
        fields: [
            {
                fieldtype: "Int",
                label: __("Delete Data Older Than (Days)"),
                fieldname: "days_old",
                default: frm.doc.data_retention_days || 365
            },
            {
                fieldtype: "Check",
                label: __("Delete Forecast Details"),
                fieldname: "delete_details",
                default: 1
            },
            {
                fieldtype: "Check",
                label: __("Delete Log Entries"),
                fieldname: "delete_logs",
                default: 1
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.cleanup_old_data",
                args: {
                    days_old: values.days_old,
                    delete_details: values.delete_details,
                    delete_logs: values.delete_logs
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Data cleanup completed successfully!"),
                            indicator: 'green'
                        });
                        
                        frappe.msgprint({
                            title: __("Cleanup Results"),
                            message: `<strong>Records Cleaned:</strong><br>
                                     Forecasts: ${r.message.forecasts_cleaned || 0}<br>
                                     Logs: ${r.message.logs_cleaned || 0}<br>
                                     Space Freed: ${r.message.space_freed || 'N/A'}`,
                            indicator: 'green'
                        });
                    }
                }
            });
            
            dialog.hide();
        },
        primary_action_label: __("Cleanup Data")
    });
    
    dialog.show();
}

function show_model_performance_report(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_model_performance_report",
        callback: function(r) {
            if (r.message) {
                show_performance_report_dialog(r.message);
            }
        }
    });
}

function export_system_report(frm) {
    let url = `/api/method/ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.export_system_report`;
    window.open(url, '_blank');
}

function toggle_forecast_fields(frm) {
    let enabled = frm.doc.enable_financial_forecasting;
    
    // Toggle visibility of forecast-related sections
    frm.toggle_display('model_settings_section', enabled);
    frm.toggle_display('integration_settings_section', enabled);
    frm.toggle_display('notification_settings_section', enabled);
}

function display_system_status(frm) {
    if (!frm.status_added) {
        frappe.call({
            method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_system_status",
            callback: function(r) {
                if (r.message) {
                    let status_html = `
                        <div class="system-status-dashboard">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="status-metric">
                                        <h4>${r.message.total_forecasts || 0}</h4>
                                        <small>Total Forecasts</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="status-metric">
                                        <h4>${r.message.active_companies || 0}</h4>
                                        <small>Active Companies</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="status-metric">
                                        <h4>${r.message.avg_confidence || 0}%</h4>
                                        <small>Avg. Confidence</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="status-metric">
                                        <h4 style="color: ${r.message.system_health >= 75 ? '#27ae60' : '#e74c3c'}">${r.message.system_health || 0}%</h4>
                                        <small>System Health</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    frm.dashboard.add_section(status_html, __("System Status"));
                    frm.status_added = true;
                }
            }
        });
    }
}

// Utility dialog functions
function show_bulk_forecast_results(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Bulk Forecast Results"),
        size: "large",
        fields: [{
            fieldtype: "HTML",
            fieldname: "results_html"
        }]
    });
    
    let results_html = `
        <div class="forecast-results">
            <h4>Forecast Generation Complete</h4>
            <table class="table table-bordered">
                <tr><td><strong>Total Forecasts Created:</strong></td><td>${data.total_created || 0}</td></tr>
                <tr><td><strong>Successful:</strong></td><td>${data.successful || 0}</td></tr>
                <tr><td><strong>Failed:</strong></td><td>${data.failed || 0}</td></tr>
                <tr><td><strong>Success Rate:</strong></td><td>${data.success_rate || 0}%</td></tr>
                <tr><td><strong>Average Confidence:</strong></td><td>${data.avg_confidence || 0}%</td></tr>
            </table>
        </div>
    `;
    
    dialog.fields_dict.results_html.$wrapper.html(results_html);
    dialog.show();
}

function show_forecast_results_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Forecast Results"),
        fields: [{
            fieldtype: "HTML",
            fieldname: "results_html"
        }]
    });
    
    let results_html = `
        <div class="forecast-results">
            <h4>Forecast Generation Results</h4>
            <p><strong>Status:</strong> ${data.status || 'Unknown'}</p>
            <p><strong>Forecasts Created:</strong> ${data.forecasts_created || 0}</p>
            <p><strong>Average Confidence:</strong> ${data.avg_confidence || 0}%</p>
            ${data.details ? `<p><strong>Details:</strong> ${data.details}</p>` : ''}
        </div>
    `;
    
    dialog.fields_dict.results_html.$wrapper.html(results_html);
    dialog.show();
}

function show_health_report_dialog(health_data) {
    let dialog = new frappe.ui.Dialog({
        title: __("System Health Report"),
        size: "large",
        fields: [{
            fieldtype: "HTML",
            fieldname: "health_html"
        }]
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
                    <h5>Performance Metrics</h5>
                    <ul>
                        <li>Total Forecasts: ${health_data.total_forecasts || 0}</li>
                        <li>Average Confidence: ${health_data.avg_confidence || 0}%</li>
                        <li>High Confidence Ratio: ${health_data.high_confidence_ratio || 0}%</li>
                        <li>Active Companies: ${health_data.active_companies || 0}</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h5>System Status</h5>
                    <ul>
                        <li>Model Performance: ${health_data.model_performance || 'N/A'}</li>
                        <li>Data Quality: ${health_data.data_quality || 'N/A'}</li>
                        <li>Integration Status: ${health_data.integration_status || 'N/A'}</li>
                        <li>Last Update: ${health_data.last_update || 'N/A'}</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.health_html.$wrapper.html(health_html);
    dialog.show();
}

function show_sync_results_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Sync Results"),
        fields: [{
            fieldtype: "HTML",
            fieldname: "sync_html"
        }]
    });
    
    let sync_html = `
        <div class="sync-results">
            <h4>Synchronization Complete</h4>
            <table class="table table-bordered">
                <tr><td><strong>Forecasts Synchronized:</strong></td><td>${data.synced_count || 0}</td></tr>
                <tr><td><strong>Updated Records:</strong></td><td>${data.updated_count || 0}</td></tr>
                <tr><td><strong>Errors:</strong></td><td>${data.error_count || 0}</td></tr>
                <tr><td><strong>Duration:</strong></td><td>${data.duration || 'N/A'}</td></tr>
            </table>
        </div>
    `;
    
    dialog.fields_dict.sync_html.$wrapper.html(sync_html);
    dialog.show();
}

function show_performance_report_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Model Performance Report"),
        size: "large",
        fields: [{
            fieldtype: "HTML",
            fieldname: "performance_html"
        }]
    });
    
    let performance_html = `
        <div class="performance-report">
            <h4>Model Performance Analysis</h4>
            <div class="row">
                <div class="col-md-6">
                    <h5>Accuracy Metrics</h5>
                    <table class="table table-bordered">
                        <tr><td>Overall Accuracy</td><td>${data.overall_accuracy || 'N/A'}</td></tr>
                        <tr><td>ARIMA Model</td><td>${data.arima_accuracy || 'N/A'}</td></tr>
                        <tr><td>Prophet Model</td><td>${data.prophet_accuracy || 'N/A'}</td></tr>
                        <tr><td>Ensemble Model</td><td>${data.ensemble_accuracy || 'N/A'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Usage Statistics</h5>
                    <table class="table table-bordered">
                        <tr><td>Most Used Model</td><td>${data.most_used_model || 'N/A'}</td></tr>
                        <tr><td>Best Performing</td><td>${data.best_performing || 'N/A'}</td></tr>
                        <tr><td>Recommendation</td><td>${data.recommendation || 'N/A'}</td></tr>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.performance_html.$wrapper.html(performance_html);
    dialog.show();
}

// ============================================================================
// FORECAST SYNCHRONIZATION FUNCTIONS
// ============================================================================

function sync_all_forecasts(frm) {
    frappe.confirm(
        __("Synchronize all AI Financial Forecasts with specific forecast types? This will update Cash Flow, Revenue, Expense, and Accuracy forecasts."),
        function() {
            frappe.show_alert({
                message: __("Starting forecast synchronization..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.forecasting.sync_manager.sync_all_forecasts",
                args: {
                    company: null, // Sync all companies
                    forecast_start_date: null // Sync all dates
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Forecast synchronization completed!"),
                            indicator: 'green'
                        });
                        
                        show_sync_results_dialog(r.message.results);
                    } else {
                        let error_msg = r.message ? r.message.error : "Unknown error occurred";
                        frappe.msgprint({
                            title: __("Sync Failed"),
                            message: `<div class="sync-error-details">
                                <p><strong>Error:</strong> ${error_msg}</p>
                                <p><strong>Suggestion:</strong> Check the browser console and server logs for detailed error information.</p>
                                <p><strong>Common fixes:</strong></p>
                                <ul>
                                    <li>Ensure all required fields are set in the AI Financial Forecasts</li>
                                    <li>Check that all target DocTypes are properly configured</li>
                                    <li>Verify database permissions</li>
                                </ul>
                            </div>`,
                            indicator: 'red'
                        });
                        
                        // Log detailed error to console for debugging
                        console.error("Sync failed:", r);
                    }
                },
                error: function(xhr, status, error) {
                    frappe.msgprint({
                        title: __("Network Error"),
                        message: `<div class="network-error-details">
                            <p><strong>Status:</strong> ${status}</p>
                            <p><strong>Error:</strong> ${error}</p>
                            <p>Please check your network connection and try again.</p>
                        </div>`,
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function check_sync_status(frm) {
    frappe.call({
        method: "ai_inventory.forecasting.sync_manager.get_sync_status",
        args: {
            company: null,
            days: 7
        },
        callback: function(r) {
            if (r.message && !r.message.error) {
                show_sync_status_dialog(r.message);
            } else {
                frappe.msgprint({
                    title: __("Error"),
                    message: r.message.error || __("Failed to fetch sync status"),
                    indicator: 'red'
                });
            }
        }
    });
}

function force_sync_specific_forecast(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Force Sync Specific Forecast"),
        fields: [
            {
                fieldtype: "Select",
                label: __("Forecast Type"),
                fieldname: "forecast_type",
                options: ["Cash Flow", "Revenue", "Expense"],
                reqd: 1
            },
            {
                fieldtype: "Link",
                label: __("Company"),
                fieldname: "company",
                options: "Company",
                reqd: 1
            },
            {
                fieldtype: "Date",
                label: __("Forecast Date"),
                fieldname: "forecast_date",
                reqd: 1,
                default: frappe.datetime.get_today()
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: "ai_inventory.forecasting.sync_manager.force_sync_specific_forecast",
                args: {
                    forecast_type: values.forecast_type,
                    company: values.company,
                    forecast_start_date: values.forecast_date
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        dialog.hide();
                    } else {
                        frappe.msgprint({
                            title: __("Sync Failed"),
                            message: r.message.error || __("Unknown error occurred"),
                            indicator: 'red'
                        });
                    }
                }
            });
        },
        primary_action_label: __("Force Sync")
    });
    
    dialog.show();
}

function show_sync_status_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Forecast Sync Status"),
        size: "large",
        fields: [{
            fieldtype: "HTML",
            fieldname: "sync_status_html"
        }]
    });
    
    let sync_rates_html = "";
    for (let type in data.sync_summary) {
        let summary = data.sync_summary[type];
        let rate_color = summary.sync_rate >= 90 ? "green" : summary.sync_rate >= 70 ? "orange" : "red";
        
        sync_rates_html += `
            <tr>
                <td>${type}</td>
                <td>${summary.financial}</td>
                <td>${summary.synced}</td>
                <td><span style="color: ${rate_color}; font-weight: bold;">${summary.sync_rate.toFixed(1)}%</span></td>
            </tr>
        `;
    }
    
    let sync_status_html = `
        <div class="sync-status">
            <h4>Forecast Synchronization Status (Last 7 Days)</h4>
            
            <div class="row">
                <div class="col-md-6">
                    <h5>Summary</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Financial Forecasts:</strong></td><td>${data.total_financial_forecasts}</td></tr>
                        <tr><td><strong>Accuracy Records:</strong></td><td>${data.accuracy_tracking}</td></tr>
                        <tr><td><strong>Last Sync:</strong></td><td>${data.last_sync_date || 'Never'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Sync Rates by Type</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Financial</th>
                                <th>Synced</th>
                                <th>Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${sync_rates_html}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="alert alert-info">
                <strong>Note:</strong> Sync rates below 90% may indicate sync issues. Use "Force Sync Specific" to manually sync individual forecasts.
            </div>
        </div>
    `;
    
    dialog.fields_dict.sync_status_html.$wrapper.html(sync_status_html);
    dialog.show();
}

function show_sync_results_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Sync Results"),
        size: "large",
        fields: [{
            fieldtype: "HTML",
            fieldname: "sync_results_html"
        }]
    });
    
    let results_by_type_html = "";
    for (let type in data.results_by_type) {
        let typeData = data.results_by_type[type];
        results_by_type_html += `
            <tr>
                <td>${type}</td>
                <td>${typeData.success}</td>
                <td>${typeData.errors}</td>
            </tr>
        `;
    }
    
    let error_details_html = "";
    if (data.error_details && data.error_details.length > 0) {
        error_details_html = `
            <h5>Error Details</h5>
            <table class="table table-bordered">
                <thead>
                    <tr><th>Forecast ID</th><th>Error</th></tr>
                </thead>
                <tbody>
        `;
        
        data.error_details.forEach(error => {
            error_details_html += `
                <tr>
                    <td>${error.forecast_id}</td>
                    <td>${error.error}</td>
                </tr>
            `;
        });
        
        error_details_html += "</tbody></table>";
    }
    
    let sync_results_html = `
        <div class="sync-results">
            <h4>Synchronization Results</h4>
            
            <div class="row">
                <div class="col-md-6">
                    <h5>Overall Summary</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Forecasts:</strong></td><td>${data.total_forecasts}</td></tr>
                        <tr><td><strong>Successfully Synced:</strong></td><td style="color: green;">${data.synced_successfully}</td></tr>
                        <tr><td><strong>Sync Errors:</strong></td><td style="color: red;">${data.sync_errors}</td></tr>
                        <tr><td><strong>Success Rate:</strong></td><td><strong>${((data.synced_successfully / data.total_forecasts) * 100).toFixed(1)}%</strong></td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Results by Type</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr><th>Type</th><th>Success</th><th>Errors</th></tr>
                        </thead>
                        <tbody>
                            ${results_by_type_html}
                        </tbody>
                    </table>
                </div>
            </div>
            
            ${error_details_html}
        </div>
    `;
    
    dialog.fields_dict.sync_results_html.$wrapper.html(sync_results_html);
    dialog.show();
}

// ============================================================================
// ACCURACY TRACKING FUNCTIONS
// ============================================================================

function generate_accuracy_tracking(frm) {
    frappe.confirm(
        __("Generate accuracy tracking records for all forecasts that don't have tracking? This will help monitor forecast performance."),
        function() {
            frappe.show_alert({
                message: __("Generating accuracy tracking records..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.generate_accuracy_tracking",
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __(`Accuracy tracking generation completed! Created ${r.message.tracking_created} records.`),
                            indicator: 'green'
                        });
                        
                        // Show detailed results
                        frappe.msgprint({
                            title: __("Accuracy Tracking Generation Results"),
                            message: `
                                <div class="accuracy-generation-results">
                                    <h4>Generation Summary</h4>
                                    <ul>
                                        <li><strong>Records Created:</strong> ${r.message.tracking_created}</li>
                                        <li><strong>Errors:</strong> ${r.message.errors}</li>
                                        <li><strong>Status:</strong> ${r.message.status}</li>
                                    </ul>
                                    <p>You can now view accuracy tracking records in the AI Forecast Accuracy DocType.</p>
                                </div>
                            `,
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __("Generation Failed"),
                            message: r.message.error || __("Unknown error occurred"),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function view_accuracy_summary(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Accuracy Summary Options"),
        fields: [
            {
                fieldtype: "Link",
                label: __("Company"),
                fieldname: "company",
                options: "Company"
            },
            {
                fieldtype: "Int",
                label: __("Days"),
                fieldname: "days",
                default: 30,
                description: __("Number of days to analyze")
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_accuracy_summary",
                args: {
                    company: values.company,
                    days: values.days
                },
                callback: function(r) {
                    if (r.message && !r.message.error) {
                        show_accuracy_summary_dialog(r.message);
                        dialog.hide();
                    } else {
                        frappe.msgprint({
                            title: __("Error"),
                            message: r.message.error || __("Failed to get accuracy summary"),
                            indicator: 'red'
                        });
                    }
                }
            });
        },
        primary_action_label: __("View Summary")
    });
    
    dialog.show();
}

function show_accuracy_summary_dialog(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Forecast Accuracy Summary"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "accuracy_summary_html"
            }
        ]
    });
    
    // Generate HTML for accuracy by type
    let accuracy_by_type_html = "";
    if (data.accuracy_by_type && Object.keys(data.accuracy_by_type).length > 0) {
        for (let [type, typeData] of Object.entries(data.accuracy_by_type)) {
            accuracy_by_type_html += `<tr>
                <td>${type}</td>
                <td>${typeData.count}</td>
                <td>${typeData.avg_accuracy.toFixed(1)}%</td>
            </tr>`;
        }
    } else {
        accuracy_by_type_html = "<tr><td colspan='3'>No data available</td></tr>";
    }
    
    // Generate HTML for top performing models
    let top_models_html = "";
    if (data.top_performing_models && data.top_performing_models.length > 0) {
        data.top_performing_models.slice(0, 5).forEach(model => {
            top_models_html += `<tr>
                <td>${model.model}</td>
                <td>${model.count}</td>
                <td>${model.avg_accuracy.toFixed(1)}%</td>
            </tr>`;
        });
    } else {
        top_models_html = "<tr><td colspan='3'>No data available</td></tr>";
    }
    
    // Generate HTML for performance distribution
    let performance_html = "";
    if (data.performance_distribution) {
        for (let [grade, count] of Object.entries(data.performance_distribution)) {
            performance_html += `<tr>
                <td>${grade}</td>
                <td>${count}</td>
            </tr>`;
        }
    }
    
    // Generate HTML for improvement areas
    let improvement_html = "";
    if (data.improvement_areas && data.improvement_areas.length > 0) {
        data.improvement_areas.forEach(area => {
            improvement_html += `<li>${area}</li>`;
        });
    } else {
        improvement_html = "<li>No specific improvement areas identified</li>";
    }
    
    let summary_html = `
        <div class="accuracy-summary">
            <div class="row">
                <div class="col-md-6">
                    <h4>Overall Summary</h4>
                    <table class="table table-bordered">
                        <tr><td><strong>Total Records:</strong></td><td>${data.total_accuracy_records}</td></tr>
                        <tr><td><strong>Average Accuracy:</strong></td><td><strong>${data.avg_accuracy.toFixed(1)}%</strong></td></tr>
                    </table>
                    
                    <h5>Accuracy by Forecast Type</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr><th>Type</th><th>Records</th><th>Avg Accuracy</th></tr>
                        </thead>
                        <tbody>
                            ${accuracy_by_type_html}
                        </tbody>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Performance Grade Distribution</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr><th>Grade</th><th>Count</th></tr>
                        </thead>
                        <tbody>
                            ${performance_html}
                        </tbody>
                    </table>
                    
                    <h5>Top Performing Models</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr><th>Model</th><th>Records</th><th>Avg Accuracy</th></tr>
                        </thead>
                        <tbody>
                            ${top_models_html}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <h5>Improvement Areas</h5>
                    <ul>
                        ${improvement_html}
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.accuracy_summary_html.$wrapper.html(summary_html);
    dialog.show();
}

function test_sync_functionality(frm) {
    frappe.confirm(
        __("Run sync debugging test? This will attempt to create one forecast of each type to identify issues."),
        function() {
            frappe.show_alert({
                message: __("Running sync test..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.sync_test_functions.test_sync_single_forecast",
                callback: function(r) {
                    if (r.message) {
                        show_sync_test_results(r.message);
                    } else {
                        frappe.msgprint({
                            title: __("Test Failed"),
                            message: __("Unable to run sync test. Check console for errors."),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function show_sync_test_results(data) {
    let dialog = new frappe.ui.Dialog({
        title: __("Sync Test Results"),
        size: "large",
        fields: [{
            fieldtype: "HTML",
            fieldname: "test_results_html"
        }]
    });
    
    let test_results_html = `
        <div class="sync-test-results">
            <h4>Sync Functionality Test</h4>
            <p><strong>Tested Forecast:</strong> ${data.forecast_tested || 'N/A'}</p>
            <p><strong>Forecast Type:</strong> ${data.forecast_type || 'N/A'}</p>
            <p><strong>Company:</strong> ${data.company || 'N/A'}</p>
            
            <h5>Test Results by DocType:</h5>
            <div class="test-results-details">
    `;
    
    if (data.test_results) {
        for (let [doctype, result] of Object.entries(data.test_results)) {
            let status_color = result.success ? "green" : "red";
            let status_text = result.success ? "SUCCESS" : "FAILED";
            
            test_results_html += `
                <div class="test-result-item">
                    <h6>${doctype.toUpperCase()} Forecast</h6>
                    <p><span style="color: ${status_color}; font-weight: bold;">${status_text}</span></p>
                    ${result.success ? 
                        `<p>Created: ${result.created_id}</p>` : 
                        `<p>Error: ${result.error}</p>`
                    }
                </div>
                <hr>
            `;
        }
    } else {
        test_results_html += `<p>No test results available.</p>`;
    }
    
    if (data.error) {
        test_results_html += `
            <div class="alert alert-danger">
                <strong>Test Error:</strong> ${data.error}
            </div>
        `;
    }
    
    test_results_html += `
            </div>
            <div class="alert alert-info">
                <strong>Note:</strong> This test creates sample forecast records to identify sync issues. 
                Use the results to troubleshoot the "No Label must be set first" error.
            </div>
        </div>
    `;
    
    dialog.fields_dict.test_results_html.$wrapper.html(test_results_html);
    dialog.show();
}

function update_forecast_accuracy(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("Update Forecast Accuracy"),
        fields: [
            {
                fieldtype: "Link",
                label: __("AI Financial Forecast"),
                fieldname: "forecast_reference",
                options: "AI Financial Forecast",
                reqd: 1
            },
            {
                fieldtype: "Currency",
                label: __("Actual Value"),
                fieldname: "actual_value",
                reqd: 1,
                description: __("Enter the actual value to compare against the forecast")
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.update_accuracy_with_actuals",
                args: {
                    forecast_reference: values.forecast_reference,
                    actual_value: values.actual_value
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Accuracy updated successfully!"),
                            indicator: 'green'
                        });
                        
                        frappe.msgprint({
                            title: __("Accuracy Update Results"),
                            message: `
                                <div class="accuracy-update-results">
                                    <h4>Updated Accuracy Metrics</h4>
                                    <ul>
                                        <li><strong>Accuracy Percentage:</strong> ${r.message.accuracy_percentage.toFixed(1)}%</li>
                                        <li><strong>Performance Grade:</strong> ${r.message.performance_grade}</li>
                                        <li><strong>Absolute Error:</strong> ${frappe.format(r.message.absolute_error, {fieldtype: "Currency"})}</li>
                                    </ul>
                                </div>
                            `,
                            indicator: 'green'
                        });
                        
                        dialog.hide();
                    } else {
                        frappe.msgprint({
                            title: __("Update Failed"),
                            message: r.message.error || __("Unknown error occurred"),
                            indicator: 'red'
                        });
                    }
                }
            });
        },
        primary_action_label: __("Update Accuracy")
    });
    
    dialog.show();
}
