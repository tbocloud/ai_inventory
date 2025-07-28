// ai_inventory/public/js/purchase_order.js

frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        // Add ML prediction button
        if (!frm.is_new()) {
            frm.add_custom_button(__('🤖 Get ML Price Predictions'), function() {
                get_ml_price_predictions_for_po(frm);
            }, __('AI Tools'));
        }
        
        // Add auto-create from forecasts button
        if (frm.is_new()) {
            frm.add_custom_button(__('📊 Create from AI Forecasts'), function() {
                create_po_from_forecasts(frm);
            }, __('AI Tools'));
        }
    },
    
    supplier: function(frm) {
        if (frm.doc.supplier && !frm.is_new()) {
            // Auto-populate ML predictions when supplier is selected
            setTimeout(() => {
                get_ml_price_predictions_for_po(frm);
            }, 1000);
        }
    }
});

frappe.ui.form.on('Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && frm.doc.supplier) {
            // Get ML price prediction for this item
            get_ml_price_prediction_for_item(frm, row, cdt, cdn);
        }
    },
    
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && frm.doc.supplier && row.qty > 0) {
            // Update ML price prediction based on quantity
            get_ml_price_prediction_for_item(frm, row, cdt, cdn);
        }
    }
});

function get_ml_price_predictions_for_po(frm) {
    if (!frm.doc.supplier) {
        frappe.msgprint(__('Please select a supplier first'));
        return;
    }
    
    if (!frm.doc.items || frm.doc.items.length === 0) {
        frappe.msgprint(__('Please add items to get price predictions'));
        return;
    }
    
    let dialog = new frappe.ui.Dialog({
        title: __('🤖 ML Price Predictions for {0}', [frm.doc.supplier]),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'predictions_area'
            }
        ]
    });
    
    dialog.show();
    
    let predictions_wrapper = dialog.fields_dict.predictions_area.$wrapper;
    predictions_wrapper.html(`
        <div class="text-center" style="padding: 20px;">
            <i class="fa fa-brain fa-spin fa-2x text-primary"></i>
            <h4 style="margin-top: 15px;">Analyzing Price Predictions...</h4>
            <p class="text-muted">Using ML to predict optimal prices based on historical data</p>
        </div>
    `);
    
    // Get predictions for all items
    let predictions_promises = [];
    
    frm.doc.items.forEach((item, index) => {
        if (item.item_code) {
            let promise = new Promise((resolve) => {
                frappe.call({
                    method: 'ai_inventory.ml_supplier_analyzer.predict_purchase_price',
                    args: {
                        item_code: item.item_code,
                        supplier: frm.doc.supplier,
                        company: frm.doc.company,
                        qty: item.qty || 1
                    },
                    callback: function(r) {
                        resolve({
                            index: index,
                            item_code: item.item_code,
                            current_rate: item.rate || 0,
                            prediction: r.message || {}
                        });
                    },
                    error: function() {
                        resolve({
                            index: index,
                            item_code: item.item_code,
                            current_rate: item.rate || 0,
                            prediction: { status: 'error', message: 'Prediction failed' }
                        });
                    }
                });
            });
            predictions_promises.push(promise);
        }
    });
    
    Promise.all(predictions_promises).then((results) => {
        display_price_predictions(predictions_wrapper, results, frm, dialog);
    });
}

