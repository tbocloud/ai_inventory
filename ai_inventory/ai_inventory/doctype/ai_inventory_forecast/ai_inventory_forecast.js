// ai_inventory/ai_inventory/doctype/ai_inventory_forecast/ai_inventory_forecast.js
// FIXED VERSION - Persistent status banner and stock dialog

frappe.ui.form.on('AI Inventory Forecast', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Run AI Forecast'), function() {
            run_ai_forecast(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('View Stock Levels'), function() {
            view_stock_levels_dialog(frm); // Changed to dialog
        }, __('Actions'));
        
        frm.add_custom_button(__('Create Purchase Order'), function() {
            create_purchase_order(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Sync Now'), function() {
            sync_individual_forecast(frm);
        }, __('Actions'));
        
        // Add bulk actions button for list view
        if (frm.is_new()) {
            frm.add_custom_button(__('Bulk Forecast'), function() {
                show_bulk_forecast_dialog();
            }, __('Tools'));
        }
        
        // Add Sync All button (only for users with Stock Manager role)
        if (frappe.user.has_role('Stock Manager') || frappe.user.has_role('System Manager')) {
            frm.add_custom_button(__('Sync All Forecasts'), function() {
                sync_all_forecasts();
            }, __('Tools'));
        }
        
        // Multi-company specific buttons
        if (!frm.is_new() && frm.doc.company) {
            frm.add_custom_button(__('Sync Company Forecasts'), function() {
                sync_company_forecasts(frm);
            }, __('Company'));
            
            frm.add_custom_button(__('View Company Dashboard'), function() {
                view_company_dashboard(frm);
            }, __('Company'));
        }
        
        // Set indicator colors based on movement type and alerts
        set_form_indicators(frm);
        
        // Auto-refresh current stock
        if (frm.doc.item_code && frm.doc.warehouse && !frm.is_new()) {
            refresh_current_stock(frm);
        }
        
        // Show forecast chart if data available
        if (frm.doc.predicted_consumption && frm.doc.historical_data) {
            render_forecast_chart(frm);
        }
        
        // Add CSS styles
        add_custom_styles();
        
        // Validate company-warehouse relationship
        validate_company_warehouse(frm);
    },
    
    setup: function(frm) {
        // Set up company filter for warehouse
        frm.set_query('warehouse', function() {
            let filters = {"disabled": 0};
            if (frm.doc.company) {
                filters.company = frm.doc.company;
            }
            return {
                filters: filters
            };
        });
        
        // Set up company filter for supplier
        frm.set_query('supplier', function() {
            let filters = {"disabled": 0};
            if (frm.doc.company) {
                filters.company = frm.doc.company;
            }
            return {
                filters: filters
            };
        });
    },
    
    company: function(frm) {
        // Clear warehouse when company changes
        if (frm.doc.warehouse) {
            // Check if current warehouse belongs to new company
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Warehouse',
                    fieldname: 'company',
                    filters: { name: frm.doc.warehouse }
                },
                callback: function(r) {
                    if (r.message && r.message.company !== frm.doc.company) {
                        frm.set_value('warehouse', '');
                        frappe.msgprint(__('Warehouse cleared as it does not belong to the selected company'));
                    }
                }
            });
        }
        
        // Clear supplier if it doesn't belong to company
        if (frm.doc.supplier) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Supplier',
                    fieldname: 'company',
                    filters: { name: frm.doc.supplier }
                },
                callback: function(r) {
                    if (r.message && r.message.company && r.message.company !== frm.doc.company) {
                        frm.set_value('supplier', '');
                        frappe.msgprint(__('Supplier cleared as it does not belong to the selected company'));
                    }
                }
            });
        }
        
        // Refresh current stock after company change
        if (frm.doc.item_code && frm.doc.warehouse) {
            refresh_current_stock(frm);
        }
    },
    
    item_code: function(frm) {
        if (frm.doc.item_code && frm.doc.warehouse) {
            // Auto-set company from warehouse if not set
            if (!frm.doc.company && frm.doc.warehouse) {
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Warehouse',
                        fieldname: 'company',
                        filters: { name: frm.doc.warehouse }
                    },
                    callback: function(r) {
                        if (r.message && r.message.company) {
                            frm.set_value('company', r.message.company);
                        }
                    }
                });
            }
            
            refresh_current_stock(frm);
            // Auto-run forecast for new records
            if (frm.is_new()) {
                setTimeout(() => run_ai_forecast(frm), 1000);
            }
        }
    },
    
    warehouse: function(frm) {
        if (frm.doc.warehouse) {
            // Auto-set company from warehouse if not set
            if (!frm.doc.company) {
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Warehouse',
                        fieldname: 'company',
                        filters: { name: frm.doc.warehouse }
                    },
                    callback: function(r) {
                        if (r.message && r.message.company) {
                            frm.set_value('company', r.message.company);
                        }
                    }
                });
            }
            
            if (frm.doc.item_code) {
                refresh_current_stock(frm);
                if (frm.is_new()) {
                    setTimeout(() => run_ai_forecast(frm), 1000);
                }
            }
        }
    },
    
    forecast_period_days: function(frm) {
        if (frm.doc.item_code && frm.doc.warehouse && frm.doc.company && !frm.is_new()) {
            run_ai_forecast(frm);
        }
    },
    
    auto_create_po: function(frm) {
        if (frm.doc.auto_create_po && !frm.doc.supplier) {
            frappe.msgprint(__('Please select a preferred supplier for auto PO creation'));
        }
    }
});

