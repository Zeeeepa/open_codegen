/**
 * Supabase Connection Component
 * Provides UI for connecting to Supabase database with validation and testing
 */

class SupabaseConnect {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.isConnected = false;
        this.connectionConfig = null;
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        this.checkConnectionStatus();
    }

    render() {
        this.container.innerHTML = `
            <div class="supabase-connect-container">
                <div class="supabase-header">
                    <h2>
                        <i class="icon-database"></i>
                        Connect Supabase Database
                    </h2>
                    <div class="connection-status" id="connection-status">
                        <span class="status-indicator" id="status-indicator"></span>
                        <span class="status-text" id="status-text">Not Connected</span>
                    </div>
                </div>

                <div class="supabase-form" id="supabase-form">
                    <div class="form-group">
                        <label for="supabase-url">
                            <i class="icon-link"></i>
                            Supabase Project URL
                        </label>
                        <input 
                            type="url" 
                            id="supabase-url" 
                            placeholder="https://your-project.supabase.co"
                            required
                        >
                        <small class="help-text">
                            Find this in your Supabase project settings under "API"
                        </small>
                    </div>

                    <div class="form-group">
                        <label for="supabase-key">
                            <i class="icon-key"></i>
                            Supabase API Key
                        </label>
                        <div class="input-with-toggle">
                            <input 
                                type="password" 
                                id="supabase-key" 
                                placeholder="Your anon or service_role key"
                                required
                            >
                            <button type="button" class="toggle-password" id="toggle-password">
                                <i class="icon-eye"></i>
                            </button>
                        </div>
                        <small class="help-text">
                            Use anon key for basic access or service_role key for full access
                        </small>
                    </div>

                    <div class="form-group">
                        <label for="table-prefix">
                            <i class="icon-table"></i>
                            Table Prefix
                        </label>
                        <input 
                            type="text" 
                            id="table-prefix" 
                            value="codegen_adapter"
                            placeholder="codegen_adapter"
                        >
                        <small class="help-text">
                            Prefix for database table names (optional)
                        </small>
                    </div>

                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="auto-create-tables" checked>
                            <span class="checkmark"></span>
                            Automatically create tables if they don't exist
                        </label>
                    </div>

                    <div class="form-actions">
                        <button type="button" class="btn btn-test" id="test-connection">
                            <i class="icon-test"></i>
                            Test Connection
                        </button>
                        <button type="button" class="btn btn-primary" id="connect-button">
                            <i class="icon-connect"></i>
                            Connect
                        </button>
                        <button type="button" class="btn btn-secondary" id="disconnect-button" style="display: none;">
                            <i class="icon-disconnect"></i>
                            Disconnect
                        </button>
                    </div>
                </div>

                <div class="connection-results" id="connection-results" style="display: none;">
                    <div class="results-header">
                        <h3>Connection Results</h3>
                    </div>
                    <div class="results-content" id="results-content">
                        <!-- Results will be populated here -->
                    </div>
                </div>

                <div class="database-info" id="database-info" style="display: none;">
                    <div class="info-header">
                        <h3>Database Information</h3>
                        <button type="button" class="btn btn-small" id="refresh-info">
                            <i class="icon-refresh"></i>
                            Refresh
                        </button>
                    </div>
                    <div class="info-content" id="info-content">
                        <!-- Database info will be populated here -->
                    </div>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Toggle password visibility
        document.getElementById('toggle-password').addEventListener('click', () => {
            this.togglePasswordVisibility();
        });

        // Test connection
        document.getElementById('test-connection').addEventListener('click', () => {
            this.testConnection();
        });

        // Connect
        document.getElementById('connect-button').addEventListener('click', () => {
            this.connect();
        });

        // Disconnect
        document.getElementById('disconnect-button').addEventListener('click', () => {
            this.disconnect();
        });

        // Refresh database info
        document.getElementById('refresh-info').addEventListener('click', () => {
            this.refreshDatabaseInfo();
        });

        // Form validation
        const inputs = this.container.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.validateForm();
            });
        });
    }

    togglePasswordVisibility() {
        const keyInput = document.getElementById('supabase-key');
        const toggleButton = document.getElementById('toggle-password');
        const icon = toggleButton.querySelector('i');

        if (keyInput.type === 'password') {
            keyInput.type = 'text';
            icon.className = 'icon-eye-off';
        } else {
            keyInput.type = 'password';
            icon.className = 'icon-eye';
        }
    }

    validateForm() {
        const url = document.getElementById('supabase-url').value.trim();
        const key = document.getElementById('supabase-key').value.trim();
        
        const isValid = url && key && this.isValidUrl(url);
        
        document.getElementById('test-connection').disabled = !isValid;
        document.getElementById('connect-button').disabled = !isValid;

        return isValid;
    }

    isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.hostname.includes('supabase.co') || url.hostname.includes('localhost');
        } catch (_) {
            return false;
        }
    }

    getFormData() {
        return {
            url: document.getElementById('supabase-url').value.trim(),
            key: document.getElementById('supabase-key').value.trim(),
            table_prefix: document.getElementById('table-prefix').value.trim() || 'codegen_adapter',
            auto_create_tables: document.getElementById('auto-create-tables').checked
        };
    }

    async testConnection() {
        if (!this.validateForm()) {
            this.showError('Please fill in all required fields with valid values.');
            return;
        }

        const testButton = document.getElementById('test-connection');
        const originalText = testButton.innerHTML;
        
        try {
            testButton.innerHTML = '<i class="icon-loading"></i> Testing...';
            testButton.disabled = true;

            const config = this.getFormData();
            const response = await fetch('/api/supabase/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();
            this.showConnectionResults(result, true);

        } catch (error) {
            this.showError(`Connection test failed: ${error.message}`);
        } finally {
            testButton.innerHTML = originalText;
            testButton.disabled = false;
        }
    }

    async connect() {
        if (!this.validateForm()) {
            this.showError('Please fill in all required fields with valid values.');
            return;
        }

        const connectButton = document.getElementById('connect-button');
        const originalText = connectButton.innerHTML;
        
        try {
            connectButton.innerHTML = '<i class="icon-loading"></i> Connecting...';
            connectButton.disabled = true;

            const config = this.getFormData();
            const response = await fetch('/api/supabase/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();
            
            if (result.success) {
                this.isConnected = true;
                this.connectionConfig = config;
                this.updateConnectionStatus(true, 'Connected');
                this.showConnectionResults(result, false);
                this.showDatabaseInfo();
                this.toggleFormVisibility(false);
                
                // Store connection config in localStorage (without sensitive key)
                const safeConfig = { ...config };
                delete safeConfig.key;
                localStorage.setItem('supabase_config', JSON.stringify(safeConfig));
                
                this.showSuccess('Successfully connected to Supabase!');
            } else {
                this.showError(`Connection failed: ${result.message}`);
                this.showConnectionResults(result, false);
            }

        } catch (error) {
            this.showError(`Connection failed: ${error.message}`);
        } finally {
            connectButton.innerHTML = originalText;
            connectButton.disabled = false;
        }
    }

    async disconnect() {
        try {
            this.isConnected = false;
            this.connectionConfig = null;
            this.updateConnectionStatus(false, 'Not Connected');
            this.toggleFormVisibility(true);
            
            // Clear stored config
            localStorage.removeItem('supabase_config');
            
            // Hide results and database info
            document.getElementById('connection-results').style.display = 'none';
            document.getElementById('database-info').style.display = 'none';
            
            this.showSuccess('Disconnected from Supabase.');
            
        } catch (error) {
            this.showError(`Disconnect failed: ${error.message}`);
        }
    }

    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/supabase/status');
            const status = await response.json();
            
            if (status.connected) {
                this.isConnected = true;
                this.updateConnectionStatus(true, 'Connected');
                this.toggleFormVisibility(false);
                this.showDatabaseInfo();
                
                // Load saved config if available
                const savedConfig = localStorage.getItem('supabase_config');
                if (savedConfig) {
                    const config = JSON.parse(savedConfig);
                    document.getElementById('supabase-url').value = config.url || '';
                    document.getElementById('table-prefix').value = config.table_prefix || 'codegen_adapter';
                    document.getElementById('auto-create-tables').checked = config.auto_create_tables !== false;
                }
            } else {
                this.updateConnectionStatus(false, status.message || 'Not Connected');
            }
        } catch (error) {
            console.error('Failed to check connection status:', error);
        }
    }

    async showDatabaseInfo() {
        try {
            const response = await fetch('/api/supabase/stats');
            const stats = await response.json();
            
            const infoContent = document.getElementById('info-content');
            infoContent.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_endpoints || 0}</div>
                        <div class="stat-label">Total Endpoints</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.active_sessions || 0}</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_messages || 0}</div>
                        <div class="stat-label">Total Messages</div>
                    </div>
                </div>
                
                <div class="tables-info">
                    <h4>Database Tables</h4>
                    <div class="tables-list" id="tables-list">
                        Loading tables...
                    </div>
                </div>
            `;
            
            document.getElementById('database-info').style.display = 'block';
            
            // Load tables info
            this.loadTablesInfo();
            
        } catch (error) {
            console.error('Failed to load database info:', error);
        }
    }

    async loadTablesInfo() {
        try {
            const response = await fetch('/api/supabase/tables');
            const tablesData = await response.json();
            
            const tablesList = document.getElementById('tables-list');
            if (tablesData.tables && tablesData.tables.length > 0) {
                tablesList.innerHTML = tablesData.tables.map(table => 
                    `<span class="table-tag">${table}</span>`
                ).join('');
            } else {
                tablesList.innerHTML = '<span class="no-tables">No tables found</span>';
            }
        } catch (error) {
            document.getElementById('tables-list').innerHTML = '<span class="error">Failed to load tables</span>';
        }
    }

    async refreshDatabaseInfo() {
        const refreshButton = document.getElementById('refresh-info');
        const originalText = refreshButton.innerHTML;
        
        try {
            refreshButton.innerHTML = '<i class="icon-loading"></i>';
            refreshButton.disabled = true;
            
            await this.showDatabaseInfo();
            
        } catch (error) {
            this.showError('Failed to refresh database info');
        } finally {
            refreshButton.innerHTML = originalText;
            refreshButton.disabled = false;
        }
    }

    showConnectionResults(result, isTest) {
        const resultsContainer = document.getElementById('connection-results');
        const resultsContent = document.getElementById('results-content');
        
        const statusClass = result.success ? 'success' : 'error';
        const statusIcon = result.success ? 'icon-check' : 'icon-x';
        
        let html = `
            <div class="result-item ${statusClass}">
                <div class="result-header">
                    <i class="${statusIcon}"></i>
                    <span>${isTest ? 'Connection Test' : 'Connection'} ${result.success ? 'Successful' : 'Failed'}</span>
                </div>
                <div class="result-details">
                    <p>${result.message}</p>
                    ${result.connection_time ? `<p><strong>Connection Time:</strong> ${result.connection_time.toFixed(2)}s</p>` : ''}
                </div>
            </div>
        `;
        
        if (result.tables_found && result.tables_found.length > 0) {
            html += `
                <div class="result-item info">
                    <div class="result-header">
                        <i class="icon-info"></i>
                        <span>Existing Tables Found</span>
                    </div>
                    <div class="result-details">
                        <div class="tables-found">
                            ${result.tables_found.map(table => `<span class="table-tag">${table}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        if (result.tables_created && result.tables_created.length > 0) {
            html += `
                <div class="result-item success">
                    <div class="result-header">
                        <i class="icon-plus"></i>
                        <span>Tables Created</span>
                    </div>
                    <div class="result-details">
                        <div class="tables-created">
                            ${result.tables_created.map(table => `<span class="table-tag">${table}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        if (result.error_details) {
            html += `
                <div class="result-item error">
                    <div class="result-header">
                        <i class="icon-alert"></i>
                        <span>Error Details</span>
                    </div>
                    <div class="result-details">
                        <pre class="error-details">${result.error_details}</pre>
                    </div>
                </div>
            `;
        }
        
        resultsContent.innerHTML = html;
        resultsContainer.style.display = 'block';
    }

    updateConnectionStatus(connected, message) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        statusIndicator.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
        statusText.textContent = message;
    }

    toggleFormVisibility(show) {
        const form = document.getElementById('supabase-form');
        const connectButton = document.getElementById('connect-button');
        const disconnectButton = document.getElementById('disconnect-button');
        
        if (show) {
            form.style.display = 'block';
            connectButton.style.display = 'inline-block';
            disconnectButton.style.display = 'none';
        } else {
            form.style.display = 'none';
            connectButton.style.display = 'none';
            disconnectButton.style.display = 'inline-block';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="icon-${type === 'success' ? 'check' : 'alert'}"></i>
            <span>${message}</span>
            <button type="button" class="close-notification">&times;</button>
        `;
        
        // Add to container
        this.container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Add close button functionality
        notification.querySelector('.close-notification').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SupabaseConnect;
}
