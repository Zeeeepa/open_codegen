import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Language as WebIcon,
  Api as ApiIcon,
  Link as LinkIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import toast from 'react-hot-toast';

import { endpointService } from '../services/endpointService';

function WebsiteManager({ config }) {
  const [websites, setWebsites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState({});

  // Form state
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [analysisProgress, setAnalysisProgress] = useState(0);

  useEffect(() => {
    loadWebsites();
  }, []);

  const loadWebsites = async () => {
    try {
      const data = await endpointService.getWebsites();
      setWebsites(data);
    } catch (error) {
      console.error('Failed to load websites:', error);
      toast.error('Failed to load websites');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeWebsite = async () => {
    if (!websiteUrl.trim()) return;

    setAnalyzing(true);
    setAnalysisProgress(0);

    try {
      // Start analysis
      const analysisId = await endpointService.startWebsiteAnalysis(websiteUrl);
      
      // Poll for progress
      const pollProgress = setInterval(async () => {
        try {
          const progress = await endpointService.getAnalysisProgress(analysisId);
          setAnalysisProgress(progress.percentage);
          
          if (progress.completed) {
            clearInterval(pollProgress);
            const results = await endpointService.getAnalysisResults(analysisId);
            setAnalysisResults(results);
            setAnalyzing(false);
            toast.success('Website analysis completed');
          }
        } catch (error) {
          clearInterval(pollProgress);
          setAnalyzing(false);
          toast.error('Analysis failed');
        }
      }, 1000);

    } catch (error) {
      console.error('Failed to analyze website:', error);
      toast.error('Failed to start website analysis');
      setAnalyzing(false);
    }
  };

  const handleSaveWebsite = async () => {
    try {
      await endpointService.saveWebsite({
        url: websiteUrl,
        analysis: analysisResults,
      });
      toast.success('Website saved successfully');
      setDialogOpen(false);
      setWebsiteUrl('');
      setAnalysisResults({});
      loadWebsites();
    } catch (error) {
      console.error('Failed to save website:', error);
      toast.error('Failed to save website');
    }
  };

  const handleCreateEndpointsFromWebsite = async (website) => {
    try {
      const endpoints = await endpointService.createEndpointsFromWebsite(website.id);
      toast.success(`Created ${endpoints.length} endpoints from website`);
    } catch (error) {
      console.error('Failed to create endpoints:', error);
      toast.error('Failed to create endpoints from website');
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
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
        <Typography variant="h4">Website Manager</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          Add Website
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Analyze websites to discover API endpoints and create client integrations for any AI provider.
      </Typography>

      {/* Websites Grid */}
      <Grid container spacing={3}>
        {websites.map((website) => (
          <Grid item xs={12} md={6} lg={4} key={website.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <WebIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" noWrap>
                    {website.name || new URL(website.url).hostname}
                  </Typography>
                </Box>
                
                <Typography variant="caption" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                  {website.url}
                </Typography>

                <Box sx={{ mt: 2, mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Discovered: {website.endpoints?.length || 0} endpoints
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Links: {website.links?.length || 0} resources
                  </Typography>
                </Box>

                {website.analysis_date && (
                  <Typography variant="caption" color="text.secondary">
                    Analyzed: {new Date(website.analysis_date).toLocaleDateString()}
                  </Typography>
                )}
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={<ApiIcon />}
                  onClick={() => handleCreateEndpointsFromWebsite(website)}
                  disabled={!website.endpoints?.length}
                >
                  Create Endpoints
                </Button>
              </CardActions>

              {/* Website Details */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="caption">Analysis Details</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {website.endpoints && website.endpoints.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Discovered Endpoints:
                      </Typography>
                      <List dense>
                        {website.endpoints.slice(0, 5).map((endpoint, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <ApiIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText
                              primary={`${endpoint.method} ${endpoint.path}`}
                              secondary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Chip
                                    label={`${getConfidenceLabel(endpoint.confidence)} Confidence`}
                                    color={getConfidenceColor(endpoint.confidence)}
                                    size="small"
                                  />
                                  <Typography variant="caption">
                                    {Math.round(endpoint.confidence * 100)}%
                                  </Typography>
                                </Box>
                              }
                            />
                          </ListItem>
                        ))}
                        {website.endpoints.length > 5 && (
                          <ListItem>
                            <ListItemText
                              primary={`... and ${website.endpoints.length - 5} more`}
                            />
                          </ListItem>
                        )}
                      </List>
                    </Box>
                  )}

                  {website.links && website.links.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Discovered Resources:
                      </Typography>
                      <List dense>
                        {website.links.slice(0, 3).map((link, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <LinkIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText
                              primary={link.text || 'Untitled'}
                              secondary={link.url}
                            />
                          </ListItem>
                        ))}
                        {website.links.length > 3 && (
                          <ListItem>
                            <ListItemText
                              primary={`... and ${website.links.length - 3} more resources`}
                            />
                          </ListItem>
                        )}
                      </List>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Add Website Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <WebIcon sx={{ mr: 1 }} />
            Analyze Website
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Website URL"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            placeholder="https://api.example.com"
            sx={{ mt: 2, mb: 2 }}
            disabled={analyzing}
          />

          {analyzing && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Analyzing website... {Math.round(analysisProgress)}%
              </Typography>
              <LinearProgress variant="determinate" value={analysisProgress} />
            </Box>
          )}

          {analysisResults.endpoints && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="success" sx={{ mb: 2 }}>
                Analysis completed! Found {analysisResults.endpoints.length} potential endpoints
                and {analysisResults.links?.length || 0} resources.
              </Alert>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Preview Results</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Discovered Endpoints:
                  </Typography>
                  <List dense>
                    {analysisResults.endpoints.slice(0, 10).map((endpoint, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          {endpoint.confidence >= 0.8 ? (
                            <CheckIcon color="success" fontSize="small" />
                          ) : endpoint.confidence >= 0.6 ? (
                            <InfoIcon color="warning" fontSize="small" />
                          ) : (
                            <ErrorIcon color="error" fontSize="small" />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={`${endpoint.method} ${endpoint.path}`}
                          secondary={`Confidence: ${Math.round(endpoint.confidence * 100)}%`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          {!analysisResults.endpoints ? (
            <Button
              onClick={handleAnalyzeWebsite}
              variant="contained"
              disabled={!websiteUrl.trim() || analyzing}
              startIcon={analyzing ? <CircularProgress size={16} /> : <SearchIcon />}
            >
              {analyzing ? 'Analyzing...' : 'Analyze'}
            </Button>
          ) : (
            <Button onClick={handleSaveWebsite} variant="contained">
              Save Website
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default WebsiteManager;

