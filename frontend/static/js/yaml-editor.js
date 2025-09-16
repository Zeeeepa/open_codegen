/**
 * YAML Editor with AI-Assisted Validation
 * Integrates with Codegen API for intelligent configuration validation
 */

class YAMLEditor {
    constructor() {
        this.editor = null;
        this.currentConfig = null;
        this.validationResults = null;
        this.templates = new Map();
        
        this.init();
        this.loadTemplates();
    }

    init() {
        // Initialize CodeMirror editor
        const textarea = document.getElementById('yamlEditor');
        if (textarea) {
            this.editor = CodeMirror.fromTextArea(textarea, {
                mode: 'yaml',
                theme: 'monokai',
                lineNumbers: true,
                lineWrapping: true,
                indentUnit: 2,
                tabSize: 2,
                autoCloseBrackets: true,
                matchBrackets: true,
                foldGutter: true,
                gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
                extraKeys: {
                    'Ctrl-Space': 'autocomplete',
                    'Ctrl-S': () => this.saveConfiguration(),
                    'Ctrl-Enter': () => this.validateWithAI()
                }
            });

            // Auto-resize editor
            this.editor.setSize(null, '100%');
            
            // Add change listener for real-time validation
            this.editor.on('change', () => {
                this.clearValidationStatus();
                this.debounceValidation();
            });
        }

        this.bindEvents();
        this.loadDefaultTemplate();
    }

    bindEvents() {
        // Validation button
        const validateBtn = document.getElementById('validateYamlBtn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => this.validateWithAI());
        }

        // Save configuration button
        const saveBtn = document.getElementById('saveConfigBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveConfiguration());
        }

        // Load template button
        const loadTemplateBtn = document.getElementById('loadTemplateBtn');
        if (loadTemplateBtn) {
            loadTemplateBtn.addEventListener('click', () => this.showTemplateSelector());
        }

        // File upload
        const uploadBtn = document.getElementById('uploadYamlBtn');
        const fileInput = document.getElementById('yamlFileInput');
        
        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // Download button
        const downloadBtn = document.getElementById('downloadYamlBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadConfiguration());
        }
    }

    loadTemplates() {
        // Load built-in templates
        this.templates.set('z.ai', {
            name: 'Z.ai Chat Interface',
            description: 'Template for Z.ai web chat integration',
            content: `name: ZaiIntegration
URL: chat.z.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: yes
useproxy: no
custom_selectors:
  text_input: 'textarea[placeholder*="message"]'
  send_button: 'button[type="submit"]'
  response_area: '.message-content'
  new_conversation: '.new-chat'`
        });

        this.templates.set('mistral', {
            name: 'Mistral AI Chat',
            description: 'Template for Mistral AI web chat integration',
            content: `name: MistralIntegration
URL: chat.mistral.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '3'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: yes
useproxy: no
custom_selectors:
  text_input: 'textarea'
  send_button: '.send-btn'
  response_area: '.chat-content'
  new_conversation: '.new-chat'`
        });

        this.templates.set('deepseek', {
            name: 'DeepSeek Chat',
            description: 'Template for DeepSeek web chat integration',
            content: `name: DeepSeekIntegration
URL: chat.deepseek.com
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: yes
useproxy: no
custom_selectors:
  text_input: 'textarea[placeholder*="Ask"]'
  send_button: 'button.send-button'
  response_area: '.ai-response'
  new_conversation: '.new-conversation'`
        });

        this.templates.set('claude', {
            name: 'Claude Chat',
            description: 'Template for Claude/Anthropic web chat integration',
            content: `name: ClaudeIntegration
URL: claude.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '5'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: yes
useproxy: no
custom_selectors:
  text_input: 'textarea[placeholder*="Talk"]'
  send_button: 'button[aria-label*="Send"]'
  response_area: '.claude-response'
  new_conversation: 'button:contains("New conversation")'`
        });

        this.templates.set('rest_api', {
            name: 'REST API Endpoint',
            description: 'Template for REST API integration',
            content: `name: RestAPIIntegration
URL: https://api.example.com
api_key: 'your-api-key-here'
maxautoscaleparallel: '10'
savecookiesforfutureuse: 'no'
createuniquefingerprintsandboxdeploymentsnapshot: no
useproxy: no
endpoint_config:
  chat_completions: '/v1/chat/completions'
  models: '/v1/models'
  headers:
    Authorization: 'Bearer {api_key}'
    Content-Type: 'application/json'`
        });
    }

    loadDefaultTemplate() {
        if (this.editor && !this.editor.getValue().trim()) {
            this.editor.setValue(this.templates.get('z.ai').content);
        }
    }

    showTemplateSelector() {
        const modal = this.createTemplateModal();
        document.body.appendChild(modal);
        modal.classList.add('active');
    }

    createTemplateModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Select Configuration Template</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="template-grid">
                        ${Array.from(this.templates.entries()).map(([key, template]) => `
                            <div class="template-card" data-template="${key}">
                                <h4>${template.name}</h4>
                                <p>${template.description}</p>
                                <button class="btn btn-primary btn-sm" onclick="yamlEditor.loadTemplate('${key}'); this.closest('.modal').remove();">
                                    Use Template
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // Add template card styles
        const style = document.createElement('style');
        style.textContent = `
            .template-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }
            .template-card {
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 1rem;
                text-align: center;
            }
            .template-card h4 {
                margin-bottom: 0.5rem;
                color: var(--text-primary);
            }
            .template-card p {
                color: var(--text-secondary);
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }
        `;
        modal.appendChild(style);

        return modal;
    }

    loadTemplate(templateKey) {
        const template = this.templates.get(templateKey);
        if (template && this.editor) {
            this.editor.setValue(template.content);
            this.showToast('success', `Loaded ${template.name} template`);
            this.clearValidationStatus();
        }
    }

    async validateWithAI() {
        const yamlContent = this.editor.getValue();
        
        if (!yamlContent.trim()) {
            this.showToast('warning', 'Please enter YAML configuration to validate');
            return;
        }

        this.setValidationStatus('pending', 'Validating with AI...');
        this.showLoading(true);

        try {
            const response = await fetch('/api/config/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    yaml_content: yamlContent
                })
            });

            if (!response.ok) {
                throw new Error(`Validation failed: ${response.status}`);
            }

            const result = await response.json();
            this.displayValidationResults(result);
            
        } catch (error) {
            console.error('Validation error:', error);
            this.setValidationStatus('invalid', 'Validation failed');
            this.displayValidationError(error.message);
            this.showToast('error', 'AI validation failed');
        } finally {
            this.showLoading(false);
        }
    }

    displayValidationResults(result) {
        const { valid, config, abstraction, issues, suggestions } = result;
        
        if (valid) {
            this.setValidationStatus('valid', 'Configuration is valid');
            this.showToast('success', 'Configuration validated successfully');
        } else {
            this.setValidationStatus('invalid', 'Configuration has issues');
            this.showToast('warning', 'Configuration needs attention');
        }

        const content = document.getElementById('validationContent');
        if (content) {
            content.innerHTML = this.generateValidationHTML(result);
        }

        this.validationResults = result;
    }

    generateValidationHTML(result) {
        const { valid, config, abstraction, issues, suggestions } = result;
        
        let html = `
            <div class="validation-results">
                <div class="validation-summary">
                    <h4>Validation Summary</h4>
                    <div class="summary-item">
                        <strong>Status:</strong> 
                        <span class="status-badge ${valid ? 'valid' : 'invalid'}">
                            ${valid ? 'Valid' : 'Invalid'}
                        </span>
                    </div>
        `;

        if (config) {
            html += `
                    <div class="summary-item">
                        <strong>Endpoint:</strong> ${config.name}
                    </div>
                    <div class="summary-item">
                        <strong>URL:</strong> ${config.url}
                    </div>
                    <div class="summary-item">
                        <strong>Max Parallel:</strong> ${config.max_autoscale_parallel}
                    </div>
            `;
        }

        html += `</div>`;

        if (issues && issues.length > 0) {
            html += `
                <div class="validation-issues">
                    <h4>Issues Found</h4>
                    <ul class="issue-list">
                        ${issues.map(issue => `<li class="issue-item">${issue}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (suggestions) {
            if (suggestions.selectors) {
                html += `
                    <div class="validation-suggestions">
                        <h4>AI-Suggested Selectors</h4>
                        <div class="selector-suggestions">
                            ${Object.entries(suggestions.selectors).map(([key, value]) => `
                                <div class="selector-item">
                                    <strong>${key}:</strong>
                                    <code>${value}</code>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            if (suggestions.optimizations && suggestions.optimizations.length > 0) {
                html += `
                    <div class="validation-optimizations">
                        <h4>Optimization Suggestions</h4>
                        <ul class="optimization-list">
                            ${suggestions.optimizations.map(opt => `<li>${opt}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            if (suggestions.security_recommendations && suggestions.security_recommendations.length > 0) {
                html += `
                    <div class="validation-security">
                        <h4>Security Recommendations</h4>
                        <ul class="security-list">
                            ${suggestions.security_recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
        }

        if (abstraction) {
            html += `
                <div class="interface-abstraction">
                    <h4>Interface Elements Detected</h4>
                    <div class="element-grid">
                        ${Object.entries(abstraction.elements).map(([key, element]) => `
                            <div class="element-card">
                                <strong>${key.replace('_', ' ').toUpperCase()}</strong>
                                <code>${element.selector}</code>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        html += `</div>`;

        // Add validation result styles
        const style = document.createElement('style');
        style.textContent = `
            .validation-results { font-size: 0.875rem; }
            .validation-summary { margin-bottom: 1.5rem; }
            .summary-item { margin-bottom: 0.5rem; }
            .status-badge { 
                padding: 0.25rem 0.5rem; 
                border-radius: var(--radius-sm); 
                font-size: 0.75rem; 
                font-weight: 600;
            }
            .status-badge.valid { background: #dcfce7; color: #166534; }
            .status-badge.invalid { background: #fef2f2; color: #dc2626; }
            .issue-list, .optimization-list, .security-list { 
                margin: 0.5rem 0; 
                padding-left: 1.5rem; 
            }
            .issue-item { color: var(--error-color); margin-bottom: 0.25rem; }
            .selector-suggestions { margin: 0.5rem 0; }
            .selector-item { 
                margin-bottom: 0.5rem; 
                padding: 0.5rem; 
                background: var(--background-color); 
                border-radius: var(--radius-sm); 
            }
            .selector-item code { 
                background: var(--surface-color); 
                padding: 0.25rem 0.5rem; 
                border-radius: var(--radius-sm); 
                font-size: 0.8125rem; 
            }
            .element-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 0.75rem; 
                margin-top: 0.5rem; 
            }
            .element-card { 
                padding: 0.75rem; 
                border: 1px solid var(--border-color); 
                border-radius: var(--radius-md); 
                text-align: center; 
            }
            .element-card code { 
                display: block; 
                margin-top: 0.5rem; 
                font-size: 0.75rem; 
                color: var(--text-secondary); 
            }
        `;
        
        if (!document.querySelector('#validation-styles')) {
            style.id = 'validation-styles';
            document.head.appendChild(style);
        }

        return html;
    }

    displayValidationError(error) {
        const content = document.getElementById('validationContent');
        if (content) {
            content.innerHTML = `
                <div class="validation-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>Validation Error</h4>
                    <p>${error}</p>
                    <button class="btn btn-primary btn-sm" onclick="yamlEditor.validateWithAI()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    async saveConfiguration() {
        const yamlContent = this.editor.getValue();
        
        if (!yamlContent.trim()) {
            this.showToast('warning', 'No configuration to save');
            return;
        }

        // If we have validation results, use them
        if (this.validationResults && this.validationResults.valid) {
            await this.saveValidatedConfiguration();
        } else {
            // Validate first, then save
            await this.validateWithAI();
            if (this.validationResults && this.validationResults.valid) {
                await this.saveValidatedConfiguration();
            } else {
                this.showToast('error', 'Please fix validation issues before saving');
            }
        }
    }

    async saveValidatedConfiguration() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/config/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    yaml_content: this.editor.getValue(),
                    validation_results: this.validationResults
                })
            });

            if (!response.ok) {
                throw new Error(`Save failed: ${response.status}`);
            }

            const result = await response.json();
            this.showToast('success', `Configuration saved: ${result.config_path}`);
            
            // Refresh endpoints list
            if (window.dashboard) {
                window.dashboard.refreshEndpoints();
            }
            
        } catch (error) {
            console.error('Save error:', error);
            this.showToast('error', 'Failed to save configuration');
        } finally {
            this.showLoading(false);
        }
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.match(/\.(yaml|yml)$/i)) {
            this.showToast('error', 'Please select a YAML file (.yaml or .yml)');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.editor.setValue(e.target.result);
            this.showToast('success', `Loaded ${file.name}`);
            this.clearValidationStatus();
        };
        reader.readAsText(file);
    }

    downloadConfiguration() {
        const yamlContent = this.editor.getValue();
        
        if (!yamlContent.trim()) {
            this.showToast('warning', 'No configuration to download');
            return;
        }

        // Extract name from YAML for filename
        let filename = 'config.yaml';
        try {
            const lines = yamlContent.split('\n');
            const nameLine = lines.find(line => line.trim().startsWith('name:'));
            if (nameLine) {
                const name = nameLine.split(':')[1].trim().replace(/['"]/g, '');
                filename = `${name.toLowerCase().replace(/\s+/g, '_')}.yaml`;
            }
        } catch (e) {
            // Use default filename
        }

        const blob = new Blob([yamlContent], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showToast('success', `Downloaded ${filename}`);
    }

    setValidationStatus(status, message) {
        const statusElement = document.getElementById('validationStatus');
        if (statusElement) {
            statusElement.className = `validation-status ${status}`;
            statusElement.innerHTML = `
                <i class="fas ${this.getStatusIcon(status)}"></i>
                <span>${message}</span>
            `;
        }
    }

    clearValidationStatus() {
        this.setValidationStatus('', 'Not validated');
        const content = document.getElementById('validationContent');
        if (content) {
            content.innerHTML = `
                <div class="validation-placeholder">
                    <i class="fas fa-robot"></i>
                    <p>Click "Validate with AI" to get intelligent feedback on your configuration</p>
                </div>
            `;
        }
        this.validationResults = null;
    }

    getStatusIcon(status) {
        switch (status) {
            case 'valid': return 'fa-check-circle';
            case 'invalid': return 'fa-exclamation-circle';
            case 'pending': return 'fa-spinner fa-spin';
            default: return 'fa-question-circle';
        }
    }

    debounceValidation() {
        clearTimeout(this.validationTimeout);
        this.validationTimeout = setTimeout(() => {
            // Auto-validate after 2 seconds of inactivity
            // this.validateWithAI();
        }, 2000);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.toggle('active', show);
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

// Initialize YAML editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.yamlEditor = new YAMLEditor();
});
