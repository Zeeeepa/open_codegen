/**
 * Monitoring Module
 * Handles real-time monitoring dashboard functionality
 */

class MonitoringDashboard {
    constructor() {
        this.refreshInterval = null;
        this.performanceChart = null;
        this.autoRefreshEnabled = true;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeChart();
        this.startAutoRefresh();
    }
    
    initializeElements() {
        this.refreshBtn = document.getElementById('refreshMetricsBtn');
        this.autoRefreshToggle = document.getElementById('autoRefreshToggle');
        this.performanceCanvas = document.getElementById('performanceCanvas');
        this.healthList = document.getElementById('healthList');
        this.cpuMeter = document.getElementById('cpuMeter');
        this.memoryMeter = document.getElementById('memoryMeter');
        this.cpuValue = document.getElementById('cpuValue');
        this.memoryValue = document.getElementById('memoryValue');
        this.logViewer = document.getElementById('logViewer');
    }
    
    initializeEventListeners() {
        this.refreshBtn.addEventListener('click', () => this.refreshMetrics());
        
        this.autoRefreshToggle.addEventListener('change', (e) => {
            this.autoRefreshEnabled = e.target.checked;
            if (this.autoRefreshEnabled) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
    }
    
    initializeChart() {
        if (!this.performanceCanvas) return;
        
        const ctx = this.performanceCanvas.getContext('2d');
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1,
                    fill: true
                }, {
                    label: 'Success Rate (%)',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.1,
                    fill: true,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Response Time (ms)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Success Rate (%)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }
    
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Refresh every 5 seconds
        this.refreshInterval = setInterval(() => {
            if (this.autoRefreshEnabled) {
                this.refreshMetrics();
            }
        }, 5000);
        
        // Initial refresh
        this.refreshMetrics();
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    async refreshMetrics() {
        try {
            // Show loading state
            this.refreshBtn.innerHTML = '<i class="fas fa-spin fa-spinner"></i> Refreshing...';
            this.refreshBtn.disabled = true;
            
            // Fetch multiple metrics in parallel
            const [systemMetrics, endpointHealth, performanceData, logs] = await Promise.all([
                this.fetchSystemMetrics(),
                this.fetchEndpointHealth(),
                this.fetchPerformanceData(),
                this.fetchRecentLogs()
            ]);
            
            // Update UI components
            this.updateSystemMetrics(systemMetrics);
            this.updateEndpointHealth(endpointHealth);
            this.updatePerformanceChart(performanceData);
            this.updateLogs(logs);
            
        } catch (error) {
            console.error('Failed to refresh metrics:', error);
            this.showError('Failed to refresh metrics: ' + error.message);
        } finally {
            // Restore button state
            this.refreshBtn.innerHTML = '<i class="fas fa-sync"></i> Refresh';
            this.refreshBtn.disabled = false;
        }
    }
    
    async fetchSystemMetrics() {
        const response = await fetch('/api/monitoring/system');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }
    
    async fetchEndpointHealth() {
        const response = await fetch('/api/monitoring/endpoints');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }
    
    async fetchPerformanceData() {
        const response = await fetch('/api/monitoring/performance?limit=20');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }
    
    async fetchRecentLogs() {
        const response = await fetch('/api/monitoring/logs?limit=50');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }
    
    updateSystemMetrics(metrics) {
        // Update CPU usage
        const cpuUsage = metrics.cpu_usage || 0;
        this.cpuMeter.style.width = `${cpuUsage}%`;
        this.cpuValue.textContent = `${cpuUsage.toFixed(1)}%`;
        
        // Update Memory usage
        const memoryUsage = metrics.memory_usage || 0;
        this.memoryMeter.style.width = `${memoryUsage}%`;
        this.memoryValue.textContent = `${memoryUsage.toFixed(1)}%`;
        
        // Add color coding based on usage levels
        this.updateMeterColor(this.cpuMeter, cpuUsage);
        this.updateMeterColor(this.memoryMeter, memoryUsage);
    }
    
    updateMeterColor(meter, usage) {
        meter.className = 'meter-fill';
        if (usage > 90) {
            meter.classList.add('meter-critical');
        } else if (usage > 70) {
            meter.classList.add('meter-warning');
        } else {
            meter.classList.add('meter-normal');
        }
    }
    
    updateEndpointHealth(healthData) {
        this.healthList.innerHTML = '';
        
        if (!healthData.endpoints || healthData.endpoints.length === 0) {
            this.healthList.innerHTML = `
                <div class="health-item">
                    <span class="health-indicator offline"></span>
                    <span>No endpoints configured</span>
                </div>
            `;
            return;
        }
        
        healthData.endpoints.forEach(endpoint => {
            const healthItem = document.createElement('div');
            healthItem.className = 'health-item';
            
            const status = endpoint.status || 'unknown';
            const statusClass = this.getStatusClass(status);
            
            healthItem.innerHTML = `
                <span class="health-indicator ${statusClass}"></span>
                <div class="health-details">
                    <div class="health-name">${endpoint.name}</div>
                    <div class="health-status">${status.toUpperCase()}</div>
                    <div class="health-metrics">
                        Avg: ${endpoint.avg_response_time || 0}ms | 
                        Success: ${endpoint.success_rate || 0}%
                    </div>
                </div>
            `;
            
            this.healthList.appendChild(healthItem);
        });
    }
    
    getStatusClass(status) {
        switch (status.toLowerCase()) {
            case 'online':
            case 'healthy': return 'online';
            case 'offline':
            case 'error': return 'offline';
            case 'warning':
            case 'degraded': return 'warning';
            default: return 'offline';
        }
    }
    
    updatePerformanceChart(performanceData) {
        if (!this.performanceChart || !performanceData.metrics) return;
        
        const labels = performanceData.metrics.map(m => 
            new Date(m.timestamp).toLocaleTimeString()
        );
        
        const responseTimes = performanceData.metrics.map(m => m.avg_response_time || 0);
        const successRates = performanceData.metrics.map(m => m.success_rate || 0);
        
        // Keep only last 20 data points
        if (labels.length > 20) {
            labels.splice(0, labels.length - 20);
            responseTimes.splice(0, responseTimes.length - 20);
            successRates.splice(0, successRates.length - 20);
        }
        
        this.performanceChart.data.labels = labels;
        this.performanceChart.data.datasets[0].data = responseTimes;
        this.performanceChart.data.datasets[1].data = successRates;
        
        this.performanceChart.update('none');
    }
    
    updateLogs(logData) {
        this.logViewer.innerHTML = '';
        
        if (!logData.logs || logData.logs.length === 0) {
            this.logViewer.innerHTML = '<div class="log-entry log-info">No recent logs</div>';
            return;
        }
        
        logData.logs.forEach(log => {
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${log.level || 'info'}`;
            
            const timestamp = new Date(log.timestamp).toLocaleString();
            logEntry.innerHTML = `
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level">[${(log.level || 'INFO').toUpperCase()}]</span>
                <span class="log-message">${log.message}</span>
            `;
            
            this.logViewer.appendChild(logEntry);
        });
        
        // Scroll to bottom to show newest logs
        this.logViewer.scrollTop = this.logViewer.scrollHeight;
    }
    
    showError(message) {
        // Add error message to logs
        const errorEntry = document.createElement('div');
        errorEntry.className = 'log-entry log-error';
        errorEntry.innerHTML = `
            <span class="log-timestamp">${new Date().toLocaleString()}</span>
            <span class="log-level">[ERROR]</span>
            <span class="log-message">${message}</span>
        `;
        
        this.logViewer.appendChild(errorEntry);
        this.logViewer.scrollTop = this.logViewer.scrollHeight;
    }
}

// Initialize monitoring dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.monitoringDashboard = new MonitoringDashboard();
});