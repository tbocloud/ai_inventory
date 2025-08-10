// Copyright (c) 2025, sammish and contributors
// For license information, please see license.txt

frappe.ui.form.on("AI Forecast Accuracy", {
    refresh(frm) {
        // Add custom buttons
        add_accuracy_buttons(frm);
        
        // Set up field watchers
        setup_field_watchers(frm);
        
        // Show accuracy indicators
        show_accuracy_indicators(frm);
        
        // Add dashboard link
        add_dashboard_link(frm);
    },
    
    predicted_value(frm) {
        calculate_accuracy_metrics(frm);
    },
    
    actual_value(frm) {
        calculate_accuracy_metrics(frm);
    },
    
    forecast_type(frm) {
        setup_forecast_type_filters(frm);
    }
});

function add_accuracy_buttons(frm) {
    // Recalculate Accuracy Button
    frm.add_custom_button(__('Recalculate Accuracy'), function() {
        recalculate_accuracy(frm);
    }, __('AI Actions'));
    
    // Generate Report Button
    frm.add_custom_button(__('Generate Report'), function() {
        generate_accuracy_report(frm);
    }, __('Analytics'));
    
    // Compare Forecasts Button
    frm.add_custom_button(__('Compare Forecasts'), function() {
        compare_forecast_performance(frm);
    }, __('Analytics'));
    
    // View Historical Trends Button
    frm.add_custom_button(__('Historical Trends'), function() {
        view_historical_trends(frm);
    }, __('Analytics'));
    
    // Update Related Forecast Button
    if (frm.doc.forecast_reference) {
        frm.add_custom_button(__('Update Source Forecast'), function() {
            update_source_forecast(frm);
        }, __('AI Actions'));
    }
}

function setup_field_watchers(frm) {
    // Auto-calculate when values change
    frm.fields_dict.predicted_value.$input.on('change', function() {
        setTimeout(() => calculate_accuracy_metrics(frm), 100);
    });
    
    frm.fields_dict.actual_value.$input.on('change', function() {
        setTimeout(() => calculate_accuracy_metrics(frm), 100);
    });
    
    // Format currency fields
    if (frm.doc.predicted_value) {
        frm.set_df_property('predicted_value', 'description', 
            `Formatted: ${frappe.format(frm.doc.predicted_value, {fieldtype: 'Currency'})}`);
    }
    
    if (frm.doc.actual_value) {
        frm.set_df_property('actual_value', 'description', 
            `Formatted: ${frappe.format(frm.doc.actual_value, {fieldtype: 'Currency'})}`);
    }
}

function show_accuracy_indicators(frm) {
    if (!frm.doc.accuracy_percentage && frm.doc.accuracy_percentage !== 0) return;
    
    let accuracy = Number(frm.doc.accuracy_percentage || 0);
    let color = 'red';
    let message = 'Poor Performance';
    
    if (accuracy >= 90) {
        color = 'green';
        message = 'Excellent Performance';
    } else if (accuracy >= 80) {
        color = 'blue';
        message = 'Good Performance';
    } else if (accuracy >= 70) {
        color = 'orange';
        message = 'Fair Performance';
    } else if (accuracy >= 60) {
        color = 'yellow';
        message = 'Average Performance';
    }
    
    frm.dashboard.add_indicator(__('Accuracy: ') + accuracy.toFixed(1) + '%', color);
    frm.dashboard.add_indicator(__(message), color);
    
    // Add variance indicator
    if (typeof frm.doc.variance_percentage === 'number') {
        let variance_color = Math.abs(frm.doc.variance_percentage) <= 10 ? 'green' : 'red';
        frm.dashboard.add_indicator(__('Variance: ') + Number(frm.doc.variance_percentage).toFixed(1) + '%', variance_color);
    }
}

function add_dashboard_link(frm) {
    if (frm.doc.forecast_type) {
                const href = `/app/query-report/Forecast%20Accuracy%20Analysis?company=${encodeURIComponent(frm.doc.company || '')}&forecast_type=${encodeURIComponent(frm.doc.forecast_type || '')}`;
                const html = `
                        <div class="ai-accuracy-quick-links">
                            <a class="btn btn-sm btn-secondary" href="${href}" target="_blank">
                                ${__("View Forecast Accuracy Analysis")}
                            </a>
                        </div>
                `;
                frm.dashboard.add_section(html, __('Quick Links'));
    }
}

function calculate_accuracy_metrics(frm) {
    if (!frm.doc.predicted_value || !frm.doc.actual_value) {
        return;
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_forecast_accuracy.ai_forecast_accuracy.calculate_metrics",
        args: {
            predicted: frm.doc.predicted_value,
            actual: frm.doc.actual_value
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let metrics = r.message.metrics;
                
                // Update form fields
                if (typeof metrics.accuracy_percentage !== 'undefined') frm.set_value('accuracy_percentage', metrics.accuracy_percentage);
                if (typeof metrics.variance !== 'undefined') frm.set_value('variance', metrics.variance);
                if (typeof metrics.variance_percentage !== 'undefined') frm.set_value('variance_percentage', metrics.variance_percentage);
                if (typeof metrics.absolute_percentage_error !== 'undefined') frm.set_value('absolute_percentage_error', metrics.absolute_percentage_error);
                if (typeof metrics.accuracy_rating !== 'undefined') frm.set_value('accuracy_rating', metrics.accuracy_rating);
                
                // Show results
                frappe.show_alert({
                    message: __('Accuracy calculated: ') + metrics.accuracy_percentage.toFixed(1) + '%',
                    indicator: metrics.accuracy_percentage >= 80 ? 'green' : 'orange'
                });
                
                // Refresh indicators
                show_accuracy_indicators(frm);
            }
        }
    });
}

