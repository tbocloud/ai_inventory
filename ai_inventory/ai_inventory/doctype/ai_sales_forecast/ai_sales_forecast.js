// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

// List view customization
frappe.listview_settings['AI Sales Forecast'] = {
    add_fields: ["confidence_score", "sales_trend", "movement_type", "predicted_qty", "sales_alert"],
    get_indicator: function(doc) {
        if (doc.sales_alert) {
            return [__("High Opportunity"), "green", "sales_alert,=,1"];
        } else if (doc.movement_type === "Critical") {
            return [__("🔴 Critical"), "red", "movement_type,=,Critical"];
        } else if (doc.movement_type === "Fast Moving") {
            return [__("🟢 Fast Moving"), "green", "movement_type,=,Fast Moving"];
        } else if (doc.confidence_score >= 80) {
            return [__("High Confidence"), "blue", "confidence_score,>=,80"];
        } else if (doc.confidence_score >= 60) {
            return [__("Medium Confidence"), "orange", "confidence_score,>=,60"];
        } else if (doc.confidence_score < 60 && doc.confidence_score > 0) {
            return [__("Low Confidence"), "red", "confidence_score,<,60"];
        } else {
            return [__("No Forecast"), "gray", "confidence_score,=,0"];
        }
    },
    formatters: {
        movement_type: function(value) {
            const colors = {
                'Fast Moving': 'green',
                'Slow Moving': 'orange',
                'Non Moving': 'red',
                'Critical': 'purple'
            };
            const color = colors[value] || 'gray';
            return `<span style="color: ${color}; font-weight: bold;">${value || '-'}</span>`;
        },
        confidence_score: function(value) {
            if (value >= 80) {
                return `<span style="color: green; font-weight: bold;">${value}%</span>`;
            } else if (value >= 60) {
                return `<span style="color: orange; font-weight: bold;">${value}%</span>`;
            } else if (value > 0) {
                return `<span style="color: red; font-weight: bold;">${value}%</span>`;
            } else {
                return `<span style="color: gray;">-</span>`;
            }
        },
        predicted_qty: function(value) {
            if (value > 0) {
                return `<span style="color: blue; font-weight: bold;">${value}</span>`;
            } else {
                return `<span style="color: gray;">-</span>`;
            }
        },
        sales_trend: function(value) {
            const colors = {
                'Increasing': 'green',
                'Stable': 'blue', 
                'Decreasing': 'orange',
                'Volatile': 'red'
            };
            const color = colors[value] || 'gray';
            return `<span style="color: ${color}; font-weight: bold;">${value || '-'}</span>`;
        }
    }
};

