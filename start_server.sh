#!/bin/bash

# Kill any existing server
pkill -f 'python api_system.py' 2>/dev/null

# Check for Codegen SDK URL
if [ -z "$CODEGEN_API_URL" ]; then
    echo -e "\033[1;33m⚠️  Using default Codegen SDK URL: http://localhost:8000/api/generate\033[0m"
    echo -e "\033[1;33m⚠️  Set CODEGEN_API_URL environment variable to change this.\033[0m"
fi

# Start the server in the background
echo -e "\033[1;34m🚀 Starting API Router System on port 8887...\033[0m"

# Start the server in the background and redirect output to a log file
nohup python api_system.py > server.log 2>&1 &

# Get the PID of the server
SERVER_PID=$!

# Wait a moment for the server to start
sleep 2
if ps -p $SERVER_PID > /dev/null; then
    echo "Server started with PID $SERVER_PID (logs in server.log)"
    
    # Check if the server is healthy
    HEALTH_CHECK=$(curl -s http://localhost:8887/health)
    if [[ $HEALTH_CHECK == *"\"status\":\"healthy\""* ]]; then
        echo -e "\033[1;32m✅ Server is healthy!\033[0m"
        
        # Extract routing URL from health check
        ROUTING_TO=$(echo $HEALTH_CHECK | grep -o '"routing_to":"[^"]*"' | cut -d'"' -f4)
        if [ ! -z "$ROUTING_TO" ]; then
            echo -e "\033[1;32m🔄 Routing requests to: $ROUTING_TO\033[0m"
        fi
    else
        echo -e "\033[1;31m❌ Server health check failed!\033[0m"
        echo "Health check response: $HEALTH_CHECK"
        echo "Check server.log for details."
        exit 1
    fi
    
    echo ""
    echo -e "\033[1;32m📋 Access Information:\033[0m"
    echo "------------------------"
    echo -e "\033[1;36m🌐 Web UI: http://localhost:8887/\033[0m"
    echo -e "\033[1;36m🧰 Health Check: http://localhost:8887/health\033[0m"
    
    echo ""
    echo -e "\033[1;32m📱 API Endpoints:\033[0m"
    echo "------------------------"
    echo "OpenAI:    POST http://localhost:8887/v1/chat/completions"
    echo "Anthropic: POST http://localhost:8887/v1/anthropic/completions"
    echo "Google:    POST http://localhost:8887/v1/gemini/completions"
    
    echo ""
    echo -e "\033[1;32m🔌 How to Use with Existing Applications:\033[0m"
    echo "------------------------"
    echo "OpenAI:    Set OPENAI_API_BASE=http://localhost:8887/v1"
    echo "Anthropic: Set ANTHROPIC_API_URL=http://localhost:8887/v1"
    echo "Google:    Set GEMINI_API_URL=http://localhost:8887/v1"
    
    echo ""
    echo -e "\033[1;33m⚠️  NOTE: The server runs in the background. To stop it:\033[0m"
    echo "pkill -f 'python api_system.py'"
else
    echo -e "\033[1;31m❌ Failed to start server!\033[0m"
    echo "Check server.log for details."
    exit 1
fi