function validate_company_warehouse(frm) {
    // Validate that warehouse belongs to the selected company
    if (frm.doc.warehouse && frm.doc.company && !frm.is_new()) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Warehouse',
                fieldname: 'company',
                filters: { name: frm.doc.warehouse }
            },
            callback: function(r) {
                if (r.message && r.message.company !== frm.doc.company) {
                    frm.dashboard.add_comment(
                        __('⚠️ Warehouse {0} does not belong to company {1}', [frm.doc.warehouse, frm.doc.company]),
                        'red',
                        true
                    );
                }
            }
        });
    }
}

function sync_company_forecasts(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('No company specified'));
        return;
    }
    
    frappe.confirm(
        __('This will sync ALL AI forecasts for {0}. This may take several minutes. Continue?', [frm.doc.company]),
        function() {
            frappe.show_alert({
                message: __('Starting sync for {0}...', [frm.doc.company]),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now',
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

function view_company_dashboard(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('No company specified'));
        return;
    }
    
    // Open AI Inventory Forecast list with company filter
    frappe.route_options = {
        "company": frm.doc.company
    };
    frappe.set_route("List", "AI Inventory Forecast");
}

function add_custom_styles() {
    // Add styles only once
    if (!$('#ai-inventory-styles').length) {
        $('<style id="ai-inventory-styles">')
            .prop('type', 'text/css')
            .html(`
                .sync-stat {
                    text-align: center;
                    padding: 15px;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                .sync-stat h3 {
                    margin: 0;
                    font-size: 2em;
                    font-weight: bold;
                }
                .sync-stat small {
                    color: #6c757d;
                    font-size: 0.875em;
                }
                .sync-progress-container {
                    padding: 20px;
                }
                .forecast-results {
                    padding: 10px;
                }
                .sync-status-banner {
                    background: #e3f2fd;
                    padding: 8px;
                    margin: 10px 0;
                    border-radius: 4px;
                    font-size: 12px;
                }
                .filter-shortcuts {
                    margin: 10px 0;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 4px;
                }
                .filter-shortcuts button {
                    margin-right: 5px;
                    margin-bottom: 5px;
                }
                .company-indicator {
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                    margin-left: 5px;
                }
                .persistent-status-banner {
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .stock-dialog-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .stock-dialog-table th,
                .stock-dialog-table td {
                    padding: 8px 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                .stock-dialog-table th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                .stock-dialog-table tr:hover {
                    background-color: #f5f5f5;
                }
            `)
            .appendTo('head');
    }
}

function run_ai_forecast(frm) {
    if (!frm.doc.item_code || !frm.doc.warehouse) {
        frappe.msgprint(__('Please select Item Code and Warehouse first'));
        return;
    }
    
    // Check if company is set
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set the Company before running forecast'));
        return;
    }
    
    frappe.show_alert({
        message: __('Running AI Forecast for {0}...', [frm.doc.company]),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'run_ai_forecast',
        doc: frm.doc,
        callback: function(r) {
            if (!r.exc) {
                frm.refresh();
                frappe.show_alert({
                    message: __('AI Forecast completed successfully for {0}', [frm.doc.company]),
                    indicator: 'green'
                });
                
                // Show results in a dialog
                show_forecast_results_dialog(frm);
            }
        }
    });
}

function sync_individual_forecast(frm) {
    if (!frm.doc.item_code || !frm.doc.warehouse) {
        frappe.msgprint(__('Please select Item Code and Warehouse first'));
        return;
    }
    
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set the Company before syncing'));
        return;
    }
    
    frappe.confirm(
        __('This will sync the AI forecast for this item in {0} immediately. Continue?', [frm.doc.company]),
        function() {
            frappe.show_alert({
                message: __('Syncing forecast for {0}...', [frm.doc.company]),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.hooks_handlers.trigger_immediate_forecast_update',
                args: {
                    item_code: frm.doc.item_code,
                    warehouse: frm.doc.warehouse
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

function sync_all_forecasts() {
    frappe.confirm(
        __('This will sync ALL AI forecasts across all companies. This may take several minutes. Continue?'),
        function() {
            show_sync_progress_dialog();
        }
    );
}

function show_sync_progress_dialog() {
    let sync_dialog = new frappe.ui.Dialog({
        title: __('Syncing All AI Forecasts'),
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
            run_background_sync();
        }
    });
    
    sync_dialog.show();
    
    let progress_wrapper = sync_dialog.fields_dict.sync_progress.$wrapper;
    progress_wrapper.html(`
        <div class="sync-progress-container">
            <div class="text-center">
                <i class="fa fa-spinner fa-spin fa-2x text-primary"></i>
                <h4 style="margin-top: 15px;">Starting AI Forecast Sync...</h4>
                <p class="text-muted">Syncing all active forecasts across all companies...</p>
            </div>
            <div class="progress" style="margin-top: 20px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 10%"></div>
            </div>
            <div id="sync-status" style="margin-top: 10px; font-size: 12px; color: #666;">
                Initializing sync process...
            </div>
        </div>
    `);
    
    // Start the sync
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now',
        callback: function(r) {
            if (r.message) {
                display_sync_results_in_dialog(sync_dialog, r.message);
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

function display_sync_results_in_dialog(dialog, result) {
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
                <div class="sync-stat">
                    <h3 class="text-primary">${result.total_items || 0}</h3>
                    <small>Total Items</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="sync-stat">
                    <h3 class="text-success">${result.successful || 0}</h3>
                    <small>Successful</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="sync-stat">
                    <h3 class="text-danger">${result.failed || 0}</h3>
                    <small>Failed</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="sync-stat">
                    <h3 class="text-info">${result.success_rate || 0}%</h3>
                    <small>Success Rate</small>
                </div>
            </div>
        </div>
    `;
    
    // Add reorder alerts section if any
    if (result.reorder_alerts_count && result.reorder_alerts_count > 0) {
        html += `
            <div class="alert alert-warning" style="margin-top: 20px;">
                <h5><i class="fa fa-exclamation-triangle"></i> Reorder Alerts Generated</h5>
                <p><strong>${result.reorder_alerts_count} items</strong> need immediate attention across companies.</p>
        `;
        
        if (result.critical_items && result.critical_items.length > 0) {
            html += '<h6>Critical Items:</h6><ul>';
            result.critical_items.forEach(item => {
                let company_badge = item.company ? `<span class="company-indicator">${item.company}</span>` : '';
                html += `<li><strong>${item.item_code}</strong> at ${item.warehouse}${company_badge} (${item.movement_type})</li>`;
            });
            html += '</ul>';
        }
        
        html += `
                <a href="/app/ai-inventory-forecast?reorder_alert=1" target="_blank" 
                   class="btn btn-warning btn-sm">
                    <i class="fa fa-external-link"></i> View Reorder Alerts
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
            message: __('AI Forecast sync completed successfully across all companies!'),
            indicator: 'green'
        });
    }
}

function run_background_sync() {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.enqueue_sync_ai_forecasts',
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

function refresh_current_stock(frm) {
    if (!frm.doc.company) {
        return;
    }
    
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Bin',
            filters: {
                item_code: frm.doc.item_code,
                warehouse: frm.doc.warehouse
            },
            fieldname: 'actual_qty'
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('current_stock', r.message.actual_qty || 0);
            }
        }
    });
}

function set_form_indicators(frm) {
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
    
    if (frm.doc.reorder_alert) {
        frm.dashboard.set_headline_alert(
            __('🚨 REORDER ALERT: Stock level is below recommended reorder point for {0}', [frm.doc.company || 'this company']),
            'red'
        );
    }
    
    if (frm.doc.movement_type) {
        let color = get_movement_type_color(frm.doc.movement_type);
        frm.dashboard.add_comment(
            __('Movement Type: {0}', [frm.doc.movement_type]),
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

function get_movement_type_color(movement_type) {
    const colors = {
        'Fast Moving': 'green',
        'Slow Moving': 'orange',
        'Non Moving': 'red',
        'Critical': 'purple'
    };
    return colors[movement_type] || 'blue';
}

function show_forecast_results_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('AI Forecast Results - {0} ({1})', [frm.doc.item_code, frm.doc.company]),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'forecast_summary'
            }
        ]
    });
    
    let html = `
        <div class="forecast-results">
            <div class="row">
                <div class="col-md-6">
                    <h5>📊 Current Status</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Company</strong></td><td>${frm.doc.company || 'Not Set'}</td></tr>
                        <tr><td><strong>Current Stock</strong></td><td>${frm.doc.current_stock || 0} units</td></tr>
                        <tr><td><strong>Movement Type</strong></td><td><span class="label label-${get_movement_type_color(frm.doc.movement_type)}">${frm.doc.movement_type || 'Unknown'}</span></td></tr>
                        <tr><td><strong>Reorder Alert</strong></td><td>${frm.doc.reorder_alert ? '<span class="text-danger">🚨 YES</span>' : '<span class="text-success">✅ NO</span>'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>🔮 Forecast (${frm.doc.forecast_period_days} days)</h5>
                    <table class="table table-bordered">
                        <tr><td><strong>Predicted Consumption</strong></td><td>${frm.doc.predicted_consumption || 0} units</td></tr>
                        <tr><td><strong>Confidence Level</strong></td><td>${frm.doc.confidence_score || 0}%</td></tr>
                        <tr><td><strong>Suggested Reorder Level</strong></td><td>${frm.doc.reorder_level || 0} units</td></tr>
                        <tr><td><strong>Suggested Order Qty</strong></td><td>${frm.doc.suggested_qty || 0} units</td></tr>
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
    
    // Add action buttons if reorder is needed
    if (frm.doc.reorder_alert) {
        dialog.set_primary_action(__('Create Purchase Order'), function() {
            create_purchase_order(frm);
            dialog.hide();
        });
    }
}

// Helper function to safely get attribute
function getattr(obj, attr, default_val) {
    return obj && obj[attr] !== undefined ? obj[attr] : default_val;
}

// CREATE PURCHASE ORDER FUNCTION - NEWLY ADDED
function create_purchase_order(frm) {
    if (!frm.doc.item_code || !frm.doc.warehouse) {
        frappe.msgprint(__('Please select Item Code and Warehouse first'));
        return;
    }
    
    if (!frm.doc.company) {
        frappe.msgprint(__('Please set the Company before creating purchase order'));
        return;
    }
    
    // Check if we have a supplier
    let supplier = frm.doc.supplier || getattr(frm.doc, 'preferred_supplier', null);
    if (!supplier) {
        frappe.msgprint(__('Please set a Supplier or Preferred Supplier before creating purchase order'));
        return;
    }
    
    // Check if we have suggested quantity
    if (!frm.doc.suggested_qty || frm.doc.suggested_qty <= 0) {
        frappe.msgprint(__('No suggested quantity available. Please run AI Forecast first.'));
        return;
    }
    
    // Show confirmation dialog
    frappe.confirm(
        __('Create Purchase Order for {0} units of {1} from {2}?', [
            frm.doc.suggested_qty, 
            frm.doc.item_code, 
            supplier
        ]),
        function() {
            // User confirmed, create PO
            frappe.show_alert({
                message: __('Creating Purchase Order...'),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'create_purchase_order',
                doc: frm.doc,
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Purchase Order {0} created successfully!', [r.message.po_name]),
                            indicator: 'green'
                        });
                        
                        // Show success dialog with options
                        show_po_success_dialog(frm, r.message);
                        
                        // Refresh the form to show updated forecast details
                        frm.refresh();
                    } else {
                        frappe.msgprint(__('Failed to create Purchase Order: {0}', [
                            r.message?.message || 'Unknown error'
                        ]));
                    }
                },
                error: function(r) {
                    frappe.msgprint(__('Error creating Purchase Order: {0}', [
                        r.message || 'Network error'
                    ]));
                }
            });
        }
    );
}

function show_po_success_dialog(frm, result) {
    let dialog = new frappe.ui.Dialog({
        title: __('Purchase Order Created Successfully'),
        size: 'medium',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'po_success_message'
            }
        ],
        primary_action_label: __('View Purchase Order'),
        primary_action: function() {
            // Open the created PO
            frappe.set_route('Form', 'Purchase Order', result.po_name);
            dialog.hide();
        }
    });
    
    let html = `
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 48px; color: #28a745; margin-bottom: 15px;">
                ✅
            </div>
            <h4 style="color: #28a745;">Purchase Order Created!</h4>
            <p><strong>PO Number:</strong> ${result.po_name}</p>
            <p><strong>Item:</strong> ${frm.doc.item_code}</p>
            <p><strong>Quantity:</strong> ${frm.doc.suggested_qty} units</p>
            <p><strong>Supplier:</strong> ${frm.doc.supplier || frm.doc.preferred_supplier}</p>
            <p><strong>Company:</strong> ${frm.doc.company}</p>
            <p><strong>Warehouse:</strong> ${frm.doc.warehouse}</p>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <small class="text-muted">
                    💡 The Purchase Order has been created based on AI forecast recommendations. 
                    You can modify quantities and other details in the Purchase Order form.
                </small>
            </div>
        </div>
    `;
    
    dialog.fields_dict.po_success_message.$wrapper.html(html);
    dialog.show();
    
    // Add secondary action to view all POs
    dialog.set_secondary_action(__('View All Purchase Orders'), function() {
        frappe.set_route('List', 'Purchase Order', {
            'supplier': frm.doc.supplier || frm.doc.preferred_supplier,
            'company': frm.doc.company
        });
        dialog.hide();
    });
}

// FIXED: View Stock Levels in Dialog instead of redirecting
function view_stock_levels_dialog(frm) {
    if (!frm.doc.item_code) {
        frappe.msgprint(__('Please select an item first'));
        return;
    }
    
    let dialog = new frappe.ui.Dialog({
        title: __('Stock Levels - {0} ({1})', [frm.doc.item_code, frm.doc.company || 'All Companies']),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'stock_levels'
            }
        ]
    });
    
    dialog.show();
    
    // Show loading
    dialog.fields_dict.stock_levels.$wrapper.html(`
        <div class="text-center" style="padding: 50px;">
            <i class="fa fa-spinner fa-spin fa-2x text-primary"></i>
            <h4 style="margin-top: 15px;">Loading stock levels...</h4>
        </div>
    `);
    
    // Get stock data
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.get_item_stock_levels',
        args: {
            item_code: frm.doc.item_code,
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                display_stock_levels_in_dialog(dialog, r.message.stock_data, frm);
            } else {
                dialog.fields_dict.stock_levels.$wrapper.html(`
                    <div class="alert alert-warning">
                        <h4><i class="fa fa-exclamation-triangle"></i> No Stock Data</h4>
                        <p>No stock data found for ${frm.doc.item_code}</p>
                    </div>
                `);
            }
        },
        error: function() {
            dialog.fields_dict.stock_levels.$wrapper.html(`
                <div class="alert alert-danger">
                    <h4><i class="fa fa-exclamation-triangle"></i> Error</h4>
                    <p>Failed to load stock data. Please try again.</p>
                </div>
            `);
        }
    });
}

function display_stock_levels_in_dialog(dialog, stock_data, frm) {
    if (!stock_data || stock_data.length === 0) {
        dialog.fields_dict.stock_levels.$wrapper.html(`
            <div class="alert alert-info">
                <h4><i class="fa fa-info-circle"></i> No Stock Found</h4>
                <p>No stock data found for ${frm.doc.item_code} in ${frm.doc.company || 'any company'}</p>
            </div>
        `);
        return;
    }
    
    // Calculate totals
    let total_stock = stock_data.reduce((sum, item) => sum + (item.actual_qty || 0), 0);
    let total_reserved = stock_data.reduce((sum, item) => sum + (item.reserved_qty || 0), 0);
    let total_ordered = stock_data.reduce((sum, item) => sum + (item.ordered_qty || 0), 0);
    let total_planned = stock_data.reduce((sum, item) => sum + (item.planned_qty || 0), 0);
    
    let html = `
        <div style="margin-bottom: 20px;">
            <div class="row">
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                        <h3 style="margin: 0; color: #28a745;">${total_stock}</h3>
                        <small>Total Available Stock</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #fff3cd; border-radius: 5px;">
                        <h3 style="margin: 0; color: #ffc107;">${total_reserved}</h3>
                        <small>Reserved Stock</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #d1ecf1; border-radius: 5px;">
                        <h3 style="margin: 0; color: #17a2b8;">${total_ordered}</h3>
                        <small>On Order</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div style="text-align: center; padding: 15px; background: #e2e3e5; border-radius: 5px;">
                        <h3 style="margin: 0; color: #6c757d;">${total_planned}</h3>
                        <small>Planned</small>
                    </div>
                </div>
            </div>
        </div>
        
        <h5>📦 Stock by Warehouse</h5>
        <table class="stock-dialog-table">
            <thead>
                <tr>
                    <th>Warehouse</th>
                    <th>Company</th>
                    <th>Available Qty</th>
                    <th>Reserved Qty</th>
                    <th>Ordered Qty</th>
                    <th>Planned Qty</th>
                    <th>Actual Qty</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    stock_data.forEach(item => {
        let status_color = 'green';
        let status_text = 'Good';
        
        if (item.actual_qty <= 0) {
            status_color = 'red';
            status_text = 'Out of Stock';
        } else if (item.actual_qty <= 10) {
            status_color = 'orange';
            status_text = 'Low Stock';
        }
        
        html += `
            <tr>
                <td><strong>${item.warehouse}</strong></td>
                <td><span class="company-indicator">${item.company || 'N/A'}</span></td>
                <td style="color: ${item.actual_qty > 0 ? 'green' : 'red'}; font-weight: bold;">${item.actual_qty || 0}</td>
                <td>${item.reserved_qty || 0}</td>
                <td style="color: blue;">${item.ordered_qty || 0}</td>
                <td style="color: #6c757d;">${item.planned_qty || 0}</td>
                <td><strong>${item.actual_qty || 0}</strong></td>
                <td><span style="color: ${status_color}; font-weight: bold;">${status_text}</span></td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        
        <div style="margin-top: 20px;">
            <small class="text-muted">
                📊 <strong>Legend:</strong> 
                Available Qty = Stock available for sale | 
                Reserved Qty = Stock reserved for sales orders | 
                Ordered Qty = Stock on purchase orders | 
                Planned Qty = Planned production quantity
            </small>
        </div>
    `;
    
    dialog.fields_dict.stock_levels.$wrapper.html(html);
    
    // Add action button to open full stock balance report
    dialog.set_primary_action(__('Open Stock Balance Report'), function() {
        frappe.route_options = { 
            "item_code": frm.doc.item_code
        };
        if (frm.doc.company) {
            frappe.route_options.company = frm.doc.company;
        }
        frappe.set_route("query-report", "Stock Balance");
        dialog.hide();
    });
}

// =============================================================================
// LIST VIEW SETTINGS - ADD THIS TO THE END OF ai_inventory_forecast.js
// =============================================================================

// Helper function: Add CSS styles
function add_ai_forecast_styles() {
    if (!$('#ai-forecast-listview-styles').length) {
        $('<style id="ai-forecast-listview-styles">')
            .prop('type', 'text/css')
            .html(`
                .ai-company-indicator {
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
                #ai-forecast-status-banner {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    position: sticky;
                    top: 60px;
                    z-index: 999;
                }
            `)
            .appendTo('head');
    }
}

// Helper function: Add status banner
function add_ai_forecast_status_banner(listview) {
    $('#ai-forecast-status-banner').remove();
    
    let banner = $(`
        <div id="ai-forecast-status-banner">
            <div class="row">
                <div class="col-md-9">
                    <h5 style="margin: 0; color: white;">📊 AI Inventory Forecast Status</h5>
                    <div id="ai-status-metrics" style="margin-top: 10px;">
                        <i class="fa fa-spinner fa-spin"></i> Loading status...
                    </div>
                </div>
                <div class="col-md-3 text-right">
                    <button class="btn btn-sm btn-light" onclick="sync_all_forecasts_from_list()">
                        🔄 Sync All
                    </button>
                    <button class="btn btn-sm btn-light ml-2" onclick="refresh_ai_status()">
                        ⟳ Refresh
                    </button>
                </div>
            </div>
        </div>
    `);
    
    if (listview.page.$title_area?.length) {
        banner.insertAfter(listview.page.$title_area);
    } else {
        banner.prependTo(listview.page.main);
    }
    
    setTimeout(() => refresh_ai_status(listview), 500);
}

// Helper function: Refresh status
function refresh_ai_status(listview) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.get_simple_sync_status',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let stats = r.message.current_stats || {};
                let html = `
                    <div class="row">
                        <div class="col-md-3">
                            <strong style="color: #fff;">Total:</strong> 
                            <span style="color: #fff;">${stats.total_forecasts || 0}</span>
                        </div>
                        <div class="col-md-3">
                            <strong style="color: #fff;">Alerts:</strong> 
                            <span style="color: ${stats.current_alerts > 0 ? '#ffc107' : '#fff'}">
                                ${stats.current_alerts || 0}
                            </span>
                        </div>
                        <div class="col-md-3">
                            <strong style="color: #fff;">Updated Today:</strong> 
                            <span style="color: #fff;">${stats.updated_today || 0}</span>
                        </div>
                        <div class="col-md-3">
                            <strong style="color: #fff;">Avg Confidence:</strong> 
                            <span style="color: #fff;">${Math.round(stats.avg_confidence || 0)}%</span>
                        </div>
                    </div>
                `;
                $('#ai-status-metrics').html(html);
            } else {
                $('#ai-status-metrics').html('<span style="color: #ffc107;">Status unavailable</span>');
            }
        },
        error: function() {
            $('#ai-status-metrics').html('<span style="color: #dc3545;">Failed to load</span>');
        }
    });
}

