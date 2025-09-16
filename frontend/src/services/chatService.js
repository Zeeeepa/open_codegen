import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

class ChatService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    });
  }

  async sendMessage({ message, provider, model, conversation_history = [] }) {
    try {
      const response = await this.client.post('/api/chat', {
        message,
        provider,
        model,
        conversation_history,
        stream: true,
      }, {
        responseType: 'stream',
      });

      return {
        stream: response.data,
      };
    } catch (error) {
      console.error('Chat service error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to send message');
    }
  }

  async sendMessageSync({ message, provider, model, conversation_history = [] }) {
    try {
      const response = await this.client.post('/api/chat', {
        message,
        provider,
        model,
        conversation_history,
        stream: false,
      });

      return response.data;
    } catch (error) {
      console.error('Chat service error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to send message');
    }
  }

  async getConversationHistory(conversationId) {
    try {
      const response = await this.client.get(`/api/conversations/${conversationId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get conversation history:', error);
      throw new Error('Failed to load conversation history');
    }
  }

  async saveConversation(conversation) {
    try {
      const response = await this.client.post('/api/conversations', conversation);
      return response.data;
    } catch (error) {
      console.error('Failed to save conversation:', error);
      throw new Error('Failed to save conversation');
    }
  }

  async getProviders() {
    try {
      const response = await this.client.get('/api/providers');
      return response.data;
    } catch (error) {
      console.error('Failed to get providers:', error);
      throw new Error('Failed to load providers');
    }
  }

  async getModels(provider) {
    try {
      const response = await this.client.get(`/api/providers/${provider}/models`);
      return response.data;
    } catch (error) {
      console.error('Failed to get models:', error);
      throw new Error('Failed to load models');
    }
  }

  async testProvider(provider, apiKey) {
    try {
      const response = await this.client.post(`/api/providers/${provider}/test`, {
        api_key: apiKey,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to test provider:', error);
      throw new Error(error.response?.data?.detail || 'Provider test failed');
    }
  }
}

export const chatService = new ChatService();

