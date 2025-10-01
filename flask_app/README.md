gunicorn -w 4 -b 0.0.0.0:5000 app:app
pip install waitress
# Deal Scout Flask Application

This directory hosts the Deal Scout web application: a product| Symp| Symptom | Suggested Checks |
| --- | --- |
| Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated, inspect logs for Kaggle download delays. Current default: 400 rows for ~30-60s startup. |
| Tier filter returns empty list | Wait for training to complete (tiers auto-precompute after training), verify `precomputed_*` columns exist, inspect `/api/diagnostics/score-distribution`. |
| High probability but "Avoid" tier | Check `/api/diagnostics/coherence-audit` and adjust `PROB_TEMPER_*` env vars if needed. Note: New thresholds are Invest ≥65%, Monitor 50-64%, Avoid <50%. |
| Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity; fallback uses cached CSV. |
| Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). |uggested Checks |
| --- | --- |
| Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated, inspect logs for Kaggle download delays. |
| Tier filter returns empty list | Wait for training to complete (tiers auto-precompute after training), verify `precomputed_*` columns exist, inspect `/api/diagnostics/score-distribution`. |
| High probability but "Avoid" tier | Check `/api/diagnostics/coherence-audit` and adjust `PROB_TEMPER_*` env vars if needed. |
| Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity; fallback uses cached CSV. |
| Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). |dy Flask stack with instant-start ML models, cached diagnostics, and Kaggle-aware data ingestion.

---

## 🛠️ Quick Launch

### Windows (recommended)

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\run_web_app.ps1
```

The bootstrap script will:

- Create/activate `venv/` (unless `USE_VENV=0`).
- Install pinned dependencies via `requirements.txt`.
- Set instant-start environment defaults (`AUTO_TRAIN_ON_IMPORT=false`, `BOOTSTRAP_FAST=true`, etc.).
- Source Kaggle credentials from `kaggle.json` if present.
- Launch the Flask dev server on http://localhost:5000.

### Manual setup (cross-platform)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1   # macOS/Linux: source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
set FLASK_ENV=development
set AUTO_TRAIN_ON_IMPORT=false
python app.py
```

Optional environment toggles:

- `PRECOMPUTE_MAX_ROWS=400` – limit initial precompute rows for faster warmup (default: 400 rows for 30-60s startup).
- `CACHE_MODELS=false` – bypass on-disk model cache.
- `SKIP_KAGGLE=true` – force synthetic dataset even when credentials exist.

---

## 🧭 Application Layout

```
flask_app/
├── app.py                 # Flask routes, REST + diagnostics endpoints
├── model.py               # ML pipeline, Kaggle ingestion, caching, precompute
├── templates/
│   ├── index.html         # Main UI
│   ├── error.html         # Error page
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── run_web_app.ps1        # Windows bootstrapper
├── start_server.ps1/.sh   # Minimal launch scripts for deployments
├── requirements.txt       # Runtime dependencies
├── kaggle_data/           # Cached Kaggle datasets (created on demand)
├── .model_cache/          # Persisted model + tier artifacts (created on demand)
└── _tools/                # Smoke tests, diagnostics helpers
```

---

## 🌐 Core Features

- **Company Explorer:** `/api/companies` powers the UI catalog with pagination, search, consolidated industry groups, regions, funding rounds, status, and tier filtering. Investment tiers use stricter thresholds (Invest ≥65%, Monitor 50-64%, Avoid <50%) calibrated for realistic VC funnel distribution.
- **Deal Analysis Modal:** `/api/companies/<id>/analyze` returns component scores, business fundamentals radar, risk commentary, and chart payloads.
- **Admin Utilities:**
  - `/api/admin/precompute` – warm attractiveness tiers and persist to cache (default: 400 rows for fast startup).
  - `/api/admin/cache/clear` – drop analysis caches in memory/disk.
  - `/api/data-source` – confirm Kaggle/synthetic dataset provenance.
- **Diagnostics:** `/__debug/info`, `/__routes`, `/api/diagnostics/*` provide build IDs, cache status, score distributions, and coherence audits.
- **Instant-start ML:** background threads continue training while the UI remains responsive; probability tempering ensures tier labels align with displayed probabilities.

---

## 🔌 Key Environment Flags

| Variable | Default | Description |
| --- | --- | --- |
| `AUTO_TRAIN_ON_IMPORT` | `false` | Skip heavyweight model training during module import. |
| `BOOTSTRAP_FAST` | `true` | Use lightweight bootstrap models until background training finishes. |
| `LAZY_BACKGROUND_TRAIN` | `true` | Spawn background training thread post-startup. |
| `PRECOMPUTE_MAX_ROWS` | `400` | Row cap for initial precompute (optimized for 30-60s startup). |
| `CACHE_MODELS` | `true` | Persist/load models and tiers under `.model_cache/`. |
| `PROB_TEMPER_*` | See script | Temper probability outputs to avoid contradictory tiers. |
| `SKIP_KAGGLE` | `false` | Force synthetic data by default. |
| `KAGGLE_USERNAME`, `KAGGLE_KEY` | n/a | API credentials when not using `kaggle.json`. |

**Note:** Tier precomputation now happens automatically after both bootstrap and full model training, eliminating the need for manual precompute triggers. The training banner and manual precompute controls have been removed from the UI for a cleaner experience.