function recalculate_accuracy(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the document first'));
        return;
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_forecast_accuracy.ai_forecast_accuracy.recalculate_accuracy",
        args: {
            accuracy_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Accuracy recalculated successfully'),
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Error recalculating accuracy: ') + (r.message.message || 'Unknown error'));
            }
        }
    });
}

function generate_accuracy_report(frm) {
    if (!frm.doc.forecast_type || !frm.doc.company) {
        frappe.msgprint(__('Forecast Type and Company are required for report generation'));
        return;
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_forecast_accuracy.ai_forecast_accuracy.generate_accuracy_report",
        args: {
            forecast_type: frm.doc.forecast_type,
            company: frm.doc.company,
            from_date: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
            to_date: frappe.datetime.get_today()
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                show_accuracy_report_dialog(r.message.report);
            } else {
                frappe.msgprint(__('Error generating report: ') + (r.message.message || 'Unknown error'));
            }
        }
    });
}

function show_accuracy_report_dialog(report_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Accuracy Performance Report'),
        size: 'large',
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'report_html'
        }]
    });
    
    let html = `
        <div class="accuracy-report">
            <h4>📊 Forecast Accuracy Analysis</h4>
            
            <div class="row">
                <div class="col-md-6">
                    <h5>Overall Performance</h5>
                    <table class="table table-condensed">
                        <tr><td><strong>Total Forecasts:</strong></td><td>${report_data.total_forecasts}</td></tr>
                        <tr><td><strong>Average Accuracy:</strong></td><td><span class="text-success">${report_data.average_accuracy.toFixed(1)}%</span></td></tr>
                        <tr><td><strong>Best Performance:</strong></td><td>${report_data.best_accuracy.toFixed(1)}%</td></tr>
                        <tr><td><strong>Worst Performance:</strong></td><td>${report_data.worst_accuracy.toFixed(1)}%</td></tr>
                    </table>
                </div>
                
                <div class="col-md-6">
                    <h5>Performance Distribution</h5>
                    <table class="table table-condensed">
                        <tr><td><strong>Excellent (≥90%):</strong></td><td>${report_data.excellent_count}</td></tr>
                        <tr><td><strong>Good (80-89%):</strong></td><td>${report_data.good_count}</td></tr>
                        <tr><td><strong>Fair (70-79%):</strong></td><td>${report_data.fair_count}</td></tr>
                        <tr><td><strong>Poor (<70%):</strong></td><td>${report_data.poor_count}</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <h5>Recent Trends</h5>
                    <p>${report_data.trend_analysis}</p>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.report_html.$wrapper.html(html);
    dialog.show();
}

function compare_forecast_performance(frm) {
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_forecast_accuracy.ai_forecast_accuracy.compare_forecasts",
        args: {
            company: frm.doc.company,
            current_forecast: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                show_comparison_dialog(r.message.comparison);
            } else {
                frappe.msgprint(__('Error comparing forecasts: ') + (r.message.message || 'Unknown error'));
            }
        }
    });
}

function show_comparison_dialog(comparison_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Forecast Performance Comparison'),
        size: 'large',
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'comparison_html'
        }]
    });
    
    let html = `
        <div class="forecast-comparison">
            <h4>🔍 Performance Comparison</h4>
            
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Forecast Type</th>
                        <th>Average Accuracy</th>
                        <th>Best Performance</th>
                        <th>Consistency Score</th>
                        <th>Trend</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    comparison_data.forEach(function(item) {
        html += `
            <tr>
                <td>${item.forecast_type}</td>
                <td><span class="text-${item.avg_accuracy >= 80 ? 'success' : 'warning'}">${item.avg_accuracy.toFixed(1)}%</span></td>
                <td>${item.best_accuracy.toFixed(1)}%</td>
                <td>${item.consistency_score.toFixed(1)}</td>
                <td><span class="text-${item.trend === 'improving' ? 'success' : item.trend === 'declining' ? 'danger' : 'info'}">${item.trend}</span></td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    dialog.fields_dict.comparison_html.$wrapper.html(html);
    dialog.show();
}

function view_historical_trends(frm) {
    if (!frm.doc.forecast_type) {
        frappe.msgprint(__('Forecast Type is required'));
        return;
    }
    
    frappe.route_options = {
        "forecast_type": frm.doc.forecast_type,
        "company": frm.doc.company,
        "from_date": frappe.datetime.add_days(frappe.datetime.get_today(), -90),
        "to_date": frappe.datetime.get_today()
    };
    
    frappe.set_route("query-report", "Forecast Accuracy Analysis");
}

function update_source_forecast(frm) {
    if (!frm.doc.forecast_reference) {
        frappe.msgprint(__('No source forecast reference found'));
        return;
    }
    
    frappe.call({
        method: "ai_inventory.ai_inventory.doctype.ai_forecast_accuracy.ai_forecast_accuracy.update_source_forecast",
        args: {
            accuracy_name: frm.doc.name,
            forecast_reference: frm.doc.forecast_reference
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Source forecast updated with accuracy data'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('Error updating source forecast: ') + (r.message.message || 'Unknown error'));
            }
        }
    });
}

function setup_forecast_type_filters(frm) {
    // Set up filters based on forecast type
    if (frm.doc.forecast_type) {
        frm.set_query('forecast_reference', function() {
            let doctype_map = {
                'Cash Flow': 'AI Cashflow Forecast',
                'Revenue': 'AI Revenue Forecast',
                'Expense': 'AI Expense Forecast',
                'Financial': 'AI Financial Forecast'
            };
            
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
    }
}