frappe.ui.form.on('AI Sales Forecast', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Run AI Forecast'), function() {
            run_ai_sales_forecast(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('View Sales History'), function() {
            view_sales_history_dialog(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Create Sales Order'), function() {
            create_sales_order(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Sync Now'), function() {
            sync_individual_sales_forecast(frm);
        }, __('Actions'));
        
        // Add bulk actions button for list view
        if (frm.is_new()) {
            frm.add_custom_button(__('Bulk Forecast'), function() {
                show_bulk_sales_forecast_dialog();
            }, __('Tools'));
        }
        
        // Add Sync All button (only for users with Sales Manager role)
        if (frappe.user.has_role('Sales Manager') || frappe.user.has_role('System Manager')) {
            frm.add_custom_button(__('Sync All Forecasts'), function() {
                sync_all_sales_forecasts();
            }, __('Tools'));
        }
        
        // Multi-company specific buttons
        if (!frm.is_new() && frm.doc.company) {
            frm.add_custom_button(__('Sync Company Forecasts'), function() {
                sync_company_sales_forecasts(frm);
            }, __('Company'));
            
            frm.add_custom_button(__('View Company Dashboard'), function() {
                view_company_sales_dashboard(frm);
            }, __('Company'));
        }
        
        // Set indicator colors based on forecast trend and alerts
        set_sales_form_indicators(frm);
        
        // Auto-refresh current sales data
        if (frm.doc.item_code && frm.doc.customer && !frm.is_new()) {
            refresh_current_sales_data(frm);
        }
        
        // Show forecast chart if data available
        if (frm.doc.predicted_qty && frm.doc.forecast_details) {
            render_sales_forecast_chart(frm);
        }
        
        // Add CSS styles
        add_sales_custom_styles();
        
        // Validate company-customer relationship
        validate_company_customer(frm);
    },
    
    setup: function(frm) {
        // Set up company filter for customer (do NOT use default_company)
        frm.set_query('customer', function() {
            let filters = {"disabled": 0};
            if (frm.doc.company) {
                filters.company = frm.doc.company;
            }
            return {
                filters: filters
            };
        });
        
        // Set up company filter for territory
        frm.set_query('territory', function() {
            let filters = {"disabled": 0};
            return {
                filters: filters
            };
        });
    },
    
    company: function(frm) {
        // Clear customer when company changes
        if (frm.doc.customer) {
            // Check if current customer belongs to new company
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Customer',
                    fieldname: ['name', 'disabled'],
                    filters: { name: frm.doc.customer }
                },
                callback: function(r) {
                    if (r.message && r.message.disabled) {
                        frm.set_value('customer', '');
                        frappe.msgprint(__('Customer cleared as it is disabled'));
                    }
                }
            });
        }
        
        // Refresh current sales data after company change
        if (frm.doc.item_code && frm.doc.customer) {
            refresh_current_sales_data(frm);
        }
    },
    
    item_code: function(frm) {
        if (frm.doc.item_code) {
            refresh_current_sales_data(frm);
            // Auto-run forecast for new records
            if (frm.is_new()) {
                setTimeout(() => run_ai_sales_forecast(frm), 1000);
            }
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer && frm.doc.item_code) {
            refresh_current_sales_data(frm);
            if (frm.is_new()) {
                setTimeout(() => run_ai_sales_forecast(frm), 1000);
            }
        }
    },
    
    forecast_period_days: function(frm) {
        if (frm.doc.item_code && frm.doc.customer && frm.doc.company && !frm.is_new()) {
            run_ai_sales_forecast(frm);
        }
    }
});

function validate_company_customer(frm) {
    // Validate that customer is active and accessible
    if (frm.doc.customer && frm.doc.company && !frm.is_new()) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Customer',
                fieldname: ['name', 'disabled', 'customer_name'],
                filters: { name: frm.doc.customer }
            },
            callback: function(r) {
                if (r.message && r.message.disabled) {
                    frm.dashboard.add_comment(
                        __('⚠️ Customer {0} is disabled', [frm.doc.customer]),
                        'orange',
                        true
                    );
                } else if (r.message && r.message.customer_name) {
                    frm.dashboard.add_comment(
                        __('✅ Customer: {0}', [r.message.customer_name]),
                        'green',
                        true
                    );
                }
            }
        });
    }
}

function sync_company_sales_forecasts(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('No company specified'));
        return;
    }
    
    frappe.confirm(
        __('This will sync ALL AI sales forecasts for {0}. This may take several minutes. Continue?', [frm.doc.company]),
        function() {
            frappe.show_alert({
                message: __('Starting sync for {0}...', [frm.doc.company]),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.sync_ai_sales_forecasts_now',
                args: {
                    company: frm.doc.company
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Sync completed for {0}: {1} successful, {2} failed', [
                                frm.doc.company, r.message.successful, r.message.failed
                            ]),
                            indicator: 'green'
                        });
                        
                        // Refresh the form
                        setTimeout(() => {
                            frm.refresh();
                        }, 2000);
                    } else {
                        frappe.msgprint(__('Sync failed for {0}: {1}', [frm.doc.company, r.message?.message || 'Unknown error']));
                    }
                }
            });
        }
    );
}

function view_company_sales_dashboard(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('No company specified'));
        return;
    }
    
    // Open AI Sales Forecast list with company filter
    frappe.route_options = {
        "company": frm.doc.company
    };
    frappe.set_route("List", "AI Sales Forecast");
}

