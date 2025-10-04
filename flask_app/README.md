# Deal Scout Flask Applicationgunicorn -w 4 -b 0.0.0.0:5000 app:app

pip install waitress

This directory hosts the Deal Scout web application: a production-ready Flask stack with instant-start ML models, cached diagnostics, and Kaggle-aware data ingestion.# Deal Scout Flask Application



---This directory hosts the Deal Scout web application: a product| Symp| Symptom | Suggested Checks |

| --- | --- |

## 🛠️ Quick Launch| Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated, inspect logs for Kaggle download delays. Current default: 400 rows for ~30-60s startup. |

| Tier filter returns empty list | Wait for training to complete (tiers auto-precompute after training), verify `precomputed_*` columns exist, inspect `/api/diagnostics/score-distribution`. |

### Windows (recommended)| High probability but "Avoid" tier | Check `/api/diagnostics/coherence-audit` and adjust `PROB_TEMPER_*` env vars if needed. Note: New thresholds are Invest ≥65%, Monitor 50-64%, Avoid <50%. |

| Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity; fallback uses cached CSV. |

```powershell| Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). |uggested Checks |

cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"| --- | --- |

.\run_web_app.ps1| Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated, inspect logs for Kaggle download delays. |

```| Tier filter returns empty list | Wait for training to complete (tiers auto-precompute after training), verify `precomputed_*` columns exist, inspect `/api/diagnostics/score-distribution`. |

| High probability but "Avoid" tier | Check `/api/diagnostics/coherence-audit` and adjust `PROB_TEMPER_*` env vars if needed. |

The bootstrap script will:| Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity; fallback uses cached CSV. |

| Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). |dy Flask stack with instant-start ML models, cached diagnostics, and Kaggle-aware data ingestion.

- Create/activate `venv/` (unless `USE_VENV=0`)

- Install pinned dependencies via `requirements.txt`---

- Set instant-start environment defaults (`AUTO_TRAIN_ON_IMPORT=false`, `BOOTSTRAP_FAST=true`, etc.)

- Source Kaggle credentials from `kaggle.json` if present## 🛠️ Quick Launch

- Launch the Flask dev server on http://localhost:5000

### Windows (recommended)

### Manual setup (cross-platform)

```powershell

```powershellcd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"

python -m venv venv.\run_web_app.ps1

.\venv\Scripts\Activate.ps1   # macOS/Linux: source venv/bin/activate```

pip install --upgrade pip

pip install -r requirements.txtThe bootstrap script will:

set FLASK_ENV=development

set AUTO_TRAIN_ON_IMPORT=false- Create/activate `venv/` (unless `USE_VENV=0`).

python app.py- Install pinned dependencies via `requirements.txt`.

```- Set instant-start environment defaults (`AUTO_TRAIN_ON_IMPORT=false`, `BOOTSTRAP_FAST=true`, etc.).

- Source Kaggle credentials from `kaggle.json` if present.

Optional environment toggles:- Launch the Flask dev server on http://localhost:5000.



- `KAGGLE_MAX_ROWS=400` – limit data loading rows for faster startup (default: 400, was 2000 - **5x speedup**)### Manual setup (cross-platform)

- `PRECOMPUTE_MAX_ROWS=400` – limit initial precompute rows (default: 400)

- `CACHE_MODELS=false` – bypass on-disk model cache```powershell

- `SKIP_KAGGLE=true` – force synthetic dataset even when credentials existpython -m venv venv

- `FORCE_RETRAIN=true` – bypass model cache and force retraining.\venv\Scripts\Activate.ps1   # macOS/Linux: source venv/bin/activate

pip install --upgrade pip

---pip install -r requirements.txt

set FLASK_ENV=development

## 🧭 Application Layoutset AUTO_TRAIN_ON_IMPORT=false

python app.py

``````

flask_app/

├── app.py                 # Flask routes, REST + diagnostics endpointsOptional environment toggles:

├── model.py               # ML pipeline, Kaggle ingestion, caching, precompute

├── templates/- `PRECOMPUTE_MAX_ROWS=400` – limit initial precompute rows for faster warmup (default: 400 rows for 30-60s startup).

│   ├── index.html         # Main UI- `CACHE_MODELS=false` – bypass on-disk model cache.

│   ├── error.html         # Error page- `SKIP_KAGGLE=true` – force synthetic dataset even when credentials exist.

│   └── ...

├── static/---

│   ├── css/

│   ├── js/## 🧭 Application Layout

