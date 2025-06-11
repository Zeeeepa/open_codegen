#!/bin/bash
# Script to start the server and provide access instructions

# Check if server is already running
if lsof -i :8887 > /dev/null 2>&1; then
    echo "✅ Server is already running on port 8887"
else
    echo "🚀 Starting server on port 8887..."
    python server.py > server.log 2>&1 &
    SERVER_PID=$!
    echo "Server started with PID $SERVER_PID (logs in server.log)"
fi

echo ""
echo "📋 Access Information:"
echo "------------------------"
echo "🌐 Web UI: http://localhost:8887/"
echo "🩺 Health Check: http://localhost:8887/health"
echo ""
echo "📱 API Endpoints:"
echo "------------------------"
echo "OpenAI:    POST http://localhost:8887/v1/chat/completions"
echo "Anthropic: POST http://localhost:8887/v1/anthropic/completions"
echo "Google:    POST http://localhost:8887/v1/gemini/generateContent"
echo ""
echo "🧪 Run Tests:"
echo "------------------------"
echo "python run_tests.py"
echo ""
echo "⚠️  NOTE: The server runs in the background. To stop it:"
echo "pkill -f 'python server.py'"

