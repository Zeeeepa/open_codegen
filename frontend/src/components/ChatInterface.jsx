import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon,
  Clear as ClearIcon,
  Settings as SettingsIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import toast from 'react-hot-toast';

import { chatService } from '../services/chatService';

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', models: ['gpt-4', 'gpt-3.5-turbo'] },
  { id: 'anthropic', name: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet'] },
  { id: 'gemini', name: 'Google Gemini', models: ['gemini-pro', 'gemini-pro-vision'] },
  { id: 'zai', name: 'Z.ai', models: ['glm-4.5', 'glm-4.5v'] },
  { id: 'codegen', name: 'Codegen', models: ['codegen-standard', 'codegen-advanced'] },
];

function ChatInterface({ config }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleProviderChange = (event) => {
    const provider = event.target.value;
    setSelectedProvider(provider);
    const providerData = PROVIDERS.find(p => p.id === provider);
    if (providerData && providerData.models.length > 0) {
      setSelectedModel(providerData.models[0]);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
      provider: selectedProvider,
      model: selectedModel,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setStreamingMessage('');

    try {
      const response = await chatService.sendMessage({
        message: inputMessage,
        provider: selectedProvider,
        model: selectedModel,
        conversation_history: messages,
      });

      if (response.stream) {
        // Handle streaming response
        const reader = response.stream.getReader();
        let assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          provider: selectedProvider,
          model: selectedModel,
        };

        setMessages(prev => [...prev, assistantMessage]);

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = new TextDecoder().decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') continue;

                try {
                  const parsed = JSON.parse(data);
                  if (parsed.choices && parsed.choices[0].delta.content) {
                    const content = parsed.choices[0].delta.content;
                    setStreamingMessage(prev => prev + content);
                    
                    // Update the last message
                    setMessages(prev => {
                      const updated = [...prev];
                      updated[updated.length - 1].content += content;
                      return updated;
                    });
                  }
                } catch (e) {
                  console.error('Error parsing streaming data:', e);
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
          setStreamingMessage('');
        }
      } else {
        // Handle non-streaming response
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.content,
          timestamp: new Date(),
          provider: selectedProvider,
          model: selectedModel,
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setStreamingMessage('');
  };

  const renderMessage = (message) => {
    const isUser = message.role === 'user';
    
    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
        }}
      >
        <Paper
          sx={{
            p: 2,
            maxWidth: '70%',
            bgcolor: isUser ? 'primary.main' : 'background.paper',
            color: isUser ? 'primary.contrastText' : 'text.primary',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {isUser ? <PersonIcon sx={{ mr: 1 }} /> : <BotIcon sx={{ mr: 1 }} />}
            <Typography variant="caption">
              {isUser ? 'You' : `${message.provider} (${message.model})`}
            </Typography>
            <Typography variant="caption" sx={{ ml: 'auto', opacity: 0.7 }}>
              {message.timestamp.toLocaleTimeString()}
            </Typography>
          </Box>
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </Paper>
      </Box>
    );
  };

  const currentProvider = PROVIDERS.find(p => p.id === selectedProvider);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h5">AI Chat Interface</Typography>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Provider</InputLabel>
            <Select
              value={selectedProvider}
              onChange={handleProviderChange}
              label="Provider"
            >
              {PROVIDERS.map(provider => (
                <MenuItem key={provider.id} value={provider.id}>
                  {provider.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Model</InputLabel>
            <Select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              label="Model"
            >
              {currentProvider?.models.map(model => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ ml: 'auto' }}>
            <IconButton onClick={clearChat} title="Clear Chat">
              <ClearIcon />
            </IconButton>
            <IconButton title="Settings">
              <SettingsIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* Messages */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 2,
          bgcolor: 'background.default',
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              opacity: 0.5,
            }}
          >
            <BotIcon sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h6">Start a conversation</Typography>
            <Typography variant="body2">
              Select a provider and model, then type your message below
            </Typography>
          </Box>
        ) : (
          <>
            {messages.map(renderMessage)}
            {isLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
                <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CircularProgress size={20} sx={{ mr: 2 }} />
                    <Typography>Thinking...</Typography>
                  </Box>
                </Paper>
              </Box>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            sx={{ minWidth: 'auto', px: 2 }}
          >
            <SendIcon />
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

export default ChatInterface;

