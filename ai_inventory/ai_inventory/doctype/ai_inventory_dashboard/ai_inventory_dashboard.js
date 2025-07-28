// ai_inventory/ai_inventory/doctype/ai_settings/ai_settings.js
// CORRECTED VERSION - WITH Bulk Purchase Button

frappe.ui.form.on('AI Inventory Dashboard', {
    refresh: function(frm) {
        // Sync buttons group
        frm.add_custom_button(__('🔄 Sync Now'), function() {
            sync_ai_forecasts_now(frm);
        }, __('AI Forecast'));
        
        frm.add_custom_button(__('📊 View Status'), function() {
            show_sync_status_dialog(frm);
        }, __('AI Forecast'));
        
        // Bulk creation buttons group
        frm.add_custom_button(__('📦 Create for All Items'), function() {
            bulk_create_for_all_items(frm);
        }, __('Bulk Creation'));
        
        frm.add_custom_button(__('📈 Create for Items with Stock'), function() {
            bulk_create_for_items_with_stock(frm);
        }, __('Bulk Creation'));
        
        // Bulk Purchase Order button group - RESTORED
        frm.add_custom_button(__('📋 Bulk Purchase Orders'), function() {
            bulk_create_purchase_orders(frm);
        }, __('Purchase Orders'));
        
        frm.add_custom_button(__('🔄 Enable Auto PO'), function() {
            bulk_enable_auto_purchase_orders(frm);
        }, __('Purchase Orders'));
        
        // ML Analysis buttons group
        frm.add_custom_button(__('🤖 Run ML Analysis'), function() {
            run_ml_supplier_analysis(frm);
        }, __('ML Analysis'));
        
        frm.add_custom_button(__('📊 Supplier Analytics'), function() {
            show_supplier_analytics_summary(frm);
        }, __('ML Analysis'));
        
        // Show setup status
        display_setup_status(frm);
        
        // Add Fix button for missing forecasts
        frm.add_custom_button(__('🔧 Fix Missing Forecasts'), function() {
            fix_missing_forecasts(frm);
        }, __('Maintenance'));
        
        frm.add_custom_button(__('📊 Check Coverage'), function() {
            check_forecast_coverage_dialog(frm);
        }, __('Maintenance'));
    }
});

