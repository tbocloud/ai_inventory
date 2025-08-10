// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Expense Forecast", {
    refresh: function(frm) {
        // Add custom buttons and functionality
        add_custom_buttons(frm);
        
        // Setup field watchers
        setup_field_watchers(frm);
        
        // Auto-calculate totals on load
        if (!frm.is_new()) {
            calculate_expense_totals(frm);
        }
    },
    
    company: function(frm) {
        // Filter accounts based on company
        frm.set_query("expense_account", function() {
            return {
                filters: {
                    "company": frm.doc.company,
                    "account_type": "Expense Account",
                    "is_group": 0
                }
            };
        });
        
        frm.set_query("cost_center", function() {
            return {
                filters: {
                    "company": frm.doc.company,
                    "is_group": 0
                }
            };
        });
    },
    
    // Auto-calculate when expense fields change
    fixed_expenses: function(frm) { calculate_expense_totals(frm); },
    variable_expenses: function(frm) { calculate_expense_totals(frm); },
    semi_variable_expenses: function(frm) { calculate_expense_totals(frm); },
    inventory_related_expenses: function(frm) { calculate_expense_totals(frm); },
    operational_expenses: function(frm) { calculate_expense_totals(frm); },
    administrative_expenses: function(frm) { calculate_expense_totals(frm); },
    storage_costs: function(frm) { calculate_expense_totals(frm); },
    handling_costs: function(frm) { calculate_expense_totals(frm); },
    purchase_related_expenses: function(frm) { calculate_expense_totals(frm); },
    reorder_costs: function(frm) { calculate_expense_totals(frm); },
    carrying_costs: function(frm) { calculate_expense_totals(frm); },
    stockout_costs: function(frm) { calculate_expense_totals(frm); }
});

function add_custom_buttons(frm) {
    if (!frm.is_new()) {
        // Sync to Financial Forecast button
        frm.add_custom_button(__('Sync to Financial Forecast'), function() {
            sync_to_financial_forecast(frm);
        }, __('Sync'));
        
        // Analyze Expense Trends button
        frm.add_custom_button(__('Analyze Expense Trends'), function() {
            analyze_expense_trends(frm);
        }, __('AI Actions'));
        
        // Calculate Risk Factors button
        frm.add_custom_button(__('Calculate Risk Factors'), function() {
            calculate_risk_factors(frm);
        }, __('Analytics'));
        
        // Generate Optimization Suggestions button
        frm.add_custom_button(__('Generate Optimization Suggestions'), function() {
            generate_optimization_suggestions(frm);
        }, __('Optimize'));
    }
}

function setup_field_watchers(frm) {
    // Watch for currency changes
    frm.fields_dict.total_predicted_expense.$input.on('change', function() {
        calculate_expense_totals(frm);
    });
}

function calculate_expense_totals(frm) {
    // Calculate total predicted expenses
    let expense_fields = ['fixed_expenses', 'variable_expenses', 'semi_variable_expenses',
                         'inventory_related_expenses', 'operational_expenses', 'administrative_expenses',
                         'storage_costs', 'handling_costs', 'purchase_related_expenses',
                         'reorder_costs', 'carrying_costs', 'stockout_costs'];
    
    let total_expenses = 0;
    
    expense_fields.forEach(field => {
        total_expenses += (frm.doc[field] || 0);
    });
    
    // Update total
    frm.set_value('total_predicted_expense', total_expenses);
    
    // Calculate expense growth rate
    calculate_expense_growth_rate(frm, total_expenses);
    
    // Set confidence score based on data completeness
    let confidence = calculate_confidence_score(frm);
    frm.set_value('confidence_score', confidence);
    
    // Calculate prediction factors
    set_expense_factors(frm);
    
    // Calculate budget variance if budget data is available
    calculate_budget_variance(frm, total_expenses);
    
    // Refresh the form to show changes
    frm.refresh();
}

function calculate_expense_growth_rate(frm, current_expenses) {
    // This would typically compare with previous period data
    // For now, set a default growth rate based on expense types
    let growth_rate = 3; // Default 3% inflation
    
    // Higher growth for variable expenses
    let variable_portion = (frm.doc.variable_expenses || 0) + (frm.doc.semi_variable_expenses || 0);
    if (variable_portion > current_expenses * 0.5) {
        growth_rate = 5; // 5% for variable-heavy expenses
    }
    
    // Inventory-related expenses may grow faster
    let inventory_portion = (frm.doc.inventory_related_expenses || 0) + 
                           (frm.doc.storage_costs || 0) + 
                           (frm.doc.carrying_costs || 0);
    if (inventory_portion > current_expenses * 0.3) {
        growth_rate = 7; // 7% for inventory-heavy expenses
    }
    
    frm.set_value('expense_growth_rate', growth_rate);
}

