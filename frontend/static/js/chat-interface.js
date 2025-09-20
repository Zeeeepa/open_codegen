/**
 * Chat Interface Module
 * Handles the test chat functionality for AI endpoints
 */

class ChatInterface {
    constructor() {
        this.currentEndpoint = null;
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendMessageBtn');
        this.endpointSelector = document.getElementById('endpointSelector');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        
        this.initializeEventListeners();
        this.loadEndpoints();
    }
    
    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter (but not Shift+Enter)
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Enable/disable send button based on input and endpoint selection
        this.chatInput.addEventListener('input', () => this.updateSendButton());
        this.endpointSelector.addEventListener('change', (e) => {
            this.currentEndpoint = e.target.value;
            this.updateSendButton();
        });
        
        // Clear chat
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
    }
    
    async loadEndpoints() {
        try {
            const response = await fetch('/api/endpoints/');
            const endpoints = await response.json();
            
            this.endpointSelector.innerHTML = '<option value="">Select an endpoint to test</option>';
            
            endpoints.forEach(endpoint => {
                const option = document.createElement('option');
                option.value = endpoint.id;
                option.textContent = `${endpoint.name} (${endpoint.type})`;
                this.endpointSelector.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load endpoints:', error);
            this.addSystemMessage('Failed to load available endpoints', 'error');
        }
    }
    
    updateSendButton() {
        const hasInput = this.chatInput.value.trim().length > 0;
        const hasEndpoint = this.currentEndpoint && this.currentEndpoint.length > 0;
        this.sendButton.disabled = !(hasInput && hasEndpoint);
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || !this.currentEndpoint) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.chatInput.value = '';
        this.updateSendButton();
        
        // Show loading state
        const loadingElement = this.addMessage('Thinking...', 'assistant', true);
        
        try {
            // Send to API
            const response = await fetch(`/api/endpoints/${this.currentEndpoint}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    stream: false
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Remove loading message
            loadingElement.remove();
            
            // Add AI response
            this.addMessage(result.response || 'No response received', 'assistant');
            
        } catch (error) {
            console.error('Chat error:', error);
            loadingElement.remove();
            this.addMessage(`Error: ${error.message}`, 'assistant', false, 'error');
        }
    }
    
    addMessage(content, role, isLoading = false, type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role} ${type === 'error' ? 'message-error' : ''}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isLoading) {
            messageContent.innerHTML = `
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span>${content}</span>
            `;
        } else {
            messageContent.textContent = content;
        }
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(timestamp);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    addSystemMessage(content, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `system-message system-message-${type}`;
        
        const icon = type === 'error' ? 'fas fa-exclamation-triangle' : 'fas fa-info-circle';
        messageDiv.innerHTML = `
            <i class="${icon}"></i>
            <span>${content}</span>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    clearChat() {
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-robot"></i>
                <p>Welcome to the AI Endpoint Test Interface!</p>
                <p>Select an endpoint above and start chatting to test its functionality.</p>
            </div>
        `;
    }
}

// Initialize chat interface when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
});