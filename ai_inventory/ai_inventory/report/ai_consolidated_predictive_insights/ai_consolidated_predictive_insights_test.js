// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["AI Consolidated Predictive Insights"] = {
    "filters": [
        // Date Range Filters
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -180),
            "reqd": 1,
            "width": "100px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), 30),
            "reqd": 1,
            "width": "100px"
        },
        
        // Business Entity Filters
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "width": "100px"
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": "100px"
        },
        {
            "fieldname": "territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory",
            "width": "100px"
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": "100px"
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "width": "100px"
        },
        
        // AI/ML Advanced Filters
        {
            "fieldname": "confidence_threshold",
            "label": __("Min AI Confidence %"),
            "fieldtype": "Float",
            "default": 70.0,
            "width": "120px"
        },
        {
            "fieldname": "prediction_horizon",
            "label": __("Prediction Horizon (Days)"),
            "fieldtype": "Int",
            "default": 30,
            "width": "150px"
        },
        {
            "fieldname": "priority_filter",
            "label": __("Priority Level"),
            "fieldtype": "Select",
            "options": "\nHigh\nMedium\nLow",
            "width": "100px"
        },
        {
            "fieldname": "stock_status_filter",
            "label": __("Stock Status"),
            "fieldtype": "Select",
            "options": "\n🔴 Out of Stock\n🟡 Low Stock\n🟢 Normal\n🔵 Overstocked",
            "width": "120px"
        },
        {
            "fieldname": "risk_threshold",
            "label": __("Max Risk Score"),
            "fieldtype": "Float",
            "default": 80.0,
            "width": "120px"
        },
        {
            "fieldname": "high_priority_only",
            "label": __("High Priority Only"),
            "fieldtype": "Check",
            "width": "80px"
        },
        {
            "fieldname": "critical_items_only",
            "label": __("Critical Items Only"),
            "fieldtype": "Check",
            "width": "80px"
        }
    ],
    
    onload: function(report) {
        // Initialize advanced report features
        report.page.add_inner_button(__("🔄 Refresh Forecasts"), function() {
            refresh_ai_forecasts(report);
        });
        
        report.page.add_inner_button(__("📊 Analytics Dashboard"), function() {
            show_analytics_dashboard(report);
        });
        
        report.page.add_inner_button(__("📈 Predictive Insights"), function() {
            show_predictive_insights(report);
        });
        
        report.page.add_inner_button(__("📋 Export Analysis"), function() {
            export_predictive_analysis(report);
        });
        
        report.page.add_inner_button(__("⚙️ ML Settings"), function() {
            show_ml_settings_dialog(report);
        });
        
        // Add the new analysis buttons
        report.page.add_inner_button(__("📝 Quick Recorder Analysis"), function() {
            show_quick_recorder_analysis(report);
        });
        
        report.page.add_inner_button(__("💰 Revenue Opportunities"), function() {
            show_revenue_opportunities(report);
        });
        
        report.page.add_inner_button(__("⚠️ Risk Assessment"), function() {
            show_risk_assessment(report);
        });
        
        report.page.add_inner_button(__("📊 Demand Forecasting"), function() {
            show_demand_forecasting(report);
        });
        
        // Add AI Purchase Order button
        report.page.add_inner_button(__("🛒 AI Purchase Order"), function() {
            create_ai_purchase_order(report);
        });
        
        // Add real-time update toggle
        add_realtime_toggle(report);
        
        // Initialize dashboard widgets
        setup_dashboard_widgets(report);
        
        // Setup event handlers
        setup_advanced_event_handlers(report);
    }
};

// ===== UTILITY FUNCTIONS =====

function refresh_ai_forecasts(report) {
    frappe.show_alert({message: __("Refreshing AI forecasts..."), indicator: 'blue'});
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.scheduled_forecast_generation",
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({message: __("Forecasts refreshed successfully!"), indicator: 'green'});
                report.refresh();
            } else {
                frappe.show_alert({message: __("Forecast refresh completed"), indicator: 'blue'});
                report.refresh();
            }
        },
        error: function(err) {
            console.error("Forecast refresh error:", err);
            frappe.show_alert({message: __("Error refreshing forecasts"), indicator: 'red'});
        }
    });
}

function show_analytics_dashboard(report) {
    // Redirect to AI Sales Dashboard for detailed analytics
    frappe.set_route("query-report", "AI Sales Dashboard");
}