function add_sales_custom_styles() {
    // Add styles only once
    if (!$('#ai-sales-styles').length) {
        $('<style id="ai-sales-styles">')
            .prop('type', 'text/css')
            .html(`
                .sales-sync-stat {
                    text-align: center;
                    padding: 15px;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                .sales-sync-stat h3 {
                    margin: 0;
                    font-size: 2em;
                    font-weight: bold;
                }
                .sales-sync-stat small {
                    color: #6c757d;
                    font-size: 0.875em;
                }
                .sales-progress-container {
                    padding: 20px;
                }
                .sales-forecast-results {
                    padding: 10px;
                }
                .sales-status-banner {
                    background: #f8f9fa;
                    padding: 8px;
                    margin: 10px 0;
                    border-radius: 4px;
                    font-size: 12px;
                }
                .sales-dialog-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .sales-dialog-table th,
                .sales-dialog-table td {
                    padding: 8px 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                .sales-dialog-table th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                .sales-dialog-table tr:hover {
                    background-color: #f5f5f5;
                }
                .sales-company-indicator {
                    display: inline-block;
                    background: #28a745;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                    margin-left: 5px;
                }
                .sales-persistent-status-banner {
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
            `)
            .appendTo('head');
    }
}

function run_ai_sales_forecast(frm) {
    if (!frm.doc.item_code) {
        frappe.msgprint(__('Please select Item Code first'));
        return;
    }
    
    // Check if company is set
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set the Company before running forecast'));
        return;
    }
    
    frappe.show_alert({
        message: __('Running AI Sales Forecast for {0}...', [frm.doc.company]),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.run_ai_forecast',
        args: {
            docname: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frm.refresh();
                frappe.show_alert({
                    message: __('AI Sales Forecast completed successfully for {0}', [frm.doc.company]),
                    indicator: 'green'
                });
                
                // Show results in a dialog
                show_sales_forecast_results_dialog(frm);
            } else {
                // Check if it's a processing flag error
                if (r.message && r.message.message && 
                    (r.message.message.includes('already processing') || 
                     r.message.message.includes('in progress'))) {
                    
                    frappe.show_alert({
                        message: __('AI Forecast is already running for this item. Please wait...'),
                        indicator: 'orange'
                    });
                } else {
                    frappe.msgprint(__('Forecast failed: {0}', [r.message?.message || 'Unknown error']));
                }
            }
        },
        error: function(r) {
            frappe.msgprint(__('Error running forecast: {0}', [r.message || 'Network error']));
        }
    });
}

function sync_individual_sales_forecast(frm) {
    if (!frm.doc.item_code) {
        frappe.msgprint(__('Please select Item Code first'));
        return;
    }
    
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set the Company before syncing'));
        return;
    }
    
    frappe.confirm(
        __('This will sync the AI sales forecast for this item in {0} immediately. Continue?', [frm.doc.company]),
        function() {
            frappe.show_alert({
                message: __('Syncing sales forecast for {0}...', [frm.doc.company]),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.generate_forecast_for_item',
                args: {
                    item_code: frm.doc.item_code,
                    customer: frm.doc.customer,
                    company: frm.doc.company
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frm.refresh();
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint(__('Sync failed: {0}', [r.message?.message || 'Unknown error']));
                    }
                }
            });
        }
    );
}

function sync_all_sales_forecasts() {
    frappe.confirm(
        __('This will sync ALL AI sales forecasts across all companies. This may take several minutes. Continue?'),
        function() {
            show_sales_sync_progress_dialog();
        }
    );
}

function show_sales_sync_progress_dialog() {
    let sync_dialog = new frappe.ui.Dialog({
        title: __('Syncing All AI Sales Forecasts'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'sync_progress'
            }
        ],
        primary_action_label: __('Run in Background'),
        primary_action: function() {
            sync_dialog.hide();
            run_background_sales_sync();
        }
    });
    
    sync_dialog.show();
    
    let progress_wrapper = sync_dialog.fields_dict.sync_progress.$wrapper;
    progress_wrapper.html(`
        <div class="sales-progress-container">
            <div class="text-center">
                <i class="fa fa-spinner fa-spin fa-2x text-success"></i>
                <h4 style="margin-top: 15px;">Starting AI Sales Forecast Sync...</h4>
                <p class="text-muted">Syncing all active sales forecasts across all companies...</p>
            </div>
            <div class="progress" style="margin-top: 20px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                     role="progressbar" style="width: 10%"></div>
            </div>
            <div id="sales-sync-status" style="margin-top: 10px; font-size: 12px; color: #666;">
                Initializing sync process...
            </div>
        </div>
    `);
    
    // Start the sync
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.sync_ai_sales_forecasts_now',
        callback: function(r) {
            if (r.message) {
                display_sales_sync_results_in_dialog(sync_dialog, r.message);
            }
        },
        error: function(r) {
            progress_wrapper.html(`
                <div class="alert alert-danger">
                    <h4><i class="fa fa-exclamation-triangle"></i> Sync Failed</h4>
                    <p>${r.message || 'An error occurred during sync'}</p>
                </div>
            `);
        }
    });
}

