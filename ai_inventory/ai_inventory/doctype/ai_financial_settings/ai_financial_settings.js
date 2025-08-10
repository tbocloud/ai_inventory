// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Financial Settings", {
    refresh(frm) {
    // Scope class for targeted CSS on this form
    frm.$wrapper.addClass('ai-financial-settings-form');

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
    // Enhanced Sync Management Section
    frm.add_custom_button(__("🔄 Master Sync All Forecasts"), function() {
        master_sync_all_forecasts(frm);
    }, __("🔧 Sync Management"));
    
    frm.add_custom_button(__("💰 Sync Cashflow Forecasts"), function() {
        sync_specific_forecast_type(frm, 'cashflow');
    }, __("🔧 Sync Management"));
    
    frm.add_custom_button(__("📈 Sync Revenue Forecasts"), function() {
        sync_specific_forecast_type(frm, 'revenue');
    }, __("🔧 Sync Management"));
    
    frm.add_custom_button(__("💸 Sync Expense Forecasts"), function() {
        sync_specific_forecast_type(frm, 'expense');
    }, __("🔧 Sync Management"));
    
    frm.add_custom_button(__("🎯 Sync Accuracy Records"), function() {
        sync_specific_forecast_type(frm, 'accuracy');
    }, __("🔧 Sync Management"));
    
    frm.add_custom_button(__("📊 Check Sync Status"), function() {
        check_comprehensive_sync_status(frm);
    }, __("🔧 Sync Management"));
    
    frm.add_custom_button(__("🔧 Force Rebuild All"), function() {
        force_rebuild_all_forecasts(frm);
    }, __("🔧 Sync Management"));
    
    // System Health Section
    frm.add_custom_button(__("🩺 System Health Check"), function() {
        run_comprehensive_health_check(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("↺ Backfill Cashflow (from Financial)"), function() {
        frappe.call({
            method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.backfill_cashflow_forecasts",
            args: { limit: 100 },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __("Backfill created ") + (r.message.created || 0) + __(" cashflow records"),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __("Backfill Failed"),
                        message: (r.message && r.message.error) || __("Unknown error"),
                        indicator: 'red'
                    });
                }
            }
        });
    }, __("System Management"));
    
    frm.add_custom_button(__("📋 Sync Queue Status"), function() {
        check_sync_queue_status(frm);
    }, __("System Management"));
    
    frm.add_custom_button(__("🗑️ Cleanup Old Data"), function() {
        cleanup_old_forecast_data(frm);
    }, __("System Management"));
    
    // Legacy Functions (keeping for compatibility)
    frm.add_custom_button(__("Sync to Inventory All Forecast"), function() {
        sync_all_to_inventory(frm);
    }, __("Legacy Sync"));
    
    frm.add_custom_button(__("Test Sync (Debug)"), function() {
        test_sync_functionality(frm);
    }, __("Legacy Sync"));
    
    // Enhanced Alert Management Section
    frm.add_custom_button(__("🚨 Check Financial Alerts"), function() {
        trigger_financial_alert_check(frm);
    }, __("🚨 Alert Management"));
    
    frm.add_custom_button(__("📊 View Alerts Dashboard"), function() {
        view_financial_alerts_dashboard(frm);
    }, __("🚨 Alert Management"));
    
    frm.add_custom_button(__("🗂️ Manage All Alerts"), function() {
        manage_ai_financial_alerts(frm);
    }, __("🚨 Alert Management"));
    
    frm.add_custom_button(__("🏗️ Create Alert DocType"), function() {
        create_financial_alert_doctype(frm);
    }, __("🚨 Alert Management"));
    
    frm.add_custom_button(__("⚙️ Setup AI Automation"), function() {
        setup_ai_financial_settings_automation(frm);
    }, __("🚨 Alert Management"));
    
    frm.add_custom_button(__("🔧 Cleanup Invalid Alert Links"), function() {
        frappe.call({
            method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.cleanup_invalid_forecast_references",
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __("Cleaned ") + (r.message.cleaned_count || 0) + __(" invalid forecast references"),
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __("Cleanup Failed"),
                        message: (r.message && r.message.error) || __("Unknown error"),
                        indicator: 'red'
                    });
                }
            }
        });
    }, __("🚨 Alert Management"));
    
    frm.add_custom_button(__("🔍 Debug Alert References"), function() {
        frappe.call({
            method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.debug_forecast_references",
            callback: function(r) {
                if (r.message && r.message.success) {
                    let debug_info = r.message.debug_info || [];
                    let message = `Found ${debug_info.length} alerts with forecast references:\n\n`;
                    debug_info.forEach(info => {
                        message += `Alert: ${info.alert_name}\n`;
                        message += `Forecast: ${info.related_forecast} (${info.forecast_exists ? 'EXISTS' : 'MISSING'})\n`;
                        message += `Title: ${info.alert_title}\n\n`;
                    });
                    
                    frappe.msgprint({
                        title: __("Debug: Alert References"),
                        message: message,
                        indicator: 'blue'
                    });
                } else {
                    frappe.msgprint({
                        title: __("Debug Failed"),
                        message: (r.message && r.message.error) || __("Unknown error"),
                        indicator: 'red'
                    });
                }
            }
        });
    }, __("🚨 Alert Management"));
    
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

