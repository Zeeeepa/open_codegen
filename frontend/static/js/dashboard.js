/**
 * AI Endpoint Orchestrator Dashboard JavaScript
 * Main dashboard functionality and API interactions
 */

class EndpointDashboard {
    constructor() {
        this.apiBase = '/api/endpoints';
        this.endpoints = new Map();
        this.currentTab = 'dashboard';
        this.connectionStatus = 'connected';
        this.refreshInterval = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupTabNavigation();
        this.startPeriodicRefresh();
        await this.loadInitialData();
        this.updateConnectionStatus();
    }

    setupEventListeners() {
        // Global event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.loadInitialData();
        });

        // Modal event listeners
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    setupTabNavigation() {
        const navTabs = document.querySelectorAll('.nav-tab');
        navTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update active content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        this.currentTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'dashboard':
                await this.refreshDashboard();
                break;
            case 'endpoints':
                await this.refreshEndpoints();
                break;
            case 'yaml-editor':
                this.initializeYAMLEditor();
                break;
            case 'chat-interface':
                await this.refreshChatEndpoints();
                break;
            case 'monitoring':
                await this.refreshMonitoring();
                break;
            case 'templates':
                await this.loadTemplates();
                break;
        }
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.refreshDashboard(),
                this.loadGlobalStats()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    async refreshDashboard() {
        try {
            const endpoints = await this.fetchEndpoints();
            this.updateDashboardStats(endpoints);
            this.updateEndpointsOverview(endpoints);
            this.updateRecentActivity();
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
        }
    }

    async fetchEndpoints() {
        const response = await fetch(this.apiBase);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const endpoints = await response.json();
        
        // Update local cache
        this.endpoints.clear();
        endpoints.forEach(endpoint => {
            this.endpoints.set(endpoint.id, endpoint);
        });
        
        return endpoints;
    }

    updateDashboardStats(endpoints) {
        const totalEndpoints = endpoints.length;
        const runningEndpoints = endpoints.filter(e => e.status === 'running').length;
        const healthyEndpoints = endpoints.filter(e => e.status === 'running' && !e.has_errors).length;
        const totalRequests = endpoints.reduce((sum, e) => sum + (e.total_requests || 0), 0);

        // Update dashboard stats
        document.getElementById('dashTotalEndpoints').textContent = totalEndpoints;
        document.getElementById('dashRunningEndpoints').textContent = runningEndpoints;
        document.getElementById('dashHealthyEndpoints').textContent = healthyEndpoints;
        document.getElementById('dashTotalRequests').textContent = totalRequests.toLocaleString();

        // Update header stats
        document.getElementById('totalEndpoints').textContent = totalEndpoints;
        document.getElementById('activeEndpoints').textContent = runningEndpoints;
        document.getElementById('totalRequests').textContent = totalRequests.toLocaleString();
    }

    updateEndpointsOverview(endpoints) {
        const container = document.getElementById('endpointsOverview');
        
        if (endpoints.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plug"></i>
                    <p>No endpoints configured</p>
                    <button class="btn-link" onclick="dashboard.showCreateEndpointModal()">Create your first endpoint</button>
                </div>
            `;
            return;
        }

        const endpointsHtml = endpoints.slice(0, 5).map(endpoint => `
            <div class="endpoint-overview-item">
                <div class="endpoint-overview-info">
                    <h5>${endpoint.name}</h5>
                    <span class="endpoint-type">${endpoint.provider_type}</span>
                </div>
                <div class="endpoint-overview-status">
                    <span class="status-indicator ${endpoint.status}">${endpoint.status}</span>
                    <div class="endpoint-overview-actions">
                        <button class="btn-icon" onclick="dashboard.toggleEndpoint('${endpoint.id}')" title="${endpoint.status === 'running' ? 'Stop' : 'Start'}">
                            <i class="fas fa-${endpoint.status === 'running' ? 'stop' : 'play'}"></i>
                        </button>
                        <button class="btn-icon" onclick="dashboard.testEndpoint('${endpoint.id}')" title="Test">
                            <i class="fas fa-vial"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = endpointsHtml;
    }

    updateRecentActivity() {
        const activityList = document.getElementById('activityList');
        const activities = this.getRecentActivities();
        
        const activitiesHtml = activities.map(activity => `
            <div class="activity-item">
                <i class="fas fa-${activity.icon}"></i>
                <span>${activity.message}</span>
                <time>${activity.time}</time>
            </div>
        `).join('');

        activityList.innerHTML = activitiesHtml;
    }

    getRecentActivities() {
        // This would typically come from an API
        return [
            {
                icon: 'info-circle',
                message: 'System initialized',
                time: 'Just now'
            },
            {
                icon: 'play',
                message: 'Endpoint "Z.AI Test" started',
                time: '2 minutes ago'
            },
            {
                icon: 'check-circle',
                message: 'Configuration validated successfully',
                time: '5 minutes ago'
            }
        ];
    }

    async refreshEndpoints() {
        try {
            const endpoints = await this.fetchEndpoints();
            this.renderEndpointsGrid(endpoints);
        } catch (error) {
            console.error('Failed to refresh endpoints:', error);
            this.showNotification('Failed to load endpoints', 'error');
        }
    }

    renderEndpointsGrid(endpoints) {
        const grid = document.getElementById('endpointsGrid');
        
        if (endpoints.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plug"></i>
                    <p>No endpoints configured</p>
                    <button class="btn primary" onclick="dashboard.showCreateEndpointModal()">
                        <i class="fas fa-plus"></i>
                        Create Endpoint
                    </button>
                </div>
            `;
            return;
        }

        const endpointsHtml = endpoints.map(endpoint => this.renderEndpointCard(endpoint)).join('');
        grid.innerHTML = endpointsHtml;
    }

    renderEndpointCard(endpoint) {
        const statusClass = endpoint.status || 'stopped';
        const statusIcon = statusClass === 'running' ? 'play' : statusClass === 'error' ? 'exclamation-triangle' : 'stop';
        
        return `
            <div class="endpoint-card" data-endpoint-id="${endpoint.id}">
                <div class="endpoint-header">
                    <div class="endpoint-info">
                        <h4>${endpoint.name}</h4>
                        <span class="endpoint-type">${endpoint.provider_type}</span>
                    </div>
                    <div class="endpoint-status ${statusClass}">
                        <i class="fas fa-${statusIcon}"></i>
                        ${statusClass}
                    </div>
                </div>
                
                <div class="endpoint-metrics">
                    <div class="metric-item">
                        <span class="metric-value">${endpoint.total_requests || 0}</span>
                        <span class="metric-label">Requests</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-value">${endpoint.success_rate ? (endpoint.success_rate * 100).toFixed(1) + '%' : '0%'}</span>
                        <span class="metric-label">Success</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-value">${endpoint.avg_response_time ? endpoint.avg_response_time.toFixed(0) + 'ms' : '0ms'}</span>
                        <span class="metric-label">Avg Time</span>
                    </div>
                </div>
                
                <div class="endpoint-actions">
                    <button class="btn ${statusClass === 'running' ? 'warning' : 'success'}" 
                            onclick="dashboard.toggleEndpoint('${endpoint.id}')">
                        <i class="fas fa-${statusClass === 'running' ? 'stop' : 'play'}"></i>
                        ${statusClass === 'running' ? 'Stop' : 'Start'}
                    </button>
                    <button class="btn secondary" onclick="dashboard.testEndpoint('${endpoint.id}')">
                        <i class="fas fa-vial"></i>
                        Test
                    </button>
                    <button class="btn secondary" onclick="dashboard.editEndpoint('${endpoint.id}')">
                        <i class="fas fa-edit"></i>
                        Edit
                    </button>
                    <button class="btn error" onclick="dashboard.deleteEndpoint('${endpoint.id}')">
                        <i class="fas fa-trash"></i>
                        Delete
                    </button>
                </div>
            </div>
        `;
    }

    async toggleEndpoint(endpointId) {
        try {
            const endpoint = this.endpoints.get(endpointId);
            if (!endpoint) return;

            const action = endpoint.status === 'running' ? 'stop' : 'start';
            const response = await fetch(`${this.apiBase}/${endpointId}/${action}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Failed to ${action} endpoint`);
            }

            this.showNotification(`Endpoint ${action}ed successfully`, 'success');
            await this.refreshCurrentTab();
        } catch (error) {
            console.error(`Failed to toggle endpoint:`, error);
            this.showNotification(`Failed to toggle endpoint: ${error.message}`, 'error');
        }
    }

    async testEndpoint(endpointId) {
        try {
            const response = await fetch(`${this.apiBase}/${endpointId}/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: 'Hello, this is a test message.'
                })
            });

            if (!response.ok) {
                throw new Error('Test failed');
            }

            const result = await response.json();
            this.showNotification('Endpoint test successful', 'success');
            
            // Switch to chat interface to show result
            this.switchTab('chat-interface');
            this.displayTestResult(endpointId, result);
        } catch (error) {
            console.error('Failed to test endpoint:', error);
            this.showNotification(`Test failed: ${error.message}`, 'error');
        }
    }

    async deleteEndpoint(endpointId) {
        if (!confirm('Are you sure you want to delete this endpoint?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/${endpointId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete endpoint');
            }

            this.showNotification('Endpoint deleted successfully', 'success');
            await this.refreshCurrentTab();
        } catch (error) {
            console.error('Failed to delete endpoint:', error);
            this.showNotification(`Failed to delete endpoint: ${error.message}`, 'error');
        }
    }

    showCreateEndpointModal() {
        const modal = document.getElementById('createEndpointModal');
        modal.classList.add('active');
        
        // Reset form
        document.getElementById('createEndpointForm').reset();
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('active');
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    async createEndpoint() {
        const form = document.getElementById('createEndpointForm');
        const formData = new FormData(form);
        
        const endpointData = {
            name: document.getElementById('endpointName').value,
            provider_type: document.getElementById('endpointType').value,
            provider_name: document.getElementById('endpointProvider').value,
            model_name: document.getElementById('endpointProvider').value + '-model',
            config_data: {
                url: document.getElementById('endpointUrl').value,
                auth_email: document.getElementById('authEmail').value,
                auth_password: document.getElementById('authPassword').value,
                api_key: document.getElementById('apiKey').value,
                max_parallel: parseInt(document.getElementById('maxParallel').value)
            }
        };

        try {
            const response = await fetch(this.apiBase, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(endpointData)
            });

            if (!response.ok) {
                throw new Error('Failed to create endpoint');
            }

            this.showNotification('Endpoint created successfully', 'success');
            this.closeModal('createEndpointModal');
            await this.refreshCurrentTab();
        } catch (error) {
            console.error('Failed to create endpoint:', error);
            this.showNotification(`Failed to create endpoint: ${error.message}`, 'error');
        }
    }

    async refreshCurrentTab() {
        await this.loadTabData(this.currentTab);
        await this.loadGlobalStats();
    }

    async loadGlobalStats() {
        try {
            const endpoints = await this.fetchEndpoints();
            this.updateDashboardStats(endpoints);
        } catch (error) {
            console.error('Failed to load global stats:', error);
        }
    }

    startPeriodicRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshCurrentTab();
        }, 30000);
    }

    stopPeriodicRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('connectionStatus');
        const statusClass = this.connectionStatus === 'connected' ? 'connected' : 'disconnected';
        
        statusElement.className = `connection-status ${statusClass}`;
        statusElement.innerHTML = `
            <i class="fas fa-circle"></i>
            <span>${this.connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}</span>
        `;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Placeholder methods for other tabs
    initializeYAMLEditor() {
        // Will be implemented in yaml-editor.js
        console.log('Initializing YAML editor...');
    }

    async refreshChatEndpoints() {
        // Will be implemented in chat-interface.js
        console.log('Refreshing chat endpoints...');
    }

    async refreshMonitoring() {
        // Will be implemented in monitoring.js
        console.log('Refreshing monitoring data...');
    }

    async loadTemplates() {
        // Load template data
        console.log('Loading templates...');
    }

    displayTestResult(endpointId, result) {
        // Will be implemented in chat-interface.js
        console.log('Displaying test result:', result);
    }
}

// Global functions for HTML onclick handlers
window.showCreateEndpointModal = () => dashboard.showCreateEndpointModal();
window.closeModal = (modalId) => dashboard.closeModal(modalId);
window.createEndpoint = () => dashboard.createEndpoint();
window.switchTab = (tabName) => dashboard.switchTab(tabName);
window.refreshDashboard = () => dashboard.refreshCurrentTab();
window.refreshEndpoints = () => dashboard.refreshEndpoints();

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new EndpointDashboard();
    window.dashboard = dashboard; // Make available globally
});
