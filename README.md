# 🚀 Deal> **📘 New to Deal Scout?** Start with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete navigation.  
> **🚀 Quick Start?** See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) to get started in 2 minutes!  
> **🔄 How It Works?** Read [flask_app/WORKFLOW_SIMPLE.md](flask_app/WORKFLOW_SIMPLE.md) for plain-English explanation or [flask_app/WORKFLOW_GUIDE.md](flask_app/WORKFLOW_GUIDE.md) for technical details!  
> **🌐 Public Deployment?** Check [flask_app/NGROK_DEPLOYMENT_GUIDE.md](flask_app/NGROK_DEPLOYMENT_GUIDE.md) to deploy via ngrok in minutes!out – Startup Deal Evaluator

An instant-start Flask web application that helps investment teams discover, benchmark, and analyze startups using an ensemble machine learning pipeline, Kaggle-powered data ingestion, and rich diagnostics.

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-production--ready-blue.svg)
![Kaggle](https://img.shields.io/badge/kaggle-integration-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **📘 New to Deal Scout?** Start with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete navigation.  
> **🚀 Quick Start?** See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) to get started in 2 minutes!  
> **� Public Deployment?** Check [flask_app/NGROK_DEPLOYMENT_GUIDE.md](flask_app/NGROK_DEPLOYMENT_GUIDE.md) to deploy via ngrok in minutes!  
> **�🏗️ Tech Stack?** Read [TECH_STACK.md](TECH_STACK.md) for comprehensive technology overview and [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) for visual diagrams.  
> **📊 Recent Updates?** Check [PRECOMPUTE_MESSAGE_FIX.md](PRECOMPUTE_MESSAGE_FIX.md) and [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md) for latest improvements.  
> **🎨 Visualizations?** See [VISUALIZATION_ENHANCEMENTS.md](VISUALIZATION_ENHANCEMENTS.md) for details on our enhanced analytics dashboard.  
> **⚡ Quick Reference?** Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands and tier thresholds.  
> **📓 Interactive Notebook?** Try [Deal_Scout_Interactive.ipynb](Deal_Scout_Interactive.ipynb) for Jupyter-based exploration! See [JUPYTER_NOTEBOOK_GUIDE.md](JUPYTER_NOTEBOOK_GUIDE.md) for details.

---

## 🎯 What’s Inside

- **Responsive web UI** with company catalog, tier filters, and a full-screen deal analysis workspace.
- **REST + diagnostics APIs** for company search (`/api/companies`), deep dives, admin cache workflows, and health probes.
- **Instant-start ML runtime** that boots in seconds, warms in the background, and persists models/tier precomputes to disk.
- **KaggleHub + offline data pipeline** with automatic credential discovery, cached `investments_VC.csv` failsafes, and synthetic fallbacks.
- **PowerShell + shell tooling** for reproducible startup (`run_web_app.ps1`), smoke tests, and automation scripts.

---

## 🧭 Architecture Snapshot

```
Deal Scout
├── flask_app/
│   ├── app.py                 # Flask routes, API, admin diagnostics
│   ├── model.py               # ML pipeline, Kaggle ingestion, caching
│   ├── templates/             # Jinja2 templates (index, error, admin banner)
│   ├── static/                # CSS/JS/assets for the UI
│   ├── run_web_app.ps1        # Instant-start bootstrap script (Windows)
│   ├── start_server.ps1/.sh   # Deployment helpers
│   └── requirements.txt       # Runtime dependencies
├── docs/                      # Product + technical documentation
│   ├── user_guide.md          # UI walkthrough
│   ├── technical_specs.md     # ML + system design reference
│   └── project_summary.md     # Executive summary
├── Deal_Scout_Interactive.ipynb  # 📓 NEW: Interactive Jupyter Notebook
├── JUPYTER_NOTEBOOK_GUIDE.md     # 📓 Notebook documentation & usage
├── notebook_requirements.txt     # Notebook-specific dependencies
├── DEPLOYMENT_GUIDE.md        # GitHub + hosting instructions
├── KAGGLE_INTEGRATION_GUIDE.md# Detailed credential setup
├── KAGGLEHUB_INTEGRATION_COMPLETE.md
├── FLASK_CONVERSION_GUIDE.md  # Notebook-to-Flask history and tips
├── startup_deal_evaluator.ipynb (legacy)  # Original notebook for reference only
└── requirements.txt           # Flask app dependency snapshot
```

> The Flask web application is the primary supported experience. The new **Deal_Scout_Interactive.ipynb** provides an alternative interactive notebook environment with live widgets and visualizations.

---

## ⚙️ Getting Started

### 1. Launch with the PowerShell Bootstrap (Windows)

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\run_web_app.ps1
```

The script will:

- Ensure Python is present and create a local virtual environment (unless `USE_VENV=0`).
- Install pinned dependencies.
- Enable the instant-start defaults (fast bootstrap, lazy training, probability tempering, caching).
- Auto-load Kaggle credentials from `flask_app/kaggle.json` when available.
- Launch the Flask development server on http://localhost:5000 with auto-reload enabled.

### 2. Manual Setup (Cross-platform)

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
set FLASK_ENV=development
set AUTO_TRAIN_ON_IMPORT=false
python app.py
```

> For macOS/Linux replace the PowerShell commands with the equivalent `source venv/bin/activate` workflow and environment exports.

---

## 🌐 Web Experience

