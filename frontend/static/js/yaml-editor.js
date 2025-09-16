/**
 * YAML Editor with AI-Assisted Validation
 * Handles YAML configuration editing and validation
 */

class YAMLEditor {
    constructor() {
        this.editor = null;
        this.currentTemplate = null;
        this.validationResults = [];
        this.templates = this.getBuiltInTemplates();
        
        this.init();
    }

    init() {
        // Initialize when the YAML editor tab is first accessed
        document.addEventListener('DOMContentLoaded', () => {
            if (window.dashboard && window.dashboard.currentTab === 'yaml-editor') {
                this.initializeEditor();
            }
        });
    }

    initializeEditor() {
        const editorElement = document.getElementById('yamlEditor');
        if (!editorElement || this.editor) return;

        // Initialize CodeMirror if available, otherwise use textarea
        if (window.CodeMirror) {
            this.editor = CodeMirror.fromTextArea(editorElement, {
                mode: 'yaml',
                theme: 'monokai',
                lineNumbers: true,
                lineWrapping: true,
                indentUnit: 2,
                tabSize: 2,
                autoCloseBrackets: true,
                matchBrackets: true,
                foldGutter: true,
                gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter']
            });

            this.editor.on('change', () => {
                this.onEditorChange();
            });
        } else {
            // Fallback to textarea
            this.editor = {
                getValue: () => editorElement.value,
                setValue: (value) => { editorElement.value = value; },
                on: () => {} // No-op for compatibility
            };
            
            editorElement.addEventListener('input', () => {
                this.onEditorChange();
            });
        }

        this.loadDefaultTemplate();
    }

    onEditorChange() {
        // Clear previous validation results
        this.clearValidationResults();
        
        // Show info message
        this.showValidationMessage('Configuration modified. Click "Validate" to check syntax and AI validation.', 'info');
    }

    getBuiltInTemplates() {
        return {
            zai: {
                name: 'Z.AI Web Chat',
                description: 'Configuration for Z.AI web chat interface',
                content: `name: ZaiTest1Integration
URL: https://chat.z.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea[placeholder*="message"], input[type="text"]'
  send_button: 'button[type="submit"], button:contains("Send")'
  response_area: '.message-content, .response-text'
  new_conversation: 'button:contains("New"), .new-chat-button'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries`
            },
            mistral: {
                name: 'Mistral AI',
                description: 'Configuration for Mistral AI chat interface',
                content: `name: MistralTestIntegration
URL: https://chat.mistral.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '3'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea[data-testid="chat-input"]'
  send_button: 'button[data-testid="send-button"]'
  response_area: '.message-content'
  new_conversation: 'button[data-testid="new-chat"]'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries`
            },
            deepseek: {
                name: 'DeepSeek',
                description: 'Configuration for DeepSeek chat interface',
                content: `name: DeepSeekTestIntegration
URL: https://chat.deepseek.com
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '20'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea.chat-input'
  send_button: 'button.send-btn'
  response_area: '.message-bubble'
  new_conversation: '.new-chat-btn'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries`
            },
            claude: {
                name: 'Claude',
                description: 'Configuration for Claude chat interface',
                content: `name: ClaudeTestIntegration
URL: https://claude.ai
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '5'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'div[contenteditable="true"]'
  send_button: 'button[aria-label="Send Message"]'
  response_area: '.message-content'
  new_conversation: 'button:contains("New Conversation")'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries`
            },
            openai: {
                name: 'OpenAI API',
                description: 'Configuration for OpenAI REST API',
                content: `name: OpenAIAPIIntegration
URL: https://api.openai.com/v1/chat/completions
api_key: 'your-api-key-here'
maxautoscaleparallel: '10'
provider_type: rest_api
model: gpt-4
headers:
  Authorization: 'Bearer {api_key}'
  Content-Type: 'application/json'
request_format:
  model: '{model}'
  messages: []
  temperature: 0.7
  max_tokens: 2000
response_format:
  content_path: 'choices[0].message.content'
  error_path: 'error.message'
interaction_methods:
  - method: chat_completion
    description: Standard chat completion API
  - method: streaming_completion
    description: Streaming chat completion
  - method: function_calling
    description: Function calling support
  - method: error_handling
    description: Handle API errors and rate limits`
            },
            generic: {
                name: 'Generic Web Chat',
                description: 'Generic configuration template for web chat interfaces',
                content: `name: GenericWebChatIntegration
URL: https://example.com/chat
authemail: 'your-email@example.com'
authpassword: 'your-password'
maxautoscaleparallel: '5'
savecookiesforfutureuse: 'yes'
createuniquefingerprintsandboxdeploymentsnapshot: 'yes'
useproxy: 'no'
provider_type: web_chat
interface_elements:
  text_input: 'textarea, input[type="text"]'
  send_button: 'button[type="submit"], .send-button'
  response_area: '.message, .response'
  new_conversation: '.new-chat, .clear-chat'
interaction_methods:
  - method: direct_input
    description: Direct text input and send
  - method: streaming_response
    description: Handle streaming responses
  - method: session_management
    description: Manage conversation sessions
  - method: error_handling
    description: Handle errors and retries`
            }
        };
    }

