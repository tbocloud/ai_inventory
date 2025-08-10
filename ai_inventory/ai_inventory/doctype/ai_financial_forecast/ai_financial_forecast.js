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
        
        // Set company default currency if not set
        if (frm.doc.company && !frm.doc.currency) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Company",
                    fieldname: "default_currency",
                    filters: {"name": frm.doc.company}
                },
                callback: function(r) {
                    if (r.message && r.message.default_currency) {
                        frm.set_value("currency", r.message.default_currency);
                    }
                }
            });
        }
    },
    
    account: function(frm) {
        if (frm.doc.account) {
            // Auto-populate account details and currency
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
                        
                        // Set account currency if available and not already set
                        if (r.message.account_currency && !frm.doc.currency) {
                            frm.set_value("currency", r.message.account_currency);
                        }
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
        // Forecast Analysis Button
        frm.add_custom_button(__("Generate Analytics"), function() {
            load_forecast_dashboard(frm);
        }, __("Actions"));
        
        // Manual Sync Button
        frm.add_custom_button(__("Sync Now"), function() {
            trigger_manual_sync(frm);
        }, __("Integration"));
        
        // Sync Details Button
        frm.add_custom_button(__("Sync Details"), function() {
            show_sync_details(frm);
        }, __("Integration"));
        
        // Inventory Sync Button
        frm.add_custom_button(__("Sync to Inventory"), function() {
            sync_to_inventory_forecasts(frm);
        }, __("Integration"));
        
        // View Related Inventory Button
        if (frm.doc.related_inventory_forecast) {
            frm.add_custom_button(__("View Inventory Forecast"), function() {
                frappe.set_route("Form", "AI Inventory Forecast", frm.doc.related_inventory_forecast);
            }, __("Integration"));
        }
        
        // List Related Inventory Forecasts
        frm.add_custom_button(__("List Inventory Forecasts"), function() {
            show_related_inventory_forecasts(frm);
        }, __("Integration"));
        
        // Retry Failed Syncs
        if (frm.doc.sync_status === "Failed") {
            frm.add_custom_button(__("Retry Sync"), function() {
                retry_failed_sync(frm);
            }, __("Integration"));
        }
        
        // Update Balance Button
        frm.add_custom_button(__("Update Balance"), function() {
            update_current_balance(frm);
        }, __("Actions"));
        
        // Validate Forecast Button
        frm.add_custom_button(__("Validate Forecast"), function() {
            validate_forecast_data(frm);
        }, __("Actions"));
        
        // Export Data Button
        frm.add_custom_button(__("Export Data"), function() {
            export_forecast_data(frm);
        }, __("Actions"));
    }
    
    // Set sync status indicator color
    set_sync_status_indicator(frm);
}

function trigger_manual_sync(frm) {
    frappe.show_alert({
        message: __("Initiating sync..."),
        indicator: "blue"
    });
    
    frappe.call({
        method: "ai_inventory.forecasting.sync_manager.trigger_manual_sync",
        args: {
            forecast_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Sync completed successfully"),
                    indicator: "green"
                });
                
                frappe.msgprint({
                    title: "Sync Success",
                    message: "Manual sync completed successfully.",
                    indicator: "green"
                });
                
                // Refresh after a delay to avoid conflicts
                setTimeout(function() {
                    frm.reload_doc();
                }, 1500);
            } else {
                let error_msg = r.message ? r.message.error || "Unknown error" : "No response";
                frappe.show_alert({
                    message: __("Sync failed: ") + error_msg,
                    indicator: "red"
                });
                
                frappe.msgprint({
                    title: "Sync Error",
                    message: "Manual sync failed: " + error_msg,
                    indicator: "red"
                });
            }
        },
        error: function(r) {
            frappe.show_alert({
                message: __("Sync request failed"),
                indicator: "red"
            });
            
            frappe.msgprint({
                title: __("Request Error"),
                message: __("Failed to initiate sync. Please try again."),
                indicator: "red"
            });
        }
    });
}

function show_sync_details(frm) {
    frappe.call({
        method: "get_sync_details",
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                show_sync_details_dialog(r.message);
            } else {
                frappe.msgprint(__("Error loading sync details: ") + (r.message.error || "Unknown error"));
            }
        }
    });
}