- **Company Explorer:** Paginated grid with search, raw/normalized industry filters, region filters, funding round, success status, and attractiveness tier selectors (Invest ≥65%, Monitor 50-64%, Avoid <50%). Tiers are precomputed for instant filtering.
- **Deal Analysis Modal:** One-click deep dive per company, component score breakdowns, radar charts, risk factors, and investment commentary.
- **Admin Banner:** Quick links for Kaggle status, data source, tier precompute triggers, and cache clearing.
- **Diagnostics Overlay:** `/__debug/info`, `/__routes`, and `/api/diagnostics/*` endpoints surface build IDs, cache health, and score distribution audits.
- **Instant-start workflows:** Background training keeps the UI responsive; tier score caches persist across restarts.

---

## 🌐 Public Deployment with ngrok

Deploy your local Flask app to a public URL in minutes using ngrok:

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\start_ngrok.ps1
```

**Features:**
- ✅ Public HTTPS URL (e.g., `https://your-app.ngrok-free.dev`)
- ✅ Share with anyone instantly
- ✅ No deployment infrastructure required
- ✅ Real-time traffic monitoring
- ✅ Works on mobile devices

**Documentation:**
- **Complete Guide:** [flask_app/NGROK_DEPLOYMENT_GUIDE.md](flask_app/NGROK_DEPLOYMENT_GUIDE.md)
- **Quick Reference:** [flask_app/NGROK_QUICK_REF.md](flask_app/NGROK_QUICK_REF.md)
- **Setup Complete:** [flask_app/NGROK_DEPLOYMENT_COMPLETE.md](flask_app/NGROK_DEPLOYMENT_COMPLETE.md)

> **Note:** ngrok creates temporary public URLs. Free tier URLs change on each restart. Upgrade to Pro for persistent domains.

---

## 🧠 Machine Learning Pipeline

- **Ensemble classification**: grid-searched RandomForest, HistGradientBoosting, ExtraTrees, Logistic Regression, and soft voting with tuned probability thresholds. Achieves 60-75% accuracy.
- **Regression models** for funding and valuation recommendations (R² typically 80-85%), trained on aligned feature matrices.
- **Feature engineering**: 44+ features including consolidated industry/region groupings, efficiency ratios, log transforms, categorical encodings, and probability calibration.
- **Stricter Scoring (Schema 2025-10-01-stricter-tiers)**:
  - Success probability: 70% weight, mapped (0.25-0.85) → (0-1) for higher selectivity
  - Lower base rates: operating companies 28% (was 40%)
  - Hard gating: sp<0.40 caps at 49 (Avoid), sp<0.50 caps at 64 (Monitor)
  - Distribution normalization DISABLED to allow natural scoring
- **Tier Thresholds**: Invest ≥65, Monitor 50-64, Avoid <50 (raised from 60/45 for selectivity)
- **Expected Distribution**: ~10-20% Invest, ~30-40% Monitor, ~40-60% Avoid (natural from strict scoring)
- **Performance**: Fast bootstrap (<1s) + background training (10-30s); cached models load instantly on restart
- **Caching strategy**: model artifacts + tier precomputes stored under `flask_app/.model_cache/` with SHA-based signatures; admin endpoints manage lifecycle.

---

## 📡 API Surface

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/companies` | GET | Company catalog with pagination, search, filters, and optional tier constraint. |
| `/api/companies/<company_id>` | GET | Raw company metrics + derived efficiency ratios. |
| `/api/companies/<company_id>/analyze` | GET | Full ML analysis package with charts, component scores, and risk flags. |
| `/api/companies/compare` | POST | Batch comparison for selected company IDs. |
| `/api/companies/analyze` | POST | Batch ML analysis (JSON payload of IDs). |
| `/api/data-source` | GET | Data provenance (synthetic vs Kaggle) and dataset health. |
| `/api/diagnostics/*` | GET | Training status, score distribution, coherence audits. |
| `/api/admin/precompute` | POST | Force tier precomputation; optional cache persistence toggle. |
| `/api/admin/cache/clear` | POST | Drop analysis caches in-memory and/or on disk. |
| `/__routes`, `/__debug/info` | GET | Runtime insight into registered routes and template state. |
| `/health`, `/api/test-*` | GET | Health check and smoke endpoints. |

> Legacy notebook endpoints such as `/api/evaluate` are no longer part of the supported API surface.

---

## 📊 Data Sources & Kaggle Integration

- **Default:** Synthetic dataset generated at boot for environments without credentials.
- **KaggleHub:** Automatic download of `arindam235/startup-investments-crunchbase`; cached to `flask_app/kaggle_data/` for offline re-use.
- **Credential discovery:** Environment variables `KAGGLE_USERNAME`/`KAGGLE_KEY` or `flask_app/kaggle.json`.
- **Fallback:** Bundled `investments_VC.csv` used when Kaggle requests fail or rate-limit.



## 🧪 Tooling & Scripts

| Script | Location | Purpose |
| --- | --- | --- |
| `run_web_app.ps1` | `flask_app/` | One-click setup and launch on Windows (venv, deps, env vars). |




---

## 📜 License & Attribution

Licensed under the MIT License – see [LICENSE](LICENSE).

Built with:

- Flask, Jinja2, and Bootstrap for the web layer
- pandas, scikit-learn, seaborn, matplotlib for analytics
- KaggleHub for dataset access and caching

