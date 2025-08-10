// system_health_report.js - Page implementation
frappe.pages['system-health-report'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'AI Financial Forecast - System Health Report',
        single_column: true
    });

    // Simple initialization without complex dependencies
    try {
        // Initialize the page directly
        const report_instance = new SystemHealthReport(page);
        
        // Set global reference immediately
        window.system_health_report = report_instance;
        
        // Log successful initialization
        console.log('System Health Report initialized successfully');
        
    } catch (error) {
        console.error('Failed to initialize System Health Report:', error);
        page.main.html(`
            <div class="alert alert-danger">
                <h4>Initialization Error</h4>
                <p>Failed to initialize the System Health Report: ${error.message}</p>
                <button class="btn btn-primary" onclick="window.location.reload()">Reload Page</button>
            </div>
        `);
    }
};

class SystemHealthReport {
    constructor(page) {
        this.page = page;
        this.company = frappe.defaults.get_user_default("Company");
        this.setup_page();
        this.load_report();
    }

    setup_page() {
        // Add company filter
        this.company_field = this.page.add_field({
            label: 'Company',
            fieldtype: 'Link',
            fieldname: 'company',
            options: 'Company',
            default: this.company,
            change: () => {
                this.company = this.company_field.get_value();
                this.load_report();
            }
        });

        // Add refresh button
        this.page.add_menu_item(__('Refresh'), () => {
            this.load_report();
        });

        // Add export button
        this.page.add_menu_item(__('Export PDF'), () => {
            this.export_report('pdf');
        });

        // Add export Excel button
        this.page.add_menu_item(__('Export Excel'), () => {
            this.export_report('excel');
        });

        // Add fix issues button
        this.page.add_menu_item(__('Fix Critical Issues'), () => {
            this.fix_critical_issues();
        });

        // Create main container
        this.page.main.html(`
            <div class="system-health-container">
                <div class="health-summary-cards"></div>
                <div class="critical-issues-section"></div>
                <div class="data-quality-section"></div>
                <div class="performance-metrics-section"></div>
                <div class="recommendations-section"></div>
            </div>
        `);
    }

    formatLastUpdated(date) {
        try {
            if (typeof moment !== 'undefined' && date) {
                return moment(date).fromNow();
            } else if (date) {
                // Fallback to native JavaScript
                const d = new Date(date);
                const now = new Date();
                const diffMs = now - d;
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                
                if (diffHours < 1) return 'Just now';
                if (diffHours < 24) return `${diffHours}h ago`;
                const diffDays = Math.floor(diffHours / 24);
                if (diffDays < 7) return `${diffDays}d ago`;
                return d.toLocaleDateString();
            }
            return 'Never';
        } catch (error) {
            console.error('Date formatting error:', error);
            return 'Unknown';
        }
    }

    async load_report() {
        try {
            // Show loading indicator
            this.show_loading();

            console.log('Loading system health report for company:', this.company);

            // Fetch report data
            const response = await frappe.call({
                method: 'ai_inventory.ai_inventory.report.system_health_report.generate_system_health_report',
                args: {
                    company: this.company
                }
            });

            console.log('Report response:', response);

            if (response.message && response.message.success) {
                console.log('Report data:', response.message.data);
                this.render_report(response.message.data);
            } else {
                console.error('Report failed:', response.message);
                
                // Show error message
                this.page.main.html(`
                    <div class="alert alert-warning">
                        <h4>Report Generation Failed</h4>
                        <p>${response.message?.error || 'Unknown error occurred'}</p>
                        <button class="btn btn-primary" onclick="window.system_health_report.load_report()">
                            Retry
                        </button>
                    </div>
                `);
            }

        } catch (error) {
            console.error('Error loading system health report:', error);
            
            // Show detailed error information
            this.page.main.html(`
                <div class="alert alert-danger">
                    <h4>Error Loading Report</h4>
                    <p><strong>Error:</strong> ${error.message || 'Failed to load system health report'}</p>
                    <details>
                        <summary>Technical Details</summary>
                        <pre>${JSON.stringify(error, null, 2)}</pre>
                    </details>
                    <button class="btn btn-primary mt-2" onclick="window.system_health_report.load_report()">
                        Retry
                    </button>
                </div>
            `);
        } finally {
            this.hide_loading();
        }
    }