function show_predictive_insights(report) {
    frappe.show_alert({message: __("Opening predictive insights..."), indicator: 'blue'});
    
    // Create a dialog with predictive insights
    let dialog = new frappe.ui.Dialog({
        title: __("🔮 AI Predictive Insights"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "insights_html",
                options: `
                    <div class="insights-container">
                        <h4>📊 Key Predictions</h4>
                        <ul>
                            <li>🚀 High growth items detected: Check items with increasing trends</li>
                            <li>⚠️ Stock alerts: Monitor low stock situations</li>
                            <li>💰 Revenue opportunities: Focus on high-potential items</li>
                            <li>🎯 Customer insights: Track customer scores and patterns</li>
                        </ul>
                        <br>
                        <p><strong>Recommendation:</strong> Use the filters above to drill down into specific insights.</p>
                    </div>
                `
            }
        ]
    });
    
    dialog.show();
}

function export_predictive_analysis(report) {
    frappe.show_alert({message: __("Exporting analysis..."), indicator: 'blue'});
    
    // Get current report data
    let data = report.data || [];
    
    if (data.length === 0) {
        frappe.show_alert({message: __("No data to export"), indicator: 'orange'});
        return;
    }
    
    // Create downloadable content
    frappe.tools.downloadify(data, ["CSV"], "AI_Predictive_Analysis");
    frappe.show_alert({message: __("Export completed!"), indicator: 'green'});
}

function show_ml_settings_dialog(report) {
    let dialog = new frappe.ui.Dialog({
        title: __("⚙️ ML Settings"),
        fields: [
            {
                fieldtype: "Section Break",
                label: __("Prediction Parameters")
            },
            {
                fieldtype: "Float",
                fieldname: "confidence_threshold",
                label: __("Confidence Threshold %"),
                default: 70.0,
                description: __("Minimum confidence level for predictions")
            },
            {
                fieldtype: "Int",
                fieldname: "prediction_horizon",
                label: __("Prediction Horizon (Days)"),
                default: 30,
                description: __("Number of days to predict ahead")
            },
            {
                fieldtype: "Check",
                fieldname: "enable_advanced_analytics",
                label: __("Enable Advanced Analytics"),
                default: 1
            }
        ],
        primary_action_label: __("Apply Settings"),
        primary_action: function(values) {
            // Update report filters with new settings
            report.set_filter("confidence_threshold", values.confidence_threshold);
            report.set_filter("prediction_horizon", values.prediction_horizon);
            
            frappe.show_alert({message: __("Settings applied!"), indicator: 'green'});
            dialog.hide();
            report.refresh();
        }
    });
    
    dialog.show();
}

function add_realtime_toggle(report) {
    // Add a toggle for real-time updates (placeholder)
    report.page.add_field({
        fieldtype: "Check",
        fieldname: "realtime_updates",
        label: __("Real-time Updates"),
        default: 0,
        change: function() {
            let enabled = this.get_value();
            if (enabled) {
                frappe.show_alert({message: __("Real-time updates enabled"), indicator: 'blue'});
            } else {
                frappe.show_alert({message: __("Real-time updates disabled"), indicator: 'gray'});
            }
        }
    });
}

function setup_dashboard_widgets(report) {
    // Add summary widgets (placeholder implementation)
    console.log("Dashboard widgets initialized");
}

function setup_advanced_event_handlers(report) {
    // Setup advanced event handlers for better UX
    console.log("Advanced event handlers initialized");
}

// ===== NEW ANALYSIS FUNCTIONS =====

function show_quick_recorder_analysis(report) {
    frappe.show_alert({message: __("Loading quick recorder analysis..."), indicator: 'blue'});
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.get_quick_recorder_analysis",
        callback: function(r) {
            if (r.message && r.message.status === "success") {
                let data = r.message.data;
                let summary = r.message.summary;
                
                let dialog = new frappe.ui.Dialog({
                    title: __("📝 Quick Recorder Analysis"),
                    size: "large",
                    fields: [
                        {
                            fieldtype: "HTML",
                            fieldname: "analysis_html",
                            options: `
                                <div class="analysis-container">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="card">
                                                <h5>📊 Summary</h5>
                                                <p><strong>Total Items:</strong> ${summary.total_items}</p>
                                                <p><strong>High Priority:</strong> ${summary.high_priority}</p>
                                                <p><strong>Revenue Potential:</strong> ₹${(summary.total_revenue_potential || 0).toLocaleString()}</p>
                                            </div>
                                        </div>
                                        <div class="col-md-8">
                                            <h5>🎯 Top Priority Items</h5>
                                            <table class="table table-bordered">
                                                <thead>
                                                    <tr>
                                                        <th>Item Code</th>
                                                        <th>Predicted Qty</th>
                                                        <th>Confidence</th>
                                                        <th>Priority</th>
                                                        <th>Revenue</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${data.map(item => `
                                                        <tr>
                                                            <td>${item.item_code}</td>
                                                            <td>${item.predicted_qty}</td>
                                                            <td>${item.confidence_score}%</td>
                                                            <td><span class="indicator ${item.priority === 'High Priority' ? 'red' : item.priority === 'Medium Priority' ? 'orange' : 'green'}">${item.priority}</span></td>
                                                            <td>₹${(item.revenue_potential || 0).toLocaleString()}</td>
                                                        </tr>
                                                    `).join('')}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            `
                        }
                    ]
                });
                
                dialog.show();
            } else {
                frappe.show_alert({message: __("Error loading analysis"), indicator: 'red'});
            }
        },
        error: function(err) {
            console.error("Quick recorder analysis error:", err);
            frappe.show_alert({message: __("Error loading quick recorder analysis"), indicator: 'red'});
        }
    });
}

