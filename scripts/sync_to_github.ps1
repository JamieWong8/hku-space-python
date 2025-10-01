# Sync Deal Scout Workspace to GitHub
# Stages, commits (if changes), and pushes to the configured remote/branch.
# Safe to run repeatedly. Handles first-time init and empty remote.
#
# Usage:
#   .\sync_to_github.ps1                    # Use defaults
#   .\sync_to_github.ps1 -Branch dev        # Push to different branch
#   .\sync_to_github.ps1 -CommitMsg "..."   # Custom commit message
#
# Documentation: See DEPLOYMENT_GUIDE.md and DOCUMENTATION_INDEX.md

[CmdletBinding()]
param(
    # GitHub repository to push to (default: your repo)
    [string]$RepoUrl = 'https://github.com/JamieWong8/hku-space-python.git',
    # Branch name to use
    [string]$Branch = 'main',
    # Workspace root (default: parent of this script's folder)
    [string]$Workspace = $(Split-Path -Parent $PSScriptRoot),
    # Optional custom commit message
    [string]$CommitMsg = ""
)

$ErrorActionPreference = 'Continue'  # Changed from 'Stop' to prevent silent exits
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Trap errors to prevent silent closure
trap {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

function Write-Header($text) {
    $line = ''.PadLeft(60,'=')
    Write-Host $line -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
}

Write-Header "Sync to GitHub: $RepoUrl ($Branch)"

# 1) Verify Git is installed
try {
    $gitVersion = git --version 2>$null
    if (-not $gitVersion) { throw "git not found" }
    Write-Host "Git detected: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not on PATH. Install Git for Windows first:" -ForegroundColor Red
    Write-Host " https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# 2) Move to workspace root (supports spaces in path)
if (-not (Test-Path -LiteralPath $Workspace)) {
    Write-Host "ERROR: Workspace path not found: $Workspace" -ForegroundColor Red
    exit 1
}
Set-Location -LiteralPath $Workspace
Write-Host "Workspace: $(Get-Location)" -ForegroundColor Green

# 3) Initialize repo if needed
$insideRepo = $false
& git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { $insideRepo = $true }

if (-not $insideRepo) {
    Write-Host "Initializing new Git repository..." -ForegroundColor Yellow
    git init | Out-Null
    # Set HEAD to desired branch name before first commit (no-op if already set)
    git symbolic-ref HEAD "refs/heads/$Branch" 2>$null | Out-Null
}

# 4) Do NOT create or use .gitignore here; commit absolutely everything requested by user

# 5) Configure remote 'origin' to desired URL
$remotes = (git remote 2>$null) -split "\r?\n" | Where-Object { $_ }
if ($remotes -contains 'origin') {
    git remote set-url origin $RepoUrl | Out-Null
    Write-Host "Updated remote 'origin' -> $RepoUrl" -ForegroundColor Green
} else {
    git remote add origin $RepoUrl | Out-Null
    Write-Host "Added remote 'origin' -> $RepoUrl" -ForegroundColor Green
}

# 6) Try to fetch and fast-forward/rebase from remote branch if it exists
Write-Host "Fetching from remote..." -ForegroundColor Yellow
$fetchResult = git fetch origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Fetch had issues: $fetchResult" -ForegroundColor Yellow
    Write-Host "Continuing with local changes..." -ForegroundColor Yellow
}

$remoteHasBranch = $false
$ls = git ls-remote --heads origin $Branch 2>&1
if ($LASTEXITCODE -eq 0 -and $ls) { 
    $remoteHasBranch = $true 
    Write-Host "Remote branch '$Branch' found." -ForegroundColor Green
}

if ($remoteHasBranch) {
    Write-Host "Checking for remote updates..." -ForegroundColor Yellow
    # Check if we're behind remote
    $localCommit = git rev-parse HEAD 2>$null
    $remoteCommit = git rev-parse "origin/$Branch" 2>$null
    
    if ($localCommit -and $remoteCommit -and $localCommit -ne $remoteCommit) {
        Write-Host "Remote has new commits; attempting merge..." -ForegroundColor Yellow
        $mergeResult = git merge "origin/$Branch" --no-edit 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Warning: Could not merge remote changes automatically." -ForegroundColor Yellow
            Write-Host "Details: $mergeResult" -ForegroundColor DarkGray
            Write-Host "Your local changes will be committed on top of current state." -ForegroundColor Yellow
        } else {
            Write-Host "Merged remote changes successfully." -ForegroundColor Green
        }
    } else {
        Write-Host "Already up to date with remote." -ForegroundColor Green
    }
}

# 7) Stage changes (force-add to include files normally ignored)
Write-Host "Staging changes (including ignored files)..." -ForegroundColor Yellow
git add -A -f

# 8) Commit only if there are staged changes
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit." -ForegroundColor DarkYellow
} else {
    # Use custom message if provided, otherwise generate timestamp-based message
    if ([string]::IsNullOrWhiteSpace($CommitMsg)) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $hostname  = $env:COMPUTERNAME
        $CommitMsg = "Sync: $timestamp from $hostname"
    }
    Write-Host "Creating commit: $CommitMsg" -ForegroundColor Yellow
    $commitResult = git commit -m $CommitMsg 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Committed changes successfully" -ForegroundColor Green
    } else {
        Write-Host "Warning: Commit had issues: $commitResult" -ForegroundColor Yellow
    }
}

# 9) Ensure branch name and push
try {
    # If current branch isn't $Branch, switch or create it
    $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($currentBranch -ne $Branch) {
        git checkout -B $Branch | Out-Null
    }
} catch {
    # In detached HEAD or brand-new repo without commits, set branch name explicitly
    git symbolic-ref HEAD "refs/heads/$Branch" 2>$null | Out-Null
}

Write-Host "Pushing to origin/$Branch..." -ForegroundColor Yellow
$pushResult = git push -u origin $Branch 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Push complete!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Push failed!" -ForegroundColor Red
    Write-Host "Details: $pushResult" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "  1. Authenticate: Git Credential Manager should prompt for login" -ForegroundColor White
    Write-Host "  2. Check repository exists: https://github.com/JamieWong8/hku-space-python" -ForegroundColor White
    Write-Host "  3. Verify permissions: You must have write access to the repository" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Header "Sync finished"

Write-Host ""
Write-Host "✅ Your workspace has been synced to GitHub!" -ForegroundColor Green
Write-Host ""
Write-Host "Repository: $RepoUrl" -ForegroundColor Cyan
Write-Host "Branch: $Branch" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  • View on GitHub: https://github.com/JamieWong8/hku-space-python" -ForegroundColor White
Write-Host "  • Documentation: See DOCUMENTATION_INDEX.md for complete guide" -ForegroundColor White
Write-Host "  • Recent changes: See OCTOBER_2025_UPDATES.md" -ForegroundColor White
Write-Host ""

# Keep window open so user can see the output
Write-Host "Press any key to close..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
