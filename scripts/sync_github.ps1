param(
    [string]$RepoUrl = 'https://github.com/JamieWong8/hku-space-python.git',
    [string]$Branch = 'main',
    [string]$Workspace = $(Split-Path -Parent $PSScriptRoot),
    [string]$CommitMsg = ""
)

Write-Host "=== GitHub Sync ===" -ForegroundColor Cyan
Write-Host "Repository: $RepoUrl"
Write-Host "Branch: $Branch"
Write-Host "Workspace: $Workspace"
Write-Host ""

Set-Location -LiteralPath $Workspace
Write-Host "Working in: $(Get-Location)" -ForegroundColor Green

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git symbolic-ref HEAD "refs/heads/$Branch" 2>$null | Out-Null
}

$remotes = git remote 2>$null
if ($remotes -contains 'origin') {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}

Write-Host "Fetching from remote..." -ForegroundColor Yellow
git fetch origin 2>&1 | Out-Null

Write-Host "Staging all changes..." -ForegroundColor Yellow
git add -A -f

$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit" -ForegroundColor Yellow
} else {
    if ([string]::IsNullOrWhiteSpace($CommitMsg)) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $CommitMsg = "Sync: $timestamp from $env:COMPUTERNAME"
    }
    Write-Host "Committing: $CommitMsg" -ForegroundColor Yellow
    git commit -m $CommitMsg
}

$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne $Branch) {
    git checkout -B $Branch
}

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin $Branch 2>&1 | Tee-Object -Variable pushOutput | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! Synced to GitHub" -ForegroundColor Green
    Write-Host "View at: https://github.com/JamieWong8/hku-space-python" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Push failed!" -ForegroundColor Red
    Write-Host $pushOutput -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
