# 🚀 Deal Scout – Startup Deal Evaluator

An instant-start Flask web application that helps investment teams discover, benchmark, and analyze startups using an ensemble machine learning pipeline, Kaggle-powered data ingestion, and rich diagnostics.

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-production--ready-blue.svg)
![Kaggle](https://img.shields.io/badge/kaggle-integration-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **📘 New to Deal Scout?** Start with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete navigation.  
> **📊 Recent Updates?** See [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) for latest scoring and performance improvements.  
> **⚡ Quick Reference?** Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands and tier thresholds.

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
├── DEPLOYMENT_GUIDE.md        # GitHub + hosting instructions
├── KAGGLE_INTEGRATION_GUIDE.md# Detailed credential setup
├── KAGGLEHUB_INTEGRATION_COMPLETE.md
├── FLASK_CONVERSION_GUIDE.md  # Notebook-to-Flask history and tips
├── startup_deal_evaluator.ipynb (legacy)  # Original notebook for reference only
└── requirements.txt           # Notebook dependency snapshot
```

> The notebook remains in the repo for historical reference; the supported experience is the Flask web application.

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

## 🧠 Machine Learning Pipeline

- **Ensemble classification**: grid-searched RandomForest, HistGradientBoosting, ExtraTrees, Logistic Regression, and soft voting with tuned probability thresholds.
- **Regression models** for funding and valuation recommendations, trained on aligned feature matrices.
- **Feature engineering**: consolidated industry/region groupings, efficiency ratios, log transforms, categorical encodings, and probability tempering to avoid contradictory risk labels.
- **Tier Thresholds (Updated Oct 2025)**: Invest ≥65%, Monitor 50-64%, Avoid <50% - calibrated for realistic VC funnel distribution (25% / 45% / 30%).
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

Refer to:

- `KAGGLE_INTEGRATION_GUIDE.md` – API token setup, directory structure.
- `KAGGLEHUB_INTEGRATION_COMPLETE.md` – Operational checklist when running on Kaggle notebooks/VMs.

---

## 🧪 Tooling & Scripts

| Script | Location | Purpose |
| --- | --- | --- |
| `run_web_app.ps1` | `flask_app/` | One-click setup and launch on Windows (venv, deps, env vars). |
| `start_server.ps1` / `.sh` | `flask_app/` | Production-style launcher without installer logic. |
| `_tools/smoke_test.py` & friends | `flask_app/_tools/` | Smoke tests, data verification utilities. |
| `setup_deployment.ps1` / `.sh` | repo root | Helpers for packaging and deployment scaffolding. |

---

## 📚 Documentation Map

- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** ⭐ **Complete navigation guide** to all documentation
- **[OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md)** - Latest scoring, performance, and UI updates
- [User Guide](docs/user_guide.md) – How to use the web UI, company explorer, and analysis workflows.
- [Technical Specs](docs/technical_specs.md) – Architecture diagrams, feature engineering, ML configuration.
- [Project Summary](docs/project_summary.md) – Executive overview for stakeholders.
- [Deployment Guide](DEPLOYMENT_GUIDE.md) – GitHub publishing, Docker/Gunicorn/Waitress notes, CI hooks.
- [Flask Conversion Guide](FLASK_CONVERSION_GUIDE.md) – Migration notes from the original notebook.
- [Fixes Summary](FIXES_SUMMARY.md) – Recent bug fixes and improvements.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Run smoke tests and linting (`pytest`, `python -m compileall`, etc.).
4. Submit a pull request referencing updated documentation or test coverage.

> Contributions should preserve the instant-start defaults, keep probability tempering coherent, and include documentation updates when surfaces change.

---

## 📜 License & Attribution

Licensed under the MIT License – see [LICENSE](LICENSE).

Built with:

- Flask, Jinja2, and Bootstrap for the web layer
- pandas, scikit-learn, seaborn, matplotlib for analytics
- KaggleHub for dataset access and caching

---

## 🛣️ Roadmap Highlights

- Enhanced multi-model ensembles with time-series drift monitoring.
- Streaming data connectors (Crunchbase Live, PitchBook APIs, etc.).
- Enterprise SSO, role-based access, and audit logging.
- Front-end componentization (React/Vue) backed by the existing REST APIs.
- Expanded admin console with cache status, training controls, and queue metrics.

Have feedback or questions? Open an issue or reach out through the project discussion board.

---

**If Deal Scout saves your diligence team time, we’d love a ⭐ on GitHub.**