│   └── images/

├── run_web_app.ps1        # Windows bootstrapper```

├── start_server.ps1/.sh   # Minimal launch scripts for deploymentsflask_app/

├── requirements.txt       # Runtime dependencies├── app.py                 # Flask routes, REST + diagnostics endpoints

├── kaggle_data/           # Cached Kaggle datasets (created on demand)├── model.py               # ML pipeline, Kaggle ingestion, caching, precompute

├── .model_cache/          # Persisted model + tier artifacts (created on demand)├── templates/

└── _tools/                # Smoke tests, diagnostics helpers│   ├── index.html         # Main UI

```│   ├── error.html         # Error page

│   └── ...

---├── static/

│   ├── css/

## 🌐 Core Features│   ├── js/

│   └── images/

- **Company Explorer:** `/api/companies` powers the UI catalog with pagination, search, consolidated industry groups, regions, funding rounds, status, and tier filtering. Investment tiers use stricter thresholds (Invest ≥65, Monitor 50-64, Avoid <50) producing realistic VC distributions (~50%+ in Avoid tier).├── run_web_app.ps1        # Windows bootstrapper

- **Fast Data Loading:** Configurable `KAGGLE_MAX_ROWS=400` (default) loads **5x faster** than previous 2000-row default. Startup time: ~1-2 seconds with cached models.├── start_server.ps1/.sh   # Minimal launch scripts for deployments

- **Strict Scoring (Schema 2025-10-01-stricter-tiers):**├── requirements.txt       # Runtime dependencies

  - Success probability dominates (70% weight) with stricter normalization├── kaggle_data/           # Cached Kaggle datasets (created on demand)

  - Lower base rates (28% vs 40% for operating companies)├── .model_cache/          # Persisted model + tier artifacts (created on demand)

  - Hard gating prevents mediocre companies from high scores└── _tools/                # Smoke tests, diagnostics helpers

  - Distribution normalization DISABLED for natural scoring```

- **Deal Analysis Modal:** `/api/companies/<id>/analyze` returns component scores, business fundamentals radar, risk commentary, and chart payloads.

- **Admin Utilities:**---

  - `/api/admin/precompute` – manually trigger tier precomputation (auto-runs after training)

  - `/api/admin/cache/clear` – drop analysis caches in memory/disk## 🌐 Core Features

  - `/api/data-source` – confirm Kaggle/synthetic dataset provenance

- **Diagnostics:** `/__debug/info`, `/__routes`, `/api/diagnostics/*` provide build IDs, cache status, score distributions, and coherence audits.- **Company Explorer:** `/api/companies` powers the UI catalog with pagination, search, consolidated industry groups, regions, funding rounds, status, and tier filtering. Investment tiers use stricter thresholds (Invest ≥65%, Monitor 50-64%, Avoid <50%) calibrated for realistic VC funnel distribution.

- **Instant-start ML:** Fast bootstrap (<1s) serves UI immediately; background training (10-30s) completes with automatic tier precomputation. Accurate status messages show tier distribution.- **Deal Analysis Modal:** `/api/companies/<id>/analyze` returns component scores, business fundamentals radar, risk commentary, and chart payloads.

- **Admin Utilities:**

---  - `/api/admin/precompute` – warm attractiveness tiers and persist to cache (default: 400 rows for fast startup).

  - `/api/admin/cache/clear` – drop analysis caches in memory/disk.

## 🔌 Key Environment Flags  - `/api/data-source` – confirm Kaggle/synthetic dataset provenance.

- **Diagnostics:** `/__debug/info`, `/__routes`, `/api/diagnostics/*` provide build IDs, cache status, score distributions, and coherence audits.

| Variable | Default | Description |- **Instant-start ML:** background threads continue training while the UI remains responsive; probability tempering ensures tier labels align with displayed probabilities.

| --- | --- | --- |

| `AUTO_TRAIN_ON_IMPORT` | `false` | Skip heavyweight model training during module import. |---

| `BOOTSTRAP_FAST` | `true` | Use lightweight bootstrap models (<1s startup) until background training finishes. |

| `LAZY_BACKGROUND_TRAIN` | `true` | Spawn background training thread post-startup (10-30s). |## 🔌 Key Environment Flags

| `KAGGLE_MAX_ROWS` | `400` | Row limit for Kaggle data loading (**5x faster** than old 2000 default). |

| `PRECOMPUTE_MAX_ROWS` | `400` | Row cap for tier precomputation (matches data loading for consistency). || Variable | Default | Description |

