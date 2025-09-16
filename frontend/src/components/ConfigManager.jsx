import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import toast from 'react-hot-toast';

import { configService } from '../services/configService';

function ConfigManager({ config, onConfigUpdate }) {
  const [formData, setFormData] = useState({
    codegen_api_key: '',
    codegen_base_url: 'https://api.codegen.com',
    openai_api_key: '',
    anthropic_api_key: '',
    gemini_api_key: '',
    zai_api_key: '',
    default_provider: 'openai',
    enable_streaming: true,
    enable_cors: true,
    server_port: 8000,
    log_level: 'INFO',
    max_tokens: 4096,
    temperature: 0.7,
    timeout: 30,
  });

  const [showSecrets, setShowSecrets] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (config) {
      setFormData(prev => ({ ...prev, ...config }));
    }
  }, [config]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleSecretVisibility = (field) => {
    setShowSecrets(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const updatedConfig = await configService.updateConfig(formData);
      onConfigUpdate(updatedConfig);
      toast.success('Configuration saved successfully');
    } catch (error) {
      console.error('Failed to save configuration:', error);
      toast.error('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      const defaultConfig = await configService.getDefaultConfig();
      setFormData(defaultConfig);
      toast.success('Configuration reset to defaults');
    } catch (error) {
      console.error('Failed to reset configuration:', error);
      toast.error('Failed to reset configuration');
    }
  };

  const handleExport = async () => {
    try {
      const configData = await configService.exportConfig();
      const blob = new Blob([JSON.stringify(configData, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'codegen-config.json';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Configuration exported');
    } catch (error) {
      console.error('Failed to export configuration:', error);
      toast.error('Failed to export configuration');
    }
  };

  const handleImport = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const importedConfig = JSON.parse(e.target.result);
        setFormData(prev => ({ ...prev, ...importedConfig }));
        toast.success('Configuration imported');
      } catch (error) {
        console.error('Failed to import configuration:', error);
        toast.error('Invalid configuration file');
      }
    };
    reader.readAsText(file);
  };

  const renderSecretField = (field, label, placeholder = '') => (
    <TextField
      fullWidth
      label={label}
      type={showSecrets[field] ? 'text' : 'password'}
      value={formData[field] || ''}
      onChange={(e) => handleInputChange(field, e.target.value)}
      placeholder={placeholder}
      InputProps={{
        endAdornment: (
          <IconButton
            onClick={() => toggleSecretVisibility(field)}
            edge="end"
            size="small"
          >
            {showSecrets[field] ? <VisibilityOffIcon /> : <VisibilityIcon />}
          </IconButton>
        ),
      }}
    />
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Configuration</Typography>
        <Box>
          <input
            accept=".json"
            style={{ display: 'none' }}
            id="import-config"
            type="file"
            onChange={handleImport}
          />
          <label htmlFor="import-config">
            <Button component="span" startIcon={<ImportIcon />} sx={{ mr: 1 }}>
              Import
            </Button>
          </label>
          <Button startIcon={<ExportIcon />} onClick={handleExport} sx={{ mr: 1 }}>
            Export
          </Button>
          <Button startIcon={<RefreshIcon />} onClick={handleReset} sx={{ mr: 1 }}>
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={loading}
          >
            Save
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* API Keys */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="API Keys" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  {renderSecretField('codegen_api_key', 'Codegen API Key', 'Your Codegen API key')}
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Codegen Base URL"
                    value={formData.codegen_base_url || ''}
                    onChange={(e) => handleInputChange('codegen_base_url', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  {renderSecretField('openai_api_key', 'OpenAI API Key', 'sk-...')}
                </Grid>
                <Grid item xs={12} md={6}>
                  {renderSecretField('anthropic_api_key', 'Anthropic API Key', 'sk-ant-...')}
                </Grid>
                <Grid item xs={12} md={6}>
                  {renderSecretField('gemini_api_key', 'Google Gemini API Key', 'AIza...')}
                </Grid>
                <Grid item xs={12} md={6}>
                  {renderSecretField('zai_api_key', 'Z.ai API Key', 'Optional - Z.ai key')}
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Provider Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Provider Settings" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Default Provider</InputLabel>
                    <Select
                      value={formData.default_provider || 'openai'}
                      onChange={(e) => handleInputChange('default_provider', e.target.value)}
                      label="Default Provider"
                    >
                      <MenuItem value="openai">OpenAI</MenuItem>
                      <MenuItem value="anthropic">Anthropic</MenuItem>
                      <MenuItem value="gemini">Google Gemini</MenuItem>
                      <MenuItem value="zai">Z.ai</MenuItem>
                      <MenuItem value="codegen">Codegen</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Tokens"
                    value={formData.max_tokens || 4096}
                    onChange={(e) => handleInputChange('max_tokens', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Temperature"
                    inputProps={{ min: 0, max: 2, step: 0.1 }}
                    value={formData.temperature || 0.7}
                    onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Timeout (seconds)"
                    value={formData.timeout || 30}
                    onChange={(e) => handleInputChange('timeout', parseInt(e.target.value))}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Server Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Server Settings" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Server Port"
                    value={formData.server_port || 8000}
                    onChange={(e) => handleInputChange('server_port', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Log Level</InputLabel>
                    <Select
                      value={formData.log_level || 'INFO'}
                      onChange={(e) => handleInputChange('log_level', e.target.value)}
                      label="Log Level"
                    >
                      <MenuItem value="DEBUG">DEBUG</MenuItem>
                      <MenuItem value="INFO">INFO</MenuItem>
                      <MenuItem value="WARNING">WARNING</MenuItem>
                      <MenuItem value="ERROR">ERROR</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.enable_streaming || false}
                        onChange={(e) => handleInputChange('enable_streaming', e.target.checked)}
                      />
                    }
                    label="Enable Streaming"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.enable_cors || false}
                        onChange={(e) => handleInputChange('enable_cors', e.target.checked)}
                      />
                    }
                    label="Enable CORS"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Advanced Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Advanced Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Alert severity="warning" sx={{ mb: 2 }}>
                These settings are for advanced users. Changing them may affect system stability.
              </Alert>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Custom Headers (JSON)"
                    multiline
                    rows={3}
                    value={formData.custom_headers || '{}'}
                    onChange={(e) => handleInputChange('custom_headers', e.target.value)}
                    placeholder='{"Authorization": "Bearer token"}'
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Proxy URL"
                    value={formData.proxy_url || ''}
                    onChange={(e) => handleInputChange('proxy_url', e.target.value)}
                    placeholder="http://proxy.example.com:8080"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.debug_mode || false}
                        onChange={(e) => handleInputChange('debug_mode', e.target.checked)}
                      />
                    }
                    label="Debug Mode (Verbose Logging)"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>
    </Box>
  );
}

export default ConfigManager;

