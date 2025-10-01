# Deal Scout Startup Flow with Auto-Precompute

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Server Startup (0:00)                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  python app.py   │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Fast Bootstrap (0:00 - 0:05)                           │
│ ✓ Generate 300 sample companies                                │
│ ✓ Train lightweight models                                      │
│ ✓ Precompute tiers for bootstrap data                          │
│ → Server becomes responsive (with temp data)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Flask Server Starts (0:05)                             │
│ ✓ HTTP server listening on port 5000                           │
│ ✓ API endpoints available                                       │
│ ✓ Web interface accessible                                      │
│ → Users can browse (but see 50% scores for real data)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├──────────────────┐
                              │                  │
                              ▼                  ▼
                    ┌────────────────┐  ┌────────────────┐
                    │  THREAD 1:     │  │  THREAD 2:     │
                    │  Background    │  │  Startup Check │
                    │  Training      │  │  (app.py)      │
                    └────────────────┘  └────────────────┘
                              │                  │
                              ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4a: Background Training (0:05 - 2:30)                     │
│ • Load real Kaggle dataset (2000 companies)                    │
│ • Train production ML models                                    │
│ • Load from cache if available                                  │
└─────────────────────────────────────────────────────────────────┘
│ STEP 4b: Startup Check (0:15)                                  │
│ • Wait 10 seconds for background thread                        │
│ • Check if precomputed data exists                             │
│ • If not, queue for later check                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Training Completes (2:30)                              │
│ ✓ Models trained and validated                                 │
│ ✓ Check PRECOMPUTE_DISABLE flag                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ PRECOMPUTE_      │
                    │ DISABLE = false? │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                YES │                   │ NO
                    ▼                   ▼
        ┌────────────────────┐  ┌─────────────────┐
        │ STEP 6:            │  │ Manual Trigger  │
        │ Auto-Precompute    │  │ Required        │
        │ (model.py)         │  │ (Old Behavior)  │
        └────────────────────┘  └─────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Auto-Precompute Runs (2:30 - 4:30)                     │
│ • Call precompute_investment_tiers(max_rows=None)              │
│ • Process all 2000 companies                                    │
│ • Calculate attractiveness scores                               │
│ • Assign investment tiers (Invest/Monitor/Avoid)               │
│ • Add columns to sample_data DataFrame                          │
│ • Progress: 400...800...1200...1600...2000                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Precompute Complete (4:30)                             │
│ ✅ All 2000 companies have accurate scores                     │
│ ✅ DataFrame updated with precomputed columns                  │
│ ✅ Startup check thread verifies availability                  │
│ ✅ Cache saved to disk for future startups                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Fully Ready! (4:30+)                                   │
│ ✓ Server running with real data                                │
│ ✓ All companies showing accurate scores                        │
│ ✓ Tier filtering works instantly                               │
│ ✓ No manual intervention needed                                │
│                                                                 │
│ User Experience:                                                │
│ • Company List: Varied scores (20-85%)                         │
│ • Analysis Dashboard: Matches company list scores              │
│ • Tier Filter: Fast filtering (<1 second)                      │
│ • Consistent: List scores = Analysis scores ✅                 │
└─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
                         KEY POINTS
═══════════════════════════════════════════════════════════════════

⏱️  TIMELINE:
   0:05 - Server is responsive (bootstrap data)
   2:30 - Real models trained
   4:30 - Full precomputation complete
   
🎯 USER EXPERIENCE:
   0:00-4:30  → Can browse, but sees 50% scores
   4:30+      → Sees accurate varied scores
   
⚡ PERFORMANCE:
   Bootstrap: 300 companies, instant
   Full: 2000 companies, ~4-5 min total
   Cached: ~30 seconds (next startup)
   
🔧 CONTROL:
   PRECOMPUTE_DISABLE=true  → Old behavior (manual)
   PRECOMPUTE_DISABLE=false → Auto-precompute (default)
   
🔄 FALLBACK:
   If auto-precompute fails, startup check tries again
   If both fail, manual trigger still available
   
═══════════════════════════════════════════════════════════════════
```

## Data Flow Diagram

```
┌────────────────┐
│  Bootstrap     │
│  sample_data   │  ← 300 synthetic companies with precomputed scores
│  (In Memory)   │
└────────┬───────┘
         │
         │ Background Training Loads Real Data
         ▼
┌────────────────┐
│  Real Data     │
│  sample_data   │  ← 2000 real companies (NO precomputed scores yet)
│  (In Memory)   │
└────────┬───────┘
         │
         │ Auto-Precompute Triggered
         ▼
┌────────────────┐
│  Full Data     │
│  sample_data   │  ← 2000 companies WITH precomputed scores
│  + Precomputed │     ✓ precomputed_attractiveness_score
│  (In Memory)   │     ✓ precomputed_investment_tier
└────────┬───────┘     ✓ precomputed_investment_tier_norm
         │             ✓ precomputed_recommendation
         │             ✓ precomputed_risk_level
         ▼
┌────────────────┐
│  Cache Saved   │
│  (On Disk)     │  ← Saved for faster next startup
└────────────────┘
```

## Flask App Data Access (After Fix)

```
OLD (BROKEN):
┌─────────────┐
│  app.py     │
│  endpoint   │──┐
└─────────────┘  │
                 │ from model import sample_data
                 ▼
         ┌──────────────┐
         │ Local Copy   │  ← Stale reference!
         │ sample_data  │     (No precomputed columns)
         └──────────────┘


NEW (FIXED):
┌─────────────┐
│  app.py     │
│  endpoint   │──┐
└─────────────┘  │
                 │ model.sample_data
                 ▼
         ┌──────────────┐
         │  model.py    │
         │  sample_data │  ← Current reference!
         │  (Global)    │     (WITH precomputed columns)
         └──────────────┘
```

---

**Visual Reference for Understanding Auto-Precompute Flow**
