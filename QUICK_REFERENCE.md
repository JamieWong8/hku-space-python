# Documentation Quick Reference

**Fast access to key information:**

---

## 🚀 Quick Start

**New users start here:**
1. Read [README.md](README.md)
2. Run `flask_app\run_web_app.ps1`
3. Open http://localhost:5000

---

## 📊 Tier Thresholds (Updated Oct 2025)

| Tier | Score | Distribution |
|------|-------|--------------|
| **Invest** | ≥65% | ~25% |
| **Monitor** | 50-64% | ~45% |
| **Avoid** | <50% | ~30% |

---

## ⚡ Performance Settings

**Precompute:** 400 rows (default)  
**Startup time:** 30-60 seconds  
**Previous:** 2000 rows, 2-5 minutes

---

## 🔍 Key Files

- **Setup:** `flask_app/run_web_app.ps1`
- **Main app:** `flask_app/app.py`
- **ML models:** `flask_app/model.py`
- **UI:** `flask_app/templates/index.html`

---

## 📝 Documentation Files

**Essential:**
- [README.md](README.md) - Main overview
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - All docs
- [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) - Recent changes

**Setup:**
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - GitHub upload
- [KAGGLE_INTEGRATION_GUIDE.md](KAGGLE_INTEGRATION_GUIDE.md) - API keys

**Technical:**
- [flask_app/README.md](flask_app/README.md) - API reference
- [docs/technical_specs.md](docs/technical_specs.md) - Architecture
- [docs/user_guide.md](docs/user_guide.md) - UI walkthrough

---

## 🧪 Diagnostics

**Endpoints:**
```
GET /api/diagnostics/score-distribution
GET /api/diagnostics/training-status
GET /api/diagnostics/coherence-audit
```

**Scripts:**
```powershell
cd flask_app
python _tools/smoke_test.py
python trigger_precompute.py
```

---

## 🛠️ Common Commands

**Start app:**
```powershell
cd flask_app
.\run_web_app.ps1
```

**Upload to GitHub:**
```powershell
cd scripts
.\sync_to_github.ps1
```

**Trigger precompute:**
```powershell
cd flask_app
python trigger_precompute.py
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Slow startup | Check `PRECOMPUTE_MAX_ROWS=400` |
| Tier mismatch | Verify October 2025 updates applied |
| Kaggle errors | Check `flask_app/kaggle.json` |
| Empty tiers | Wait for training to complete |

**Full troubleshooting:** [flask_app/README.md](flask_app/README.md)

---

## 📞 Where to Look

| Question | Document |
|----------|----------|
| How do I install? | [README.md](README.md) |
| What changed recently? | [OCTOBER_2025_UPDATES.md](OCTOBER_2025_UPDATES.md) |
| How does the UI work? | [docs/user_guide.md](docs/user_guide.md) |
| How do I deploy? | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| What's the architecture? | [docs/technical_specs.md](docs/technical_specs.md) |
| Where are all the docs? | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

---

**Full navigation:** [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
