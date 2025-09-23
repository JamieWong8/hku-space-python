#!/bin/bash
# Quick Setup Script for Startup Deal Evaluator
# This script automates the GitHub deployment process

echo "🚀 Startup Deal Evaluator - GitHub Deployment Setup"
echo "=================================================="

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   Download from: https://git-scm.com/download/win"
    echo "   Then run this script again."
    exit 1
fi

echo "✅ Git is installed: $(git --version)"

# Check if we're in a Git repository
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Already in a Git repository"
fi

# Check Git configuration
if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
    echo ""
    echo "⚙️  Git configuration needed:"
    echo "Please run these commands with your information:"
    echo "   git config --global user.name \"Your Name\""
    echo "   git config --global user.email \"your.email@example.com\""
    echo ""
    read -p "Press Enter after configuring Git..."
fi

echo "✅ Git configuration complete"
echo "   Name: $(git config user.name)"
echo "   Email: $(git config user.email)"

# Stage all files
echo ""
echo "📁 Adding files to Git..."
git add .
echo "✅ Files staged for commit"

# Show what will be committed
echo ""
echo "📋 Files to be committed:"
git status --short

# Create initial commit
echo ""
read -p "📝 Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Initial commit: Startup Deal Evaluator ML application"
fi

git commit -m "$commit_msg"
echo "✅ Initial commit created"

# Instructions for GitHub
echo ""
echo "🌟 Next Steps:"
echo "=============="
echo "1. Create a new repository on GitHub:"
echo "   - Go to: https://github.com/new"
echo "   - Name: startup-deal-evaluator"
echo "   - Description: AI-powered startup investment analysis tool"
echo "   - Make it Public (recommended)"
echo "   - Don't initialize with README/license (we have them)"
echo ""
echo "2. After creating the repository, run these commands:"
echo "   (Replace USERNAME with your GitHub username)"
echo ""
echo "   git remote add origin https://github.com/USERNAME/startup-deal-evaluator.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Visit your repository to see your deployed project!"
echo ""
echo "🎉 Your Startup Deal Evaluator is ready for deployment!"

# Create a reminder file
cat > deployment_commands.txt << EOF
# GitHub Deployment Commands
# Replace USERNAME with your actual GitHub username

git remote add origin https://github.com/USERNAME/startup-deal-evaluator.git
git branch -M main
git push -u origin main

# After successful push, your project will be live at:
# https://github.com/USERNAME/startup-deal-evaluator
EOF

echo "📄 Deployment commands saved to: deployment_commands.txt"