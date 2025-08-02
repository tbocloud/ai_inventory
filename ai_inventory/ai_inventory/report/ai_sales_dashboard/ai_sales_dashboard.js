// ai_inventory/ai_inventory/report/ai_sales_dashboard/ai_sales_dashboard.js

frappe.query_reports["AI Sales Dashboard"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 0,
            "width": "100px"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            "reqd": 0,
            "width": "100px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0,
            "width": "100px"
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 0,
            "width": "100px"
        },
        {
            "fieldname": "territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory",
            "reqd": 0,
            "width": "100px"
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "reqd": 0,
            "width": "100px"
        },
        {
            "fieldname": "sales_trend",
            "label": __("Sales Trend"),
            "fieldtype": "Select",
            "options": "\nIncreasing\nDecreasing\nStable\nVolatile\nSeasonal",
            "reqd": 0
        },
        {
            "fieldname": "movement_type", 
            "label": __("Movement Type"),
            "fieldtype": "Select",
            "options": "\nFast Moving\nSlow Moving\nCritical\nNon Moving",
            "reqd": 0
        },
        {
            "fieldname": "sales_alert",
            "label": __("Show Sales Alerts Only"),
            "fieldtype": "Check",
            "default": 0,
            "reqd": 0
        },
        {
            "fieldname": "low_confidence",
            "label": __("Low Confidence Items (<70%)"),
            "fieldtype": "Check",
            "default": 0,
            "reqd": 0
        },
        {
            "fieldname": "high_opportunity",
            "label": __("High Opportunity Items"),
            "fieldtype": "Check",
            "default": 0,
            "reqd": 0
        },
        {
            "fieldname": "fast_moving_only",
            "label": __("Fast Moving Only"),
            "fieldtype": "Check",
            "default": 0,
            "reqd": 0
        },
        {
            "fieldname": "volatility_index",
            "label": __("Volatility Index"),
            "fieldtype": "Float",
            "reqd": 0,
            "width": "120px"
        },
        {
            "fieldname": "reorder_level",
            "label": __("Show Reorder Level Alerts"),
            "fieldtype": "Check",
            "default": 0,
            "reqd": 0
        },
        {
            "fieldname": "suggested_qty",
            "label": __("Show Suggested Quantities"),
            "fieldtype": "Check",
            "default": 0,
            "reqd": 0
        },
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (!data) return value;
        
        // Enhanced formatting with better visual indicators
        switch(column.fieldname) {
            case "sales_alert":
                if (data.sales_alert == 1) {
                    value = `<span class="indicator red" title="High Priority Alert">🚨 Alert</span>`;
                } else {
                    value = `<span class="text-muted">—</span>`;
                }
                break;
                
            case "movement_type":
                const movement_icons = {
                    "Critical": {icon: "🚨", color: "#d73527", weight: "bold"},
                    "Fast Moving": {icon: "🚀", color: "#28a745", weight: "bold"}, 
                    "Slow Moving": {icon: "🐌", color: "#ffc107", weight: "bold"},
                    "Non Moving": {icon: "⏸️", color: "#6c757d", weight: "normal"},
                    "Normal": {icon: "📊", color: "#17a2b8", weight: "normal"}
                };
                
                const movement = data.movement_type;
                const movement_style = movement_icons[movement] || movement_icons["Normal"];
                value = `<span style="color: ${movement_style.color}; font-weight: ${movement_style.weight};">
                    ${movement_style.icon} ${movement}</span>`;
                break;
                
            case "sales_trend":
                const trend_icons = {
                    "Increasing": {icon: "📈", color: "#28a745"},
                    "Decreasing": {icon: "📉", color: "#dc3545"},
                    "Stable": {icon: "📊", color: "#17a2b8"},
                    "Volatile": {icon: "⚡", color: "#fd7e14"},
                    "Seasonal": {icon: "🔄", color: "#6f42c1"},
                    "Unknown": {icon: "❓", color: "#6c757d"}
                };
                
                const trend = data.sales_trend;
                const trend_style = trend_icons[trend] || trend_icons["Unknown"];
                value = `<span style="color: ${trend_style.color}; font-weight: 500;">
                    ${trend_style.icon} ${trend}</span>`;
                break;
                
            case "demand_pattern":
                if (data.demand_pattern && data.demand_pattern !== "📊 Unknown") {
                    value = `<span style="font-size: 0.9em; color: #495057;">${data.demand_pattern}</span>`;
                } else {
                    value = `<span class="text-muted">${data.demand_pattern || "—"}</span>`;
                }
                break;
                
            case "confidence_score":
                if (data.confidence_score !== undefined && data.confidence_score !== null) {
                    const confidence = parseFloat(data.confidence_score);
                    let color, badge_class;
                    
                    if (confidence >= 80) {
                        color = "#28a745";
                        badge_class = "success";
                    } else if (confidence >= 60) {
                        color = "#ffc107";
                        badge_class = "warning";
                    } else {
                        color = "#dc3545";
                        badge_class = "danger";
                    }
                    
                    value = `<span class="badge badge-${badge_class}" style="color: white; font-weight: bold;">
                        ${confidence.toFixed(1)}%</span>`;
                }
                break;
                
            case "customer_score":
                if (data.customer_score !== undefined && data.customer_score !== null) {
                    const score = parseFloat(data.customer_score);
                    let color = score >= 70 ? "#28a745" : score >= 40 ? "#ffc107" : "#dc3545";
                    let stars = score >= 80 ? "⭐⭐⭐" : score >= 60 ? "⭐⭐" : score >= 40 ? "⭐" : "";
                    
                    value = `<span style="color: ${color}; font-weight: bold;">
                        ${score.toFixed(1)} ${stars}</span>`;
                }
                break;
                
            case "market_potential":
                if (data.market_potential !== undefined && data.market_potential !== null) {
                    const potential = parseFloat(data.market_potential);
                    let color = potential >= 70 ? "#28a745" : potential >= 40 ? "#ffc107" : "#dc3545";
                    let arrow = potential >= 70 ? "🔥" : potential >= 40 ? "📊" : "📉";
                    
                    value = `<span style="color: ${color}; font-weight: 500;">
                        ${arrow} ${potential.toFixed(1)}%</span>`;
                }
                break;
                
            case "revenue_potential":
                if (data.revenue_potential !== undefined && data.revenue_potential !== null) {
                    const amount = parseFloat(data.revenue_potential);
                    if (amount > 0) {
                        const formatted = format_currency(amount);
                        const size = amount > 50000 ? "💰💰" : amount > 10000 ? "💰" : "💵";
                        value = `<span style="color: #28a745; font-weight: bold;">
                            ${size} ${formatted}</span>`;
                    }
                }
                break;
                
            case "cross_sell_score":
                if (data.cross_sell_score !== undefined && data.cross_sell_score !== null) {
                    const score = parseFloat(data.cross_sell_score);
                    let color = score >= 60 ? "#28a745" : score >= 30 ? "#ffc107" : "#6c757d";
                    let icon = score >= 60 ? "🎯" : score >= 30 ? "📈" : "📊";
                    
                    value = `<span style="color: ${color}; font-size: 0.9em;">
                        ${icon} ${score.toFixed(1)}</span>`;
                }
                break;
                
            case "churn_risk":
                const risk_styles = {
                    "🟢 Low": {color: "#28a745", bg: "#d4edda"},
                    "🟡 Medium": {color: "#856404", bg: "#fff3cd"},
                    "🔴 High": {color: "#721c24", bg: "#f8d7da"},
                    "❓ Unknown": {color: "#6c757d", bg: "#e2e3e5"}
                };
                
                const risk = data.churn_risk;
                const risk_style = risk_styles[risk] || risk_styles["❓ Unknown"];
                
                value = `<span style="color: ${risk_style.color}; background: ${risk_style.bg}; 
                    padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: 500;">
                    ${risk}</span>`;
                break;
                
            case "predicted_consumption":
            case "predicted_qty":
                if (data.predicted_qty !== undefined && data.predicted_qty !== null) {
                    const qty = parseFloat(data.predicted_qty);
                    const formatted = qty.toLocaleString();
                    const size_indicator = qty > 1000 ? "📦📦" : qty > 100 ? "📦" : "📋";
                    value = `<span style="font-weight: 500; color: #2c3e50;">${size_indicator} ${formatted}</span>`;
                }
                break;
                
            case "demand_trend":
            case "sales_trend":
                const demand_trend_icons = {
                    "Increasing": {icon: "📈", color: "#28a745"},
                    "Decreasing": {icon: "📉", color: "#dc3545"},
                    "Stable": {icon: "📊", color: "#17a2b8"},
                    "Volatile": {icon: "⚡", color: "#fd7e14"},
                    "Seasonal": {icon: "🔄", color: "#6f42c1"},
                    "Unknown": {icon: "❓", color: "#6c757d"}
                };
                
                const demand_trend = data.sales_trend || data.demand_trend;
                const demand_trend_style = demand_trend_icons[demand_trend] || demand_trend_icons["Unknown"];
                value = `<span style="color: ${demand_trend_style.color}; font-weight: 500;">
                    ${demand_trend_style.icon} ${demand_trend}</span>`;
                break;
                
            case "seasonality_score":
            case "seasonality_index":
                if (data.seasonality_index !== undefined && data.seasonality_index !== null) {
                    const index = parseFloat(data.seasonality_index);
                    let color = index > 1.2 ? "#28a745" : index < 0.8 ? "#dc3545" : "#17a2b8";
                    let trend = index > 1.2 ? "📈" : index < 0.8 ? "📉" : "➡️";
                    
                    value = `<span style="color: ${color}; font-weight: 500;">
                        ${trend} ${index.toFixed(2)}</span>`;
                }
                break;
                
            case "volatility_index":
                if (data.volatility_index !== undefined && data.volatility_index !== null) {
                    const volatility = parseFloat(data.volatility_index);
                    let color = volatility > 0.7 ? "#dc3545" : volatility > 0.4 ? "#ffc107" : "#28a745";
                    let icon = volatility > 0.7 ? "⚡" : volatility > 0.4 ? "📊" : "📈";
                    
                    value = `<span style="color: ${color}; font-weight: 500;">
                        ${icon} ${volatility.toFixed(2)}</span>`;
                }
                break;
                
            case "reorder_level":
                if (data.reorder_level !== undefined && data.reorder_level !== null) {
                    const level = parseFloat(data.reorder_level);
                    const current_stock = parseFloat(data.current_stock || 0);
                    let color = current_stock <= level ? "#dc3545" : "#28a745";
                    let icon = current_stock <= level ? "🚨" : "✅";
                    
                    value = `<span style="color: ${color}; font-weight: bold;">
                        ${icon} ${level.toFixed(0)}</span>`;
                }
                break;
                
            case "suggested_qty":
                if (data.suggested_qty !== undefined && data.suggested_qty !== null) {
                    const qty = parseFloat(data.suggested_qty);
                    const formatted = qty.toLocaleString();
                    const urgency = qty > 100 ? "🔥" : qty > 50 ? "📦" : "📋";
                    
                    value = `<span style="color: #007bff; font-weight: 500;">
                        ${urgency} ${formatted}</span>`;
                }
                break;
                
            case "customer_churn_probability":
                if (data.customer_churn_probability !== undefined && data.customer_churn_probability !== null) {
                    const probability = parseFloat(data.customer_churn_probability);
                    let color = probability > 70 ? "#dc3545" : probability > 40 ? "#ffc107" : "#28a745";
                    let risk_level = probability > 70 ? "🔴 High" : probability > 40 ? "🟡 Medium" : "🟢 Low";
                    
                    value = `<span style="color: ${color}; font-weight: bold;">
                        ${risk_level} (${probability.toFixed(1)}%)</span>`;
                }
                break;
                
            case "item_forecasted_qty_30_days":
                if (data.item_forecasted_qty_30_days !== undefined && data.item_forecasted_qty_30_days !== null) {
                    const qty = parseFloat(data.item_forecasted_qty_30_days);
                    const formatted = qty.toLocaleString();
                    const trend_icon = qty > 0 ? "📈" : "📊";
                    
                    value = `<span style="color: #007bff; font-weight: 500;">
                        ${trend_icon} ${formatted}</span>`;
                }
                break;
                
            case "forecast_date":
                if (data.forecast_date) {
                    const date = new Date(data.forecast_date);
                    const today = new Date();
                    const diffDays = Math.floor((today - date) / (1000 * 60 * 60 * 24));
                    
                    let color = diffDays > 7 ? "#dc3545" : diffDays > 3 ? "#ffc107" : "#28a745";
                    let freshness = diffDays > 7 ? "⚠️" : diffDays > 3 ? "📅" : "✅";
                    
                    value = `<span style="color: ${color}; font-size: 0.9em;">
                        ${freshness} ${frappe.datetime.str_to_user(data.forecast_date)}</span>`;
                }
                break;
                
            case "last_updated":
            case "last_forecast_date":
                if (data.last_forecast_date) {
                    const date = new Date(data.last_forecast_date);
                    const today = new Date();
                    const diffHours = Math.floor((today - date) / (1000 * 60 * 60));
                    
                    let color = diffHours > 72 ? "#dc3545" : diffHours > 24 ? "#ffc107" : "#28a745";
                    let freshness = diffHours > 72 ? "⏰" : diffHours > 24 ? "🕐" : "🆕";
                    
                    const timeAgo = diffHours < 1 ? "Just now" : 
                                   diffHours < 24 ? `${diffHours}h ago` : 
                                   `${Math.floor(diffHours/24)}d ago`;
                    
                    value = `<span style="color: ${color}; font-size: 0.9em;">
                        ${freshness} ${timeAgo}</span>`;
                }
                break;
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Enhanced UI improvements
        add_custom_buttons(report);
        add_summary_cards(report);
        enhance_report_layout(report);
        
        // Auto-refresh every 5 minutes for live data
        if (frappe.user.has_role("Sales Manager")) {
            setInterval(() => {
                if (document.visibilityState === 'visible') {
                    report.refresh();
                }
            }, 300000); // 5 minutes
        }
    },
    
    "after_datatable_render": function(datatable) {
        // Add row highlighting for important items
        datatable.bodyRenderer.visibleRows.forEach(row => {
            const data = row.data;
            const rowElement = row.element;
            
            // Safety check for data structure
            if (!data || typeof data !== 'object') {
                return;
            }
            
            // Highlight critical items
            if (data.movement_type === 'Critical') {
                rowElement.style.backgroundColor = '#fff5f5';
                rowElement.style.borderLeft = '4px solid #dc3545';
            }
            
            // Highlight high alerts
            else if (data.sales_alert == 1) {
                rowElement.style.backgroundColor = '#f0fff4';
                rowElement.style.borderLeft = '4px solid #28a745';
            }
            
            // Highlight growth opportunities
            else if (data.sales_trend === 'Increasing' && data.confidence_score > 80) {
                rowElement.style.backgroundColor = '#f8f9ff';
                rowElement.style.borderLeft = '4px solid #17a2b8';
            }
        });
    }
};

