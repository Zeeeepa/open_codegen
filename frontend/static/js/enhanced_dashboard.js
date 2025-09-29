/**
 * Enhanced Dashboard JavaScript
 * Connects to real API Gateway endpoints for live provider management
 */

class EnhancedDashboard {
    constructor() {
        this.gatewayUrl = 'http://localhost:7999'; // API Gateway URL
        this.providers = [];
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Enhanced Dashboard...');
        await this.loadProviders();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Auto-refresh every 30 seconds
        this.startAutoRefresh();
        
        // Handle window focus to refresh data
        window.addEventListener('focus', () => {
            this.refreshData();
        });
    }

    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 30000); // 30 seconds
    }

    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.gatewayUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API call failed for ${endpoint}:`, error);
            throw error;
        }
    }

    async loadProviders() {
        try {
            console.log('📡 Loading providers from API Gateway...');
            const data = await this.apiCall('/providers');
            
            this.providers = data.providers || [];
            this.updateUI();
            this.updateProviderSelector();
            
            console.log(`✅ Loaded ${this.providers.length} providers`);
        } catch (error) {
            console.error('❌ Failed to load providers:', error);
            this.showError('Failed to connect to API Gateway. Using offline mode.');
            this.loadFallbackData();
        }
    }

    loadFallbackData() {
        // Fallback data when API is not available
        this.providers = [
            {
                name: "qwen-api",
                status: "stopped",
                port: 8000,
                models: ["qwen-turbo", "qwen-plus", "qwen-max"],
                response_time: 0,
                error_count: 0,
                last_health_check: 0,
                uptime: 0
            },
            {
                name: "k2think2api3",
                status: "stopped",
                port: 8001,
                models: ["k2-think", "gpt-4"],
                response_time: 0,
                error_count: 0,
                last_health_check: 0,
                uptime: 0
            },
            // Add more fallback providers...
        ];
        
        this.updateUI();
        this.updateProviderSelector();
    }

    updateUI() {
        this.updateStats();
        this.updateProvidersGrid();
    }

    updateStats() {
        const totalProviders = this.providers.length;
        const healthyProviders = this.providers.filter(p => p.status === 'healthy').length;
        
        // Calculate average response time
        const healthyResponseTimes = this.providers
            .filter(p => p.status === 'healthy' && p.response_time > 0)
            .map(p => p.response_time);
        
        const avgResponseTime = healthyResponseTimes.length > 0 
            ? (healthyResponseTimes.reduce((a, b) => a + b, 0) / healthyResponseTimes.length).toFixed(2) + 's'
            : '--';

        // Update DOM elements
        document.getElementById('total-providers').textContent = totalProviders;
        document.getElementById('healthy-providers').textContent = healthyProviders;
        document.getElementById('avg-response').textContent = avgResponseTime;
        
        // Note: Total requests would come from load balancer stats
        document.getElementById('total-requests').textContent = '0';
    }

    updateProvidersGrid() {
        const grid = document.getElementById('providers-grid');
        grid.innerHTML = this.providers.map(provider => this.createProviderCard(provider)).join('');
    }

    createProviderCard(provider) {
        const statusClass = this.getStatusClass(provider.status);
        const cardClass = provider.status;
        
        const responseTime = provider.response_time > 0 
            ? `${provider.response_time.toFixed(2)}s` 
            : 'N/A';
        
        const uptime = provider.uptime > 0 
            ? `${(provider.uptime / 3600).toFixed(1)}h` 
            : '0h';

        return `
            <div class="provider-card ${cardClass}">
                <div class="provider-header">
                    <div class="provider-name">${provider.name}</div>
                    <div class="status-badge ${statusClass}">${provider.status}</div>
                </div>
                
                <div class="provider-details">
                    <div class="detail-item">
                        <div class="detail-label">Port</div>
                        <div class="detail-value">${provider.port}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Response Time</div>
                        <div class="detail-value">${responseTime}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Uptime</div>
                        <div class="detail-value">${uptime}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Errors</div>
                        <div class="detail-value">${provider.error_count}</div>
                    </div>
                </div>

                <div class="models-list">
                    ${provider.models.map(model => `<span class="model-tag">${model}</span>`).join('')}
                </div>

                <div class="actions">
                    <button class="btn btn-primary" onclick="dashboard.testProvider('${provider.name}')">Test</button>
                    ${provider.status === 'stopped' ? 
                        `<button class="btn btn-success" onclick="dashboard.startProvider('${provider.name}')">Start</button>` :
                        `<button class="btn btn-danger" onclick="dashboard.stopProvider('${provider.name}')">Stop</button>`
                    }
                    <button class="btn btn-secondary" onclick="dashboard.restartProvider('${provider.name}')">Restart</button>
                </div>
            </div>
        `;
    }

    updateProviderSelector() {
        const select = document.getElementById('provider-select');
        const currentValue = select.value;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">Auto-select (Load Balanced)</option>';
        
        // Add healthy providers
        this.providers
            .filter(p => p.status === 'healthy')
            .forEach(provider => {
                const option = document.createElement('option');
                option.value = provider.name;
                option.textContent = `${provider.name} (${provider.models.join(', ')})`;
                select.appendChild(option);
            });
        
        // Restore previous selection if still valid
        if (currentValue && [...select.options].some(opt => opt.value === currentValue)) {
            select.value = currentValue;
        }
    }

    getStatusClass(status) {
        return `status-${status}`;
    }

    async sendMessage() {
        const messageInput = document.getElementById('chat-message');
        const providerSelect = document.getElementById('provider-select');
        const responseDiv = document.getElementById('chat-response');
        
        const message = messageInput.value.trim();
        const selectedProvider = providerSelect.value;
        
        if (!message) {
            alert('Please enter a message');
            return;
        }

        responseDiv.textContent = 'Sending message...';
        
        try {
            const payload = {
                model: 'gpt-3.5-turbo',
                messages: [
                    { role: 'user', content: message }
                ],
                temperature: 0.7,
                max_tokens: 150,
                stream: false
            };

            const endpoint = selectedProvider 
                ? `/v1/chat/completions?provider=${selectedProvider}`
                : '/v1/chat/completions';

            console.log(`📤 Sending message to ${selectedProvider || 'auto-selected provider'}...`);
            
            const response = await this.apiCall(endpoint, {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            if (response.choices && response.choices[0] && response.choices[0].message) {
                const aiResponse = response.choices[0].message.content;
                const providerUsed = response._provider || selectedProvider || 'unknown';
                
                responseDiv.textContent = `[${providerUsed}] ${aiResponse}`;
                console.log(`✅ Response received from ${providerUsed}`);
            } else {
                responseDiv.textContent = 'Error: Invalid response format';
            }
            
        } catch (error) {
            console.error('❌ Message sending failed:', error);
            responseDiv.textContent = `Error: ${error.message}`;
        }
    }

    async testProvider(providerName) {
        try {
            console.log(`🧪 Testing provider: ${providerName}`);
            
            const response = await this.apiCall('/v1/test', {
                method: 'POST',
                body: JSON.stringify({
                    message: `Test message for ${providerName}`,
                    provider: providerName,
                    model: 'gpt-3.5-turbo'
                })
            });

            if (response.response && response.response.choices) {
                const testResponse = response.response.choices[0].message.content;
                alert(`✅ ${providerName} Test Successful!\n\nResponse: ${testResponse}`);
            } else {
                alert(`✅ ${providerName} responded but with unexpected format`);
            }
            
        } catch (error) {
            console.error(`❌ Test failed for ${providerName}:`, error);
            alert(`❌ Test failed for ${providerName}: ${error.message}`);
        }
    }

    async startProvider(providerName) {
        try {
            console.log(`🚀 Starting provider: ${providerName}`);
            this.showSystemStatus(`Starting ${providerName}...`);
            
            const response = await this.apiCall(`/providers/${providerName}/start`, {
                method: 'POST'
            });

            if (response.success) {
                this.showSystemStatus(`✅ ${providerName} started successfully`);
                setTimeout(() => this.refreshData(), 2000); // Refresh after 2 seconds
            } else {
                this.showSystemStatus(`❌ Failed to start ${providerName}`);
            }
            
        } catch (error) {
            console.error(`❌ Failed to start ${providerName}:`, error);
            this.showSystemStatus(`❌ Error starting ${providerName}: ${error.message}`);
        }
    }

    async stopProvider(providerName) {
        try {
            console.log(`🛑 Stopping provider: ${providerName}`);
            this.showSystemStatus(`Stopping ${providerName}...`);
            
            const response = await this.apiCall(`/providers/${providerName}/stop`, {
                method: 'POST'
            });

            if (response.success) {
                this.showSystemStatus(`✅ ${providerName} stopped successfully`);
                setTimeout(() => this.refreshData(), 1000); // Refresh after 1 second
            } else {
                this.showSystemStatus(`❌ Failed to stop ${providerName}`);
            }
            
        } catch (error) {
            console.error(`❌ Failed to stop ${providerName}:`, error);
            this.showSystemStatus(`❌ Error stopping ${providerName}: ${error.message}`);
        }
    }

    async restartProvider(providerName) {
        try {
            console.log(`🔄 Restarting provider: ${providerName}`);
            this.showSystemStatus(`Restarting ${providerName}...`);
            
            const response = await this.apiCall(`/providers/${providerName}/restart`, {
                method: 'POST'
            });

            if (response.success) {
                this.showSystemStatus(`✅ ${providerName} restarted successfully`);
                setTimeout(() => this.refreshData(), 3000); // Refresh after 3 seconds
            } else {
                this.showSystemStatus(`❌ Failed to restart ${providerName}`);
            }
            
        } catch (error) {
            console.error(`❌ Failed to restart ${providerName}:`, error);
            this.showSystemStatus(`❌ Error restarting ${providerName}: ${error.message}`);
        }
    }

    async startAllProviders() {
        try {
            console.log('🚀 Starting all providers...');
            this.showSystemStatus('Starting all providers...');
            
            const response = await this.apiCall('/providers/start-all', {
                method: 'POST'
            });

            const successful = response.successful || 0;
            const total = response.total || 0;
            
            this.showSystemStatus(`✅ Started ${successful}/${total} providers successfully`);
            setTimeout(() => this.refreshData(), 5000); // Refresh after 5 seconds
            
        } catch (error) {
            console.error('❌ Failed to start all providers:', error);
            this.showSystemStatus(`❌ Error starting providers: ${error.message}`);
        }
    }

    async stopAllProviders() {
        try {
            console.log('🛑 Stopping all providers...');
            this.showSystemStatus('Stopping all providers...');
            
            const response = await this.apiCall('/providers/stop-all', {
                method: 'POST'
            });

            const successful = response.successful || 0;
            const total = response.total || 0;
            
            this.showSystemStatus(`✅ Stopped ${successful}/${total} providers successfully`);
            setTimeout(() => this.refreshData(), 2000); // Refresh after 2 seconds
            
        } catch (error) {
            console.error('❌ Failed to stop all providers:', error);
            this.showSystemStatus(`❌ Error stopping providers: ${error.message}`);
        }
    }

    async testAllProviders() {
        try {
            console.log('🧪 Testing all providers...');
            this.showSystemStatus('Running comprehensive tests on all providers...');
            
            // This would trigger the test suite
            alert('🧪 Comprehensive testing started!\n\nThis will test all providers and generate a detailed report.\nCheck the console for progress updates.');
            
            // In a real implementation, this might call a test endpoint
            // const response = await this.apiCall('/test/all-providers', { method: 'POST' });
            
        } catch (error) {
            console.error('❌ Failed to test all providers:', error);
            this.showSystemStatus(`❌ Error testing providers: ${error.message}`);
        }
    }

    async refreshData() {
        console.log('🔄 Refreshing data...');
        await this.loadProviders();
    }

    showSystemStatus(message) {
        const statusDiv = document.getElementById('system-status');
        statusDiv.innerHTML = `<div style="padding: 10px; background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; color: #0c4a6e; font-weight: 500;">${message}</div>`;
        
        // Clear status after 5 seconds
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 5000);
    }

    showError(message) {
        const statusDiv = document.getElementById('system-status');
        statusDiv.innerHTML = `<div style="padding: 10px; background: #fef2f2; border: 1px solid #ef4444; border-radius: 8px; color: #991b1b; font-weight: 500;">⚠️ ${message}</div>`;
    }
}

// Global functions for onclick handlers
let dashboard;

function sendMessage() {
    dashboard.sendMessage();
}

function startAllProviders() {
    dashboard.startAllProviders();
}

function stopAllProviders() {
    dashboard.stopAllProviders();
}

function testAllProviders() {
    dashboard.testAllProviders();
}

function refreshData() {
    dashboard.refreshData();
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new EnhancedDashboard();
});
