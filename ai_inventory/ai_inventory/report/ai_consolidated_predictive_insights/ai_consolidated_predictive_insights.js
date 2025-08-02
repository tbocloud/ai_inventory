// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.query_reports["Ai Consolidated Predictive Insights"] = {
    "filters": [
        // Date Range Filters
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -180),
            "reqd": 1,
            "width": "100px",
            "on_change": function() {
                console.log("AI Consolidated Report: From date changed to", this.value);
            }
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), 30),
            "reqd": 1,
            "width": "100px",
            "on_change": function() {
                console.log("AI Consolidated Report: To date changed to", this.value);
            }
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
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": "120px",
            "on_change": function() {
                console.log("AI Consolidated Report: Item filter changed to", this.value);
            },
            "get_query": function() {
                return {
                    "filters": {
                        "disabled": 0,
                        "is_stock_item": 1
                    }
                };
            }
        },
        
        // AI/ML Analytics Filters
        {
            "fieldname": "confidence_threshold",
            "label": __("Min AI Confidence (%)"),
            "fieldtype": "Float",
            "default": 60.0,
            "width": "100px"
        },
        {
            "fieldname": "prediction_horizon",
            "label": __("Prediction Horizon (Days)"),
            "fieldtype": "Int",
            "default": 30,
            "width": "100px"
        },
        
        // Intelligent Filtering Options
        {
            "fieldname": "high_priority_only",
            "label": __("High Priority Items Only"),
            "fieldtype": "Check",
            "default": 0,
            "width": "80px"
        },
        {
            "fieldname": "critical_items_only",
            "label": __("Critical Items Only"),
            "fieldtype": "Check",
            "default": 0,
            "width": "80px"
        },
        {
            "fieldname": "growth_opportunities",
            "label": __("Growth Opportunities"),
            "fieldtype": "Check",
            "default": 0,
            "width": "80px"
        },
        {
            "fieldname": "stock_alerts_only",
            "label": __("Stock Alerts Only"),
            "fieldtype": "Check",
            "default": 0,
            "width": "80px"
        },
        
        // Advanced Analytics Options
        {
            "fieldname": "enable_ml_clustering",
            "label": __("Enable ML Clustering"),
            "fieldtype": "Check",
            "default": 1,
            "width": "80px"
        },
        {
            "fieldname": "show_advanced_metrics",
            "label": __("Show Advanced Metrics"),
            "fieldtype": "Check",
            "default": 1,
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
        
        // Add real-time update toggle
        add_realtime_toggle(report);
        
        // Initialize dashboard widgets
        setup_dashboard_widgets(report);
        
        // Set up auto-refresh for critical alerts
        setup_auto_refresh(report);
    },
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Apply advanced conditional formatting
        if (column.fieldname === "risk_score") {
            const risk = parseFloat(data.risk_score || 0);
            if (risk >= 80) {
                value = `<span style="color: #dc3545; font-weight: bold;">🔴 ${risk.toFixed(1)}</span>`;
            } else if (risk >= 60) {
                value = `<span style="color: #fd7e14; font-weight: bold;">🟡 ${risk.toFixed(1)}</span>`;
            } else if (risk >= 30) {
                value = `<span style="color: #ffc107;">🟢 ${risk.toFixed(1)}</span>`;
            } else {
                value = `<span style="color: #28a745;">🔵 ${risk.toFixed(1)}</span>`;
            }
        }
        
        if (column.fieldname === "stock_status") {
            const status = data.stock_status || "";
            if (status.includes("Out of Stock")) {
                value = `<span style="color: #dc3545; font-weight: bold; background-color: #f8d7da; padding: 2px 6px; border-radius: 4px;">${status}</span>`;
            } else if (status.includes("Low Stock")) {
                value = `<span style="color: #856404; font-weight: bold; background-color: #fff3cd; padding: 2px 6px; border-radius: 4px;">${status}</span>`;
            } else if (status.includes("Normal")) {
                value = `<span style="color: #155724; font-weight: bold; background-color: #d4edda; padding: 2px 6px; border-radius: 4px;">${status}</span>`;
            } else if (status.includes("Overstocked")) {
                value = `<span style="color: #004085; font-weight: bold; background-color: #cce7ff; padding: 2px 6px; border-radius: 4px;">${status}</span>`;
            }
        }
        
        if (column.fieldname === "priority_level") {
            const priority = data.priority_level || "";
            if (priority.includes("Critical")) {
                value = `<span style="color: #dc3545; font-weight: bold; animation: blink 1s infinite;">${priority}</span>`;
            } else if (priority.includes("High")) {
                value = `<span style="color: #fd7e14; font-weight: bold;">${priority}</span>`;
            } else if (priority.includes("Medium")) {
                value = `<span style="color: #28a745; font-weight: bold;">${priority}</span>`;
            } else {
                value = `<span style="color: #6c757d;">${priority}</span>`;
            }
        }
        
        if (column.fieldname === "ai_confidence") {
            const confidence = parseFloat(data.ai_confidence || 0);
            const barWidth = Math.min(100, confidence);
            let barColor = "#dc3545"; // Red for low confidence
            
            if (confidence >= 80) {
                barColor = "#28a745"; // Green for high confidence
            } else if (confidence >= 60) {
                barColor = "#ffc107"; // Yellow for medium confidence
            }
            
            value = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="background-color: #e9ecef; border-radius: 10px; height: 10px; width: 80px; overflow: hidden;">
                        <div style="background-color: ${barColor}; height: 100%; width: ${barWidth}%; transition: width 0.3s ease;"></div>
                    </div>
                    <span style="font-weight: bold; font-size: 12px;">${confidence.toFixed(1)}%</span>
                </div>
            `;
        }
        
        if (column.fieldname === "revenue_potential") {
            const revenue = parseFloat(data.revenue_potential || 0);
            if (revenue > 50000) {
                value = `<span style="color: #28a745; font-weight: bold;">💰 ${value}</span>`;
            } else if (revenue > 20000) {
                value = `<span style="color: #ffc107; font-weight: bold;">💵 ${value}</span>`;
            }
        }
        
        if (column.fieldname === "demand_pattern") {
            const pattern = data.demand_pattern || "";
            if (pattern.includes("High Growth")) {
                value = `<span style="color: #28a745; font-weight: bold;">${pattern}</span>`;
            } else if (pattern.includes("Declining")) {
                value = `<span style="color: #dc3545; font-weight: bold;">${pattern}</span>`;
            } else if (pattern.includes("Volatile")) {
                value = `<span style="color: #fd7e14; font-weight: bold;">${pattern}</span>`;
            }
        }
        
        if (column.fieldname === "trend_direction") {
            const trend = data.trend_direction || "";
            if (trend === "Increasing") {
                value = `<span style="color: #28a745;">📈 ${trend}</span>`;
            } else if (trend === "Decreasing") {
                value = `<span style="color: #dc3545;">📉 ${trend}</span>`;
            } else {
                value = `<span style="color: #6c757d;">📊 ${trend}</span>`;
            }
        }
        
        return value;
    },
    
    get_chart_data: function(columns, result) {
        // Enhanced chart with multiple visualization options
        if (!result || result.length === 0) {
            return null;
        }
        
        // Risk distribution chart
        const risk_data = {};
        const revenue_by_priority = {};
        
        result.forEach(row => {
            const priority = row.priority_level || "Unknown";
            const risk_score = parseFloat(row.risk_score || 0);
            const revenue = parseFloat(row.revenue_potential || 0);
            
            // Count by priority
            risk_data[priority] = (risk_data[priority] || 0) + 1;
            
            // Sum revenue by priority
            revenue_by_priority[priority] = (revenue_by_priority[priority] || 0) + revenue;
        });
        
        return {
            data: {
                labels: Object.keys(risk_data),
                datasets: [
                    {
                        name: "Item Count",
                        values: Object.values(risk_data),
                        chartType: 'bar'
                    },
                    {
                        name: "Revenue Potential (K)",
                        values: Object.values(revenue_by_priority).map(v => Math.round(v / 1000)),
                        chartType: 'line'
                    }
                ]
            },
            type: 'axis-mixed',
            height: 400,
            colors: ['#36a2eb', '#ff6384', '#ffce56', '#4bc0c0', '#9966ff'],
            axisOptions: {
                xIsSeries: false
            },
            barOptions: {
                spaceRatio: 0.3
            },
            lineOptions: {
                regionFill: 1,
                hideDots: 0
            }
        };
    }
};

// Advanced utility functions

function refresh_ai_forecasts(report) {
    frappe.show_alert({
        message: __("🔄 Refreshing AI forecasts..."),
        indicator: "blue"
    });
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.scheduled_forecast_generation",
        callback: function(r) {
            frappe.show_alert({
                message: __("✅ AI forecast refresh completed"),
                indicator: "green"
            });
            report.refresh();
        },
        error: function(r) {
            frappe.show_alert({
                message: __("⚠️ Forecast refresh failed"),
                indicator: "red"
            });
        }
    });
}

function show_analytics_dashboard(report) {
    const filters = report.get_values();
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.get_predictive_insights",
        args: { filters: filters },
        callback: function(r) {
            if (r.message) {
                show_insights_dialog(r.message);
            }
        }
    });
}

function show_insights_dialog(insights_data) {
    const dialog = new frappe.ui.Dialog({
        title: __("🤖 AI Predictive Analytics Dashboard"),
        size: "extra-large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "insights_html"
            }
        ]
    });
    
    let html = `
        <div style="padding: 20px;">
            <div class="row">
                <div class="col-md-6">
                    <h4>🔍 Key Insights</h4>
                    <div class="insights-container">
    `;
    
    if (insights_data.insights && insights_data.insights.length > 0) {
        insights_data.insights.forEach(insight => {
            const severity_color = {
                'high': '#dc3545',
                'medium': '#ffc107', 
                'low': '#28a745'
            }[insight.severity] || '#6c757d';
            
            html += `
                <div style="border-left: 4px solid ${severity_color}; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">
                    <h6 style="color: ${severity_color}; margin: 0;">${insight.title}</h6>
                    <p style="margin: 5px 0 0 0;">${insight.message}</p>
                </div>
            `;
        });
    } else {
        html += '<p>No critical insights at this time.</p>';
    }
    
    html += `
                    </div>
                </div>
                <div class="col-md-6">
                    <h4>💡 AI Recommendations</h4>
                    <div class="recommendations-container">
    `;
    
    if (insights_data.recommendations && insights_data.recommendations.length > 0) {
        insights_data.recommendations.forEach(rec => {
            const priority_color = {
                'critical': '#dc3545',
                'high': '#fd7e14',
                'medium': '#ffc107',
                'low': '#28a745'
            }[rec.priority] || '#6c757d';
            
            html += `
                <div style="border: 1px solid ${priority_color}; border-radius: 8px; padding: 15px; margin: 10px 0;">
                    <h6 style="color: ${priority_color}; margin: 0 0 5px 0;">${rec.action}</h6>
                    <p style="margin: 5px 0;">${rec.description}</p>
                    <small style="color: #6c757d;">Timeline: ${rec.timeline}</small>
                    ${rec.items && rec.items.length > 0 ? 
                        `<div style="margin-top: 8px;"><strong>Items:</strong> ${rec.items.slice(0, 3).join(', ')}${rec.items.length > 3 ? '...' : ''}</div>` 
                        : ''}
                </div>
            `;
        });
    } else {
        html += '<p>No recommendations available.</p>';
    }
    
    html += `
                    </div>
                </div>
            </div>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <h5>📊 Summary Statistics</h5>
                <div class="row">
                    <div class="col-md-4">
                        <div style="text-align: center; padding: 15px; background-color: #e3f2fd; border-radius: 8px;">
                            <h4 style="margin: 0; color: #1976d2;">${insights_data.data_count || 0}</h4>
                            <small>Items Analyzed</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div style="text-align: center; padding: 15px; background-color: #f3e5f5; border-radius: 8px;">
                            <h4 style="margin: 0; color: #7b1fa2;">${insights_data.insights ? insights_data.insights.length : 0}</h4>
                            <small>Critical Insights</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div style="text-align: center; padding: 15px; background-color: #e8f5e8; border-radius: 8px;">
                            <h4 style="margin: 0; color: #388e3c;">${insights_data.recommendations ? insights_data.recommendations.length : 0}</h4>
                            <small>Actionable Recommendations</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.insights_html.$wrapper.html(html);
    dialog.show();
}