// Helper Functions
function add_custom_buttons(report) {
    // Main action buttons
    report.page.add_inner_button(__("🔄 Refresh Data"), function() {
        frappe.show_alert({message: __("Refreshing dashboard..."), indicator: 'blue'});
        report.refresh();
    }, __("Actions"));
    
    report.page.add_inner_button(__("📊 AI Insights"), function() {
        show_ai_insights_dialog(report);
    }, __("Analytics"));
    
    report.page.add_inner_button(__("📈 Trends Analysis"), function() {
        show_trends_analysis(report);
    }, __("Analytics"));
    
    // Export options
    report.page.add_menu_item(__("📋 Export to Excel"), function() {
        export_to_excel(report);
    }, __("Export"));
    
    report.page.add_menu_item(__("📄 Export Summary"), function() {
        export_summary_report(report);
    }, __("Export"));
    
    // Bulk operations
    report.page.add_menu_item(__("📝 Create Sales Orders"), function() {
        create_bulk_sales_orders(report);
    }, __("Bulk Actions"));
    
    report.page.add_menu_item(__("🔄 Update Forecasts"), function() {
        update_bulk_forecasts(report);
    }, __("Bulk Actions"));
    
    // Settings
    report.page.add_menu_item(__("⚙️ Dashboard Settings"), function() {
        show_dashboard_settings();
    }, __("Settings"));
}

