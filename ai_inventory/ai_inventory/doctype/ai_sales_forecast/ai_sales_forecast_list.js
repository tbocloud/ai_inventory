// AI Sales Forecast List View JavaScript

frappe.listview_settings['AI Sales Forecast'] = {
    add_fields: ["confidence_score", "sales_alert", "movement_type", "sales_trend", "predicted_qty"],
    
    get_indicator: function(doc) {
        // Color indicators based on confidence and alerts
        if (doc.sales_alert == 1) {
            return [__("Sales Alert"), "red", "sales_alert,=,1"];
        } else if (doc.confidence_score >= 80) {
            return [__("High Confidence"), "green", "confidence_score,>=,80"];
        } else if (doc.confidence_score >= 60) {
            return [__("Medium Confidence"), "orange", "confidence_score,>=,60"];
        } else if (doc.confidence_score < 60) {
            return [__("Low Confidence"), "red", "confidence_score,<,60"];
        } else if (doc.movement_type == 'Critical') {
            return [__("Critical"), "red", "movement_type,=,Critical"];
        } else if (doc.movement_type == 'Fast Moving') {
            return [__("Fast Moving"), "green", "movement_type,=,Fast Moving"];
        }
        return [__("Normal"), "blue"];
    },
    
    formatters: {
        confidence_score(value) {
            if (!value) return '';
            
            let color = value >= 80 ? 'green' : value >= 60 ? 'orange' : 'red';
            let badge_class = value >= 80 ? 'success' : value >= 60 ? 'warning' : 'danger';
            
            return `<span class="badge badge-${badge_class}" style="color: white; font-weight: bold;">
                ${value.toFixed(1)}%</span>`;
        },
        
        predicted_qty(value) {
            if (!value) return '';
            return `<span style="font-weight: 500;">${parseFloat(value).toLocaleString()}</span>`;
        },
        
        sales_trend(value) {
            if (!value) return '';
            
            const trend_icons = {
                "Increasing": "📈",
                "Decreasing": "📉", 
                "Stable": "📊",
                "Volatile": "⚡",
                "Seasonal": "🔄"
            };
            
            const trend_colors = {
                "Increasing": "#28a745",
                "Decreasing": "#dc3545",
                "Stable": "#17a2b8",
                "Volatile": "#fd7e14",
                "Seasonal": "#6f42c1"
            };
            
            const icon = trend_icons[value] || "❓";
            const color = trend_colors[value] || "#6c757d";
            
            return `<span style="color: ${color}; font-weight: 500;">
                ${icon} ${value}</span>`;
        },
        
        movement_type(value) {
            if (!value) return '';
            
            const movement_styles = {
                "Critical": {icon: "🚨", color: "#d73527", weight: "bold"},
                "Fast Moving": {icon: "🚀", color: "#28a745", weight: "bold"},
                "Slow Moving": {icon: "🐌", color: "#ffc107", weight: "bold"},
                "Non Moving": {icon: "⏸️", color: "#6c757d", weight: "normal"},
                "Normal": {icon: "📊", color: "#17a2b8", weight: "normal"}
            };
            
            const style = movement_styles[value] || movement_styles["Normal"];
            return `<span style="color: ${style.color}; font-weight: ${style.weight};">
                ${style.icon} ${value}</span>`;
        }
    },
    
    onload: function(listview) {
        // Add custom buttons
        listview.page.add_action_item(__("🔄 Refresh Forecasts"), function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_sales_forecast.ai_sales_forecast.sync_ai_sales_forecasts_now",
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Forecasts refreshed successfully!"),
                            indicator: 'green'
                        });
                        listview.refresh();
                    }
                }
            });
        });
        
        listview.page.add_action_item(__("📊 Dashboard"), function() {
            frappe.set_route("query-report", "AI Sales Dashboard");
        });
        
        // Add quick filters
        this.add_quick_filters(listview);
    },
    
    add_quick_filters: function(listview) {
        // High confidence filter
        listview.page.add_inner_button(__("High Confidence"), function() {
            listview.filter_area.add([
                ["AI Sales Forecast", "confidence_score", ">=", 80]
            ]);
        }, __("Quick Filters"));
        
        // Sales alerts filter
        listview.page.add_inner_button(__("Sales Alerts"), function() {
            listview.filter_area.add([
                ["AI Sales Forecast", "sales_alert", "=", 1]
            ]);
        }, __("Quick Filters"));
        
        // Critical items filter
        listview.page.add_inner_button(__("Critical Items"), function() {
            listview.filter_area.add([
                ["AI Sales Forecast", "movement_type", "=", "Critical"]
            ]);
        }, __("Quick Filters"));
        
        // Fast moving filter
        listview.page.add_inner_button(__("Fast Moving"), function() {
            listview.filter_area.add([
                ["AI Sales Forecast", "movement_type", "=", "Fast Moving"]
            ]);
        }, __("Quick Filters"));
    },
    
    // Custom primary action
    primary_action: function() {
        frappe.new_doc("AI Sales Forecast");
    }
};

// Add custom CSS for better styling
frappe.ready(function() {
    $(`<style>
        .list-row[data-doctype="AI Sales Forecast"] {
            border-left: 3px solid transparent;
        }
        
        .list-row[data-doctype="AI Sales Forecast"][data-sales-alert="1"] {
            border-left-color: #dc3545;
            background-color: #fff5f5;
        }
        
        .list-row[data-doctype="AI Sales Forecast"][data-movement-type="Critical"] {
            border-left-color: #fd7e14;
            background-color: #fff8f0;
        }
        
        .list-row[data-doctype="AI Sales Forecast"][data-movement-type="Fast Moving"] {
            border-left-color: #28a745;
            background-color: #f8fff9;
        }
        
        .badge {
            border-radius: 12px;
            font-size: 0.75em;
            padding: 3px 8px;
        }
    </style>`).appendTo('head');
});

console.log("🚀 AI Sales Forecast List View JavaScript loaded successfully!");