function show_revenue_opportunities(report) {
    frappe.show_alert({message: __("Loading revenue opportunities..."), indicator: 'blue'});
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.get_revenue_opportunities",
        callback: function(r) {
            if (r.message && r.message.status === "success") {
                let data = r.message.data;
                let summary = r.message.summary;
                
                let dialog = new frappe.ui.Dialog({
                    title: __("💰 Revenue Opportunities"),
                    size: "extra-large",
                    fields: [
                        {
                            fieldtype: "HTML",
                            fieldname: "opportunities_html",
                            options: `
                                <div class="opportunities-container">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="card">
                                                <h5>💼 Summary</h5>
                                                <p><strong>Total Opportunities:</strong> ${summary.total_opportunities}</p>
                                                <p><strong>High Value Items:</strong> ${summary.high_value_count}</p>
                                                <p><strong>Total Potential:</strong> ₹${(summary.total_potential || 0).toLocaleString()}</p>
                                            </div>
                                        </div>
                                        <div class="col-md-9">
                                            <h5>🎯 Revenue Opportunities</h5>
                                            <table class="table table-bordered">
                                                <thead>
                                                    <tr>
                                                        <th>Item Code</th>
                                                        <th>Customer</th>
                                                        <th>Revenue Potential</th>
                                                        <th>Predicted Qty</th>
                                                        <th>Cross-sell Score</th>
                                                        <th>Opportunity Level</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${data.map(item => `
                                                        <tr>
                                                            <td>${item.item_code}</td>
                                                            <td>${item.customer || 'All Customers'}</td>
                                                            <td><strong>₹${(item.revenue_potential || 0).toLocaleString()}</strong></td>
                                                            <td>${item.predicted_qty}</td>
                                                            <td>${item.cross_sell_score}</td>
                                                            <td><span class="indicator ${item.opportunity_level === 'High Value' ? 'green' : item.opportunity_level === 'Medium Value' ? 'orange' : 'gray'}">${item.opportunity_level}</span></td>
                                                        </tr>
                                                    `).join('')}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            `
                        }
                    ]
                });
                
                dialog.show();
            } else {
                frappe.show_alert({message: __("Error loading opportunities"), indicator: 'red'});
            }
        },
        error: function(err) {
            console.error("Revenue opportunities error:", err);
            frappe.show_alert({message: __("Error loading revenue opportunities"), indicator: 'red'});
        }
    });
}

function show_risk_assessment(report) {
    frappe.show_alert({message: __("Loading risk assessment..."), indicator: 'blue'});
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.get_risk_assessment",
        callback: function(r) {
            if (r.message && r.message.status === "success") {
                let data = r.message.data;
                let summary = r.message.summary;
                
                let dialog = new frappe.ui.Dialog({
                    title: __("⚠️ Risk Assessment"),
                    size: "extra-large",
                    fields: [
                        {
                            fieldtype: "HTML",
                            fieldname: "risk_html",
                            options: `
                                <div class="risk-container">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="card">
                                                <h5>🎯 Risk Summary</h5>
                                                <p><strong>Total Items:</strong> ${summary.total_items}</p>
                                                <p><strong>High Risk:</strong> <span class="text-danger">${summary.high_risk}</span></p>
                                                <p><strong>Medium Risk:</strong> <span class="text-warning">${summary.medium_risk}</span></p>
                                                <p><strong>Low Risk:</strong> <span class="text-success">${summary.low_risk}</span></p>
                                            </div>
                                        </div>
                                        <div class="col-md-9">
                                            <h5>⚠️ Risk Assessment Details</h5>
                                            <table class="table table-bordered">
                                                <thead>
                                                    <tr>
                                                        <th>Item Code</th>
                                                        <th>Risk Level</th>
                                                        <th>Risk Factor</th>
                                                        <th>Churn Risk</th>
                                                        <th>Confidence</th>
                                                        <th>Sales Trend</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${data.map(item => `
                                                        <tr>
                                                            <td>${item.item_code}</td>
                                                            <td><span class="indicator ${item.risk_level === 'High Risk' ? 'red' : item.risk_level === 'Medium Risk' ? 'orange' : 'green'}">${item.risk_level}</span></td>
                                                            <td>${item.risk_factor}</td>
                                                            <td>${item.churn_risk}</td>
                                                            <td>${item.confidence_score}%</td>
                                                            <td>${item.sales_trend}</td>
                                                        </tr>
                                                    `).join('')}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            `
                        }
                    ]
                });
                
                dialog.show();
            } else {
                frappe.show_alert({message: __("Error loading risk assessment"), indicator: 'red'});
            }
        },
        error: function(err) {
            console.error("Risk assessment error:", err);
            frappe.show_alert({message: __("Error loading risk assessment"), indicator: 'red'});
        }
    });
}