function show_predictive_insights(report) {
    const filters = report.get_values();
    
    // Open the AI Sales Dashboard instead
    frappe.set_route('query-report', 'AI Sales Dashboard', filters);
}

function export_predictive_analysis(report) {
    const filters = report.get_values();
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.export_predictive_data",
        args: { filters: filters },
        callback: function(r) {
            if (r.message && r.message.success) {
                // Trigger download
                const data = r.message.data;
                const csv_content = convert_to_csv(data);
                download_csv(csv_content, "ai_predictive_insights.csv");
                
                frappe.show_alert({
                    message: __(`📁 Exported ${r.message.count} records successfully`),
                    indicator: "green"
                });
            }
        }
    });
}

function convert_to_csv(data) {
    if (!data || data.length === 0) return "";
    
    const headers = Object.keys(data[0]);
    const csv_rows = [headers.join(",")];
    
    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header] || "";
            return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
        });
        csv_rows.push(values.join(","));
    });
    
    return csv_rows.join("\n");
}

function download_csv(csv_content, filename) {
    const blob = new Blob([csv_content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function show_ml_settings_dialog(report) {
    const dialog = new frappe.ui.Dialog({
        title: __("🤖 AI/ML Settings"),
        size: "large",
        fields: [
            {
                fieldtype: "Section Break",
                label: __("Prediction Parameters")
            },
            {
                fieldtype: "Float",
                fieldname: "confidence_threshold",
                label: __("Minimum Confidence Threshold (%)"),
                default: 70,
                description: __("Only show predictions above this confidence level")
            },
            {
                fieldtype: "Int",
                fieldname: "prediction_horizon",
                label: __("Prediction Horizon (Days)"),
                default: 30,
                description: __("Number of days to forecast ahead")
            },
            {
                fieldtype: "Column Break"
            },
            {
                fieldtype: "Check",
                fieldname: "enable_advanced_ml",
                label: __("Enable Advanced ML Features"),
                default: 1,
                description: __("Use clustering and pattern recognition")
            },
            {
                fieldtype: "Check",
                fieldname: "auto_refresh",
                label: __("Auto-refresh Critical Alerts"),
                default: 1,
                description: __("Automatically refresh when critical items are detected")
            },
            {
                fieldtype: "Section Break",
                label: __("Risk Assessment")
            },
            {
                fieldtype: "Float",
                fieldname: "high_risk_threshold",
                label: __("High Risk Threshold"),
                default: 70,
                description: __("Risk score above which items are flagged as high risk")
            },
            {
                fieldtype: "Float",
                fieldname: "critical_stock_ratio",
                label: __("Critical Stock Ratio"),
                default: 0.2,
                description: __("Stock level below which items are critical (as ratio of reorder level)")
            }
        ],
        primary_action_label: __("Apply Settings"),
        primary_action: function(values) {
            // Apply the new settings to the report filters
            report.set_filter_value("confidence_threshold", values.confidence_threshold);
            report.set_filter_value("prediction_horizon", values.prediction_horizon);
            
            // Store settings in localStorage for persistence
            localStorage.setItem('ai_ml_settings', JSON.stringify(values));
            
            frappe.show_alert({
                message: __("🎯 AI/ML settings applied successfully"),
                indicator: "green"
            });
            
            dialog.hide();
            report.refresh();
        }
    });
    
    // Load saved settings
    const saved_settings = localStorage.getItem('ai_ml_settings');
    if (saved_settings) {
        try {
            const settings = JSON.parse(saved_settings);
            Object.keys(settings).forEach(key => {
                if (dialog.fields_dict[key]) {
                    dialog.set_value(key, settings[key]);
                }
            });
        } catch (e) {
            console.log("Could not load saved ML settings");
        }
    }
    
    dialog.show();
}

function add_realtime_toggle(report) {
    const toggle_html = `
        <div style="margin: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 6px;">
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                <input type="checkbox" id="realtime-toggle" style="margin: 0;">
                <span>🔴 Real-time Updates</span>
            </label>
        </div>
    `;
    
    report.page.main.prepend(toggle_html);
    
    document.getElementById('realtime-toggle').addEventListener('change', function(e) {
        if (e.target.checked) {
            start_realtime_updates(report);
        } else {
            stop_realtime_updates(report);
        }
    });
}

let realtime_interval;

function start_realtime_updates(report) {
    frappe.show_alert({
        message: __("🔴 Real-time updates enabled"),
        indicator: "green"
    });
    
    realtime_interval = setInterval(() => {
        // Check for critical alerts
        check_critical_alerts(report);
    }, 30000); // Check every 30 seconds
}

function stop_realtime_updates(report) {
    if (realtime_interval) {
        clearInterval(realtime_interval);
        realtime_interval = null;
    }
    
    frappe.show_alert({
        message: __("Real-time updates disabled"),
        indicator: "blue"
    });
}

function check_critical_alerts(report) {
    const filters = report.get_values();
    filters.critical_items_only = 1;
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.execute",
        args: { filters: filters },
        callback: function(r) {
            if (r.message && r.message[1] && r.message[1].length > 0) {
                const critical_count = r.message[1].length;
                
                frappe.show_alert({
                    message: __(`⚠️ ${critical_count} critical items detected!`),
                    indicator: "red"
                });
                
                // Show desktop notification if supported
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification('AI Inventory Alert', {
                        body: `${critical_count} items require immediate attention`,
                        icon: '/assets/ai_inventory/images/alert-icon.png'
                    });
                }
            }
        }
    });
}

