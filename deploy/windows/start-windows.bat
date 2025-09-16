@echo off
title OpenCodegen Enhanced - Starting...
color 0A

echo.
echo ========================================
echo   OpenCodegen Enhanced - Windows
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..\..\

REM Change to project directory
cd /d "%PROJECT_DIR%"

echo Current directory: %CD%
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run the installation script first.
    echo.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Creating default configuration...
    echo.
    
    echo # OpenCodegen Enhanced Configuration > .env
    echo CODEGEN_ORG_ID=323 >> .env
    echo CODEGEN_TOKEN=your_codegen_token_here >> .env
    echo CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run >> .env
    echo CODEGEN_DEFAULT_MODEL=codegen-standard >> .env
    echo TRANSPARENT_MODE=false >> .env
    echo PORT=8001 >> .env
    echo. >> .env
    echo # Supabase Configuration (Optional) >> .env
    echo SUPABASE_URL=your_supabase_url_here >> .env
    echo SUPABASE_KEY=your_supabase_key_here >> .env
    echo. >> .env
    echo # Enhanced Features >> .env
    echo ENABLE_WEB_INTERFACE=true >> .env
    echo ENABLE_ENDPOINT_MANAGEMENT=true >> .env
    echo ENABLE_AI_ASSISTANCE=true >> .env
    
    echo Default .env file created. Please edit it with your configuration.
    echo.
)

REM Load environment variables from .env file
echo Loading configuration...
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" (
        set "%%a=%%b"
    )
)

REM Set default port if not specified
if "%PORT%"=="" set PORT=8001

echo Configuration loaded:
echo - Port: %PORT%
echo - Codegen Base URL: %CODEGEN_BASE_URL%
echo - Web Interface: %ENABLE_WEB_INTERFACE%
echo.

REM Check if port is available
echo Checking if port %PORT% is available...
netstat -an | find ":%PORT% " >nul
if %errorlevel%==0 (
    echo WARNING: Port %PORT% is already in use!
    echo Please stop the service using that port or change the PORT in .env file.
    echo.
    set /p choice="Continue anyway? (y/N): "
    if /i not "%choice%"=="y" (
        echo Startup cancelled.
        pause
        exit /b 1
    )
) else (
    echo Port %PORT% is available.
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation was successful
if "%VIRTUAL_ENV%"=="" (
    echo ERROR: Failed to activate virtual environment!
    echo Please check your installation.
    echo.
    pause
    exit /b 1
)

echo Virtual environment activated: %VIRTUAL_ENV%
echo.

REM Check if required modules are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Required dependencies not found!
    echo Installing missing dependencies...
    pip install fastapi uvicorn supabase aiohttp selenium beautifulsoup4
    if %errorlevel% neq 0 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo Dependencies check passed.
echo.

REM Start the application
echo Starting OpenCodegen Enhanced...
echo.
echo ========================================
echo   Server will start on port %PORT%
echo   Web Interface: http://localhost:%PORT%
echo   API Documentation: http://localhost:%PORT%/docs
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the FastAPI application
python -m backend.api.main

REM If we get here, the server has stopped
echo.
echo ========================================
echo   OpenCodegen Enhanced has stopped
echo ========================================
echo.

REM Check exit code
if %errorlevel% neq 0 (
    echo Server exited with error code: %errorlevel%
    echo.
    echo Common issues:
    echo - Port %PORT% might be in use
    echo - Configuration file might be invalid
    echo - Required dependencies might be missing
    echo.
    echo Check the error messages above for more details.
) else (
    echo Server stopped normally.
)

echo.
pause
