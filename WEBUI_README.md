# Web UI Control Panel

The OpenAI Codegen Adapter now includes a beautiful Web UI control panel that allows you to monitor and control the service status.

## Features

🎛️ **Service Control**
- Real-time status display (ON/OFF)
- One-click toggle button to enable/disable the service
- Visual status indicators with animations

📊 **Monitoring**
- Service health status
- Last updated timestamp
- Server information display

🎨 **Modern Interface**
- Responsive design that works on all devices
- Beautiful gradient backgrounds and animations
- Intuitive user experience

## How to Use

1. **Start the server:**
   ```bash
   python3 server.py
   ```

2. **Open the Web UI:**
   Navigate to `http://localhost:8887` in your web browser

3. **Control the service:**
   - View the current status (ON/OFF)
   - Click "Turn On" or "Turn Off" to toggle the service
   - Monitor real-time updates

## API Endpoints

The Web UI uses these new API endpoints:

- `GET /` - Web UI interface
- `GET /api/status` - Get current service status
- `POST /api/toggle` - Toggle service on/off
- `GET /health` - Health check

## Service Behavior

When the service is **OFF**:
- All API endpoints (except Web UI and control endpoints) return HTTP 503
- The Web UI remains accessible for control
- Status and toggle endpoints continue to work

When the service is **ON**:
- All API endpoints work normally
- Full OpenAI-compatible API functionality available

## Technical Details

- Built with FastAPI and modern HTML/CSS/JavaScript
- Real-time status updates every 5 seconds
- Responsive design for mobile and desktop
- Error handling and user feedback
- Middleware-based service control

## Screenshots

The Web UI features:
- Clean, modern design with gradient backgrounds
- Animated status indicators
- Responsive toggle buttons
- Real-time status updates
- Error and success notifications

Perfect for monitoring and controlling your Codegen Adapter service!

