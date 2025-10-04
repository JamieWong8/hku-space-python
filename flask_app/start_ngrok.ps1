# ===========================================
# 🚀 Deal Scout - ngrok Deployment Script
# ===========================================
# Automated deployment to ngrok for public access
# Usage: .\start_ngrok.ps1

# Set error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Failure { param($msg) Write-Host $msg -ForegroundColor Red }

# Clear screen
Clear-Host

Write-Host ""
Write-Host "=================================" -ForegroundColor Magenta
Write-Host "  🚀 Deal Scout ngrok Deployer  " -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta
Write-Host ""

# -----------------------
# Step 1: Check ngrok installation
# -----------------------
Write-Info "📋 Step 1/5: Checking ngrok installation..."

$ngrokInstalled = $false
try {
    $ngrokVersion = & ngrok version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ngrokInstalled = $true
        Write-Success "   ✅ ngrok is installed: $ngrokVersion"
    }
} catch {
    $ngrokInstalled = $false
}

if (-not $ngrokInstalled) {
    Write-Failure "   ❌ ngrok is NOT installed"
    Write-Host ""
    Write-Warning "   Installation Options:"
    Write-Host ""
    Write-Host "   Option 1: Chocolatey (Recommended)" -ForegroundColor White
    Write-Host "   ----------------------------------------"
    Write-Host "   choco install ngrok -y" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Option 2: Scoop" -ForegroundColor White
    Write-Host "   ----------------------------------------"
    Write-Host "   scoop install ngrok" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Option 3: Manual Download" -ForegroundColor White
    Write-Host "   ----------------------------------------"
    Write-Host "   1. Download from: https://ngrok.com/download" -ForegroundColor Gray
    Write-Host "   2. Extract ngrok.exe to a folder in PATH" -ForegroundColor Gray
    Write-Host "   3. Or place in: C:\Windows\System32\" -ForegroundColor Gray
    Write-Host ""
    
    $install = Read-Host "   Would you like to install ngrok via Chocolatey? (y/n)"
    if ($install -eq 'y') {
        Write-Info "   Installing ngrok via Chocolatey..."
        
        # Check if Chocolatey is installed
        $chocoInstalled = $false
        try {
            & choco --version | Out-Null
            $chocoInstalled = $true
        } catch {
            $chocoInstalled = $false
        }
        
        if (-not $chocoInstalled) {
            Write-Warning "   Chocolatey is not installed. Installing Chocolatey first..."
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            
            # Refresh environment
            $env:ChocolateyInstall = Convert-Path "$((Get-Command choco).Path)\..\.."
            Import-Module "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
            refreshenv
        }
        
        # Install ngrok
        choco install ngrok -y
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Success "   ✅ ngrok installed successfully!"
    } else {
        Write-Failure "   ❌ Cannot proceed without ngrok. Please install manually and run again."
        exit 1
    }
}

Write-Host ""

# -----------------------
# Step 2: Configure auth token
# -----------------------
Write-Info "📋 Step 2/5: Configuring ngrok auth token..."

$authToken = "33adT18UpEgZsio7QsTk2hL0eIR_6dU1kNTrWrUQagBvqGFKR"

try {
    & ngrok config add-authtoken $authToken 2>&1 | Out-Null
    Write-Success "   ✅ Auth token configured successfully"
} catch {
    Write-Failure "   ❌ Failed to configure auth token: $_"
    exit 1
}

Write-Host ""

# -----------------------
# Step 3: Check Flask app
# -----------------------
Write-Info "📋 Step 3/5: Checking Flask app..."

$flaskPort = 5000
$flaskRunning = $false

try {
    $connection = Get-NetTCPConnection -LocalPort $flaskPort -ErrorAction SilentlyContinue
    if ($connection) {
        $flaskRunning = $true
        Write-Success "   ✅ Flask app is already running on port $flaskPort"
    }
} catch {
    $flaskRunning = $false
}

if (-not $flaskRunning) {
    Write-Warning "   ⚠️  Flask app is NOT running"
    Write-Info "   Starting Flask app..."
    
    # Get the script directory (flask_app folder)
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    
    # Start Flask in a new window
    $flaskProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; python app.py" -PassThru -WindowStyle Normal
    
    Write-Success "   ✅ Flask app started (PID: $($flaskProcess.Id))"
    Write-Info "   Waiting 10 seconds for Flask to initialize..."
    Start-Sleep -Seconds 10
}

Write-Host ""

# -----------------------
# Step 4: Start ngrok tunnel
# -----------------------
Write-Info "📋 Step 4/5: Starting ngrok tunnel..."

# Check if ngrok is already running
$ngrokRunning = Get-Process -Name ngrok -ErrorAction SilentlyContinue

if ($ngrokRunning) {
    Write-Warning "   ⚠️  ngrok is already running"
    $restart = Read-Host "   Would you like to restart it? (y/n)"
    if ($restart -eq 'y') {
        Stop-Process -Name ngrok -Force
        Start-Sleep -Seconds 2
        Write-Success "   ✅ Stopped existing ngrok process"
    } else {
        Write-Info "   Using existing ngrok tunnel..."
        Write-Host ""
        Write-Success "✅ Deployment check complete!"
        Write-Host ""
        Write-Host "Access your app:" -ForegroundColor Cyan
        Write-Host "  • Local:  http://127.0.0.1:5000" -ForegroundColor White
        Write-Host "  • ngrok:  Check ngrok web interface at http://127.0.0.1:4040" -ForegroundColor White
        Write-Host ""
        exit 0
    }
}