function show_ai_insights_dialog(report) {
    const data = report.data || [];
    
    if (data.length === 0) {
        frappe.msgprint({
            title: __("No Data"),
            message: __("No forecast data available for insights generation."),
            indicator: "orange"
        });
        return;
    }
    
    // Get current filters
    const filters = report.get_values();
    
    frappe.call({
        method: "ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard.get_forecast_insights",
        args: {filters: filters},
        callback: function(r) {
            if (r.message) {
                show_insights_modal(r.message);
            }
        }
    });
}

function show_insights_modal(insights_data) {
    const insights = insights_data.insights || [];
    const recommendations = insights_data.recommendations || [];
    
    let insights_html = `
        <div class="ai-insights-container">
            <div class="row">
                <div class="col-md-12">
                    <h4 style="color: #2c3e50; margin-bottom: 20px;">
                        🤖 AI Sales Intelligence Report
                    </h4>
                </div>
            </div>
    `;
    
    // Add insights section
    if (insights.length > 0) {
        insights_html += `
            <div class="row">
                <div class="col-md-12">
                    <h5 style="color: #34495e; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
                        🎯 Recommended Actions
                    </h5>
                </div>
            </div>
            <div class="row">
        `;
        
        recommendations.forEach(rec => {
            const priority_colors = {
                high: "#e74c3c",
                medium: "#f39c12",
                low: "#27ae60"
            };
            
            const priority_icons = {
                high: "🔥",
                medium: "⚡",
                low: "📋"
            };
            
            insights_html += `
                <div class="col-md-12 mb-3">
                    <div class="card" style="border-left: 4px solid ${priority_colors[rec.priority]}; padding: 15px;">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 style="color: ${priority_colors[rec.priority]}; margin-bottom: 8px;">
                                    ${priority_icons[rec.priority]} ${rec.action}
                                    <span class="badge badge-${rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'success'}" 
                                          style="font-size: 0.7em; margin-left: 10px;">
                                        ${rec.priority.toUpperCase()} PRIORITY
                                    </span>
                                </h6>
                                <p style="margin-bottom: 10px; color: #2c3e50;">
                                    ${rec.description}
                                </p>
                                ${rec.items && rec.items.length > 0 ? `
                                    <div style="background: #f8f9fa; padding: 8px; border-radius: 4px;">
                                        <small class="text-muted">
                                            <strong>Items:</strong> ${rec.items.join(', ')}
                                            ${rec.items.length > 5 ? '...' : ''}
                                        </small>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        insights_html += `</div>`;
    }
    
    // Add footer
    insights_html += `
            <div class="row">
                <div class="col-md-12">
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 4px; margin-top: 20px;">
                        <small class="text-muted">
                            📅 Analysis Date: ${insights_data.analysis_date || frappe.datetime.get_today()}<br>
                            📊 Total Items Analyzed: ${insights_data.total_items || 0}<br>
                            🤖 Powered by AI Sales Intelligence
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frappe.msgprint({
        title: __("🤖 AI Sales Insights"),
        message: insights_html,
        wide: true
    });
}

function show_trends_analysis(report) {
    const data = report.data || [];
    
    if (data.length === 0) {
        frappe.msgprint(__("No data available for trends analysis"));
        return;
    }
    
    // Analyze trends
    const trends = {
        increasing: data.filter(d => d.sales_trend === 'Increasing').length,
        decreasing: data.filter(d => d.sales_trend === 'Decreasing').length,
        stable: data.filter(d => d.sales_trend === 'Stable').length,
        volatile: data.filter(d => d.sales_trend === 'Volatile').length
    };
    
    const movements = {
        critical: data.filter(d => d.movement_type === 'Critical').length,
        fast: data.filter(d => d.movement_type === 'Fast Moving').length,
        slow: data.filter(d => d.movement_type === 'Slow Moving').length,
        normal: data.filter(d => !['Critical', 'Fast Moving', 'Slow Moving'].includes(d.movement_type)).length
    };
    
    const avg_confidence = data.reduce((sum, d) => sum + (parseFloat(d.confidence_score) || 0), 0) / data.length;
    const total_revenue_potential = data.reduce((sum, d) => sum + (parseFloat(d.revenue_potential) || 0), 0);
    
    const trends_html = `
        <div class="trends-analysis">
            <h4 style="color: #2c3e50; margin-bottom: 20px;">📈 Sales Trends Analysis</h4>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="trend-card">
                        <h5 style="color: #3498db;">📊 Sales Trends Distribution</h5>
                        <div class="trend-items">
                            <div class="trend-item">
                                <span class="trend-label">📈 Increasing:</span>
                                <span class="trend-value" style="color: #27ae60;">${trends.increasing} items (${((trends.increasing/data.length)*100).toFixed(1)}%)</span>
                            </div>
                            <div class="trend-item">
                                <span class="trend-label">📉 Decreasing:</span>
                                <span class="trend-value" style="color: #e74c3c;">${trends.decreasing} items (${((trends.decreasing/data.length)*100).toFixed(1)}%)</span>
                            </div>
                            <div class="trend-item">
                                <span class="trend-label">📊 Stable:</span>
                                <span class="trend-value" style="color: #3498db;">${trends.stable} items (${((trends.stable/data.length)*100).toFixed(1)}%)</span>
                            </div>
                            <div class="trend-item">
                                <span class="trend-label">⚡ Volatile:</span>
                                <span class="trend-value" style="color: #f39c12;">${trends.volatile} items (${((trends.volatile/data.length)*100).toFixed(1)}%)</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="trend-card">
                        <h5 style="color: #e74c3c;">🚀 Movement Analysis</h5>
                        <div class="trend-items">
                            <div class="trend-item">
                                <span class="trend-label">🚨 Critical:</span>
                                <span class="trend-value" style="color: #e74c3c;">${movements.critical} items</span>
                            </div>
                            <div class="trend-item">
                                <span class="trend-label">🚀 Fast Moving:</span>
                                <span class="trend-value" style="color: #27ae60;">${movements.fast} items</span>
                            </div>
                            <div class="trend-item">
                                <span class="trend-label">🐌 Slow Moving:</span>
                                <span class="trend-value" style="color: #f39c12;">${movements.slow} items</span>
                            </div>
                            <div class="trend-item">
                                <span class="trend-label">📊 Normal:</span>
                                <span class="trend-value" style="color: #3498db;">${movements.normal} items</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="metric-card" style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                        <h3 style="color: #2c3e50; margin-bottom: 10px;">${avg_confidence.toFixed(1)}%</h3>
                        <p style="color: #7f8c8d; margin: 0;">Average AI Confidence</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card" style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                        <h3 style="color: #27ae60; margin-bottom: 10px;">${format_currency(total_revenue_potential)}</h3>
                        <p style="color: #7f8c8d; margin: 0;">Total Revenue Potential</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card" style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                        <h3 style="color: #3498db; margin-bottom: 10px;">${data.length}</h3>
                        <p style="color: #7f8c8d; margin: 0;">Total Items Analyzed</p>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
            .trend-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #ecf0f1;
                height: 100%;
            }
            .trend-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #ecf0f1;
            }
            .trend-item:last-child {
                border-bottom: none;
            }
            .trend-label {
                font-weight: 500;
                color: #2c3e50;
            }
            .trend-value {
                font-weight: bold;
            }
        </style>
    `;
    
    frappe.msgprint({
        title: __("📈 Sales Trends Analysis"),
        message: trends_html,
        wide: true
    });
}

function export_to_excel(report) {
    const data = report.data || [];
    if (data.length === 0) {
        frappe.msgprint(__("No data to export"));
        return;
    }
    
    frappe.show_alert({message: __("Exporting to Excel..."), indicator: 'blue'});
    
    // Enhanced export with formatting
    const export_data = data.map(row => {
        return {
            'Item Code': row.item_code,
            'Item Name': row.item_name,
            'Customer': row.customer_name,
            'Territory': row.territory,
            'Company': row.company,
            'Predicted Quantity': row.predicted_qty,
            'Sales Trend': row.sales_trend,
            'Movement Type': row.movement_type,
            'Demand Pattern': row.demand_pattern,
            'Customer Score': row.customer_score,
            'Market Potential %': row.market_potential,
            'Seasonality Index': row.seasonality_index,
            'AI Confidence %': row.confidence_score,
            'Revenue Potential': row.revenue_potential,
            'Cross-sell Score': row.cross_sell_score,
            'Churn Risk': row.churn_risk,
            'Sales Alert': row.sales_alert ? 'Yes' : 'No',
            'Forecast Date': row.forecast_date,
            'Last Updated': row.last_forecast_date
        };
    });
    
    frappe.tools.downloadify(export_data, null, "AI_Sales_Dashboard_" + frappe.datetime.get_today());
}

function export_summary_report(report) {
    const summary = report.summary_data || [];
    const data = report.data || [];
    
    if (summary.length === 0) {
        frappe.msgprint(__("No summary data to export"));
        return;
    }
    
    let summary_text = "AI SALES DASHBOARD - EXECUTIVE SUMMARY\n";
    summary_text += "=" .repeat(50) + "\n\n";
    summary_text += `Report Generated: ${frappe.datetime.get_today()}\n`;
    summary_text += `Total Records: ${data.length}\n\n`;
    
    summary_text += "KEY METRICS:\n";
    summary_text += "-".repeat(20) + "\n";
    
    summary.forEach(item => {
        summary_text += `${item.label}: ${item.value}\n`;
    });
    
    // Create and download text file
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(summary_text));
    element.setAttribute('download', `AI_Sales_Summary_${frappe.datetime.get_today()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    
    frappe.show_alert({message: __("Summary report downloaded"), indicator: 'green'});
}

function create_bulk_sales_orders(report) {
    const selected_rows = report.datatable.getSelection();
    
    if (!selected_rows || selected_rows.length === 0) {
        frappe.msgprint(__("Please select rows to create sales orders"));
        return;
    }
    
    const forecast_ids = selected_rows.map(row => report.data[row[0]].forecast_id);
    
    frappe.confirm(
        __("Create sales orders for {0} selected forecasts?", [selected_rows.length]),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard.create_bulk_sales_orders",
                args: {forecast_ids: forecast_ids},
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Created {0} sales orders successfully!", [r.message.created_count]),
                            indicator: 'green'
                        });
                        
                        if (r.message.errors && r.message.errors.length > 0) {
                            frappe.msgprint({
                                title: __("Some errors occurred"),
                                message: r.message.errors.join("<br>"),
                                indicator: 'orange'
                            });
                        }
                        
                        report.refresh();
                    }
                }
            });
        }
    );
}