function calculate_confidence_score(frm) {
    let total_fields = 12; // Major expense fields
    let filled_fields = 0;
    
    let key_fields = ['fixed_expenses', 'variable_expenses', 'operational_expenses', 
                     'administrative_expenses', 'inventory_related_expenses',
                     'storage_costs', 'handling_costs', 'purchase_related_expenses',
                     'company', 'forecast_date', 'expense_account', 'cost_center'];
    
    key_fields.forEach(field => {
        if (frm.doc[field] && (typeof frm.doc[field] === 'string' || frm.doc[field] > 0)) {
            filled_fields++;
        }
    });
    
    return Math.round((filled_fields / total_fields) * 100);
}

function set_expense_factors(frm) {
    // Set seasonal adjustment
    let current_month = new Date().getMonth() + 1;
    let seasonal_adjustment = 1.0;
    
    // Holiday seasons typically have higher expenses
    if (current_month === 12) {
        seasonal_adjustment = 1.15; // 15% boost for December
    } else if (current_month === 1) {
        seasonal_adjustment = 0.95; // 5% reduction for January
    }
    
    frm.set_value('seasonal_adjustment', seasonal_adjustment);
    
    // Set inflation factor (simplified)
    frm.set_value('inflation_factor', 3.5); // 3.5% average inflation
    
    // Set efficiency factor
    let efficiency_factor = 1.0;
    let confidence = frm.doc.confidence_score || 0;
    
    if (confidence >= 80) {
        efficiency_factor = 1.05; // 5% efficiency gain for high confidence
    } else if (confidence <= 50) {
        efficiency_factor = 0.95; // 5% efficiency loss for low confidence
    }
    
    frm.set_value('efficiency_factor', efficiency_factor);
}

function calculate_budget_variance(frm, actual_expenses) {
    // This would typically compare with budget data
    // For now, assume a budget exists and calculate variance
    let assumed_budget = actual_expenses * 1.1; // Assume budget is 10% higher
    let variance = ((actual_expenses - assumed_budget) / assumed_budget) * 100;
    
    frm.set_value('budget_variance', variance);
    
    // Set alert status based on variance
    let alert_status = 'Normal';
    if (Math.abs(variance) > 20) {
        alert_status = 'Critical';
    } else if (Math.abs(variance) > 10) {
        alert_status = 'Warning';
    }
    
    frm.set_value('alert_status', alert_status);
}

function sync_to_financial_forecast(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_expense_forecast.ai_expense_forecast.sync_with_financial_forecast",
        args: {
            expense_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __("Successfully synced to AI Financial Forecast"),
                    indicator: 'green'
                });
                
                if (r.message.financial_forecast_name) {
                    frappe.set_route("Form", "AI Financial Forecast", r.message.financial_forecast_name);
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

function analyze_expense_trends(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_expense_forecast.ai_expense_forecast.analyze_expense_trends",
        args: {
            expense_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("Expense trends analyzed successfully"),
                    indicator: 'green'
                });
            }
        }
    });
}

function calculate_risk_factors(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_expense_forecast.ai_expense_forecast.calculate_expense_risks",
        args: {
            expense_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let risk_level = r.message.risk_level || 'Unknown';
                let color = risk_level === 'Low' ? 'green' : (risk_level === 'Medium' ? 'orange' : 'red');
                
                frappe.show_alert({
                    message: __("Risk Level: ") + risk_level + " - " + (r.message.message || ""),
                    indicator: color
                });
                
                frm.reload_doc();
            }
        }
    });
}

function generate_optimization_suggestions(frm) {
    // Calculate optimization suggestions based on expense breakdown
    let suggestions = [];
    
    let total_expense = frm.doc.total_predicted_expense || 0;
    
    // Check for high fixed expenses
    if ((frm.doc.fixed_expenses || 0) > total_expense * 0.6) {
        suggestions.push("Consider reducing fixed expenses - they represent >60% of total expenses");
    }
    
    // Check for high inventory costs
    let inventory_costs = (frm.doc.inventory_related_expenses || 0) + 
                         (frm.doc.storage_costs || 0) + 
                         (frm.doc.carrying_costs || 0);
    if (inventory_costs > total_expense * 0.3) {
        suggestions.push("High inventory costs detected - consider optimizing stock levels and storage");
    }
    
    // Check for high operational expenses
    if ((frm.doc.operational_expenses || 0) > total_expense * 0.4) {
        suggestions.push("Operational expenses are high - review processes for efficiency improvements");
    }
    
    // Set optimization suggestions
    frm.set_value('optimization_suggestions', suggestions.join('\n'));
    
    frappe.show_alert({
        message: __("Generated ") + suggestions.length + __(" optimization suggestions"),
        indicator: 'blue'
    });
}
