// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Cashflow Forecast", {
    refresh: function(frm) {
        // Add custom buttons and functionality
        add_custom_buttons(frm);
        
        // Setup field watchers
        setup_field_watchers(frm);
        
        // Auto-calculate totals on load
        if (!frm.is_new()) {
            calculate_cashflow_totals(frm);
        }
    },
    
    company: function(frm) {
        // Filter accounts based on company
        frm.set_query("cash_account", function() {
            return {
                filters: {
                    "company": frm.doc.company,
                    "account_type": "Cash",
                    "is_group": 0
                }
            };
        });
    },
    
    // Auto-calculate when inflow fields change
    receivables_collection: function(frm) { calculate_cashflow_totals(frm); },
    sales_forecast_amount: function(frm) { calculate_cashflow_totals(frm); },
    other_income: function(frm) { calculate_cashflow_totals(frm); },
    investment_returns: function(frm) { calculate_cashflow_totals(frm); },
    loan_proceeds: function(frm) { calculate_cashflow_totals(frm); },
    
    // Auto-calculate when outflow fields change
    payables_payment: function(frm) { calculate_cashflow_totals(frm); },
    inventory_purchases: function(frm) { calculate_cashflow_totals(frm); },
    operating_expenses: function(frm) { calculate_cashflow_totals(frm); },
    capital_expenditure: function(frm) { calculate_cashflow_totals(frm); },
    loan_payments: function(frm) { calculate_cashflow_totals(frm); },
    
    opening_balance: function(frm) { calculate_cashflow_totals(frm); },
    minimum_cash_required: function(frm) { calculate_cashflow_totals(frm); }
});

function add_custom_buttons(frm) {
    if (!frm.is_new()) {
        // Sync to Financial Forecast button
        frm.add_custom_button(__('Sync to Financial Forecast'), function() {
            sync_to_financial_forecast(frm);
        }, __('Sync'));
        
        // Calculate Predictions button
        frm.add_custom_button(__('Calculate AI Predictions'), function() {
            calculate_ai_predictions(frm);
        }, __('AI Actions'));
        
        // Validate Cash Requirements button
        frm.add_custom_button(__('Validate Cash Requirements'), function() {
            validate_cash_requirements(frm);
        }, __('Validate'));

        // Populate from GL button (fills monthly inflow/outflow from GL)
        frm.add_custom_button(__('Populate from GL (month)'), function() {
            populate_from_gl(frm);
        }, __('AI Actions'));

        // Recalculate Totals button
        frm.add_custom_button(__('Recalculate Totals'), function() {
            calculate_cashflow_totals(frm);
            frm.save_or_update();
        }, __('Validate'));
    }
}

function setup_field_watchers(frm) {
    // Watch for currency changes
    frm.fields_dict.predicted_inflows.$input.on('change', function() {
        calculate_cashflow_totals(frm);
    });
    
    frm.fields_dict.predicted_outflows.$input.on('change', function() {
        calculate_cashflow_totals(frm);
    });
}

function calculate_cashflow_totals(frm) {
    // Calculate total inflows
    let inflow_fields = ['receivables_collection', 'sales_forecast_amount', 'other_income', 
                        'investment_returns', 'loan_proceeds'];
    let total_inflows = 0;
    
    inflow_fields.forEach(field => {
        total_inflows += (frm.doc[field] || 0);
    });
    
    // Calculate total outflows
    let outflow_fields = ['payables_payment', 'inventory_purchases', 'operating_expenses',
                         'capital_expenditure', 'loan_payments'];
    let total_outflows = 0;
    
    outflow_fields.forEach(field => {
        total_outflows += (frm.doc[field] || 0);
    });
    
    // Calculate net cash flow
    let net_cash_flow = total_inflows - total_outflows;
    
    // Calculate closing balance
    let opening_balance = frm.doc.opening_balance || 0;
    let closing_balance = opening_balance + net_cash_flow;
    
    // Calculate surplus/deficit
    let minimum_required = frm.doc.minimum_cash_required || 0;
    let surplus_deficit = closing_balance - minimum_required;
    
    // Calculate liquidity ratio
    let liquidity_ratio = total_outflows > 0 ? (total_inflows / total_outflows) * 100 : 100;
    
    // Update fields
    frm.set_value('predicted_inflows', total_inflows);
    frm.set_value('predicted_outflows', total_outflows);
    frm.set_value('net_cash_flow', net_cash_flow);
    frm.set_value('closing_balance', closing_balance);
    frm.set_value('surplus_deficit', surplus_deficit);
    frm.set_value('liquidity_ratio', liquidity_ratio);
    
    // Set confidence score based on data completeness
    let confidence = calculate_confidence_score(frm);
    frm.set_value('confidence_score', confidence);
    
    // Refresh the form to show changes
    frm.refresh();
}

function calculate_confidence_score(frm) {
    let total_fields = 10; // Major cashflow fields
    let filled_fields = 0;
    
    let key_fields = ['receivables_collection', 'sales_forecast_amount', 'payables_payment', 
                     'inventory_purchases', 'operating_expenses', 'opening_balance',
                     'minimum_cash_required', 'capital_expenditure', 'other_income', 'loan_payments'];
    
    key_fields.forEach(field => {
        if (frm.doc[field] && frm.doc[field] > 0) {
            filled_fields++;
        }
    });
    
    return Math.round((filled_fields / total_fields) * 100);
}

function sync_to_financial_forecast(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_cashflow_forecast.ai_cashflow_forecast.sync_with_financial_forecast",
        args: {
            cashflow_name: frm.doc.name
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

function calculate_ai_predictions(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_cashflow_forecast.ai_cashflow_forecast.set_ai_predictions",
        args: {
            cashflow_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("AI predictions calculated successfully"),
                    indicator: 'green'
                });
            }
        }
    });
}

function validate_cash_requirements(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_cashflow_forecast.ai_cashflow_forecast.validate_cash_requirements",
        args: {
            cashflow_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let status = r.message.status || 'Unknown';
                let color = status === 'Healthy' ? 'green' : (status === 'Warning' ? 'orange' : 'red');
                
                frappe.show_alert({
                    message: __("Cash Status: ") + status + " - " + (r.message.message || ""),
                    indicator: color
                });
            }
        }
    });
}

function populate_from_gl(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_cashflow_forecast.ai_cashflow_forecast.populate_from_gl",
        args: { cashflow_name: frm.doc.name },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("Populated from GL and recalculated"),
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