| `CACHE_MODELS` | `true` | Persist/load models and tiers under `.model_cache/`. || --- | --- | --- |

| `FORCE_RETRAIN` | `false` | Bypass model cache and force retraining. || `AUTO_TRAIN_ON_IMPORT` | `false` | Skip heavyweight model training during module import. |

| `SHRINK_PROBABILITY_INTERACTIVE` | `true` | Apply conservative probability shrinkage in interactive mode. || `BOOTSTRAP_FAST` | `true` | Use lightweight bootstrap models until background training finishes. |

| `SKIP_KAGGLE` | `false` | Force synthetic data even when credentials exist. || `LAZY_BACKGROUND_TRAIN` | `true` | Spawn background training thread post-startup. |

| `KAGGLE_USERNAME`, `KAGGLE_KEY` | n/a | API credentials when not using `kaggle.json`. || `PRECOMPUTE_MAX_ROWS` | `400` | Row cap for initial precompute (optimized for 30-60s startup). |

| `CACHE_MODELS` | `true` | Persist/load models and tiers under `.model_cache/`. |

**Note:** Tier precomputation now happens automatically after both bootstrap and full model training with accurate status messages showing tier distribution (e.g., "✅ Auto-precompute completed: 400 companies scored"). No manual triggers needed!| `PROB_TEMPER_*` | See script | Temper probability outputs to avoid contradictory tiers. |

| `SKIP_KAGGLE` | `false` | Force synthetic data by default. |

Environment variables may be set in the shell or ahead of script execution:| `KAGGLE_USERNAME`, `KAGGLE_KEY` | n/a | API credentials when not using `kaggle.json`. |



```powershell**Note:** Tier precomputation now happens automatically after both bootstrap and full model training, eliminating the need for manual precompute triggers. The training banner and manual precompute controls have been removed from the UI for a cleaner experience.

$env:KAGGLE_MAX_ROWS = '400'

$env:CACHE_MODELS = 'true'Environment variables may be set in the shell or ahead of script execution:

.\run_web_app.ps1

``````powershell

$env:PRECOMPUTE_MAX_ROWS = '400'

---$env:CACHE_MODELS = 'true'

.\run_web_app.ps1

## 📡 REST + Diagnostics API```



| Endpoint | Method | Purpose |---

| --- | --- | --- |

| `/api/companies` | GET | Catalog with filters: page, per_page, search, industry, industry_group, region, funding_round, status, tier (Invest/Monitor/Avoid: 65/50 thresholds). |## 📡 REST + Diagnostics API

| `/api/companies/<company_id>` | GET | Raw metrics + derived efficiency ratios. |

| `/api/companies/<company_id>/analyze` | GET | Full analysis package with component scores and chart data. || Endpoint | Method | Purpose |

| `/api/companies/analyze` | POST | Batch analysis – payload `{ "company_ids": [...] }`. || --- | --- | --- |

| `/api/companies/compare` | POST | Return raw metrics for side-by-side comparison. || `/api/companies` | GET | Catalog with filters: page, per_page, search, industry, industry_group, region, funding_round, status, tier (Invest/Monitor/Avoid: 65/50 thresholds). |

| `/api/data-source` | GET | Indicates synthetic vs Kaggle dataset and dataset health stats. || `/api/companies/<company_id>` | GET | Raw metrics + derived efficiency ratios. |

| `/api/diagnostics/training-status` | GET | Background training + cache status. || `/api/companies/<company_id>/analyze` | GET | Full analysis package with component scores and chart data. |

| `/api/diagnostics/score-distribution` | GET | Summary stats for attractiveness scores (see tier distribution). || `/api/companies/analyze` | POST | Batch analysis – payload `{ "company_ids": [...] }`. |

| `/api/diagnostics/coherence-audit` | GET | Detect mismatches between tiers and probabilities. || `/api/companies/compare` | POST | Return raw metrics for side-by-side comparison. |

| `/api/admin/precompute` | POST | Trigger tier precompute (`{"max_rows": int, "save_to_disk": bool}`). Default: 400 rows. || `/api/data-source` | GET | Indicates synthetic vs Kaggle dataset and dataset health stats. |

| `/api/admin/cache/clear` | POST | Clear caches (`{"disk": bool, "scope": "all"}`). || `/api/diagnostics/training-status` | GET | Background training + cache status. |

