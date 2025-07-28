// COMPLETELY REPLACE the run_ml_supplier_analysis function in ai_settings.js

function run_ml_supplier_analysis(frm) {
    // First check which companies have purchase data
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Company',
            fields: ['name']
        },
        callback: function(companies_result) {
            if (!companies_result.message || companies_result.message.length === 0) {
                frappe.msgprint(__('No companies found. Please create a company first.'));
                return;
            }
            
            // Check purchase data for each company
            frappe.call({
                method: 'ai_inventory.ml_supplier_analyzer.get_companies_with_purchase_data',
                callback: function(r) {
                    let companies_with_data = [];
                    let all_companies = companies_result.message;
                    
                    if (r.message && r.message.length > 0) {
                        companies_with_data = r.message.filter(comp => comp.purchase_orders > 0);
                    }
                    
                    // Show company selection dialog
                    show_ml_company_selection_dialog(all_companies, companies_with_data);
                },
                error: function() {
                    // Fallback: show all companies
                    show_ml_company_selection_dialog(companies_result.message, []);
                }
            });
        }
    });
}

function show_ml_company_selection_dialog(all_companies, companies_with_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Select Company for ML Supplier Analysis'),
        size: 'large',
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'company',
                label: __('Company'),
                options: 'Company',
                reqd: 1
            },
            {
                fieldtype: 'HTML',
                fieldname: 'company_info',
                options: generate_company_info_html(companies_with_data, all_companies)
            }
        ],
        primary_action_label: __('Run ML Analysis'),
        primary_action: function(values) {
            if (!values.company) {
                frappe.msgprint(__('Please select a company'));
                return;
            }
            
            dialog.hide();
            
            // Check if selected company has data
            let selected_company_data = companies_with_data.find(c => c.company === values.company);
            
            if (!selected_company_data || selected_company_data.purchase_orders === 0) {
                frappe.confirm(
                    __('Company "{0}" has no purchase order data. ML analysis may not be meaningful. Do you want to continue anyway?', [values.company]),
                    function() {
                        run_ml_analysis_for_company(values.company);
                    },
                    function() {
                        // Show data creation guidance
                        show_data_creation_guidance(values.company);
                    }
                );
            } else {
                run_ml_analysis_for_company(values.company);
            }
        },
        secondary_action_label: __('Create Sample Data'),
        secondary_action: function(values) {
            if (!values.company) {
                frappe.msgprint(__('Please select a company first'));
                return;
            }
            create_sample_purchase_data(values.company);
            dialog.hide();
        }
    });
    
    dialog.show();
}