# Start ngrok in a new window
Write-Info "   Launching ngrok..."
$ngrokProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http $flaskPort" -PassThru -WindowStyle Normal

Write-Success "   ✅ ngrok tunnel started (PID: $($ngrokProcess.Id))"
Write-Info "   Waiting 5 seconds for ngrok to establish connection..."
Start-Sleep -Seconds 5

Write-Host ""

# -----------------------
# Step 5: Get ngrok URL
# -----------------------
Write-Info "📋 Step 5/5: Retrieving public URL..."

try {
    # Try to get URL from ngrok API
    $maxRetries = 5
    $retryCount = 0
    $ngrokUrl = $null
    
    while ($retryCount -lt $maxRetries -and -not $ngrokUrl) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -Method Get -ErrorAction SilentlyContinue
            if ($response.tunnels -and $response.tunnels.Count -gt 0) {
                $ngrokUrl = $response.tunnels[0].public_url
                break
            }
        } catch {
            $retryCount++
        }
    }
    
    if ($ngrokUrl) {
        Write-Success "   ✅ Public URL retrieved successfully!"
    } else {
        Write-Warning "   ⚠️  Could not auto-retrieve URL (ngrok may still be initializing)"
        Write-Info "   Check manually at: http://127.0.0.1:4040"
    }
} catch {
    Write-Warning "   ⚠️  Could not retrieve URL automatically: $_"
    Write-Info "   Check manually at: http://127.0.0.1:4040"
}

Write-Host ""
Write-Host ""

# -----------------------
# Success Summary
# -----------------------
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ✅ Deployment Successful!              " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 Access Your App:" -ForegroundColor Cyan
Write-Host "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
if ($ngrokUrl) {
    Write-Host "   🌍 Public URL:  " -NoNewline -ForegroundColor White
    Write-Host $ngrokUrl -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   📋 Copy and share this URL with anyone!" -ForegroundColor Gray
} else {
    Write-Host "   🌍 Public URL:  " -NoNewline -ForegroundColor White
    Write-Host "Check at http://127.0.0.1:4040" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "   🏠 Local URL:   " -NoNewline -ForegroundColor White
Write-Host "http://127.0.0.1:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "   📊 ngrok Web:   " -NoNewline -ForegroundColor White
Write-Host "http://127.0.0.1:4040" -ForegroundColor Yellow
Write-Host ""

Write-Host ""
Write-Host "📱 Features:" -ForegroundColor Cyan
Write-Host "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "   ✅ HTTPS enabled automatically" -ForegroundColor Gray
Write-Host "   ✅ Accessible from any device" -ForegroundColor Gray
Write-Host "   ✅ Real-time request logs" -ForegroundColor Gray
Write-Host "   ✅ Request inspector available" -ForegroundColor Gray
Write-Host ""

Write-Host ""
Write-Host "⚡ Quick Actions:" -ForegroundColor Cyan
Write-Host "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "   🌐 Open Public URL:     " -NoNewline -ForegroundColor Gray
if ($ngrokUrl) {
    Write-Host "start $ngrokUrl" -ForegroundColor White
    
    # Ask if user wants to open in browser
    $openBrowser = Read-Host "   Would you like to open the URL in your browser? (y/n)"
    if ($openBrowser -eq 'y') {
        Start-Process $ngrokUrl
        Write-Success "   ✅ Browser opened!"
    }
} else {
    Write-Host "Check web interface first" -ForegroundColor White
}
Write-Host ""
Write-Host "   📊 Open Web Interface:  " -NoNewline -ForegroundColor Gray
Write-Host "start http://127.0.0.1:4040" -ForegroundColor White
Write-Host ""
Write-Host "   🛑 Stop Deployment:     " -NoNewline -ForegroundColor Gray
Write-Host "Press Ctrl+C in ngrok/Flask terminals" -ForegroundColor White
Write-Host ""

Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "   • Changes to Flask code will auto-reload" -ForegroundColor Gray
Write-Host "   • URL is public - anyone can access it" -ForegroundColor Gray
Write-Host "   • Free tier URL changes on each restart" -ForegroundColor Gray
Write-Host "   • Monitor traffic at http://127.0.0.1:4040" -ForegroundColor Gray
Write-Host "   • Upgrade to Pro for persistent URL" -ForegroundColor Gray
Write-Host ""

Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "   📖 Full Guide:  " -NoNewline -ForegroundColor Gray
Write-Host "NGROK_DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "   🆘 Troubleshooting:  " -NoNewline -ForegroundColor Gray
Write-Host "See guide for common issues" -ForegroundColor White
Write-Host ""

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Ask if user wants to open web interface
$openWeb = Read-Host "Would you like to open the ngrok web interface? (y/n)"
if ($openWeb -eq 'y') {
    Start-Process "http://127.0.0.1:4040"
    Write-Success "✅ Web interface opened!"
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
