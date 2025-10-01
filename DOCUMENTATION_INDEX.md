# Deal Scout Documentation Index

**Quick Navigation:** Complete guide to all documentation in the Deal Scout workspace.

---

## 📖 Getting Started

**Start here if you're new to Deal### "How do I...?"

- **...install and run the app?** → [README.md](README.md) or [flask_app/README.md](flask_app/README.md)
- **...upload to GitHub?** → [GITHUB_SYNC_GUIDE.md](GITHUB_SYNC_GUIDE.md) or run `scripts\sync_to_github.ps1`
- **...set up Kaggle credentials?** → [KAGGLE_INTEGRATION_GUIDE.md](KAGGLE_INTEGRATION_GUIDE.md)
- **...understand the UI?** → [docs/user_guide.md](docs/user_guide.md)
- **...understand the scoring system?** → [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md)
- **...deploy to production?** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **...debug issues?** → [flask_app/README.md](flask_app/README.md) troubleshooting section

1. **[README.md](README.md)** - Main project overview, features, quick start guide
2. **[flask_app/README.md](flask_app/README.md)** - Flask application documentation, API reference, troubleshooting
3. **[docs/user_guide.md](docs/user_guide.md)** - Step-by-step UI walkthrough for end users

---

## 🚀 Setup & Deployment

**Installation, configuration, and deployment guides:**

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - GitHub publishing, Docker, Gunicorn/Waitress, CI/CD
- **[GITHUB_SYNC_GUIDE.md](GITHUB_SYNC_GUIDE.md)** ⭐ - Complete guide to sync_to_github.ps1 script
- **[KAGGLE_INTEGRATION_GUIDE.md](KAGGLE_INTEGRATION_GUIDE.md)** - Kaggle API credentials, dataset setup
- **[scripts/](scripts/)** - Automation scripts:
  - `sync_to_github.ps1` - Upload all files to GitHub (see GITHUB_SYNC_GUIDE.md)
  - `README.md` - Scripts documentation
  - `install_vscode_shell_integration.ps1` - VS Code integration
  - `parse_run_web_app.ps1` - Script analysis tool

---

## 🔧 Technical Documentation

**Architecture, APIs, and system design:**

- **[docs/technical_specs.md](docs/technical_specs.md)** - ML architecture, feature engineering, system diagrams
- **[docs/project_summary.md](docs/project_summary.md)** - Executive summary for stakeholders
- **[flask_app/MODERNIZATION_SUMMARY.md](flask_app/MODERNIZATION_SUMMARY.md)** - Flask conversion history and improvements

---

## 📊 Recent Updates (October 2025)

**Latest changes to scoring, performance, and UI:**

- **[OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md)** ⭐ **COMPREHENSIVE** - All October updates in one place:
  - Scoring threshold changes (65/50 vs 60/45)
  - Precompute optimization (400 rows)
  - UI consistency fixes
  - Distribution normalization (25% / 45% / 30%)
  - Frontend-backend synchronization
  
- **[FIXES_SUMMARY.md](FIXES_SUMMARY.md)** - October 1, 2025 fixes (Analysis Modal 404, Kaggle dataset loading)

---

## 🛠️ Operational Guides

**Day-to-day usage and maintenance:**

### Running the Application

```powershell
# Quick start (Windows)
cd flask_app
.\run_web_app.ps1

# Manual start
python app.py

# Trigger tier precomputation
python trigger_precompute.py
```

### Environment Variables

Key configuration flags (see [flask_app/README.md](flask_app/README.md) for complete list):

- `PRECOMPUTE_MAX_ROWS=400` - Startup precompute limit (default: 400)
- `AUTO_TRAIN_ON_IMPORT=false` - Skip training on module import
- `CACHE_MODELS=true` - Enable model/tier caching
- `SKIP_KAGGLE=true` - Force synthetic dataset

### Kaggle Integration

