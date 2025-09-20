@echo off
echo ========================================
echo Universal AI Endpoint Manager - Windows Deployment
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Checking version...
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

REM Create virtual environment
echo.
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install backend dependencies
echo.
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt

REM Install Playwright browsers
echo.
echo Installing Playwright browsers...
playwright install chromium

REM Go back to root directory
cd ..

REM Create .env file if it doesn't exist
if not exist "backend\.env" (
    echo.
    echo Creating .env file...
    copy backend\.env.example backend\.env
    echo Please edit backend\.env with your configuration
)

REM Create startup script
echo.
echo Creating startup script...
(
echo @echo off
echo echo Starting Universal AI Endpoint Manager...
echo call venv\Scripts\activate.bat
echo cd backend
echo python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo pause
) > start_server.bat

echo.
echo ========================================
echo Deployment completed successfully!
echo ========================================
echo.
echo To start the server:
echo 1. Run start_server.bat
echo 2. Open http://localhost:8000 in your browser
echo.
echo Configuration:
echo - Edit backend\.env for API keys and settings
echo - Web interface will be available at http://localhost:8000
echo - API documentation at http://localhost:8000/docs
echo.
echo Press any key to start the server now...
pause >nul

REM Start the server
call start_server.bat