function display_sales_sync_results_in_dialog(dialog, result) {
    let progress_wrapper = dialog.fields_dict.sync_progress.$wrapper;
    
    let status_class = result.status === 'success' ? 'alert-success' : 
                      result.status === 'error' ? 'alert-danger' : 'alert-info';
    
    let html = `
        <div class="alert ${status_class}">
            <h4><i class="fa fa-check-circle"></i> Sync ${result.status === 'success' ? 'Completed' : 'Status'}</h4>
            <p><strong>${result.message}</strong></p>
        </div>
        
        <div class="row">
            <div class="col-md-3">
                <div class="sales-sync-stat">
                    <h3 class="text-primary">${result.total_items || 0}</h3>
                    <small>Total Items</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="sales-sync-stat">
                    <h3 class="text-success">${result.successful || 0}</h3>
                    <small>Successful</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="sales-sync-stat">
                    <h3 class="text-danger">${result.failed || 0}</h3>
                    <small>Failed</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="sales-sync-stat">
                    <h3 class="text-info">${result.success_rate || 0}%</h3>
                    <small>Success Rate</small>
                </div>
            </div>
        </div>
    `;
    
    // Add high opportunity alerts section if any
    if (result.high_opportunity_count && result.high_opportunity_count > 0) {
        html += `
            <div class="alert alert-info" style="margin-top: 20px;">
                <h5><i class="fa fa-line-chart"></i> High Opportunity Alerts</h5>
                <p><strong>${result.high_opportunity_count} items</strong> show high sales potential across companies.</p>
        `;
        
        if (result.high_opportunity_items && result.high_opportunity_items.length > 0) {
            html += '<h6>Top Opportunities:</h6><ul>';
            result.high_opportunity_items.forEach(item => {
                let company_badge = item.company ? `<span class="sales-company-indicator">${item.company}</span>` : '';
                html += `<li><strong>${item.item_code}</strong>${company_badge} (${item.forecast_trend || 'Growing'})</li>`;
            });
            html += '</ul>';
        }
        
        html += `
                <a href="/app/ai-sales-forecast?forecast_trend=Growing" target="_blank" 
                   class="btn btn-info btn-sm">
                    <i class="fa fa-external-link"></i> View High Opportunities
                </a>
            </div>
        `;
    }
    
    progress_wrapper.html(html);
    
    // Update dialog actions
    dialog.set_primary_action(__('Close'), function() {
        dialog.hide();
    });
    
    // Show success message
    if (result.status === 'success') {
        frappe.show_alert({
            message: __('AI Sales Forecast sync completed successfully across all companies!'),
            indicator: 'green'
        });
    }
}

function run_background_sales_sync() {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.enqueue_sync_ai_sales_forecasts',
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: r.message.status === 'success' ? 'green' : 'orange'
                });
            }
        }
    });
}

function refresh_current_sales_data(frm) {
    if (!frm.doc.company) {
        return;
    }
    
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.get_recent_sales_data',
        args: {
            item_code: frm.doc.item_code,
            customer: frm.doc.customer,
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let data = r.message.sales_data;
                if (data) {
                    // Note: Fields recent_sales_qty and average_sales don't exist in DocType
                    // So we'll just refresh the form instead
                    frm.refresh_field('actual_qty');
                }
            }
        }
    });
}

