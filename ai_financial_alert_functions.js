// ============================================================================
// AI Financial Alert Management Functions
// Enhanced functionality for AI Financial Alert system
// ============================================================================

// Test function to create sample alerts for demonstration
function create_sample_financial_alert() {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.create_financial_alert",
        args: {
            alert_data: {
                company: "TBO Cloud",
                title: "Sample Low Balance Alert",
                message: "Cash flow forecast indicates potential low balance in next 7 days",
                priority: "High",
                alert_type: "Cash Flow Warning",
                threshold_value: 10000,
                actual_value: 8500,
                forecast_type: "Cash Flow",
                confidence_level: 85,
                recommended_action: "Review upcoming expenses and consider increasing cash reserves"
            }
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: `Sample alert created: ${r.message.alert_id}`,
                    indicator: 'green'
                });
                frappe.set_route("Form", "AI Financial Alert", r.message.alert_id);
            } else {
                frappe.show_alert({
                    message: "Failed to create sample alert: " + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

// Function to resolve an alert
function resolve_financial_alert(alert_id, action_taken, action_result) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.resolve_alert",
        args: {
            alert_id: alert_id,
            action_taken: action_taken,
            action_result: action_result
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: "Alert resolved successfully",
                    indicator: 'green'
                });
                location.reload();
            } else {
                frappe.show_alert({
                    message: "Failed to resolve alert: " + (r.message ? r.message.error : "Unknown error"),
                    indicator: 'red'
                });
            }
        }
    });
}

// Function to get alert statistics
function get_alert_statistics() {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_alert.ai_financial_alert.get_active_alerts",
        callback: function(r) {
            if (r.message && r.message.success) {
                let alerts = r.message.alerts;
                let stats = {
                    total: alerts.length,
                    critical: alerts.filter(a => a.priority === 'Critical').length,
                    high: alerts.filter(a => a.priority === 'High').length,
                    medium: alerts.filter(a => a.priority === 'Medium').length,
                    low: alerts.filter(a => a.priority === 'Low').length
                };
                
                console.log("Alert Statistics:", stats);
                return stats;
            }
        }
    });
}

// Function to create alert from forecast check
function create_alert_from_forecast_check(forecast_name) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_financial_forecast.ai_financial_forecast.check_balance_alerts",
        args: {
            forecast_name: forecast_name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                if (r.message.alert_records_created && r.message.alert_records_created.length > 0) {
                    frappe.show_alert({
                        message: `${r.message.alert_records_created.length} alert(s) created from forecast check`,
                        indicator: 'orange'
                    });
                } else {
                    frappe.show_alert({
                        message: "No alerts needed - forecast looks good",
                        indicator: 'green'
                    });
                }
            }
        }
    });
}

// Add alert management to form toolbar
frappe.ui.form.on('AI Financial Alert', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open' || frm.doc.status === 'Investigating') {
            frm.add_custom_button(__('Mark as Resolved'), function() {
                frappe.prompt([
                    {
                        fieldtype: 'Small Text',
                        fieldname: 'action_taken',
                        label: 'Action Taken',
                        reqd: 1
                    },
                    {
                        fieldtype: 'Small Text',
                        fieldname: 'action_result',
                        label: 'Result/Outcome'
                    }
                ], function(values) {
                    resolve_financial_alert(frm.doc.name, values.action_taken, values.action_result);
                }, __('Resolve Alert'));
            });
        }
        
        if (frm.doc.related_forecast) {
            frm.add_custom_button(__('View Related Forecast'), function() {
                frappe.set_route("Form", "AI Financial Forecast", frm.doc.related_forecast);
            });
        }
        
        frm.add_custom_button(__('Create Sample Alert'), function() {
            create_sample_financial_alert();
        });
    }
});

// Realtime notifications for new alerts
frappe.realtime.on('new_financial_alert', function(data) {
    if (data.priority === 'Critical' || data.priority === 'High') {
        frappe.show_alert({
            message: `🚨 New ${data.priority} Alert: ${data.title}`,
            indicator: data.priority === 'Critical' ? 'red' : 'orange'
        });
        
        // Show desktop notification if supported
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`AI Financial Alert - ${data.priority}`, {
                body: data.message,
                icon: '/assets/ai_inventory/images/alert-icon.png'
            });
        }
    }
});

// Request notification permission on page load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}