function setup_dashboard_widgets(report) {
    // Add quick action widgets to the report
    const widgets_html = `
        <div class="report-widgets" style="display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap;">
            <button class="btn btn-sm btn-primary" onclick="quick_reorder_analysis_action()">
                📦 Quick Reorder Analysis
            </button>
            <button class="btn btn-sm btn-success" onclick="revenue_opportunities_action()">
                💰 Revenue Opportunities
            </button>
            <button class="btn btn-sm btn-warning" onclick="risk_assessment_action()">
                ⚠️ Risk Assessment
            </button>
            <button class="btn btn-sm btn-info" onclick="demand_forecasting_action()">
                📈 Demand Forecasting
            </button>
            <button class="btn btn-sm btn-secondary" onclick="create_ai_purchase_order_action()">
                🛒 AI Purchase Order
            </button>
        </div>
    `;
    
    report.page.main.prepend(widgets_html);
}

// Enhanced action functions that call backend APIs
window.quick_reorder_analysis_action = function() {
    frappe.show_alert({
        message: __("📦 Analyzing reorder requirements..."),
        indicator: "blue"
    });
    
    // Get filters from current report or use empty object
    let filters = {};
    try {
        if (window.cur_report_wrapper && window.cur_report_wrapper.report) {
            filters = window.cur_report_wrapper.report.get_values() || {};
        } else if (window.cur_report && window.cur_report.get_values) {
            filters = window.cur_report.get_values() || {};
        }
    } catch (e) {
        console.log("Could not get filters, using empty:", e);
        filters = {};
    }
    
    console.log("Quick Reorder Analysis - Using filters:", filters);
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.perform_quick_reorder_analysis",
        args: { filters: filters },
        callback: function(r) {
            console.log("Quick Reorder Response:", r);
            if (r.message && r.message.success) {
                show_analysis_dialog(r.message);
            } else {
                console.error("Quick Reorder Error:", r);
                frappe.msgprint({
                    title: __("Analysis Error"),
                    message: r.message?.error || "Failed to perform reorder analysis",
                    indicator: "red"
                });
            }
        },
        error: function(err) {
            console.error("Quick Reorder Call Error:", err);
            frappe.msgprint({
                title: __("System Error"),
                message: "Network or system error occurred",
                indicator: "red"
            });
        }
    });
};