function show_demand_forecasting(report) {
    frappe.show_alert({message: __("Loading demand forecasting..."), indicator: 'blue'});
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.get_demand_forecasting",
        callback: function(r) {
            if (r.message && r.message.status === "success") {
                let data = r.message.data;
                let summary = r.message.summary;
                
                let dialog = new frappe.ui.Dialog({
                    title: __("📊 Demand Forecasting"),
                    size: "extra-large",
                    fields: [
                        {
                            fieldtype: "HTML",
                            fieldname: "demand_html",
                            options: `
                                <div class="demand-container">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="card">
                                                <h5>📈 Demand Summary</h5>
                                                <p><strong>Total Items:</strong> ${summary.total_items}</p>
                                                <p><strong>High Demand:</strong> ${summary.high_demand}</p>
                                                <p><strong>Total Predicted:</strong> ${(summary.total_predicted_qty || 0).toLocaleString()}</p>
                                            </div>
                                        </div>
                                        <div class="col-md-9">
                                            <h5>📊 Demand Forecast Details</h5>
                                            <table class="table table-bordered">
                                                <thead>
                                                    <tr>
                                                        <th>Item Code</th>
                                                        <th>Predicted Qty</th>
                                                        <th>Current Stock</th>
                                                        <th>Demand Pattern</th>
                                                        <th>Seasonality</th>
                                                        <th>Forecast Level</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${data.map(item => `
                                                        <tr>
                                                            <td>${item.item_code}</td>
                                                            <td><strong>${item.predicted_qty}</strong></td>
                                                            <td>${item.current_stock || 0}</td>
                                                            <td>${item.demand_pattern || 'Unknown'}</td>
                                                            <td>${item.seasonality_index || 1.0}</td>
                                                            <td><span class="indicator ${item.demand_forecast_level === 'High Demand Expected' ? 'red' : item.demand_forecast_level === 'Moderate Demand Expected' ? 'orange' : 'green'}">${item.demand_forecast_level}</span></td>
                                                        </tr>
                                                    `).join('')}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            `
                        }
                    ]
                });
                
                dialog.show();
            } else {
                frappe.show_alert({message: __("Error loading demand forecasting"), indicator: 'red'});
            }
        },
        error: function(err) {
            console.error("Demand forecasting error:", err);
            frappe.show_alert({message: __("Error loading demand forecasting"), indicator: 'red'});
        }
    });
}

// ===== AI PURCHASE ORDER FUNCTION =====