    loadTemplate() {
        const templateSelect = document.getElementById('templateSelect');
        const selectedTemplate = templateSelect.value;
        
        if (!selectedTemplate) return;
        
        const template = this.templates[selectedTemplate];
        if (template) {
            this.editor.setValue(template.content);
            this.currentTemplate = selectedTemplate;
            this.showValidationMessage(`Loaded ${template.name} template`, 'success');
        }
    }

    loadDefaultTemplate() {
        // Load Z.AI template by default
        this.editor.setValue(this.templates.zai.content);
        this.currentTemplate = 'zai';
        document.getElementById('templateSelect').value = 'zai';
    }

    async validateYAML() {
        const yamlContent = this.editor.getValue();
        
        if (!yamlContent.trim()) {
            this.showValidationMessage('Please enter YAML configuration to validate', 'warning');
            return;
        }

        this.showValidationMessage('Validating configuration...', 'info');

        try {
            // Basic YAML syntax validation
            const syntaxValidation = this.validateYAMLSyntax(yamlContent);
            
            // AI-assisted validation using Codegen API
            const aiValidation = await this.validateWithAI(yamlContent);
            
            // Combine results
            this.validationResults = [...syntaxValidation, ...aiValidation];
            this.displayValidationResults();
            
        } catch (error) {
            console.error('Validation error:', error);
            this.showValidationMessage(`Validation failed: ${error.message}`, 'error');
        }
    }

    validateYAMLSyntax(yamlContent) {
        const results = [];
        const lines = yamlContent.split('\n');
        
        // Basic YAML syntax checks
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const lineNum = i + 1;
            
            // Check for required fields
            if (line.includes('name:') && !line.includes('name: ')) {
                results.push({
                    type: 'error',
                    message: `Line ${lineNum}: Missing space after 'name:' colon`,
                    line: lineNum
                });
            }
            
            // Check for proper indentation
            if (line.trim() && line.startsWith(' ') && line.search(/[^ ]/) % 2 !== 0) {
                results.push({
                    type: 'warning',
                    message: `Line ${lineNum}: Inconsistent indentation (should be 2 spaces)`,
                    line: lineNum
                });
            }
        }
        
        // Check for required fields
        const requiredFields = ['name', 'URL', 'provider_type'];
        for (const field of requiredFields) {
            if (!yamlContent.includes(`${field}:`)) {
                results.push({
                    type: 'error',
                    message: `Missing required field: ${field}`,
                    line: null
                });
            }
        }
        
        // Check for valid provider_type
        const validProviderTypes = ['web_chat', 'rest_api'];
        const providerTypeMatch = yamlContent.match(/provider_type:\s*['"]?(\w+)['"]?/);
        if (providerTypeMatch && !validProviderTypes.includes(providerTypeMatch[1])) {
            results.push({
                type: 'error',
                message: `Invalid provider_type: ${providerTypeMatch[1]}. Must be one of: ${validProviderTypes.join(', ')}`,
                line: null
            });
        }
        
        return results;
    }

    async validateWithAI(yamlContent) {
        try {
            // This would integrate with the Codegen API for AI validation
            const response = await fetch('/api/config/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    yaml_content: yamlContent,
                    validation_type: 'ai_assisted'
                })
            });

            if (!response.ok) {
                throw new Error('AI validation service unavailable');
            }