function display_price_predictions(wrapper, predictions, frm, dialog) {
    let html = `
        <div style="padding: 15px;">
            <h4>🤖 ML Price Predictions Analysis</h4>
            <p class="text-muted">Predicted prices based on historical purchase data and market analysis</p>
            
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Item Code</th>
                        <th>Current Rate</th>
                        <th>ML Predicted Rate</th>
                        <th>Difference</th>
                        <th>Confidence</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    let total_savings = 0;
    let high_confidence_count = 0;
    
    predictions.forEach((pred) => {
        let prediction = pred.prediction;
        let predicted_price = prediction.predicted_price || 0;
        let confidence = prediction.confidence || 0;
        let current_rate = pred.current_rate;
        
        let difference = predicted_price - current_rate;
        let difference_percent = current_rate > 0 ? (difference / current_rate) * 100 : 0;
        
        let difference_color = difference > 0 ? 'text-danger' : 'text-success';
        let confidence_color = confidence > 80 ? 'text-success' : confidence > 60 ? 'text-warning' : 'text-danger';
        
        if (confidence > 70) {
            high_confidence_count++;
            total_savings += Math.abs(difference) * (frm.doc.items[pred.index].qty || 1);
        }
        
        html += `
            <tr>
                <td><strong>${pred.item_code}</strong></td>
                <td>₹${current_rate.toFixed(2)}</td>
                <td>₹${predicted_price.toFixed(2)}</td>
                <td class="${difference_color}">
                    ${difference >= 0 ? '+' : ''}₹${difference.toFixed(2)}
                    (${difference_percent >= 0 ? '+' : ''}${difference_percent.toFixed(1)}%)
                </td>
                <td class="${confidence_color}">${confidence}%</td>
                <td>
                    ${confidence > 60 ? 
                        `<button class="btn btn-xs btn-primary" onclick="apply_predicted_price(${pred.index}, ${predicted_price}, ${confidence})">Apply</button>` :
                        '<span class="text-muted">Low confidence</span>'
                    }
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
            
            <div class="alert alert-info">
                <h5>📊 Prediction Summary</h5>
                <ul>
                    <li><strong>High Confidence Predictions:</strong> ${high_confidence_count} out of ${predictions.length} items</li>
                    <li><strong>Potential Impact:</strong> ₹${Math.abs(total_savings).toFixed(2)} per order</li>
                    <li><strong>Recommendation:</strong> Apply predictions with confidence > 70%</li>
                </ul>
            </div>
            
            <div class="text-center">
                <button class="btn btn-success" onclick="apply_all_high_confidence_predictions()">
                    Apply All High Confidence Predictions
                </button>
            </div>
        </div>
    `;
    
    wrapper.html(html);
    
    // Store predictions globally for apply functions
    window.current_predictions = predictions;
    window.current_frm = frm;
    window.current_dialog = dialog;
}

window.apply_predicted_price = function(index, predicted_price, confidence) {
    let frm = window.current_frm;
    let row = frm.doc.items[index];
    
    if (row) {
        // Update the rate and custom fields
        frappe.model.set_value(row.doctype, row.name, 'rate', predicted_price);
        frappe.model.set_value(row.doctype, row.name, 'predicted_price', predicted_price);
        frappe.model.set_value(row.doctype, row.name, 'price_confidence', confidence);
        
        // Refresh the form
        frm.refresh_field('items');
        
        frappe.show_alert({
            message: __('Applied ML predicted price: ₹{0} (Confidence: {1}%)', [predicted_price.toFixed(2), confidence]),
            indicator: 'green'
        });
    }
};

window.apply_all_high_confidence_predictions = function() {
    let frm = window.current_frm;
    let predictions = window.current_predictions;
    let applied_count = 0;
    
    predictions.forEach((pred) => {
        let confidence = pred.prediction.confidence || 0;
        let predicted_price = pred.prediction.predicted_price || 0;
        
        if (confidence > 70 && predicted_price > 0) {
            let row = frm.doc.items[pred.index];
            if (row) {
                frappe.model.set_value(row.doctype, row.name, 'rate', predicted_price);
                frappe.model.set_value(row.doctype, row.name, 'predicted_price', predicted_price);
                frappe.model.set_value(row.doctype, row.name, 'price_confidence', confidence);
                applied_count++;
            }
        }
    });
    
    frm.refresh_field('items');
    
    if (applied_count > 0) {
        frappe.show_alert({
            message: __('Applied ML predictions to {0} items', [applied_count]),
            indicator: 'green'
        });
        
        if (window.current_dialog) {
            window.current_dialog.hide();
        }
    } else {
        frappe.msgprint(__('No high-confidence predictions available to apply'));
    }
};

function get_ml_price_prediction_for_item(frm, row, cdt, cdn) {
    if (!frm.doc.supplier || !row.item_code) return;
    
    frappe.call({
        method: 'ai_inventory.ml_supplier_analyzer.predict_purchase_price',
        args: {
            item_code: row.item_code,
            supplier: frm.doc.supplier,
            company: frm.doc.company,
            qty: row.qty || 1
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let predicted_price = r.message.predicted_price;
                let confidence = r.message.confidence;
                
                if (confidence > 60 && predicted_price > 0) {
                    // Update the custom fields
                    frappe.model.set_value(cdt, cdn, 'predicted_price', predicted_price);
                    frappe.model.set_value(cdt, cdn, 'price_confidence', confidence);
                    
                    // Show suggestion if significantly different from current rate
                    if (row.rate > 0) {
                        let difference_percent = Math.abs((predicted_price - row.rate) / row.rate) * 100;
                        
                        if (difference_percent > 10) {
                            frappe.show_alert({
                                message: __('ML suggests ₹{0} for {1} (Confidence: {2}%)', [
                                    predicted_price.toFixed(2), 
                                    row.item_code, 
                                    confidence
                                ]),
                                indicator: 'blue'
                            });
                        }
                    } else {
                        // Auto-apply if no rate is set and confidence is high
                        if (confidence > 80) {
                            frappe.model.set_value(cdt, cdn, 'rate', predicted_price);
                            frappe.show_alert({
                                message: __('Auto-applied ML price: ₹{0}', [predicted_price.toFixed(2)]),
                                indicator: 'green'
                            });
                        }
                    }
                }
            }
        }
    });
}

function create_po_from_forecasts(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('📊 Create PO from AI Forecasts'),
        size: 'large',
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'supplier',
                label: __('Supplier'),
                options: 'Supplier',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            disabled: 0,
                            company: frm.doc.company || ""
                        }
                    };
                }
            },
            {
                fieldtype: 'Link',
                fieldname: 'company',
                label: __('Company'),
                options: 'Company',
                default: frm.doc.company,
                reqd: 1
            },
            {
                fieldtype: 'MultiSelectPills',
                fieldname: 'movement_types',
                label: __('Movement Types'),
                options: [
                    { "label": "Fast Moving", "value": "Fast Moving" },
                    { "label": "Slow Moving", "value": "Slow Moving" },
                    { "label": "Critical", "value": "Critical" }
                ],
                default: ["Fast Moving", "Critical"]
            },
            {
                fieldtype: 'Check',
                fieldname: 'reorder_alerts_only',
                label: __('Reorder Alerts Only'),
                default: 1
            },
            {
                fieldtype: 'HTML',
                fieldname: 'forecasts_preview'
            }
        ],
        primary_action_label: __('Create Purchase Order'),
        primary_action: function(values) {
            create_po_from_forecast_data(frm, values, dialog);
        }
    });
    
    dialog.show();
    
    // Add event listeners for dynamic preview
    dialog.fields_dict.supplier.$input.on('change', function() {
        update_forecasts_preview(dialog);
    });
    
    dialog.fields_dict.company.$input.on('change', function() {
        update_forecasts_preview(dialog);
    });
}

function update_forecasts_preview(dialog) {
    let values = dialog.get_values();
    if (!values.supplier || !values.company) return;
    
    let preview_wrapper = dialog.fields_dict.forecasts_preview.$wrapper;
    preview_wrapper.html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading forecasts...</div>');
    
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.get_forecasts_for_supplier',
        args: {
            supplier: values.supplier,
            company: values.company,
            movement_types: values.movement_types || [],
            reorder_alerts_only: values.reorder_alerts_only || 0
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                display_forecasts_preview(preview_wrapper, r.message.forecasts);
            } else {
                preview_wrapper.html('<div class="alert alert-info">No matching forecasts found</div>');
            }
        }
    });
}

function display_forecasts_preview(wrapper, forecasts) {
    if (!forecasts || forecasts.length === 0) {
        wrapper.html('<div class="alert alert-info">No forecasts available for selected criteria</div>');
        return;
    }
    
    let total_value = forecasts.reduce((sum, f) => sum + (f.suggested_qty * (f.predicted_price || 100)), 0);
    
    let html = `
        <div style="margin-top: 15px;">
            <h5>📋 Forecast Preview (${forecasts.length} items)</h5>
            <div class="alert alert-primary">
                <strong>Estimated Order Value:</strong> ₹${total_value.toFixed(2)}
            </div>
            
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Current Stock</th>
                        <th>Suggested Qty</th>
                        <th>Movement Type</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    forecasts.slice(0, 10).forEach(forecast => {
        html += `
            <tr>
                <td><strong>${forecast.item_code}</strong></td>
                <td>${forecast.current_stock}</td>
                <td>${forecast.suggested_qty}</td>
                <td><span class="badge badge-${getMovementBadgeColor(forecast.movement_type)}">${forecast.movement_type}</span></td>
                <td>${forecast.confidence_score}%</td>
            </tr>
        `;
    });
    
    if (forecasts.length > 10) {
        html += `<tr><td colspan="5" class="text-center"><em>... and ${forecasts.length - 10} more items</em></td></tr>`;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    wrapper.html(html);
}

function getMovementBadgeColor(movement_type) {
    const colors = {
        'Fast Moving': 'success',
        'Slow Moving': 'warning',
        'Non Moving': 'danger',
        'Critical': 'dark'
    };
    return colors[movement_type] || 'secondary';
}

function create_po_from_forecast_data(frm, values, dialog) {
    frappe.call({
        method: 'ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast.get_forecasts_for_supplier',
        args: {
            supplier: values.supplier,
            company: values.company,
            movement_types: values.movement_types || [],
            reorder_alerts_only: values.reorder_alerts_only || 0
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success' && r.message.forecasts.length > 0) {
                // Clear existing items
                frm.clear_table('items');
                
                // Set supplier and company
                frm.set_value('supplier', values.supplier);
                frm.set_value('company', values.company);
                
                // Add items from forecasts
                r.message.forecasts.forEach(forecast => {
                    let row = frm.add_child('items');
                    row.item_code = forecast.item_code;
                    row.qty = forecast.suggested_qty;
                    row.warehouse = forecast.warehouse;
                    row.schedule_date = frappe.datetime.add_days(frappe.datetime.nowdate(), forecast.lead_time_days || 14);
                    
                    // Add ML predictions if available
                    if (forecast.predicted_price > 0) {
                        row.rate = forecast.predicted_price;
                        row.predicted_price = forecast.predicted_price;
                        row.price_confidence = forecast.confidence_score;
                    }
                });
                
                frm.refresh_field('items');
                dialog.hide();
                
                frappe.show_alert({
                    message: __('Purchase Order created from {0} AI forecasts', [r.message.forecasts.length]),
                    indicator: 'green'
                });
                
                // Auto-calculate totals
                frm.trigger('calculate_taxes_and_totals');
                
            } else {
                frappe.msgprint(__('No suitable forecasts found for the selected criteria'));
            }
        }
    });
}