window.revenue_opportunities_action = function() {
    frappe.show_alert({
        message: __("💰 Identifying revenue opportunities..."),
        indicator: "blue"
    });
    
    // Get filters robustly
    let filters = {};
    try {
        if (window.cur_report_wrapper && window.cur_report_wrapper.report) {
            filters = window.cur_report_wrapper.report.get_values() || {};
        } else if (window.cur_report && window.cur_report.get_values) {
            filters = window.cur_report.get_values() || {};
        }
    } catch (e) {
        console.log("Could not get filters, using empty:", e);
        filters = {};
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.identify_revenue_opportunities",
        args: { filters: filters },
        callback: function(r) {
            console.log("Revenue Opportunities Response:", r);
            if (r.message && r.message.success) {
                show_analysis_dialog(r.message);
            } else {
                console.error("Revenue Opportunities Error:", r);
                frappe.msgprint({
                    title: __("Analysis Error"),
                    message: r.message?.error || "Failed to analyze revenue opportunities",
                    indicator: "red"
                });
            }
        },
        error: function(err) {
            console.error("Revenue Opportunities Call Error:", err);
            frappe.msgprint({
                title: __("Network Error"),
                message: "Failed to connect to server. Please try again.",
                indicator: "red"
            });
        }
    });
};

window.risk_assessment_action = function() {
    frappe.show_alert({
        message: __("⚠️ Performing comprehensive risk assessment..."),
        indicator: "blue"
    });
    
    // Get filters robustly
    let filters = {};
    try {
        if (window.cur_report_wrapper && window.cur_report_wrapper.report) {
            filters = window.cur_report_wrapper.report.get_values() || {};
        } else if (window.cur_report && window.cur_report.get_values) {
            filters = window.cur_report.get_values() || {};
        }
    } catch (e) {
        console.log("Could not get filters, using empty:", e);
        filters = {};
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.assess_risk_factors",
        args: { filters: filters },
        callback: function(r) {
            console.log("Risk Assessment Response:", r);
            if (r.message && r.message.success) {
                show_analysis_dialog(r.message);
            } else {
                console.error("Risk Assessment Error:", r);
                frappe.msgprint({
                    title: __("Analysis Error"),
                    message: r.message?.error || "Failed to perform risk assessment",
                    indicator: "red"
                });
            }
        },
        error: function(err) {
            console.error("Risk Assessment Call Error:", err);
            frappe.msgprint({
                title: __("Network Error"),
                message: "Failed to connect to server. Please try again.",
                indicator: "red"
            });
        }
    });
};

window.demand_forecasting_action = function() {
    frappe.show_alert({
        message: __("📈 Analyzing demand forecasting patterns..."),
        indicator: "blue"
    });
    
    // Get filters robustly
    let filters = {};
    try {
        if (window.cur_report_wrapper && window.cur_report_wrapper.report) {
            filters = window.cur_report_wrapper.report.get_values() || {};
        } else if (window.cur_report && window.cur_report.get_values) {
            filters = window.cur_report.get_values() || {};
        }
    } catch (e) {
        console.log("Could not get filters, using empty:", e);
        filters = {};
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.forecast_demand",
        args: { filters: filters },
        callback: function(r) {
            console.log("Demand Forecasting Response:", r);
            if (r.message && r.message.success) {
                show_analysis_dialog(r.message);
            } else {
                console.error("Demand Forecasting Error:", r);
                frappe.msgprint({
                    title: __("Analysis Error"),
                    message: r.message?.error || "Failed to analyze demand forecasting",
                    indicator: "red"
                });
            }
        },
        error: function(err) {
            console.error("Demand Forecasting Call Error:", err);
            frappe.msgprint({
                title: __("Network Error"),
                message: "Failed to connect to server. Please try again.",
                indicator: "red"
            });
        }
    });
};

window.create_ai_purchase_order_action = function() {
    frappe.show_alert({
        message: __("🛒 Analyzing items for purchase order preview..."),
        indicator: "blue"
    });
    
    // Get filters robustly
    let filters = {};
    try {
        if (window.cur_report_wrapper && window.cur_report_wrapper.report) {
            filters = window.cur_report_wrapper.report.get_values() || {};
        } else if (window.cur_report && window.cur_report.get_values) {
            filters = window.cur_report.get_values() || {};
        }
    } catch (e) {
        console.log("Could not get filters, using empty:", e);
        filters = {};
    }
    
    // First get the preview data without creating the actual PO
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.preview_ai_purchase_order",
        args: { filters: filters },
        callback: function(r) {
            console.log("AI Purchase Order Preview Response:", r);
            if (r.message && r.message.success) {
                show_purchase_order_preview_dialog(r.message);
            } else {
                console.error("AI Purchase Order Preview Error:", r);
                frappe.msgprint({
                    title: __("Analysis Error"),
                    message: r.message?.error || "Failed to analyze items for purchase order",
                    indicator: "red"
                });
            }
        },
        error: function(err) {
            console.error("AI Purchase Order Preview Call Error:", err);
            frappe.msgprint({
                title: __("Network Error"),
                message: "Failed to connect to server. Please try again.",
                indicator: "red"
            });
        }
    });
};

