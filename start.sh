#!/bin/bash

# OpenAI Codegen Adapter Startup Script
# This starts both the API interceptor and the Web UI interface
# Web UI will be available at: http://localhost (or https://localhost if using transparent mode)

# Path to Python executable (try to detect automatically)
PYTHON_PATH=""

# Try to find Python executable
if command -v python3 &> /dev/null; then
    PYTHON_PATH="python3"
elif command -v python &> /dev/null; then
    PYTHON_PATH="python"
elif [ -f "/home/l/.pyenv/versions/3.13.0/bin/python" ]; then
    PYTHON_PATH="/home/l/.pyenv/versions/3.13.0/bin/python"
else
    echo "Error: Python executable not found. Please install Python 3.7+ or update PYTHON_PATH in this script."
    exit 1
fi

echo "🐍 Using Python: $PYTHON_PATH"

# Check if backend server exists
if [ ! -f "backend/server.py" ]; then
    echo "Error: backend/server.py not found. Please ensure the project is properly structured."
    exit 1
fi

# Check if UI files exist
if [ ! -f "src/index.html" ]; then
    echo "Error: src/index.html not found. Please ensure the project is properly structured."
    exit 1
fi

echo "🚀 Starting OpenAI Codegen Adapter..."
echo "📊 Web UI will be available at: http://localhost (or https://localhost if using transparent mode)"
echo "🔧 API endpoints will intercept OpenAI API calls and redirect to Codegen SDK"
echo ""

# Run the backend server with Python module path
# This starts both the OpenAI API interceptor and serves the Web UI
sudo "$PYTHON_PATH" -m backend.server
