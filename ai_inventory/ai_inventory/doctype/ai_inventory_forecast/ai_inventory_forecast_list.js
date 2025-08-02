// AI Inventory Forecast List View JavaScript

frappe.listview_settings['AI Inventory Forecast'] = {
    add_fields: ["prediction_confidence", "stock_alert", "movement_type", "predicted_consumption", "reorder_level"],
    
    get_indicator: function(doc) {
        // Color indicators based on confidence and alerts
        if (doc.stock_alert == 1) {
            return [__("Stock Alert"), "red", "stock_alert,=,1"];
        } else if (doc.prediction_confidence >= 80) {
            return [__("High Confidence"), "green", "prediction_confidence,>=,80"];
        } else if (doc.prediction_confidence >= 60) {
            return [__("Medium Confidence"), "orange", "prediction_confidence,>=,60"];
        } else if (doc.prediction_confidence < 60) {
            return [__("Low Confidence"), "red", "prediction_confidence,<,60"];
        } else if (doc.movement_type == 'Critical') {
            return [__("Critical"), "red", "movement_type,=,Critical"];
        } else if (doc.movement_type == 'Fast Moving') {
            return [__("Fast Moving"), "green", "movement_type,=,Fast Moving"];
        }
        return [__("Normal"), "blue"];
    },
    
    formatters: {
        prediction_confidence(value) {
            if (!value) return '';
            
            let color = value >= 80 ? 'green' : value >= 60 ? 'orange' : 'red';
            let badge_class = value >= 80 ? 'success' : value >= 60 ? 'warning' : 'danger';
            
            return `<span class="badge badge-${badge_class}" style="color: white; font-weight: bold;">
                ${value.toFixed(1)}%</span>`;
        },
        
        predicted_consumption(value) {
            if (!value) return '';
            return `<span style="font-weight: 500;">${parseFloat(value).toLocaleString()}</span>`;
        },
        
        reorder_level(value) {
            if (!value) return '';
            return `<span style="font-weight: 500; color: #fd7e14;">${parseFloat(value).toLocaleString()}</span>`;
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
                method: "ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.sync_ai_inventory_forecasts_now",
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Inventory forecasts refreshed successfully!"),
                            indicator: 'green'
                        });
                        listview.refresh();
                    }
                }
            });
        });
        
        listview.page.add_action_item(__("📊 Dashboard"), function() {
            frappe.set_route("query-report", "AI Inventory Dashboard");
        });
        
        listview.page.add_action_item(__("📦 Purchase Orders"), function() {
            frappe.call({
                method: "ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.create_purchase_orders_from_forecasts",
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Purchase orders created successfully!"),
                            indicator: 'green'
                        });
                        frappe.set_route("List", "Purchase Order");
                    }
                }
            });
        });
        
        // Add quick filters
        this.add_quick_filters(listview);
    },
    
    add_quick_filters: function(listview) {
        // High confidence filter
        listview.page.add_inner_button(__("High Confidence"), function() {
            listview.filter_area.add([
                ["AI Inventory Forecast", "prediction_confidence", ">=", 80]
            ]);
        }, __("Quick Filters"));
        
        // Stock alerts filter
        listview.page.add_inner_button(__("Stock Alerts"), function() {
            listview.filter_area.add([
                ["AI Inventory Forecast", "stock_alert", "=", 1]
            ]);
        }, __("Quick Filters"));
        
        // Critical items filter
        listview.page.add_inner_button(__("Critical Items"), function() {
            listview.filter_area.add([
                ["AI Inventory Forecast", "movement_type", "=", "Critical"]
            ]);
        }, __("Quick Filters"));
        
        // Fast moving filter
        listview.page.add_inner_button(__("Fast Moving"), function() {
            listview.filter_area.add([
                ["AI Inventory Forecast", "movement_type", "=", "Fast Moving"]
            ]);
        }, __("Quick Filters"));
        
        // Low stock filter
        listview.page.add_inner_button(__("Low Stock"), function() {
            listview.filter_area.add([
                ["AI Inventory Forecast", "current_stock", "<=", "reorder_level"]
            ]);
        }, __("Quick Filters"));
    },
    
    // Custom primary action
    primary_action: function() {
        frappe.new_doc("AI Inventory Forecast");
    }
};

// Add custom CSS for better styling
frappe.ready(function() {
    $(`<style>
        .list-row[data-doctype="AI Inventory Forecast"] {
            border-left: 3px solid transparent;
        }
        
        .list-row[data-doctype="AI Inventory Forecast"][data-stock-alert="1"] {
            border-left-color: #dc3545;
            background-color: #fff5f5;
        }
        
        .list-row[data-doctype="AI Inventory Forecast"][data-movement-type="Critical"] {
            border-left-color: #fd7e14;
            background-color: #fff8f0;
        }
        
        .list-row[data-doctype="AI Inventory Forecast"][data-movement-type="Fast Moving"] {
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

console.log("🚀 AI Inventory Forecast List View JavaScript loaded successfully!");
