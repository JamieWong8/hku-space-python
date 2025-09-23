# PowerShell Setup Script for Startup Deal Evaluator
# This script automates the GitHub deployment process

Write-Host "🚀 Startup Deal Evaluator - GitHub Deployment Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if Git is installed
try {
    $gitVersion = git --version 2>$null
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first:" -ForegroundColor Red
    Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "   Then run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in a Git repository
if (!(Test-Path ".git")) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Already in a Git repository" -ForegroundColor Green
}

# Check Git configuration
$gitName = git config user.name 2>$null
$gitEmail = git config user.email 2>$null

if ([string]::IsNullOrEmpty($gitName) -or [string]::IsNullOrEmpty($gitEmail)) {
    Write-Host ""
    Write-Host "⚙️  Git configuration needed:" -ForegroundColor Yellow
    Write-Host "Please run these commands with your information:" -ForegroundColor Yellow
    Write-Host "   git config --global user.name `"Your Name`"" -ForegroundColor Cyan
    Write-Host "   git config --global user.email `"your.email@example.com`"" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter after configuring Git"
    
    # Re-check configuration
    $gitName = git config user.name 2>$null
    $gitEmail = git config user.email 2>$null
}

Write-Host "✅ Git configuration complete" -ForegroundColor Green
Write-Host "   Name: $gitName" -ForegroundColor White
Write-Host "   Email: $gitEmail" -ForegroundColor White

# Stage all files
Write-Host ""
Write-Host "📁 Adding files to Git..." -ForegroundColor Yellow
git add .
Write-Host "✅ Files staged for commit" -ForegroundColor Green

# Show what will be committed
Write-Host ""
Write-Host "📋 Files to be committed:" -ForegroundColor Cyan
git status --short

# Create initial commit
Write-Host ""
$commitMsg = Read-Host "📝 Enter commit message (or press Enter for default)"
if ([string]::IsNullOrEmpty($commitMsg)) {
    $commitMsg = "Initial commit: Startup Deal Evaluator ML application"
}

git commit -m $commitMsg
Write-Host "✅ Initial commit created" -ForegroundColor Green

# Instructions for GitHub
Write-Host ""
Write-Host "🌟 Next Steps:" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Cyan
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   - Go to: https://github.com/new" -ForegroundColor Yellow
Write-Host "   - Name: startup-deal-evaluator" -ForegroundColor Yellow
Write-Host "   - Description: AI-powered startup investment analysis tool" -ForegroundColor Yellow
Write-Host "   - Make it Public (recommended)" -ForegroundColor Yellow
Write-Host "   - Don't initialize with README/license (we have them)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. After creating the repository, run these commands:" -ForegroundColor White
Write-Host "   (Replace USERNAME with your GitHub username)" -ForegroundColor Yellow
Write-Host ""
Write-Host "   git remote add origin https://github.com/USERNAME/startup-deal-evaluator.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Visit your repository to see your deployed project!" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Your Startup Deal Evaluator is ready for deployment!" -ForegroundColor Green

# Create a reminder file
$deploymentCommands = @"
# GitHub Deployment Commands
# Replace USERNAME with your actual GitHub username

git remote add origin https://github.com/USERNAME/startup-deal-evaluator.git
git branch -M main
git push -u origin main

# After successful push, your project will be live at:
# https://github.com/USERNAME/startup-deal-evaluator
"@

$deploymentCommands | Out-File -FilePath "deployment_commands.txt" -Encoding UTF8

Write-Host "📄 Deployment commands saved to: deployment_commands.txt" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host