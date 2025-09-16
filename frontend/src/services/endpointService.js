import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

class EndpointService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    });
  }

  // Endpoint Management
  async getEndpoints() {
    try {
      const response = await this.client.get('/api/endpoints');
      return response.data;
    } catch (error) {
      console.error('Failed to get endpoints:', error);
      throw new Error('Failed to load endpoints');
    }
  }

  async createEndpoint(endpoint) {
    try {
      const response = await this.client.post('/api/endpoints', endpoint);
      return response.data;
    } catch (error) {
      console.error('Failed to create endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create endpoint');
    }
  }

  async updateEndpoint(id, endpoint) {
    try {
      const response = await this.client.put(`/api/endpoints/${id}`, endpoint);
      return response.data;
    } catch (error) {
      console.error('Failed to update endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to update endpoint');
    }
  }

  async deleteEndpoint(id) {
    try {
      const response = await this.client.delete(`/api/endpoints/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to delete endpoint');
    }
  }

  async testEndpoint(id, testData = {}) {
    try {
      const response = await this.client.post(`/api/endpoints/${id}/test`, testData);
      return response.data;
    } catch (error) {
      console.error('Failed to test endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Endpoint test failed');
    }
  }

  async generateEndpoint(prompt) {
    try {
      const response = await this.client.post('/api/endpoints/generate', {
        prompt,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to generate endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to generate endpoint');
    }
  }

  // Website Management
  async getWebsites() {
    try {
      const response = await this.client.get('/api/websites');
      return response.data;
    } catch (error) {
      console.error('Failed to get websites:', error);
      throw new Error('Failed to load websites');
    }
  }

  async startWebsiteAnalysis(url) {
    try {
      const response = await this.client.post('/api/websites/analyze', {
        url,
      });
      return response.data.analysis_id;
    } catch (error) {
      console.error('Failed to start website analysis:', error);
      throw new Error(error.response?.data?.detail || 'Failed to start website analysis');
    }
  }

  async getAnalysisProgress(analysisId) {
    try {
      const response = await this.client.get(`/api/websites/analysis/${analysisId}/progress`);
      return response.data;
    } catch (error) {
      console.error('Failed to get analysis progress:', error);
      throw new Error('Failed to get analysis progress');
    }
  }

  async getAnalysisResults(analysisId) {
    try {
      const response = await this.client.get(`/api/websites/analysis/${analysisId}/results`);
      return response.data;
    } catch (error) {
      console.error('Failed to get analysis results:', error);
      throw new Error('Failed to get analysis results');
    }
  }

  async saveWebsite(websiteData) {
    try {
      const response = await this.client.post('/api/websites', websiteData);
      return response.data;
    } catch (error) {
      console.error('Failed to save website:', error);
      throw new Error(error.response?.data?.detail || 'Failed to save website');
    }
  }

  async createEndpointsFromWebsite(websiteId) {
    try {
      const response = await this.client.post(`/api/websites/${websiteId}/create-endpoints`);
      return response.data;
    } catch (error) {
      console.error('Failed to create endpoints from website:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create endpoints from website');
    }
  }

  async deleteWebsite(id) {
    try {
      const response = await this.client.delete(`/api/websites/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete website:', error);
      throw new Error(error.response?.data?.detail || 'Failed to delete website');
    }
  }

  // Proxy and Client Endpoint Management
  async createClientEndpoint(websiteUrl, provider, config = {}) {
    try {
      const response = await this.client.post('/api/client-endpoints', {
        website_url: websiteUrl,
        provider,
        config,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create client endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create client endpoint');
    }
  }

  async getClientEndpoints() {
    try {
      const response = await this.client.get('/api/client-endpoints');
      return response.data;
    } catch (error) {
      console.error('Failed to get client endpoints:', error);
      throw new Error('Failed to load client endpoints');
    }
  }

  async testClientEndpoint(id, testMessage) {
    try {
      const response = await this.client.post(`/api/client-endpoints/${id}/test`, {
        message: testMessage,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to test client endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Client endpoint test failed');
    }
  }

  async updateClientEndpoint(id, config) {
    try {
      const response = await this.client.put(`/api/client-endpoints/${id}`, config);
      return response.data;
    } catch (error) {
      console.error('Failed to update client endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to update client endpoint');
    }
  }

  async deleteClientEndpoint(id) {
    try {
      const response = await this.client.delete(`/api/client-endpoints/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete client endpoint:', error);
      throw new Error(error.response?.data?.detail || 'Failed to delete client endpoint');
    }
  }

  // Provider Integration
  async getProviderEndpoints(provider) {
    try {
      const response = await this.client.get(`/api/providers/${provider}/endpoints`);
      return response.data;
    } catch (error) {
      console.error('Failed to get provider endpoints:', error);
      throw new Error('Failed to load provider endpoints');
    }
  }

  async createProviderProxy(provider, targetUrl, config = {}) {
    try {
      const response = await this.client.post('/api/provider-proxy', {
        provider,
        target_url: targetUrl,
        config,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create provider proxy:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create provider proxy');
    }
  }
}

export const endpointService = new EndpointService();