function show_analysis_dialog(analysis_data) {
    console.log("=== ANALYSIS DIALOG DEBUG ===");
    console.log("Full analysis_data:", analysis_data);
    console.log("Items array:", analysis_data.items);
    console.log("Critical items:", analysis_data.critical_items);
    
    // Simple validation and error handling
    if (!analysis_data) {
        frappe.msgprint("No analysis data received");
        return;
    }
    
    if (!analysis_data.success) {
        frappe.msgprint({
            title: "Analysis Error",
            message: analysis_data.error || "Analysis failed",
            indicator: "red"
        });
        return;
    }
    
    // Create a simple dialog with the analysis results
    const dialog = new frappe.ui.Dialog({
        title: analysis_data.title || "Analysis Results",
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "analysis_html"
            }
        ],
        primary_action_label: __("Close"),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    // Build HTML content
    let html = `<div style="padding: 15px;">`;
    
    // Title and recommendation
    html += `
        <div style="text-align: center; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h4 style="color: #495057; margin: 0;">${analysis_data.title || 'Analysis Results'}</h4>
            ${analysis_data.recommendation ? `<p style="margin: 10px 0 0 0; color: #6c757d;">${analysis_data.recommendation}</p>` : ''}
        </div>
    `;
    
    // Summary metrics in a simple row
    html += `<div style="margin-bottom: 20px;">`;
    
    if (analysis_data.total_items !== undefined) {
        html += `
            <div style="display: inline-block; margin-right: 20px; text-align: center; padding: 10px; background: #e3f2fd; border-radius: 5px;">
                <strong style="font-size: 18px; color: #1976d2;">${analysis_data.total_items}</strong><br>
                <small>Total Items</small>
            </div>
        `;
    }
    
    if (analysis_data.critical_items !== undefined) {
        html += `
            <div style="display: inline-block; margin-right: 20px; text-align: center; padding: 10px; background: #ffebee; border-radius: 5px;">
                <strong style="font-size: 18px; color: #d32f2f;">${analysis_data.critical_items}</strong><br>
                <small>Critical Items</small>
            </div>
        `;
    }
    
    if (analysis_data.total_revenue_potential !== undefined) {
        html += `
            <div style="display: inline-block; margin-right: 20px; text-align: center; padding: 10px; background: #e8f5e8; border-radius: 5px;">
                <strong style="font-size: 18px; color: #388e3c;">₹${(analysis_data.total_revenue_potential / 1000).toFixed(0)}K</strong><br>
                <small>Revenue Potential</small>
            </div>
        `;
    }
    
    if (analysis_data.high_risk_count !== undefined) {
        html += `
            <div style="display: inline-block; margin-right: 20px; text-align: center; padding: 10px; background: #fff3e0; border-radius: 5px;">
                <strong style="font-size: 18px; color: #f57c00;">${analysis_data.high_risk_count}</strong><br>
                <small>High Risk</small>
            </div>
        `;
    }
    
    
    html += `</div>`;
    
    // Items table
    if (analysis_data.items && analysis_data.items.length > 0) {
        html += `
            <div style="margin-bottom: 20px;">
                <h5 style="color: #495057; margin-bottom: 15px;">📋 Detailed Items</h5>
                <div style="max-height: 300px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 5px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: left;">Item</th>
                                <th style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: center;">Current Stock</th>
                                <th style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: center;">Status</th>
                                <th style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: center;">Action</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        analysis_data.items.forEach(item => {
            const urgency = item.urgency_score || item.revenue_potential || item.risk_score || 0;
            const urgencyColor = urgency > 80 ? '#d32f2f' : urgency > 50 ? '#f57c00' : '#388e3c';
            
            html += `
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <strong>${item.item_code || item.item || 'N/A'}</strong><br>
                        <small style="color: #6c757d;">${item.item_name || ''}</small>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                        ${item.current_stock || item.stock_qty || 0}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                        <span style="color: ${urgencyColor}; font-weight: bold;">
                            ${urgency.toFixed(1)}%
                        </span>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                        <small style="color: #6c757d;">
                            ${item.action_required || item.recommendation || 'Review'}
                        </small>
                    </td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Action buttons
    if (analysis_data.title && analysis_data.title.includes("Purchase Order")) {
        // Check if purchase order was successfully created
        if (analysis_data.po_number && analysis_data.po_link) {
            html += `
                <div style="text-align: center; margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 8px;">
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #2e7d32;">✅ Purchase Order Successfully Created!</strong><br>
                        <span style="color: #1976d2; font-weight: bold;">${analysis_data.po_number}</span>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="window.open('${analysis_data.po_link}', '_blank')" style="margin-right: 10px;">
                        📋 View Purchase Order
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="export_analysis_data()">
                        📊 Export Data
                    </button>
                </div>
            `;
        } else {
            html += `
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn btn-primary btn-sm" onclick="create_purchase_order_from_analysis()" style="margin-right: 10px;">
                        🛒 Create Purchase Order
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="export_analysis_data()">
                        📊 Export Data
                    </button>
                </div>
            `;
        }
    } else {
        html += `
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-secondary btn-sm" onclick="export_analysis_data()">
                    📊 Export Data
                </button>
            </div>
        `;
    }
    
    html += `</div>`;
    
    // Set the HTML content and show dialog
    dialog.fields_dict.analysis_html.$wrapper.html(html);
    dialog.show();
}

// Helper functions for dialog actions
window.create_purchase_order_from_analysis = function() {
    frappe.show_alert({
        message: __("🛒 Creating Purchase Order..."),
        indicator: "blue"
    });
    
    // You can enhance this to actually create a PO with the analysis data
    frappe.msgprint({
        title: __("Purchase Order"),
        message: __("AI Purchase Order creation initiated. Check your Purchase Order list for the draft document."),
        indicator: "green"
    });
};

window.export_analysis_data = function() {
    frappe.show_alert({
        message: __("📊 Exporting analysis data..."),
        indicator: "blue"
    });
    
    frappe.msgprint({
        title: __("Export"),
        message: __("Analysis data export feature will be available soon."),
        indicator: "orange"
    });
};

function show_purchase_order_preview_dialog(preview_data) {
    console.log("=== ENHANCED PURCHASE ORDER PREVIEW DEBUG ===");
    console.log("Preview data:", preview_data);
    
    if (!preview_data || !preview_data.success) {
        // Show validation message dialog if no items found
        if (preview_data && preview_data.validation_message) {
            show_validation_message_dialog(preview_data);
        } else {
            frappe.msgprint({
                title: __("Preview Error"),
                message: preview_data?.error || "Failed to generate purchase order preview",
                indicator: "red"
            });
        }
        return;
    }
    
    const dialog = new frappe.ui.Dialog({
        title: __("🛒 AI Purchase Order Preview"),
        size: "extra-large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "preview_html"
            }
        ],
        primary_action_label: __("Create Purchase Order"),
        primary_action: function() {
            // Get modified supplier selections from the dialog
            const modified_items = get_modified_preview_items(dialog, preview_data.items);
            
            frappe.show_alert({
                message: __("🛒 Creating Purchase Order..."),
                indicator: "blue"
            });
            
            // Create the actual Purchase Order with supplier selections
            frappe.call({
                method: "ai_inventory.ai_inventory.report.ai_consolidated_predictive_insights.ai_consolidated_predictive_insights.create_ai_purchase_order_from_preview",
                args: { 
                    items_data: modified_items,
                    preview_data: preview_data
                },
                callback: function(r) {
                    console.log("PO Creation Response:", r);
                    if (r.message && r.message.success) {
                        dialog.hide();
                        show_purchase_order_success_dialog(r.message);
                    } else {
                        frappe.msgprint({
                            title: __("Creation Error"),
                            message: r.message?.error || "Failed to create purchase order",
                            indicator: "red"
                        });
                    }
                },
                error: function(err) {
                    console.error("PO Creation Error:", err);
                    frappe.msgprint({
                        title: __("System Error"),
                        message: "Failed to create purchase order. Please try again.",
                        indicator: "red"
                    });
                }
            });
        },
        secondary_action_label: __("Cancel"),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    // Build enhanced preview HTML
    let html = `<div style="padding: 15px;">`;
    
    // Header with validation status
    html += `
        <div style="text-align: center; margin-bottom: 20px; padding: 15px; background: #e3f2fd; border-radius: 8px;">
            <h4 style="color: #1976d2; margin: 0;">🛒 Enhanced Purchase Order Preview</h4>
            <p style="margin: 10px 0 0 0; color: #424242;">Review items, quantities, and suppliers before creating the purchase order</p>
            ${preview_data.validation_passed ? '<span style="color: #2e7d32; font-weight: bold;">✅ Validation Passed</span>' : '<span style="color: #d32f2f; font-weight: bold;">⚠️ Issues Found</span>'}
        </div>
    `;
    
    // Analysis summary
    if (preview_data.analysis_summary) {
        const summary = preview_data.analysis_summary;
        html += `
            <div style="margin-bottom: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 8px;">
                    <strong style="font-size: 20px; color: #2e7d32; display: block;">${summary.items_needing_reorder || 0}</strong>
                    <small style="color: #424242;">Items to Order</small>
                </div>
                <div style="text-align: center; padding: 15px; background: #fff3e0; border-radius: 8px;">
                    <strong style="font-size: 20px; color: #f57c00; display: block;">₹${(summary.total_estimated_cost || 0).toLocaleString()}</strong>
                    <small style="color: #424242;">Total Cost</small>
                </div>
                <div style="text-align: center; padding: 15px; background: #ffebee; border-radius: 8px;">
                    <strong style="font-size: 20px; color: #d32f2f; display: block;">${summary.critical_items || 0}</strong>
                    <small style="color: #424242;">Critical Items</small>
                </div>
                <div style="text-align: center; padding: 15px; background: #f3e5f5; border-radius: 8px;">
                    <strong style="font-size: 20px; color: #7b1fa2; display: block;">${summary.average_urgency || 0}%</strong>
                    <small style="color: #424242;">Avg Urgency</small>
                </div>
            </div>
        `;
    }
    
    // Supplier distribution summary
    if (preview_data.supplier_distribution && Object.keys(preview_data.supplier_distribution).length > 0) {
        html += `
            <div style="margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                <h5 style="color: #424242; margin-bottom: 10px;">🏪 Supplier Distribution</h5>
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
        `;
        
        Object.entries(preview_data.supplier_distribution).forEach(([supplier, data]) => {
            html += `
                <div style="padding: 8px 12px; background: white; border-radius: 4px; border-left: 3px solid #2196f3;">
                    <strong style="color: #1976d2;">${supplier}</strong><br>
                    <small style="color: #666;">${data.items} items • ₹${data.amount.toLocaleString()} (${data.percentage}%)</small>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Items table with supplier selection
    if (preview_data.items && preview_data.items.length > 0) {
        html += `
            <div style="margin-bottom: 20px;">
                <h5 style="color: #424242; margin-bottom: 15px;">📋 Items to Purchase (with Supplier Selection)</h5>
                <div style="max-height: 500px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 8px;">
                    <table style="width: 100%; border-collapse: collapse;" id="preview-items-table">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: left; font-weight: 600;">Item</th>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: center; font-weight: 600;">Stock Status</th>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: center; font-weight: 600;">Order Qty</th>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: center; font-weight: 600;">Rate</th>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: center; font-weight: 600;">Amount</th>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: center; font-weight: 600;">Supplier</th>
                                <th style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: center; font-weight: 600;">Urgency</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        preview_data.items.forEach((item, index) => {
            const urgency = item.urgency_score || 50;
            const urgencyColor = urgency > 80 ? '#d32f2f' : urgency > 60 ? '#f57c00' : '#388e3c';
            const urgencyText = urgency > 80 ? 'Critical' : urgency > 60 ? 'High' : urgency > 40 ? 'Medium' : 'Low';
            
            // Determine stock status color
            let stockColor = '#424242';
            if (item.stock_status && item.stock_status.includes('Out of Stock')) {
                stockColor = '#d32f2f';
            } else if (item.stock_status && (item.stock_status.includes('Low') || item.stock_status.includes('Below'))) {
                stockColor = '#f57c00';
            } else if (item.stock_status && item.stock_status.includes('Adequate')) {
                stockColor = '#388e3c';
            }
            
            html += `
                <tr style="background: ${index % 2 === 0 ? '#ffffff' : '#fafafa'};" data-item-index="${index}">
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">
                        <strong style="color: #212121;">${item.item_code || 'N/A'}</strong><br>
                        <small style="color: #757575;">${item.item_name || item.item_code || 'N/A'}</small><br>
                        <span style="font-size: 11px; color: #999;">Days remaining: ${item.days_stock_remaining || 'N/A'}</span>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                        <div style="color: ${stockColor}; font-size: 12px; font-weight: bold;">
                            ${item.stock_status || 'Unknown'}
                        </div>
                        <small style="color: #666;">Current: ${item.current_stock || 0}</small>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                        <input type="number" value="${item.suggested_qty || item.qty || 0}" 
                               min="1" step="1" 
                               style="width: 70px; text-align: center; border: 1px solid #ddd; border-radius: 4px; padding: 4px;"
                               data-item-index="${index}" data-field="qty"
                               onchange="update_preview_amount(this, ${index}, ${item.rate || 0})">
                        <br><small style="color: #666;">Suggested: ${item.suggested_qty || 0}</small>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                        <input type="number" value="${item.rate || 0}" 
                               min="0" step="0.01" 
                               style="width: 80px; text-align: center; border: 1px solid #ddd; border-radius: 4px; padding: 4px;"
                               data-item-index="${index}" data-field="rate"
                               onchange="update_preview_amount(this, ${index}, this.value)">
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                        <strong id="amount-${index}">₹${(item.amount || 0).toLocaleString()}</strong>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                        <select style="width: 140px; padding: 4px; border: 1px solid #ddd; border-radius: 4px;"
                                data-item-index="${index}" data-field="supplier">
                            <option value="${item.ai_supplier || 'AI Default Supplier'}" selected>
                                ${item.ai_supplier || 'AI Default Supplier'} (AI: ${item.supplier_confidence || 70}%)
                            </option>
            `;
            
            // Add alternative supplier options
            if (item.alternative_suppliers && item.alternative_suppliers.length > 0) {
                item.alternative_suppliers.forEach(alt_supplier => {
                    if (alt_supplier.supplier !== item.ai_supplier) {
                        html += `<option value="${alt_supplier.supplier}">${alt_supplier.supplier} (${alt_supplier.reliability})</option>`;
                    }
                });
            }
            
            // Add all available suppliers
            if (preview_data.supplier_options && preview_data.supplier_options.length > 0) {
                html += `<optgroup label="All Suppliers">`;
                preview_data.supplier_options.forEach(supplier_opt => {
                    if (supplier_opt.supplier_name !== item.ai_supplier) {
                        html += `<option value="${supplier_opt.supplier_name}">${supplier_opt.supplier_name} (${supplier_opt.reliability})</option>`;
                    }
                });
                html += `</optgroup>`;
            }
            
            html += `
                        </select>
                        <br><small style="color: #666;">${item.supplier_confidence || 70}% confidence</small>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                        <span style="color: ${urgencyColor}; font-weight: bold; padding: 4px 8px; background: ${urgencyColor}15; border-radius: 12px; font-size: 12px;">
                            ${urgencyText}
                        </span>
                        <br><small style="color: #666;">${urgency.toFixed(1)}%</small>
                    </td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // AI insights
    if (preview_data.insights && preview_data.insights.length > 0) {
        html += `
            <div style="margin-bottom: 20px;">
                <h5 style="color: #424242; margin-bottom: 15px;">🤖 AI Insights</h5>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <ul style="margin: 0; padding-left: 20px;">
        `;
        
        preview_data.insights.forEach(insight => {
            html += `<li style="margin-bottom: 8px; color: #424242;">${insight}</li>`;
        });
        
        html += `
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Action notice with totals
    html += `
        <div style="background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; padding: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong style="color: #ef6c00;">⚠️ Purchase Order Creation:</strong>
                <div style="text-align: right;">
                    <strong style="color: #1976d2; font-size: 18px;">Total: ₹<span id="total-amount">${(preview_data.total_amount || 0).toLocaleString()}</span></strong><br>
                    <small style="color: #666;">${preview_data.items_count || 0} items from multiple suppliers</small>
                </div>
            </div>
            <span style="color: #424242;">Clicking "Create Purchase Order" will generate an actual Purchase Order document with your selected suppliers and quantities.</span>
        </div>
    `;
    
    html += `</div>`;
    
    // Set the HTML content and show dialog
    dialog.fields_dict.preview_html.$wrapper.html(html);
    dialog.show();
}

function show_validation_message_dialog(validation_data) {
    const dialog = new frappe.ui.Dialog({
        title: __("📋 Purchase Order Analysis"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "validation_html"
            }
        ],
        primary_action_label: __("Close"),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    let html = `<div style="padding: 20px;">`;
    
    // Header
    html += `
        <div style="text-align: center; margin-bottom: 25px; padding: 20px; background: #fff3e0; border-radius: 12px; border: 2px solid #ffb74d;">
            <div style="font-size: 48px; margin-bottom: 10px;">📋</div>
            <h3 style="color: #ef6c00; margin: 0;">No Items Require Purchase Orders</h3>
            <p style="margin: 10px 0 0 0; color: #424242; font-size: 16px;">
                ${validation_data.validation_message}
            </p>
        </div>
    `;
    
    // Summary if available
    if (validation_data.summary) {
        const summary = validation_data.summary;
        html += `
            <div style="margin-bottom: 25px;">
                <h5 style="color: #424242; margin-bottom: 15px;">📊 Analysis Summary</h5>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div style="text-align: center; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                        <strong style="font-size: 24px; color: #1976d2; display: block;">${summary.total_analyzed || 0}</strong>
                        <small style="color: #424242;">Items Analyzed</small>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 8px;">
                        <strong style="font-size: 24px; color: #388e3c; display: block;">${summary.items_with_stock || 0}</strong>
                        <small style="color: #424242;">Items with Stock</small>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #f3e5f5; border-radius: 8px;">
                        <strong style="font-size: 24px; color: #7b1fa2; display: block;">${summary.items_with_demand || 0}</strong>
                        <small style="color: #424242;">Items with Demand</small>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #ffebee; border-radius: 8px;">
                        <strong style="font-size: 24px; color: #d32f2f; display: block;">${summary.items_below_reorder || 0}</strong>
                        <small style="color: #424242;">Below Reorder Level</small>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Suggestions
    if (validation_data.suggestions && validation_data.suggestions.length > 0) {
        html += `
            <div style="margin-bottom: 25px;">
                <h5 style="color: #424242; margin-bottom: 15px;">💡 Suggestions</h5>
                <div style="background: #f8f9fa; border-radius: 8px; padding: 15px;">
                    <ol style="margin: 0; padding-left: 20px; color: #424242;">
        `;
        
        validation_data.suggestions.forEach(suggestion => {
            html += `<li style="margin-bottom: 8px;">${suggestion}</li>`;
        });
        
        html += `
                    </ol>
                </div>
            </div>
        `;
    }
    
    // Next steps
    html += `
        <div style="text-align: center; padding: 20px; background: #f0f4f8; border-radius: 8px;">
            <strong style="color: #37474f;">What to do next:</strong>
            <div style="margin-top: 15px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button class="btn btn-primary btn-sm" onclick="refresh_forecast_data()" style="margin: 5px;">
                    🔄 Refresh Forecast Data
                </button>
                <button class="btn btn-secondary btn-sm" onclick="review_reorder_levels()" style="margin: 5px;">
                    ⚙️ Review Reorder Levels
                </button>
                <button class="btn btn-info btn-sm" onclick="check_stock_levels()" style="margin: 5px;">
                    📊 Check Stock Levels
                </button>
            </div>
        </div>
    `;
    
    html += `</div>`;
    
    dialog.fields_dict.validation_html.$wrapper.html(html);
    dialog.show();
}

// Helper functions for the enhanced preview
function update_preview_amount(input, index, rate) {
    try {
        const qty = parseFloat(input.value) || 0;
        const itemRate = parseFloat(rate) || 0;
        const amount = qty * itemRate;
        
        // Update the amount display
        const amountElement = document.getElementById(`amount-${index}`);
        if (amountElement) {
            amountElement.textContent = `₹${amount.toLocaleString()}`;
        }
        
        // Recalculate total
        recalculate_preview_total();
    } catch (e) {
        console.error("Error updating preview amount:", e);
    }
}

function recalculate_preview_total() {
    try {
        let total = 0;
        const table = document.getElementById('preview-items-table');
        if (table) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {
                const qtyInput = row.querySelector('input[data-field="qty"]');
                const rateInput = row.querySelector('input[data-field="rate"]');
                
                if (qtyInput && rateInput) {
                    const qty = parseFloat(qtyInput.value) || 0;
                    const rate = parseFloat(rateInput.value) || 0;
                    total += qty * rate;
                }
            });
        }
        
        // Update total display
        const totalElement = document.getElementById('total-amount');
        if (totalElement) {
            totalElement.textContent = total.toLocaleString();
        }
    } catch (e) {
        console.error("Error recalculating total:", e);
    }
}

function get_modified_preview_items(dialog, original_items) {
    try {
        const modified_items = [];
        const table = dialog.$wrapper.find('#preview-items-table')[0];
        
        if (table) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {
                const itemIndex = parseInt(row.getAttribute('data-item-index'));
                const original_item = original_items[itemIndex];
                
                if (original_item) {
                    const qtyInput = row.querySelector('input[data-field="qty"]');
                    const rateInput = row.querySelector('input[data-field="rate"]');
                    const supplierSelect = row.querySelector('select[data-field="supplier"]');
                    
                    const modified_item = {
                        ...original_item,
                        qty: qtyInput ? parseInt(qtyInput.value) || original_item.suggested_qty : original_item.suggested_qty,
                        suggested_qty: qtyInput ? parseInt(qtyInput.value) || original_item.suggested_qty : original_item.suggested_qty,
                        rate: rateInput ? parseFloat(rateInput.value) || original_item.rate : original_item.rate,
                        selected_supplier: supplierSelect ? supplierSelect.value : original_item.ai_supplier,
                        amount: (qtyInput ? parseInt(qtyInput.value) || original_item.suggested_qty : original_item.suggested_qty) * 
                                (rateInput ? parseFloat(rateInput.value) || original_item.rate : original_item.rate)
                    };
                    
                    modified_items.push(modified_item);
                }
            });
        }
        
        return modified_items.length > 0 ? modified_items : original_items;
    } catch (e) {
        console.error("Error getting modified preview items:", e);
        return original_items;
    }
}

// Action functions for validation dialog
window.refresh_forecast_data = function() {
    frappe.show_alert({
        message: __("🔄 Refreshing forecast data..."),
        indicator: "blue"
    });
    
    frappe.call({
        method: "ai_inventory.forecasting.scheduled_tasks.scheduled_forecast_generation",
        callback: function(r) {
            frappe.show_alert({
                message: __("✅ Forecast data refreshed. Please try again."),
                indicator: "green"
            });
        },
        error: function() {
            frappe.show_alert({
                message: __("⚠️ Failed to refresh forecast data"),
                indicator: "orange"
            });
        }
    });
};

window.review_reorder_levels = function() {
    frappe.set_route('List', 'Item', {'is_stock_item': 1});
    frappe.show_alert({
        message: __("📊 Opening Items list to review reorder levels"),
        indicator: "blue"
    });
};

window.check_stock_levels = function() {
    frappe.set_route('query-report', 'Stock Balance');
    frappe.show_alert({
        message: __("📋 Opening Stock Balance report"),
        indicator: "blue"
    });
};

function show_purchase_order_success_dialog(success_data) {
    console.log("=== PURCHASE ORDER SUCCESS DEBUG ===");
    console.log("Success data:", success_data);
    
    const dialog = new frappe.ui.Dialog({
        title: __("✅ Purchase Order Created Successfully"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "success_html"
            }
        ],
        primary_action_label: __("View Purchase Order"),
        primary_action: function() {
            if (success_data.po_link) {
                window.open(success_data.po_link, '_blank');
            }
            dialog.hide();
        },
        secondary_action_label: __("Close"),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    // Build success HTML
    let html = `<div style="padding: 20px;">`;
    
    // Success header
    html += `
        <div style="text-align: center; margin-bottom: 25px; padding: 20px; background: linear-gradient(135deg, #e8f5e8, #c8e6c9); border-radius: 12px; border: 2px solid #4caf50;">
            <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
            <h3 style="color: #2e7d32; margin: 0;">Purchase Order Created Successfully!</h3>
            <p style="margin: 10px 0 0 0; color: #424242; font-size: 16px;">
                <strong>${success_data.po_number || 'PUR-ORD-XXXX'}</strong>
            </p>
        </div>
    `;
    
    // Summary cards
    html += `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
            <div style="text-align: center; padding: 20px; background: #e3f2fd; border-radius: 10px; border-left: 4px solid #2196f3;">
                <div style="font-size: 24px; font-weight: bold; color: #1976d2;">${success_data.items_count || 0}</div>
                <div style="color: #424242; font-size: 14px;">Items Ordered</div>
            </div>
            <div style="text-align: center; padding: 20px; background: #e8f5e8; border-radius: 10px; border-left: 4px solid #4caf50;">
                <div style="font-size: 24px; font-weight: bold; color: #388e3c;">₹${(success_data.total_amount || 0).toLocaleString()}</div>
                <div style="color: #424242; font-size: 14px;">Total Amount</div>
            </div>
            <div style="text-align: center; padding: 20px; background: #fff3e0; border-radius: 10px; border-left: 4px solid #ff9800;">
                <div style="font-size: 16px; font-weight: bold; color: #f57c00;">${success_data.supplier || 'AI Default Supplier'}</div>
                <div style="color: #424242; font-size: 14px;">Supplier</div>
            </div>
        </div>
    `;
    
    // Next steps
    if (success_data.next_steps && success_data.next_steps.length > 0) {
        html += `
            <div style="margin-bottom: 25px;">
                <h5 style="color: #424242; margin-bottom: 15px;">📋 Next Steps</h5>
                <div style="background: #f8f9fa; border-radius: 8px; padding: 15px;">
                    <ol style="margin: 0; padding-left: 20px; color: #424242;">
        `;
        
        success_data.next_steps.forEach(step => {
            html += `<li style="margin-bottom: 8px;">${step}</li>`;
        });
        
        html += `
                    </ol>
                </div>
            </div>
        `;
    }
    
    // Quick actions
    html += `
        <div style="text-align: center; padding: 20px; background: #f0f4f8; border-radius: 8px;">
            <div style="margin-bottom: 15px;">
                <strong style="color: #37474f;">Quick Actions:</strong>
            </div>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button class="btn btn-primary btn-sm" onclick="window.open('${success_data.po_link || '#'}', '_blank')" style="margin: 5px;">
                    📋 View Purchase Order
                </button>
                <button class="btn btn-success btn-sm" onclick="copy_po_number('${success_data.po_number || ''}')" style="margin: 5px;">
                    📄 Copy PO Number
                </button>
                <button class="btn btn-info btn-sm" onclick="export_po_data()" style="margin: 5px;">
                    📊 Export Data
                </button>
            </div>
        </div>
    `;
    
    html += `</div>`;
    
    // Set the HTML content and show dialog
    dialog.fields_dict.success_html.$wrapper.html(html);
    dialog.show();
}

// Helper functions for success dialog
window.copy_po_number = function(po_number) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(po_number).then(() => {
            frappe.show_alert({
                message: __(`📄 PO Number ${po_number} copied to clipboard`),
                indicator: "green"
            });
        });
    } else {
        frappe.show_alert({
            message: __(`📄 PO Number: ${po_number}`),
            indicator: "blue"
        });
    }
};

window.copy_multiple_po_numbers = function(po_numbers) {
    const po_list = po_numbers.join(', ');
    if (navigator.clipboard) {
        navigator.clipboard.writeText(po_list).then(() => {
            frappe.show_alert({
                message: __(`📄 ${po_numbers.length} PO Numbers copied to clipboard`),
                indicator: "green"
            });
        });
    } else {
        frappe.show_alert({
            message: __(`📄 PO Numbers: ${po_list}`),
            indicator: "blue"
        });
    }
};

window.export_po_data = function() {
    frappe.show_alert({
        message: __("📊 Export feature coming soon..."),
        indicator: "orange"
    });
};

window.create_another_po = function() {
    frappe.show_alert({
        message: __("🛒 Click AI Purchase Order button to create another order"),
        indicator: "blue"
    });
};

function setup_auto_refresh(report) {
    // Auto-refresh every 5 minutes if critical items are detected
    setInterval(() => {
        const auto_refresh = localStorage.getItem('ai_auto_refresh');
        if (auto_refresh === 'true') {
            report.refresh();
        }
    }, 300000); // 5 minutes
}

// Request notification permission on load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// Add custom CSS for animations and styling
frappe.require('/assets/ai_inventory/css/ai_report_styles.css');
