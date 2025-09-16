# OpenAI Codegen Adapter - Windows Uninstaller
# This script removes the OpenAI Codegen Adapter installation

param(
    [string]$InstallPath = "$env:ProgramFiles\OpenAI-Codegen-Adapter",
    [string]$DataPath = "$env:LOCALAPPDATA\OpenAI-Codegen-Adapter",
    [switch]$KeepData = $false
)

# Require Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script requires Administrator privileges. Please run as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "🗑️ OpenAI Codegen Adapter - Windows Uninstaller" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red

# Confirm uninstallation
Write-Host ""
Write-Host "⚠️ This will remove the OpenAI Codegen Adapter from your system." -ForegroundColor Yellow
Write-Host "   Installation Path: $InstallPath" -ForegroundColor Gray
Write-Host "   Data Path: $DataPath" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Are you sure you want to continue? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "❌ Uninstallation cancelled." -ForegroundColor Yellow
    exit 0
}

# Stop and remove Windows Service
Write-Host "🛑 Stopping and removing Windows Service..." -ForegroundColor Yellow
$serviceName = "OpenAI-Codegen-Adapter"

try {
    # Check if service exists
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($service) {
        # Stop service if running
        if ($service.Status -eq 'Running') {
            Write-Host "   Stopping service..." -ForegroundColor Gray
            Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
        
        # Remove service using NSSM if available
        $nssmPath = "$InstallPath\nssm.exe"
        if (Test-Path $nssmPath) {
            Write-Host "   Removing service with NSSM..." -ForegroundColor Gray
            & $nssmPath remove $serviceName confirm 2>$null
        } else {
            # Try to remove service using sc.exe
            Write-Host "   Removing service with sc.exe..." -ForegroundColor Gray
            & sc.exe delete $serviceName 2>$null
        }
        
        Write-Host "✅ Windows Service removed" -ForegroundColor Green
    } else {
        Write-Host "   No service found to remove" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️ Failed to remove service: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Remove firewall rules
Write-Host "🔥 Removing Windows Firewall rules..." -ForegroundColor Yellow
try {
    Remove-NetFirewallRule -DisplayName "OpenAI Codegen Adapter" -ErrorAction SilentlyContinue
    Write-Host "✅ Firewall rules removed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to remove firewall rules: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Remove desktop shortcuts
Write-Host "🖥️ Removing desktop shortcuts..." -ForegroundColor Yellow
try {
    $shortcuts = @(
        "$env:PUBLIC\Desktop\OpenAI Codegen Adapter.lnk",
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\OpenAI Codegen Adapter.lnk"
    )
    
    foreach ($shortcut in $shortcuts) {
        if (Test-Path $shortcut) {
            Remove-Item $shortcut -Force
        }
    }
    
    Write-Host "✅ Desktop shortcuts removed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to remove shortcuts: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Remove installation directory
Write-Host "📁 Removing installation directory..." -ForegroundColor Yellow
try {
    if (Test-Path $InstallPath) {
        # Kill any running processes that might be using files
        $processes = Get-Process | Where-Object { $_.Path -like "$InstallPath*" }
        foreach ($process in $processes) {
            Write-Host "   Stopping process: $($process.ProcessName)" -ForegroundColor Gray
            $process | Stop-Process -Force -ErrorAction SilentlyContinue
        }
        
        Start-Sleep -Seconds 2
        
        Remove-Item $InstallPath -Recurse -Force
        Write-Host "✅ Installation directory removed" -ForegroundColor Green
    } else {
        Write-Host "   Installation directory not found" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️ Failed to remove installation directory: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   You may need to manually delete: $InstallPath" -ForegroundColor Gray
}

# Handle data directory
if (-not $KeepData) {
    Write-Host "📊 Removing data directory..." -ForegroundColor Yellow
    
    # Ask for confirmation before removing data
    Write-Host ""
    Write-Host "⚠️ This will permanently delete all application data including:" -ForegroundColor Yellow
    Write-Host "   - Configuration files" -ForegroundColor Gray
    Write-Host "   - Log files" -ForegroundColor Gray
    Write-Host "   - Stored endpoints and websites" -ForegroundColor Gray
    Write-Host "   - Any custom settings" -ForegroundColor Gray
    Write-Host ""
    
    $confirmData = Read-Host "Do you want to delete all data? (y/N)"
    if ($confirmData -eq 'y' -or $confirmData -eq 'Y') {
        try {
            if (Test-Path $DataPath) {
                Remove-Item $DataPath -Recurse -Force
                Write-Host "✅ Data directory removed" -ForegroundColor Green
            } else {
                Write-Host "   Data directory not found" -ForegroundColor Gray
            }
        } catch {
            Write-Host "⚠️ Failed to remove data directory: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "   You may need to manually delete: $DataPath" -ForegroundColor Gray
        }
    } else {
        Write-Host "📦 Data directory preserved at: $DataPath" -ForegroundColor Cyan
        Write-Host "   You can manually delete this later if needed" -ForegroundColor Gray
    }
} else {
    Write-Host "📦 Data directory preserved at: $DataPath" -ForegroundColor Cyan
}

# Clean up registry entries (if any)
Write-Host "🔧 Cleaning up registry entries..." -ForegroundColor Yellow
try {
    # Remove any registry entries that might have been created
    $registryPaths = @(
        "HKLM:\SOFTWARE\OpenAI-Codegen-Adapter",
        "HKCU:\SOFTWARE\OpenAI-Codegen-Adapter"
    )
    
    foreach ($regPath in $registryPaths) {
        if (Test-Path $regPath) {
            Remove-Item $regPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Host "✅ Registry entries cleaned" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to clean registry entries: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final cleanup
Write-Host "🧹 Performing final cleanup..." -ForegroundColor Yellow

# Remove any temporary files
$tempFiles = @(
    "$env:TEMP\python-installer.exe",
    "$env:TEMP\node-installer.msi",
    "$env:TEMP\nssm.zip"
)

foreach ($tempFile in $tempFiles) {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "✅ Cleanup completed" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "🎉 Uninstallation completed!" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""

if ($KeepData -or $confirmData -ne 'y') {
    Write-Host "📦 Your data has been preserved at:" -ForegroundColor Cyan
    Write-Host "   $DataPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   This includes:" -ForegroundColor Gray
    Write-Host "   - Configuration files" -ForegroundColor Gray
    Write-Host "   - Log files" -ForegroundColor Gray
    Write-Host "   - Stored endpoints and websites" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   You can manually delete this directory if you no longer need it." -ForegroundColor Gray
    Write-Host ""
}

Write-Host "✅ OpenAI Codegen Adapter has been successfully removed from your system." -ForegroundColor Green
Write-Host ""
Write-Host "Thank you for using OpenAI Codegen Adapter!" -ForegroundColor Cyan

# Optional: Open data directory if it still exists
if ((Test-Path $DataPath) -and (-not $KeepData -and $confirmData -ne 'y')) {
    $openData = Read-Host "Would you like to open the data directory to review remaining files? (y/N)"
    if ($openData -eq 'y' -or $openData -eq 'Y') {
        Start-Process explorer.exe -ArgumentList $DataPath
    }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