function update_bulk_forecasts(report) {
    const selected_rows = report.datatable.getSelection();
    
    if (!selected_rows || selected_rows.length === 0) {
        frappe.msgprint(__("Please select rows to update forecasts"));
        return;
    }
    
    const forecast_ids = selected_rows.map(row => report.data[row[0]].forecast_id);
    
    frappe.confirm(
        __("Refresh forecasts for {0} selected items?", [selected_rows.length]),
        function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.report.ai_sales_dashboard.ai_sales_dashboard.update_bulk_forecasts",
                args: {forecast_ids: forecast_ids},
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Updated {0} forecasts successfully!", [r.message.updated_count]),
                            indicator: 'green'
                        });
                        report.refresh();
                    }
                }
            });
        }
    );
}

function show_dashboard_settings() {
    const settings_html = `
        <div class="dashboard-settings">
            <h4>⚙️ Dashboard Settings</h4>
            <div class="form-group">
                <label>Auto-refresh interval (minutes):</label>
                <select class="form-control" id="refresh-interval">
                    <option value="0">Disabled</option>
                    <option value="1">1 minute</option>
                    <option value="5" selected>5 minutes</option>
                    <option value="10">10 minutes</option>
                    <option value="15">15 minutes</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="show-animations" checked>
                    Enable animations and transitions
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="compact-view">
                    Compact view mode
                </label>
            </div>
        </div>
    `;
    
    const dialog = new frappe.ui.Dialog({
        title: __("Dashboard Settings"),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'settings_html',
                options: settings_html
            }
        ],
        primary_action_label: __("Save Settings"),
        primary_action: function() {
            const refresh_interval = document.getElementById('refresh-interval').value;
            const show_animations = document.getElementById('show-animations').checked;
            const compact_view = document.getElementById('compact-view').checked;
            
            // Save to localStorage
            localStorage.setItem('ai_dashboard_settings', JSON.stringify({
                refresh_interval: refresh_interval,
                show_animations: show_animations,
                compact_view: compact_view
            }));
            
            frappe.show_alert({message: __("Settings saved"), indicator: 'green'});
            dialog.hide();
        }
    });
    
    dialog.show();
}