// Helper function: Sync all forecasts
function sync_all_forecasts_from_list() {
    frappe.confirm(
        __('This will sync ALL AI forecasts. Continue?'),
        function() {
            frappe.show_alert({
                message: __('Starting sync...'),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now',
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Sync completed: {0} successful, {1} failed', [
                                r.message.successful, r.message.failed
                            ]),
                            indicator: 'green'
                        });
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        frappe.msgprint(__('Sync failed: {0}', [r.message?.message || 'Unknown error']));
                    }
                }
            });
        }
    );
}

// MAIN LIST VIEW SETTINGS
frappe.listview_settings['AI Inventory Forecast'] = {
    add_fields: ['company', 'current_stock', 'reorder_level', 'confidence_score', 'movement_type', 'last_forecast_date', 'reorder_alert'],
    hide_name_column: true,

    onload: function(listview) {
        add_ai_forecast_styles();
        setTimeout(() => {
            add_ai_forecast_status_banner(listview);
        }, 500);
        
        listview.page.add_menu_item(__("🔄 Sync All"), function() {
            sync_all_forecasts_from_list();
        });
    },

    refresh: function(listview) {
        setTimeout(() => {
            if (!$('#ai-forecast-status-banner').length) {
                add_ai_forecast_status_banner(listview);
            }
            refresh_ai_status(listview);
        }, 300);
    },

    formatters: {
        movement_type: function(value) {
            if (value === 'Fast Moving') {
                return '<span style="color: green; font-weight: bold;">Fast Moving</span>';
            } else if (value === 'Slow Moving') {
                return '<span style="color: orange; font-weight: bold;">Slow Moving</span>';
            } else if (value === 'Non Moving') {
                return '<span style="color: red; font-weight: bold;">Non Moving</span>';
            } else if (value === 'Critical') {
                return '<span style="color: purple; font-weight: bold;">Critical</span>';
            } else {
                return '<span style="color: grey;">Unknown</span>';
            }
        },
        
        company: function(value) {
            if (value) {
                return '<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">' + value + '</span>';
            }
            return '<span style="color: red;">No Company</span>';
        },
        
        confidence_score: function(value) {
            if (value > 80) {
                return '<span style="color: green; font-weight: bold;">' + value + '%</span>';
            } else if (value > 60) {
                return '<span style="color: orange; font-weight: bold;">' + value + '%</span>';
            } else if (value > 0) {
                return '<span style="color: red; font-weight: bold;">' + value + '%</span>';
            }
            return '<span style="color: grey;">-</span>';
        }
    }
};

// INDICATOR FUNCTION
frappe.get_indicator = function(doc, doctype) {
    if (doctype === 'AI Inventory Forecast') {
        if (doc.reorder_alert) {
            return [__("🚨 REORDER ALERT"), "red", "reorder_alert,=,1"];
        } else if (doc.movement_type === "Critical") {
            return [__("🔴 Critical"), "purple", "movement_type,=,Critical"];
        } else if (doc.movement_type === "Fast Moving") {
            return [__("🟢 Fast Moving"), "green", "movement_type,=,Fast Moving"];
        } else if (doc.movement_type === "Slow Moving") {
            return [__("🟡 Slow Moving"), "orange", "movement_type,=,Slow Moving"];
        } else if (doc.movement_type === "Non Moving") {
            return [__("🔴 Non Moving"), "red", "movement_type,=,Non Moving"];
        } else {
            return [__("⚪ Unknown"), "grey", "movement_type,=,"];
        }
    }
};