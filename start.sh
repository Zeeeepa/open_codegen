#!/bin/bash

# OpenAI Codegen Adapter Startup Script
# This starts both the API interceptor and the Web UI interface
# Web UI will be available at: http://localhost (or https://localhost if using transparent mode)

# Path to Python executable
PYTHON_PATH="/home/l/.pyenv/versions/3.13.0/bin/python"

# Check if Python executable exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python executable not found at $PYTHON_PATH"
    exit 1
fi

# Check if server.py exists
if [ ! -f "server.py" ]; then
    echo "Error: server.py not found in current directory"
    exit 1
fi

# Run server.py with specific Python version
# This starts both the OpenAI API interceptor and the Web UI
sudo "$PYTHON_PATH" server.py
