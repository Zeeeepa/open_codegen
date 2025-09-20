/**
 * Main Dashboard JavaScript
 * Handles navigation, endpoint management, and UI interactions
 */

class Dashboard {
    constructor() {
        this.endpoints = new Map();
        this.activeTab = 'dashboard';
        this.connectionStatus = 'connected';
        
        this.init();
        this.loadEndpoints();
        this.startPeriodicUpdates();
    }

    init() {
        this.bindEvents();
        this.initializeUI();
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Add endpoint button
        const addEndpointBtn = document.getElementById('addEndpointBtn');
        if (addEndpointBtn) {
            addEndpointBtn.addEventListener('click', () => this.showAddEndpointModal());
        }

        // Add endpoint form
        const addEndpointForm = document.getElementById('addEndpointForm');
        if (addEndpointForm) {
            addEndpointForm.addEventListener('submit', (e) => this.handleAddEndpoint(e));
        }

        // Endpoint type change
        const endpointType = document.getElementById('endpointType');
        if (endpointType) {
            endpointType.addEventListener('change', (e) => this.handleEndpointTypeChange(e));
        }

        // Modal close buttons
        document.querySelectorAll('.modal-close, #cancelAddEndpoint').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Settings button
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettings());
        }
    }

    initializeUI() {
        // Set initial connection status
        this.updateConnectionStatus('connected');
        
        // Initialize dashboard stats
        this.updateDashboardStats({
            activeEndpoints: 0,
            avgResponseTime: '0ms',
            successRate: '0%',
            totalRequests: 0
        });

        // Add initial activity
        this.addActivity('System initialized', 'info');
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.activeTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    loadTabData(tabName) {
        switch (tabName) {
            case 'dashboard':
                this.refreshDashboard();
                break;
            case 'endpoints':
                this.refreshEndpoints();
                break;
            case 'monitoring':
                this.refreshMonitoring();
                break;
            case 'templates':
                this.loadTemplates();
                break;
        }
    }

    async loadEndpoints() {
        try {
            const response = await fetch('/api/config/list');
            if (!response.ok) {
                throw new Error(`Failed to load endpoints: ${response.status}`);
            }

            const data = await response.json();
            this.endpoints.clear();

            // Process configurations
            data.configs.forEach(config => {
                this.endpoints.set(config.name, {
                    ...config,
                    status: 'offline',
                    health: 'unknown',
                    lastResponse: null,
                    requests: 0,
                    errors: 0
                });
            });

            this.updateEndpointsDisplay();
            this.updateDashboardStats();

        } catch (error) {
            console.error('Failed to load endpoints:', error);
            this.showToast('error', 'Failed to load endpoints');
        }
    }

    updateEndpointsDisplay() {
        const grid = document.getElementById('endpointsGrid');
        if (!grid) return;

        if (this.endpoints.size === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plug"></i>
                    <h3>No Endpoints Configured</h3>
                    <p>Add your first AI endpoint to get started</p>
                    <button class="btn btn-primary" onclick="dashboard.showAddEndpointModal()">
                        <i class="fas fa-plus"></i> Add Endpoint
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = Array.from(this.endpoints.values()).map(endpoint => `
            <div class="endpoint-card" data-endpoint="${endpoint.name}">
                <div class="endpoint-header">
                    <div class="endpoint-info">
                        <h3>${endpoint.name}</h3>
                        <p class="endpoint-url">${endpoint.url}</p>
                    </div>
                    <div class="endpoint-status">
                        <span class="status-indicator ${endpoint.status}"></span>
                        <span class="status-text">${endpoint.status}</span>
                    </div>
                </div>
                
                <div class="endpoint-details">
                    <div class="detail-item">
                        <span class="label">Type:</span>
                        <span class="value">${endpoint.type}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Max Parallel:</span>
                        <span class="value">${endpoint.max_parallel}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Requests:</span>
                        <span class="value">${endpoint.requests}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Errors:</span>
                        <span class="value">${endpoint.errors}</span>
                    </div>
                </div>

                <div class="endpoint-actions">
                    <button class="btn btn-sm ${endpoint.status === 'online' ? 'btn-secondary' : 'btn-primary'}" 
                            onclick="dashboard.toggleEndpoint('${endpoint.name}')">
                        <i class="fas ${endpoint.status === 'online' ? 'fa-stop' : 'fa-play'}"></i>
                        ${endpoint.status === 'online' ? 'Stop' : 'Start'}
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="dashboard.testEndpoint('${endpoint.name}')">
                        <i class="fas fa-vial"></i> Test
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="dashboard.editEndpoint('${endpoint.name}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="dashboard.deleteEndpoint('${endpoint.name}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');

        // Add empty state styles
        const style = document.createElement('style');
        style.textContent = `
            .empty-state {
                grid-column: 1 / -1;
                text-align: center;
                padding: 4rem 2rem;
                color: var(--text-muted);
            }
            .empty-state i {
                font-size: 4rem;
                margin-bottom: 1rem;
                color: var(--primary-color);
            }
            .empty-state h3 {
                margin-bottom: 0.5rem;
                color: var(--text-primary);
            }
            .empty-state p {
                margin-bottom: 2rem;
            }
            .endpoint-card {
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                padding: 1.5rem;
                box-shadow: var(--shadow-sm);
            }
            .endpoint-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 1rem;
            }
            .endpoint-info h3 {
                margin-bottom: 0.25rem;
                color: var(--text-primary);
            }
            .endpoint-url {
                color: var(--text-secondary);
                font-size: 0.875rem;
            }
            .endpoint-status {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .status-text {
                font-size: 0.875rem;
                font-weight: 500;
                text-transform: capitalize;
            }
            .endpoint-details {
                margin-bottom: 1.5rem;
            }
            .detail-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 0.5rem;
            }
            .detail-item .label {
                color: var(--text-secondary);
                font-size: 0.875rem;
            }
            .detail-item .value {
                font-weight: 500;
                font-size: 0.875rem;
            }
            .endpoint-actions {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
            }
        `;
        
        if (!document.querySelector('#endpoint-styles')) {
            style.id = 'endpoint-styles';
            document.head.appendChild(style);
        }
    }

    showAddEndpointModal() {
        const modal = document.getElementById('addEndpointModal');
        if (modal) {
            // Reset form
            document.getElementById('addEndpointForm').reset();
            document.getElementById('authGroup').style.display = 'none';
            
            modal.classList.add('active');
        }
    }

    handleEndpointTypeChange(event) {
        const type = event.target.value;
        const authGroup = document.getElementById('authGroup');
        
        if (type === 'web_chat') {
            authGroup.style.display = 'block';
        } else {
            authGroup.style.display = 'none';
        }
    }

    async handleAddEndpoint(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const endpointData = {
            name: formData.get('endpointName'),
            type: formData.get('endpointType'),
            url: formData.get('endpointUrl'),
            auth_email: formData.get('authEmail'),
            auth_password: formData.get('authPassword'),
            max_parallel: parseInt(formData.get('maxParallel')),
            save_cookies: formData.get('saveCookies') === 'on',
            unique_fingerprint: formData.get('uniqueFingerprint') === 'on',
            use_proxy: formData.get('useProxy') === 'on'
        };

        try {
            // Generate YAML configuration
            const yamlConfig = this.generateYAMLFromForm(endpointData);
            
            // Validate and save configuration
            const response = await fetch('/api/config/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    yaml_content: yamlConfig
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to save endpoint: ${response.status}`);
            }

            const result = await response.json();
            
            // Close modal and refresh
            document.getElementById('addEndpointModal').classList.remove('active');
            this.showToast('success', `Endpoint '${endpointData.name}' added successfully`);
            this.loadEndpoints();
            this.addActivity(`Added endpoint: ${endpointData.name}`, 'success');

        } catch (error) {
            console.error('Failed to add endpoint:', error);
            this.showToast('error', 'Failed to add endpoint');
        }
    }

    generateYAMLFromForm(data) {
        return `name: ${data.name}
URL: ${data.url}
${data.auth_email ? `authemail: '${data.auth_email}'` : ''}
${data.auth_password ? `authpassword: '${data.auth_password}'` : ''}
maxautoscaleparallel: '${data.max_parallel}'
savecookiesforfutureuse: '${data.save_cookies ? 'yes' : 'no'}'
createuniquefingerprintsandboxdeploymentsnapshot: ${data.unique_fingerprint}
useproxy: ${data.use_proxy}`;
    }

    async toggleEndpoint(endpointName) {
        const endpoint = this.endpoints.get(endpointName);
        if (!endpoint) return;

        const newStatus = endpoint.status === 'online' ? 'offline' : 'online';
        
        try {
            // TODO: Implement actual endpoint start/stop logic
            endpoint.status = newStatus;
            this.endpoints.set(endpointName, endpoint);
            
            this.updateEndpointsDisplay();
            this.showToast('success', `Endpoint '${endpointName}' ${newStatus === 'online' ? 'started' : 'stopped'}`);
            this.addActivity(`${newStatus === 'online' ? 'Started' : 'Stopped'} endpoint: ${endpointName}`, 'info');
            
        } catch (error) {
            console.error('Failed to toggle endpoint:', error);
            this.showToast('error', 'Failed to toggle endpoint');
        }
    }

    async testEndpoint(endpointName) {
        const endpoint = this.endpoints.get(endpointName);
        if (!endpoint) return;

        try {
            this.showToast('info', `Testing endpoint '${endpointName}'...`);
            
            // TODO: Implement actual endpoint testing
            await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate test
            
            this.showToast('success', `Endpoint '${endpointName}' test completed`);
            this.addActivity(`Tested endpoint: ${endpointName}`, 'info');
            
        } catch (error) {
            console.error('Failed to test endpoint:', error);
            this.showToast('error', 'Endpoint test failed');
        }
    }

    editEndpoint(endpointName) {
        // TODO: Implement endpoint editing
        this.showToast('info', `Edit functionality for '${endpointName}' coming soon`);
    }

    async deleteEndpoint(endpointName) {
        if (!confirm(`Are you sure you want to delete endpoint '${endpointName}'?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/config/config/${endpointName}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Failed to delete endpoint: ${response.status}`);
            }

            this.endpoints.delete(endpointName);
            this.updateEndpointsDisplay();
            this.showToast('success', `Endpoint '${endpointName}' deleted`);
            this.addActivity(`Deleted endpoint: ${endpointName}`, 'warning');

        } catch (error) {
            console.error('Failed to delete endpoint:', error);
            this.showToast('error', 'Failed to delete endpoint');
        }
    }

    updateDashboardStats(stats = null) {
        if (!stats) {
            const endpoints = Array.from(this.endpoints.values());
            stats = {
                activeEndpoints: endpoints.filter(e => e.status === 'online').length,
                avgResponseTime: this.calculateAvgResponseTime(endpoints),
                successRate: this.calculateSuccessRate(endpoints),
                totalRequests: endpoints.reduce((sum, e) => sum + e.requests, 0)
            };
        }

        document.getElementById('activeEndpoints').textContent = stats.activeEndpoints;
        document.getElementById('avgResponseTime').textContent = stats.avgResponseTime;
        document.getElementById('successRate').textContent = stats.successRate;
        document.getElementById('totalRequests').textContent = stats.totalRequests;

        // Update endpoint status list
        this.updateEndpointStatusList();
    }

    calculateAvgResponseTime(endpoints) {
        const validTimes = endpoints
            .filter(e => e.lastResponse)
            .map(e => e.lastResponse);
        
        if (validTimes.length === 0) return '0ms';
        
        const avg = validTimes.reduce((sum, time) => sum + time, 0) / validTimes.length;
        return `${Math.round(avg)}ms`;
    }

    calculateSuccessRate(endpoints) {
        const totalRequests = endpoints.reduce((sum, e) => sum + e.requests, 0);
        const totalErrors = endpoints.reduce((sum, e) => sum + e.errors, 0);
        
        if (totalRequests === 0) return '0%';
        
        const successRate = ((totalRequests - totalErrors) / totalRequests) * 100;
        return `${Math.round(successRate)}%`;
    }

    updateEndpointStatusList() {
        const list = document.getElementById('endpointStatusList');
        if (!list) return;

        if (this.endpoints.size === 0) {
            list.innerHTML = `
                <div class="status-item">
                    <span class="status-indicator offline"></span>
                    <span>No endpoints configured</span>
                </div>
            `;
            return;
        }

        list.innerHTML = Array.from(this.endpoints.values()).map(endpoint => `
            <div class="status-item">
                <span class="status-indicator ${endpoint.status}"></span>
                <span>${endpoint.name}</span>
                <span class="status-details">${endpoint.type}</span>
            </div>
        `).join('');
    }

    addActivity(message, type = 'info') {
        const list = document.getElementById('activityList');
        if (!list) return;

        const activity = document.createElement('div');
        activity.className = 'activity-item';
        activity.innerHTML = `
            <i class="fas ${this.getActivityIcon(type)}"></i>
            <span>${message}</span>
            <time>Just now</time>
        `;

        // Add to top of list
        list.insertBefore(activity, list.firstChild);

        // Keep only last 10 activities
        while (list.children.length > 10) {
            list.removeChild(list.lastChild);
        }
    }

    getActivityIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'warning': return 'fa-exclamation-triangle';
            case 'error': return 'fa-exclamation-circle';
            default: return 'fa-info-circle';
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;

        this.connectionStatus = status;
        statusElement.className = `connection-status ${status === 'connected' ? '' : 'disconnected'}`;
        statusElement.innerHTML = `
            <i class="fas fa-circle"></i>
            <span>${status === 'connected' ? 'Connected' : 'Disconnected'}</span>
        `;
    }

    refreshDashboard() {
        this.updateDashboardStats();
    }

    refreshEndpoints() {
        this.loadEndpoints();
    }

    refreshMonitoring() {
        // TODO: Implement monitoring refresh
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/config/templates');
            if (!response.ok) {
                throw new Error(`Failed to load templates: ${response.status}`);
            }

            const data = await response.json();
            this.displayTemplates(data.templates);

        } catch (error) {
            console.error('Failed to load templates:', error);
            this.showToast('error', 'Failed to load templates');
        }
    }

    displayTemplates(templates) {
        const grid = document.getElementById('templatesGrid');
        if (!grid) return;

        grid.innerHTML = Object.entries(templates).map(([key, template]) => `
            <div class="template-card">
                <div class="template-header">
                    <h3>${template.name}</h3>
                    <span class="template-type">${template.provider_type}</span>
                </div>
                <p class="template-description">${template.description}</p>
                <div class="template-actions">
                    <button class="btn btn-primary btn-sm" onclick="dashboard.useTemplate('${key}')">
                        <i class="fas fa-plus"></i> Use Template
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="dashboard.previewTemplate('${key}')">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                </div>
            </div>
        `).join('');
    }

    useTemplate(templateKey) {
        // Switch to YAML editor and load template
        this.switchTab('yaml-editor');
        if (window.yamlEditor) {
            window.yamlEditor.loadTemplate(templateKey);
        }
    }

    previewTemplate(templateKey) {
        // TODO: Implement template preview
        this.showToast('info', 'Template preview coming soon');
    }

    showSettings() {
        // TODO: Implement settings modal
        this.showToast('info', 'Settings panel coming soon');
    }

    startPeriodicUpdates() {
        // Update dashboard every 30 seconds
        setInterval(() => {
            if (this.activeTab === 'dashboard') {
                this.refreshDashboard();
            }
        }, 30000);

        // Update connection status every 10 seconds
        setInterval(() => {
            this.checkConnectionStatus();
        }, 10000);
    }

    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/health', { method: 'HEAD' });
            const status = response.ok ? 'connected' : 'disconnected';
            this.updateConnectionStatus(status);
        } catch (error) {
            this.updateConnectionStatus('disconnected');
        }
    }

    showToast(type, message) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas ${this.getToastIcon(type)}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    getToastIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