- **[KAGGLEHUB_INTEGRATION_COMPLETE.md](KAGGLEHUB_INTEGRATION_COMPLETE.md)** - Kaggle notebook/VM operational checklist
- **Dataset:** `arindam235/startup-investments-crunchbase`
- **Credentials:** `flask_app/kaggle.json` or environment variables

---

## 🧪 Testing & Diagnostics

**Verification scripts and tools:**

### Diagnostic Scripts (flask_app/_tools/)

- `smoke_test.py` - Lightweight endpoint checks
- `verify_funding_and_valuation.py` - Data validation
- `diagnose_model_import.py` - Model loading diagnostics
- `check_precompute_limit.py` - Verify precompute configuration
- `test_score_distribution.py` - Analyze score distributions

### Test Suites

- `flask_app/test_*.py` - Pytest test modules:
  - `test_flask.py` - Flask app tests
  - `test_routes.py` - API endpoint tests
  - `test_analysis.py` - ML analysis tests
  - `test_pipeline.py` - Pipeline integration tests
  - `test_kagglehub.py` - Kaggle integration tests

### API Diagnostics Endpoints

```
GET /__debug/info           - Template/build diagnostics
GET /__routes               - Registered routes
GET /api/diagnostics/training-status
GET /api/diagnostics/score-distribution
GET /api/diagnostics/coherence-audit
```

---

## 📝 Historical Documentation

**Legacy guides and conversion notes:**

- **[FLASK_CONVERSION_GUIDE.md](FLASK_CONVERSION_GUIDE.md)** - Notebook-to-Flask migration history
- **[startup_deal_evaluator.ipynb](startup_deal_evaluator.ipynb)** - Original notebook (reference only, not actively maintained)

---

## 🎯 Key Reference Information

### Current Tier Thresholds (Updated Oct 2025)

| Tier | Score Range | Distribution |
|------|-------------|--------------|
| **Invest** | ≥65% | ~25% of companies |
| **Monitor** | 50-64% | ~45% of companies |
| **Avoid** | <50% | ~30% of companies |

**Why these thresholds?**  
Calibrated to match real-world VC funnel patterns with realistic selectivity.

### Precompute Configuration

- **Default:** 400 rows (~30-60 second startup)
- **Previous:** 2000 rows (~2-5 minute startup)
- **Full dataset:** Computed in background after training

### API Overview

| Endpoint | Description |
|----------|-------------|
| `/api/companies` | Company catalog with filters |
| `/api/companies/<id>/analyze` | Deep dive analysis |
| `/api/admin/precompute` | Trigger tier computation |
| `/api/admin/cache/clear` | Clear analysis caches |
| `/api/data-source` | Dataset provenance info |

---

## 🗂️ Documentation by Category

### For End Users
1. [docs/user_guide.md](docs/user_guide.md) - UI walkthrough
2. [README.md](README.md) - Project overview
3. [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) - Latest changes

### For Developers
1. [docs/technical_specs.md](docs/technical_specs.md) - Architecture
2. [flask_app/README.md](flask_app/README.md) - API reference
3. [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) - Recent code changes
4. [flask_app/MODERNIZATION_SUMMARY.md](flask_app/MODERNIZATION_SUMMARY.md) - Evolution history

### For DevOps
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment strategies
2. [KAGGLE_INTEGRATION_GUIDE.md](KAGGLE_INTEGRATION_GUIDE.md) - External dependencies
3. [flask_app/README.md](flask_app/README.md) - Environment configuration
4. [scripts/](scripts/) - Automation scripts

### For Stakeholders
1. [docs/project_summary.md](docs/project_summary.md) - Executive overview
2. [README.md](README.md) - Feature highlights
3. [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) - Recent improvements

---

## 🔍 Finding What You Need

### "How do I...?"

