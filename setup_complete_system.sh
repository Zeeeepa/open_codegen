#!/bin/bash

# 🚀 Complete Setup Script for Unified AI Provider Gateway System
# This script will clone the repository with all AI providers and set up the system

echo "🚀 Setting up Unified AI Provider Gateway System..."
echo "=================================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Set python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✅ Prerequisites check passed"

# Clone the repository with all submodules
echo "📥 Cloning repository with all AI providers..."
git clone --recursive https://github.com/Zeeeepa/open_codegen.git

# Navigate to the project directory
cd open_codegen

# Checkout the feature branch
echo "🔄 Checking out feature branch..."
git checkout codegen-bot/api-interception-system-1758999258

# Update submodules to ensure we have the latest
echo "🔄 Updating submodules..."
git submodule update --init --recursive

# Install Python dependencies
echo "📦 Installing Python dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🚀 To start the system, run:"
echo "   cd open_codegen"
echo "   $PYTHON_CMD scripts/start_unified_system.py"
echo ""
echo "🌐 Then access:"
echo "   • API Gateway: http://localhost:7999"
echo "   • Dashboard: Open frontend/enhanced_index.html in browser"
echo "   • OpenAI API: http://localhost:7999/v1/chat/completions"
echo ""
echo "🧪 Test with:"
echo "   curl -X POST http://localhost:7999/v1/chat/completions \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\":\"gpt-3.5-turbo\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'"
echo ""
echo "✅ Your unified AI provider gateway is ready!"
