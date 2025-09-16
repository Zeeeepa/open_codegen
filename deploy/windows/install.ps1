# OpenCodegen Enhanced Windows Installation Script
# This script installs and configures OpenCodegen Enhanced with UI integration

param(
    [string]$InstallPath = "C:\OpenCodegen",
    [switch]$InstallAsService = $true,
    [switch]$SkipDependencies = $false,
    [string]$Port = "8001"
)

# Ensure running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges. Please run as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "=== OpenCodegen Enhanced Windows Installer ===" -ForegroundColor Green
Write-Host "Installation Path: $InstallPath" -ForegroundColor Yellow
Write-Host "Port: $Port" -ForegroundColor Yellow
Write-Host "Install as Service: $InstallAsService" -ForegroundColor Yellow
Write-Host ""

# Create installation directory
Write-Host "Creating installation directory..." -ForegroundColor Blue
if (!(Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# Check for Python
Write-Host "Checking Python installation..." -ForegroundColor Blue
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check for Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Blue
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Found Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js not found. Please install Node.js from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check for Git
Write-Host "Checking Git installation..." -ForegroundColor Blue
try {
    $gitVersion = git --version 2>&1
    Write-Host "Found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git not found. Please install Git from https://git-scm.com" -ForegroundColor Red
    exit 1
}

# Clone or update repository
Write-Host "Setting up OpenCodegen Enhanced..." -ForegroundColor Blue
$repoPath = Join-Path $InstallPath "open_codegen"

if (Test-Path $repoPath) {
    Write-Host "Updating existing installation..." -ForegroundColor Yellow
    Set-Location $repoPath
    git pull origin main
} else {
    Write-Host "Cloning repository..." -ForegroundColor Yellow
    Set-Location $InstallPath
    git clone https://github.com/Zeeeepa/open_codegen.git
    Set-Location $repoPath
}

# Install Python dependencies
if (!$SkipDependencies) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Blue
    
    # Create virtual environment
    python -m venv venv
    
    # Activate virtual environment and install dependencies
    & ".\venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    }
    
    # Install additional dependencies for enhanced features
    pip install fastapi uvicorn supabase aiohttp selenium beautifulsoup4
    
    Write-Host "Python dependencies installed successfully!" -ForegroundColor Green
}

# Install and build frontend
if (!$SkipDependencies) {
    Write-Host "Installing and building frontend..." -ForegroundColor Blue
    
    $frontendPath = Join-Path $repoPath "frontend"
    if (Test-Path $frontendPath) {
        Set-Location $frontendPath
        
        # Install npm dependencies
        npm install
        
        # Build production frontend
        npm run build
        
        Write-Host "Frontend built successfully!" -ForegroundColor Green
        Set-Location $repoPath
    } else {
        Write-Host "Frontend directory not found, skipping frontend build..." -ForegroundColor Yellow
    }
}

# Create configuration files
Write-Host "Creating configuration files..." -ForegroundColor Blue

# Create environment configuration
$envContent = @"
# OpenCodegen Enhanced Configuration
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=your_codegen_token_here
CODEGEN_BASE_URL=https://codegen-sh--rest-api.modal.run
CODEGEN_DEFAULT_MODEL=codegen-standard
TRANSPARENT_MODE=false
PORT=$Port

# Supabase Configuration (Optional)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Enhanced Features
ENABLE_WEB_INTERFACE=true
ENABLE_ENDPOINT_MANAGEMENT=true
ENABLE_AI_ASSISTANCE=true
"@

$envPath = Join-Path $repoPath ".env"
$envContent | Out-File -FilePath $envPath -Encoding UTF8

# Create startup script
$startupScript = @"
@echo off
cd /d "$repoPath"
call venv\Scripts\activate.bat
python -m backend.api.main
pause
"@

$startupPath = Join-Path $repoPath "start-windows.bat"
$startupScript | Out-File -FilePath $startupPath -Encoding ASCII

# Create service installation script
$serviceScript = @"
@echo off
echo Installing OpenCodegen Enhanced as Windows Service...

sc create "OpenCodegenEnhanced" binPath= "cmd /c cd /d `"$repoPath`" && venv\Scripts\python.exe -m backend.api.main" start= auto
sc description "OpenCodegenEnhanced" "OpenCodegen Enhanced API Server with UI Integration"

echo Service installed successfully!
echo Starting service...
sc start "OpenCodegenEnhanced"

echo.
echo Service Status:
sc query "OpenCodegenEnhanced"
pause
"@

$servicePath = Join-Path $repoPath "install-service.bat"
$serviceScript | Out-File -FilePath $servicePath -Encoding ASCII

# Install Chrome/Chromium for headless browsing
Write-Host "Checking for Chrome/Chromium..." -ForegroundColor Blue
$chromeFound = $false

# Check for Chrome
$chromePaths = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
)

foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Host "Found Chrome at: $path" -ForegroundColor Green
        $chromeFound = $true
        break
    }
}

if (!$chromeFound) {
    Write-Host "Chrome not found. Web interface testing may not work properly." -ForegroundColor Yellow
    Write-Host "Please install Google Chrome from https://chrome.google.com" -ForegroundColor Yellow
}

# Configure Windows Firewall
Write-Host "Configuring Windows Firewall..." -ForegroundColor Blue
try {
    netsh advfirewall firewall add rule name="OpenCodegen Enhanced" dir=in action=allow protocol=TCP localport=$Port
    Write-Host "Firewall rule added for port $Port" -ForegroundColor Green
} catch {
    Write-Host "Failed to add firewall rule. You may need to configure it manually." -ForegroundColor Yellow
}

# Install as Windows Service (optional)
if ($InstallAsService) {
    Write-Host "Installing as Windows Service..." -ForegroundColor Blue
    
    # Create service wrapper script
    $serviceWrapper = @"
import sys
import os
import subprocess
import time
import logging

# Setup logging
logging.basicConfig(
    filename=r'$InstallPath\opencodegen_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # Change to the correct directory
        os.chdir(r'$repoPath')
        
        # Activate virtual environment and run the application
        python_exe = r'$repoPath\venv\Scripts\python.exe'
        
        logging.info("Starting OpenCodegen Enhanced service...")
        
        # Run the FastAPI application
        process = subprocess.Popen([
            python_exe, '-m', 'backend.api.main'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Monitor the process
        while True:
            if process.poll() is not None:
                logging.error("Service process terminated unexpectedly")
                break
            time.sleep(10)
            
    except Exception as e:
        logging.error(f"Service error: {e}")

if __name__ == "__main__":
    main()
"@

    $serviceWrapperPath = Join-Path $repoPath "service_wrapper.py"
    $serviceWrapper | Out-File -FilePath $serviceWrapperPath -Encoding UTF8
    
    Write-Host "Service wrapper created. Run install-service.bat as Administrator to install the service." -ForegroundColor Green
}

# Create desktop shortcut
Write-Host "Creating desktop shortcut..." -ForegroundColor Blue
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OpenCodegen Enhanced.lnk")
$Shortcut.TargetPath = $startupPath
$Shortcut.WorkingDirectory = $repoPath
$Shortcut.IconLocation = "shell32.dll,13"
$Shortcut.Description = "OpenCodegen Enhanced - AI API Proxy with Web Interface"
$Shortcut.Save()

# Create start menu shortcut
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$StartMenuShortcut = $WshShell.CreateShortcut("$startMenuPath\OpenCodegen Enhanced.lnk")
$StartMenuShortcut.TargetPath = $startupPath
$StartMenuShortcut.WorkingDirectory = $repoPath
$StartMenuShortcut.IconLocation = "shell32.dll,13"
$StartMenuShortcut.Description = "OpenCodegen Enhanced - AI API Proxy with Web Interface"
$StartMenuShortcut.Save()

Write-Host ""
Write-Host "=== Installation Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Details:" -ForegroundColor Yellow
Write-Host "- Installation Path: $InstallPath" -ForegroundColor White
Write-Host "- Configuration File: $envPath" -ForegroundColor White
Write-Host "- Startup Script: $startupPath" -ForegroundColor White
Write-Host "- Service Script: $servicePath" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit the .env file to configure your API tokens" -ForegroundColor White
Write-Host "2. Run 'start-windows.bat' to start the application" -ForegroundColor White
Write-Host "3. Open http://localhost:$Port in your browser" -ForegroundColor White
Write-Host "4. Configure Supabase connection in Settings if needed" -ForegroundColor White
Write-Host ""
if ($InstallAsService) {
    Write-Host "To install as Windows Service:" -ForegroundColor Yellow
    Write-Host "- Run 'install-service.bat' as Administrator" -ForegroundColor White
    Write-Host ""
}
Write-Host "For support, visit: https://github.com/Zeeeepa/open_codegen" -ForegroundColor Cyan
Write-Host ""

# Offer to start the application
$startNow = Read-Host "Would you like to start OpenCodegen Enhanced now? (y/N)"
if ($startNow -eq "y" -or $startNow -eq "Y") {
    Write-Host "Starting OpenCodegen Enhanced..." -ForegroundColor Green
    Start-Process -FilePath $startupPath -WorkingDirectory $repoPath
    
    # Wait a moment and try to open browser
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:$Port"
}

Write-Host "Installation script completed successfully!" -ForegroundColor Green
