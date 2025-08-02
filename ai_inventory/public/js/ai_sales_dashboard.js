
// ==========================================
// ai_inventory/public/js/ai_sales_dashboard.js
// Frontend JavaScript for dashboard interactions

frappe.ui.form.on('AI Sales Dashboard', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Train Models'), function() {
            frappe.call({
                method: 'ai_inventory.forecasting.core.train_models',
                callback: function(r) {
                    if (r.message.success) {
                        frappe.msgprint(__('Model training completed successfully'));
                        frm.reload_doc();
                    } else {
                        frappe.msgprint(__('Model training failed: ') + r.message.message);
                    }
                }
            });
        }, __('AI Actions'));
        
        frm.add_custom_button(__('Generate Forecasts'), function() {
            frappe.call({
                method: 'ai_inventory.forecasting.core.generate_forecasts',
                callback: function(r) {
                    if (r.message.success) {
                        frappe.msgprint(__('Forecast generation completed: ') + r.message.forecasts_created + __(' forecasts created'));
                        frm.reload_doc();
                    } else {
                        frappe.msgprint(__('Forecast generation failed: ') + r.message.message);
                    }
                }
            });
        }, __('AI Actions'));
        
        frm.add_custom_button(__('View Analytics'), function() {
            frappe.set_route('query-report', 'Sales Forecast Analytics');
        }, __('Reports'));
        
        // Load dashboard summary
        load_dashboard_summary(frm);
    }
});

function load_dashboard_summary(frm) {
    frappe.call({
        method: 'ai_inventory.api.dashboard.get_dashboard_summary',
        callback: function(r) {
            if (r.message.success) {
                update_dashboard_display(frm, r.message);
            }
        }
    });
}

function update_dashboard_display(frm, data) {
    // Create dashboard HTML
    const dashboard_html = `
        <div class="row">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-primary">${data.summary.total_forecasts}</h2>
                        <p>Total Forecasts (30 days)</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-success">${data.summary.high_confidence_forecasts}</h2>
                        <p>High Confidence (>80%)</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-info">${data.summary.enabled_items}</h2>
                        <p>Items with Forecasting</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="text-warning">${data.summary.average_accuracy}%</h2>
                        <p>Average Accuracy</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add to form
    if (!frm.dashboard_wrapper) {
        frm.dashboard_wrapper = $('<div class="form-dashboard-section">').appendTo(frm.layout.wrapper.find('.form-layout'));
    }
    
    frm.dashboard_wrapper.html(dashboard_html);
}