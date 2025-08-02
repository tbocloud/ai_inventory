// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on('AI Sales Dashboard', {
    refresh: function(frm) {
        // Manual Sync buttons group
        frm.add_custom_button(__('🔄 Sync Now'), function() {
            sync_ai_sales_forecasts_now(frm);
        }, __('AI Sales Forecast'));
        
        frm.add_custom_button(__('📊 View Status'), function() {
            show_sales_sync_status_dialog(frm);
        }, __('AI Sales Forecast'));
        
        // Bulk creation buttons group
        frm.add_custom_button(__('📦 Create for All Customers'), function() {
            bulk_create_for_all_customers(frm);
        }, __('Bulk Creation'));
        
        frm.add_custom_button(__('📈 Create for Recent Customers'), function() {
            bulk_create_for_recent_customers(frm);
        }, __('Bulk Creation'));
        
        // Purchase Order buttons group - NEW AI-POWERED FEATURE
        frm.add_custom_button(__('📦 Bulk Purchase Orders'), function() {
            create_bulk_purchase_orders_from_ai(frm);
        }, __('🤖 AI Purchase Orders'));
        
        frm.add_custom_button(__('📊 Purchase Insights'), function() {
            show_purchase_order_ai_insights(frm);
        }, __('🤖 AI Purchase Orders'));
        
        frm.add_custom_button(__('🎯 Smart Procurement'), function() {
            show_smart_procurement_dialog(frm);
        }, __('🤖 AI Purchase Orders'));
        
        // Sales Order buttons group
        frm.add_custom_button(__('📋 Bulk Sales Orders'), function() {
            bulk_create_sales_orders(frm);
        }, __('Sales Orders'));
        
        frm.add_custom_button(__('🔄 Enable Auto SO'), function() {
            bulk_enable_auto_sales_orders(frm);
        }, __('Sales Orders'));
        
        // Analytics buttons group
        frm.add_custom_button(__('📊 Sales Analytics'), function() {
            show_sales_analytics_summary(frm);
        }, __('Analytics'));
        
        frm.add_custom_button(__('🎯 Customer Insights'), function() {
            show_customer_insights(frm);
        }, __('Analytics'));
        
        // Show setup status
        display_sales_setup_status(frm);
        
        // Maintenance buttons
        frm.add_custom_button(__('🔧 Fix Missing Forecasts'), function() {
            fix_missing_sales_forecasts(frm);
        }, __('Maintenance'));
        
        frm.add_custom_button(__('📊 Check Coverage'), function() {
            check_sales_forecast_coverage_dialog(frm);
        }, __('Maintenance'));
    }
});

function sync_ai_sales_forecasts_now(frm) {
    frappe.confirm(__('This will run AI sales forecasting for all active items and customers. Continue?'), function() {
        frappe.show_alert({
            message: __('Starting AI Sales Forecast Sync...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.sync_ai_sales_forecasts_now',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Sales Forecast Sync Results'),
                        message: `<strong>${r.message.message}</strong><br>
                                 Total: ${r.message.total_items || 0}<br>
                                 Successful: ${r.message.successful || 0}<br>
                                 Failed: ${r.message.failed || 0}<br>
                                 Success Rate: ${r.message.success_rate || 0}%<br>
                                 High-Confidence Forecasts: ${r.message.high_confidence_count || 0}`,
                        wide: true
                    });
                    
                    if (r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('AI Sales Forecast sync completed successfully!'),
                            indicator: 'green'
                        });
                    }
                }
            }
        });
    });
}

function show_sales_sync_status_dialog(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.get_sales_sync_status',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let stats = r.message.current_stats || {};
                
                let message = `
                    <h4>AI Sales Forecast Status</h4>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Total Forecasts:</strong></td>
                            <td>${stats.total_forecasts || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>High-Confidence Forecasts:</strong></td>
                            <td style="color: green;">${stats.high_confidence || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Updated Today:</strong></td>
                            <td>${stats.updated_today || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Avg Confidence:</strong></td>
                            <td>${(stats.avg_confidence || 0).toFixed(1)}%</td>
                        </tr>
                        <tr>
                            <td><strong>Unique Customers:</strong></td>
                            <td>${stats.unique_customers || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Unique Items:</strong></td>
                            <td>${stats.unique_items || 0}</td>
                        </tr>
                    </table>
                `;
                
                frappe.msgprint({
                    title: __('AI Sales Forecast Status'),
                    message: message,
                    wide: true
                });
            }
        }
    });
}