// Custom method for AI Inventory Forecast to get forecasts for supplier
frappe.provide('ai_inventory.ai_inventory.doctype.ai_inventory_forecast.ai_inventory_forecast');

// This would be added to the AI Inventory Forecast Python file
/*
@frappe.whitelist()
def get_forecasts_for_supplier(supplier, company=None, movement_types=None, reorder_alerts_only=0):
    """Get forecasts for a specific supplier"""
    try:
        filters = {
            "preferred_supplier": supplier,
            "suggested_qty": [">", 0]
        }
        
        if company:
            filters["company"] = company
        
        if movement_types and isinstance(movement_types, list):
            filters["movement_type"] = ["in", movement_types]
        
        if cint(reorder_alerts_only):
            filters["reorder_alert"] = 1
        
        forecasts = frappe.get_all("AI Inventory Forecast",
            filters=filters,
            fields=[
                "name", "item_code", "warehouse", "current_stock", 
                "suggested_qty", "movement_type", "confidence_score",
                "lead_time_days", "predicted_consumption"
            ],
            order_by="movement_type = 'Critical' DESC, movement_type = 'Fast Moving' DESC, suggested_qty DESC"
        )
        
        # Get ML price predictions for each item
        for forecast in forecasts:
            try:
                from ai_inventory.ml_supplier_analyzer import MLSupplierAnalyzer
                analyzer = MLSupplierAnalyzer()
                price_result = analyzer.predict_item_price(
                    forecast.item_code, supplier, company, forecast.suggested_qty
                )
                
                if price_result.get('status') == 'success':
                    forecast['predicted_price'] = price_result.get('predicted_price', 0)
                    forecast['price_confidence'] = price_result.get('confidence', 0)
                else:
                    forecast['predicted_price'] = 0
                    forecast['price_confidence'] = 0
            except:
                forecast['predicted_price'] = 0
                forecast['price_confidence'] = 0
        
        return {
            "status": "success",
            "forecasts": forecasts
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
*/