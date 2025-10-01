def log_prediction(inputs, outputs, duration):
# Deal Scout Technical Specifications

## 1. System Overview

Deal Scout is a Flask-first web platform for evaluating venture investments. The current release focuses on:

- Zero-touch startup, with a PowerShell bootstrap that provisions the virtual environment, installs dependencies, and starts the Flask server instantly.
- KaggleHub-powered data ingestion with resilient local caching and deterministic fallbacks.
- Ensemble ML pipeline (RandomForest, HistGradientBoosting, ExtraTrees, Logistic Regression, soft voting) with probability tempering to harmonize attractiveness tiers.
- Cached attractiveness precomputation and tier administration endpoints for enterprise-grade responsiveness.
- A modern responsive UI with tier filters, analysis modal, diagnostics banner, and admin tooling.

```
┌───────────────────────────── Deal Scout Platform ─────────────────────────────┐
│                                                                               │
│  Data Ingestion        ML + Analytics            Web + Ops                    │
│  ────────────          ──────────────           ─────────                     │
│  • KaggleHub datasets  • Feature engineering    • Flask 3.x REST API          │
│  • Cached CSV failsafe • Ensemble classification• React-lite JS front-end     │
│  • Synthetic generator • Funding & valuation RF • Bootstrap / Chart.js UI     │
│  • Credential auto-detect• Probability tempering• Admin diagnostics + caching │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## 2. Data Architecture

### 2.1 Source Prioritization Pipeline

1. **Primary** – `kagglehub.dataset_download("arindam235/startup-investments-crunchbase")`
   - Cached under `%LOCALAPPDATA%\kagglehub\datasets\…` and mirrored to `flask_app/kaggle_data/`.
   - Structures include `investments_VC.csv`, `objects.csv`, and `funding_rounds.csv`.
2. **Secondary** – previously downloaded KaggleHub cache (`.cache/kagglehub`).
3. **Tertiary** – bundled `flask_app/kaggle_data/investments_VC.csv`.
4. **Failsafe** – synthetic generator `generate_startup_data()`.

The loader uses a 30-second background thread timeout with graceful degradation. Data sources are surfaced through `/api/data-source` and the UI banner.

### 2.2 Data Model

All datasets are normalized to a consistent schema before training and storage:

| Column | Type | Description |
| --- | --- | --- |
| `company_id` | `str` | Deterministic identifier (`vc_XXXX`, `startup_XXXX`, etc.). |
| `company_name` | `str` | Real name when available; synthetic otherwise. |
| `industry` / `industry_group` | `str` | Raw market label plus consolidated taxonomy via `consolidate_industry()`. |
| `location` / `region` | `str` | Original location plus region bucket from `map_location_to_region()`. |
| `funding_round` | `str` | Seed, Series A, Series B, Series C, Series D+. |
| `funding_amount_usd` | `float` | Normalized total funding (USD). |
| `valuation_usd` | `float` | Derived valuation using stage-adjusted multiplier. |
| `team_size` | `int` | Employee count (synthetic where missing). |
| `years_since_founding` | `float` | Derived from founding date or synthetic. |
| `num_investors` | `int` | Count of distinct investors. |
| `competition_level` | `int` (1–10) | Competitive intensity heuristic. |
| `market_size_billion_usd` | `float` | TAM estimate in billions. |
| `status` | `str` | Operating, Acquired, IPO, Closed, etc. |
| `is_successful` | `int` | Success target influenced by status & funding heuristics. |
| `success_score` | `float` | Smoothed success confidence. |
| `has_funding_total_usd` | `bool` | Authoritative funding flag for UI filtering. |
| `precomputed_*` | `float/str` | Optional cached analysis outputs for rapid tier filtering. |

### 2.3 Feature Engineering

Performed inside `engineer_features()` and re-used for inference via `prepare_features_for_prediction()`:

- Derived numerics: `funding_efficiency`, `funding_per_employee`, log transforms, normalized competition buckets.
- Categorical expansion: `industry`, `industry_group`, `location`, `region`, `funding_round`, `status`, `age_category`, `team_size_category`, `competition_category` using one-hot encoding (`drop_first=True`).
- Scaling: `StandardScaler` applied to the numerical feature bundle captured at training time and rebound to the classifier for inference alignment.

## 3. Machine Learning Stack

### 3.1 Training Workflow

1. **Data load** – `load_data()` executes source prioritization and populates `sample_data`.
2. **Feature engineering** – returns matrix + scaler + target series.
3. **Model selection** – GridSearchCV over:
   - `RandomForestClassifier` (200–400 trees, depth ≤ 20, balanced subsample weights).
   - `HistGradientBoostingClassifier` (learning rate 0.05–0.1).
   - `ExtraTreesClassifier` (up to 600 estimators).
   - `LogisticRegression` (balanced, `C` sweep).
4. **Soft Voting Ensemble** – built when ≥2 tuned estimators succeed. Held-out accuracy decides the champion.
5. **Threshold tuning** – calibrates decision boundary (0.25–0.75 search) to maximize validation accuracy, wrapped by `ThresholdedClassifier`.
6. **Regression models** – twin `RandomForestRegressor` instances for funding amount and valuation projections.
7. **Caching** – `.model_cache/` persists pickles plus metadata keyed by `SCORING_SCHEMA_VERSION` and dataset signature. Precompute artifacts (tiers + analysis cache) saved separately for reuse.

Typical results on KaggleCrunchbase data (2k rows):

- Classification accuracy ~0.78–0.82 (varies with dataset freshness).
- Funding regression R² ~0.72–0.80.
- Valuation regression R² ~0.80–0.86.

### 3.2 Probability Tempering

Environment-controlled smoothing avoids contradictions such as "Avoid" deals with 0.92 success probability:

| Variable | Default | Description |
| --- | --- | --- |
| `PROB_TEMPER_ENABLE` | `true` | Master toggle. |
| `PROB_TEMPER_TRIP` | `0.80` | Upper probability bound to clamp. |
| `PROB_TEMPER_MAX` / `MIN` | `0.82` / `0.18` | Hard caps applied post-ensemble. |
| `PROB_TEMPER_ONLY_AVOID` | `false` | When true, only downshifts Avoid-tier anomalies. |

### 3.3 Precomputation & Caching

Investment tiers are automatically precomputed after both bootstrap and full model training completes. The `precompute_investment_tiers(max_rows=None)` function populates `precomputed_attractiveness_score`, `precomputed_investment_tier`, normalized tier labels, risk levels, and user-facing recommendations. Results are automatically saved to disk cache for fast restarts. The manual precompute endpoint (`/api/admin/precompute`) remains available for on-demand recalculation if needed.

## 4. REST API Surface

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Render catalog UI with filter metadata. |
| `/health` | GET | Liveness probe. |
| `/__debug/info` | GET | Template + build diagnostics (cache headers, build ID). |
| `/__routes` | GET | Enumerate registered routes for troubleshooting. |
| `/__build` | GET | Build stamp & timestamp. |
| `/api/data-source` | GET | Current dataset, sample size, success rate. |
| `/api/companies` | GET | Paginated catalog with server-side filters (search, tier, grouped industries, regions, etc.). |
| `/api/companies/<id>` | GET | Raw company metrics + derived heuristics. |
| `/api/companies/<id>/analyze` | GET | Comprehensive analysis (component scores, charts, commentary). |
| `/api/companies/analyze` | POST | Batch analysis (list of company IDs). |
| `/api/companies/compare` | POST | Lightweight comparison payload. |
| `/api/visualizations/<id>` | GET | PNG dashboard snapshot (fallback error canvas on failure). |
| `/api/diagnostics/training-status` | GET | Model readiness, background thread status, bootstrap rows. |
| `/api/diagnostics/score-distribution` | GET | Tier counts, distribution stats, dataset length. |
| `/api/diagnostics/coherence-audit` | GET | Detects inconsistencies between tiers, probabilities, and risk labels. |
| `/api/admin/precompute` | POST | Trigger precompute; optional `max_rows`, `save_to_disk`. |
| `/api/admin/cache/clear` | POST | Clear in-memory cache; optional disk purge. |
| `/api/test-*` | GET | Smoke endpoints to validate analysis/commentary wiring. |

All JSON responses include `build_id` to verify deployment freshness. Admin endpoints write to `debug_log.txt` for traceability.

## 5. Front-End Architecture

### 5.1 Layout Components

- **Header banner** – data source badge, build ID, admin quick actions.
- **Filter drawer** – consolidated industry groups, regions, funding stages, tier toggles, success status, search.
- **Company grid** – cards display attractiveness score, tier, funding, valuation, success probability, risk level.
- **Analysis modal** – multi-chart layout (Chart.js) with narrative commentary, component breakdowns, risk factors, and admin shortcuts.
- **Diagnostics panel** – optional admin view surfacing `/api/diagnostics` outputs inside UI for live demos.

### 5.2 Chart Inventory

| Chart | Source | Notes |
| --- | --- | --- |
| Attractiveness doughnut | `dashboard_charts['attractiveness_gauge']` | Color-coded by tier threshold. |
| Feature contribution pie | Weighted heuristics (no revenue slice when tempered). |
| Industry success rates | Static benchmarking with active industry highlighted. |
| Risk-return scatter | Peer simulation (synthetic) plus target deal star. |
| Business fundamentals radar | Market size, competition, team, valuation, funding. |
| Component score bars | Market, team, financial, growth contributions from ML output. |

## 6. Operations & Environment

### 6.1 Bootstrap Scripts

- `run_web_app.ps1` – Powershell automation (venv creation, dependency install, Kaggle credential copy, `python app.py`).
- `start_server.ps1` / `start_server_kaggle.ps1` – convenience wrappers with production flags.
- `launch_app.bat`, `start_app.bat` – Windows shortcuts for manual execution.

### 6.2 Environment Variables

| Variable | Default | Effect |
| --- | --- | --- |
| `FLASK_ENV` | `development` | Enables debug logging + template reload. |
| `BOOTSTRAP_FAST` | `true` | Skips auto-training on import; defers to cached models. |
| `AUTO_TRAIN_ON_IMPORT` | `false` | Prevents long bootstrap during demos. |
| `SKIP_KAGGLE` | `false` | Force synthetic data (useful offline). |
| `CACHE_MODELS` | `true` | Persist model artifacts across sessions. |
| `PRECOMPUTE_MAX_ROWS` | *(unset)* | Limit initial precompute row count; full dataset used after training. |
| `FORCE_RETRAIN` | `false` | Ignore cached models and retrain on startup. |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | *(from creds)* | Optional environment credential override. |

**Note:** `PRECOMPUTE_DISABLE` has been removed—tiers now auto-compute after training for optimal UX.

Credential resolution order: env vars → colocated `kaggle.json` → `%HOMEPATH%/.kaggle/kaggle.json` → template warning.

### 6.3 Logging & Diagnostics

- `debug_log.txt` – append-only runtime log for analysis and admin endpoints.
- `error_debug.txt` – 500 handler tracebacks.
- `_tools/` scripts – CLI diagnostics (smoke tests, precompute limit checks, funding/valuation verification).
- Admin API endpoints remain available for cache management and diagnostics.

## 7. Performance & Scalability

- **Startup**: <10s with cached models; ~90s for cold retrain including grid search.
- **Catalog API**: <150 ms typical with precomputed tiers (P95 < 400 ms including filter cascades).
- **Analysis modal**: <450 ms when using cached analysis; up to 1.5s when computing charts on demand.
- **Memory footprint**: ~350 MB with models + dataset loaded; additional 150 MB for analysis cache of 2k companies.
- **Precompute**: default all rows; limit `max_rows` for dev loops to keep under 5s.

Scaling recommendations:

- Run behind Gunicorn (`gunicorn -w 4 -b 0.0.0.0:5000 app:app`) for production.
- Use `PRECOMPUTE_DISABLE=true` with external job scheduling that populates cache via `/api/admin/precompute`.
- Persist `.model_cache/` and `kaggle_data/` between deployments for stable warm cache.

## 8. Testing & Quality Gates

- `pytest` suites in `flask_app/` cover routes, pipeline integrity, KaggleHub integration, and Kaggle fallback scenarios.
- Smoke utilities (`_tools/smoke_test.py`, `_tools/verify_funding_and_valuation.py`) provide quick validation of dataset health and scoring coherence.
- CI recommendation: run `pytest`, `_tools/smoke_test.py`, and `/api/diagnostics/coherence-audit` after each deployment.

## 9. Security & Compliance Considerations

- Kaggle credentials remain local; template includes placeholders only.
- CORS open by design (`*`) for demo simplicity—tighten in production.
- Response headers enforce no-cache to guarantee template updates propagate instantly.
- No persistent storage; all computations in-memory per process. Add DB or secret store before multi-user rollout.

## 10. Roadmap Hooks

- Integrate OAuth or API key auth for admin endpoints.
- Externalize probability tempering and tier thresholds into configurable JSON for PM experimentation.
- Add Celery/RQ worker for asynchronous precompute and heavy analytics.
- Expand UI to support cohort analysis and portfolio exports.

For operational usage instructions, consult `docs/user_guide.md`. Deployment detail lives in `DEPLOYMENT_GUIDE.md`.