| `/__debug/info`, `/__routes` | GET | Template/route diagnostics with build ID. || `/api/diagnostics/score-distribution` | GET | Summary stats for attractiveness scores (see tier distribution). |

| `/health` | GET | Lightweight health probe. || `/api/diagnostics/coherence-audit` | GET | Detect mismatches between tiers and probabilities. |

| `/api/admin/precompute` | POST | Trigger tier precompute (`{"max_rows": int, "save_to_disk": bool}`). Default: 400 rows. |

Payload/response formats are returned as JSON. See `docs/user_guide.md` for UI flows that consume these endpoints.| `/api/admin/cache/clear` | POST | Clear caches (`{"disk": bool, "scope": "all"}`). |

| `/__debug/info`, `/__routes` | GET | Template/route diagnostics with build ID. |

---| `/health` | GET | Lightweight health probe. |



## 🗃️ Data & CachingPayload/response formats are returned as JSON. See `docs/user_guide.md` for UI flows that consume these endpoints.



- **Kaggle ingestion:** `model.py` attempts KaggleHub download of `arindam235/startup-investments-crunchbase`, then merges/normalizes company data. If Kaggle is unavailable, it falls back to the bundled `kaggle_data/investments_VC.csv` or synthetic generation.---

- **Fast data loading:** `KAGGLE_MAX_ROWS=400` (default) provides **5x speedup** vs old 2000-row default. Adjust higher for more data, lower for faster startup.

- **Cache directory:** `.model_cache/` stores (a) model .pkl files and metadata, (b) precomputed tier DataFrame snapshots, and (c) serialized analysis cache. Safe to delete when you need a full rebuild.## 🗃️ Data & Caching

- **Analysis cache:** In-memory `ANALYSIS_CACHE` keyed by company_id to avoid re-computation; cleared via admin API or restart.

- **Kaggle ingestion:** `model.py` attempts KaggleHub download of `arindam235/startup-investments-crunchbase`, then merges/normalizes company data. If Kaggle is unavailable, it falls back to the bundled `kaggle_data/investments_VC.csv` or synthetic generation.

---- **Cache directory:** `.model_cache/` stores (a) model .pkl files and metadata, (b) precomputed tier DataFrame snapshots, and (c) serialized analysis cache. Safe to delete when you need a full rebuild.

- **Analysis cache:** In-memory `ANALYSIS_CACHE` keyed by company_id to avoid re-computation; cleared via admin API or restart.

## 🧪 Testing & Utilities

---

- `python -m pytest` (from repo root) – executes unit and smoke tests (see `test_*.py`)

- `_tools/smoke_test.py` – lightweight checks that endpoints respond with expected structure## 🧪 Testing & Utilities

- `_tools/verify_funding_and_valuation.py` – validates ingestion data for missing/invalid funding totals

- `_tools/test_score_distribution.py` – validates strict scoring produces expected tier distribution- `python -m pytest` (from repo root) – executes unit and smoke tests (see `test_*.py`).

- `_tools/smoke_test.py` – lightweight checks that endpoints respond with expected structure.

When modifying ML logic or templates, run the smoke tools before opening a PR.- `_tools/verify_funding_and_valuation.py` – validates ingestion data for missing/invalid funding totals.



---When modifying ML logic or templates, run the smoke tools before opening a PR.



## 🚀 Deployment Notes---



- **Gunicorn/Waitress**: For production, run `gunicorn app:app` or `waitress-serve --port=5000 app:app` with `AUTO_TRAIN_ON_IMPORT=false`. Tiers are automatically precomputed after model training completes.## 🚀 Deployment Notes

- **Docker**: The included `Dockerfile` supplies a slim container; ensure Kaggle credentials are mounted via secrets and that `/app/.model_cache` is writable if you want persistent caching.

- **CI/CD**: Incorporate `python -m compileall`, `pytest`, and optionally the smoke scripts in pipelines before deploying.- **Gunicorn/Waitress**: For production, run `gunicorn app:app` or `waitress-serve --port=5000 app:app` with `AUTO_TRAIN_ON_IMPORT=false`. Tiers are automatically precomputed after model training completes.

- **Docker**: The included `Dockerfile` supplies a slim container; ensure Kaggle credentials are mounted via secrets and that `/app/.model_cache` is writable if you want persistent caching.

---- **CI/CD**: Incorporate `python -m compileall`, `pytest`, and optionally the smoke scripts in pipelines before deploying.



## 🛠️ Troubleshooting Cheatsheet---