function add_summary_cards(report) {
    if (!report.summary_data || report.summary_data.length === 0) return;
    
    const summary_wrapper = $(`
        <div class="report-summary-cards" style="margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <div class="row" id="summary-cards-container"></div>
        </div>
    `);
    
    const cards_container = summary_wrapper.find('#summary-cards-container');
    
    // Show first 8 summary cards
    report.summary_data.slice(0, 8).forEach(function(item) {
        const indicator_colors = {
            'Red': '#e74c3c',
            'Green': '#27ae60', 
            'Blue': '#3498db',
            'Orange': '#f39c12',
            'Purple': '#9b59b6',
            'Grey': '#95a5a6'
        };
        
        const color = indicator_colors[item.indicator] || '#3498db';
        
        const card_html = `
            <div class="col-lg-3 col-md-6 col-sm-6 col-xs-12">
                <div class="summary-card" style="
                    background: white;
                    padding: 20px;
                    margin: 8px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-left: 4px solid ${color};
                    transition: transform 0.2s ease;
                " onmouseover="this.style.transform='translateY(-2px)'" 
                   onmouseout="this.style.transform='translateY(0)'">
                    <div class="summary-value" style="
                        font-size: 28px;
                        font-weight: bold;
                        color: ${color};
                        margin-bottom: 8px;
                    ">${item.value}</div>
                    <div class="summary-label" style="
                        font-size: 13px;
                        color: #7f8c8d;
                        font-weight: 500;
                        line-height: 1.3;
                    ">${item.label}</div>
                </div>
            </div>
        `;
        cards_container.append(card_html);
    });
    
    $('.layout-main-section .report-wrapper').prepend(summary_wrapper);
}

