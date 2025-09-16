import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  IconButton,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Api as ApiIcon,
  Language as WebIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  Menu as MenuIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

const DRAWER_WIDTH = 240;
const COLLAPSED_WIDTH = 60;

const menuItems = [
  { path: '/chat', label: 'AI Chat', icon: <ChatIcon /> },
  { path: '/endpoints', label: 'API Endpoints', icon: <ApiIcon /> },
  { path: '/websites', label: 'Website Manager', icon: <WebIcon /> },
  { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/config', label: 'Configuration', icon: <SettingsIcon /> },
];

function Sidebar({ open, onToggle }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: open ? DRAWER_WIDTH : COLLAPSED_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: open ? DRAWER_WIDTH : COLLAPSED_WIDTH,
          boxSizing: 'border-box',
          transition: 'width 0.3s',
          overflowX: 'hidden',
          bgcolor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: open ? 'space-between' : 'center',
          minHeight: 64,
        }}
      >
        {open && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CodeIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" noWrap>
              Codegen
            </Typography>
          </Box>
        )}
        <IconButton onClick={onToggle} size="small">
          <MenuIcon />
        </IconButton>
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ flexGrow: 1, pt: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <ListItem key={item.path} disablePadding>
              <Tooltip title={!open ? item.label : ''} placement="right">
                <ListItemButton
                  onClick={() => handleNavigation(item.path)}
                  selected={isActive}
                  sx={{
                    minHeight: 48,
                    justifyContent: open ? 'initial' : 'center',
                    px: 2.5,
                    '&.Mui-selected': {
                      bgcolor: 'primary.main',
                      color: 'primary.contrastText',
                      '&:hover': {
                        bgcolor: 'primary.dark',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'primary.contrastText',
                      },
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 0,
                      mr: open ? 3 : 'auto',
                      justifyContent: 'center',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    sx={{ opacity: open ? 1 : 0 }}
                  />
                </ListItemButton>
              </Tooltip>
            </ListItem>
          );
        })}
      </List>

      <Divider />

      {/* Footer */}
      <Box sx={{ p: 2, textAlign: 'center' }}>
        {open && (
          <Typography variant="caption" color="text.secondary">
            OpenAI Codegen Adapter
            <br />
            v1.0.0
          </Typography>
        )}
      </Box>
    </Drawer>
  );
}

export default Sidebar;