function sync_all_to_inventory(frm) {
    frappe.confirm(
        "Sync all AI Financial Forecasts to inventory forecasts? This will create or update inventory predictions for all items based on all existing financial forecasts.",
        function() {
            frappe.show_alert({
                message: "Starting bulk inventory sync for all AI Financial Forecasts...",
                indicator: "blue"
            });
            
            frappe.call({
                method: "ai_inventory.forecasting.sync_manager.bulk_sync_to_inventory",
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: "All AI Financial Forecasts synced to inventory successfully!",
                            indicator: 'green'
                        });
                        
                        let msg = "Bulk inventory sync from AI Financial Forecasts completed successfully.";
                        if (r.message.total_processed) {
                            msg += " Processed " + r.message.total_processed + " AI Financial Forecasts.";
                        }
                        if (r.message.total_synced) {
                            msg += " Created/updated " + r.message.total_synced + " inventory forecasts.";
                        }
                        if (r.message.errors && r.message.errors.length > 0) {
                            msg += " Encountered " + r.message.errors.length + " errors.";
                        }
                        
                        frappe.msgprint({
                            title: "AI Financial Forecast to Inventory Sync Results",
                            message: msg,
                            indicator: "green"
                        });
                        
                        // Show detailed results if available
                        if (r.message.details) {
                            show_inventory_sync_details(r.message);
                        }
                    } else {
                        frappe.show_alert({
                            message: "AI Financial Forecast inventory sync failed: " + (r.message ? r.message.error : "Unknown error"),
                            indicator: 'red'
                        });
                        
                        frappe.msgprint({
                            title: "Sync Error",
                            message: "Bulk AI Financial Forecast to inventory sync failed. " + (r.message ? r.message.error : "Please check the error logs."),
                            indicator: "red"
                        });
                    }
                },
                error: function(r) {
                    frappe.show_alert({
                        message: "Request failed. Please try again.",
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function show_inventory_sync_details(sync_result) {
    let dialog = new frappe.ui.Dialog({
        title: "AI Financial Forecast to Inventory Sync Details",
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "sync_details"
            }
        ]
    });
    
    let html = "<div class='sync-results'>";
    html += "<h4>AI Financial Forecast to Inventory Sync Summary</h4>";
    html += "<p><strong>Total AI Financial Forecasts Processed:</strong> " + (sync_result.total_processed || 0) + "</p>";
    html += "<p><strong>Inventory Forecasts Created/Updated:</strong> " + (sync_result.total_synced || 0) + "</p>";
    html += "<p><strong>Errors:</strong> " + (sync_result.errors ? sync_result.errors.length : 0) + "</p>";
    
    if (sync_result.company_breakdown) {
        html += "<h4>By Company</h4>";
        for (let company in sync_result.company_breakdown) {
            let data = sync_result.company_breakdown[company];
            html += "<p><strong>" + company + ":</strong> " + data.synced + " inventory forecasts created from financial forecasts</p>";
        }
    }
    
    if (sync_result.errors && sync_result.errors.length > 0) {
        html += "<h4>Errors</h4>";
        html += "<ul>";
        sync_result.errors.forEach(function(error) {
            html += "<li>" + error + "</li>";
        });
        html += "</ul>";
    }
    
    html += "</div>";
    
    dialog.fields_dict.sync_details.$wrapper.html(html);
    dialog.show();
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

// ============================================================================
// COMPREHENSIVE SYNC MANAGEMENT FUNCTIONS
// ============================================================================

function check_comprehensive_sync_status(frm) {
    frappe.show_alert({
        message: __("Fetching comprehensive sync status..."),
        indicator: 'blue'
    });
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_comprehensive_sync_status",
        callback: function(r) {
            if (r.message && r.message.success) {
                show_comprehensive_sync_status_dialog(r.message);
            } else {
                frappe.msgprint({
                    title: __("❌ Sync Status Error"),
                    message: __("Failed to fetch comprehensive sync status: ") + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_comprehensive_sync_status_dialog(data) {
    let sync_html = `
        <div class="comprehensive-sync-status">
            <h3>🔄 Comprehensive Sync Status Report</h3>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <div class="status-summary">
                        <h5>📊 Overall Status</h5>
                        <p><strong>System Health:</strong> <span class="badge badge-${data.overall_health === 'Excellent' ? 'success' : data.overall_health === 'Good' ? 'warning' : 'danger'}">${data.overall_health}</span></p>
                        <p><strong>Last Sync:</strong> ${data.last_sync_time || 'Never'}</p>
                        <p><strong>Next Scheduled:</strong> ${data.next_scheduled_sync || 'Not scheduled'}</p>
                        <p><strong>Auto Sync:</strong> <span class="badge badge-${data.auto_sync_enabled ? 'success' : 'secondary'}">${data.auto_sync_enabled ? 'Enabled' : 'Disabled'}</span></p>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="sync-metrics">
                        <h5>📈 Sync Metrics</h5>
                        <p><strong>Total Forecasts:</strong> ${data.total_forecasts || 0}</p>
                        <p><strong>Synced Forecasts:</strong> ${data.synced_forecasts || 0}</p>
                        <p><strong>Pending Sync:</strong> <span style="color: ${data.pending_sync > 0 ? 'orange' : 'green'};">${data.pending_sync || 0}</span></p>
                        <p><strong>Failed Syncs:</strong> <span style="color: ${data.failed_syncs > 0 ? 'red' : 'green'};">${data.failed_syncs || 0}</span></p>
                    </div>
                </div>
            </div>
            
            <div class="forecast-types-status">
                <h5>📋 Forecast Types Status</h5>
                <div class="row">
    `;
    
    if (data.forecast_types) {
        Object.keys(data.forecast_types).forEach(type => {
            const forecast_data = data.forecast_types[type];
            sync_html += `
                <div class="col-md-4">
                    <div class="forecast-type-card" style="border: 1px solid #ddd; padding: 10px; margin: 5px; border-radius: 5px;">
                        <h6>${type} Forecasts</h6>
                        <p><strong>Total:</strong> ${forecast_data.total || 0}</p>
                        <p><strong>Synced:</strong> <span style="color: green;">${forecast_data.synced || 0}</span></p>
                        <p><strong>Pending:</strong> <span style="color: orange;">${forecast_data.pending || 0}</span></p>
                        <p><strong>Failed:</strong> <span style="color: red;">${forecast_data.failed || 0}</span></p>
                        <p><strong>Last Updated:</strong> ${forecast_data.last_updated || 'Never'}</p>
                    </div>
                </div>
            `;
        });
    }
    
    sync_html += `
                </div>
            </div>
            
            <div class="sync-queue-status mt-3">
                <h5>🔄 Sync Queue Status</h5>
                <p><strong>Queue Length:</strong> ${data.queue_length || 0}</p>
                <p><strong>Processing:</strong> ${data.currently_processing || 0}</p>
                <p><strong>Queue Health:</strong> <span class="badge badge-${data.queue_health === 'Good' ? 'success' : 'warning'}">${data.queue_health || 'Unknown'}</span></p>
            </div>
            
            <div class="recent-errors mt-3">
                <h5>⚠️ Recent Sync Errors</h5>
    `;
    
    if (data.recent_errors && data.recent_errors.length > 0) {
        sync_html += '<div class="error-list">';
        data.recent_errors.slice(0, 5).forEach(error => {
            sync_html += `
                <div class="error-item" style="background: #fff3cd; padding: 8px; margin: 5px 0; border-radius: 3px;">
                    <strong>${error.timestamp}:</strong> ${error.message}
                    <br><small>Forecast: ${error.forecast_type} - ${error.company}</small>
                </div>
            `;
        });
        sync_html += '</div>';
    } else {
        sync_html += '<p style="color: green;">✅ No recent sync errors</p>';
    }
    
    sync_html += `
            </div>
            
            <div class="action-buttons mt-4 text-center">
                <button class="btn btn-primary" onclick="force_sync_all_from_dialog()">🔄 Force Sync All</button>
                <button class="btn btn-warning" onclick="clear_sync_queue()">🗑️ Clear Queue</button>
                <button class="btn btn-info" onclick="refresh_sync_status()">🔄 Refresh Status</button>
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __("🔄 Comprehensive Sync Status"),
        size: 'extra-large',
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "sync_status_html",
                options: sync_html
            }
        ]
    });
    
    dialog.show();
}

function force_rebuild_all_forecasts(frm) {
    frappe.confirm(
        __("⚠️ WARNING: This will force rebuild ALL forecasts from scratch. This may take 15-30 minutes and will overwrite existing data. Continue?"),
        function() {
            frappe.show_alert({
                message: __("🔄 Starting comprehensive rebuild..."),
                indicator: 'orange'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.force_rebuild_all_forecasts",
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __(`✅ Rebuild completed! ${r.message.total_rebuilt || 0} forecasts rebuilt.`),
                            indicator: 'green'
                        });
                        
                        setTimeout(() => {
                            frm.reload_doc();
                        }, 2000);
                    } else {
                        frappe.show_alert({
                            message: __("❌ Rebuild failed: " + (r.message ? r.message.error : "Unknown error")),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function run_comprehensive_health_check(frm) {
    frappe.show_alert({
        message: __("🩺 Running comprehensive system health check..."),
        indicator: 'blue'
    });
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.run_system_health_check",
        callback: function(r) {
            if (r.message && r.message.success) {
                show_health_check_results_dialog(r.message);
            } else {
                frappe.msgprint({
                    title: __("❌ Health Check Error"),
                    message: __("Failed to complete health check: ") + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_health_check_results_dialog(data) {
    let health_html = `
        <div class="health-check-results">
            <h3>🩺 System Health Check Results</h3>
            
            <div class="overall-health mb-3">
                <h4>Overall Health: <span class="badge badge-${data.overall_score >= 80 ? 'success' : data.overall_score >= 60 ? 'warning' : 'danger'}">${data.overall_score}%</span></h4>
                <div class="progress">
                    <div class="progress-bar bg-${data.overall_score >= 80 ? 'success' : data.overall_score >= 60 ? 'warning' : 'danger'}" 
                         style="width: ${data.overall_score}%"></div>
                </div>
            </div>
            
            <div class="health-categories">
    `;
    
    const categories = [
        {key: 'database_health', name: '🗄️ Database Health', icon: '🗄️'},
        {key: 'sync_health', name: '🔄 Sync System Health', icon: '🔄'},
        {key: 'forecast_health', name: '📊 Forecast Health', icon: '📊'},
        {key: 'alert_health', name: '🚨 Alert System Health', icon: '🚨'},
        {key: 'api_health', name: '🔌 API Health', icon: '🔌'}
    ];
    
    categories.forEach(category => {
        const cat_data = data.categories && data.categories[category.key];
        if (cat_data) {
            health_html += `
                <div class="health-category" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h5>${category.icon} ${category.name}: <span class="badge badge-${cat_data.score >= 80 ? 'success' : cat_data.score >= 60 ? 'warning' : 'danger'}">${cat_data.score}%</span></h5>
                    
                    <div class="category-details">
            `;
            
            if (cat_data.checks && cat_data.checks.length > 0) {
                cat_data.checks.forEach(check => {
                    health_html += `
                        <div class="check-item" style="margin: 5px 0;">
                            <span class="${check.passed ? 'text-success' : 'text-danger'}">${check.passed ? '✅' : '❌'}</span>
                            <strong>${check.name}:</strong> ${check.message}
                        </div>
                    `;
                });
            }
            
            health_html += `
                    </div>
                </div>
            `;
        }
    });
    
    health_html += `
            </div>
            
            <div class="recommendations mt-3">
                <h5>💡 Recommendations</h5>
    `;
    
    if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(rec => {
            health_html += `
                <div class="recommendation" style="background: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 3px;">
                    <strong>${rec.priority === 'high' ? '🔴' : rec.priority === 'medium' ? '🟡' : '🟢'} ${rec.title}:</strong>
                    <p>${rec.description}</p>
                    ${rec.action ? `<button class="btn btn-sm btn-primary" onclick="${rec.action}">${rec.action_text || 'Take Action'}</button>` : ''}
                </div>
            `;
        });
    } else {
        health_html += '<p style="color: green;">✅ No specific recommendations - system is healthy!</p>';
    }
    
    health_html += `
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __("🩺 System Health Check Results"),
        size: 'large',
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "health_results_html",
                options: health_html
            }
        ]
    });
    
    dialog.show();
}

function check_sync_queue_status(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_sync_queue_status",
        callback: function(r) {
            if (r.message && r.message.success) {
                show_sync_queue_dialog(r.message);
            } else {
                frappe.msgprint({
                    title: __("❌ Queue Status Error"),
                    message: __("Failed to fetch sync queue status: ") + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_sync_queue_dialog(data) {
    let queue_html = `
        <div class="sync-queue-status">
            <h3>📋 Sync Queue Status</h3>
            
            <div class="queue-summary mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4>${data.total_in_queue || 0}</h4>
                            <p>Total in Queue</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4>${data.processing || 0}</h4>
                            <p>Currently Processing</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4>${data.completed_today || 0}</h4>
                            <p>Completed Today</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4>${data.failed_today || 0}</h4>
                            <p>Failed Today</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="queue-items">
                <h5>🔄 Items in Queue</h5>
    `;
    
    if (data.queue_items && data.queue_items.length > 0) {
        queue_html += '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>Forecast Type</th><th>Company</th><th>Priority</th><th>Added</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
        
        data.queue_items.forEach(item => {
            queue_html += `
                <tr>
                    <td>${item.forecast_type}</td>
                    <td>${item.company}</td>
                    <td><span class="badge badge-${item.priority === 'high' ? 'danger' : item.priority === 'medium' ? 'warning' : 'info'}">${item.priority}</span></td>
                    <td>${item.added_time}</td>
                    <td><span class="badge badge-${item.status === 'processing' ? 'warning' : item.status === 'pending' ? 'info' : 'secondary'}">${item.status}</span></td>
                    <td><button class="btn btn-sm btn-danger" onclick="remove_from_queue('${item.id}')">Remove</button></td>
                </tr>
            `;
        });
        
        queue_html += '</tbody></table></div>';
    } else {
        queue_html += '<p style="color: green;">✅ Queue is empty</p>';
    }
    
    queue_html += `
            </div>
            
            <div class="queue-actions mt-3 text-center">
                <button class="btn btn-warning" onclick="clear_sync_queue()">🗑️ Clear Queue</button>
                <button class="btn btn-primary" onclick="process_queue_now()">▶️ Process Queue Now</button>
                <button class="btn btn-info" onclick="refresh_queue_status()">🔄 Refresh</button>
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __("📋 Sync Queue Status"),
        size: 'large',
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "queue_status_html",
                options: queue_html
            }
        ]
    });
    
    dialog.show();
}

function cleanup_old_forecast_data(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __("🗑️ Cleanup Old Forecast Data"),
        fields: [
            {
                fieldtype: "Int",
                label: __("Days to Keep"),
                fieldname: "days_to_keep",
                reqd: 1,
                default: 90,
                description: "Delete forecast data older than this many days"
            },
            {
                fieldtype: "Check",
                label: __("Include Legacy Syncs"),
                fieldname: "include_legacy_syncs",
                default: 1,
                description: "Also cleanup legacy sync records"
            },
            {
                fieldtype: "Check",
                label: __("Include Error Logs"),
                fieldname: "include_error_logs",
                default: 1,
                description: "Cleanup old error logs"
            },
            {
                fieldtype: "Check",
                label: __("Dry Run (Preview Only)"),
                fieldname: "dry_run",
                default: 1,
                description: "Preview what will be deleted without actually deleting"
            }
        ],
        primary_action: function(values) {
            frappe.show_alert({
                message: __("🗑️ Starting cleanup process..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.cleanup_old_data",
                args: values,
                callback: function(r) {
                    if (r.message && r.message.success) {
                        show_cleanup_results_dialog(r.message, values.dry_run);
                    } else {
                        frappe.show_alert({
                            message: __("❌ Cleanup failed: " + (r.message ? r.message.error : "Unknown error")),
                            indicator: 'red'
                        });
                    }
                }
            });
            
            dialog.hide();
        },
        primary_action_label: __("Start Cleanup")
    });
    
    dialog.show();
}

function show_cleanup_results_dialog(data, is_dry_run) {
    let cleanup_html = `
        <div class="cleanup-results">
            <h3>🗑️ Cleanup Results ${is_dry_run ? '(Preview)' : '(Completed)'}</h3>
            
            <div class="cleanup-summary">
                <div class="row">
                    <div class="col-md-4">
                        <div class="cleanup-stat" style="text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4>${data.total_deleted || 0}</h4>
                            <p>Total Records ${is_dry_run ? 'to Delete' : 'Deleted'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="cleanup-stat" style="text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4>${data.space_freed || '0 MB'}</h4>
                            <p>Space ${is_dry_run ? 'to Free' : 'Freed'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="cleanup-stat" style="text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4>${data.processing_time || '0s'}</h4>
                            <p>Processing Time</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="cleanup-details mt-3">
                <h5>📋 Cleanup Details</h5>
    `;
    
    if (data.details && data.details.length > 0) {
        cleanup_html += '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>DocType</th><th>Records ${is_dry_run ? "to Delete" : "Deleted"}</th><th>Date Range</th></tr></thead><tbody>';
        
        data.details.forEach(detail => {
            cleanup_html += `
                <tr>
                    <td>${detail.doctype}</td>
                    <td>${detail.count}</td>
                    <td>${detail.date_range}</td>
                </tr>
            `;
        });
        
        cleanup_html += '</tbody></table></div>';
    }
    
    if (is_dry_run) {
        cleanup_html += `
            <div class="text-center mt-3">
                <button class="btn btn-danger" onclick="execute_actual_cleanup()">🗑️ Execute Actual Cleanup</button>
            </div>
        `;
    }
    
    cleanup_html += '</div>';
    
    let dialog = new frappe.ui.Dialog({
        title: __(`🗑️ Cleanup Results ${is_dry_run ? '(Preview)' : '(Completed)'}`),
        size: 'large',
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "cleanup_results_html",
                options: cleanup_html
            }
        ]
    });
    
    dialog.show();
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

// ===== ENHANCED SYNC MANAGEMENT FUNCTIONS =====

function master_sync_all_forecasts(frm) {
    frappe.confirm(
        __(`🔄 Master Sync All Forecasts
        
This will perform a comprehensive synchronization of ALL forecast types:
• AI Cashflow Forecasts → AI Financial Forecast
• AI Revenue Forecasts → AI Financial Forecast  
• AI Expense Forecasts → AI Financial Forecast
• AI Forecast Accuracy Records → Update accuracy data

This process may take several minutes. Continue?`),
        function() {
            show_master_sync_progress(frm);
        }
    );
}

function show_master_sync_progress(frm) {
    let progress_dialog = new frappe.ui.Dialog({
        title: __("🔄 Master Sync Progress"),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'progress_html'
            }
        ]
    });
    
    let progress_html = `
        <div class="master-sync-progress">
            <h4>🔄 Master Sync in Progress</h4>
            <div class="progress-steps">
                <div id="step-1" class="progress-step">
                    <span class="step-icon">⏳</span> Step 1: Syncing Cashflow Forecasts...
                </div>
                <div id="step-2" class="progress-step">
                    <span class="step-icon">⏳</span> Step 2: Syncing Revenue Forecasts...
                </div>
                <div id="step-3" class="progress-step">
                    <span class="step-icon">⏳</span> Step 3: Syncing Expense Forecasts...
                </div>
                <div id="step-4" class="progress-step">
                    <span class="step-icon">⏳</span> Step 4: Syncing Accuracy Records...
                </div>
                <div id="step-5" class="progress-step">
                    <span class="step-icon">⏳</span> Step 5: Final Validation...
                </div>
            </div>
            <div id="progress-results" class="progress-results" style="display: none;">
                <h5>📊 Sync Results</h5>
                <div id="results-content"></div>
            </div>
        </div>
        
        <style>
        .progress-step {
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #ddd;
            padding-left: 15px;
        }
        .progress-step.running {
            border-left-color: #007bff;
            background-color: #f8f9fa;
        }
        .progress-step.completed {
            border-left-color: #28a745;
            background-color: #d4edda;
        }
        .progress-step.error {
            border-left-color: #dc3545;
            background-color: #f8d7da;
        }
        </style>
    `;
    
    progress_dialog.fields_dict.progress_html.$wrapper.html(progress_html);
    progress_dialog.show();
    
    // Start the sync process
    execute_master_sync_steps(progress_dialog);
}

function execute_master_sync_steps(dialog) {
    let steps = [
        { id: 'step-1', type: 'cashflow', name: 'Cashflow Forecasts' },
        { id: 'step-2', type: 'revenue', name: 'Revenue Forecasts' },
        { id: 'step-3', type: 'expense', name: 'Expense Forecasts' },
        { id: 'step-4', type: 'accuracy', name: 'Accuracy Records' },
        { id: 'step-5', type: 'validation', name: 'Final Validation' }
    ];
    
    let results = [];
    
    function processStep(index) {
        if (index >= steps.length) {
            showFinalResults(dialog, results);
            return;
        }
        
        let step = steps[index];
        
        // Update UI
        dialog.$wrapper.find(`#${step.id}`).addClass('running');
        dialog.$wrapper.find(`#${step.id} .step-icon`).text('🔄');
        
        // Call sync function
        frappe.call({
            method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.master_sync_forecast_type",
            args: {
                forecast_type: step.type
            },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    dialog.$wrapper.find(`#${step.id}`).removeClass('running').addClass('completed');
                    dialog.$wrapper.find(`#${step.id} .step-icon`).text('✅');
                    results.push({
                        step: step.name,
                        status: 'success',
                        data: r.message
                    });
                } else {
                    dialog.$wrapper.find(`#${step.id}`).removeClass('running').addClass('error');
                    dialog.$wrapper.find(`#${step.id} .step-icon`).text('❌');
                    results.push({
                        step: step.name,
                        status: 'error',
                        message: r.message ? r.message.message : 'Unknown error'
                    });
                }
                
                // Process next step
                setTimeout(() => processStep(index + 1), 1000);
            }
        });
    }
    
    processStep(0);
}

function showFinalResults(dialog, results) {
    let results_html = '<table class="table table-striped"><thead><tr><th>Step</th><th>Status</th><th>Details</th></tr></thead><tbody>';
    
    results.forEach(function(result) {
        let status_icon = result.status === 'success' ? '✅' : '❌';
        let details = result.status === 'success' ? 
            `Synced: ${result.data.synced_count || 0} records` : 
            result.message;
            
        results_html += `
            <tr>
                <td>${result.step}</td>
                <td>${status_icon} ${result.status}</td>
                <td>${details}</td>
            </tr>
        `;
    });
    
    results_html += '</tbody></table>';
    
    dialog.$wrapper.find('#progress-results').show();
    dialog.$wrapper.find('#results-content').html(results_html);
    
    // Show summary alert
    let success_count = results.filter(r => r.status === 'success').length;
    let error_count = results.filter(r => r.status === 'error').length;
    
    frappe.show_alert({
        message: __(`Master Sync Complete: ${success_count} successful, ${error_count} errors`),
        indicator: error_count === 0 ? 'green' : 'orange'
    });
}

function sync_specific_forecast_type(frm, forecast_type) {
    let type_names = {
        'cashflow': '💰 Cashflow Forecasts',
        'revenue': '📈 Revenue Forecasts', 
        'expense': '💸 Expense Forecasts',
        'accuracy': '🎯 Accuracy Records'
    };
    
    frappe.confirm(
        __(`Sync ${type_names[forecast_type]}?
        
This will synchronize all ${type_names[forecast_type]} with the AI Financial Forecast system.`),
        function() {
            frappe.show_alert({
                message: __(`Starting sync for ${type_names[forecast_type]}...`),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.master_sync_forecast_type",
                args: {
                    forecast_type: forecast_type
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __(`${type_names[forecast_type]} synced successfully! Processed: ${r.message.synced_count} records`),
                            indicator: 'green'
                        });
                        
                        show_sync_type_results(type_names[forecast_type], r.message);
                    } else {
                        frappe.msgprint({
                            title: __("Sync Error"),
                            message: r.message ? r.message.message : __("Unknown error occurred"),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

// ============================================================================
// AI Financial Alert Management Functions
// ============================================================================

function trigger_financial_alert_check(frm) {
    frappe.confirm(
        __("Manually trigger financial alert check? This will scan all forecasts for potential issues."),
        function() {
            frappe.show_alert({
                message: __("Checking for financial alerts..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.trigger_alert_check",
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __(`Alert check completed. ${r.message.alerts_created || 0} new alerts created.`),
                            indicator: 'green'
                        });
                        
                        if (r.message.alerts_created > 0) {
                            frappe.set_route("List", "AI Financial Alert");
                        }
                    } else {
                        frappe.show_alert({
                            message: __("Alert check failed: " + (r.message ? r.message.error : "Unknown error")),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function view_financial_alerts_dashboard(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_financial_alerts_dashboard",
        callback: function(r) {
            if (r.message && r.message.success) {
                show_alerts_dashboard(r.message);
            } else {
                frappe.msgprint({
                    title: __("Error"),
                    message: __("Failed to load alerts dashboard: ") + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

// ============================================================================
// ENHANCED ALERT MANAGEMENT FUNCTIONS
// ============================================================================

function create_financial_alert_doctype(frm) {
    frappe.confirm(
        __("Create AI Financial Alert DocType? This will set up the alert system structure."),
        function() {
            frappe.show_alert({
                message: __("🏗️ Creating AI Financial Alert DocType..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.create_alert_doctype",
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("✅ AI Financial Alert DocType created successfully!"),
                            indicator: 'green'
                        });
                        
                        setTimeout(() => {
                            frappe.set_route("Form", "DocType", "AI Financial Alert");
                        }, 2000);
                    } else {
                        frappe.show_alert({
                            message: __("❌ Failed to create DocType: " + (r.message ? r.message.error : "Unknown error")),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function setup_ai_financial_settings_automation(frm) {
    frappe.confirm(
        __("Setup automated financial forecasting based on sync frequency? This will configure scheduled tasks."),
        function() {
            frappe.show_alert({
                message: __("⚙️ Setting up automation..."),
                indicator: 'blue'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.setup_automation",
                args: {
                    sync_frequency: frm.doc.sync_frequency || 'Daily',
                    enable_alerts: true,
                    enable_auto_sync: frm.doc.auto_sync_enabled || false
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("✅ Automation setup completed!"),
                            indicator: 'green'
                        });
                        
                        show_automation_setup_results(r.message);
                    } else {
                        frappe.show_alert({
                            message: __("❌ Automation setup failed: " + (r.message ? r.message.error : "Unknown error")),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function show_automation_setup_results(data) {
    let automation_html = `
        <div class="automation-setup-results">
            <h3>⚙️ Automation Setup Results</h3>
            
            <div class="setup-summary">
                <h5>📋 Configuration Summary</h5>
                <p><strong>Sync Frequency:</strong> ${data.sync_frequency}</p>
                <p><strong>Auto Sync Enabled:</strong> <span class="badge badge-${data.auto_sync_enabled ? 'success' : 'secondary'}">${data.auto_sync_enabled ? 'Yes' : 'No'}</span></p>
                <p><strong>Alert System:</strong> <span class="badge badge-${data.alerts_enabled ? 'success' : 'secondary'}">${data.alerts_enabled ? 'Enabled' : 'Disabled'}</span></p>
                <p><strong>Next Scheduled Run:</strong> ${data.next_run_time}</p>
            </div>
            
            <div class="scheduled-tasks">
                <h5>🕐 Scheduled Tasks Created</h5>
    `;
    
    if (data.scheduled_tasks && data.scheduled_tasks.length > 0) {
        automation_html += '<ul>';
        data.scheduled_tasks.forEach(task => {
            automation_html += `<li><strong>${task.name}:</strong> ${task.description} (Frequency: ${task.frequency})</li>`;
        });
        automation_html += '</ul>';
    } else {
        automation_html += '<p>No scheduled tasks were created.</p>';
    }
    
    automation_html += `
            </div>
            
            <div class="automation-features">
                <h5>🚀 Enabled Features</h5>
                <div class="row">
                    <div class="col-md-6">
                        <div class="feature-card" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h6>🔄 Automatic Sync</h6>
                            <p>Forecasts will automatically sync based on the configured frequency.</p>
                            <p><strong>Status:</strong> <span class="badge badge-${data.auto_sync_enabled ? 'success' : 'secondary'}">${data.auto_sync_enabled ? 'Active' : 'Inactive'}</span></p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="feature-card" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h6>🚨 Alert Monitoring</h6>
                            <p>System will automatically monitor for financial anomalies and create alerts.</p>
                            <p><strong>Status:</strong> <span class="badge badge-${data.alerts_enabled ? 'success' : 'secondary'}">${data.alerts_enabled ? 'Active' : 'Inactive'}</span></p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="next-steps mt-3">
                <h5>📝 Next Steps</h5>
                <ul>
                    <li>Monitor the system status dashboard for sync progress</li>
                    <li>Check the AI Financial Alert list for any alerts</li>
                    <li>Review sync logs in the System Management section</li>
                    <li>Adjust sync frequency if needed based on performance</li>
                </ul>
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __("⚙️ Automation Setup Results"),
        size: 'large',
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "automation_results_html",
                options: automation_html
            }
        ]
    });
    
    dialog.show();
}

function manage_ai_financial_alerts(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.get_all_financial_alerts",
        callback: function(r) {
            if (r.message && r.message.success) {
                show_financial_alerts_management_dialog(r.message);
            } else {
                frappe.msgprint({
                    title: __("❌ Alert Management Error"),
                    message: __("Failed to load financial alerts: ") + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_financial_alerts_management_dialog(data) {
    let alerts_html = `
        <div class="financial-alerts-management">
            <h3>🚨 Financial Alerts Management</h3>
            
            <div class="alerts-summary mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <div class="alert-stat text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4 style="color: red;">${data.critical_alerts || 0}</h4>
                            <p>Critical Alerts</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="alert-stat text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4 style="color: orange;">${data.high_alerts || 0}</h4>
                            <p>High Priority</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="alert-stat text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4 style="color: yellow;">${data.medium_alerts || 0}</h4>
                            <p>Medium Priority</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="alert-stat text-center" style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                            <h4 style="color: green;">${data.resolved_alerts || 0}</h4>
                            <p>Resolved</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="active-alerts">
                <h5>⚠️ Active Alerts</h5>
    `;
    
    if (data.active_alerts && data.active_alerts.length > 0) {
        alerts_html += '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>Priority</th><th>Type</th><th>Message</th><th>Company</th><th>Created</th><th>Actions</th></tr></thead><tbody>';
        
        data.active_alerts.forEach(alert => {
            alerts_html += `
                <tr>
                    <td><span class="badge badge-${alert.priority === 'Critical' ? 'danger' : alert.priority === 'High' ? 'warning' : 'info'}">${alert.priority}</span></td>
                    <td>${alert.alert_type}</td>
                    <td>${alert.alert_message || alert.alert_title || 'No details available'}</td>
                    <td>${alert.company || 'N/A'}</td>
                    <td>${frappe.datetime.prettyDate(alert.creation)}</td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="resolve_alert('${alert.name}')">Resolve</button>
                        <button class="btn btn-sm btn-info" onclick="view_alert_details('${alert.name}')">Details</button>
                    </td>
                </tr>
            `;
        });
        
        alerts_html += '</tbody></table></div>';
    } else {
        alerts_html += '<p style="color: green;">✅ No active alerts</p>';
    }
    
    alerts_html += `
            </div>
            
            <div class="alert-actions mt-3 text-center">
                <button class="btn btn-primary" onclick="create_manual_alert()">➕ Create Manual Alert</button>
                <button class="btn btn-warning" onclick="bulk_resolve_alerts()">✅ Bulk Resolve</button>
                <button class="btn btn-info" onclick="export_alerts_report()">📊 Export Report</button>
                <button class="btn btn-secondary" onclick="configure_alert_rules()">⚙️ Configure Rules</button>
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __("🚨 Financial Alerts Management"),
        size: 'extra-large',
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "alerts_management_html", 
                options: alerts_html
            }
        ]
    });
    
    dialog.show();
}

function show_alerts_dashboard(data) {
    let alert_html = `
        <div class="alerts-dashboard">
            <h4>📊 Financial Alerts Dashboard</h4>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="alert-summary-box">
                        <h5>🚨 Alert Summary</h5>
                        <p><strong>Total Active:</strong> ${data.total_active}</p>
                        <p><strong>Critical:</strong> <span style="color: red;">${data.critical_count}</span></p>
                        <p><strong>High Priority:</strong> <span style="color: orange;">${data.high_count}</span></p>
                    </div>
                </div>
                
                <div class="col-md-8">
                    <div class="active-alerts-box">
                        <h5>⚠️ Recent Active Alerts</h5>
                        <div class="alert-list">
    `;
    
    if (data.active_alerts && data.active_alerts.length > 0) {
        data.active_alerts.slice(0, 5).forEach(alert => {
            let priority_color = alert.priority === 'Critical' ? 'red' : 
                               alert.priority === 'High' ? 'orange' : 
                               alert.priority === 'Medium' ? 'blue' : 'gray';
            
            alert_html += `
                <div class="alert-item" style="border-left: 4px solid ${priority_color}; padding: 8px; margin: 5px 0;">
                    <strong>${alert.alert_title}</strong> 
                    <span class="badge" style="background-color: ${priority_color}; color: white;">${alert.priority}</span>
                    <br>
                    <small>${alert.company} | ${alert.alert_type} | ${alert.alert_date}</small>
                    <br>
                    <a href="/app/ai-financial-alert/${alert.name}" target="_blank">View Details</a>
                </div>
            `;
        });
    } else {
        alert_html += '<p>No active alerts found.</p>';
    }
    
    alert_html += `
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row" style="margin-top: 20px;">
                <div class="col-md-12">
                    <a href="/app/ai-financial-alert" class="btn btn-primary" target="_blank">
                        View All Alerts
                    </a>
                    <button class="btn btn-secondary" onclick="frappe.call({
                        method: 'ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.trigger_alert_check',
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frappe.show_alert('Alert check triggered', 'green');
                                setTimeout(() => location.reload(), 2000);
                            }
                        }
                    })">
                        🔄 Refresh Alerts
                    </button>
                </div>
            </div>
        </div>
        
        <style>
            .alerts-dashboard {
                padding: 15px;
            }
            .alert-summary-box, .active-alerts-box {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                background-color: #f9f9f9;
            }
            .alert-item {
                background-color: white;
                border-radius: 4px;
                margin: 8px 0;
            }
            .badge {
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.8em;
            }
        </style>
    `;
    
    frappe.msgprint({
        title: __("Financial Alerts Dashboard"),
        message: alert_html,
        wide: true
    });
}

// ============================================================================
// AI Financial Alert Management Functions
// Enhanced functionality for AI Financial Alert system
// ============================================================================

// Test function to create sample alerts for demonstration
function create_sample_financial_alert() {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.create_financial_alert",
        args: {
            alert_data: {
                company: "TBO Cloud",
                title: "Sample Low Balance Alert",
                message: "Cash flow forecast indicates potential low balance in next 7 days",
                priority: "High",
                alert_type: "Cash Flow Warning",
                threshold_value: 10000,
                actual_value: 8500,
                forecast_type: "Cash Flow",
                confidence_level: 85,
                recommended_action: "Review upcoming expenses and consider increasing cash reserves"
            }
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: `Sample alert created: ${r.message.alert_id}`,
                    indicator: 'green'
                });
                frappe.set_route("Form", "AI Financial Alert", r.message.alert_id);
            } else {
                frappe.show_alert({
                    message: "Failed to create sample alert: " + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

// Function to resolve an alert
function resolve_financial_alert(alert_id, action_taken, action_result) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.resolve_alert",
        args: {
            alert_id: alert_id,
            action_taken: action_taken,
            action_result: action_result
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: "Alert resolved successfully",
                    indicator: 'green'
                });
                location.reload();
            } else {
                frappe.show_alert({
                    message: "Failed to resolve alert: " + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

// Function to get alert statistics
function get_alert_statistics() {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.get_active_alerts",
        callback: function(r) {
            if (r.message && r.message.success) {
                let alerts = r.message.alerts;
                let stats = {
                    total: alerts.length,
                    critical: alerts.filter(a => a.priority === 'Critical').length,
                    high: alerts.filter(a => a.priority === 'High').length,
                    medium: alerts.filter(a => a.priority === 'Medium').length,
                    low: alerts.filter(a => a.priority === 'Low').length
                };
                
                console.log("Alert Statistics:", stats);
                return stats;
            }
        }
    });
}

// Function to create alert from forecast check
function create_alert_from_forecast_check(forecast_name) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_forecast.ai_financial_forecast.check_balance_alerts",
        args: {
            forecast_name: forecast_name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                if (r.message.alert_records_created && r.message.alert_records_created.length > 0) {
                    frappe.show_alert({
                        message: `${r.message.alert_records_created.length} alert(s) created from forecast check`,
                        indicator: 'orange'
                    });
                } else {
                    frappe.show_alert({
                        message: "No alerts needed - forecast looks good",
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

// Add alert management to form toolbar
frappe.ui.form.on('AI Financial Alert', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open' || frm.doc.status === 'Investigating') {
            frm.add_custom_button(__('Mark as Resolved'), function() {
                frappe.prompt([
                    {
                        fieldtype: 'Small Text',
                        fieldname: 'action_taken',
                        label: 'Action Taken',
                        reqd: 1
                    },
                    {
                        fieldtype: 'Small Text',
                        fieldname: 'action_result',
                        label: 'Result/Outcome'
                    }
                ], function(values) {
                    resolve_financial_alert(frm.doc.name, values.action_taken, values.action_result);
                }, __('Resolve Alert'));
            });
        }
        
        if (frm.doc.related_forecast) {
            frm.add_custom_button(__('View Related Forecast'), function() {
                frappe.set_route("Form", "AI Financial Forecast", frm.doc.related_forecast);
            });
        }
        
        frm.add_custom_button(__('Create Sample Alert'), function() {
            create_sample_financial_alert();
        });
    }
});

// Realtime notifications for new alerts
frappe.realtime.on('new_financial_alert', function(data) {
    if (data.priority === 'Critical' || data.priority === 'High') {
        frappe.show_alert({
            message: `🚨 New ${data.priority} Alert: ${data.title}`,
            indicator: data.priority === 'Critical' ? 'red' : 'orange'
        });
        
        // Show desktop notification if supported
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`AI Financial Alert - ${data.priority}`, {
                body: data.message,
                icon: '/assets/ai_inventory/images/alert-icon.png'
            });
        }
    }
});

// Request notification permission on page load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// ============================================================================
// UTILITY FUNCTIONS FOR DIALOGS
// ============================================================================

function force_sync_all_from_dialog() {
    frappe.show_alert({
        message: __("🔄 Starting force sync for all forecasts..."),
        indicator: 'blue'
    });
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.force_sync_all_forecasts",
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("✅ Force sync completed successfully!"),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __("❌ Force sync failed"),
                    indicator: 'red'
                });
            }
        }
    });
}

function clear_sync_queue() {
    frappe.confirm(
        __("Clear the entire sync queue? This will remove all pending sync operations."),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.clear_sync_queue",
                callback: function(r) {
                    frappe.show_alert({
                        message: r.message && r.message.success ? __("✅ Sync queue cleared") : __("❌ Failed to clear queue"),
                        indicator: r.message && r.message.success ? 'green' : 'red'
                    });
                }
            });
        }
    );
}

function refresh_sync_status() {
    frappe.show_alert({
        message: __("🔄 Refreshing sync status..."),
        indicator: 'blue'
    });
    
    // Close current dialog and reopen with fresh data
    $('.modal').modal('hide');
    setTimeout(() => {
        check_comprehensive_sync_status({});
    }, 500);
}

function refresh_queue_status() {
    frappe.show_alert({
        message: __("🔄 Refreshing queue status..."),
        indicator: 'blue'
    });
    
    $('.modal').modal('hide');
    setTimeout(() => {
        check_sync_queue_status({});
    }, 500);
}

function process_queue_now() {
    frappe.confirm(
        __("Process the sync queue immediately? This will start processing all pending sync operations."),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.process_sync_queue",
                callback: function(r) {
                    frappe.show_alert({
                        message: r.message && r.message.success ? __("✅ Queue processing started") : __("❌ Failed to process queue"),
                        indicator: r.message && r.message.success ? 'green' : 'red'
                    });
                }
            });
        }
    );
}

function remove_from_queue(item_id) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.remove_from_sync_queue",
        args: { item_id: item_id },
        callback: function(r) {
            frappe.show_alert({
                message: r.message && r.message.success ? __("✅ Item removed from queue") : __("❌ Failed to remove item"),
                indicator: r.message && r.message.success ? 'green' : 'red'
            });
            
            if (r.message && r.message.success) {
                refresh_queue_status();
            }
        }
    });
}

function execute_actual_cleanup() {
    frappe.confirm(
        __("Execute the actual cleanup? This will permanently delete the identified old data."),
        function() {
            frappe.show_alert({
                message: __("🗑️ Executing cleanup..."),
                indicator: 'orange'
            });
            
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.cleanup_old_data",
                args: { dry_run: false },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("✅ Cleanup completed successfully!"),
                            indicator: 'green'
                        });
                        show_cleanup_results_dialog(r.message, false);
                    } else {
                        frappe.show_alert({
                            message: __("❌ Cleanup failed"),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function resolve_alert(alert_name) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.resolve_alert",
        args: { alert_name: alert_name },
        callback: function(r) {
            frappe.show_alert({
                message: r.message && r.message.success ? __("✅ Alert resolved") : __("❌ Failed to resolve alert"),
                indicator: r.message && r.message.success ? 'green' : 'red'
            });
            
            if (r.message && r.message.success) {
                $('.modal').modal('hide');
                setTimeout(() => {
                    manage_ai_financial_alerts({});
                }, 500);
            }
        }
    });
}

function view_alert_details(alert_name) {
    frappe.set_route("Form", "AI Financial Alert", alert_name);
}

function create_manual_alert() {
    frappe.new_doc("AI Financial Alert");
}

function bulk_resolve_alerts() {
    frappe.confirm(
        __("Resolve all active alerts? This action cannot be undone."),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.bulk_resolve_alerts",
                callback: function(r) {
                    frappe.show_alert({
                        message: r.message && r.message.success ? __(`✅ ${r.message.resolved_count || 0} alerts resolved`) : __("❌ Failed to resolve alerts"),
                        indicator: r.message && r.message.success ? 'green' : 'red'
                    });
                }
            });
        }
    );
}

function export_alerts_report() {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_settings.ai_financial_settings.export_alerts_report",
        callback: function(r) {
            if (r.message && r.message.success) {
                window.open(r.message.file_url, '_blank');
            } else {
                frappe.show_alert({
                    message: __("❌ Failed to export report"),
                    indicator: 'red'
                });
            }
        }
    });
}

function configure_alert_rules() {
    frappe.set_route("List", "AI Financial Alert Rule");
}