Environment variables may be set in the shell or ahead of script execution:

```powershell
$env:PRECOMPUTE_MAX_ROWS = '400'
$env:CACHE_MODELS = 'true'
.\run_web_app.ps1
```

---

## 📡 REST + Diagnostics API

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/companies` | GET | Catalog with filters: page, per_page, search, industry, industry_group, region, funding_round, status, tier (Invest/Monitor/Avoid: 65/50 thresholds). |
| `/api/companies/<company_id>` | GET | Raw metrics + derived efficiency ratios. |
| `/api/companies/<company_id>/analyze` | GET | Full analysis package with component scores and chart data. |
| `/api/companies/analyze` | POST | Batch analysis – payload `{ "company_ids": [...] }`. |
| `/api/companies/compare` | POST | Return raw metrics for side-by-side comparison. |
| `/api/data-source` | GET | Indicates synthetic vs Kaggle dataset and dataset health stats. |
| `/api/diagnostics/training-status` | GET | Background training + cache status. |
| `/api/diagnostics/score-distribution` | GET | Summary stats for attractiveness scores (see tier distribution). |
| `/api/diagnostics/coherence-audit` | GET | Detect mismatches between tiers and probabilities. |
| `/api/admin/precompute` | POST | Trigger tier precompute (`{"max_rows": int, "save_to_disk": bool}`). Default: 400 rows. |
| `/api/admin/cache/clear` | POST | Clear caches (`{"disk": bool, "scope": "all"}`). |
| `/__debug/info`, `/__routes` | GET | Template/route diagnostics with build ID. |
| `/health` | GET | Lightweight health probe. |

Payload/response formats are returned as JSON. See `docs/user_guide.md` for UI flows that consume these endpoints.

---

## 🗃️ Data & Caching

- **Kaggle ingestion:** `model.py` attempts KaggleHub download of `arindam235/startup-investments-crunchbase`, then merges/normalizes company data. If Kaggle is unavailable, it falls back to the bundled `kaggle_data/investments_VC.csv` or synthetic generation.
- **Cache directory:** `.model_cache/` stores (a) model .pkl files and metadata, (b) precomputed tier DataFrame snapshots, and (c) serialized analysis cache. Safe to delete when you need a full rebuild.
- **Analysis cache:** In-memory `ANALYSIS_CACHE` keyed by company_id to avoid re-computation; cleared via admin API or restart.

---

## 🧪 Testing & Utilities

- `python -m pytest` (from repo root) – executes unit and smoke tests (see `test_*.py`).
- `_tools/smoke_test.py` – lightweight checks that endpoints respond with expected structure.
- `_tools/verify_funding_and_valuation.py` – validates ingestion data for missing/invalid funding totals.

When modifying ML logic or templates, run the smoke tools before opening a PR.

---

## 🚀 Deployment Notes

- **Gunicorn/Waitress**: For production, run `gunicorn app:app` or `waitress-serve --port=5000 app:app` with `AUTO_TRAIN_ON_IMPORT=false`. Tiers are automatically precomputed after model training completes.
- **Docker**: The included `Dockerfile` supplies a slim container; ensure Kaggle credentials are mounted via secrets and that `/app/.model_cache` is writable if you want persistent caching.
- **CI/CD**: Incorporate `python -m compileall`, `pytest`, and optionally the smoke scripts in pipelines before deploying.

---

## 🛠️ Troubleshooting Cheatsheet

| Symptom | Suggested Checks |
| --- | --- |
| Server boots slowly | Confirm `AUTO_TRAIN_ON_IMPORT=false`, ensure `.model_cache/` is populated, inspect logs for Kaggle download delays. |
| Tier filter returns empty list | Run `/api/admin/precompute`, verify `precomputed_*` columns exist, inspect `/api/diagnostics/score-distribution`. |
| High probability but “Avoid” tier | Check `/api/diagnostics/coherence-audit` and adjust `PROB_TEMPER_*` env vars if needed. |
| Kaggle download failures | Review logs, ensure `KAGGLE_USERNAME/KEY` set, confirm connectivity; fallback uses cached CSV. |
| Memory pressure from Matplotlib | Confirm `matplotlib.use('Agg')` and that figures are closed (already enforced in `app.py`). |

---

## 🤝 Contributing

1. Update or add tests in `test_*.py` when altering API behavior.
2. Run the smoke tools and capture key outputs in the PR description.
3. Update documentation (this file, root README, or docs/ guides) when endpoints or workflows change.
4. Follow pep8/black formatting for Python files.

---

## 📞 Support & Resources

- [../README.md](../README.md) – Portfolio-level overview and roadmap.
- [../docs/user_guide.md](../docs/user_guide.md) – UI walkthrough for non-technical stakeholders.
- [../docs/technical_specs.md](../docs/technical_specs.md) – ML architecture, feature sets, deployment diagrams.
- `/debug_log.txt`, `/error_debug.txt` – rotation-friendly logs written by the app for diagnostics.

Tier precomputation is now fully automatic. The training banner has been removed for a cleaner user experience—tiers are computed immediately after bootstrap and full model training completes.

---

**Deal Scout keeps improving—submit ideas or issues via GitHub and help us build smarter startup diligence workflows.**