| Symptom | Suggested Checks |## 🛠️ Troubleshooting Cheatsheet

| --- | --- |

| Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated. With cached models: <1s. Without cache: ~10-30s for background training. Reduce `KAGGLE_MAX_ROWS` if loading is slow. || Symptom | Suggested Checks |

| Tier filter returns empty list | Wait for training to complete (watch for "✅ Auto-precompute completed" message), verify `precomputed_*` columns exist via `/api/diagnostics/score-distribution`. || --- | --- |

| Most companies in Avoid tier | This is **EXPECTED** with stricter scoring (Schema 2025-10-01). Natural distribution: ~50%+ Avoid, ~30-40% Monitor, ~10-20% Invest. This reflects realistic VC success rates (25% overall). || Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated, inspect logs for Kaggle download delays. |

| High probability but "Avoid" tier | Check `/api/diagnostics/coherence-audit`. Note: New thresholds are Invest ≥65, Monitor 50-64, Avoid <50. Success probability <40% is capped at 49 (Avoid tier) by design. || Tier filter returns empty list | Run `/api/admin/precompute`, verify `precomputed_*` columns exist, inspect `/api/diagnostics/score-distribution`. |

| Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity. System automatically falls back to cached `kaggle_data/investments_VC.csv` or synthetic data. || High probability but “Avoid” tier | Check `/api/diagnostics/coherence-audit` and adjust `PROB_TEMPER_*` env vars if needed. |

| False "Auto-precompute failed" message | **Fixed in latest version!** System now checks actual data columns to verify success instead of non-existent return values. || Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity; fallback uses cached CSV. |

| Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). || Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). |



------



## 🤝 Contributing## 🤝 Contributing



1. Update or add tests in `test_*.py` when altering API behavior1. Update or add tests in `test_*.py` when altering API behavior.

2. Run the smoke tools and capture key outputs in the PR description2. Run the smoke tools and capture key outputs in the PR description.

3. Update documentation (this file, root README, or docs/ guides) when endpoints or workflows change3. Update documentation (this file, root README, or docs/ guides) when endpoints or workflows change.

4. Follow pep8/black formatting for Python files4. Follow pep8/black formatting for Python files.



------



## 📞 Support & Resources## 📞 Support & Resources



- [../README.md](../README.md) – Portfolio-level overview and roadmap- [../README.md](../README.md) – Portfolio-level overview and roadmap.

- [../QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md) – **Get started in 2 minutes!**- [../docs/user_guide.md](../docs/user_guide.md) – UI walkthrough for non-technical stakeholders.

- [../SCORING_METHODOLOGY.md](../SCORING_METHODOLOGY.md) – Complete scoring methodology and ML model documentation- [../docs/technical_specs.md](../docs/technical_specs.md) – ML architecture, feature sets, deployment diagrams.

- [../docs/user_guide.md](../docs/user_guide.md) – UI walkthrough for non-technical stakeholders- `/debug_log.txt`, `/error_debug.txt` – rotation-friendly logs written by the app for diagnostics.

- [../docs/technical_specs.md](../docs/technical_specs.md) – ML architecture, feature sets, deployment diagrams

- [../PRECOMPUTE_MESSAGE_FIX.md](../PRECOMPUTE_MESSAGE_FIX.md) – Fixed misleading error messagesTier precomputation is now fully automatic. The training banner has been removed for a cleaner user experience—tiers are computed immediately after bootstrap and full model training completes.

- [../KAGGLE_MAX_ROWS_UPDATE.md](../KAGGLE_MAX_ROWS_UPDATE.md) – Fast data loading feature details

- [../SCORING_STRICTNESS_COMPLETE.md](../SCORING_STRICTNESS_COMPLETE.md) – Strict scoring implementation---

- `/debug_log.txt`, `/error_debug.txt` – rotation-friendly logs written by the app for diagnostics

**Deal Scout keeps improving—submit ideas or issues via GitHub and help us build smarter startup diligence workflows.**
**Recent Improvements (October 2025):**
- ✅ Stricter scoring with realistic VC distributions (~50%+ Avoid tier)
- ✅ **5x faster data loading** (400 vs 2000 rows)
- ✅ Fixed misleading precompute error messages
- ✅ Automatic tier precomputation after training
- ✅ Consistent 65/50 tier thresholds throughout codebase
- ✅ Comprehensive scoring methodology documentation

---

**Deal Scout keeps improving—submit ideas or issues via GitHub and help us build smarter startup diligence workflows.**
