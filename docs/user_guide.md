# Deal Scout – User Guide

This guide walks through the Deal Scout web experience, from launching the application to interpreting advanced analytics and managing diagnostics.

---

## 1. Launching the Application

### Windows (recommended)

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\run_web_app.ps1
```

The script bootstraps a virtual environment, installs dependencies, loads Kaggle credentials (if present), and starts the Flask server on http://localhost:5000.

### Cross-platform manual start

1. Create/activate a virtual environment and install requirements:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Export recommended environment flags:
   ```powershell
   set FLASK_ENV=development
   set AUTO_TRAIN_ON_IMPORT=false
   set BOOTSTRAP_FAST=true
   ```
3. Launch the app:
   ```powershell
   python app.py
   ```

---

## 2. Understanding the Interface

### 2.1 Layout Overview

- **Header Banner:** Displays build ID, data source (Kaggle vs synthetic), and instant diagnostics toggles.
- **Filter Drawer:** Controls search, industries, consolidated industry groups, regions, funding rounds, success status, and attractiveness tiers.
- **Company Catalog:** Card/grid showing startups with key metrics such as funding, valuation, success probability, and tier badges.
- **Analysis Drawer/Modal:** Opens per company with charts, component scores, narrative commentary, and admin shortcuts.

### 2.2 Filter Controls

| Control | Description |
| --- | --- |
| Search | Case-insensitive match on company name. |
| Industry | Exact industry labels from the dataset. |
| Industry Group | Consolidated categories (Fintech, Healthcare, SaaS, etc.). |
| Region | Auto-mapped regions (North America, Europe, Asia, etc.). |
| Funding Round | Seed → Series D+ filter. |
| Status | Operating, Acquired, IPO, Closed. |
| Tier | Attractiveness tier (Invest ≥65% / Monitor 50-64% / Avoid <50%). |

> Tier filters leverage precomputed columns when available; thresholds updated Oct 2025 for realistic VC funnel distribution.

### 2.3 Company Card Details

Each card surfaces:

- `attractiveness_score` – 0–100 scaled rating (Invest ≥65, Monitor 50-64, Avoid <50).
- `investment_tier` – Invest / Monitor / Avoid labels.
- `funding_amount_usd`, `valuation_usd`, `team_size`, `market_size_billion_usd`.
- Risk level when cached/precomputed.

Click **View analysis** to open the detailed modal.

---

## 3. Company Analysis Modal

### 3.1 Summary Panel

- Headline metrics: attractiveness score, funding recommendation, valuation range, risk level.
- Investment commentary: bullet list of ML-generated insights.
- Tier + risk badge for quick triage.
- Note: Success probability removed from display (Oct 2025) - internal metric only.

### 3.2 Component Charts

| Chart | Insights Provided |
| --- | --- |
| Business fundamentals radar | Market size, competition, team, valuation, funding normalized scores. |
| Component score bars | Market, team, financial, growth component contributions. |
| Feature contribution pie | Most influential factors (no revenue slice in tempered outputs). |
| Risk/return scatter | Position relative to simulated industry peers. |
| Industry success rates | Benchmarking across major verticals (with active industry highlighted). |

### 3.3 Risk Factors

Dynamic list summarizing critical risks (e.g., low funding, small team, high competition, early stage). These signals originate from `model.py` heuristics and provide a qualitative complement to the score.

### 3.4 Admin Shortcuts (when banner visible)

- Trigger tier precompute.
- Clear caches (memory/disk).
- View Kaggle ingest status.

---

## 4. Data Sources & Kaggle Integration

### 4.1 Credential Setup

- Preferred: place `kaggle.json` in `flask_app/` or configure `KAGGLE_USERNAME` / `KAGGLE_KEY` environment variables.
- Alternately, use system-wide `~/.kaggle/kaggle.json`.

The bootstrap script will auto-detect credentials and set environment variables for the session.

### 4.2 Source Prioritization

1. KaggleHub dataset `arindam235/startup-investments-crunchbase`.
2. Cached copy under `flask_app/kaggle_data/` (if previously downloaded).
3. Bundled `kaggle_data/investments_VC.csv` failsafe.
4. Synthetic generator (as a last resort or when `SKIP_KAGGLE=true`).

Use `/api/data-source` or the UI banner to confirm which source is active.

---

## 5. Advanced Workflows

### 5.1 Batch Analysis

- Select multiple companies via the UI comparison controls or POST to `/api/companies/analyze` with company IDs.
- Review the `analysis_results` array for batched insights and confirm `summary.total_analyzed` matches expectations.

### 5.2 Precompute Attractiveness Tiers

1. Invoke `/api/admin/precompute` from the admin banner or via REST:
   ```powershell
   curl -X POST http://localhost:5000/api/admin/precompute -H "Content-Type: application/json" -d '{"max_rows": 400, "save_to_disk": true}'
   ```
2. Monitor `/api/diagnostics/score-distribution` for updated stats.
3. Cached values persist under `.model_cache/`.

### 5.3 Clearing Caches

- Use `/api/admin/cache/clear` with payload options:
  - `{ "disk": false }` – drop only in-memory analysis cache.
  - `{ "disk": true }` – delete `.model_cache/` artifacts in addition to memory.

### 5.4 Adjusting Probability Tempering

- Environment variables `PROB_TEMPER_ENABLE`, `PROB_TEMPER_TRIP`, `PROB_TEMPER_MAX`, `PROB_TEMPER_MIN`, `PROB_TEMPER_ONLY_AVOID` control smoothing of success probabilities to avoid mismatched tiers (e.g., Avoid with 0.92 probability).
- Update in shell prior to launch:
  ```powershell
  $env:PROB_TEMPER_MAX = '0.80'
  .\run_web_app.ps1
  ```

---

## 6. Diagnostics & Troubleshooting

### 6.1 Quick Status Checklist

| Check | Endpoint / Location | Expected Output |
| --- | --- | --- |
| Server health | `/health` | `{ "status": "healthy" }` |
| Template/version info | `/__debug/info` | JSON with `build_id`, template mtime, cache headers. |
| Route registration | `/__routes` | List of endpoints with HTTP methods. |
| Training status | `/api/diagnostics/training-status` | `background_training_alive`, model readiness. |
| Score distribution | `/api/diagnostics/score-distribution` | Histogram statistics, tier counts. |
| Coherence audit | `/api/diagnostics/coherence-audit` | Mismatch counts for tiers vs probabilities. |

### 6.2 Common Scenarios

- **Blank catalog after applying tier filter**
  - Confirm precompute columns exist (`precomputed_attractiveness_score`).
  - Trigger `/api/admin/precompute` if absent.
  - Check logs for exceptions during fallback analysis.

- **Kaggle download failures**
  - Ensure credentials valid (`/api/data-source` shows synthetic fallback otherwise).
  - Inspect the console output from `run_web_app.ps1` for KaggleHub error messages.
  - Use cached CSV by ensuring `kaggle_data/investments_VC.csv` exists.

- **Slow warmup or high CPU**
  - Verify `AUTO_TRAIN_ON_IMPORT=false` and `BOOTSTRAP_FAST=true`.
  - Reduce `PRECOMPUTE_MAX_ROWS` or set `PRECOMPUTE_DISABLE=true` during development.

- **Probability looks inconsistent with tier**
  - Review `/api/diagnostics/coherence-audit`.
  - Tune `PROB_TEMPER_*` environment values.
  - Confirm caches aren’t stale by clearing them and recomputing.

### 6.3 Log Files

- `debug_log.txt` – General runtime messages (including analysis request traces).
- `error_debug.txt` – Stack traces for 500 errors.
- Manually rotate these files or tail them during investigations.

---

## 7. Best Practices

- **Use filters first:** Narrow the catalog with tier + region filters before opening detailed analyses.
- **Precompute before demos:** Run `/api/admin/precompute` to guarantee fast tier filtering during live presentations.
- **Capture diagnostics:** When filing issues, attach outputs from `/api/diagnostics/training-status` and `/api/data-source`.
- **Version control configs:** Track `.env` or deployment scripts to ensure consistent instant-start settings across environments.
- **Validate after code changes:** Run `_tools/smoke_test.py` and relevant `pytest` suites before pushing to shared branches.

---

## 8. Additional Resources

- [Technical Specifications](technical_specs.md) – Deep dive into model architecture, feature sets, and deployment diagrams.
- [Project Summary](project_summary.md) – Executive overview for stakeholders.
- [Deployment Guide](../DEPLOYMENT_GUIDE.md) – Instructions for publishing to GitHub or cloud environments.
- [Root README](../README.md) – Product overview and roadmap.

For questions or feedback, file an issue in the repository with logs and diagnostic outputs.

---

**Deal Scout keeps your diligence team ahead—use the filters, run diagnostics, and share insights effortlessly.**