function show_sync_details_dialog(sync_data) {
    let html = `
        <div class="sync-details-container">
            <div class="row">
                <div class="col-md-6">
                    <h5>Sync Status</h5>
                    <p><strong>Current Status:</strong> <span class="indicator ${get_status_color(sync_data.current_status)}">${sync_data.current_status}</span></p>
                    <p><strong>Last Sync:</strong> ${sync_data.last_sync_date || 'Never'}</p>
                    <p><strong>Auto Sync:</strong> ${sync_data.auto_sync_enabled ? 'Enabled' : 'Disabled'}</p>
                    <p><strong>Sync Frequency:</strong> ${sync_data.sync_frequency}</p>
                </div>
                <div class="col-md-6">
                    <h5>Sync Summary</h5>
                    <p><strong>Total Syncs:</strong> ${sync_data.sync_summary.total_syncs}</p>
                    <p><strong>Successful:</strong> ${sync_data.sync_summary.successful_syncs}</p>
                    <p><strong>Failed:</strong> ${sync_data.sync_summary.failed_syncs}</p>
                    <p><strong>Success Rate:</strong> ${sync_data.sync_summary.total_syncs > 0 ? Math.round((sync_data.sync_summary.successful_syncs / sync_data.sync_summary.total_syncs) * 100) : 0}%</p>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12">
                    <h5>Related Records</h5>
                    <div class="related-records">
                        ${Object.entries(sync_data.related_records).map(([key, value]) => 
                            `<span class="badge badge-info mr-2">${key.replace(/_/g, ' ').toUpperCase()}: ${value}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12">
                    <h5>Recent Sync Logs</h5>
                    <div class="sync-logs">
                        ${sync_data.sync_logs.map(log => `
                            <div class="sync-log-item border-bottom pb-2 mb-2">
                                <span class="indicator ${get_status_color(log.sync_status)}">${log.sync_status}</span>
                                <span class="text-muted">${log.sync_timestamp}</span>
                                <br>
                                <small>${log.sync_message || 'No message'}</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frappe.msgprint({
        title: __("Sync Details"),
        message: html,
        wide: true
    });
}

function get_status_color(status) {
    const colors = {
        'Completed': 'green',
        'Syncing': 'blue',
        'Pending': 'orange',
        'Failed': 'red'
    };
    return colors[status] || 'gray';
}

function set_sync_status_indicator(frm) {
    if (frm.doc.sync_status) {
        frm.dashboard.add_indicator(__("Sync Status: {0}", [frm.doc.sync_status]), get_status_color(frm.doc.sync_status));
    }
}

function retry_failed_sync(frm) {
    frappe.confirm(
        __("Are you sure you want to retry the failed sync operation?"),
        function() {
            trigger_manual_sync(frm);
        }
    );
}

function sync_to_inventory_forecasts(frm) {
    frappe.show_alert({
        message: __("Syncing to inventory forecasts..."),
        indicator: "blue"
    });
    
    frappe.call({
        method: "ai_inventory.forecasting.sync_manager.sync_single_forecast",
        args: {
            financial_forecast_id: frm.doc.name
        },
        callback: function(r) {
            console.log("Sync response:", r); // Debug log
            
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Inventory sync completed successfully"),
                    indicator: "green"
                });
                
                // Show detailed sync results for inventory
                if (r.message.synced_to && r.message.synced_to.includes("AI Inventory Forecast")) {
                    let msg = "Successfully synced to inventory forecasts.";
                    let details_found = false;
                    
                    // Get inventory sync details from the response
                    if (r.message.inventory_forecast_details) {
                        const details = r.message.inventory_forecast_details;
                        if (details.items_processed) {
                            msg += " Processed " + details.items_processed + " items.";
                            details_found = true;
                        }
                        if (details.synced_forecasts && details.synced_forecasts.length > 0) {
                            msg += " Created/updated " + details.synced_forecasts.length + " forecasts.";
                            details_found = true;
                        }
                        if (details.message) {
                            msg += " " + details.message;
                            details_found = true;
                        }
                    }
                    
                    // Fallback if no details found, use general success info
                    if (!details_found && r.message.synced_to) {
                        msg += " Synced to: " + r.message.synced_to.join(", ");
                    }
                    
                    // Show success dialog with actual content
                    frappe.msgprint({
                        title: "Inventory Sync Success",
                        message: msg,
                        indicator: "green"
                    });
                    
                } else if (r.message.synced_to && r.message.synced_to.length > 0) {
                    // Show general sync success
                    frappe.msgprint({
                        title: "Sync Completed",
                        message: "Sync operation completed successfully for: " + r.message.synced_to.join(", "),
                        indicator: "green"
                    });
                } else {
                    // Show basic success if no specific details
                    frappe.msgprint({
                        title: "Sync Completed",
                        message: "Sync operation completed successfully.",
                        indicator: "green"
                    });
                }
                
                // Refresh document to avoid modification conflicts
                setTimeout(function() {
                    frm.reload_doc();
                }, 1000);
            } else {
                let error_msg = "Unknown error";
                if (r.message && r.message.error) {
                    error_msg = r.message.error;
                } else if (r.message && r.message.errors && r.message.errors.length > 0) {
                    error_msg = r.message.errors.join("; ");
                }
                
                frappe.show_alert({
                    message: __("Inventory sync failed: ") + error_msg,
                    indicator: "red"
                });
                
                // Show detailed error dialog
                frappe.msgprint({
                    title: __("Sync Error"),
                    message: __("Inventory sync failed. Error: {0}<br><br>Please check:<br>• Company has at least one warehouse<br>• Items exist in the system<br>• Proper permissions are set", [error_msg]),
                    indicator: "red"
                });
            }
        },
        error: function(r) {
            frappe.show_alert({
                message: __("Sync request failed"),
                indicator: "red"
            });
            
            frappe.msgprint({
                title: __("Request Error"),
                message: __("Failed to initiate sync. Please check your network connection and try again."),
                indicator: "red"
            });
        }
    });
}

function show_related_inventory_forecasts(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "AI Inventory Forecast",
            filters: {
                source_financial_forecast: frm.doc.name
            },
            fields: ["name", "item_code", "item_name", "predicted_consumption", "confidence_score", "movement_type"]
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                show_inventory_forecasts_dialog(r.message, frm);
            } else {
                // Try to find by company if no direct link
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "AI Inventory Forecast",
                        filters: {
                            company: frm.doc.company
                        },
                        fields: ["name", "item_code", "item_name", "predicted_consumption", "confidence_score", "movement_type"],
                        limit_page_length: 20,
                        order_by: "creation desc"
                    },
                    callback: function(r2) {
                        if (r2.message && r2.message.length > 0) {
                            frappe.msgprint({
                                title: __("Related Inventory Forecasts (by Company)"),
                                message: __("Found {0} inventory forecasts for company {1}. Click 'Sync to Inventory' to create direct relationships.", [r2.message.length, frm.doc.company]),
                                indicator: "yellow"
                            });
                            show_inventory_forecasts_dialog(r2.message, frm);
                        } else {
                            frappe.msgprint(__("No inventory forecasts found. Click 'Sync to Inventory' to create inventory forecasts based on this financial forecast."));
                        }
                    }
                });
            }
        }
    });
}

function show_inventory_forecasts_dialog(forecasts, frm) {
    let html = `
        <div class="inventory-forecasts-container">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Item Code</th>
                        <th>Item Name</th>
                        <th>Predicted Consumption</th>
                        <th>Confidence</th>
                        <th>Movement Type</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${forecasts.map(forecast => `
                        <tr>
                            <td>${forecast.item_code}</td>
                            <td>${forecast.item_name || '-'}</td>
                            <td>${forecast.predicted_consumption || 0}</td>
                            <td><span class="badge badge-${get_confidence_color(forecast.confidence_score)}">${forecast.confidence_score || 0}%</span></td>
                            <td>${forecast.movement_type || 'Normal'}</td>
                            <td><a href="/app/ai-inventory-forecast/${forecast.name}" target="_blank" class="btn btn-sm btn-primary">View</a></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __("Related Inventory Forecasts"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "forecasts_html",
                options: html
            }
        ],
        primary_action_label: __("Sync New Forecasts"),
        primary_action: function() {
            sync_to_inventory_forecasts(frm);
            dialog.hide();
        }
    });
    
    dialog.show();
}

function get_confidence_color(score) {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'danger';
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

function update_current_balance(frm) {
    frappe.show_alert({
        message: "Updating current balance...",
        indicator: "blue"
    });
    
    frappe.call({
        method: "ai_inventory.balance.current_balance_manager.update_balance",
        args: {
            company: frm.doc.company,
            account: frm.doc.account
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: "Balance updated successfully",
                    indicator: "green"
                });
                
                frappe.msgprint({
                    title: "Balance Update Success",
                    message: "Current balance has been updated. New balance: " + (r.message.new_balance || "N/A"),
                    indicator: "green"
                });
                
                frm.reload_doc();
            } else {
                frappe.show_alert({
                    message: "Failed to update balance: " + (r.message ? r.message.error : "Unknown error"),
                    indicator: "red"
                });
            }
        },
        error: function() {
            frappe.show_alert({
                message: "Request failed. Please try again.",
                indicator: "red"
            });
        }
    });
}

function validate_forecast_data(frm) {
    frappe.show_alert({
        message: "Validating forecast data...",
        indicator: "blue"
    });
    
    frappe.call({
        method: "validate_forecast",
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: "Forecast validation completed",
                    indicator: "green"
                });
                
                let msg = "Forecast data validation completed successfully.";
                if (r.message.warnings && r.message.warnings.length > 0) {
                    msg += " Found " + r.message.warnings.length + " warnings.";
                }
                if (r.message.recommendations && r.message.recommendations.length > 0) {
                    msg += " " + r.message.recommendations.length + " recommendations available.";
                }
                
                frappe.msgprint({
                    title: "Validation Results",
                    message: msg,
                    indicator: r.message.warnings && r.message.warnings.length > 0 ? "orange" : "green"
                });
                
                if (r.message.warnings || r.message.recommendations) {
                    show_validation_details(r.message);
                }
            } else {
                frappe.show_alert({
                    message: "Validation failed: " + (r.message ? r.message.error : "Unknown error"),
                    indicator: "red"
                });
            }
        },
        error: function() {
            frappe.show_alert({
                message: "Validation request failed",
                indicator: "red"
            });
        }
    });
}

function show_validation_details(validation_result) {
    let dialog = new frappe.ui.Dialog({
        title: "Forecast Validation Details",
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "validation_details"
            }
        ]
    });
    
    let html = "<div class='validation-results'>";
    
    if (validation_result.warnings && validation_result.warnings.length > 0) {
        html += "<h4 style='color: orange;'>Warnings</h4><ul>";
        validation_result.warnings.forEach(function(warning) {
            html += "<li>" + warning + "</li>";
        });
        html += "</ul>";
    }
    
    if (validation_result.recommendations && validation_result.recommendations.length > 0) {
        html += "<h4 style='color: blue;'>Recommendations</h4><ul>";
        validation_result.recommendations.forEach(function(rec) {
            html += "<li>" + rec + "</li>";
        });
        html += "</ul>";
    }
    
    if (validation_result.metrics) {
        html += "<h4>Validation Metrics</h4>";
        html += "<p><strong>Accuracy Score:</strong> " + (validation_result.metrics.accuracy || "N/A") + "</p>";
        html += "<p><strong>Confidence Level:</strong> " + (validation_result.metrics.confidence || "N/A") + "</p>";
        html += "<p><strong>Data Quality:</strong> " + (validation_result.metrics.data_quality || "N/A") + "</p>";
    }
    
    html += "</div>";
    
    dialog.fields_dict.validation_details.$wrapper.html(html);
    dialog.show();
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
function format_currency(amount, currency_code = null) {
    // Get currency from document or system default
    const doc_currency = cur_frm && cur_frm.doc && cur_frm.doc.currency;
    const company_currency = cur_frm && cur_frm.doc && cur_frm.doc.company ? 
        frappe.defaults.get_default("currency") || 
        frappe.boot.sysdefaults.currency ||
        "INR" : "INR";
    
    const currency = currency_code || doc_currency || company_currency;
    
    // Map common currencies to locale
    const currency_locale_map = {
        'INR': 'en-IN',
        'USD': 'en-US', 
        'EUR': 'en-GB',
        'GBP': 'en-GB',
        'JPY': 'ja-JP',
        'CNY': 'zh-CN'
    };
    
    const locale = currency_locale_map[currency] || 'en-IN';
    
    try {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: currency === 'JPY' ? 0 : 2,
            maximumFractionDigits: currency === 'JPY' ? 0 : 2
        }).format(amount || 0);
    } catch (e) {
        // Fallback for unsupported currencies
        return `${currency} ${(amount || 0).toLocaleString()}`;
    }
}
