# 🚀 Enhanced Startup Script Guide

## Overview

The enhanced `start.sh` script provides comprehensive setup and startup functionality for the OpenAI Codegen Adapter project. It automatically handles package management, environment configuration, and server startup.

## Features

### 🔍 **Automatic Package Discovery**
- Searches for codegen package in multiple locations
- Checks system-wide and user-specific Python package directories
- Uses pip to locate package installation path

### 📦 **Package Management**
- Automatically upgrades existing codegen package to latest version
- Installs codegen package if not found
- Handles both system and user installations

### 🛠️ **Environment Configuration**
- Sets up PYTHONPATH for proper module resolution
- Configures CODEGEN_SDK_PATH with precise package location
- Sets default credentials if not provided
- Validates Python version compatibility

### 🏗️ **Project Validation**
- Verifies project structure integrity
- Checks for required backend and frontend files
- Provides clear error messages for missing components

### 🎨 **Enhanced User Experience**
- Colored output for better readability
- Structured logging with info, success, warning, and error levels
- Progress indicators for each setup step
- Graceful error handling and cleanup

## Usage

### Basic Usage
```bash
./start.sh
```

### With Custom Environment Variables
```bash
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-token"
./start.sh
```

## Script Flow

1. **🐍 Python Detection**
   - Locates Python 3.7+ executable
   - Reports Python version
   - Validates pip availability

2. **📦 Package Management**
   - Searches for existing codegen package
   - Upgrades or installs codegen package
   - Sets precise package location

3. **🛠️ Environment Setup**
   - Configures PYTHONPATH
   - Sets codegen SDK path
   - Applies default credentials

4. **✅ Project Validation**
   - Verifies backend/server.py exists
   - Confirms src/index.html is present
   - Validates project structure

5. **🚀 Server Startup**
   - Starts backend server on port 8000
   - Serves frontend UI
   - Enables API interception

## Output Example

```bash
ℹ️  Starting Enhanced OpenAI Codegen Adapter Setup...
✅ Using Python: python3
ℹ️  Python version: 3.13.4
ℹ️  Searching for codegen package...
✅ Found codegen package at: /usr/local/lib/python3.13/site-packages/codegen
ℹ️  Attempting to upgrade existing codegen package...
✅ Codegen package upgraded successfully
ℹ️  Setting up environment...
✅ Codegen SDK path set to: /usr/local/lib/python3.13/site-packages/codegen
ℹ️  Using default CODEGEN_ORG_ID: 323
ℹ️  Using default CODEGEN_TOKEN
ℹ️  Validating project structure...
✅ Project structure validated
ℹ️  Starting OpenAI Codegen Adapter server...
ℹ️  📊 Web UI will be available at: http://localhost:8000
ℹ️  🔧 API endpoints will intercept OpenAI API calls and redirect to Codegen SDK
ℹ️  🎯 System Message functionality available in UI
```

## Access Points

After successful startup:

- **Web UI**: http://localhost:8000
- **OpenAI API Endpoint**: http://localhost:8000/v1/chat/completions
- **Anthropic API Endpoint**: http://localhost:8000/v1/messages
- **Gemini API Endpoint**: http://localhost:8000/v1/gemini/generateContent
- **Health Check**: http://localhost:8000/health

## Error Handling

The script includes comprehensive error handling:

- **Python Not Found**: Clear instructions for Python installation
- **Package Installation Failed**: Guidance for manual installation
- **Project Structure Invalid**: Specific missing file identification
- **Server Startup Failed**: Detailed error reporting

## Customization

### Environment Variables

- `CODEGEN_ORG_ID`: Your organization ID
- `CODEGEN_TOKEN`: Your authentication token
- `PYTHONPATH`: Additional Python module paths

### Script Variables

- `SERVER_PORT`: Change default port (default: 8000)
- `PYTHON_PATH`: Override Python executable path

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x start.sh
   ```

2. **Python Not Found**
   - Install Python 3.7+
   - Update PATH environment variable

3. **Package Installation Failed**
   - Check internet connection
   - Verify pip is installed
   - Try manual installation: `pip install codegen`

4. **Port Already in Use**
   - Change SERVER_PORT in script
   - Kill existing process on port 8000

### Debug Mode

For detailed debugging, run with bash verbose mode:
```bash
bash -x start.sh
```

## Integration

The enhanced startup script integrates seamlessly with:

- **Development Environments**: Local development setup
- **CI/CD Pipelines**: Automated deployment scripts
- **Docker Containers**: Container startup commands
- **System Services**: Service manager integration

## Security

- Default credentials are provided for testing only
- Production deployments should use custom credentials
- Package upgrades ensure latest security patches
- Environment variables prevent credential exposure

