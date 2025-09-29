@echo off
REM 🚀 Complete Setup Script for Unified AI Provider Gateway System (Windows)
REM This script will clone the repository with all AI providers and set up the system

echo 🚀 Setting up Unified AI Provider Gateway System...
echo ==================================================

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first.
    pause
    exit /b 1
)

REM Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Clone the repository with all submodules
echo 📥 Cloning repository with all AI providers...
git clone --recursive https://github.com/Zeeeepa/open_codegen.git

REM Navigate to the project directory
cd open_codegen

REM Checkout the feature branch
echo 🔄 Checking out feature branch...
git checkout codegen-bot/api-interception-system-1758999258

REM Update submodules to ensure we have the latest
echo 🔄 Updating submodules...
git submodule update --init --recursive

REM Install Python dependencies
echo 📦 Installing Python dependencies...
python -m pip install -r requirements.txt

echo.
echo 🎉 Setup Complete!
echo ==================
echo.
echo 🚀 To start the system, run:
echo    cd open_codegen
echo    python scripts/start_unified_system.py
echo.
echo 🌐 Then access:
echo    • API Gateway: http://localhost:7999
echo    • Dashboard: Open frontend/enhanced_index.html in browser
echo    • OpenAI API: http://localhost:7999/v1/chat/completions
echo.
echo 🧪 Test with:
echo    curl -X POST http://localhost:7999/v1/chat/completions ^
echo      -H "Content-Type: application/json" ^
echo      -d "{\"model\":\"gpt-3.5-turbo\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}"
echo.
echo ✅ Your unified AI provider gateway is ready!
pause