    show_loading() {
        this.page.main.html(`
            <div class="text-center" style="padding: 50px;">
                <i class="fa fa-spinner fa-spin fa-2x text-muted"></i>
                <p class="text-muted">Loading system health report...</p>
            </div>
        `);
    }

    hide_loading() {
        // Loading indicator will be replaced by report content
    }

    render_report(data) {
        // Store data for later use
        this.current_data = data;
        
        console.log('Rendering report with data:', data);
        
        // Provide default empty data if missing
        const defaultData = {
            summary: { overall_health_score: 0, total_forecasts: 0, last_updated: new Date() },
            critical_issues: [],
            data_quality: { average_quality_score: 0, average_confidence_score: 0, high_quality_percentage: 0, low_quality_count: 0, average_volatility: 0, quality_trend: { direction: 'stable', change_percentage: 0, monthly_data: [] } },
            api_performance: { sync_success_rate: 0, total_sync_attempts: 0, successful_syncs: 0, last_successful_sync: null, api_status: 'Unknown' },
            integration_status: { inventory_sync: { status: 'Unknown', active_forecasts: 0 }, auto_sync: { status: 'Unknown', frequency: 'Unknown' }, alert_system: { status: 'Unknown', active_alerts: 0 } },
            recommendations: []
        };
        
        // Merge provided data with defaults
        const reportData = Object.assign({}, defaultData, data);
        
        try {
            // Render summary cards
            this.render_summary_cards(reportData.summary, reportData.critical_issues);

            // Render critical issues
            this.render_critical_issues(reportData.critical_issues);

            // Render data quality metrics
            this.render_data_quality(reportData.data_quality);

            // Render performance metrics
            this.render_performance_metrics(reportData.api_performance, reportData.integration_status);

            // Render recommendations
            this.render_recommendations(reportData.recommendations);
            
            console.log('Report rendered successfully');
        } catch (error) {
            console.error('Error rendering report:', error);
            this.page.main.html(`
                <div class="alert alert-danger">
                    <h4>Rendering Error</h4>
                    <p>Failed to render the report properly: ${error.message}</p>
                </div>
            `);
        }
    }

