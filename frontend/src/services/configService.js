import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

class ConfigService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
    });
  }

  async getConfig() {
    try {
      const response = await this.client.get('/api/config');
      return response.data;
    } catch (error) {
      console.error('Failed to get configuration:', error);
      throw new Error('Failed to load configuration');
    }
  }

  async updateConfig(config) {
    try {
      const response = await this.client.put('/api/config', config);
      return response.data;
    } catch (error) {
      console.error('Failed to update configuration:', error);
      throw new Error(error.response?.data?.detail || 'Failed to update configuration');
    }
  }

  async getDefaultConfig() {
    try {
      const response = await this.client.get('/api/config/default');
      return response.data;
    } catch (error) {
      console.error('Failed to get default configuration:', error);
      throw new Error('Failed to load default configuration');
    }
  }

  async exportConfig() {
    try {
      const response = await this.client.get('/api/config/export');
      return response.data;
    } catch (error) {
      console.error('Failed to export configuration:', error);
      throw new Error('Failed to export configuration');
    }
  }

  async importConfig(config) {
    try {
      const response = await this.client.post('/api/config/import', config);
      return response.data;
    } catch (error) {
      console.error('Failed to import configuration:', error);
      throw new Error(error.response?.data?.detail || 'Failed to import configuration');
    }
  }

  async validateConfig(config) {
    try {
      const response = await this.client.post('/api/config/validate', config);
      return response.data;
    } catch (error) {
      console.error('Failed to validate configuration:', error);
      throw new Error(error.response?.data?.detail || 'Configuration validation failed');
    }
  }

  async getSystemStats() {
    try {
      const response = await this.client.get('/api/system/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to get system stats:', error);
      return {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageResponseTime: 0,
        activeEndpoints: 0,
        totalWebsites: 0,
        uptime: 0,
      };
    }
  }

  async getRecentActivity() {
    try {
      const response = await this.client.get('/api/system/activity');
      return response.data;
    } catch (error) {
      console.error('Failed to get recent activity:', error);
      return [];
    }
  }

  async getPerformanceData() {
    try {
      const response = await this.client.get('/api/system/performance');
      return response.data;
    } catch (error) {
      console.error('Failed to get performance data:', error);
      return {
        labels: [],
        datasets: [],
      };
    }
  }

  async getSystemHealth() {
    try {
      const response = await this.client.get('/api/system/health');
      return response.data;
    } catch (error) {
      console.error('Failed to get system health:', error);
      throw new Error('Failed to check system health');
    }
  }

  async restartSystem() {
    try {
      const response = await this.client.post('/api/system/restart');
      return response.data;
    } catch (error) {
      console.error('Failed to restart system:', error);
      throw new Error('Failed to restart system');
    }
  }
}

export const configService = new ConfigService();

