# ==========================================
# 🔧 Install ngrok - Manual Installation
# ==========================================
# Downloads and installs ngrok CLI for Windows

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  ngrok Manual Installer          " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Define paths
$downloadUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
$tempZip = "$env:TEMP\ngrok.zip"
$installDir = "$env:USERPROFILE\ngrok"
$ngrokExe = "$installDir\ngrok.exe"

# Step 1: Download ngrok
Write-Host "Step 1/4: Downloading ngrok..." -ForegroundColor Cyan
try {
    $ProgressPreference = 'SilentlyContinue'  # Speed up download
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip
    Write-Host "   Downloaded successfully" -ForegroundColor Green
} catch {
    Write-Host "   Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please download manually from:" -ForegroundColor Yellow
    Write-Host "   https://ngrok.com/download" -ForegroundColor White
    exit 1
}

Write-Host ""

# Step 2: Extract ngrok
Write-Host "Step 2/4: Extracting ngrok..." -ForegroundColor Cyan
try {
    # Create install directory
    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir | Out-Null
    }
    
    # Extract ZIP
    Expand-Archive -Path $tempZip -DestinationPath $installDir -Force
    
    Write-Host "   Extracted to: $installDir" -ForegroundColor Green
} catch {
    Write-Host "   Extraction failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Add to PATH
Write-Host "Step 3/4: Adding ngrok to PATH..." -ForegroundColor Cyan
try {
    # Get current user PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    # Check if already in PATH
    if ($currentPath -notlike "*$installDir*") {
        # Add to PATH
        $newPath = "$currentPath;$installDir"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        
        # Update current session PATH
        $env:Path = "$env:Path;$installDir"
        
        Write-Host "   Added to PATH" -ForegroundColor Green
    } else {
        Write-Host "   Already in PATH" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   Could not add to PATH automatically" -ForegroundColor Yellow
    Write-Host "   Please add manually: $installDir" -ForegroundColor White
}

Write-Host ""

# Step 4: Verify installation
Write-Host "Step 4/4: Verifying installation..." -ForegroundColor Cyan
try {
    # Refresh PATH in current session
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path","Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path","User")
    $env:Path = "$machinePath;$userPath"
    
    # Test ngrok command
    $version = & "$ngrokExe" version 2>&1
    Write-Host "   ngrok installed successfully!" -ForegroundColor Green
    Write-Host "   Version: $version" -ForegroundColor White
} catch {
    Write-Host "   Installation complete but verification failed" -ForegroundColor Yellow
    Write-Host "   You may need to restart PowerShell for PATH changes to take effect" -ForegroundColor White
}

Write-Host ""

# Cleanup
Write-Host "Cleaning up..." -ForegroundColor Cyan
Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
Write-Host "   Temporary files removed" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation Complete!            " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Installation Location:" -ForegroundColor Cyan
Write-Host "   $installDir" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Close and reopen PowerShell (to refresh PATH)" -ForegroundColor White
Write-Host "   2. Run: start_ngrok.ps1" -ForegroundColor Yellow
Write-Host "   3. Or manually configure ngrok with your auth token" -ForegroundColor White
Write-Host ""

Write-Host "Quick Test:" -ForegroundColor Cyan
Write-Host "   Run in a NEW PowerShell window:" -ForegroundColor White
Write-Host "   ngrok version" -ForegroundColor Yellow
Write-Host ""

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