function bulk_create_for_all_customers(frm) {
    frappe.confirm(__('Create sales forecasts for ALL customers and items? This may take several minutes.'), function() {
        frappe.show_alert({
            message: __('Creating forecasts for all customers...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.create_forecasts_for_all_customers',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Bulk Creation Complete'),
                        message: `<strong>${r.message.message}</strong><br>
                                 Forecasts Created: ${r.message.forecasts_created || 0}<br>
                                 Customers Processed: ${r.message.customers_processed || 0}<br>
                                 Items Processed: ${r.message.items_processed || 0}`,
                        indicator: r.message.status === 'success' ? 'green' : 'red'
                    });
                }
            }
        });
    });
}

function bulk_create_for_recent_customers(frm) {
    frappe.confirm(__('Create forecasts only for customers with recent sales (last 90 days)? Recommended for better accuracy.'), function() {
        frappe.show_alert({
            message: __('Creating forecasts for recent customers...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.create_forecasts_for_recent_customers',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Selective Creation Complete'),
                        message: `<strong>${r.message.message}</strong><br>
                                 Forecasts Created: ${r.message.forecasts_created || 0}<br>
                                 Recent Customers: ${r.message.recent_customers || 0}<br>
                                 Items Processed: ${r.message.items_processed || 0}`,
                        indicator: r.message.status === 'success' ? 'green' : 'red'
                    });
                }
            }
        });
    });
}

function bulk_create_sales_orders(frm) {
    frappe.confirm(__('This will create Sales Orders for high-confidence forecasts. Continue?'), function() {
        frappe.show_alert({
            message: __('Creating bulk sales orders...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.bulk_create_sales_orders',
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Bulk Sales Orders'),
                        message: `<strong>${r.message.message}</strong><br>
                                 Sales Orders Created: ${r.message.orders_created || 0}<br>
                                 Items Processed: ${r.message.items_processed || 0}<br>
                                 Failed: ${r.message.failed || 0}`,
                        wide: true,
                        indicator: r.message.status === 'success' ? 'green' : 'orange'
                    });
                    
                    if (r.message.orders_created > 0) {
                        frappe.show_alert({
                            message: __('Created {0} Sales Orders successfully!', [r.message.orders_created]),
                            indicator: 'green'
                        });
                    }
                }
            }
        });
    });
}

