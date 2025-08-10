// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Revenue Forecast", {
    refresh: function(frm) {
        // Add custom buttons and functionality
        add_custom_buttons(frm);
        
        // Setup field watchers
        setup_field_watchers(frm);
        
        // Auto-calculate totals on load
        if (!frm.is_new()) {
            calculate_revenue_totals(frm);
        }
    },
    
    company: function(frm) {
        // Filter accounts and territories based on company
        frm.set_query("revenue_account", function() {
            return {
                filters: {
                    "company": frm.doc.company,
                    "account_type": "Income Account",
                    "is_group": 0
                }
            };
        });
    },
    
    // Auto-calculate when revenue fields change
    product_revenue: function(frm) { calculate_revenue_totals(frm); },
    service_revenue: function(frm) { calculate_revenue_totals(frm); },
    recurring_revenue: function(frm) { calculate_revenue_totals(frm); },
    one_time_revenue: function(frm) { calculate_revenue_totals(frm); },
    commission_revenue: function(frm) { calculate_revenue_totals(frm); },
    other_revenue: function(frm) { calculate_revenue_totals(frm); }
});

function add_custom_buttons(frm) {
    if (!frm.is_new()) {
        // Sync to Financial Forecast button
        frm.add_custom_button(__('Sync to Financial Forecast'), function() {
            sync_to_financial_forecast(frm);
        }, __('Sync'));
        
        // Analyze Growth Trends button
        frm.add_custom_button(__('Analyze Growth Trends'), function() {
            analyze_growth_trends(frm);
        }, __('AI Actions'));
        
        // Calculate Historical Accuracy button
        frm.add_custom_button(__('Calculate Historical Accuracy'), function() {
            calculate_historical_accuracy(frm);
        }, __('Analytics'));
        
        // Set Inventory Integration button
        frm.add_custom_button(__('Set Inventory Integration'), function() {
            set_inventory_integration(frm);
        }, __('Integration'));

        // Populate from Sales (month) button
        frm.add_custom_button(__('Populate from Sales (month)'), function() {
            populate_from_sales(frm);
        }, __('AI Actions'));
    }
}

function setup_field_watchers(frm) {
    // Watch for currency changes
    frm.fields_dict.total_predicted_revenue.$input.on('change', function() {
        calculate_revenue_totals(frm);
    });
}

function calculate_revenue_totals(frm) {
    // Calculate total predicted revenue
    let revenue_fields = ['product_revenue', 'service_revenue', 'recurring_revenue',
                         'one_time_revenue', 'commission_revenue', 'other_revenue'];
    let total_revenue = 0;
    
    revenue_fields.forEach(field => {
        total_revenue += (frm.doc[field] || 0);
    });
    
    // Update total
    frm.set_value('total_predicted_revenue', total_revenue);
    
    // Calculate growth rate if we have historical data
    calculate_growth_rate(frm, total_revenue);
    
    // Set confidence score based on data completeness
    let confidence = calculate_confidence_score(frm);
    frm.set_value('confidence_score', confidence);
    
    // Calculate seasonal and market factors
    set_prediction_factors(frm);
    
    // Refresh the form to show changes
    frm.refresh();
}

function calculate_growth_rate(frm, current_revenue) {
    // This would typically compare with previous period data
    // For now, set a default growth rate based on revenue size
    let growth_rate = 0;
    
    if (current_revenue > 1000000) {
        growth_rate = 5; // 5% for large revenue
    } else if (current_revenue > 500000) {
        growth_rate = 8; // 8% for medium revenue
    } else if (current_revenue > 100000) {
        growth_rate = 12; // 12% for small revenue
    } else {
        growth_rate = 15; // 15% for very small revenue
    }
    
    frm.set_value('growth_rate', growth_rate);
}

function calculate_confidence_score(frm) {
    let total_fields = 8; // Major revenue fields
    let filled_fields = 0;
    
    let key_fields = ['product_revenue', 'service_revenue', 'recurring_revenue', 
                     'one_time_revenue', 'commission_revenue', 'other_revenue',
                     'company', 'forecast_date'];
    
    key_fields.forEach(field => {
        if (frm.doc[field] && (typeof frm.doc[field] === 'string' || frm.doc[field] > 0)) {
            filled_fields++;
        }
    });
    
    return Math.round((filled_fields / total_fields) * 100);
}

function set_prediction_factors(frm) {
    // Set seasonal factor (simplified)
    let current_month = new Date().getMonth() + 1;
    let seasonal_factor = 1.0;
    
    // Holiday seasons typically have higher revenue
    if (current_month === 12 || current_month === 11) {
        seasonal_factor = 1.2; // 20% boost for holiday season
    } else if (current_month >= 6 && current_month <= 8) {
        seasonal_factor = 1.1; // 10% boost for summer
    } else if (current_month >= 1 && current_month <= 2) {
        seasonal_factor = 0.9; // 10% reduction for post-holiday
    }
    
    frm.set_value('seasonal_factor', seasonal_factor);
    
    // Set market factor (simplified)
    frm.set_value('market_factor', 1.0);
    
    // Set risk adjustment
    let risk_adjustment = 0;
    let confidence = frm.doc.confidence_score || 0;
    
    if (confidence >= 80) {
        risk_adjustment = 2; // Low risk
    } else if (confidence >= 60) {
        risk_adjustment = 5; // Medium risk
    } else {
        risk_adjustment = 10; // High risk
    }
    
    frm.set_value('risk_adjustment', risk_adjustment);
}

function sync_to_financial_forecast(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_revenue_forecast.ai_revenue_forecast.sync_with_financial_forecast",
        args: {
            revenue_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Successfully synced to AI Financial Forecast"),
                    indicator: 'green'
                });
                if (r.message.financial_forecast_name || r.message.result?.forecast_id) {
                    const target = r.message.financial_forecast_name || r.message.result?.forecast_id;
                    frappe.set_route("Form", "AI Financial Forecast", target);
                }
            } else {
                frappe.show_alert({
                    message: __("Sync failed: ") + (r.message?.error || "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

function analyze_growth_trends(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_revenue_forecast.ai_revenue_forecast.analyze_growth_trends",
        args: {
            revenue_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("Growth trends analyzed successfully"),
                    indicator: 'green'
                });
            }
        }
    });
}

function calculate_historical_accuracy(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_revenue_forecast.ai_revenue_forecast.calculate_historical_accuracy",
        args: {
            revenue_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let accuracy = r.message.accuracy || 0;
                frappe.show_alert({
                    message: __("Historical Accuracy: ") + accuracy.toFixed(1) + "%",
                    indicator: accuracy >= 75 ? 'green' : (accuracy >= 50 ? 'orange' : 'red')
                });
                
                frm.reload_doc();
            }
        }
    });
}

function set_inventory_integration(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_revenue_forecast.ai_revenue_forecast.set_inventory_integration",
        args: {
            revenue_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("Inventory integration updated successfully"),
                    indicator: 'green'
                });
            }
        }
    });
}

function populate_from_sales(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_revenue_forecast.ai_revenue_forecast.populate_from_sales",
        args: {
            revenue_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("Populated from Sales and recalculated"),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __("Populate failed: ") + (r.message?.error || "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}
