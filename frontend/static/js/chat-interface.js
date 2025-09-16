/**
 * Chat Interface for Testing Endpoints
 * Handles chat interactions with configured endpoints
 */

class ChatInterface {
    constructor() {
        this.currentEndpointId = null;
        this.chatHistory = [];
        this.isWaitingForResponse = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Chat input event listeners
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const endpointSelect = document.getElementById('chatEndpointSelect');

        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });

            chatInput.addEventListener('input', () => {
                this.updateSendButtonState();
            });
        }

        if (endpointSelect) {
            endpointSelect.addEventListener('change', () => {
                this.selectEndpoint(endpointSelect.value);
            });
        }
    }

    async refreshChatEndpoints() {
        try {
            const response = await fetch('/api/endpoints');
            if (!response.ok) {
                throw new Error('Failed to fetch endpoints');
            }

            const endpoints = await response.json();
            this.populateEndpointSelect(endpoints);
        } catch (error) {
            console.error('Failed to refresh chat endpoints:', error);
            this.addSystemMessage('Failed to load endpoints. Please refresh the page.');
        }
    }

    populateEndpointSelect(endpoints) {
        const select = document.getElementById('chatEndpointSelect');
        if (!select) return;

        // Clear existing options except the first one
        select.innerHTML = '<option value="">Select Endpoint</option>';

        // Add running endpoints only
        const runningEndpoints = endpoints.filter(e => e.status === 'running');
        
        if (runningEndpoints.length === 0) {
            select.innerHTML += '<option value="" disabled>No running endpoints available</option>';
            return;
        }

        runningEndpoints.forEach(endpoint => {
            const option = document.createElement('option');
            option.value = endpoint.id;
            option.textContent = `${endpoint.name} (${endpoint.provider_name})`;
            select.appendChild(option);
        });
    }

    selectEndpoint(endpointId) {
        if (!endpointId) {
            this.currentEndpointId = null;
            this.updateSendButtonState();
            this.addSystemMessage('Please select an endpoint to start chatting.');
            return;
        }

        this.currentEndpointId = endpointId;
        this.updateSendButtonState();
        
        // Clear chat and add welcome message
        this.clearChat();
        this.addSystemMessage(`Connected to endpoint. You can now start chatting!`);
    }

    async sendChatMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();

        if (!message || !this.currentEndpointId || this.isWaitingForResponse) {
            return;
        }

        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input and disable send button
        chatInput.value = '';
        this.isWaitingForResponse = true;
        this.updateSendButtonState();

        try {
            // Send message to endpoint
            const response = await fetch(`/api/endpoints/${this.currentEndpointId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.getConversationId()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle streaming response if supported
            if (response.headers.get('content-type')?.includes('text/stream')) {
                await this.handleStreamingResponse(response);
            } else {
                const result = await response.json();
                this.addAssistantMessage(result.response || result.content || 'No response received');
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.addErrorMessage(`Failed to send message: ${error.message}`);
        } finally {
            this.isWaitingForResponse = false;
            this.updateSendButtonState();
        }
    }

    async handleStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Create assistant message container
        const messageElement = this.addAssistantMessage('');
        const contentElement = messageElement.querySelector('.message-text');
        
        let buffer = '';
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                // Process complete lines
                for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i].trim();
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            return;
                        }
                        
                        try {
                            const parsed = JSON.parse(data);
                            const content = parsed.choices?.[0]?.delta?.content || parsed.content || '';
                            if (content) {
                                contentElement.textContent += content;
                                this.scrollToBottom();
                            }
                        } catch (e) {
                            // Ignore parsing errors for individual chunks
                        }
                    }
                }
                
                // Keep the last incomplete line in buffer
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            console.error('Streaming error:', error);
            contentElement.textContent += '\n\n[Error: Connection interrupted]';
        }
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement('user', message);
        this.appendMessage(messageElement);
        this.chatHistory.push({ role: 'user', content: message });
        return messageElement;
    }

    addAssistantMessage(message) {
        const messageElement = this.createMessageElement('assistant', message);
        this.appendMessage(messageElement);
        if (message) {
            this.chatHistory.push({ role: 'assistant', content: message });
        }
        return messageElement;
    }

    addSystemMessage(message) {
        const messageElement = this.createMessageElement('system', message);
        this.appendMessage(messageElement);
        return messageElement;
    }

    addErrorMessage(message) {
        const messageElement = this.createMessageElement('error', message);
        this.appendMessage(messageElement);
        return messageElement;
    }

    createMessageElement(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        const icon = this.getMessageIcon(type);
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-${icon}"></i>
                <div class="message-text">${this.escapeHtml(content)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
        
        return messageDiv;
    }

    getMessageIcon(type) {
        const icons = {
            user: 'user',
            assistant: 'robot',
            system: 'info-circle',
            error: 'exclamation-triangle'
        };
        return icons[type] || 'comment';
    }

    appendMessage(messageElement) {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.appendChild(messageElement);
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    updateSendButtonState() {
        const sendButton = document.getElementById('sendButton');
        const chatInput = document.getElementById('chatInput');
        
        if (sendButton && chatInput) {
            const hasMessage = chatInput.value.trim().length > 0;
            const hasEndpoint = this.currentEndpointId !== null;
            const canSend = hasMessage && hasEndpoint && !this.isWaitingForResponse;
            
            sendButton.disabled = !canSend;
            
            if (this.isWaitingForResponse) {
                sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            } else {
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            }
        }
    }

    clearChat() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        this.chatHistory = [];
    }

    getConversationId() {
        // Generate or retrieve conversation ID for session management
        if (!this.conversationId) {
            this.conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return this.conversationId;
    }

    displayTestResult(endpointId, result) {
        // Switch to the endpoint that was tested
        const endpointSelect = document.getElementById('chatEndpointSelect');
        if (endpointSelect) {
            endpointSelect.value = endpointId;
            this.selectEndpoint(endpointId);
        }

        // Add test result as system message
        this.addSystemMessage('Test completed successfully!');
        
        // Add the test response
        if (result.response || result.content) {
            this.addAssistantMessage(result.response || result.content);
        }
    }

    exportChatHistory() {
        if (this.chatHistory.length === 0) {
            alert('No chat history to export');
            return;
        }

        const chatData = {
            endpoint_id: this.currentEndpointId,
            conversation_id: this.conversationId,
            timestamp: new Date().toISOString(),
            messages: this.chatHistory
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_history_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async loadChatHistory() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                try {
                    const text = await file.text();
                    const chatData = JSON.parse(text);
                    
                    if (chatData.messages && Array.isArray(chatData.messages)) {
                        this.clearChat();
                        
                        // Restore chat history
                        this.chatHistory = chatData.messages;
                        
                        // Display messages
                        chatData.messages.forEach(msg => {
                            if (msg.role === 'user') {
                                this.addUserMessage(msg.content);
                            } else if (msg.role === 'assistant') {
                                this.addAssistantMessage(msg.content);
                            }
                        });
                        
                        this.addSystemMessage(`Loaded chat history from ${file.name}`);
                    } else {
                        throw new Error('Invalid chat history format');
                    }
                } catch (error) {
                    console.error('Failed to load chat history:', error);
                    this.addErrorMessage(`Failed to load chat history: ${error.message}`);
                }
            }
        };
        
        input.click();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Method to handle voice input (future enhancement)
    async startVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.addSystemMessage('Voice input not supported in this browser');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            this.addSystemMessage('Listening... Speak now.');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.value = transcript;
                this.updateSendButtonState();
            }
        };

        recognition.onerror = (event) => {
            this.addErrorMessage(`Voice recognition error: ${event.error}`);
        };

        recognition.onend = () => {
            this.addSystemMessage('Voice input ended.');
        };

        recognition.start();
    }
}

// Global functions for HTML onclick handlers
window.sendChatMessage = () => chatInterface.sendChatMessage();
window.clearChat = () => chatInterface.clearChat();

// Initialize chat interface
let chatInterface;
document.addEventListener('DOMContentLoaded', () => {
    chatInterface = new ChatInterface();
    window.chatInterface = chatInterface; // Make available globally
    
    // Hook into dashboard tab switching
    if (window.dashboard) {
        const originalLoadTabData = window.dashboard.loadTabData;
        window.dashboard.loadTabData = function(tabName) {
            originalLoadTabData.call(this, tabName);
            if (tabName === 'chat-interface') {
                chatInterface.refreshChatEndpoints();
            }
        };
        
        // Make displayTestResult available to dashboard
        window.dashboard.displayTestResult = (endpointId, result) => {
            chatInterface.displayTestResult(endpointId, result);
        };
    }
});
