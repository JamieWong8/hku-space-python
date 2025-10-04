# 🚀 Deal Scout Quick Start Guide

Get up and running with Deal Scout in under 2 minutes!

---

## ⚡ Fastest Start (Windows)

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout\flask_app"
.\run_web_app.ps1
```

**That's it!** The script handles everything automatically:
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Configures environment variables
- ✅ Loads Kaggle credentials (if available)
- ✅ Launches Flask server on http://localhost:5000

---

## 📊 What to Expect

### Startup Timeline

| Phase | Duration | What's Happening |
|-------|----------|------------------|
| **Bootstrap** | <1 second | Lightweight models load for instant UI access |
| **Data Loading** | 1-2 seconds | Loading 400 companies from Kaggle (or synthetic data) |
| **Background Training** | 10-30 seconds | Full ensemble models training in background |
| **Tier Precompute** | Automatic | Investment tiers calculated after training completes |

### Console Output

```
Initializing Deal Scout models (instant-start mode)...
Bootstrap: Training fast baseline models (300 samples)...
Loading: Attempting to load local kaggle_data/investments_VC.csv...
Success: Loaded 400 rows from cached investments_VC.csv
Loading: Precomputing investment tiers for 400 companies...
Success: Precomputed tiers for 400 companies (of 400)
✅ Auto-precompute completed: 400 companies scored
   🟢 Invest: 85, 🟡 Monitor: 145, 🔴 Avoid: 170
```

---

## 🌐 Using the Web Interface

Once the server starts, open your browser to: **http://localhost:5000**

### Main Features

1. **Company Explorer** (Homepage)
   - Browse 400+ startup companies
   - Filter by Investment Tier: 🟢 Invest | 🟡 Monitor | 🔴 Avoid
   - Filter by Industry, Region, Funding Round, Status
   - Search by company name
   - Click any company for detailed analysis

2. **Investment Tiers Explained**
   - **🟢 Invest (Score ≥65)**: Strong investment opportunity - ~10-20% of companies
   - **🟡 Monitor (Score 50-64)**: Promising but needs due diligence - ~30-40% of companies
   - **🔴 Avoid (Score <50)**: Significant risks or concerns - ~40-60% of companies

3. **Company Analysis Modal**
   - Overall Attractiveness Score (0-100)
   - Success Probability (ML prediction)
   - Component Scores: Financial, Market, Team, Growth
   - Business Fundamentals Radar Chart
   - Investment Commentary & Risk Factors
   - Predicted Funding & Valuation

---

## 🎯 Investment Tier Distribution

**Expected with Stricter Scoring (2025-10-01 Schema):**

```
🔴 Avoid:   ~50-60% (realistic - most startups don't succeed)
🟡 Monitor: ~30-40% (solid but not exceptional)
🟢 Invest:  ~10-20% (truly strong opportunities)
```

This reflects **realistic VC success rates** (~25% overall success) and is intentionally selective to help you focus on the best opportunities.

---

## 🛠️ Environment Configuration

### Optional: Adjust Data Loading Speed

The default 400 rows loads in ~1-2 seconds. To load more data:

```powershell
$env:KAGGLE_MAX_ROWS = '1000'  # Load 1000 companies instead
.\run_web_app.ps1
```

⚠️ **Note:** Loading 2000 rows takes ~5-10 seconds vs 1-2 seconds for 400 rows.

### Optional: Use Kaggle Real Data

1. Get your Kaggle API credentials from https://www.kaggle.com/settings
2. Save to `flask_app\kaggle.json`:

```json
{
  "username": "your_username",
  "key": "your_api_key_here"
}
```

3. Restart the app - it will automatically download real startup data!

### Optional: Force Synthetic Data

```powershell
$env:SKIP_KAGGLE = 'true'
.\run_web_app.ps1
```

---

## 📱 Alternative: Jupyter Notebook

For interactive data exploration, try the Jupyter notebook:

```powershell
cd "c:\Users\jamie\OneDrive\Documents\Deal Scout"
pip install -r notebook_requirements.txt
jupyter notebook Deal_Scout_Interactive.ipynb
```

See [JUPYTER_NOTEBOOK_GUIDE.md](JUPYTER_NOTEBOOK_GUIDE.md) for details.

---

## 🔧 Troubleshooting

### "Server boots slowly"
- ✅ **Expected:** First run takes 10-30 seconds to train models
- ✅ **Cached runs:** Subsequent runs load in <1 second
- ✅ **Reduce data:** Set `KAGGLE_MAX_ROWS=200` for faster startup

### "No companies showing up"
- Wait for console message: "✅ Auto-precompute completed: 400 companies scored"
- Refresh browser page
- Check http://localhost:5000/api/companies to verify data loaded

### "Most companies in Avoid tier"
- ✅ **This is correct!** Stricter scoring reflects realistic VC outcomes
- ~50-60% in Avoid tier is expected and intentional
- Focus on the 🟢 Invest and 🟡 Monitor tiers for opportunities

### "Kaggle download failed"
- ✅ **No problem!** App automatically uses cached or synthetic data
- For real data, add `kaggle.json` credentials file

### Port already in use
```powershell
# Kill process on port 5000
Stop-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess -Force
```

---

## 🎓 Next Steps

Once you're comfortable with the basics:

1. **Read the Scoring Methodology** → [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md)
   - Understand how attractiveness scores are calculated
   - Learn about the ML models and ensemble approach
   - See the complete formula breakdown

2. **Explore the API** → [flask_app/README.md](flask_app/README.md)
   - `/api/companies` - Company catalog with filters
   - `/api/companies/<id>/analyze` - Detailed analysis
   - `/api/diagnostics/*` - System health and metrics

3. **Check Recent Updates** → [PRECOMPUTE_MESSAGE_FIX.md](PRECOMPUTE_MESSAGE_FIX.md)
   - Fixed misleading error messages
   - 5x faster data loading
   - Stricter, more realistic scoring

4. **Deploy to Production** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
   - Docker containerization
   - Gunicorn/Waitress setup
   - CI/CD pipeline

---

## 📚 Full Documentation

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete documentation navigation
- [README.md](README.md) - Detailed project overview
- [docs/user_guide.md](docs/user_guide.md) - Complete UI walkthrough
- [docs/technical_specs.md](docs/technical_specs.md) - Architecture & ML details

---

## 💡 Pro Tips

**Fastest Workflow:**
1. Start the app: `.\run_web_app.ps1`
2. While loading, review scoring methodology
3. Once loaded, filter by 🟢 Invest tier first
4. Deep dive on top 10-20 companies
5. Move to 🟡 Monitor tier for additional opportunities

**Performance:**
- App uses cached models after first run (instant startup!)
- Tier scores are precomputed (instant filtering!)
- Analysis results are cached (instant modal opens!)

**Data:**
- Default: 400 companies for fast loading
- Kaggle: Real startup data when credentials provided
- Synthetic: Generated realistic data as fallback

---

**Ready to evaluate your first startup?** 🚀

Run `.\run_web_app.ps1` and open http://localhost:5000 to get started!
