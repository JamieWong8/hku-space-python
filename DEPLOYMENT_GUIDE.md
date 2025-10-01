git tag -a v1.0 -m "Version 1.0: Initial release with full ML pipeline"
git push origin v1.0
# 🚀 GitHub Deployment Guide – Deal Scout

This guide walks through publishing the Deal Scout repository, verifying the documentation, and preparing a shareable portfolio artifact.

## 📋 Prerequisites

1. **Git for Windows**
   - Download from <https://git-scm.com/download/win> (64-bit). Accept defaults.
   - Verify installation:
     ```powershell
     git --version
     ```

2. **GitHub account**
   - Create or sign in at <https://github.com/join>.
   - Confirm email to unlock repository creation.

3. **One-time Git identity**
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

## 🔧 Repository Setup (CLI)

Assumes workspace root: `c:\Users\jamie\OneDrive\Documents\Deal Scout` and project sources under `Deal-Scout/` + `flask_app/`.

1. **Initialize Git**
   ```powershell
   cd "c:\Users\jamie\OneDrive\Documents\Deal Scout"
   git init
   git add .
   git commit -m "Initial commit: Deal Scout web platform"
   ```

2. **Create GitHub repository**
   - Navigate to <https://github.com/new>.
   - Suggested name: `deal-scout`.
   - Leave README/.gitignore unchecked (already present locally).

3. **Connect & push**
   ```powershell
   git remote add origin https://github.com/USERNAME/deal-scout.git
   git branch -M main
   git push -u origin main
   ```

## 🌟 Using GitHub Desktop (Optional)

1. Install from <https://desktop.github.com/>.
2. **Add local repo** → choose `c:\Users\jamie\OneDrive\Documents\Deal Scout`.
3. Click **Publish repository**, select `deal-scout`, configure visibility, and publish.

## 📁 Expected Repository Layout

```
Deal Scout/
├── README.md
├── DOCUMENTATION_INDEX.md         # Complete documentation navigation
├── OCTOBER_2025_UPDATES.md       # Latest updates (scoring, performance, UI)
├── FIXES_SUMMARY.md              # Recent bug fixes
├── flask_app/
│   ├── app.py
│   ├── model.py
│   ├── run_web_app.ps1
│   ├── requirements.txt
│   ├── templates/
│   └── static/
├── Deal-Scout/                   # Legacy assets retained for reference
├── docs/
│   ├── project_summary.md
│   ├── technical_specs.md
│   └── user_guide.md
├── DEPLOYMENT_GUIDE.md
├── KAGGLE_INTEGRATION_GUIDE.md
├── KAGGLEHUB_INTEGRATION_COMPLETE.md
└── requirements.txt              # Workspace-level utilities
```

The `flask_app/` directory contains the live web application. `Deal-Scout/` houses historical notebooks and docs from earlier phases—keep for provenance or exclude via `.gitignore` if no longer needed.

## ✅ Post-Push Verification

1. **Repository page** – all files appear with correct casing and folders.
2. **Root README** – renders updated architecture overview with October 2025 tier thresholds (≥65% Invest, 50-64% Monitor, <50% Avoid).
3. **Documentation Index** – check `DOCUMENTATION_INDEX.md` provides clear navigation to all docs.
4. **October Updates** – verify `OCTOBER_2025_UPDATES.md` is accessible and properly formatted.
5. **Documentation** – check `docs/project_summary.md`, `docs/technical_specs.md`, and `docs/user_guide.md` render correctly in-browser.
6. **PowerShell scripts** – confirm `run_web_app.ps1` is tracked (no Windows line-ending issues).
7. **Large files** – ensure no Kaggle datasets or `.model_cache/` artifacts were accidentally committed (should be ignored).

## 📦 Optional Enhancements

- **GitHub Pages** – publish docs quickly:
  1. Settings → Pages → Source: `main` / `/root`.
  2. Add a simple `docs/site/index.html` (already present) to serve as landing page.

- **Repository topics** – improve discoverability: `flask`, `machine-learning`, `investment-analytics`, `kagglehub`, `venture-capital`.

- **Releases** – tag meaningful milestones:
  ```powershell
  git tag -a v1.0.0 -m "First production-ready Deal Scout release"
  git push origin v1.0.0
  ```
  Then create GitHub release notes summarizing features.

- **Actions workflow** – add CI pipeline (`.github/workflows/ci.yml`) running `pytest` and `_tools/smoke_test.py` on push.

## 🔧 Troubleshooting

| Issue | Resolution |
| --- | --- |
| Remote rejects due to large files | Remove `flask_app/.model_cache/` or `kaggle_data/` from history, add to `.gitignore`, recommit. |
| Authentication prompts every push | Create a fine-grained GitHub PAT and use `git credential-manager` or cache credentials: `git config --global credential.helper manager-core`. |
| Wrong repo root | Run `git status` to confirm. If you accidentally initialized inside `flask_app/`, move `.git` to workspace root before retrying. |
| Line ending warnings | Set `git config core.autocrlf true` to normalize Windows line endings. |

## 📣 Sharing & Next Steps

- **Demo instructions** – reference `docs/user_guide.md` for UI walkthrough and `README.md` for quick start.
- **Issue tracking** – enable GitHub Issues for feature requests or bug triage.
- **Security** – before making the repo public, scrub for secrets (run `git secrets --scan` if available) and ensure `kaggle.json` is gitignored.

## 🎉 Congratulations

Once this guide is complete you will have:

✅ A polished GitHub repository showcasing Deal Scout’s modern architecture.  
✅ Updated documentation aligned with the Flask implementation.  
✅ A repeatable bootstrap script (`run_web_app.ps1`) tested on Windows.  
✅ Clear runway for future CI/CD and portfolio demos.

Use the repository link in resumes, investor updates, or client deliverables to highlight both product thinking and engineering execution.