function enhance_report_layout(report) {
    // Add custom CSS for better styling
    const custom_css = `
        <style>
            .report-wrapper {
                background: #f8f9fa;
                min-height: 100vh;
            }
            
            .datatable-wrapper {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 20px;
                margin: 20px 0;
            }
            
            .dt-scrollable {
                border-radius: 6px;
                overflow: hidden;
            }
            
            .dt-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
            }
            
            .dt-row:hover {
                background-color: #f8f9ff !important;
            }
            
            .indicator {
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 0.8em;
                font-weight: 600;
            }
            
            .badge {
                border-radius: 12px;
                font-size: 0.75em;
            }
        </style>
    `;
    
    $('head').append(custom_css);
}

function format_currency(amount) {
    if (!amount || amount === 0) return '₹0';
    
    try {
        // Use Indian formatting as default, fallback to system settings
        const currency = frappe.boot.sysdefaults.currency || 'INR';
        const locale = currency === 'INR' ? 'en-IN' : 'en-US';
        
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    } catch (e) {
        // Fallback formatting
        return '₹' + amount.toLocaleString();
    }
}

// Additional utility functions
function get_priority_color(priority) {
    const colors = {
        'Critical': '#dc3545',
        'High': '#fd7e14', 
        'Medium': '#ffc107',
        'Low': '#28a745',
        'Normal': '#6c757d'
    };
    return colors[priority] || colors['Normal'];
}

