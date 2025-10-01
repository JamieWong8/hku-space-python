# Scripts Directory

Automation scripts for Deal Scout workspace management.

---

## 📤 sync_to_github.ps1

**Upload your entire workspace to GitHub**

### Quick Start

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\scripts"
.\sync_to_github.ps1
```

### What It Does

1. ✅ Initializes Git repository (if needed)
2. ✅ Configures remote to `https://github.com/JamieWong8/hku-space-python.git`
3. ✅ Stages ALL changes (including normally ignored files)
4. ✅ Creates commit with timestamp
5. ✅ Pushes to `main` branch
6. ✅ Safe to run multiple times

### Usage Examples

**Basic upload:**
```powershell
.\sync_to_github.ps1
```

**Custom commit message:**
```powershell
.\sync_to_github.ps1 -CommitMsg "Added October 2025 updates"
```

**Push to different branch:**
```powershell
.\sync_to_github.ps1 -Branch dev
```

**Change repository:**
```powershell
.\sync_to_github.ps1 -RepoUrl "https://github.com/YourName/your-repo.git"
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-RepoUrl` | `https://github.com/JamieWong8/hku-space-python.git` | GitHub repository URL |
| `-Branch` | `main` | Branch to push to |
| `-Workspace` | Parent of scripts folder | Workspace root path |
| `-CommitMsg` | Auto-generated timestamp | Custom commit message |

### Requirements

- **Git for Windows** - Download from https://git-scm.com/download/win
- **GitHub account** - Sign up at https://github.com
- **Authentication** - Git Credential Manager will prompt for login on first push

### Troubleshooting

**"Git is not installed"**
- Install Git for Windows from https://git-scm.com/download/win
- Restart PowerShell after installation

**"Authentication failed"**
- Sign in when Git Credential Manager prompts
- Or generate Personal Access Token at https://github.com/settings/tokens
- Use token as password when prompted

**"Push rejected"**
- Someone else may have pushed changes
- Script will pull latest and retry automatically

**"Remote already exists"**
- Script handles this automatically
- Updates remote URL if needed

### Files Included

The script uploads EVERYTHING in your workspace:
- ✅ All Python code (`*.py`)
- ✅ All documentation (`*.md`)
- ✅ Configuration files (`.env`, `requirements.txt`)
- ✅ Scripts and tools
- ⚠️ Even `.gitignore` entries (forced with `-f` flag)

**Note:** Cache folders like `.model_cache`, `.venv`, `__pycache__` are large. Consider adding a `.gitignore` file to exclude them:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Virtual environments
venv/
.venv/
env/

# Model cache
.model_cache/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Kaggle credentials (IMPORTANT: never commit real credentials!)
kaggle.json
```

### After First Upload

Once your repository is on GitHub:
1. Visit https://github.com/JamieWong8/hku-space-python
2. Verify files uploaded correctly
3. Check README.md renders properly
4. Review DOCUMENTATION_INDEX.md for navigation

### Subsequent Updates

Just run the script again:
```powershell
.\sync_to_github.ps1 -CommitMsg "Updated scoring thresholds"
```

The script is **idempotent** - safe to run multiple times.

---

## 🔧 Other Scripts

### install_vscode_shell_integration.ps1
Installs VS Code PowerShell integration for terminal features.

### parse_run_web_app.ps1
Analyzes the Flask startup script for debugging.

### number_lines.ps1
Adds line numbers to files for documentation.

---

## 📚 Related Documentation

- **[../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Complete GitHub deployment guide
- **[../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)** - All documentation navigation
- **[../OCTOBER_2025_UPDATES.md](../OCTOBER_2025_UPDATES.md)** - Recent changes to upload

---

## 💡 Tips

### Commit Message Best Practices

**Good commit messages:**
```powershell
.\sync_to_github.ps1 -CommitMsg "Updated tier thresholds to 65/50"
.\sync_to_github.ps1 -CommitMsg "Added October 2025 documentation"
.\sync_to_github.ps1 -CommitMsg "Fixed precompute performance issue"
```

**Auto-generated messages (default):**
```
Sync: 2025-10-01 14:30:00 from DESKTOP-ABC123
```

### Frequency

- **After major changes:** Run immediately
- **Daily development:** Once per day
- **Before demos:** Always sync first
- **After cleanup:** After removing obsolete files (like today!)

### Workflow

```powershell
# 1. Make changes to code/docs
# 2. Test locally
cd flask_app
.\run_web_app.ps1

# 3. Verify changes work
# 4. Sync to GitHub
cd ..\scripts
.\sync_to_github.ps1 -CommitMsg "Description of changes"

# 5. Verify on GitHub
# Open https://github.com/JamieWong8/hku-space-python
```

---

## 🆘 Getting Help

**Script Issues:**
1. Check Git is installed: `git --version`
2. Verify workspace path exists
3. Check GitHub authentication
4. Review error messages

**GitHub Issues:**
1. Visit repository settings
2. Check branch protection rules
3. Verify repository exists
4. Try cloning: `git clone https://github.com/JamieWong8/hku-space-python.git`

**Documentation:**
- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Setup instructions
- [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - All docs
- GitHub Docs: https://docs.github.com

---

**Last Updated:** October 2025  
**Script Version:** 2.0 (Custom commit messages, improved output)  
**Status:** ✅ Ready to use
