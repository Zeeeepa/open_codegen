import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  ExpandMore as ExpandMoreIcon,
  SmartToy as AiIcon,
  Code as CodeIcon,
  Language as WebIcon,
} from '@mui/icons-material';
import ReactJsonView from 'react-json-view';
import toast from 'react-hot-toast';

import { endpointService } from '../services/endpointService';

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

function EndpointManager({ config }) {
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEndpoint, setEditingEndpoint] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [aiGenerating, setAiGenerating] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    method: 'GET',
    url: '',
    headers: {},
    body: '',
    provider: 'openai',
    variables: [],
  });

  // AI generation state
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiDialogOpen, setAiDialogOpen] = useState(false);

  useEffect(() => {
    loadEndpoints();
  }, []);

  const loadEndpoints = async () => {
    try {
      const data = await endpointService.getEndpoints();
      setEndpoints(data);
    } catch (error) {
      console.error('Failed to load endpoints:', error);
      toast.error('Failed to load endpoints');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (endpoint = null) => {
    if (endpoint) {
      setEditingEndpoint(endpoint);
      setFormData({
        name: endpoint.name,
        description: endpoint.description,
        method: endpoint.method,
        url: endpoint.url,
        headers: endpoint.headers || {},
        body: endpoint.body || '',
        provider: endpoint.provider || 'openai',
        variables: endpoint.variables || [],
      });
    } else {
      setEditingEndpoint(null);
      setFormData({
        name: '',
        description: '',
        method: 'GET',
        url: '',
        headers: {},
        body: '',
        provider: 'openai',
        variables: [],
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingEndpoint(null);
  };

  const handleSaveEndpoint = async () => {
    try {
      if (editingEndpoint) {
        await endpointService.updateEndpoint(editingEndpoint.id, formData);
        toast.success('Endpoint updated successfully');
      } else {
        await endpointService.createEndpoint(formData);
        toast.success('Endpoint created successfully');
      }
      handleCloseDialog();
      loadEndpoints();
    } catch (error) {
      console.error('Failed to save endpoint:', error);
      toast.error('Failed to save endpoint');
    }
  };

  const handleDeleteEndpoint = async (id) => {
    if (window.confirm('Are you sure you want to delete this endpoint?')) {
      try {
        await endpointService.deleteEndpoint(id);
        toast.success('Endpoint deleted successfully');
        loadEndpoints();
      } catch (error) {
        console.error('Failed to delete endpoint:', error);
        toast.error('Failed to delete endpoint');
      }
    }
  };

  const handleTestEndpoint = async (endpoint) => {
    try {
      setTestResults(prev => ({ ...prev, [endpoint.id]: { loading: true } }));
      const result = await endpointService.testEndpoint(endpoint.id);
      setTestResults(prev => ({
        ...prev,
        [endpoint.id]: { loading: false, data: result }
      }));
      toast.success('Endpoint tested successfully');
    } catch (error) {
      console.error('Failed to test endpoint:', error);
      setTestResults(prev => ({
        ...prev,
        [endpoint.id]: { loading: false, error: error.message }
      }));
      toast.error('Endpoint test failed');
    }
  };

  const handleAiGenerate = async () => {
    if (!aiPrompt.trim()) return;

    setAiGenerating(true);
    try {
      const generatedEndpoint = await endpointService.generateEndpoint(aiPrompt);
      setFormData({
        name: generatedEndpoint.name,
        description: generatedEndpoint.description,
        method: generatedEndpoint.method,
        url: generatedEndpoint.url,
        headers: generatedEndpoint.headers || {},
        body: generatedEndpoint.body || '',
        provider: generatedEndpoint.provider || 'openai',
        variables: generatedEndpoint.variables || [],
      });
      setAiDialogOpen(false);
      setDialogOpen(true);
      toast.success('Endpoint generated successfully');
    } catch (error) {
      console.error('Failed to generate endpoint:', error);
      toast.error('Failed to generate endpoint');
    } finally {
      setAiGenerating(false);
    }
  };

  const getStatusColor = (endpoint) => {
    const result = testResults[endpoint.id];
    if (result?.loading) return 'info';
    if (result?.error) return 'error';
    if (result?.data) return 'success';
    return 'default';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">API Endpoint Manager</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<AiIcon />}
            onClick={() => setAiDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            AI Generate
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Endpoint
          </Button>
        </Box>
      </Box>

      {/* Endpoints Grid */}
      <Grid container spacing={3}>
        {endpoints.map((endpoint) => (
          <Grid item xs={12} md={6} lg={4} key={endpoint.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" noWrap>
                    {endpoint.name}
                  </Typography>
                  <Chip
                    label={endpoint.method}
                    color={endpoint.method === 'GET' ? 'primary' : 'secondary'}
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {endpoint.description}
                </Typography>

                <Typography variant="caption" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                  {endpoint.url}
                </Typography>

                <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={endpoint.provider}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={getStatusColor(endpoint) === 'success' ? 'Working' : 
                           getStatusColor(endpoint) === 'error' ? 'Error' : 'Untested'}
                    color={getStatusColor(endpoint)}
                    size="small"
                  />
                </Box>
              </CardContent>

              <CardActions>
                <IconButton
                  size="small"
                  onClick={() => handleTestEndpoint(endpoint)}
                  disabled={testResults[endpoint.id]?.loading}
                >
                  {testResults[endpoint.id]?.loading ? (
                    <CircularProgress size={16} />
                  ) : (
                    <TestIcon />
                  )}
                </IconButton>
                <IconButton size="small" onClick={() => handleOpenDialog(endpoint)}>
                  <EditIcon />
                </IconButton>
                <IconButton size="small" onClick={() => handleDeleteEndpoint(endpoint.id)}>
                  <DeleteIcon />
                </IconButton>
              </CardActions>

              {/* Test Results */}
              {testResults[endpoint.id] && !testResults[endpoint.id].loading && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="caption">
                      {testResults[endpoint.id].error ? 'Error Details' : 'Test Results'}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {testResults[endpoint.id].error ? (
                      <Alert severity="error">
                        {testResults[endpoint.id].error}
                      </Alert>
                    ) : (
                      <ReactJsonView
                        src={testResults[endpoint.id].data}
                        theme="monokai"
                        collapsed={1}
                        displayDataTypes={false}
                        displayObjectSize={false}
                        enableClipboard={false}
                      />
                    )}
                  </AccordionDetails>
                </Accordion>
              )}
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* AI Generation Dialog */}
      <Dialog open={aiDialogOpen} onClose={() => setAiDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AiIcon sx={{ mr: 1 }} />
            AI Endpoint Generator
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Describe the endpoint you want to create"
            placeholder="e.g., Create a POST endpoint to send chat messages to OpenAI GPT-4 with streaming response"
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAiDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAiGenerate}
            variant="contained"
            disabled={!aiPrompt.trim() || aiGenerating}
            startIcon={aiGenerating ? <CircularProgress size={16} /> : <AiIcon />}
          >
            {aiGenerating ? 'Generating...' : 'Generate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Endpoint Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingEndpoint ? 'Edit Endpoint' : 'Create New Endpoint'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Method</InputLabel>
                <Select
                  value={formData.method}
                  onChange={(e) => setFormData(prev => ({ ...prev, method: e.target.value }))}
                  label="Method"
                >
                  {HTTP_METHODS.map(method => (
                    <MenuItem key={method} value={method}>{method}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="URL"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                placeholder="https://api.example.com/endpoint"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Provider</InputLabel>
                <Select
                  value={formData.provider}
                  onChange={(e) => setFormData(prev => ({ ...prev, provider: e.target.value }))}
                  label="Provider"
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
                multiline
                rows={4}
                label="Request Body (JSON)"
                value={formData.body}
                onChange={(e) => setFormData(prev => ({ ...prev, body: e.target.value }))}
                placeholder='{"key": "value"}'
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveEndpoint} variant="contained">
            {editingEndpoint ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default EndpointManager;