- **...install and run the app?** → [README.md](README.md) or [flask_app/README.md](flask_app/README.md)
- **...set up Kaggle credentials?** → [KAGGLE_INTEGRATION_GUIDE.md](KAGGLE_INTEGRATION_GUIDE.md)
- **...understand the UI?** → [docs/user_guide.md](docs/user_guide.md)
- **...understand the scoring system?** → [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md)
- **...deploy to production?** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **...debug issues?** → [flask_app/README.md](flask_app/README.md) troubleshooting section
- **...upload to GitHub?** → Use `scripts/sync_to_github.ps1`

### "What changed recently?"

- **Full details:** [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) ⭐
- **Quick summary:**
  - Stricter tier thresholds (Invest ≥65%)
  - Faster startup (400-row precompute)
  - UI consistency (frontend-backend sync)
  - Success probability removed from modal

### "I need technical details about..."

- **ML models:** [docs/technical_specs.md](docs/technical_specs.md)
- **API endpoints:** [flask_app/README.md](flask_app/README.md)
- **Feature engineering:** [docs/technical_specs.md](docs/technical_specs.md)
- **Caching strategy:** [flask_app/README.md](flask_app/README.md)

---

## 📁 File Organization

```
Deal Scout/
├── README.md                          # Main entry point
├── DOCUMENTATION_INDEX.md             # This file
├── OCTOBER_2025_UPDATES.md           # Recent changes (comprehensive)
├── FIXES_SUMMARY.md                  # October 1 fixes
├── DEPLOYMENT_GUIDE.md               # Deployment guide
├── KAGGLE_INTEGRATION_GUIDE.md       # Kaggle setup
├── KAGGLEHUB_INTEGRATION_COMPLETE.md # Kaggle VM guide
├── FLASK_CONVERSION_GUIDE.md         # Migration history
├── LICENSE                           # MIT License
│
├── flask_app/
│   ├── README.md                     # Flask app documentation
│   ├── MODERNIZATION_SUMMARY.md      # App evolution history
│   ├── app.py                        # Main Flask application
│   ├── model.py                      # ML models and scoring
│   ├── run_web_app.ps1              # Quick start script
│   ├── trigger_precompute.py        # Manual precompute tool
│   ├── requirements.txt              # Python dependencies
│   ├── test_*.py                    # Test suites
│   └── _tools/                      # Diagnostic scripts
│
├── docs/
│   ├── user_guide.md                # End-user documentation
│   ├── technical_specs.md           # Technical architecture
│   └── project_summary.md           # Executive summary
│
└── scripts/
    ├── sync_to_github.ps1           # GitHub upload script
    └── ...                          # Other automation
```

---

## 🆘 Quick Troubleshooting

### Common Issues

1. **Slow startup** → Check `PRECOMPUTE_MAX_ROWS` (should be 400)
2. **Tier mismatch** → Verify October 2025 updates applied (65/50 thresholds)
3. **Kaggle errors** → Check credentials in `flask_app/kaggle.json`
4. **Empty tier filter** → Wait for training to complete
5. **Cache issues** → Use `/api/admin/cache/clear` endpoint

### Verification Commands

```powershell
# Check score distribution
curl http://localhost:5000/api/diagnostics/score-distribution

# Check training status
curl http://localhost:5000/api/diagnostics/training-status

# Trigger precompute
curl -X POST http://localhost:5000/api/admin/precompute
```

---

## 📞 Support Resources

- **Documentation Issues:** Open GitHub issue with doc filename
- **Technical Questions:** See [flask_app/README.md](flask_app/README.md) troubleshooting
- **API Questions:** Check `/api/diagnostics/*` endpoints first
- **Recent Changes:** Review [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md)

---

## 🔄 Keeping Documentation Updated

When making changes, update:
1. Relevant technical docs ([README.md](README.md), [flask_app/README.md](flask_app/README.md))
2. This index if adding new files
3. [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) or create new dated summary

---

**Last Updated:** October 2025  
**Total Documentation Files:** 15+ markdown files  
**Recommended Starting Point:** [README.md](README.md) → [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) → Your specific topic