function get_trend_icon(trend) {
    const icons = {
        'Increasing': '📈',
        'Decreasing': '📉',
        'Stable': '📊',
        'Volatile': '⚡',
        'Seasonal': '🔄',
        'Unknown': '❓'
    };
    return icons[trend] || icons['Unknown'];
}

function get_movement_style(movement_type) {
    const styles = {
        'Critical': {icon: '🚨', color: '#dc3545', weight: 'bold'},
        'Fast Moving': {icon: '🚀', color: '#28a745', weight: 'bold'},
        'Slow Moving': {icon: '🐌', color: '#ffc107', weight: 'bold'},
        'Non Moving': {icon: '⏸️', color: '#6c757d', weight: 'normal'},
        'Normal': {icon: '📊', color: '#17a2b8', weight: 'normal'}
    };
    return styles[movement_type] || styles['Normal'];
}

// Enhanced data processing functions
function process_forecast_data(data) {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(row => {
        // Ensure numeric fields are properly formatted
        row.predicted_qty = parseFloat(row.predicted_qty) || 0;
        row.confidence_score = parseFloat(row.confidence_score) || 0;
        row.customer_score = parseFloat(row.customer_score) || 0;
        row.market_potential = parseFloat(row.market_potential) || 0;
        row.revenue_potential = parseFloat(row.revenue_potential) || 0;
        row.cross_sell_score = parseFloat(row.cross_sell_score) || 0;
        row.seasonality_index = parseFloat(row.seasonality_index) || 1.0;
        
        // Ensure text fields have defaults
        row.sales_trend = row.sales_trend || 'Unknown';
        row.movement_type = row.movement_type || 'Normal';
        row.demand_pattern = row.demand_pattern || '📊 Unknown';
        row.churn_risk = row.churn_risk || '❓ Unknown';
        
        return row;
    });
}

// Performance monitoring
function monitor_report_performance() {
    const start_time = performance.now();
    
    return {
        end: function(operation_name) {
            const end_time = performance.now();
            const duration = end_time - start_time;
            
            if (duration > 2000) { // More than 2 seconds
                console.warn(`${operation_name} took ${duration.toFixed(2)}ms - consider optimization`);
            }
            
            return duration;
        }
    };
}

// Local storage utilities for user preferences
function save_user_preferences(preferences) {
    try {
        localStorage.setItem('ai_sales_dashboard_prefs', JSON.stringify(preferences));
    } catch (e) {
        console.warn('Could not save user preferences:', e);
    }
}

function load_user_preferences() {
    try {
        const prefs = localStorage.getItem('ai_sales_dashboard_prefs');
        return prefs ? JSON.parse(prefs) : {};
    } catch (e) {
        console.warn('Could not load user preferences:', e);
        return {};
    }
}

// Notification system
function show_success_notification(message) {
    frappe.show_alert({
        message: message,
        indicator: 'green'
    });
}

function show_error_notification(message) {
    frappe.show_alert({
        message: message,
        indicator: 'red'
    });
}

function show_info_notification(message) {
    frappe.show_alert({
        message: message,
        indicator: 'blue'
    });
}

// Data export utilities
function prepare_export_data(data, include_analytics = true) {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(row => {
        const export_row = {
            'Item Code': row.item_code || '',
            'Item Name': row.item_name || '',
            'Customer': row.customer_name || row.customer || '',
            'Territory': row.territory || '',
            'Company': row.company || '',
            'Predicted Quantity': row.predicted_qty || 0,
            'Sales Trend': row.sales_trend || '',
            'Movement Type': row.movement_type || '',
            'AI Confidence %': row.confidence_score || 0,
            'Sales Alert': row.sales_alert ? 'Yes' : 'No',
            'Forecast Date': row.forecast_date || '',
            'Last Updated': row.last_forecast_date || ''
        };
        
        if (include_analytics) {
            export_row['Demand Pattern'] = row.demand_pattern || '';
            export_row['Customer Score'] = row.customer_score || 0;
            export_row['Market Potential %'] = row.market_potential || 0;
            export_row['Seasonality Index'] = row.seasonality_index || 1.0;
            export_row['Revenue Potential'] = row.revenue_potential || 0;
            export_row['Cross-sell Score'] = row.cross_sell_score || 0;
            export_row['Churn Risk'] = row.churn_risk || '';
        }
        
        return export_row;
    });
}

// Chart configuration for advanced visualizations
function get_advanced_chart_config(chart_data) {
    return {
        title: 'Sales Forecast Distribution',
        data: chart_data.data,
        type: chart_data.type || 'bar',
        height: 350,
        colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'],
        axisOptions: {
            xAxisMode: 'tick',
            yAxisMode: 'tick',
            xIsSeries: false
        },
        barOptions: {
            spaceRatio: 0.3,
            stacked: false
        },
        lineOptions: {
            dotSize: 4,
            hideLine: false,
            heatline: true,
            regionFill: true
        },
        tooltipOptions: {
            formatTooltipX: d => d,
            formatTooltipY: d => d + ' items'
        }
    };
}