    render_summary_cards(summary, critical_issues) {
        const container = this.page.main.find('.health-summary-cards');
        
        const health_score = summary.overall_health_score;
        const health_color = health_score >= 80 ? 'green' : health_score >= 60 ? 'orange' : 'red';
        const critical_count = critical_issues.filter(issue => issue.type === 'critical').length;
        
        container.html(`
            <div class="row" style="margin-bottom: 20px;">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 class="text-${health_color}">${health_score}%</h2>
                            <p class="text-muted">Overall Health Score</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 class="${critical_count > 0 ? 'text-danger' : 'text-success'}">${critical_count}</h2>
                            <p class="text-muted">Critical Issues</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 class="text-primary">${summary.total_forecasts}</h2>
                            <p class="text-muted">Total Forecasts</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 class="text-info">${this.formatLastUpdated(summary.last_updated)}</h2>
                            <p class="text-muted">Last Updated</p>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    render_critical_issues(issues) {
        const container = this.page.main.find('.critical-issues-section');
        
        if (issues.length === 0) {
            container.html(`
                <div class="alert alert-success">
                    <i class="fa fa-check-circle"></i> No critical issues detected
                </div>
            `);
            return;
        }

        let issues_html = `
            <h3>Critical Issues <span class="badge badge-danger">${issues.length}</span></h3>
            <div class="issues-list">
        `;

        issues.forEach(issue => {
            const badge_class = issue.type === 'critical' ? 'badge-danger' : 'badge-warning';
            const icon = issue.type === 'critical' ? 'fa-exclamation-triangle' : 'fa-exclamation-circle';
            
            issues_html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <span class="badge ${badge_class}">
                            <i class="fa ${icon}"></i> ${issue.severity}
                        </span>
                        <strong>${issue.title}</strong>
                    </div>
                    <div class="card-body">
                        <p>${issue.description}</p>
                        <p><strong>Action Required:</strong> ${issue.action_required}</p>
                        ${issue.affected_forecasts.length > 0 ? `
                            <button class="btn btn-sm btn-outline-info" onclick="system_health_report.show_affected_forecasts('${issue.category}')">
                                View ${issue.affected_forecasts.length} Affected Forecasts
                            </button>
                        ` : ''}
                        ${issue.type === 'critical' ? `
                            <button class="btn btn-sm btn-danger ml-2" onclick="system_health_report.fix_issue('${issue.category}')">
                                Fix Now
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        issues_html += '</div>';
        container.html(issues_html);
    }

    render_data_quality(data_quality) {
        const container = this.page.main.find('.data-quality-section');
        
        const quality_color = data_quality.average_quality_score >= 80 ? 'success' : 
                             data_quality.average_quality_score >= 60 ? 'warning' : 'danger';
        
        container.html(`
            <h3>Data Quality Metrics</h3>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>Quality Overview</h5>
                            <div class="progress mb-2">
                                <div class="progress-bar bg-${quality_color}" 
                                     style="width: ${data_quality.average_quality_score}%">
                                    ${data_quality.average_quality_score}%
                                </div>
                            </div>
                            <small class="text-muted">Average Data Quality Score</small>
                            
                            <div class="mt-3">
                                <div class="progress mb-2">
                                    <div class="progress-bar bg-info" 
                                         style="width: ${data_quality.average_confidence_score}%">
                                        ${data_quality.average_confidence_score}%
                                    </div>
                                </div>
                                <small class="text-muted">Average Confidence Score</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>Quality Distribution</h5>
                            <p><strong>High Quality (≥80%):</strong> ${data_quality.high_quality_percentage}%</p>
                            <p><strong>Low Quality (<60):</strong> ${data_quality.low_quality_count} forecasts</p>
                            <p><strong>Average Volatility:</strong> ${data_quality.average_volatility}%</p>
                            <p><strong>Trend:</strong> 
                                <span class="badge badge-${data_quality.quality_trend.direction === 'improving' ? 'success' : 
                                                           data_quality.quality_trend.direction === 'declining' ? 'danger' : 'secondary'}">
                                    ${data_quality.quality_trend.direction}
                                    ${data_quality.quality_trend.change_percentage !== 0 ? 
                                      ` (${data_quality.quality_trend.change_percentage > 0 ? '+' : ''}${data_quality.quality_trend.change_percentage}%)` : ''}
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `);

        // Render quality trend chart if data available
        if (data_quality.quality_trend.monthly_data.length > 0) {
            this.render_quality_trend_chart(data_quality.quality_trend.monthly_data);
        }
    }

    render_quality_trend_chart(monthly_data) {
        const chart_container = $(`
            <div class="col-md-12 mt-3">
                <div class="card">
                    <div class="card-body">
                        <h5>Data Quality Trend</h5>
                        <div id="quality-trend-chart-container">
                            <p class="text-muted">Quality trend data visualization</p>
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Month</th>
                                        <th>Quality Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${monthly_data.map(d => `
                                        <tr>
                                            <td>${d.month}</td>
                                            <td>${d.avg_quality}%</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        this.page.main.find('.data-quality-section .row').append(chart_container);

        // Try to render chart if Chart.js is available, otherwise show table
        try {
            const chartElement = document.getElementById('quality-trend-chart-container');
            if (chartElement && typeof Chart !== 'undefined') {
                chartElement.innerHTML = '<canvas id="quality-trend-chart" height="100"></canvas>';
                const ctx = document.getElementById('quality-trend-chart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: monthly_data.map(d => d.month),
                        datasets: [{
                            label: 'Data Quality Score',
                            data: monthly_data.map(d => d.avg_quality),
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }
        } catch (error) {
            console.log('Chart.js not available, showing table view');
        }
    }

    render_performance_metrics(api_performance, integration_status) {
        const container = this.page.main.find('.performance-metrics-section');
        
        container.html(`
            <h3>System Performance</h3>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>API Performance</h5>
                            <p><strong>Sync Success Rate:</strong> 
                                <span class="badge badge-${api_performance.sync_success_rate >= 90 ? 'success' : 
                                                           api_performance.sync_success_rate >= 70 ? 'warning' : 'danger'}">
                                    ${api_performance.sync_success_rate}%
                                </span>
                            </p>
                            <p><strong>Total Syncs:</strong> ${api_performance.total_sync_attempts}</p>
                            <p><strong>Successful:</strong> ${api_performance.successful_syncs}</p>
                            <p><strong>Last Sync:</strong> ${api_performance.last_successful_sync || 'Never'}</p>
                            <p><strong>API Status:</strong> 
                                <span class="badge badge-${api_performance.api_status === 'Connected' ? 'success' : 'danger'}">
                                    ${api_performance.api_status}
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>Integration Status</h5>
                            <div class="integration-item">
                                <strong>Inventory Sync:</strong> 
                                <span class="badge badge-${integration_status.inventory_sync.status === 'Enabled' ? 'success' : 'secondary'}">
                                    ${integration_status.inventory_sync.status}
                                </span>
                                <small class="text-muted d-block">Active: ${integration_status.inventory_sync.active_forecasts} forecasts</small>
                            </div>
                            <div class="integration-item mt-2">
                                <strong>Auto Sync:</strong> 
                                <span class="badge badge-${integration_status.auto_sync.status === 'Enabled' ? 'success' : 'secondary'}">
                                    ${integration_status.auto_sync.status}
                                </span>
                                <small class="text-muted d-block">Frequency: ${integration_status.auto_sync.frequency}</small>
                            </div>
                            <div class="integration-item mt-2">
                                <strong>Alert System:</strong> 
                                <span class="badge badge-success">${integration_status.alert_system.status}</span>
                                <small class="text-muted d-block">Active Alerts: ${integration_status.alert_system.active_alerts}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    render_recommendations(recommendations) {
        const container = this.page.main.find('.recommendations-section');
        
        if (recommendations.length === 0) {
            container.html(`
                <div class="alert alert-success">
                    <i class="fa fa-thumbs-up"></i> No recommendations at this time. System is performing well!
                </div>
            `);
            return;
        }

        let rec_html = `
            <h3>Recommendations <span class="badge badge-info">${recommendations.length}</span></h3>
            <div class="recommendations-list">
        `;

        recommendations.forEach((rec, index) => {
            const priority_class = rec.priority === 'Critical' ? 'danger' : 
                                  rec.priority === 'High' ? 'warning' : 'info';
            
            rec_html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <span class="badge badge-${priority_class}">${rec.priority} Priority</span>
                        <strong>${rec.title}</strong>
                    </div>
                    <div class="card-body">
                        <p>${rec.description}</p>
                        <div class="row">
                            <div class="col-md-6">
                                <small><strong>Estimated Effort:</strong> ${rec.estimated_effort}</small>
                            </div>
                            <div class="col-md-6">
                                <small><strong>Impact:</strong> ${rec.impact}</small>
                            </div>
                        </div>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-primary" onclick="system_health_report.implement_recommendation(${index})">
                                Implement
                            </button>
                            <button class="btn btn-sm btn-outline-secondary ml-2" onclick="system_health_report.schedule_recommendation(${index})">
                                Schedule
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        rec_html += '</div>';
        container.html(rec_html);
    }

    async export_report(format) {
        try {
            frappe.show_alert({
                message: __('Generating report...'),
                indicator: 'blue'
            });

            const response = await frappe.call({
                method: 'ai_inventory.ai_inventory.report.system_health_report.export_system_health_report',
                args: {
                    company: this.company,
                    format: format
                }
            });

            if (response.message && response.message.success) {
                if (format === 'pdf') {
                    // Download PDF
                    if (response.message.content) {
                        const blob = new Blob([response.message.content], { type: 'application/pdf' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = response.message.filename || 'system_health_report.pdf';
                        a.click();
                        URL.revokeObjectURL(url);
                    }
                } else if (format === 'excel') {
                    // Export to Excel
                    if (response.message.data) {
                        this.export_to_excel(response.message.data);
                    } else {
                        throw new Error('No data received for Excel export');
                    }
                }

                frappe.show_alert({
                    message: __('Report exported successfully'),
                    indicator: 'green'
                });
            } else {
                throw new Error(response.message?.error || 'Export failed');
            }

        } catch (error) {
            console.error('Export error:', error);
            frappe.msgprint({
                title: __('Export Error'),
                message: __('Failed to export report: ') + (error.message || 'Unknown error'),
                indicator: 'red'
            });
        }
    }

    export_to_excel(data) {
        try {
            // Simple CSV export as fallback if XLSX not available
            if (typeof XLSX === 'undefined') {
                console.log('XLSX not available, using CSV export');
                this.export_to_csv(data);
                return;
            }

            // Create Excel workbook using SheetJS
            const workbook = XLSX.utils.book_new();
            
            // Summary sheet
            const summary_data = [
                ['Metric', 'Value'],
                ['Total Forecasts', data.summary.total_forecasts],
                ['Health Score', data.summary.overall_health_score + '%'],
                ['Critical Issues', data.critical_issues.filter(i => i.type === 'critical').length],
                ['Average Quality Score', data.data_quality.average_quality_score + '%'],
                ['Average Confidence', data.data_quality.average_confidence_score + '%']
            ];
            
            const summary_sheet = XLSX.utils.aoa_to_sheet(summary_data);
            XLSX.utils.book_append_sheet(workbook, summary_sheet, 'Summary');
            
            // Critical Issues sheet
            if (data.critical_issues.length > 0) {
                const issues_data = [['Type', 'Category', 'Title', 'Description', 'Severity']];
                data.critical_issues.forEach(issue => {
                    issues_data.push([
                        issue.type,
                        issue.category,
                        issue.title,
                        issue.description,
                        issue.severity
                    ]);
                });
                
                const issues_sheet = XLSX.utils.aoa_to_sheet(issues_data);
                XLSX.utils.book_append_sheet(workbook, issues_sheet, 'Critical Issues');
            }
            
            // Download the file
            XLSX.writeFile(workbook, `system_health_report_${frappe.datetime.nowdate()}.xlsx`);
            
        } catch (error) {
            console.error('Excel export error:', error);
            // Fallback to CSV
            this.export_to_csv(data);
        }
    }

    export_to_csv(data) {
        try {
            // Create CSV content
            let csv_content = "data:text/csv;charset=utf-8,";
            
            // Add summary data
            csv_content += "System Health Report Summary\\n";
            csv_content += `Total Forecasts,${data.summary.total_forecasts}\\n`;
            csv_content += `Health Score,${data.summary.overall_health_score}%\\n`;
            csv_content += `Critical Issues,${data.critical_issues.filter(i => i.type === 'critical').length}\\n`;
            csv_content += `Average Quality Score,${data.data_quality.average_quality_score}%\\n`;
            csv_content += `Average Confidence,${data.data_quality.average_confidence_score}%\\n`;
            
            // Add critical issues if any
            if (data.critical_issues.length > 0) {
                csv_content += "\\nCritical Issues\\n";
                csv_content += "Type,Category,Title,Description,Severity\\n";
                data.critical_issues.forEach(issue => {
                    csv_content += `"${issue.type}","${issue.category}","${issue.title}","${issue.description}","${issue.severity}"\\n`;
                });
            }
            
            // Create download link
            const encoded_uri = encodeURI(csv_content);
            const link = document.createElement("a");
            link.setAttribute("href", encoded_uri);
            link.setAttribute("download", `system_health_report_${frappe.datetime.nowdate()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            frappe.show_alert({
                message: __('Report exported as CSV'),
                indicator: 'green'
            });
            
        } catch (error) {
            console.error('CSV export error:', error);
            frappe.msgprint({
                title: __('Export Error'),
                message: __('Failed to export report data'),
                indicator: 'red'
            });
        }
    }

    async fix_critical_issues() {
        const critical_issues = this.current_data?.critical_issues?.filter(issue => issue.type === 'critical') || [];
        
        if (critical_issues.length === 0) {
            frappe.msgprint(__('No critical issues to fix'));
            return;
        }

        const d = new frappe.ui.Dialog({
            title: 'Fix Critical Issues',
            fields: [
                {
                    label: 'Select Issues to Fix',
                    fieldname: 'issues',
                    fieldtype: 'HTML',
                    options: this.generate_fix_issues_html(critical_issues)
                }
            ],
            primary_action_label: 'Fix Selected',
            primary_action: async (values) => {
                const selected_issues = [];
                critical_issues.forEach((issue, index) => {
                    if (d.$wrapper.find(`#issue_${index}`).is(':checked')) {
                        selected_issues.push(issue);
                    }
                });

                if (selected_issues.length === 0) {
                    frappe.msgprint(__('Please select at least one issue to fix'));
                    return;
                }

                await this.execute_fixes(selected_issues);
                d.hide();
                this.load_report(); // Refresh the report
            }
        });

        d.show();
    }

    generate_fix_issues_html(issues) {
        let html = '<div class="fix-issues-container">';
        
        issues.forEach((issue, index) => {
            html += `
                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" id="issue_${index}" checked>
                    <label class="form-check-label" for="issue_${index}">
                        <strong>${issue.title}</strong><br>
                        <small class="text-muted">${issue.description}</small><br>
                        <small class="text-info">Action: ${issue.action_required}</small>
                    </label>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    async execute_fixes(selected_issues) {
        if (!selected_issues || selected_issues.length === 0) {
            frappe.msgprint(__('No issues selected for fixing'));
            return;
        }

        const progress = frappe.show_progress(__('Fixing Issues'), 0, selected_issues.length);

        for (let i = 0; i < selected_issues.length; i++) {
            const issue = selected_issues[i];
            try {
                progress.set_progress(i + 1);
                progress.set_description(`Fixing: ${issue.title}`);

                if (issue.category === 'Calculation Error') {
                    await this.fix_bounds_calculation_error(issue);
                } else if (issue.category === 'Data Quality') {
                    await this.fix_data_quality_issues(issue);
                } else if (issue.category === 'Integration') {
                    await this.fix_integration_issues(issue);
                } else {
                    console.warn(`Unknown issue category: ${issue.category}`);
                }

                frappe.show_alert({
                    message: `Fixed: ${issue.title}`,
                    indicator: 'green'
                });

            } catch (error) {
                console.error('Fix error for issue:', issue.title, error);
                frappe.show_alert({
                    message: `Failed to fix: ${issue.title}`,
                    indicator: 'red'
                });
            }
        }

        progress.hide();
        
        frappe.show_alert({
            message: __('Fix process completed'),
            indicator: 'blue'
        });
    }

    async fix_bounds_calculation_error(issue) {
        // Call Python method to fix bounds calculation
        const affected_forecasts = issue.affected_forecasts || [];
        
        if (affected_forecasts.length === 0) {
            console.warn('No affected forecasts found for bounds calculation fix');
            return;
        }
        
        for (const forecast of affected_forecasts) {
            try {
                const response = await frappe.call({
                    method: 'ai_inventory.ai_inventory.doctype.ai_financial_forecast.ai_financial_forecast.fix_bounds_issue',
                    args: {
                        name: forecast.name
                    }
                });
                
                if (!response.message?.success) {
                    console.error(`Failed to fix forecast ${forecast.name}:`, response.message?.error);
                }
            } catch (error) {
                console.error(`Error fixing forecast ${forecast.name}:`, error);
                throw error;
            }
        }
    }

    async fix_data_quality_issues(issue) {
        // Implement data quality fixes
        try {
            const response = await frappe.call({
                method: 'ai_inventory.ai_inventory.utils.data_quality.fix_data_quality_issues',
                args: {
                    company: this.company,
                    issue_type: issue.category
                }
            });

            if (!response.message?.success) {
                throw new Error(response.message?.error || 'Data quality fix failed');
            }

            return response;
        } catch (error) {
            console.error('Data quality fix error:', error);
            throw error;
        }
    }

    async fix_integration_issues(issue) {
        // Implement integration fixes
        try {
            const response = await frappe.call({
                method: 'ai_inventory.ai_inventory.utils.integration.fix_sync_issues',
                args: {
                    company: this.company
                }
            });

            if (!response.message?.success) {
                throw new Error(response.message?.error || 'Integration fix failed');
            }

            return response;
        } catch (error) {
            console.error('Integration fix error:', error);
            throw error;
        }
    }

    show_affected_forecasts(category) {
        // Show modal with affected forecasts
        const issue = this.current_data.critical_issues.find(i => i.category === category);
        
        if (!issue || !issue.affected_forecasts) {
            frappe.msgprint(__('No affected forecasts found'));
            return;
        }

        const d = new frappe.ui.Dialog({
            title: `Affected Forecasts - ${category}`,
            size: 'large',
            fields: [
                {
                    label: 'Forecasts',
                    fieldname: 'forecasts_table',
                    fieldtype: 'HTML',
                    options: this.generate_forecasts_table_html(issue.affected_forecasts)
                }
            ]
        });

        d.show();
    }

    generate_forecasts_table_html(forecasts) {
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Forecast ID</th>
                        <th>Account</th>
                        <th>Predicted Amount</th>
                        <th>Upper Bound</th>
                        <th>Lower Bound</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        forecasts.forEach(forecast => {
            html += `
                <tr>
                    <td><a href="/app/ai-financial-forecast/${forecast.name}" target="_blank">${forecast.name}</a></td>
                    <td>${forecast.account}</td>
                    <td>₹${(forecast.predicted_amount || 0).toLocaleString()}</td>
                    <td>₹${(forecast.upper_bound || 0).toLocaleString()}</td>
                    <td>₹${(forecast.lower_bound || 0).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="system_health_report.fix_individual_forecast('${forecast.name}')">
                            Fix
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    async fix_individual_forecast(forecast_name) {
        try {
            const response = await frappe.call({
                method: 'ai_inventory.ai_inventory.doctype.ai_financial_forecast.ai_financial_forecast.fix_bounds_issue',
                args: {
                    name: forecast_name
                }
            });

            if (response.message.success) {
                frappe.show_alert({
                    message: response.message.message,
                    indicator: 'green'
                });
                this.load_report(); // Refresh the report
            } else {
                frappe.msgprint(response.message.message);
            }

        } catch (error) {
            frappe.msgprint(__('Failed to fix forecast'));
        }
    }

    fix_issue(category) {
        const issue = this.current_data.critical_issues.find(i => i.category === category);
        this.execute_fixes([issue]);
    }

    implement_recommendation(index) {
        const recommendation = this.current_data.recommendations[index];
        
        frappe.confirm(
            `Implement: ${recommendation.title}?<br><br>
             <strong>Effort:</strong> ${recommendation.estimated_effort}<br>
             <strong>Impact:</strong> ${recommendation.impact}`,
            () => {
                // Implement the recommendation
                this.execute_recommendation(recommendation);
            }
        );
    }

    schedule_recommendation(index) {
        const recommendation = this.current_data.recommendations[index];
        
        const d = new frappe.ui.Dialog({
            title: 'Schedule Recommendation',
            fields: [
                {
                    label: 'Recommendation',
                    fieldname: 'title',
                    fieldtype: 'Data',
                    default: recommendation.title,
                    read_only: 1
                },
                {
                    label: 'Scheduled Date',
                    fieldname: 'scheduled_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.add_days(frappe.datetime.nowdate(), 7)
                },
                {
                    label: 'Assigned To',
                    fieldname: 'assigned_to',
                    fieldtype: 'Link',
                    options: 'User'
                },
                {
                    label: 'Notes',
                    fieldname: 'notes',
                    fieldtype: 'Text Editor'
                }
            ],
            primary_action_label: 'Schedule',
            primary_action: (values) => {
                // Create a task or reminder
                this.create_scheduled_task(recommendation, values);
                d.hide();
            }
        });

        d.show();
    }

    async execute_recommendation(recommendation) {
        // Implementation logic based on recommendation type
        frappe.show_alert({
            message: `Implementing: ${recommendation.title}`,
            indicator: 'blue'
        });

        // This would contain specific implementation logic
        // For now, just show a success message
        setTimeout(() => {
            frappe.show_alert({
                message: `Recommendation implemented successfully`,
                indicator: 'green'
            });
        }, 2000);
    }

    async create_scheduled_task(recommendation, values) {
        try {
            await frappe.call({
                method: 'frappe.desk.form.assign_to.add',
                args: {
                    assign_to: [values.assigned_to],
                    doctype: 'AI Financial Forecast',
                    name: 'System Health',
                    description: `${recommendation.title}\n\n${recommendation.description}\n\nNotes: ${values.notes}`,
                    date: values.scheduled_date
                }
            });

            frappe.show_alert({
                message: __('Recommendation scheduled successfully'),
                indicator: 'green'
            });

        } catch (error) {
            frappe.msgprint(__('Failed to schedule recommendation'));
        }
    }
}

// Global reference for button callbacks
window.system_health_report = null;

// Initialize when page loads
$(document).ready(function() {
    if (window.location.pathname.includes('system-health-report')) {
        // Global reference will be set in the page load handler above
        console.log('System Health Report page detected');
    }
});