function set_sales_form_indicators(frm) {
    // Remove existing indicators
    frm.dashboard.clear_comment();
    
    // Add company indicator
    if (frm.doc.company) {
        frm.dashboard.add_comment(
            __('🏢 Company: {0}', [frm.doc.company]),
            'blue',
            true
        );
    }
    
    if (frm.doc.sales_alert) {
        frm.dashboard.set_headline_alert(
            __('🚀 SALES ALERT: This item shows strong sales potential for {0}', [frm.doc.company || 'this company']),
            'green'
        );
    }
    
    if (frm.doc.sales_trend) {
        let color = get_sales_trend_color(frm.doc.sales_trend);
        frm.dashboard.add_comment(
            __('Sales Trend: {0}', [frm.doc.sales_trend]),
            color,
            true
        );
    }
    
    if (frm.doc.confidence_score) {
        let confidence_color = frm.doc.confidence_score > 80 ? 'green' : frm.doc.confidence_score > 60 ? 'orange' : 'red';
        frm.dashboard.add_comment(
            __('Prediction Confidence: {0}%', [frm.doc.confidence_score]),
            confidence_color,
            true
        );
    }
    
    // Add last sync indicator
    if (frm.doc.last_forecast_date) {
        let last_sync_time = frappe.datetime.comment_when(frm.doc.last_forecast_date);
        frm.dashboard.add_comment(
            __('Last synced: {0}', [last_sync_time]),
            'blue',
            true
        );
    }
}

function get_sales_trend_color(trend) {
    const colors = {
        'Growing': 'green',
        'Stable': 'blue',
        'Declining': 'orange',
        'Critical': 'red'
    };
    return colors[trend] || 'blue';
}