            const result = await response.json();
            return result.validation_results || [];
            
        } catch (error) {
            console.error('AI validation error:', error);
            return [{
                type: 'warning',
                message: 'AI validation service unavailable. Basic syntax validation only.',
                line: null
            }];
        }
    }

    displayValidationResults() {
        const resultsContainer = document.getElementById('validationResults');
        
        if (this.validationResults.length === 0) {
            resultsContainer.innerHTML = `
                <div class="validation-message success">
                    <i class="fas fa-check-circle"></i>
                    <span>Configuration is valid! No issues found.</span>
                </div>
            `;
            return;
        }

        const resultsHtml = this.validationResults.map(result => `
            <div class="validation-message ${result.type}">
                <i class="fas fa-${this.getValidationIcon(result.type)}"></i>
                <div>
                    <div>${result.message}</div>
                    ${result.line ? `<small>Line ${result.line}</small>` : ''}
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = resultsHtml;
    }

    getValidationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    showValidationMessage(message, type) {
        const resultsContainer = document.getElementById('validationResults');
        resultsContainer.innerHTML = `
            <div class="validation-message ${type}">
                <i class="fas fa-${this.getValidationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
    }

    clearValidationResults() {
        this.validationResults = [];
    }

    async saveYAMLConfig() {
        const yamlContent = this.editor.getValue();
        
        if (!yamlContent.trim()) {
            this.showValidationMessage('Please enter YAML configuration to save', 'warning');
            return;
        }

        // Validate before saving
        await this.validateYAML();
        
        // Check if there are any errors
        const hasErrors = this.validationResults.some(result => result.type === 'error');
        if (hasErrors) {
            if (!confirm('Configuration has validation errors. Save anyway?')) {
                return;
            }
        }

        try {
            const response = await fetch('/api/config/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    yaml_content: yamlContent,
                    template_name: this.currentTemplate
                })
            });

            if (!response.ok) {
                throw new Error('Failed to save configuration');
            }

            const result = await response.json();
            this.showValidationMessage('Configuration saved successfully!', 'success');
            
            // Optionally create endpoint from saved config
            if (confirm('Configuration saved! Would you like to create an endpoint from this configuration?')) {
                await this.createEndpointFromConfig(result.config_id);
            }
            
        } catch (error) {
            console.error('Save error:', error);
            this.showValidationMessage(`Failed to save configuration: ${error.message}`, 'error');
        }
    }

    async createEndpointFromConfig(configId) {
        try {
            const response = await fetch('/api/endpoints/from-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    config_id: configId
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create endpoint');
            }

            const endpoint = await response.json();
            this.showValidationMessage('Endpoint created successfully!', 'success');
            
            // Switch to endpoints tab to show the new endpoint
            if (window.dashboard) {
                window.dashboard.switchTab('endpoints');
            }
            
        } catch (error) {
            console.error('Create endpoint error:', error);
            this.showValidationMessage(`Failed to create endpoint: ${error.message}`, 'error');
        }
    }

    exportYAML() {
        const yamlContent = this.editor.getValue();
        const blob = new Blob([yamlContent], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentTemplate || 'config'}.yaml`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    importYAML() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.yaml,.yml';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.editor.setValue(e.target.result);
                    this.showValidationMessage(`Imported ${file.name}`, 'success');
                };
                reader.readAsText(file);
            }
        };
        
        input.click();
    }
}

// Global functions for HTML onclick handlers
window.loadTemplate = () => yamlEditor.loadTemplate();
window.validateYAML = () => yamlEditor.validateYAML();
window.saveYAMLConfig = () => yamlEditor.saveYAMLConfig();

// Initialize YAML editor
let yamlEditor;
document.addEventListener('DOMContentLoaded', () => {
    yamlEditor = new YAMLEditor();
    window.yamlEditor = yamlEditor; // Make available globally
    
    // Initialize editor when tab is switched
    if (window.dashboard) {
        const originalSwitchTab = window.dashboard.switchTab;
        window.dashboard.switchTab = function(tabName) {
            originalSwitchTab.call(this, tabName);
            if (tabName === 'yaml-editor') {
                setTimeout(() => yamlEditor.initializeEditor(), 100);
            }
        };
    }
});
