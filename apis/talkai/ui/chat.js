class TalkAIChat {
    constructor() {
        this.apiKey = '';
        this.model = 'MBZUAI-IFM/K2-Think';
        this.isStreaming = true;
        this.temperature = 0.7;
        this.messages = [];
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.loadModels();
    }
    initializeElements() {
        // Configuration elements
        this.apiKeyInput = document.getElementById('apiKey');
        this.toggleApiKeyBtn = document.getElementById('toggleApiKey');
        this.modelSelect = document.getElementById('modelSelect');
        this.streamToggle = document.getElementById('streamToggle');
        this.temperatureSlider = document.getElementById('temperature');
        this.temperatureValue = document.getElementById('temperatureValue');
        
        // Chat elements
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearChatBtn = document.getElementById('clearChat');
        this.toggleConfigBtn = document.getElementById('toggleConfig');
        this.configPanel = document.getElementById('configPanel');
        
        // Status and loading
        this.statusIndicator = document.getElementById('status');
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }
    bindEvents() {
        // Configuration events
        this.apiKeyInput.addEventListener('input', () => this.handleApiKeyChange());
        this.toggleApiKeyBtn.addEventListener('click', () => this.toggleApiKeyVisibility());
        this.modelSelect.addEventListener('change', () => this.handleModelChange());
        this.streamToggle.addEventListener('change', () => this.handleStreamToggle());
        this.temperatureSlider.addEventListener('input', () => this.handleTemperatureChange());
        
        // Chat events
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.toggleConfigBtn.addEventListener('click', () => this.toggleConfig());
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());
    }
    loadSettings() {
        // Load settings from localStorage
        const savedApiKey = localStorage.getItem('talkai_api_key');
        const savedModel = localStorage.getItem('talkai_model');
        const savedStreaming = localStorage.getItem('talkai_streaming');
        const savedTemperature = localStorage.getItem('talkai_temperature');
        
        if (savedApiKey) {
            this.apiKey = savedApiKey;
            this.apiKeyInput.value = savedApiKey;
            this.updateSendButtonState();
        }
        
        if (savedModel) {
            this.model = savedModel;
            this.modelSelect.value = savedModel;
        }
        
        if (savedStreaming !== null) {
            this.isStreaming = savedStreaming === 'true';
            this.streamToggle.checked = this.isStreaming;
        }
        
        if (savedTemperature) {
            this.temperature = parseFloat(savedTemperature);
            this.temperatureSlider.value = this.temperature;
            this.temperatureValue.textContent = this.temperature;
        }
    }
    saveSettings() {
        localStorage.setItem('talkai_api_key', this.apiKey);
        localStorage.setItem('talkai_model', this.model);
        localStorage.setItem('talkai_streaming', this.isStreaming.toString());
        localStorage.setItem('talkai_temperature', this.temperature.toString());
    }
    async loadModels() {
        try {
            if (!this.apiKey) return;
            
            const response = await fetch('/v1/models', {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.populateModelSelect(data.data);
                this.updateStatus('connected', 'Connected');
            } else {
                this.updateStatus('error', 'API Error');
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            this.updateStatus('error', 'Connection Error');
        }
    }
    populateModelSelect(models) {
        this.modelSelect.innerHTML = '';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.id;
            this.modelSelect.appendChild(option);
        });
        
        if (this.model && models.find(m => m.id === this.model)) {
            this.modelSelect.value = this.model;
        } else if (models.length > 0) {
            this.model = models[0].id;
            this.modelSelect.value = this.model;
        }
    }
    handleApiKeyChange() {
        this.apiKey = this.apiKeyInput.value.trim();
        this.updateSendButtonState();
        this.saveSettings();
        
        if (this.apiKey) {
            this.loadModels();
        } else {
            this.updateStatus('', 'Ready');
        }
    }
    toggleApiKeyVisibility() {
        const isPassword = this.apiKeyInput.type === 'password';
        this.apiKeyInput.type = isPassword ? 'text' : 'password';
        this.toggleApiKeyBtn.innerHTML = isPassword ? 
            '<i class="fas fa-eye-slash"></i>' : 
            '<i class="fas fa-eye"></i>';
    }
    handleModelChange() {
        this.model = this.modelSelect.value;
        this.saveSettings();
    }
    handleStreamToggle() {
        this.isStreaming = this.streamToggle.checked;
        this.saveSettings();
    }
    handleTemperatureChange() {
        this.temperature = parseFloat(this.temperatureSlider.value);
        this.temperatureValue.textContent = this.temperature;
        this.saveSettings();
    }
    handleInputChange() {
        this.updateSendButtonState();
    }
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!this.isLoading && this.canSend()) {
                this.sendMessage();
            }
        }
    }
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    updateSendButtonState() {
        const canSend = this.canSend();
        this.sendButton.disabled = !canSend;
    }
    canSend() {
        return this.apiKey && this.messageInput.value.trim() && !this.isLoading;
    }
    updateStatus(type, message) {
        this.statusIndicator.className = `status-indicator ${type}`;
        this.statusIndicator.querySelector('span').textContent = message;
    }
    toggleConfig() {
        this.configPanel.classList.toggle('show');
    }
    clearChat() {
        this.messages = [];
        this.messagesContainer.innerHTML = `
            <div class="message system-message">
                <div class="message-content">
                    <i class="fas fa-info-circle"></i>
                    Chat cleared. Start a new conversation!
                </div>
            </div>
        `;
    }
    addMessage(role, content, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}${isError ? ' error' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.formatContent(content)}</div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        if (!isError) {
            this.messages.push({ role, content });
        }
    }
    formatContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-robot"></i>
                Thinking
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    setLoading(loading) {
        this.isLoading = loading;
        this.updateSendButtonState();
        
        if (loading) {
            this.loadingOverlay.classList.add('show');
            this.addTypingIndicator();
        } else {
            this.loadingOverlay.classList.remove('show');
            this.removeTypingIndicator();
        }
    }
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;
        // Add user message
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.autoResizeTextarea();
        
        // Prepare request
        const requestBody = {
            model: this.model,
            messages: [...this.messages],
            stream: this.isStreaming,
            temperature: this.temperature
        };
        this.setLoading(true);
        try {
            if (this.isStreaming) {
                await this.handleStreamingResponse(requestBody);
            } else {
                await this.handleNonStreamingResponse(requestBody);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('assistant', `Error: ${error.message}`, true);
        } finally {
            this.setLoading(false);
        }
    }
    async handleNonStreamingResponse(requestBody) {
        const response = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error?.message || 'API request failed');
        }
        const data = await response.json();
        const assistantMessage = data.choices[0].message.content;
        this.addMessage('assistant', assistantMessage);
    }
    async handleStreamingResponse(requestBody) {
        const response = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error?.message || 'API request failed');
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        let messageDiv = null;
        // Create assistant message container
        messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        const timestamp = new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="message-content"></div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        this.messagesContainer.appendChild(messageDiv);
        const contentDiv = messageDiv.querySelector('.message-content');
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') continue;
                        try {
                            const parsed = JSON.parse(data);
                            const delta = parsed.choices?.[0]?.delta;
                            
                            if (delta?.content) {
                                assistantMessage += delta.content;
                                contentDiv.innerHTML = this.formatContent(assistantMessage);
                                this.scrollToBottom();
                            }
                        } catch (e) {
                            // Ignore parsing errors for malformed chunks
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
        // Add to messages history
        if (assistantMessage) {
            this.messages.push({ role: 'assistant', content: assistantMessage });
        }
    }
}
// Initialize the chat application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TalkAIChat();
});
