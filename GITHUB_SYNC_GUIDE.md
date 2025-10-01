# GitHub Sync Script - Complete Guide

**Upload your Deal Scout workspace to GitHub with one command**

---

## 🚀 Quick Start

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\scripts"
.\sync_to_github.ps1
```

**That's it!** The script handles everything automatically.

---

## ✨ What Just Got Better

### Updated Features (October 2025)

1. **Custom commit messages** - Use `-CommitMsg` parameter
2. **Better output** - Shows repository URL and next steps
3. **Documentation links** - Points to DOCUMENTATION_INDEX.md
4. **Improved safety** - Handles edge cases better

### Script Location

```
Deal Scout/
└── scripts/
    ├── sync_to_github.ps1          ← Main sync script
    ├── README.md                   ← This guide
    └── other scripts...
```

---

## 📋 Usage Examples

### Basic Sync (Default)

```powershell
.\sync_to_github.ps1
```

**Output:**
```
================================================================
Sync to GitHub: https://github.com/JamieWong8/hku-space-python.git (main)
================================================================
Git detected: git version 2.43.0
Workspace: C:\Users\jamie\OneDrive\Documents\Deal Scout
Updated remote 'origin' -> https://github.com/JamieWong8/hku-space-python.git
Fetching from remote...
Staging changes (including ignored files)...
Committed changes: Sync: 2025-10-01 14:30:00 from DESKTOP-ABC123
Pushing to origin/main...
Push complete.
================================================================
Sync finished
================================================================

✅ Your workspace has been synced to GitHub!

Repository: https://github.com/JamieWong8/hku-space-python.git
Branch: main

Next steps:
  • View on GitHub: https://github.com/JamieWong8/hku-space-python
  • Documentation: See DOCUMENTATION_INDEX.md for complete guide
  • Recent changes: See OCTOBER_2025_UPDATES.md
