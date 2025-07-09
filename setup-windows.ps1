#!/usr/bin/env powershell
<#
.SYNOPSIS
    Codegen AI Proxy - Windows Setup Script
.DESCRIPTION
    Automatically sets up and runs the Codegen AI Proxy on Windows using Docker
.EXAMPLE
    .\setup-windows.ps1 -CodegenApiKey "your-api-key"
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$CodegenOrgId = "",
    
    [Parameter(Mandatory=$false)]
    [string]$CodegenToken = "",
    
    [Parameter(Mandatory=$false)]
    [string]$SystemMessage = "You are a helpful AI assistant.",
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 8000,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDockerCheck
)

# Colors for output
$Red = [System.ConsoleColor]::Red
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Blue = [System.ConsoleColor]::Blue

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($message) { Write-ColorOutput $Green "✅ $message" }
function Write-Error($message) { Write-ColorOutput $Red "❌ $message" }
function Write-Warning($message) { Write-ColorOutput $Yellow "⚠️  $message" }
function Write-Info($message) { Write-ColorOutput $Blue "ℹ️  $message" }

Write-Info "🚀 Codegen AI Proxy - Windows Setup"
Write-Info "=================================="

# Check if Docker is installed and running
if (-not $SkipDockerCheck) {
    Write-Info "Checking Docker installation..."
    
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker found: $dockerVersion"
        } else {
            throw "Docker not found"
        }
    } catch {
        Write-Error "Docker is not installed or not in PATH"
        Write-Info "Please install Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    # Check if Docker is running
    try {
        docker ps 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker is running"
        } else {
            throw "Docker not running"
        }
    } catch {
        Write-Error "Docker is not running"
        Write-Info "Please start Docker Desktop and try again"
        exit 1
    }
}

# Get Codegen credentials if not provided
if ([string]::IsNullOrEmpty($CodegenOrgId)) {
    Write-Info "Codegen Organization ID is required"
    $CodegenOrgId = Read-Host "Please enter your Codegen Organization ID (e.g., 323)"
    
    if ([string]::IsNullOrEmpty($CodegenOrgId)) {
        Write-Error "Organization ID is required to continue"
        exit 1
    }
}

if ([string]::IsNullOrEmpty($CodegenToken)) {
    Write-Info "Codegen API Token is required"
    $CodegenToken = Read-Host "Please enter your Codegen API Token (sk-...)"
    
    if ([string]::IsNullOrEmpty($CodegenToken)) {
        Write-Error "API Token is required to continue"
        exit 1
    }
}

# Check if port is available
Write-Info "Checking if port $Port is available..."
$portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Warning "Port $Port is already in use"
    $newPort = Read-Host "Enter a different port number (default: 8001)"
    if (-not [string]::IsNullOrEmpty($newPort)) {
        $Port = [int]$newPort
    } else {
        $Port = 8001
    }
}

Write-Success "Using port: $Port"

# Create .env file
Write-Info "Creating configuration..."
$envContent = @"
CODEGEN_ORG_ID=$CodegenOrgId
CODEGEN_TOKEN=$CodegenToken
CODEGEN_BASE_URL=https://api.codegen.com
DEFAULT_SYSTEM_MESSAGE=$SystemMessage
LOG_LEVEL=INFO
LOG_REQUESTS=true
HOST=0.0.0.0
WORKERS=1
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Success "Configuration saved to .env"

# Create docker-compose override for Windows
$dockerComposeOverride = @"
version: '3.8'
services:
  codegen-proxy:
    ports:
      - "$Port`:8000"
    environment:
      - CODEGEN_ORG_ID=$CodegenOrgId
      - CODEGEN_TOKEN=$CodegenToken
      - DEFAULT_SYSTEM_MESSAGE=$SystemMessage
"@

$dockerComposeOverride | Out-File -FilePath "docker-compose.override.yml" -Encoding UTF8

# Stop any existing container
Write-Info "Stopping any existing containers..."
docker-compose down 2>$null

# Build and start the container
Write-Info "Building and starting Codegen AI Proxy..."
try {
    docker-compose up -d --build
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Codegen AI Proxy started successfully!"
    } else {
        throw "Failed to start container"
    }
} catch {
    Write-Error "Failed to start the proxy"
    Write-Info "Check the logs with: docker-compose logs"
    exit 1
}

# Wait a moment for the service to start
Start-Sleep -Seconds 5

# Test the service
Write-Info "Testing the proxy..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:$Port/health" -Method Get -TimeoutSec 10
    if ($response.status -eq "healthy") {
        Write-Success "Proxy is healthy and responding!"
    } else {
        Write-Warning "Proxy responded but status is: $($response.status)"
    }
} catch {
    Write-Warning "Could not connect to proxy, but it may still be starting up"
}

# Display success information
Write-Success "🎉 Setup Complete!"
Write-Info ""
Write-Info "📡 Your Codegen AI Proxy is running at:"
Write-ColorOutput $Green "   http://localhost:$Port"
Write-Info ""
Write-Info "🔗 API Endpoints:"
Write-Info "   OpenAI:    http://localhost:$Port/v1/chat/completions"
Write-Info "   Anthropic: http://localhost:$Port/v1/messages"
Write-Info "   Gemini:    http://localhost:$Port/v1/models/gemini-pro:generateContent"
Write-Info ""
Write-Info "💡 Usage Example:"
Write-ColorOutput $Yellow @"
   import openai
   openai.api_base = "http://localhost:$Port/v1"
   openai.api_key = "any-key"
   # Your existing code works unchanged!
"@
Write-Info ""
Write-Info "🌐 Web UI: http://localhost:$Port"
Write-Info ""
Write-Info "📋 Management Commands:"
Write-Info "   View logs:    docker-compose logs -f"
Write-Info "   Stop proxy:   docker-compose down"
Write-Info "   Restart:      docker-compose restart"
Write-Info ""

# Offer to open browser
$openBrowser = Read-Host "Open web UI in browser? (y/N)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:$Port"
}

Write-Success "Setup completed successfully! 🚀"
