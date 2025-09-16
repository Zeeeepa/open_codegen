/**
 * Real-time Monitoring System
 * Handles system metrics, endpoint performance, and request logs
 */

class MonitoringSystem {
    constructor() {
        this.metricsInterval = null;
        this.logsInterval = null;
        this.isMonitoring = false;
        this.metricsHistory = [];
        this.requestLogs = [];
        
        this.init();
    }

    init() {
        // Initialize monitoring when tab is accessed
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Auto-refresh controls
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startMonitoring();
                } else {
                    this.stopMonitoring();
                }
            });
        }
    }

    async refreshMonitoring() {
        try {
            await Promise.all([
                this.loadSystemMetrics(),
                this.loadEndpointMetrics(),
                this.loadRequestLogs()
            ]);
        } catch (error) {
            console.error('Failed to refresh monitoring data:', error);
        }
    }

    async loadSystemMetrics() {
        try {
            const response = await fetch('/api/monitoring/system');
            if (!response.ok) {
                throw new Error('Failed to fetch system metrics');
            }

            const metrics = await response.json();
            this.displaySystemMetrics(metrics);
            
            // Store for history
            this.metricsHistory.push({
                timestamp: new Date(),
                ...metrics
            });
            
            // Keep only last 100 entries
            if (this.metricsHistory.length > 100) {
                this.metricsHistory.shift();
            }
            
        } catch (error) {
            console.error('Failed to load system metrics:', error);
            this.displaySystemMetricsError();
        }
    }

    displaySystemMetrics(metrics) {
        const container = document.getElementById('systemMetrics');
        if (!container) return;

        const metricsHtml = `
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-microchip"></i>
                        <h4>CPU Usage</h4>
                    </div>
                    <div class="metric-value">${metrics.cpu_usage?.toFixed(1) || 0}%</div>
                    <div class="metric-bar">
                        <div class="metric-bar-fill" style="width: ${metrics.cpu_usage || 0}%"></div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-memory"></i>
                        <h4>Memory Usage</h4>
                    </div>
                    <div class="metric-value">${metrics.memory_usage?.toFixed(1) || 0}%</div>
                    <div class="metric-bar">
                        <div class="metric-bar-fill" style="width: ${metrics.memory_usage || 0}%"></div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-hdd"></i>
                        <h4>Disk Usage</h4>
                    </div>
                    <div class="metric-value">${metrics.disk_usage?.toFixed(1) || 0}%</div>
                    <div class="metric-bar">
                        <div class="metric-bar-fill" style="width: ${metrics.disk_usage || 0}%"></div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-network-wired"></i>
                        <h4>Network I/O</h4>
                    </div>
                    <div class="metric-value">${this.formatBytes(metrics.network_io || 0)}/s</div>
                    <div class="metric-detail">
                        ↑ ${this.formatBytes(metrics.network_out || 0)}/s
                        ↓ ${this.formatBytes(metrics.network_in || 0)}/s
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-clock"></i>
                        <h4>Uptime</h4>
                    </div>
                    <div class="metric-value">${this.formatUptime(metrics.uptime || 0)}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-server"></i>
                        <h4>Active Connections</h4>
                    </div>
                    <div class="metric-value">${metrics.active_connections || 0}</div>
                </div>
            </div>
            
            <div class="system-info">
                <h4>System Information</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">OS:</span>
                        <span class="info-value">${metrics.os_info || 'Unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Python Version:</span>
                        <span class="info-value">${metrics.python_version || 'Unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Last Updated:</span>
                        <span class="info-value">${new Date().toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = metricsHtml;
    }

    displaySystemMetricsError() {
        const container = document.getElementById('systemMetrics');
        if (!container) return;

        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load system metrics</p>
                <button class="btn secondary" onclick="monitoringSystem.loadSystemMetrics()">
                    <i class="fas fa-sync-alt"></i>
                    Retry
                </button>
            </div>
        `;
    }

    async loadEndpointMetrics() {
        try {
            const response = await fetch('/api/monitoring/endpoints');
            if (!response.ok) {
                throw new Error('Failed to fetch endpoint metrics');
            }

            const metrics = await response.json();
            this.displayEndpointMetrics(metrics);
            
        } catch (error) {
            console.error('Failed to load endpoint metrics:', error);
            this.displayEndpointMetricsError();
        }
    }

    displayEndpointMetrics(metrics) {
        const container = document.getElementById('endpointMetrics');
        if (!container) return;

        if (!metrics || metrics.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-line"></i>
                    <p>No endpoint metrics available</p>
                </div>
            `;
            return;
        }

        const metricsHtml = metrics.map(endpoint => `
            <div class="endpoint-metric-card">
                <div class="endpoint-metric-header">
                    <h4>${endpoint.name}</h4>
                    <span class="endpoint-status ${endpoint.status}">${endpoint.status}</span>
                </div>
                
                <div class="endpoint-metric-stats">
                    <div class="stat-item">
                        <span class="stat-label">Requests</span>
                        <span class="stat-value">${endpoint.total_requests || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Success Rate</span>
                        <span class="stat-value">${endpoint.success_rate ? (endpoint.success_rate * 100).toFixed(1) + '%' : '0%'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Avg Response</span>
                        <span class="stat-value">${endpoint.avg_response_time ? endpoint.avg_response_time.toFixed(0) + 'ms' : '0ms'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Errors</span>
                        <span class="stat-value error">${endpoint.error_count || 0}</span>
                    </div>
                </div>
                
                <div class="endpoint-metric-chart">
                    <div class="chart-placeholder">
                        <i class="fas fa-chart-area"></i>
                        <span>Response Time Trend</span>
                    </div>
                </div>
                
                <div class="endpoint-metric-details">
                    <div class="detail-item">
                        <span class="detail-label">Last Request:</span>
                        <span class="detail-value">${endpoint.last_request ? new Date(endpoint.last_request).toLocaleString() : 'Never'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Provider:</span>
                        <span class="detail-value">${endpoint.provider_name || 'Unknown'}</span>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = metricsHtml;
    }

    displayEndpointMetricsError() {
        const container = document.getElementById('endpointMetrics');
        if (!container) return;

        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load endpoint metrics</p>
                <button class="btn secondary" onclick="monitoringSystem.loadEndpointMetrics()">
                    <i class="fas fa-sync-alt"></i>
                    Retry
                </button>
            </div>
        `;
    }

    async loadRequestLogs() {
        try {
            const response = await fetch('/api/monitoring/logs?limit=50');
            if (!response.ok) {
                throw new Error('Failed to fetch request logs');
            }

            const logs = await response.json();
            this.displayRequestLogs(logs);
            
        } catch (error) {
            console.error('Failed to load request logs:', error);
            this.displayRequestLogsError();
        }
    }

    displayRequestLogs(logs) {
        const container = document.getElementById('requestLogs');
        if (!container) return;

        if (!logs || logs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No request logs available</p>
                </div>
            `;
            return;
        }

        const logsHtml = `
            <div class="logs-header">
                <h4>Recent Requests</h4>
                <div class="logs-controls">
                    <button class="btn secondary" onclick="monitoringSystem.exportLogs()">
                        <i class="fas fa-download"></i>
                        Export
                    </button>
                    <button class="btn secondary" onclick="monitoringSystem.clearLogs()">
                        <i class="fas fa-trash"></i>
                        Clear
                    </button>
                </div>
            </div>
            
            <div class="logs-table">
                <div class="logs-table-header">
                    <div class="log-col-time">Time</div>
                    <div class="log-col-endpoint">Endpoint</div>
                    <div class="log-col-method">Method</div>
                    <div class="log-col-status">Status</div>
                    <div class="log-col-duration">Duration</div>
                    <div class="log-col-message">Message</div>
                </div>
                
                <div class="logs-table-body">
                    ${logs.map(log => `
                        <div class="log-row ${this.getLogRowClass(log.status)}">
                            <div class="log-col-time">${new Date(log.timestamp).toLocaleTimeString()}</div>
                            <div class="log-col-endpoint">${log.endpoint_name || 'Unknown'}</div>
                            <div class="log-col-method">${log.method || 'GET'}</div>
                            <div class="log-col-status">
                                <span class="status-badge ${this.getStatusClass(log.status)}">${log.status || 'Unknown'}</span>
                            </div>
                            <div class="log-col-duration">${log.duration ? log.duration.toFixed(0) + 'ms' : '-'}</div>
                            <div class="log-col-message" title="${log.message || ''}">${this.truncateMessage(log.message || '')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        container.innerHTML = logsHtml;
    }

    displayRequestLogsError() {
        const container = document.getElementById('requestLogs');
        if (!container) return;

        container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load request logs</p>
                <button class="btn secondary" onclick="monitoringSystem.loadRequestLogs()">
                    <i class="fas fa-sync-alt"></i>
                    Retry
                </button>
            </div>
        `;
    }

    getLogRowClass(status) {
        if (status >= 200 && status < 300) return 'success';
        if (status >= 400 && status < 500) return 'warning';
        if (status >= 500) return 'error';
        return '';
    }

    getStatusClass(status) {
        if (status >= 200 && status < 300) return 'success';
        if (status >= 300 && status < 400) return 'info';
        if (status >= 400 && status < 500) return 'warning';
        if (status >= 500) return 'error';
        return 'secondary';
    }

    truncateMessage(message, maxLength = 50) {
        if (!message) return '';
        return message.length > maxLength ? message.substring(0, maxLength) + '...' : message;
    }

    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        
        // Refresh immediately
        this.refreshMonitoring();
        
        // Set up intervals
        this.metricsInterval = setInterval(() => {
            this.loadSystemMetrics();
            this.loadEndpointMetrics();
        }, 5000); // Every 5 seconds
        
        this.logsInterval = setInterval(() => {
            this.loadRequestLogs();
        }, 10000); // Every 10 seconds
        
        console.log('Monitoring started');
    }

    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        
        if (this.metricsInterval) {
            clearInterval(this.metricsInterval);
            this.metricsInterval = null;
        }
        
        if (this.logsInterval) {
            clearInterval(this.logsInterval);
            this.logsInterval = null;
        }
        
        console.log('Monitoring stopped');
    }

    async exportLogs() {
        try {
            const response = await fetch('/api/monitoring/logs?limit=1000&format=json');
            if (!response.ok) {
                throw new Error('Failed to export logs');
            }

            const logs = await response.json();
            const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `request_logs_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Failed to export logs:', error);
            alert('Failed to export logs: ' + error.message);
        }
    }

    async clearLogs() {
        if (!confirm('Are you sure you want to clear all request logs?')) {
            return;
        }

        try {
            const response = await fetch('/api/monitoring/logs', {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to clear logs');
            }

            this.loadRequestLogs();
            
        } catch (error) {
            console.error('Failed to clear logs:', error);
            alert('Failed to clear logs: ' + error.message);
        }
    }

    // Utility methods
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    // Method to create simple charts (future enhancement)
    createChart(containerId, data, options = {}) {
        // This would integrate with a charting library like Chart.js
        const container = document.getElementById(containerId);
        if (!container) return;

        // Placeholder for chart implementation
        container.innerHTML = `
            <div class="chart-placeholder">
                <i class="fas fa-chart-line"></i>
                <span>Chart visualization coming soon</span>
            </div>
        `;
    }
}

// Initialize monitoring system
let monitoringSystem;
document.addEventListener('DOMContentLoaded', () => {
    monitoringSystem = new MonitoringSystem();
    window.monitoringSystem = monitoringSystem; // Make available globally
    
    // Hook into dashboard tab switching
    if (window.dashboard) {
        const originalLoadTabData = window.dashboard.loadTabData;
        window.dashboard.loadTabData = function(tabName) {
            originalLoadTabData.call(this, tabName);
            if (tabName === 'monitoring') {
                monitoringSystem.refreshMonitoring();
            }
        };
        
        // Make refreshMonitoring available to dashboard
        window.dashboard.refreshMonitoring = () => {
            return monitoringSystem.refreshMonitoring();
        };
    }
});