function fix_missing_forecasts(frm) {
    frappe.confirm(__('This will create AI Inventory Forecasts for all items that don\'t have them. This may take several minutes. Continue?'), function() {
        frappe.show_alert({
            message: __('Creating missing forecasts...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.fix_item_forecast_creation',
            callback: function(r) {
                if (r.message) {
                    if (r.message.status === 'success') {
                        let msg = `<strong>${r.message.message}</strong><br><br>`;
                        
                        if (r.message.creation_details) {
                            let details = r.message.creation_details;
                            msg += `<strong>Creation Details:</strong><br>
                                   Items Processed: ${details.total_items || 0}<br>
                                   Warehouses: ${details.total_warehouses || 0}<br>
                                   Forecasts Created: ${details.forecasts_created || 0}<br>`;
                            
                            if (details.company_summary) {
                                msg += `Company Breakdown: ${details.company_summary}<br>`;
                            }
                        }
                        
                        if (r.message.after_coverage) {
                            let coverage = r.message.after_coverage;
                            msg += `<br><strong>New Coverage:</strong> ${coverage.coverage_percentage}% 
                                   (${coverage.total_forecasts} of ${coverage.total_possible_combinations} possible)`;
                        }
                        
                        frappe.msgprint({
                            title: __('Missing Forecasts Fixed'),
                            message: msg,
                            wide: true,
                            indicator: 'green'
                        });
                        
                        frappe.show_alert({
                            message: __('Missing forecasts created successfully!'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Fix Failed'),
                            message: r.message.message,
                            indicator: 'red'
                        });
                    }
                }
            },
            error: function(r) {
                frappe.msgprint({
                    title: __('Fix Error'),
                    message: 'Failed to create missing forecasts. Please check error logs.',
                    indicator: 'red'
                });
            }
        });
    });
}

function check_forecast_coverage_dialog(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.check_forecast_coverage',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let coverage = r.message;
                
                let message = `
                    <h4>AI Inventory Forecast Coverage Report</h4>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Total Stock Items:</strong></td>
                            <td>${coverage.total_items}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Warehouses:</strong></td>
                            <td>${coverage.total_warehouses}</td>
                        </tr>
                        <tr>
                            <td><strong>Possible Combinations:</strong></td>
                            <td>${coverage.total_possible_combinations}</td>
                        </tr>
                        <tr>
                            <td><strong>Existing Forecasts:</strong></td>
                            <td style="color: blue; font-weight: bold;">${coverage.total_forecasts}</td>
                        </tr>
                        <tr>
                            <td><strong>Coverage Percentage:</strong></td>
                            <td style="color: ${coverage.coverage_percentage > 80 ? 'green' : coverage.coverage_percentage > 50 ? 'orange' : 'red'}; font-weight: bold;">
                                ${coverage.coverage_percentage}%
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Missing Forecasts:</strong></td>
                            <td style="color: ${coverage.missing_forecasts > 0 ? 'red' : 'green'}; font-weight: bold;">
                                ${coverage.missing_forecasts}
                            </td>
                        </tr>
                    </table>
                `;
                
                if (coverage.company_stats && coverage.company_stats.length > 0) {
                    message += `
                        <h5>Company Breakdown:</h5>
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Company</th>
                                    <th>Forecasts</th>
                                    <th>Unique Items</th>
                                    <th>Warehouses</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    coverage.company_stats.forEach(stat => {
                        message += `
                            <tr>
                                <td><strong>${stat.company}</strong></td>
                                <td>${stat.forecast_count}</td>
                                <td>${stat.unique_items}</td>
                                <td>${stat.unique_warehouses}</td>
                            </tr>
                        `;
                    });
                    
                    message += `
                            </tbody>
                        </table>
                    `;
                }
                
                if (coverage.missing_forecasts > 0) {
                    message += `
                        <div class="alert alert-warning">
                            <strong>Action Needed:</strong> ${coverage.missing_forecasts} forecasts are missing. 
                            Use the "Fix Missing Forecasts" button to create them.
                        </div>
                    `;
                } else {
                    message += `
                        <div class="alert alert-success">
                            <strong>All Good:</strong> All possible item-warehouse combinations have forecasts!
                        </div>
                    `;
                }
                
                frappe.msgprint({
                    title: __('Forecast Coverage Report'),
                    message: message,
                    wide: true
                });
            } else {
                frappe.msgprint({
                    title: __('Coverage Check Failed'),
                    message: r.message?.message || 'Failed to check forecast coverage',
                    indicator: 'red'
                });
            }
        }
    });
}

function sync_ai_forecasts_now(frm) {
    frappe.confirm(__('This will run AI forecasting for all active items. Continue?'), function() {
        frappe.show_alert({
            message: __('Starting AI Forecast Sync...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_forecasts_now',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Sync Results'),
                        message: `<strong>${r.message.message}</strong><br>
                                 Total: ${r.message.total_items || 0}<br>
                                 Successful: ${r.message.successful || 0}<br>
                                 Failed: ${r.message.failed || 0}<br>
                                 Success Rate: ${r.message.success_rate || 0}%`,
                        wide: true
                    });
                    
                    if (r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('AI Forecast sync completed successfully!'),
                            indicator: 'green'
                        });
                    }
                }
            }
        });
    });
}

function show_sync_status_dialog(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.get_simple_sync_status',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let stats = r.message.current_stats || {};
                
                let message = `
                    <h4>AI Forecast Status</h4>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Total Forecasts:</strong></td>
                            <td>${stats.total_forecasts || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Reorder Alerts:</strong></td>
                            <td style="color: red;">${stats.current_alerts || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Updated Today:</strong></td>
                            <td>${stats.updated_today || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Avg Confidence:</strong></td>
                            <td>${(stats.avg_confidence || 0).toFixed(1)}%</td>
                        </tr>
                    </table>
                `;
                
                frappe.msgprint({
                    title: __('AI Forecast Status'),
                    message: message,
                    wide: true
                });
            }
        }
    });
}

function bulk_create_for_all_items(frm) {
    frappe.confirm(__('Create forecasts for ALL stock items? This may take several minutes.'), function() {
        frappe.call({
            method: 'ai_inventory.hooks_handlers.bulk_create_forecasts_for_existing_items',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Bulk Creation Complete'),
                        message: r.message.message,
                        indicator: r.message.status === 'success' ? 'green' : 'red'
                    });
                }
            }
        });
    });
}

function bulk_create_for_items_with_stock(frm) {
    frappe.confirm(__('Create forecasts only for items with stock? This is recommended.'), function() {
        frappe.call({
            method: 'ai_inventory.hooks_handlers.auto_create_forecasts_for_items_with_stock',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Selective Creation Complete'),
                        message: r.message.message,
                        indicator: r.message.status === 'success' ? 'green' : 'red'
                    });
                }
            }
        });
    });
}

// RESTORED: Bulk Purchase Order Functions
function bulk_create_purchase_orders(frm) {
    frappe.confirm(__('This will create Purchase Orders for all items with reorder alerts. Continue?'), function() {
        frappe.show_alert({
            message: __('Creating bulk purchase orders...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.bulk_create_purchase_orders',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Bulk Purchase Orders'),
                        message: `<strong>${r.message.message}</strong><br>
                                 Purchase Orders Created: ${r.message.pos_created || 0}<br>
                                 Items Processed: ${r.message.items_processed || 0}<br>
                                 Failed: ${r.message.failed || 0}`,
                        wide: true,
                        indicator: r.message.status === 'success' ? 'green' : 'orange'
                    });
                    
                    if (r.message.pos_created > 0) {
                        frappe.show_alert({
                            message: __('Created {0} Purchase Orders successfully!', [r.message.pos_created]),
                            indicator: 'green'
                        });
                    }
                }
            }
        });
    });
}

function bulk_enable_auto_purchase_orders(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Enable Auto Purchase Orders'),
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'company',
                label: __('Company (Optional)'),
                options: 'Company',
                get_query: function() {
                    return {
                        filters: {}
                    };
                }
            },
            {
                fieldtype: 'MultiSelectList',
                fieldname: 'movement_types',
                label: __('Movement Types'),
                options: [
                    { "value": "Fast Moving", "description": "Fast Moving Items" },
                    { "value": "Slow Moving", "description": "Slow Moving Items" },
                    { "value": "Critical", "description": "Critical Items" }
                ],
                default: ["Fast Moving", "Critical"]
            },
            {
                fieldtype: 'HTML',
                fieldname: 'help_text',
                options: `
                    <div class="alert alert-info">
                        <strong>Auto Purchase Orders:</strong><br>
                        This will enable automatic purchase order creation for selected movement types.
                        Only items with preferred suppliers will be enabled.
                    </div>
                `
            }
        ],
        primary_action_label: __('Enable Auto PO'),
        primary_action: function(values) {
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.bulk_enable_auto_po',
                args: {
                    company: values.company,
                    movement_types: values.movement_types
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Auto PO Enabled'),
                            message: r.message.message,
                            indicator: r.message.status === 'success' ? 'green' : 'orange'
                        });
                        dialog.hide();
                    }
                }
            });
        }
    });
    
    dialog.show();
}

// REPLACE the existing run_ml_supplier_analysis function with this version
function run_ml_supplier_analysis(frm) {
    // Prevent multiple dialogs
    if (window.ml_analysis_dialog_open) {
        frappe.show_alert({
            message: __('ML Analysis dialog is already open'),
            indicator: 'orange'
        });
        return;
    }
    
    window.ml_analysis_dialog_open = true;
    
    console.log("🔍 Starting ML analysis with company selection...");
    
    // Simple direct approach - get companies and show dialog immediately
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Company',
            fields: ['name'],
            limit_page_length: 0
        },
        callback: function(companies_result) {
            if (!companies_result.message || companies_result.message.length === 0) {
                window.ml_analysis_dialog_open = false;
                frappe.msgprint({
                    title: __('No Companies Found'),
                    message: __('No companies found. Please create a company first.'),
                    indicator: 'red'
                });
                return;
            }
            
            // Show simplified company selection dialog
            show_simple_company_dialog(companies_result.message);
        },
        error: function() {
            window.ml_analysis_dialog_open = false;
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to load companies. Please try again.'),
                indicator: 'red'
            });
        }
    });
}

// Add these helper functions after the main function
function show_simple_company_dialog(companies) {
    let dialog = new frappe.ui.Dialog({
        title: __('🏢 Select Company for ML Analysis'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'company',
                label: __('Company'),
                options: companies.map(c => c.name).join('\n'),
                reqd: 1,
                default: companies.length > 0 ? companies[0].name : ''
            },
            {
                fieldtype: 'HTML',
                fieldname: 'info',
                options: `
                    <div class="alert alert-info" style="margin-top: 15px;">
                        <h6><i class="fa fa-info-circle"></i> ML Supplier Analysis</h6>
                        <p>This will analyze supplier performance based on purchase order history for the selected company.</p>
                        <ul>
                            <li>Requires existing purchase orders</li>
                            <li>Analyzes delivery performance, pricing, and reliability</li>
                            <li>Updates supplier risk and performance scores</li>
                        </ul>
                    </div>
                `
            }
        ],
        primary_action_label: __('🤖 Run Analysis'),
        primary_action: function(values) {
            if (!values.company) {
                frappe.msgprint(__('Please select a company'));
                return;
            }
            
            dialog.hide();
            window.ml_analysis_dialog_open = false;
            
            // Run analysis for selected company
            run_analysis_for_company(values.company);
        }
    });
    
    // Set flag to false when dialog is hidden
    dialog.$wrapper.on('hidden.bs.modal', function() {
        window.ml_analysis_dialog_open = false;
    });
    
    dialog.show();
}

function run_analysis_for_company(company) {
    frappe.show_alert({
        message: __('Starting ML analysis for {0}...', [company]),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'ai_inventory.ml_supplier_analyzer.run_ml_supplier_analysis',
        args: {
            company: company
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('✅ ML Analysis Complete'),
                        message: `
                            <div class="alert alert-success">
                                <h4>${r.message.message}</h4>
                                <p><strong>Company:</strong> ${company}</p>
                                <p><strong>Suppliers Analyzed:</strong> ${r.message.suppliers_analyzed || 0}</p>
                                <p><strong>Suppliers Updated:</strong> ${r.message.suppliers_updated || 0}</p>
                            </div>
                        `,
                        wide: true
                    });
                    
                    frappe.show_alert({
                        message: __('✅ ML analysis completed for {0}!', [company]),
                        indicator: 'green'
                    });
                    
                } else if (r.message.status === 'info') {
                    frappe.msgprint({
                        title: __('📊 No Data Found'),
                        message: `
                            <div class="alert alert-warning">
                                <h4>${r.message.message}</h4>
                                <p><strong>To enable ML analysis for ${company}:</strong></p>
                                <ol>
                                    <li>Create suppliers (Buying → Supplier)</li>
                                    <li>Create purchase orders (Buying → Purchase Order)</li>
                                    <li>Submit the purchase orders</li>
                                    <li>Run ML analysis again</li>
                                </ol>
                            </div>
                        `,
                        wide: true,
                        indicator: 'orange'
                    });
                } else {
                    frappe.msgprint({
                        title: __('❌ Analysis Error'),
                        message: r.message.message,
                        indicator: 'red'
                    });
                }
            }
        },
        error: function() {
            frappe.msgprint({
                title: __('❌ Error'),
                message: 'ML analysis failed. Please check the error logs.',
                indicator: 'red'
            });
        }
    });
}

function show_supplier_analytics_summary(frm) {
    frappe.call({
        method: 'ai_inventory.ml_supplier_analyzer.get_supplier_analytics_summary',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let segments = r.message.supplier_segments || [];
                let recent_updates = r.message.recent_updates || 0;
                
                let message = `
                    <h4>Supplier Analytics Summary</h4>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Segment</th>
                                <th>Count</th>
                                <th>Avg Score</th>
                                <th>Avg Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (segments.length > 0) {
                    segments.forEach(segment => {
                        message += `
                            <tr>
                                <td><strong>${segment.supplier_segment || 'Unknown'}</strong></td>
                                <td>${segment.count || 0}</td>
                                <td>${(segment.avg_score || 0).toFixed(1)}%</td>
                                <td>${(segment.avg_risk || 0).toFixed(1)}%</td>
                            </tr>
                        `;
                    });
                } else {
                    message += `
                        <tr>
                            <td colspan="4" class="text-center">No supplier analytics available. Run ML analysis first.</td>
                        </tr>
                    `;
                }
                
                message += `
                        </tbody>
                    </table>
                    <p><strong>Recent Updates (Last 7 days):</strong> ${recent_updates} suppliers</p>
                `;
                
                frappe.msgprint({
                    title: __('Supplier Analytics Summary'),
                    message: message,
                    wide: true
                });
            } else {
                frappe.msgprint({
                    title: __('No Analytics Available'),
                    message: 'No supplier analytics data available. Please run ML analysis first.',
                    indicator: 'orange'
                });
            }
        }
    });
}

function display_setup_status(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.get_setup_status',
        args: {
            company: frm.doc.company || ''
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let setup = r.message.setup_status;
                frm.dashboard.clear_comment();
                
                // Coverage indicators
                if (setup.total_items === 0) {
                    frm.dashboard.add_comment(
                        __('⚠️ No stock items found. Please check item master.'),
                        'orange',
                        true
                    );
                } else {
                    if (setup.forecast_coverage >= 80) {
                        frm.dashboard.add_comment(
                            __('✅ Good forecast coverage: {0}% ({1} of {2} items)', 
                                [setup.forecast_coverage, setup.total_forecasts, setup.total_items]),
                            'green',
                            true
                        );
                    } else if (setup.forecast_coverage < 50) {
                        frm.dashboard.add_comment(
                            __('⚠️ Low forecast coverage: {0}% ({1} of {2} items)', 
                                [setup.forecast_coverage, setup.total_forecasts, setup.total_items]),
                            'orange',
                            true
                        );
                    }
                }
                
                // Reorder alerts
                if (setup.reorder_alerts > 0) {
                    frm.dashboard.add_comment(
                        __('🔔 {0} items need reordering', [setup.reorder_alerts]),
                        'red',
                        true
                    );
                }
                
                // System issues
                if (setup.issues && setup.issues.length > 0) {
                    setup.issues.forEach(issue => {
                        frm.dashboard.add_comment(
                            __('❌ {0}', [issue]),
                            'red',
                            true
                        );
                    });
                }
                
                // Recommendations
                if (setup.recommendations && setup.recommendations.length > 0) {
                    setup.recommendations.forEach(rec => {
                        frm.dashboard.add_comment(
                            __('💡 {0}', [rec]),
                            'blue',
                            true
                        );
                    });
                }
            }
        }
    });
}