function show_sales_forecast_results_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('AI Sales Forecast Results - {0} ({1})', [frm.doc.item_code, frm.doc.company]),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'forecast_summary'
            }
        ]
    });
    
    let html = `
        <div class="sales-forecast-results">
            <div class="row">
                <div class="col-md-6">
                    <h5>📊 Current Status</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Company</strong></td><td>${frm.doc.company || 'Not Set'}</td></tr>
                        <tr><td><strong>Actual Sales</strong></td><td>${frm.doc.actual_qty || 0} units</td></tr>
                        <tr><td><strong>Sales Trend</strong></td><td><span class="label label-${get_sales_trend_color(frm.doc.sales_trend)}">${frm.doc.sales_trend || 'Unknown'}</span></td></tr>
                        <tr><td><strong>Sales Alert</strong></td><td>${frm.doc.sales_alert ? '<span class="text-success">🚀 YES</span>' : '<span class="text-muted">NO</span>'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>🔮 Forecast (${frm.doc.forecast_period_days} days)</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Predicted Sales</strong></td><td>${frm.doc.predicted_qty || 0} units</td></tr>
                        <tr><td><strong>Confidence Level</strong></td><td>${frm.doc.confidence_score || 0}%</td></tr>
                        <tr><td><strong>Sales Trend</strong></td><td>${frm.doc.sales_trend || 'Unknown'}</td></tr>
                        <tr><td><strong>Model Version</strong></td><td>${frm.doc.model_version || 'N/A'}</td></tr>
                    </table>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <h5>📈 Forecast Analysis</h5>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; font-size: 12px;">${frm.doc.forecast_details || 'No analysis available'}</pre>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.forecast_summary.$wrapper.html(html);
    dialog.show();
    
    // Add action buttons if sales alert
    if (frm.doc.sales_alert) {
        dialog.set_primary_action(__('Create Sales Order'), function() {
            create_sales_order(frm);
            dialog.hide();
        });
    }
}

function create_sales_order(frm) {
    if (!frm.doc.item_code) {
        frappe.msgprint(__('Please select Item Code first'));
        return;
    }
    
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set the Company before creating sales order'));
        return;
    }
    
    // Check if we have a customer
    if (!frm.doc.customer) {
        frappe.msgprint(__('Please set a Customer before creating sales order'));
        return;
    }
    
    // Check if we have predicted sales
    if (!frm.doc.predicted_qty || frm.doc.predicted_qty <= 0) {
        frappe.msgprint(__('No predicted sales available. Please run AI Forecast first.'));
        return;
    }
    
    // Show confirmation dialog
    frappe.confirm(
        __('Create Sales Order for {0} units of {1} for customer {2}?', [
            frm.doc.predicted_qty, 
            frm.doc.item_code, 
            frm.doc.customer
        ]),
        function() {
            // User confirmed, create SO
            frappe.show_alert({
                message: __('Creating Sales Order...'),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.create_sales_order_from_data',
                args: {
                    item_code: frm.doc.item_code,
                    customer: frm.doc.customer,
                    predicted_qty: frm.doc.predicted_qty,
                    company: frm.doc.company
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Sales Order {0} created successfully!', [r.message.so_name]),
                            indicator: 'green'
                        });
                        
                        // Show success dialog with options
                        show_so_success_dialog(frm, r.message);
                        
                        // Refresh the form to show updated forecast details
                        frm.refresh();
                    } else {
                        frappe.msgprint(__('Failed to create Sales Order: {0}', [
                            r.message?.message || 'Unknown error'
                        ]));
                    }
                },
                error: function(r) {
                    frappe.msgprint(__('Error creating Sales Order: {0}', [
                        r.message || 'Network error'
                    ]));
                }
            });
        }
    );
}

function show_so_success_dialog(frm, result) {
    let dialog = new frappe.ui.Dialog({
        title: __('Sales Order Created Successfully'),
        size: 'medium',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'so_success_message'
            }
        ],
        primary_action_label: __('View Sales Order'),
        primary_action: function() {
            // Open the created SO
            frappe.set_route('Form', 'Sales Order', result.so_name);
            dialog.hide();
        }
    });
    
    let html = `
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 48px; color: #28a745; margin-bottom: 15px;">
                ✅
            </div>
            <h4 style="color: #28a745;">Sales Order Created!</h4>
            <p><strong>SO Number:</strong> ${result.so_name}</p>
            <p><strong>Item:</strong> ${frm.doc.item_code}</p>
            <p><strong>Quantity:</strong> ${frm.doc.predicted_qty} units</p>
            <p><strong>Customer:</strong> ${frm.doc.customer}</p>
            <p><strong>Company:</strong> ${frm.doc.company}</p>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <small class="text-muted">
                    💡 The Sales Order has been created based on AI forecast recommendations. 
                    You can modify quantities and other details in the Sales Order form.
                </small>
            </div>
        </div>
    `;
    
    dialog.fields_dict.so_success_message.$wrapper.html(html);
    dialog.show();
    
    // Add secondary action to view all SOs
    dialog.set_secondary_action(__('View All Sales Orders'), function() {
        frappe.set_route('List', 'Sales Order', {
            'customer': frm.doc.customer,
            'company': frm.doc.company
        });
        dialog.hide();
    });
}

function view_sales_history_dialog(frm) {
    if (!frm.doc.item_code) {
        frappe.msgprint(__('Please select an item first'));
        return;
    }
    
    let dialog = new frappe.ui.Dialog({
        title: __('Sales History - {0} ({1})', [frm.doc.item_code, frm.doc.company || 'All Companies']),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'sales_history'
            }
        ]
    });
    
    dialog.show();
    
    // Show loading
    dialog.fields_dict.sales_history.$wrapper.html(`
        <div class="text-center" style="padding: 50px;">
            <i class="fa fa-spinner fa-spin fa-2x text-success"></i>
            <h4 style="margin-top: 15px;">Loading sales history...</h4>
        </div>
    `);
    
    // Get sales history data
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.get_sales_history',
        args: {
            item_code: frm.doc.item_code,
            customer: frm.doc.customer,
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                display_sales_history_in_dialog(dialog, r.message.sales_data, frm);
            } else {
                dialog.fields_dict.sales_history.$wrapper.html(`
                    <div class="alert alert-warning">
                        <h4><i class="fa fa-exclamation-triangle"></i> No Sales Data</h4>
                        <p>No sales history found for ${frm.doc.item_code}</p>
                    </div>
                `);
            }
        },
        error: function() {
            dialog.fields_dict.sales_history.$wrapper.html(`
                <div class="alert alert-danger">
                    <h4><i class="fa fa-exclamation-triangle"></i> Error</h4>
                    <p>Failed to load sales history. Please try again.</p>
                </div>
            `);
        }
    });
}

function display_sales_history_in_dialog(dialog, sales_data, frm) {
    if (!sales_data || sales_data.length === 0) {
        dialog.fields_dict.sales_history.$wrapper.html(`
            <div class="alert alert-info">
                <h4><i class="fa fa-info-circle"></i> No Sales Found</h4>
                <p>No sales history found for ${frm.doc.item_code} in ${frm.doc.company || 'any company'}</p>
            </div>
        `);
        return;
    }
    
    // Calculate totals
    let total_sales = sales_data.reduce((sum, item) => sum + (item.qty || 0), 0);
    let total_amount = sales_data.reduce((sum, item) => sum + (item.amount || 0), 0);
    let avg_qty = total_sales / sales_data.length;
    let recent_sales = sales_data.slice(-30); // Last 30 records
    
    let html = `
        <div style="margin-bottom: 20px;">
            <div class="row">
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                        <h3 style="margin: 0; color: #28a745;">${total_sales.toFixed(1)}</h3>
                        <small>Total Sales Qty</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #d1ecf1; border-radius: 5px;">
                        <h3 style="margin: 0; color: #17a2b8;">${frappe.format(total_amount, {fieldtype: 'Currency'})}</h3>
                        <small>Total Sales Amount</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #fff3cd; border-radius: 5px;">
                        <h3 style="margin: 0; color: #ffc107;">${avg_qty.toFixed(1)}</h3>
                        <small>Average Qty/Order</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #f8d7da; border-radius: 5px;">
                        <h3 style="margin: 0; color: #dc3545;">${sales_data.length}</h3>
                        <small>Total Transactions</small>
                    </div>
                </div>
            </div>
        </div>
        
        <h5>📦 Recent Sales History</h5>
        <table class="sales-dialog-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Customer</th>
                    <th>Company</th>
                    <th>Qty</th>
                    <th>Rate</th>
                    <th>Amount</th>
                    <th>Document</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    recent_sales.reverse().forEach(item => {
        html += `
            <tr>
                <td>${frappe.datetime.str_to_user(item.posting_date) || '-'}</td>
                <td><strong>${item.customer || 'N/A'}</strong></td>
                <td><span class="sales-company-indicator">${item.company || 'N/A'}</span></td>
                <td style="color: green; font-weight: bold;">${item.qty || 0}</td>
                <td>${frappe.format(item.rate, {fieldtype: 'Currency'}) || '-'}</td>
                <td><strong>${frappe.format(item.amount, {fieldtype: 'Currency'}) || '-'}</strong></td>
                <td><a href="/app/sales-invoice/${item.parent}" target="_blank">${item.parent}</a></td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        
        <div style="margin-top: 20px;">
            <small class="text-muted">
                📊 <strong>Note:</strong> 
                Showing last ${recent_sales.length} transactions out of ${sales_data.length} total. 
                This data is used by AI algorithms to predict future sales trends.
            </small>
        </div>
    `;
    
    dialog.fields_dict.sales_history.$wrapper.html(html);
    
    // Add action button to open full sales analytics report
    dialog.set_primary_action(__('Open Sales Analytics'), function() {
        frappe.route_options = { 
            "item_code": frm.doc.item_code
        };
        if (frm.doc.customer) {
            frappe.route_options.customer = frm.doc.customer;
        }
        if (frm.doc.company) {
            frappe.route_options.company = frm.doc.company;
        }
        frappe.set_route("query-report", "Sales Analytics");
        dialog.hide();
    });
}

function show_bulk_sales_forecast_dialog() {
    let dialog = new frappe.ui.Dialog({
        title: __('Bulk AI Sales Forecast'),
        size: 'medium',
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'company',
                label: __('Company'),
                options: 'Company',
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'customer',
                label: __('Customer (Optional)'),
                options: 'Customer'
            },
            {
                fieldtype: 'Link',
                fieldname: 'territory',
                label: __('Territory (Optional)'),
                options: 'Territory'
            },
            {
                fieldtype: 'Int',
                fieldname: 'days',
                label: __('Forecast Period (Days)'),
                default: 30
            }
        ],
        primary_action_label: __('Generate Forecasts'),
        primary_action: function() {
            let values = dialog.get_values();
            if (values) {
                frappe.call({
                    method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.bulk_create_sales_forecasts',
                    args: values,
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: r.message.status === 'success' ? 'green' : 'orange'
                            });
                            dialog.hide();
                        }
                    }
                });
            }
        }
    });
    
    dialog.show();
}

function render_sales_forecast_chart(frm) {
    // Implementation for sales forecast chart rendering
    // This would create a chart showing predicted vs actual sales trends
    console.log('Rendering sales forecast chart for', frm.doc.item_code);
}