// Filter management
function get_active_filters(report) {
    const filters = report.get_values() || {};
    const active_filters = {};
    
    // Only include filters that have values
    Object.keys(filters).forEach(key => {
        if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
            active_filters[key] = filters[key];
        }
    });
    
    return active_filters;
}

function apply_smart_filters(report, filter_type) {
    switch(filter_type) {
        case 'high_priority':
            report.set_filter_value('sales_alert', 1);
            report.set_filter_value('critical_items_only', 1);
            break;
            
        case 'growth_opportunities':
            report.set_filter_value('sales_trend', ['Increasing']);
            report.set_filter_value('high_opportunity', 1);
            break;
            
        case 'risk_items':
            report.set_filter_value('movement_type', ['Critical', 'Slow Moving']);
            report.set_filter_value('low_confidence', 1);
            break;
            
        case 'clear_all':
            // Clear all filters
            const filter_names = ['company', 'customer', 'territory', 'item_group', 
                                'sales_trend', 'movement_type', 'sales_alert', 
                                'low_confidence', 'high_opportunity', 'fast_moving_only', 
                                'critical_items_only'];
            filter_names.forEach(filter => {
                report.set_filter_value(filter, null);
            });
            break;
    }
    
    report.refresh();
}

// Keyboard shortcuts
function setup_keyboard_shortcuts(report) {
    $(document).on('keydown', function(e) {
        // Only apply shortcuts when the report is active
        if (!$('.report-wrapper').is(':visible')) return;
        
        // Ctrl/Cmd + R: Refresh report
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            report.refresh();
            show_info_notification('🔄 Report refreshed');
        }
        
        // Ctrl/Cmd + E: Export to Excel
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            export_to_excel(report);
        }
        
        // Ctrl/Cmd + I: Show AI Insights
        if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
            e.preventDefault();
            show_ai_insights_dialog(report);
        }
        
        // Escape: Clear all filters
        if (e.key === 'Escape') {
            apply_smart_filters(report, 'clear_all');
            show_info_notification('🗑️ All filters cleared');
        }
    });
}

// Initialize dashboard on load
$(document).ready(function() {
    // Add custom styles
    if (!$('#ai-dashboard-styles').length) {
        $('head').append(`
            <style id="ai-dashboard-styles">
                .ai-dashboard-container {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px 0;
                }
                
                .report-summary-cards .summary-card:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                
                .datatable .dt-row.dt-row--highlight {
                    background-color: #fff3cd !important;
                    border-left: 4px solid #ffc107 !important;
                }
                
                .trend-indicator {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    padding: 2px 6px;
                    border-radius: 12px;
                    font-size: 0.8em;
                    font-weight: 500;
                }
                
                .confidence-badge {
                    border-radius: 12px;
                    padding: 3px 8px;
                    font-size: 0.75em;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }
                
                .priority-alert {
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.7; }
                    100% { opacity: 1; }
                }
                
                .report-actions {
                    display: flex;
                    gap: 10px;
                    margin: 15px 0;
                    flex-wrap: wrap;
                }
                
                .quick-filter-btn {
                    padding: 6px 12px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    background: white;
                    color: #495057;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-size: 0.85em;
                }
                
                .quick-filter-btn:hover {
                    background: #e9ecef;
                    border-color: #adb5bd;
                }
                
                .quick-filter-btn.active {
                    background: #007bff;
                    color: white;
                    border-color: #007bff;
                }
            </style>
        `);
    }
});

// Error handling wrapper
function safe_execute(func, error_message = "An error occurred") {
    return function(...args) {
        try {
            return func.apply(this, args);
        } catch (e) {
            console.error(error_message, e);
            show_error_notification(error_message);
            return null;
        }
    };
}

// Wrap main functions with error handling
const safe_show_ai_insights_dialog = safe_execute(show_ai_insights_dialog, "Failed to show AI insights");
const safe_export_to_excel = safe_execute(export_to_excel, "Failed to export data");
const safe_create_bulk_sales_orders = safe_execute(create_bulk_sales_orders, "Failed to create sales orders");

// Override original functions with safe versions
window.show_ai_insights_dialog = safe_show_ai_insights_dialog;
window.export_to_excel = safe_export_to_excel;
window.create_bulk_sales_orders = safe_create_bulk_sales_orders;

// Performance optimization: Debounce filter changes
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add quick filter buttons
function add_quick_filter_buttons(report) {
    const quick_filters_html = `
        <div class="report-actions">
            <button class="quick-filter-btn" data-filter="high_priority">
                🚨 High Priority
            </button>
            <button class="quick-filter-btn" data-filter="growth_opportunities">
                📈 Growth Items
            </button>
            <button class="quick-filter-btn" data-filter="risk_items">
                ⚠️ Risk Items
            </button>
            <button class="quick-filter-btn" data-filter="clear_all">
                🗑️ Clear All
            </button>
        </div>
    `;
    
    $('.layout-main-section .report-wrapper').prepend(quick_filters_html);
    
    // Add click handlers
    $('.quick-filter-btn').on('click', function() {
        $('.quick-filter-btn').removeClass('active');
        $(this).addClass('active');
        
        const filter_type = $(this).data('filter');
        apply_smart_filters(report, filter_type);
    });
}

console.log("🚀 AI Sales Dashboard JavaScript loaded successfully!");