```

### Custom Commit Message

```powershell
.\sync_to_github.ps1 -CommitMsg "Documentation cleanup October 2025"
```

### Different Branch

```powershell
.\sync_to_github.ps1 -Branch dev
```

### Combine Options

```powershell
.\sync_to_github.ps1 -Branch main -CommitMsg "Added scoring updates and cleaned docs"
```

---

## 🎯 What Gets Uploaded

### ✅ Included Files

The script uploads your **entire workspace**:

- **Python code:** All `.py` files including `app.py`, `model.py`
- **Documentation:** All `.md` files (README, guides, updates)
- **Templates:** `flask_app/templates/*.html`
- **Static assets:** CSS, JavaScript, images
- **Configuration:** `requirements.txt`, `.env` (be careful with secrets!)
- **Scripts:** All PowerShell scripts
- **Tests:** All `test_*.py` files

### ⚠️ Large Files to Consider Excluding

**Recommended .gitignore** (create in workspace root):

```gitignore
# Python cache
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Virtual environments (LARGE - don't upload)
venv/
.venv/
env/

# Model cache (LARGE - regenerates automatically)
.model_cache/
flask_app/.model_cache/

# Kaggle data (LARGE - downloads on demand)
flask_app/kaggle_data/

# IDE settings
.vscode/
.idea/
*.swp

# OS files
.DS_Store
Thumbs.db
desktop.ini

# IMPORTANT: Never commit real credentials!
kaggle.json
.env
```

**To create .gitignore:**
```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout"
New-Item -ItemType File -Name ".gitignore" -Force
# Then paste the content above
```

---

## 🔧 Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-RepoUrl` | string | `https://github.com/JamieWong8/hku-space-python.git` | GitHub repository URL |
| `-Branch` | string | `main` | Branch name to push to |
| `-Workspace` | string | Auto-detected | Workspace root path |
| `-CommitMsg` | string | Auto-generated | Custom commit message |

### Parameter Examples

**Change repository:**
```powershell
.\sync_to_github.ps1 -RepoUrl "https://github.com/YourName/different-repo.git"
```

**Specify workspace:**
```powershell
.\sync_to_github.ps1 -Workspace "C:\Projects\Deal Scout"
```

**Everything custom:**
```powershell
.\sync_to_github.ps1 `
    -RepoUrl "https://github.com/YourName/repo.git" `
    -Branch "develop" `
    -CommitMsg "Major update" `
    -Workspace "C:\Projects\Deal Scout"
```

---

## 🔐 First-Time Setup

### 1. Install Git for Windows

If you don't have Git installed:

1. Download: https://git-scm.com/download/win
2. Run installer (accept defaults)
3. Restart PowerShell
4. Verify: `git --version`

### 2. GitHub Authentication

**First push will prompt for credentials:**

1. Git Credential Manager window opens
2. Click "Sign in with your browser"
3. Authorize in browser
4. Done! Credentials saved for future pushes

**Alternative: Personal Access Token**

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control)
4. Copy token
5. Use as password when prompted

### 3. Verify Repository Access

```powershell
# Check remote is configured
git remote -v

# Output should show:
# origin  https://github.com/JamieWong8/hku-space-python.git (fetch)
# origin  https://github.com/JamieWong8/hku-space-python.git (push)
```

---

## 🐛 Troubleshooting

### "Git is not installed or not on PATH"

**Solution:**
```powershell
# 1. Download Git for Windows
# 2. Install (accept defaults)
# 3. Restart PowerShell
# 4. Verify:
git --version
```

### "Authentication failed"

**Solution:**
```powershell
# Clear saved credentials
git credential-manager-core erase https://github.com

# Run sync again (will prompt for login)
.\sync_to_github.ps1
```

### "Remote rejected (repository not found)"

**Possible causes:**
1. Repository doesn't exist → Create it on GitHub first
2. Wrong URL → Check repository name
3. No access → Verify you own the repository

**Solution:**
```powershell
# Create repository on GitHub:
# https://github.com/new

# Then run sync with correct URL:
.\sync_to_github.ps1 -RepoUrl "https://github.com/YourUsername/your-repo.git"
```

### "Push rejected (non-fast-forward)"

**Cause:** Remote has changes you don't have locally

**Solution:**
```powershell
# Script handles this automatically by pulling first
# If manual intervention needed:
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout"
git pull --rebase origin main
.\scripts\sync_to_github.ps1
```

### "Everything up-to-date" but files not on GitHub

**Possible causes:**
1. Files in `.gitignore` (if it exists)
2. Files not staged

**Solution:**
```powershell
# Script uses -f flag to force-add ignored files
# Check what would be committed:
git status
git ls-files
```

---

## 📅 Recommended Workflow

### Daily Development

```powershell
# Morning: Pull latest
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout"
git pull origin main

# During day: Work on code
# ... make changes ...

# Test locally
cd flask_app
.\run_web_app.ps1
# ... verify everything works ...

# End of day: Sync to GitHub
cd ..\scripts
.\sync_to_github.ps1 -CommitMsg "Daily progress: [brief description]"
```

### Major Updates

```powershell
# After completing a feature/fix
cd scripts
.\sync_to_github.ps1 -CommitMsg "Added October 2025 scoring updates (65/50 thresholds)"
```

### Documentation Updates

```powershell
# After updating docs
cd scripts
.\sync_to_github.ps1 -CommitMsg "Updated documentation - removed obsolete files"
```

### Clean Workspace (Like Today!)

```powershell
# After cleanup
cd scripts
.\sync_to_github.ps1 -CommitMsg "Documentation cleanup - consolidated October 2025 updates"
```

---

## ✅ Post-Upload Checklist

After running the script:

1. **Verify on GitHub**
   - Visit: https://github.com/JamieWong8/hku-space-python
   - Check files uploaded correctly
   - Verify README.md renders properly

2. **Check Documentation**
   - DOCUMENTATION_INDEX.md should be visible
   - OCTOBER_2025_UPDATES.md should show recent changes
   - All links should work

3. **Test Clone** (optional)
   ```powershell
   cd C:\Temp
   git clone https://github.com/JamieWong8/hku-space-python.git test-clone
   cd test-clone
   # Verify files present
   ```

4. **Share with Team**
   - Send repository URL
   - Point to DOCUMENTATION_INDEX.md
   - Mention recent updates in OCTOBER_2025_UPDATES.md

---

## 📊 Sync History

You can view your sync history:

```powershell
# View recent commits
git log --oneline -10

# View detailed history
git log -5

# View changes in last commit
git show HEAD
```

---

## 🔄 Advanced Usage

### Undo Last Commit (Before Push)

```powershell
# Undo last commit, keep changes
git reset HEAD~1

# Re-commit with better message
.\sync_to_github.ps1 -CommitMsg "Better description"
```

### Sync Specific Branch

```powershell
# Create and sync to feature branch
.\sync_to_github.ps1 -Branch feature/new-scoring

# Later merge to main on GitHub
```

### Force Push (Dangerous!)

```powershell
# Only if you're sure!
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout"
git push --force origin main
```

---

## 📚 Related Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Complete GitHub setup guide |
| [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) | Navigate all documentation |
| [OCTOBER_2025_UPDATES.md](../OCTOBER_2025_UPDATES.md) | Recent changes to upload |
| [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) | Fast command reference |

---

## 🎓 Git Commands Reference

**Basic commands the script uses:**

```powershell
git init                    # Initialize repository
git remote add origin URL   # Add remote
git add -A -f              # Stage all (force)
git commit -m "message"    # Commit changes
git push origin main       # Push to GitHub
```

**Useful commands:**

```powershell
git status                 # Show current changes
git log                    # View commit history
git pull origin main       # Get latest from GitHub
git branch                 # Show branches
git checkout -b branch     # Create new branch
```

---

## 💡 Pro Tips

1. **Commit often** - Small, frequent commits better than large ones
2. **Good messages** - Describe what changed and why
3. **Test first** - Always test locally before syncing
4. **Review changes** - Run `git status` to see what's staged
5. **Branch strategy** - Use branches for experiments, main for stable code
6. **Backup credentials** - Save your GitHub token somewhere safe

---

## 🆘 Getting Help

**Script Issues:**
```powershell
# Get parameter help
Get-Help .\sync_to_github.ps1 -Detailed

# View script content
Get-Content .\sync_to_github.ps1
```

**Git Issues:**
```powershell
# Git help
git help
git help push
```

**GitHub Issues:**
- Documentation: https://docs.github.com
- GitHub Support: https://support.github.com

**Deal Scout Issues:**
- See: [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- Check: [QUICK_REFERENCE.md](../QUICK_REFERENCE.md)

---

## ✨ Summary

**Your sync script is ready to use!**

```powershell
# Simple three-step workflow:

# 1. Navigate to scripts folder
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\scripts"

# 2. Run sync script
.\sync_to_github.ps1 -CommitMsg "Your description here"

# 3. Verify on GitHub
# Visit: https://github.com/JamieWong8/hku-space-python
```

**Key Features:**
- ✅ One command uploads everything
- ✅ Safe to run multiple times
- ✅ Custom commit messages supported
- ✅ Handles authentication automatically
- ✅ Creates repository if needed
- ✅ Pulls before pushing (avoids conflicts)

**Your workspace is now ready for GitHub! 🎉**

---

**Last Updated:** October 2025  
**Script Version:** 2.0  
**Status:** ✅ Ready to use  
**Next Step:** Run `.\sync_to_github.ps1`