function bulk_enable_auto_sales_orders(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Enable Auto Sales Orders'),
        fields: [
            {
                fieldtype: 'Percent',
                fieldname: 'confidence_threshold',
                label: __('Minimum Confidence Threshold'),
                default: 85,
                description: __('Only forecasts above this confidence will trigger auto-creation')
            },
            {
                fieldtype: 'Int',
                fieldname: 'min_quantity',
                label: __('Minimum Quantity'),
                default: 1,
                description: __('Minimum predicted quantity to create sales order')
            },
            {
                fieldtype: 'HTML',
                fieldname: 'help_text',
                options: `
                    <div class="alert alert-info">
                        <strong>Auto Sales Orders:</strong><br>
                        This will enable automatic sales order creation for high-confidence forecasts.
                        Only forecasts meeting both confidence and quantity thresholds will trigger orders.
                    </div>
                `
            }
        ],
        primary_action_label: __('Enable Auto SO'),
        primary_action: function(values) {
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.bulk_enable_auto_so',
                args: {
                    confidence_threshold: values.confidence_threshold,
                    min_quantity: values.min_quantity
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Auto SO Enabled'),
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

function show_sales_analytics_summary(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.get_sales_analytics_summary',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let analytics = r.message.analytics || {};
                
                let message = `
                    <h4>Sales Forecast Analytics Summary</h4>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Total Revenue Forecast:</strong></td>
                            <td style="color: green; font-weight: bold;">₹${(analytics.total_revenue_forecast || 0).toLocaleString()}</td>
                        </tr>
                        <tr>
                            <td><strong>High-Confidence Revenue:</strong></td>
                            <td style="color: blue;">₹${(analytics.high_confidence_revenue || 0).toLocaleString()}</td>
                        </tr>
                        <tr>
                            <td><strong>Top Performing Items:</strong></td>
                            <td>${analytics.top_items || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Active Customers:</strong></td>
                            <td>${analytics.active_customers || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Forecast Accuracy (Last Month):</strong></td>
                            <td>${(analytics.accuracy_last_month || 0).toFixed(1)}%</td>
                        </tr>
                    </table>
                `;
                
                if (analytics.top_customer_forecasts && analytics.top_customer_forecasts.length > 0) {
                    message += `
                        <h5>Top Customer Forecasts:</h5>
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Customer</th>
                                    <th>Predicted Qty</th>
                                    <th>Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    analytics.top_customer_forecasts.forEach(forecast => {
                        message += `
                            <tr>
                                <td><strong>${forecast.customer}</strong></td>
                                <td>${forecast.predicted_qty}</td>
                                <td>${forecast.confidence_score}%</td>
                            </tr>
                        `;
                    });
                    
                    message += `
                            </tbody>
                        </table>
                    `;
                }
                
                frappe.msgprint({
                    title: __('Sales Analytics Summary'),
                    message: message,
                    wide: true
                });
            } else {
                frappe.msgprint({
                    title: __('No Analytics Available'),
                    message: 'No sales analytics data available. Please run sales forecast sync first.',
                    indicator: 'orange'
                });
            }
        }
    });
}

function show_customer_insights(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Customer Insights'),
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'customer',
                label: __('Select Customer'),
                options: 'Customer',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {}
                    };
                }
            }
        ],
        primary_action_label: __('Get Insights'),
        primary_action: function(values) {
            if (!values.customer) {
                frappe.msgprint(__('Please select a customer'));
                return;
            }
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.get_customer_insights',
                args: {
                    customer: values.customer
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        let insights = r.message.insights;
                        
                        let message = `
                            <h4>Customer Insights: ${values.customer}</h4>
                            <table class="table table-bordered">
                                <tr>
                                    <td><strong>Total Forecasts:</strong></td>
                                    <td>${insights.total_forecasts || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>Avg Confidence:</strong></td>
                                    <td>${(insights.avg_confidence || 0).toFixed(1)}%</td>
                                </tr>
                                <tr>
                                    <td><strong>Total Predicted Quantity:</strong></td>
                                    <td>${insights.total_predicted_qty || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>Last Purchase Date:</strong></td>
                                    <td>${insights.last_purchase_date || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <td><strong>Purchase Frequency:</strong></td>
                                    <td>${insights.purchase_frequency || 'Unknown'}</td>
                                </tr>
                            </table>
                        `;
                        
                        frappe.msgprint({
                            title: __('Customer Insights'),
                            message: message,
                            wide: true
                        });
                    }
                }
            });
            
            dialog.hide();
        }
    });
    
    dialog.show();
}

function fix_missing_sales_forecasts(frm) {
    frappe.confirm(__('This will create AI Sales Forecasts for customers and items that don\'t have them. Continue?'), function() {
        frappe.show_alert({
            message: __('Creating missing sales forecasts...'),
            indicator: 'blue'
        });
        
        frappe.call({
            method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.fix_missing_sales_forecasts',
            callback: function(r) {
                if (r.message) {
                    if (r.message.status === 'success') {
                        frappe.msgprint({
                            title: __('Missing Forecasts Fixed'),
                            message: `<strong>${r.message.message}</strong><br>
                                     Forecasts Created: ${r.message.forecasts_created || 0}<br>
                                     Customers Processed: ${r.message.customers_processed || 0}<br>
                                     Items Processed: ${r.message.items_processed || 0}`,
                            wide: true,
                            indicator: 'green'
                        });
                        
                        frappe.show_alert({
                            message: __('Missing sales forecasts created successfully!'),
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
            }
        });
    });
}

function check_sales_forecast_coverage_dialog(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.check_sales_forecast_coverage',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let coverage = r.message;
                
                let message = `
                    <h4>AI Sales Forecast Coverage Report</h4>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Total Customers:</strong></td>
                            <td>${coverage.total_customers}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Sales Items:</strong></td>
                            <td>${coverage.total_items}</td>
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
                            <strong>All Good:</strong> All possible customer-item combinations have forecasts!
                        </div>
                    `;
                }
                
                frappe.msgprint({
                    title: __('Sales Forecast Coverage Report'),
                    message: message,
                    wide: true
                });
            } else {
                frappe.msgprint({
                    title: __('Coverage Check Failed'),
                    message: r.message?.message || 'Failed to check sales forecast coverage',
                    indicator: 'red'
                });
            }
        }
    });
}

function display_sales_setup_status(frm) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.get_sales_setup_status',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let setup = r.message.setup_status;
                frm.dashboard.clear_comment();
                
                // Coverage indicators
                if (setup.total_customers === 0) {
                    frm.dashboard.add_comment(
                        __('⚠️ No customers found. Please create customers first.'),
                        'orange',
                        true
                    );
                } else if (setup.total_items === 0) {
                    frm.dashboard.add_comment(
                        __('⚠️ No sales items found. Please check item master.'),
                        'orange',
                        true
                    );
                } else {
                    if (setup.forecast_coverage >= 80) {
                        frm.dashboard.add_comment(
                            __('✅ Good forecast coverage: {0}% ({1} forecasts)', 
                                [setup.forecast_coverage, setup.total_forecasts]),
                            'green',
                            true
                        );
                    } else if (setup.forecast_coverage < 50) {
                        frm.dashboard.add_comment(
                            __('⚠️ Low forecast coverage: {0}% ({1} forecasts)', 
                                [setup.forecast_coverage, setup.total_forecasts]),
                            'orange',
                            true
                        );
                    }
                }
                
                // High-confidence forecasts
                if (setup.high_confidence_forecasts > 0) {
                    frm.dashboard.add_comment(
                        __('🎯 {0} high-confidence forecasts available', [setup.high_confidence_forecasts]),
                        'green',
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

// ============== AI-POWERED PURCHASE ORDER FUNCTIONS ==============

function create_bulk_purchase_orders_from_ai(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('🤖 AI-Powered Bulk Purchase Orders'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'ai_intro',
                options: `
                    <div class="alert alert-info">
                        <h5><i class="fa fa-robot"></i> AI-Powered Procurement</h5>
                        <p>This feature uses <strong>Machine Learning algorithms</strong> to analyze your sales forecasts and automatically create optimized Purchase Orders.</p>
                        <ul>
                            <li>🎯 <strong>AI Analytics:</strong> Uses sales predictions and movement patterns</li>
                            <li>📊 <strong>Smart Quantities:</strong> Calculates optimal order quantities</li>
                            <li>🚨 <strong>Urgency Detection:</strong> Identifies critical stock situations</li>
                            <li>🔄 <strong>Supplier Optimization:</strong> Groups by best suppliers</li>
                        </ul>
                    </div>
                `
            },
            {
                fieldtype: 'Link',
                fieldname: 'company',
                label: __('Company'),
                options: 'Company',
                default: frappe.defaults.get_user_default('Company'),
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'territory',
                label: __('Territory (Optional)'),
                options: 'Territory',
                description: __('Filter by territory for focused procurement')
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Percent',
                fieldname: 'min_confidence',
                label: __('Minimum AI Confidence %'),
                default: 70,
                description: __('Only create POs for forecasts above this confidence level')
            },
            {
                fieldtype: 'Float',
                fieldname: 'min_predicted_qty',
                label: __('Minimum Predicted Quantity'),
                default: 1,
                description: __('Only include items with minimum predicted demand')
            },
            {
                fieldtype: 'Section Break',
                label: __('AI Analysis Options')
            },
            {
                fieldtype: 'Check',
                fieldname: 'prioritize_critical',
                label: __('Prioritize Critical Items'),
                default: 1,
                description: __('Give priority to items flagged as critical by AI')
            },
            {
                fieldtype: 'Check',
                fieldname: 'include_safety_stock',
                label: __('Include AI Safety Stock'),
                default: 1,
                description: __('Add intelligent safety stock calculations')
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Check',
                fieldname: 'group_by_supplier',
                label: __('Group by Supplier'),
                default: 1,
                description: __('Create separate POs for each supplier')
            },
            {
                fieldtype: 'Check',
                fieldname: 'auto_submit',
                label: __('Auto Submit POs'),
                default: 0,
                description: __('Automatically submit high-confidence POs')
            }
        ],
        size: 'large',
        primary_action_label: __('🚀 Create AI Purchase Orders'),
        primary_action: function(values) {
            frappe.show_alert({
                message: __('🤖 AI is analyzing sales forecasts and creating optimized Purchase Orders...'),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_dashboard.ai_sales_dashboard.create_bulk_purchase_orders_from_ai_analytics',
                args: {
                    filters: values
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        let result = r.message;
                        
                        // Show detailed results
                        let message = `
                            <div class="alert alert-success">
                                <h4><i class="fa fa-check-circle"></i> AI Purchase Orders Created Successfully!</h4>
                            </div>
                            <table class="table table-bordered">
                                <tr>
                                    <td><strong>Purchase Orders Created:</strong></td>
                                    <td style="color: green; font-weight: bold;">${result.purchase_orders_created}</td>
                                </tr>
                                <tr>
                                    <td><strong>Total Value:</strong></td>
                                    <td style="color: blue;">₹${(result.total_value || 0).toLocaleString()}</td>
                                </tr>
                                <tr>
                                    <td><strong>Failed Items:</strong></td>
                                    <td style="color: ${result.failed_items > 0 ? 'red' : 'green'};">${result.failed_items || 0}</td>
                                </tr>
                            </table>
                        `;
                        
                        // Add AI insights
                        if (result.ai_insights) {
                            let insights = result.ai_insights;
                            message += `
                                <h5><i class="fa fa-brain"></i> AI Insights</h5>
                                <table class="table table-striped">
                                    <tr><td>Items Analyzed:</td><td>${insights.total_items_analyzed || 0}</td></tr>
                                    <tr><td>High Confidence Items:</td><td>${insights.high_confidence_items || 0}</td></tr>
                                    <tr><td>Critical Items:</td><td style="color: red;">${insights.critical_items || 0}</td></tr>
                                    <tr><td>Average AI Confidence:</td><td>${insights.average_confidence || 0}%</td></tr>
                                    <tr><td>Suppliers Involved:</td><td>${insights.suppliers_involved || 0}</td></tr>
                                </table>
                            `;
                            
                            if (insights.recommendations && insights.recommendations.length > 0) {
                                message += `<h6>AI Recommendations:</h6><ul>`;
                                insights.recommendations.forEach(rec => {
                                    message += `<li>${rec}</li>`;
                                });
                                message += `</ul>`;
                            }
                        }
                        
                        // Show created POs
                        if (result.created_pos && result.created_pos.length > 0) {
                            message += `
                                <h5><i class="fa fa-file-text"></i> Created Purchase Orders</h5>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>PO Number</th>
                                            <th>Supplier</th>
                                            <th>Items</th>
                                            <th>Amount</th>
                                            <th>AI Confidence</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            `;
                            
                            result.created_pos.forEach(po => {
                                message += `
                                    <tr>
                                        <td><a href="/app/purchase-order/${po.name}" target="_blank">${po.name}</a></td>
                                        <td>${po.supplier}</td>
                                        <td>${po.total_qty}</td>
                                        <td>₹${po.total_amount?.toLocaleString()}</td>
                                        <td><span class="badge badge-${po.ai_confidence > 80 ? 'success' : po.ai_confidence > 60 ? 'warning' : 'danger'}">${po.ai_confidence}%</span></td>
                                    </tr>
                                `;
                            });
                            
                            message += `</tbody></table>`;
                        }
                        
                        frappe.msgprint({
                            title: __('🤖 AI Purchase Orders Results'),
                            message: message,
                            wide: true
                        });
                        
                        frappe.show_alert({
                            message: __('🎉 {0} AI-optimized Purchase Orders created successfully!', [result.purchase_orders_created]),
                            indicator: 'green'
                        });
                        
                    } else {
                        frappe.msgprint({
                            title: __('AI Purchase Order Creation Failed'),
                            message: r.message?.message || 'Failed to create Purchase Orders',
                            indicator: 'red'
                        });
                    }
                }
            });
            
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_purchase_order_ai_insights(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('📊 Purchase Order AI Insights'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'insights_intro',
                options: `
                    <div class="alert alert-info">
                        <h5><i class="fa fa-brain"></i> AI Purchase Insights</h5>
                        <p>Analyze AI Sales Forecast data to generate intelligent procurement recommendations and insights.</p>
                        <p><strong>💡 Tip:</strong> Leave Company blank for system-wide analysis across all companies.</p>
                    </div>
                `
            },
            {
                fieldtype: 'Link',
                fieldname: 'company',
                label: __('Company (Optional)'),
                options: 'Company',
                description: __('Leave blank for analysis across all companies')
            },
            {
                fieldtype: 'Link',
                fieldname: 'territory',
                label: __('Territory (Optional)'),
                options: 'Territory'
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Percent',
                fieldname: 'min_confidence',
                label: __('Minimum Confidence %'),
                default: 60
            }
        ],
        primary_action_label: __('🔍 Analyze'),
        primary_action: function(values) {
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_dashboard.ai_sales_dashboard.get_purchase_order_ai_insights',
                args: {
                    filters: values
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        let insights = r.message.insights;
                        
                        let message = `
                            <div class="alert alert-info">
                                <h4><i class="fa fa-brain"></i> AI Purchase Analysis</h4>
                            </div>
                            <table class="table table-bordered">
                                <tr>
                                    <td><strong>Items Analyzed:</strong></td>
                                    <td>${insights.total_items_analyzed || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>High Confidence Items:</strong></td>
                                    <td style="color: green;">${insights.high_confidence_items || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>Critical Items:</strong></td>
                                    <td style="color: red; font-weight: bold;">${insights.critical_items || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>Urgent Purchases Needed:</strong></td>
                                    <td style="color: orange;">${insights.urgent_purchases || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>Average AI Confidence:</strong></td>
                                    <td>${insights.average_confidence || 0}%</td>
                                </tr>
                                <tr>
                                    <td><strong>Suppliers Involved:</strong></td>
                                    <td>${insights.suppliers_involved || 0}</td>
                                </tr>
                                <tr>
                                    <td><strong>Total Predicted Demand:</strong></td>
                                    <td style="font-weight: bold;">${(insights.total_predicted_demand || 0).toLocaleString()}</td>
                                </tr>
                            </table>
                        `;
                        
                        // Supplier analysis
                        if (insights.supplier_analysis) {
                            message += `
                                <h5><i class="fa fa-users"></i> Supplier Analysis</h5>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Supplier</th>
                                            <th>Items</th>
                                            <th>Est. Value</th>
                                            <th>Avg Confidence</th>
                                            <th>Urgent Items</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            `;
                            
                            Object.keys(insights.supplier_analysis).forEach(supplier => {
                                let analysis = insights.supplier_analysis[supplier];
                                message += `
                                    <tr>
                                        <td><strong>${supplier}</strong></td>
                                        <td>${analysis.item_count}</td>
                                        <td>₹${(analysis.total_value || 0).toLocaleString()}</td>
                                        <td><span class="badge badge-${analysis.avg_confidence > 80 ? 'success' : analysis.avg_confidence > 60 ? 'warning' : 'danger'}">${analysis.avg_confidence}%</span></td>
                                        <td style="color: ${analysis.urgent_items > 0 ? 'red' : 'green'};">${analysis.urgent_items}</td>
                                    </tr>
                                `;
                            });
                            
                            message += `</tbody></table>`;
                        }
                        
                        // Top items
                        if (insights.top_items && insights.top_items.length > 0) {
                            message += `
                                <h5><i class="fa fa-star"></i> Top Purchase Opportunities</h5>
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Item</th>
                                            <th>Predicted Qty</th>
                                            <th>Confidence</th>
                                            <th>Urgency</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            `;
                            
                            insights.top_items.slice(0, 10).forEach(item => {
                                message += `
                                    <tr>
                                        <td><strong>${item.item_code}</strong></td>
                                        <td>${item.optimized_qty || 0}</td>
                                        <td><span class="badge badge-${item.confidence_score > 80 ? 'success' : item.confidence_score > 60 ? 'warning' : 'danger'}">${item.confidence_score}%</span></td>
                                        <td>${item.purchase_urgency || 'Normal'}</td>
                                    </tr>
                                `;
                            });
                            
                            message += `</tbody></table>`;
                        }
                        
                        // Recommendations
                        if (insights.recommendations && insights.recommendations.length > 0) {
                            message += `
                                <div class="alert alert-warning">
                                    <h5><i class="fa fa-lightbulb-o"></i> AI Recommendations</h5>
                                    <ul>
                            `;
                            insights.recommendations.forEach(rec => {
                                message += `<li>${rec}</li>`;
                            });
                            message += `</ul></div>`;
                        }
                        
                        frappe.msgprint({
                            title: __('📊 AI Purchase Insights'),
                            message: message,
                            wide: true
                        });
                    } else {
                        frappe.msgprint({
                            title: __('AI Analysis Failed'),
                            message: `
                                <div class="alert alert-warning">
                                    <h5><i class="fa fa-exclamation-triangle"></i> Purchase Order AI Insights Analysis Failed</h5>
                                    <p><strong>Issue:</strong> ${r.message?.message || 'Failed to analyze purchase insights'}</p>
                                    
                                    <h6>💡 Possible Solutions:</h6>
                                    <ul>
                                        <li>✅ <strong>Try different filters:</strong> Adjust company or confidence settings</li>
                                        <li>✅ <strong>Check forecast data:</strong> Ensure AI Sales Forecast has recent data</li>
                                        <li>✅ <strong>Use "All Companies":</strong> Leave company field blank for system-wide analysis</li>
                                        <li>✅ <strong>Lower confidence threshold:</strong> Try 50% minimum confidence</li>
                                    </ul>
                                    
                                    <p><strong>💡 Tip:</strong> The AI Purchase Order creation feature works independently and may still be available.</p>
                                </div>
                            `,
                            indicator: 'orange',
                            wide: true
                        });
                    }
                }
            });
            
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_smart_procurement_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('🎯 Smart Procurement Planner'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'smart_intro',
                options: `
                    <div class="alert alert-primary">
                        <h5><i class="fa fa-magic"></i> Smart Procurement Planning</h5>
                        <p>Advanced AI-powered procurement planning with predictive analytics and optimization.</p>
                    </div>
                `
            },
            {
                fieldtype: 'Select',
                fieldname: 'procurement_strategy',
                label: __('Procurement Strategy'),
                options: 'Conservative\nBalanced\nAggressive',
                default: 'Balanced',
                description: __('Conservative: Lower risk, Aggressive: Higher opportunity capture')
            },
            {
                fieldtype: 'Select',
                fieldname: 'urgency_level',
                label: __('Focus on Urgency'),
                options: 'All Items\nUrgent Only\nCritical Only\nHigh Opportunity Only',
                default: 'All Items'
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Currency',
                fieldname: 'budget_limit',
                label: __('Budget Limit (Optional)'),
                description: __('Maximum total value for all POs')
            },
            {
                fieldtype: 'Int',
                fieldname: 'forecast_horizon',
                label: __('Forecast Horizon (Days)'),
                default: 30,
                description: __('Planning period for demand prediction')
            }
        ],
        primary_action_label: __('🎯 Plan Smart Procurement'),
        primary_action: function(values) {
            dialog.hide();
            
            // Show loading message
            let loading_msg = frappe.msgprint({
                title: __('🤖 AI Processing'),
                message: `
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="sr-only">Loading...</span>
                        </div>
                        <p class="mt-3">Analyzing procurement strategy and generating AI-optimized purchase plans...</p>
                    </div>
                `,
                wide: true
            });
            
            // Call the smart procurement function with configuration
            frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_sales_dashboard.ai_sales_dashboard.create_smart_procurement_plan',
                args: {
                    strategy: values.procurement_strategy,
                    urgency_focus: values.urgency_level,
                    budget_limit: values.budget_limit,
                    forecast_horizon: values.forecast_horizon
                },
                callback: function(r) {
                    loading_msg.hide();
                    
                    if (r.message && r.message.status === 'success') {
                        show_smart_procurement_results(r.message);
                    } else {
                        frappe.msgprint({
                            title: __('Smart Procurement Failed'),
                            message: r.message?.message || 'Failed to generate smart procurement plan',
                            indicator: 'red'
                        });
                    }
                },
                error: function() {
                    loading_msg.hide();
                    frappe.msgprint({
                        title: __('Error'),
                        message: 'Failed to execute smart procurement planning',
                        indicator: 'red'
                    });
                }
            });
        }
    });
    
    dialog.show();
}

function show_smart_procurement_results(result) {
    let results_dialog = new frappe.ui.Dialog({
        title: __('🎯 Smart Procurement Results'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'results_html',
                options: `
                    <div class="smart-procurement-results">
                        <div class="alert alert-success">
                            <h5><i class="fa fa-check-circle"></i> Smart Procurement Plan Generated</h5>
                            <p>${result.message}</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header"><strong>📊 Plan Summary</strong></div>
                                    <div class="card-body">
                                        <p><strong>Total Budget:</strong> $${(result.total_value || 0).toLocaleString()}</p>
                                        <p><strong>Items Analyzed:</strong> ${result.ai_insights?.total_items_analyzed || 0}</p>
                                        <p><strong>POs Recommended:</strong> ${result.purchase_orders_created || 0}</p>
                                        <p><strong>Avg Confidence:</strong> ${result.ai_insights?.average_confidence || 0}%</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header"><strong>🎯 Strategy Impact</strong></div>
                                    <div class="card-body">
                                        <p><strong>High Priority Items:</strong> ${result.ai_insights?.urgent_purchases || 0}</p>
                                        <p><strong>Suppliers Involved:</strong> ${result.ai_insights?.suppliers_involved || 0}</p>
                                        <p><strong>Risk Level:</strong> ${result.risk_assessment || 'Medium'}</p>
                                        <p><strong>Optimization:</strong> ${result.optimization_score || 85}%</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${result.created_pos && result.created_pos.length > 0 ? `
                        <div class="card mt-3">
                            <div class="card-header"><strong>📋 Recommended Purchase Orders</strong></div>
                            <div class="card-body">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>PO Number</th>
                                            <th>Supplier</th>
                                            <th>Amount</th>
                                            <th>Confidence</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${result.created_pos.map(po => `
                                            <tr>
                                                <td><a href="/app/purchase-order/${po.name}" target="_blank">${po.name}</a></td>
                                                <td>${po.supplier}</td>
                                                <td>$${po.total_amount.toLocaleString()}</td>
                                                <td>
                                                    <span class="badge badge-${po.ai_confidence > 80 ? 'success' : po.ai_confidence > 60 ? 'warning' : 'secondary'}">
                                                        ${po.ai_confidence}%
                                                    </span>
                                                </td>
                                                <td><button class="btn btn-sm btn-primary" onclick="frappe.set_route('Form', 'Purchase Order', '${po.name}')">View</button></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${result.ai_insights?.recommendations ? `
                        <div class="card mt-3">
                            <div class="card-header"><strong>💡 AI Recommendations</strong></div>
                            <div class="card-body">
                                <ul>
                                    ${result.ai_insights.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    
                    <style>
                        .smart-procurement-results .card {
                            margin-bottom: 1rem;
                        }
                        .smart-procurement-results .badge {
                            font-size: 0.8rem;
                        }
                    </style>
                `
            }
        ],
        primary_action_label: __('📊 View Dashboard'),
        primary_action: function() {
            results_dialog.hide();
            // Refresh the current report to show updated data
            if (cur_frm) {
                cur_frm.reload_doc();
            }
        }
    });
    
    results_dialog.show();
}
