# OpenAI Codegen Adapter - Windows Installer
# This script installs and configures the OpenAI Codegen Adapter with Web UI

param(
    [switch]$ServiceMode = $false,
    [string]$InstallPath = "$env:ProgramFiles\OpenAI-Codegen-Adapter",
    [string]$DataPath = "$env:LOCALAPPDATA\OpenAI-Codegen-Adapter",
    [int]$Port = 8000
)

# Require Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script requires Administrator privileges. Please run as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "🚀 OpenAI Codegen Adapter - Windows Installer" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to download and install Python
function Install-Python {
    Write-Host "📦 Installing Python..." -ForegroundColor Yellow
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
        Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
        Remove-Item $pythonInstaller -Force
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "✅ Python installed successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Failed to install Python: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to download and install Node.js
function Install-NodeJS {
    Write-Host "📦 Installing Node.js..." -ForegroundColor Yellow
    
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$env:TEMP\node-installer.msi"
    
    try {
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart" -Wait
        Remove-Item $nodeInstaller -Force
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "✅ Node.js installed successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Failed to install Node.js: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check dependencies
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow

$pythonOk = Test-Command python
$nodeOk = Test-Command node
$npmOk = Test-Command npm

if (-not $pythonOk) {
    Write-Host "⚠️ Python not found. Installing..." -ForegroundColor Yellow
    if (-not (Install-Python)) {
        exit 1
    }
    $pythonOk = Test-Command python
}

if (-not $nodeOk -or -not $npmOk) {
    Write-Host "⚠️ Node.js/npm not found. Installing..." -ForegroundColor Yellow
    if (-not (Install-NodeJS)) {
        exit 1
    }
    $nodeOk = Test-Command node
    $npmOk = Test-Command npm
}

if ($pythonOk) {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python installation failed" -ForegroundColor Red
    exit 1
}

if ($nodeOk -and $npmOk) {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "✅ Node.js: $nodeVersion, npm: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js/npm installation failed" -ForegroundColor Red
    exit 1
}

# Create installation directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
New-Item -ItemType Directory -Force -Path $DataPath | Out-Null
New-Item -ItemType Directory -Force -Path "$DataPath\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "$DataPath\data" | Out-Null

# Copy application files
Write-Host "📋 Copying application files..." -ForegroundColor Yellow
$sourceDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Copy backend files
Copy-Item -Path "$sourceDir\backend" -Destination "$InstallPath\backend" -Recurse -Force
Copy-Item -Path "$sourceDir\requirements.txt" -Destination "$InstallPath\" -Force

# Copy frontend files
if (Test-Path "$sourceDir\frontend") {
    Copy-Item -Path "$sourceDir\frontend" -Destination "$InstallPath\frontend" -Recurse -Force
}

# Copy other necessary files
$filesToCopy = @("README.md", ".env.example", "start.sh")
foreach ($file in $filesToCopy) {
    if (Test-Path "$sourceDir\$file") {
        Copy-Item -Path "$sourceDir\$file" -Destination "$InstallPath\" -Force
    }
}

# Install Python dependencies
Write-Host "🐍 Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $InstallPath
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install Python dependencies: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install and build frontend
if (Test-Path "$InstallPath\frontend") {
    Write-Host "🌐 Installing and building frontend..." -ForegroundColor Yellow
    Set-Location "$InstallPath\frontend"
    try {
        npm install
        npm run build
        Write-Host "✅ Frontend built successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to build frontend: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "⚠️ Continuing without frontend..." -ForegroundColor Yellow
    }
}

# Create configuration file
Write-Host "⚙️ Creating configuration..." -ForegroundColor Yellow
$configContent = @"
# OpenAI Codegen Adapter Configuration
CODEGEN_API_KEY=your_codegen_api_key_here
CODEGEN_BASE_URL=https://api.codegen.com
SERVER_PORT=$Port
LOG_LEVEL=INFO
DATA_PATH=$DataPath
ENABLE_WEB_UI=true
ENABLE_CORS=true
"@

$configPath = "$InstallPath\.env"
Set-Content -Path $configPath -Value $configContent

# Create startup script
Write-Host "📝 Creating startup script..." -ForegroundColor Yellow
$startupScript = @"
@echo off
cd /d "$InstallPath"
echo Starting OpenAI Codegen Adapter...
python -m backend.enhanced_server
pause
"@

$startupPath = "$InstallPath\start.bat"
Set-Content -Path $startupPath -Value $startupScript

# Create PowerShell startup script
$psStartupScript = @"
# OpenAI Codegen Adapter Startup Script
Set-Location "$InstallPath"
Write-Host "🚀 Starting OpenAI Codegen Adapter..." -ForegroundColor Cyan
python -m backend.enhanced_server
"@

$psStartupPath = "$InstallPath\start.ps1"
Set-Content -Path $psStartupPath -Value $psStartupScript

# Configure Windows Service (if requested)
if ($ServiceMode) {
    Write-Host "🔧 Configuring Windows Service..." -ForegroundColor Yellow
    
    $serviceName = "OpenAI-Codegen-Adapter"
    $serviceDisplayName = "OpenAI Codegen Adapter"
    $serviceDescription = "OpenAI API interception and routing service with web UI"
    
    # Create service wrapper script
    $serviceScript = @"
import sys
import os
import subprocess
import time
import logging

# Set up logging
logging.basicConfig(
    filename=r'$DataPath\logs\service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    os.chdir(r'$InstallPath')
    
    while True:
        try:
            logging.info("Starting OpenAI Codegen Adapter service...")
            process = subprocess.Popen([
                sys.executable, '-m', 'backend.enhanced_server'
            ], cwd=r'$InstallPath')
            
            process.wait()
            logging.warning("Service process exited, restarting in 5 seconds...")
            time.sleep(5)
            
        except Exception as e:
            logging.error(f"Service error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()
"@

    $serviceScriptPath = "$InstallPath\service.py"
    Set-Content -Path $serviceScriptPath -Value $serviceScript
    
    # Install service using NSSM (Non-Sucking Service Manager)
    try {
        # Download NSSM if not present
        $nssmPath = "$InstallPath\nssm.exe"
        if (-not (Test-Path $nssmPath)) {
            Write-Host "📦 Downloading NSSM..." -ForegroundColor Yellow
            $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
            $nssmZip = "$env:TEMP\nssm.zip"
            Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
            Expand-Archive -Path $nssmZip -DestinationPath "$env:TEMP\nssm" -Force
            Copy-Item -Path "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" -Destination $nssmPath -Force
            Remove-Item $nssmZip -Force
            Remove-Item "$env:TEMP\nssm" -Recurse -Force
        }
        
        # Remove existing service if it exists
        & $nssmPath stop $serviceName 2>$null
        & $nssmPath remove $serviceName confirm 2>$null
        
        # Install new service
        & $nssmPath install $serviceName python "$serviceScriptPath"
        & $nssmPath set $serviceName DisplayName "$serviceDisplayName"
        & $nssmPath set $serviceName Description "$serviceDescription"
        & $nssmPath set $serviceName Start SERVICE_AUTO_START
        & $nssmPath set $serviceName AppDirectory "$InstallPath"
        & $nssmPath set $serviceName AppStdout "$DataPath\logs\service-stdout.log"
        & $nssmPath set $serviceName AppStderr "$DataPath\logs\service-stderr.log"
        
        Write-Host "✅ Windows Service configured" -ForegroundColor Green
        Write-Host "   Service Name: $serviceName" -ForegroundColor Gray
        Write-Host "   You can start it with: net start `"$serviceName`"" -ForegroundColor Gray
        
    } catch {
        Write-Host "⚠️ Failed to configure Windows Service: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   You can still run the application manually" -ForegroundColor Gray
    }
}

# Configure Windows Firewall
Write-Host "🔥 Configuring Windows Firewall..." -ForegroundColor Yellow
try {
    New-NetFirewallRule -DisplayName "OpenAI Codegen Adapter" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -ErrorAction SilentlyContinue
    Write-Host "✅ Firewall rule added for port $Port" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to configure firewall: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create desktop shortcuts
Write-Host "🖥️ Creating desktop shortcuts..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -comObject WScript.Shell
    
    # Desktop shortcut for manual start
    $Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\OpenAI Codegen Adapter.lnk")
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$psStartupPath`""
    $Shortcut.WorkingDirectory = $InstallPath
    $Shortcut.IconLocation = "powershell.exe,0"
    $Shortcut.Description = "Start OpenAI Codegen Adapter"
    $Shortcut.Save()
    
    # Start menu shortcut
    $startMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
    $Shortcut = $WshShell.CreateShortcut("$startMenuPath\OpenAI Codegen Adapter.lnk")
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$psStartupPath`""
    $Shortcut.WorkingDirectory = $InstallPath
    $Shortcut.IconLocation = "powershell.exe,0"
    $Shortcut.Description = "Start OpenAI Codegen Adapter"
    $Shortcut.Save()
    
    Write-Host "✅ Desktop shortcuts created" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to create shortcuts: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final instructions
Write-Host ""
Write-Host "🎉 Installation completed successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Installation Path: $InstallPath" -ForegroundColor Gray
Write-Host "📍 Data Path: $DataPath" -ForegroundColor Gray
Write-Host "📍 Configuration: $configPath" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit the configuration file to add your API keys:" -ForegroundColor White
Write-Host "   $configPath" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the application:" -ForegroundColor White
if ($ServiceMode) {
    Write-Host "   net start `"OpenAI-Codegen-Adapter`"" -ForegroundColor Gray
    Write-Host "   OR use the desktop shortcut" -ForegroundColor Gray
} else {
    Write-Host "   Use the desktop shortcut or run:" -ForegroundColor Gray
    Write-Host "   $psStartupPath" -ForegroundColor Gray
}
Write-Host ""
Write-Host "3. Access the web interface:" -ForegroundColor White
Write-Host "   http://localhost:$Port" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentation: https://github.com/your-repo/open_codegen" -ForegroundColor Gray
Write-Host ""

# Offer to start the service immediately
if ($ServiceMode) {
    $startNow = Read-Host "Would you like to start the service now? (y/N)"
    if ($startNow -eq 'y' -or $startNow -eq 'Y') {
        try {
            Start-Service "OpenAI-Codegen-Adapter"
            Write-Host "✅ Service started successfully!" -ForegroundColor Green
            Write-Host "🌐 Web interface should be available at: http://localhost:$Port" -ForegroundColor Cyan
        } catch {
            Write-Host "❌ Failed to start service: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    $startNow = Read-Host "Would you like to start the application now? (y/N)"
    if ($startNow -eq 'y' -or $startNow -eq 'Y') {
        Write-Host "🚀 Starting OpenAI Codegen Adapter..." -ForegroundColor Cyan
        Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "`"$psStartupPath`""
    }
}

Write-Host ""
Write-Host "Thank you for using OpenAI Codegen Adapter! 🚀" -ForegroundColor Cyan

