#!/bin/bash

# Start the server in the background
echo -e "\033[1;34m🚀 Starting server on port 8887...\033[0m"

# Start the server in the background and redirect output to a log file
python server.py > server.log 2>&1 &

# Get the PID of the server
SERVER_PID=$!

# Check if the server started successfully
sleep 2
if ps -p $SERVER_PID > /dev/null; then
    echo "Server started with PID $SERVER_PID (logs in server.log)"
    echo ""
    echo -e "\033[1;32m📋 Access Information:\033[0m"
    echo "------------------------"
    echo -e "\033[1;36m🌐 Web UI: http://localhost:8887/\033[0m"
    echo -e "\033[1;36m🩺 Health Check: http://localhost:8887/health\033[0m"
    echo ""
    echo -e "\033[1;32m📱 API Endpoints:\033[0m"
    echo "------------------------"
    echo -e "OpenAI:    POST http://localhost:8887/v1/chat/completions"
    echo -e "Anthropic: POST http://localhost:8887/v1/anthropic/completions"
    echo -e "Google:    POST http://localhost:8887/v1/gemini/completions"
    echo ""
    echo -e "\033[1;32m🧪 Run Tests:\033[0m"
    echo "------------------------"
    echo -e "python run_tests.py"
    echo ""
    echo -e "\033[1;33m⚠️  NOTE: The server runs in the background. To stop it:\033[0m"
    echo "pkill -f 'python server.py'"
else
    echo -e "\033[1;31m❌ Failed to start server. Check server.log for details.\033[0m"
    exit 1
fi

