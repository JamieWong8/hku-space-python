# Test Sync Script - Diagnostic Tool
# Run this to diagnose any GitHub sync issues

Write-Host "=== GitHub Sync Diagnostic Tool ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check Git Installation
Write-Host "1. Checking Git installation..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Git found: $gitVersion" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Git not found or not working" -ForegroundColor Red
        Write-Host "   Install from: https://git-scm.com/download/win" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ Git not found: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 2. Check Workspace
Write-Host "2. Checking workspace..." -ForegroundColor Yellow
$workspace = Split-Path -Parent $PSScriptRoot
Write-Host "   Workspace: $workspace" -ForegroundColor White
if (Test-Path $workspace) {
    Write-Host "   ✓ Workspace exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ Workspace not found!" -ForegroundColor Red
}
Set-Location $workspace
Write-Host ""

# 3. Check Git Repository
Write-Host "3. Checking Git repository..." -ForegroundColor Yellow
$isRepo = & git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Git repository initialized" -ForegroundColor Green
    
    # Check current branch
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    Write-Host "   Current branch: $currentBranch" -ForegroundColor White
    
    # Check remotes
    $remotes = git remote -v 2>$null
    if ($remotes) {
        Write-Host "   Remotes configured:" -ForegroundColor White
        $remotes | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
    } else {
        Write-Host "   ⚠ No remotes configured" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠ Not a Git repository (will be initialized on sync)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Check for uncommitted changes
Write-Host "4. Checking for changes..." -ForegroundColor Yellow
if ($isRepo -eq "true") {
    $status = git status --porcelain 2>$null
    if ($status) {
        $changeCount = ($status -split "`n").Count
        Write-Host "   ⚠ Found $changeCount uncommitted changes" -ForegroundColor Yellow
        Write-Host "   (First 10 shown):" -ForegroundColor Gray
        ($status -split "`n") | Select-Object -First 10 | ForEach-Object {
            Write-Host "     $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ✓ No uncommitted changes" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠ Repository not initialized yet" -ForegroundColor Yellow
}
Write-Host ""

# 5. Check GitHub connectivity
Write-Host "5. Checking GitHub connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://github.com" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ Can reach GitHub" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ Cannot reach GitHub: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Check your internet connection" -ForegroundColor Yellow
}
Write-Host ""

# 6. Check repository access
Write-Host "6. Checking repository access..." -ForegroundColor Yellow
$repoUrl = "https://github.com/JamieWong8/hku-space-python.git"
Write-Host "   Repository: $repoUrl" -ForegroundColor White
$lsRemote = git ls-remote $repoUrl 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Can access repository" -ForegroundColor Green
    if ($lsRemote -match "refs/heads/main") {
        Write-Host "   ✓ Main branch exists" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Main branch not found (will be created)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠ Cannot access repository yet" -ForegroundColor Yellow
    Write-Host "   This is normal if:" -ForegroundColor Gray
    Write-Host "     • Repository doesn't exist yet (create it on GitHub)" -ForegroundColor Gray
    Write-Host "     • You haven't authenticated yet (sync script will prompt)" -ForegroundColor Gray
    Write-Host "   Error: $lsRemote" -ForegroundColor DarkGray
}
Write-Host ""

# 7. Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready to sync? Run:" -ForegroundColor Yellow
Write-Host "  .\sync_to_github.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or with custom message:" -ForegroundColor Yellow
Write-Host "  .\sync_to_github.ps1 -CommitMsg `"Your message here`"" -ForegroundColor White
Write-Host ""

# Keep window open
Write-Host "Press any key to close..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