function generate_company_info_html(companies_with_data, all_companies) {
    let html = '<div class="company-analysis-info">';
    
    if (companies_with_data.length > 0) {
        html += `
            <div class="alert alert-success">
                <h6><i class="fa fa-check-circle"></i> Companies with Purchase Data (Recommended):</h6>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Purchase Orders</th>
                            <th>Suppliers</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        companies_with_data.forEach(comp => {
            let status = comp.purchase_orders >= 10 ? '✅ Excellent' : 
                        comp.purchase_orders >= 5 ? '✅ Good' : 
                        comp.purchase_orders >= 1 ? '⚠️ Limited' : '❌ No Data';
            
            html += `
                <tr>
                    <td><strong>${comp.company}</strong></td>
                    <td>${comp.purchase_orders}</td>
                    <td>${comp.suppliers}</td>
                    <td>${status}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Show companies without data
    let companies_without_data = all_companies.filter(comp => 
        !companies_with_data.find(c => c.company === comp.name)
    );
    
    if (companies_without_data.length > 0) {
        html += `
            <div class="alert alert-warning">
                <h6><i class="fa fa-exclamation-triangle"></i> Companies without Purchase Data:</h6>
                <ul>
        `;
        
        companies_without_data.forEach(comp => {
            html += `<li><strong>${comp.name}</strong> - No purchase orders found</li>`;
        });
        
        html += `
                </ul>
                <small><strong>Note:</strong> ML analysis needs purchase order data to analyze supplier performance.</small>
            </div>
        `;
    }
    
    html += `
        <div class="alert alert-info">
            <h6><i class="fa fa-info-circle"></i> ML Analysis Requirements:</h6>
            <ul>
                <li>At least 5-10 purchase orders for meaningful analysis</li>
                <li>Multiple suppliers for comparison</li>
                <li>Recent purchase activity (within last 12 months)</li>
            </ul>
        </div>
    `;
    
    html += '</div>';
    return html;
}

function run_ml_analysis_for_company(company) {
    frappe.show_alert({
        message: __('Starting ML supplier analysis for {0}...', [company]),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'ai_inventory.ml_supplier_analyzer.run_ml_supplier_analysis',
        args: {
            company: company
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('ML Analysis Complete for {0}', [company]),
                        message: `
                            <div class="alert alert-success">
                                <h4><i class="fa fa-check-circle"></i> ${r.message.message}</h4>
                                <table class="table table-sm">
                                    <tr><td><strong>Company:</strong></td><td>${r.message.company}</td></tr>
                                    <tr><td><strong>Suppliers Analyzed:</strong></td><td>${r.message.suppliers_analyzed || 0}</td></tr>
                                    <tr><td><strong>Suppliers Updated:</strong></td><td>${r.message.suppliers_updated || 0}</td></tr>
                                </table>
                            </div>
                        `,
                        wide: true
                    });
                    
                    // Show top suppliers if available
                    if (r.message.top_suppliers && r.message.top_suppliers.length > 0) {
                        let top_suppliers_html = `
                            <h5>🏆 Top Performing Suppliers for ${company}:</h5>
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Supplier</th>
                                        <th>Score</th>
                                        <th>Recommendation</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        r.message.top_suppliers.forEach(supplier => {
                            let scoreColor = supplier.score >= 80 ? 'success' : 
                                           supplier.score >= 60 ? 'warning' : 'danger';
                            
                            top_suppliers_html += `
                                <tr>
                                    <td><strong>${supplier.supplier}</strong></td>
                                    <td><span class="label label-${scoreColor}">${supplier.score}%</span></td>
                                    <td>${supplier.recommendation}</td>
                                </tr>
                            `;
                        });
                        
                        top_suppliers_html += '</tbody></table>';
                        
                        frappe.msgprint({
                            title: __('Top Suppliers Analysis'),
                            message: top_suppliers_html,
                            wide: true
                        });
                    }
                    
                    frappe.show_alert({
                        message: __('ML analysis completed successfully for {0}!', [company]),
                        indicator: 'green'
                    });
                    
                } else if (r.message.status === 'info') {
                    show_no_data_guidance(company, r.message.message);
                } else {
                    frappe.msgprint({
                        title: __('ML Analysis Error'),
                        message: r.message.message,
                        indicator: 'red'
                    });
                }
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('ML Analysis Error'),
                message: 'Failed to run ML supplier analysis. Please check the error logs.',
                indicator: 'red'
            });
        }
    });
}

function show_no_data_guidance(company, message) {
    frappe.msgprint({
        title: __('No Purchase Data Found'),
        message: `
            <div class="alert alert-warning">
                <h4><i class="fa fa-info-circle"></i> ${message}</h4>
                <h5>🛠️ How to Generate Supplier Analytics for ${company}:</h5>
                <ol>
                    <li><strong>Create Suppliers:</strong>
                        <br><small>Go to Buying → Supplier → New Supplier</small>
                    </li>
                    <li><strong>Create Items:</strong>
                        <br><small>Go to Stock → Item → New Item (make sure "Is Stock Item" is checked)</small>
                    </li>
                    <li><strong>Create Purchase Orders:</strong>
                        <br><small>Go to Buying → Purchase Order → New Purchase Order</small>
                        <br><small>- Select Company: ${company}</small>
                        <br><small>- Add suppliers and items</small>
                        <br><small>- Submit the Purchase Orders</small>
                    </li>
                    <li><strong>Create Purchase Receipts (Optional):</strong>
                        <br><small>Go to Stock → Purchase Receipt → New Purchase Receipt</small>
                    </li>
                    <li><strong>Run ML Analysis Again</strong></li>
                </ol>
                <div class="alert alert-info">
                    <strong>💡 Tip:</strong> Create at least 5-10 purchase orders with different suppliers for meaningful ML analysis results.
                </div>
            </div>
        `,
        wide: true,
        indicator: 'orange'
    });
}

function show_data_creation_guidance(company) {
    frappe.msgprint({
        title: __('Create Purchase Data for {0}', [company]),
        message: `
            <div class="alert alert-info">
                <h4>🚀 Quick Start Guide:</h4>
                <p>To enable ML supplier analysis, you need purchase transaction data.</p>
                
                <h5>Option 1: Manual Setup</h5>
                <ol>
                    <li>Create suppliers and items</li>
                    <li>Create and submit purchase orders</li>
                    <li>Run ML analysis again</li>
                </ol>
                
                <h5>Option 2: Sample Data</h5>
                <p>Click "Create Sample Data" to generate test purchase orders automatically.</p>
                
                <div class="text-center" style="margin-top: 15px;">
                    <button class="btn btn-primary" onclick="create_sample_purchase_data('${company}')">
                        📦 Create Sample Data for ${company}
                    </button>
                </div>
            </div>
        `,
        wide: true
    });
}

function create_sample_purchase_data(company) {
    frappe.confirm(
        __('This will create sample suppliers, items, and purchase orders for {0}. Continue?', [company]),
        function() {
            frappe.show_alert({
                message: __('Creating sample purchase data for {0}...', [company]),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'ai_inventory.ml_supplier_analyzer.create_sample_purchase_data',
                args: { company: company },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint({
                            title: __('Sample Data Created'),
                            message: r.message.message,
                            indicator: 'green'
                        });
                        
                        // Auto-run ML analysis after sample data creation
                        setTimeout(() => {
                            run_ml_analysis_for_company(company);
                        }, 2000);
                    } else {
                        frappe.msgprint({
                            title: __('Sample Data Creation Failed'),
                            message: r.message?.message || 'Failed to create sample data',
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}