function create_ai_purchase_order(report) {
    frappe.show_alert({message: __("Analyzing items for purchase orders..."), indicator: 'blue'});
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.create_ai_purchase_orders",
        callback: function(r) {
            if (r.message && r.message.status === "success") {
                let data = r.message.data;
                let summary = r.message.summary;
                
                let dialog = new frappe.ui.Dialog({
                    title: __("🛒 AI Purchase Order Generator"),
                    size: "extra-large",
                    fields: [
                        {
                            fieldtype: "HTML",
                            fieldname: "purchase_order_html",
                            options: `
                                <div class="purchase-order-container">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="card" style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
                                                <h5>📋 Summary</h5>
                                                <p><strong>Total Items:</strong> ${summary.total_items}</p>
                                                <p><strong>Purchase Orders:</strong> ${summary.purchase_orders}</p>
                                                <p><strong>Critical Items:</strong> <span class="text-danger">${summary.critical_items}</span></p>
                                                <div style="margin-top: 15px;">
                                                    <button class="btn btn-primary btn-sm" onclick="create_all_purchase_orders()">
                                                        📝 Create All Orders
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-9">
                                            <h5>🛒 Recommended Purchase Orders</h5>
                                            ${Object.keys(data).map(key => {
                                                let po = data[key];
                                                return `
                                                    <div class="card" style="margin-bottom: 15px; border: 1px solid #dee2e6;">
                                                        <div class="card-header" style="background: #e9ecef;">
                                                            <h6><strong>Supplier:</strong> ${po.supplier} | <strong>Company:</strong> ${po.company}</h6>
                                                            <button class="btn btn-success btn-sm float-right" onclick="create_single_purchase_order('${po.company}', '${po.supplier}', '${key}')">
                                                                📝 Create Order
                                                            </button>
                                                        </div>
                                                        <div class="card-body">
                                                            <table class="table table-sm">
                                                                <thead>
                                                                    <tr>
                                                                        <th>Item Code</th>
                                                                        <th>Current Stock</th>
                                                                        <th>Predicted Usage</th>
                                                                        <th>Suggested Qty</th>
                                                                        <th>Priority</th>
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    ${po.items.map(item => `
                                                                        <tr>
                                                                            <td><strong>${item.item_code}</strong></td>
                                                                            <td>${item.current_stock}</td>
                                                                            <td>${item.predicted_consumption}</td>
                                                                            <td><strong>${item.qty}</strong></td>
                                                                            <td><span class="indicator ${item.priority === 'Critical' ? 'red' : item.priority === 'Medium' ? 'orange' : 'green'}">${item.priority}</span></td>
                                                                        </tr>
                                                                    `).join('')}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </div>
                                                `;
                                            }).join('')}
                                        </div>
                                    </div>
                                </div>
                                
                                <script>
                                    window.purchase_order_data = ${JSON.stringify(data)};
                                    
                                    function create_single_purchase_order(company, supplier, key) {
                                        let po_data = window.purchase_order_data[key];
                                        if (!po_data) return;
                                        
                                        frappe.show_alert({message: "Creating purchase order...", indicator: 'blue'});
                                        
                                        frappe.call({
                                            method: "ai_inventory.forecasting.scheduled_tasks.create_purchase_order",
                                            args: {
                                                company: company,
                                                supplier: supplier,
                                                items: po_data.items
                                            },
                                            callback: function(r) {
                                                if (r.message && r.message.status === "success") {
                                                    frappe.show_alert({
                                                        message: "Purchase Order " + r.message.purchase_order + " created successfully!",
                                                        indicator: 'green'
                                                    });
                                                    
                                                    // Open the created purchase order
                                                    frappe.set_route("Form", "Purchase Order", r.message.purchase_order);
                                                } else {
                                                    frappe.show_alert({message: "Error creating purchase order", indicator: 'red'});
                                                }
                                            }
                                        });
                                    }
                                    
                                    function create_all_purchase_orders() {
                                        if (!window.purchase_order_data) return;
                                        
                                        let created_orders = [];
                                        let keys = Object.keys(window.purchase_order_data);
                                        
                                        function create_next_order(index) {
                                            if (index >= keys.length) {
                                                frappe.show_alert({
                                                    message: \`Created \${created_orders.length} purchase orders successfully!\`,
                                                    indicator: 'green'
                                                });
                                                return;
                                            }
                                            
                                            let key = keys[index];
                                            let po_data = window.purchase_order_data[key];
                                            
                                            frappe.call({
                                                method: "ai_inventory.forecasting.scheduled_tasks.create_purchase_order",
                                                args: {
                                                    company: po_data.company,
                                                    supplier: po_data.supplier,
                                                    items: po_data.items
                                                },
                                                callback: function(r) {
                                                    if (r.message && r.message.status === "success") {
                                                        created_orders.push(r.message.purchase_order);
                                                    }
                                                    create_next_order(index + 1);
                                                }
                                            });
                                        }
                                        
                                        frappe.show_alert({message: "Creating all purchase orders...", indicator: 'blue'});
                                        create_next_order(0);
                                    }
                                </script>
                            `
                        }
                    ]
                });
                
                dialog.show();
                
            } else if (r.message && r.message.status === "info") {
                frappe.show_alert({message: r.message.message, indicator: 'blue'});
            } else {
                frappe.show_alert({message: __("Error analyzing items for purchase orders"), indicator: 'red'});
            }
        },
        error: function(err) {
            console.error("AI Purchase Order error:", err);
            frappe.show_alert({message: __("Error creating AI purchase orders"), indicator: 'red'});
        }
    });
}
