# 🎨 Deal Scout - Visual Architecture Diagram

This document provides graphical visualizations of the Deal Scout architecture.

---

## System Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                           USER INTERFACE LAYER                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐ ║
║  │                         WEB BROWSER                                 │ ║
║  │  ┌───────────────┐ ┌───────────────┐ ┌────────────┐ ┌───────────┐ │ ║
║  │  │   HTML5 +     │ │  Bootstrap    │ │ JavaScript │ │ Font      │ │ ║
║  │  │   Jinja2      │ │    5.3.x      │ │   ES6+     │ │ Awesome   │ │ ║
║  │  │   Templates   │ │   Responsive  │ │   Vanilla  │ │   Icons   │ │ ║
║  │  └───────────────┘ └───────────────┘ └────────────┘ └───────────┘ │ ║
║  │                                                                     │ ║
║  │  Features:                                                          │ ║
║  │  • Responsive design (mobile/tablet/desktop)                       │ ║
║  │  • Dark/Light mode toggle                                          │ ║
║  │  • Real-time filtering & search                                    │ ║
║  │  • Modal-based company analysis                                    │ ║
║  │  • Multi-tab interface (5 tabs)                                    │ ║
║  └─────────────────────────────────────────────────────────────────────┘ ║
║                                  ▲                                        ║
║                                  │ HTTP/HTTPS                            ║
║                                  ▼                                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                         APPLICATION SERVER LAYER                          ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐ ║
║  │                    FLASK 3.0+ WEB FRAMEWORK                         │ ║
║  │                                                                     │ ║
║  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ ║
║  │  │   Routing    │  │   Template   │  │   Session Management     │ │ ║
║  │  │   Engine     │  │   Rendering  │  │   & Authentication       │ │ ║
║  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ │ ║
║  │                                                                     │ ║
║  │  API Endpoints:                                                     │ ║
║  │  ├─ GET  /                    → Home page                          │ ║
║  │  ├─ GET  /api/companies       → Company catalog JSON               │ ║
║  │  ├─ POST /analyze_company/:id → ML analysis JSON                   │ ║
║  │  ├─ GET  /evaluate            → Manual evaluation page             │ ║
║  │  └─ GET  /admin/*             → Admin diagnostics                  │ ║
║  └─────────────────────────────────────────────────────────────────────┘ ║
║                                  ▲                                        ║
║                                  │                                        ║
║                                  ▼                                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                      MACHINE LEARNING PIPELINE LAYER                      ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐ ║
║  │               SCIKIT-LEARN ML MODELS (model.py)                     │ ║
║  │                                                                     │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐│ ║
║  │  │ CLASSIFICATION ENSEMBLE (Success Prediction)                   ││ ║
║  │  │                                                                ││ ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ ││ ║
║  │  │  │  RandomForest    │  │ HistGradient     │  │  ExtraTrees  │ ││ ║
║  │  │  │  Classifier      │  │ Boosting         │  │  Classifier  │ ││ ║
║  │  │  │  (200-400 trees) │  │ Classifier       │  │              │ ││ ║
║  │  │  └──────────────────┘  └──────────────────┘  └──────────────┘ ││ ║
║  │  │                                                                ││ ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐                   ││ ║
║  │  │  │  Logistic        │  │  Voting          │                   ││ ║
║  │  │  │  Regression      │  │  Ensemble        │                   ││ ║
║  │  │  │  (Linear)        │  │  (Soft)          │                   ││ ║
║  │  │  └──────────────────┘  └──────────────────┘                   ││ ║
║  │  │                                                                ││ ║
║  │  │  → Best model selected by cross-validation accuracy           ││ ║
║  │  │  → Typical accuracy: 75-85%                                   ││ ║
║  │  └────────────────────────────────────────────────────────────────┘│ ║
║  │                                                                     │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐│ ║
║  │  │ REGRESSION MODELS (Funding & Valuation)                        ││ ║
║  │  │                                                                ││ ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐                   ││ ║
║  │  │  │  RandomForest    │  │  RandomForest    │                   ││ ║
║  │  │  │  Regressor       │  │  Regressor       │                   ││ ║
║  │  │  │  (Funding)       │  │  (Valuation)     │                   ││ ║
║  │  │  │  300 trees       │  │  300 trees       │                   ││ ║
║  │  │  └──────────────────┘  └──────────────────┘                   ││ ║
║  │  │                                                                ││ ║
║  │  │  → R² scores: 80-85%                                          ││ ║
║  │  └────────────────────────────────────────────────────────────────┘│ ║
║  │                                                                     │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐│ ║
║  │  │ FEATURE ENGINEERING                                            ││ ║
║  │  │                                                                ││ ║
║  │  │  Numerical (11):   Categorical (9):                           ││ ║
║  │  │  • funding_amount  • industry (12 categories)                 ││ ║
║  │  │  • valuation       • location (8 regions)                     ││ ║
║  │  │  • team_size       • funding_round (5 stages)                 ││ ║
║  │  │  • company_age     • status (4 types)                         ││ ║
║  │  │  • num_investors   • age_category (5 bins)                    ││ ║
║  │  │  • competition     • team_size_category                       ││ ║
║  │  │  • market_size     • competition_category                     ││ ║
║  │  │  • efficiency      • industry_group                           ││ ║
║  │  │  • per_employee    • region                                   ││ ║
║  │  │  • log(funding)    → One-hot encoded                          ││ ║
║  │  │  • log(valuation)  → StandardScaler normalized                ││ ║
║  │  │                                                                ││ ║
║  │  │  Total: ~50-100 features after encoding                       ││ ║
║  │  └────────────────────────────────────────────────────────────────┘│ ║
║  └─────────────────────────────────────────────────────────────────────┘ ║
║                                  ▲                                        ║
║                                  │                                        ║
║                                  ▼                                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                            DATA LAYER                                     ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────┐ ║
║  │   Kaggle API  │  │   Pandas      │  │   NumPy       │  │  Synthetic│ ║
║  │   (Primary)   │  │   DataFrame   │  │   Arrays      │  │  Fallback │ ║
║  │               │  │               │  │               │  │           │ ║
║  │  kagglehub    │  │  In-memory    │  │  Numerical    │  │  1000     │ ║
║  │  download     │  │  processing   │  │  operations   │  │  samples  │ ║
║  │               │  │               │  │               │  │           │ ║
║  │  investments  │  │  Filtering,   │  │  Transforms,  │  │  Auto-    │ ║
║  │  _VC.csv      │  │  sorting,     │  │  scaling,     │  │  generated│ ║
║  │               │  │  aggregation  │  │  math funcs   │  │           │ ║
║  │  400 rows     │  │               │  │               │  │           │ ║
║  │  (default)    │  │               │  │               │  │           │ ║
║  └───────────────┘  └───────────────┘  └───────────────┘  └───────────┘ ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                         CACHING & PERSISTENCE                             ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐ ║
║  │                    THREE-LEVEL CACHE SYSTEM                         │ ║
║  │                                                                     │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐│ ║
║  │  │ LEVEL 1: IN-MEMORY CACHE (RAM)                                ││ ║
║  │  │  • ANALYSIS_CACHE = {}       # Company analyses               ││ ║
║  │  │  • sample_data = DataFrame   # Loaded dataset                 ││ ║
║  │  │  • precomputed_tiers = []    # Tier assignments               ││ ║
║  │  │  Speed: Milliseconds                                          ││ ║
║  │  │  Persistence: Until restart                                   ││ ║
║  │  └────────────────────────────────────────────────────────────────┘│ ║
║  │                                                                     │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐│ ║
║  │  │ LEVEL 2: FILE SYSTEM CACHE (.model_cache/)                    ││ ║
║  │  │  • classifier_<sig>.pkl      # Trained models                 ││ ║
║  │  │  • regressor_<sig>.pkl       # Model weights                  ││ ║
║  │  │  • scaler_<sig>.pkl          # Feature scaler                 ││ ║
║  │  │  • precompute_<sig>.pkl      # Precomputed tiers              ││ ║
║  │  │  • analysis_cache_<sig>.pkl  # Analysis results               ││ ║
║  │  │  Speed: 100-200ms load time                                   ││ ║
║  │  │  Persistence: Across restarts                                 ││ ║
║  │  │  Invalidation: Data signature or schema version change        ││ ║
║  │  └────────────────────────────────────────────────────────────────┘│ ║
║  │                                                                     │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐│ ║
║  │  │ LEVEL 3: BACKGROUND TRAINING (Async Thread)                   ││ ║
║  │  │  • Runs full model training in background                     ││ ║
║  │  │  • Updates cache when complete                                ││ ║
║  │  │  • Doesn't block startup or requests                          ││ ║
║  │  │  Speed: 30-60 seconds                                         ││ ║
║  │  │  Benefit: Instant startup with eventual full accuracy         ││ ║
║  │  └────────────────────────────────────────────────────────────────┘│ ║
║  └─────────────────────────────────────────────────────────────────────┘ ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                       VISUALIZATION LAYER                                 ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────┐ ║
║  │              MATPLOTLIB (Server-Side Chart Generation)              │ ║
║  │                                                                     │ ║
║  │  6-Chart Analysis Dashboard:                                       │ ║
║  │  ┌─────────────┬─────────────┬─────────────┐                      │ ║
║  │  │   Gauge     │  Bar Chart  │   Donut     │                      │ ║
║  │  │  (Score)    │ (Benchmark) │  (Factors)  │                      │ ║
║  │  ├─────────────┼─────────────┼─────────────┤                      │ ║
║  │  │ Horizontal  │   Scatter   │    Radar    │                      │ ║
║  │  │    Bar      │ (Risk-Ret)  │ (Business)  │                      │ ║
║  │  └─────────────┴─────────────┴─────────────┘                      │ ║
║  │                                                                     │ ║
║  │  Features:                                                          │ ║
║  │  • Enhanced styling (shadows, gradients, borders)                  │ ║
║  │  • Unique color schemes per chart                                  │ ║
║  │  • 120 DPI resolution                                              │ ║
║  │  • Base64 PNG encoding                                             │ ║
║  │  • ~340KB file size                                                │ ║
║  │  • 2-3 second generation time                                      │ ║
║  └─────────────────────────────────────────────────────────────────────┘ ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Data Flow Diagram

```
┌─────────────┐
│    USER     │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. Browse companies
       ▼
┌─────────────────────────────────────────────────┐
│  GET /api/companies?tier=invest&industry=fintech│
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Flask Route Handler              │
│   • Parse query parameters         │
│   • Apply filters to sample_data   │
│   • Use precomputed tier column    │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Return JSON                      │
│   {                                │
│     companies: [                   │
│       {name, industry, tier, ...}, │
│       ...                          │
│     ]                              │
│   }                                │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   JavaScript (Frontend)            │
│   • Render company cards           │
│   • Attach click handlers          │
└──────┬─────────────────────────────┘
       │
       │ 2. User clicks "Analyze Company"
       ▼
┌─────────────────────────────────────────────────┐
│  POST /analyze_company/CompanyName              │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Flask Route Handler              │
│   • Extract company name           │
│   • Call analyze_company()         │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Check ANALYSIS_CACHE             │
│   if company_id in cache:          │
│     return cached_result           │
│   else:                            │
│     continue to analysis           │
└──────┬─────────────────────────────┘
       │ Cache miss
       ▼
┌────────────────────────────────────┐
│   Fetch Company Data               │
│   • Query sample_data DataFrame    │
│   • Extract features               │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Feature Engineering              │
│   • Create derived features        │
│   • One-hot encode categoricals    │
│   • Scale numerical features       │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────┐
│   ML Model Inference (Parallel)                │
│   ┌─────────────────────────────────────────┐  │
│   │ Classification                          │  │
│   │ success_prob = classifier.predict_proba()│  │
│   └─────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────┐  │
│   │ Regression 1                            │  │
│   │ funding = regressor.predict()           │  │
│   └─────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────┐  │
│   │ Regression 2                            │  │
│   │ valuation = regressor.predict()         │  │
│   └─────────────────────────────────────────┘  │
└──────┬─────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Apply Probability Tempering      │
│   • Shrink prediction toward base  │
│   • Prevent overconfidence         │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Calculate Attractiveness Score   │
│   • Weighted combination           │
│   • success_prob * 70              │
│   • market_norm * 15               │
│   • team_norm * 10                 │
│   • investor_norm * 5              │
│   • Apply hard gating              │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Assign Investment Tier           │
│   • score >= 65: Invest            │
│   • score >= 50: Monitor           │
│   • score < 50: Avoid              │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Generate Insights                │
│   • Rule-based analysis            │
│   • Risk factor identification     │
│   • Strength/weakness detection    │
│   • Investment commentary          │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Create Dashboard Charts          │
│   • 6 matplotlib charts            │
│   • Enhanced styling               │
│   • Base64 PNG encoding            │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Cache Result                     │
│   ANALYSIS_CACHE[company_id] = {   │
│     score, tier, insights,         │
│     charts, commentary, etc.       │
│   }                                │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   Return JSON Response             │
│   {                                │
│     attractiveness_score: 72.4,    │
│     success_probability: 0.68,     │
│     recommendation: "Invest",      │
│     risk_level: "Medium",          │
│     insights: [...],               │
│     risk_factors: [...],           │
│     commentary: [...],             │
│     dashboard_image: "data:image..." │
│   }                                │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   JavaScript (Frontend)            │
│   • Parse JSON response            │
│   • Display modal with analysis    │
│   • Populate 5 tabs                │
│   • Render chart image             │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│   User Views Analysis              │
│   • Reads insights                 │
│   • Explores charts                │
│   • Switches tabs                  │
│   • Makes investment decision      │
└────────────────────────────────────┘
```

---

## ML Training Pipeline

```
START: train_models() called
│
├─ STEP 1: Data Loading
│  ├─ Try Kaggle API (kagglehub)
│  │  └─ Success? → Load investments_VC.csv
│  │      └─ Failure? → Check local cache
│  │          └─ Failure? → Generate synthetic data
│  └─ Result: Raw DataFrame (400-10000 rows)
│
├─ STEP 2: Data Cleaning
│  ├─ Parse funding amounts ("$1.2M" → 1200000)
│  ├─ Handle missing values (median imputation)
│  ├─ Consolidate industries (50+ → 12 categories)
│  ├─ Map locations to regions (countries → 8 regions)
│  ├─ Create success labels (acquired/IPO = 1)
│  └─ Apply success rate calibration (target 25%)
│
├─ STEP 3: Feature Engineering
│  ├─ Numerical (11 features)
│  │  ├─ Raw: funding, valuation, team, age, etc.
│  │  ├─ Derived: efficiency, per-employee ratios
│  │  └─ Transforms: log(funding), log(valuation)
│  │
│  ├─ Categorical (9 features)
│  │  ├─ One-hot encode: industry, location, round
│  │  └─ Binned: age category, team size category
│  │
│  └─ StandardScaler: Normalize numerical features
│
├─ STEP 4: Train-Test Split
│  ├─ 80% training, 20% testing
│  ├─ Stratified for balanced classes
│  └─ Random state = 42 for reproducibility
│
├─ STEP 5: Model Training (Parallel)
│  │
│  ├─ Classification Models
│  │  ├─ RandomForestClassifier
│  │  │  ├─ GridSearchCV (n_estimators, max_depth, etc.)
│  │  │  ├─ 3-fold cross-validation
│  │  │  └─ Select best hyperparameters
│  │  │
│  │  ├─ HistGradientBoostingClassifier
│  │  │  ├─ GridSearchCV (learning_rate, max_iter, etc.)
│  │  │  └─ Often best performer
│  │  │
│  │  ├─ ExtraTreesClassifier
│  │  │  └─ Similar to RF but more randomized
│  │  │
│  │  ├─ LogisticRegression
│  │  │  └─ Linear baseline for comparison
│  │  │
│  │  └─ VotingClassifier
│  │     └─ Soft ensemble of all above
│  │
│  └─ Regression Models
│     ├─ RandomForestRegressor (funding prediction)
│     └─ RandomForestRegressor (valuation prediction)
│
├─ STEP 6: Model Evaluation
│  ├─ Test all models on held-out test set
│  ├─ Compare accuracies
│  ├─ Select best classifier
│  └─ Typical results:
│     ├─ Classification accuracy: 75-85%
│     └─ Regression R²: 80-85%
│
├─ STEP 7: Threshold Tuning (Optional)
│  ├─ Try thresholds from 0.3 to 0.7
│  ├─ Find optimal for accuracy
│  └─ Wrap in ThresholdedClassifier
│
├─ STEP 8: Model Persistence
│  ├─ Save classifier → .model_cache/classifier_<sig>.pkl
│  ├─ Save regressors → .model_cache/regressor_<sig>.pkl
│  ├─ Save scaler → .model_cache/scaler_<sig>.pkl
│  ├─ Save feature metadata
│  └─ Compute data signature for cache validation
│
└─ STEP 9: Tier Precomputation
   ├─ For each company in sample_data:
   │  ├─ Run analyze_company_comprehensive()
   │  ├─ Extract tier and score
   │  └─ Add to DataFrame columns
   ├─ Save to cache → .model_cache/precompute_<sig>.pkl
   └─ Result: Instant tier filtering
│
END: Models ready for inference
```

---

## Caching Strategy Flowchart

```
┌─────────────────────────────────────┐
│  Application Startup                │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ Check Cache? │
        └──────┬───────┘
               │
       ┌───────┴───────┐
       │               │
   Yes │               │ No
       ▼               ▼
┌──────────────┐  ┌──────────────┐
│ Load from    │  │ Train models │
│ .pkl files   │  │ from scratch │
└──────┬───────┘  └──────┬───────┘
       │                 │
       │                 ▼
       │          ┌──────────────┐
       │          │ Save to cache│
       │          └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
         ┌────────────────┐
         │ Models Ready   │
         │ (2-3 seconds)  │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────────────┐
         │ Kickoff Background     │
         │ Training (Optional)    │
         └────────┬───────────────┘
                  │
                  ▼
         ┌────────────────────────┐
         │ Server Ready to        │
         │ Handle Requests        │
         └────────────────────────┘

───────────────────────────────────────

Analysis Request Flow:

┌─────────────────────────────────────┐
│  User clicks "Analyze Company"      │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────────┐
        │ Check            │
        │ ANALYSIS_CACHE?  │
        └──────┬───────────┘
               │
       ┌───────┴───────┐
       │               │
   Hit │               │ Miss
       ▼               ▼
┌──────────────┐  ┌──────────────┐
│ Return       │  │ Run ML       │
│ instantly    │  │ inference    │
│ (<10ms)      │  │ (50-100ms)   │
└──────────────┘  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Generate     │
                  │ charts       │
                  │ (2-3 sec)    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Store in     │
                  │ cache        │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Return to    │
                  │ user         │
                  └──────────────┘

Cache Invalidation:

┌─────────────────────────────────────┐
│  Trigger?                           │
│  • Schema version change            │
│  • Data signature change            │
│  • Manual clear (admin endpoint)    │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────────┐
        │ Clear all caches │
        │ • .pkl files     │
        │ • In-memory dicts│
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────┐
        │ Retrain models   │
        │ Rebuild caches   │
        └──────────────────┘
```

---

## Component Interaction Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  index.html                                                     │
│  ├─ Company Catalog                                            │
│  │  ├─ Search Bar ───────────► JavaScript filter function     │
│  │  ├─ Tier Filter ──────────► updateCompanyList()            │
│  │  ├─ Industry Filter ──────► AJAX to /api/companies         │
│  │  └─ Company Cards ────────► Click → analyzeCompany()       │
│  │                                                             │
│  └─ Analysis Modal                                             │
│     ├─ Overview Tab ──────────► displayCompanyAnalysis()      │
│     ├─ Benchmarks Tab ────────► displayBenchmarks()           │
│     ├─ Fundamentals Tab ──────► displayFundamentals()         │
│     ├─ Risk Analysis Tab ─────► displayRiskFactors()          │
│     └─ Commentary Tab ─────────► displayInvestmentCommentary()│
│                                                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ AJAX Requests
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                         BACKEND                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  app.py (Flask Application)                                    │
│  ├─ @app.route('/')                                            │
│  │  └─ render_template('index.html')                          │
│  │                                                             │
│  ├─ @app.route('/api/companies')                              │
│  │  ├─ Parse filters (tier, industry, location)              │
│  │  ├─ Query sample_data DataFrame                            │
│  │  └─ Return JSON list                                       │
│  │                                                             │
│  └─ @app.route('/analyze_company/<name>')                     │
│     ├─ Call model.analyze_company_comprehensive()             │
│     ├─ Generate charts with model.create_analysis_dashboard() │
│     └─ Return JSON with analysis + base64 image               │
│                                                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Function Calls
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                       ML PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  model.py (Machine Learning Core)                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DATA FUNCTIONS                                          │  │
│  │  ├─ load_data()                                          │  │
│  │  ├─ download_kaggle_startup_data()                       │  │
│  │  ├─ process_investments_vc_data()                        │  │
│  │  └─ generate_startup_data()  # Synthetic fallback        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FEATURE ENGINEERING                                     │  │
│  │  ├─ engineer_features()                                  │  │
│  │  ├─ prepare_features_for_prediction()                    │  │
│  │  ├─ consolidate_industry()                               │  │
│  │  └─ map_location_to_region()                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MODEL TRAINING                                          │  │
│  │  ├─ train_models()                                       │  │
│  │  ├─ _fast_bootstrap_models()                            │  │
│  │  ├─ _background_train_worker()                          │  │
│  │  └─ kickoff_background_training()                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SCORING & ANALYSIS                                      │  │
│  │  ├─ analyze_company_comprehensive()                      │  │
│  │  ├─ calculate_attractiveness_score()                     │  │
│  │  ├─ _apply_probability_policy()                         │  │
│  │  ├─ get_recommendation()                                │  │
│  │  ├─ generate_insights()                                 │  │
│  │  └─ generate_investment_commentary()                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VISUALIZATION                                           │  │
│  │  ├─ create_analysis_dashboard()                         │  │
│  │  └─ Returns base64 PNG image                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CACHING                                                 │  │
│  │  ├─ _load_models_from_cache()                           │  │
│  │  ├─ _save_models_to_cache()                             │  │
│  │  ├─ _load_precompute_from_cache()                       │  │
│  │  └─ _save_precompute_to_cache()                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PRECOMPUTATION                                          │  │
│  │  └─ precompute_investment_tiers()                        │  │
│  │     ├─ Analyze all companies                             │  │
│  │     ├─ Add tier column to sample_data                    │  │
│  │     └─ Cache results                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

This visual architecture document provides graphical representations of the Deal Scout system's structure, data flow, and component interactions to complement the detailed technical documentation in TECH_STACK.md.
