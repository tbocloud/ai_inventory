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
        method: "ai_inventory.forecasting.scheduled_tasks.run_ai_forecasting",
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("✅ AI forecasts updated successfully"),
                    indicator: "green"
                });
                report.refresh();
            } else {
                frappe.show_alert({
                    message: __("⚠️ Forecast refresh failed"),
                    indicator: "red"
                });
            }
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
    
    // Open a new window with advanced analytics
    const analytics_url = `/app/ai-analytics?${$.param(filters)}`;
    window.open(analytics_url, '_blank');
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
            <button class="btn btn-sm btn-primary" onclick="quick_reorder_analysis()">
                📦 Quick Reorder Analysis
            </button>
            <button class="btn btn-sm btn-success" onclick="revenue_opportunities()">
                💰 Revenue Opportunities
            </button>
            <button class="btn btn-sm btn-warning" onclick="risk_assessment()">
                ⚠️ Risk Assessment
            </button>
            <button class="btn btn-sm btn-info" onclick="demand_forecasting()">
                📈 Demand Forecasting
            </button>
        </div>
    `;
    
    report.page.main.prepend(widgets_html);
}

// Quick action functions
window.quick_reorder_analysis = function() {
    frappe.set_route('query-report', 'AI Consolidated Predictive Insights', {
        critical_items_only: 1,
        high_priority_only: 1
    });
};

window.revenue_opportunities = function() {
    frappe.set_route('query-report', 'AI Consolidated Predictive Insights', {
        growth_opportunities: 1,
        confidence_threshold: 80
    });
};

window.risk_assessment = function() {
    frappe.set_route('query-report', 'AI Consolidated Predictive Insights', {
        stock_alerts_only: 1,
        confidence_threshold: 60
    });
};

window.demand_forecasting = function() {
    frappe.set_route('query-report', 'AI Consolidated Predictive Insights', {
        enable_ml_clustering: 1,
        show_advanced_metrics: 1,
        prediction_horizon: 60
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
