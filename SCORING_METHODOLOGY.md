# Deal Scout Investment Scoring Methodology

## Overview

Deal Scout uses a hybrid approach combining **machine learning predictions** with **rule-based scoring** to evaluate startup investment opportunities. This document explains the complete methodology used to generate the **Investment Attractiveness Score** (0-100 scale) and assign companies to investment tiers.

---

## Table of Contents

1. [Machine Learning Models](#machine-learning-models)
2. [Success Probability Prediction](#success-probability-prediction)
3. [Attractiveness Score Calculation](#attractiveness-score-calculation)
4. [Investment Tier Assignment](#investment-tier-assignment)
5. [Scoring Components Breakdown](#scoring-components-breakdown)
6. [Probability Calibration & Coherence](#probability-calibration--coherence)
7. [Data Processing Pipeline](#data-processing-pipeline)

---

## 1. Machine Learning Models

Deal Scout employs an **ensemble of machine learning models** to predict startup success and financial outcomes:

### Classification Models (Success Prediction)

The system trains multiple classifiers and selects the best performer:

1. **Random Forest Classifier**
   - 200-400 estimators
   - Balanced class weights (`balanced_subsample`)
   - Grid search optimized for max depth, min samples, and feature selection
   - Strong baseline with excellent interpretability

2. **Histogram Gradient Boosting Classifier**
   - Fast, memory-efficient gradient boosting
   - Excellent performance on tabular data
   - Handles missing values natively
   - Often the top performer

3. **Extra Trees Classifier**
   - Extremely randomized trees (more randomization than Random Forest)
   - Reduces overfitting on noisy features
   - Fast training and prediction

4. **Logistic Regression**
   - L2 regularization with balanced class weights
   - Strong linear baseline
   - Provides probability calibration reference

5. **Soft Voting Ensemble**
   - Combines predictions from top 3 models
   - Weighted by individual model accuracy
   - Often achieves best generalization

**Model Selection:** The system evaluates all trained models on a held-out test set and selects the classifier with the highest accuracy. Typical accuracy ranges from **75-85%** depending on data quality.

### Regression Models (Financial Predictions)

Two separate **Random Forest Regressors** predict:

1. **Funding Amount Predictor**
   - 300 estimators, no max depth limit
   - Predicts expected funding based on company characteristics
   - Used to assess if a company is over/under-funded

2. **Valuation Predictor**
   - 300 estimators, no max depth limit
   - Estimates company valuation
   - Helps identify valuation anomalies

Both regressors achieve **R² scores typically above 80%** on test data.

### Model Training Process

```
1. Data Preparation (Kaggle real data or synthetic fallback)
2. Feature Engineering (44+ features generated)
3. Train/Test Split (80/20, stratified for classification)
4. Grid Search Cross-Validation (3-fold CV)
5. Model Evaluation & Selection
6. Decision Threshold Tuning (optimizes classification boundary)
7. Feature Bundle Binding (prevents inference mismatches)
8. Model Caching (instant startup on subsequent runs)
```

---

## 2. Success Probability Prediction

### Base Probability Generation

The trained classifier generates a **raw success probability** (0-1 scale) using `predict_proba()`:

```python
success_probability = classifier.predict_proba(X)[0][1]
```

This probability represents the model's confidence that a startup will achieve a successful outcome (acquisition, IPO, or sustained operating success).

### Success Rate Configuration

The system uses realistic VC outcome rates:

```python
SUCCESS_RATE_CONFIG = {
    'target_success_rate': 0.25,           # 25% overall success rate
    'acquired_ipo_rate': 1.0,              # Acquired/IPO = 100% success
    'operating_base_rate': 0.28,           # 28% for operating companies
    'closed_success_rate': 0.05,           # 5% for closed companies
    'unknown_status_rate': 0.35,           # 35% for unknown status
    'funding_boost_threshold': 2000000,    # $2M+ funding boosts probability
    'high_funding_boost_threshold': 10000000,  # $10M+ extra boost
}
```

### Probability Shrinkage (Anti-Overconfidence)

To prevent overconfident predictions, the system applies **conservative shrinkage**:

1. **Temperature Scaling** (τ = 1.2): Flattens probability distribution in logit space
2. **Prior Blending**: Mixes prediction with base prior (0.4) at 20% weight
3. **Context-Aware**: Automatically applied in precompute mode, optional in interactive mode

This ensures probabilities are **well-calibrated** and reflect real-world uncertainty.

---

## 3. Attractiveness Score Calculation

The Investment Attractiveness Score is a **weighted composite** of multiple factors, with success probability dominating:

### Formula

```
Attractiveness Score = (
    Success_Probability_Normalized × 70.0 +
    Market_Opportunity_Score × 15.0 +
    Team_Strength_Score × 8.0 +
    Investor_Validation_Score × 7.0
)
```

### Component Normalization (Strict Bounds)

#### 1. Success Probability (70% weight)

**Mapping:** Linear transformation from [0.25, 0.85] → [0, 1]

```python
sp_norm = max(0.0, min(1.0, (success_probability - 0.25) / 0.60))
```

- Below 25% probability → 0.0 normalized score
- Above 85% probability → 1.0 normalized score
- **Stricter than previous versions** to increase selectivity

#### 2. Market Opportunity (15% weight)

**Formula:** Logistic transform of (market_size - 2×competition)

```python
market_norm = 1 / (1 + exp(-0.15 × (market_size - 2×competition)))
```

- Large markets with low competition → High score
- Crowded markets penalized heavily (2× competition weight)
- Prevents saturation, bounded [0, 1]

#### 3. Team Strength (8% weight)

**Formula:** Logarithmic normalization with reference max = 200 employees

```python
team_norm = log(1 + team_size) / log(1 + 200)
```

- Approaches 1.0 near 200 employees
- Prevents early saturation for small teams
- Rewards scaling but with diminishing returns

#### 4. Investor Validation (7% weight)

**Formula:** Logarithmic normalization with reference max = 15 investors

```python
investors_norm = log(1 + num_investors) / log(1 + 15)
```

- Approaches 1.0 near 15 investors
- Strong signal for investor confidence
- Diminishing returns beyond elite backing

### Gating Rules (Prevents Overly Lenient Scores)

The system applies **hard caps** based on success probability:

```python
if success_probability < 0.40:
    score = min(score, 49)  # Force into Avoid tier
elif success_probability < 0.50:
    score = min(score, 64)  # Cap at Monitor tier
```

This ensures companies with poor fundamentals **cannot** achieve high scores through other metrics alone.

---

## 4. Investment Tier Assignment

### Three-Tier System

Companies are classified into investment tiers based on their **Attractiveness Score**:

| Tier | Score Range | Color | Interpretation |
|------|-------------|-------|----------------|
| **Invest** | 65-100 | 🟢 Green | Strong investment opportunity with favorable risk/return profile |
| **Monitor** | 50-64 | 🟡 Yellow | Promising but requires further due diligence or market development |
| **Avoid** | 0-49 | 🔴 Red | Significant risks or unfavorable characteristics |

### Tier Thresholds (Updated for Selectivity)

Previous versions used 60/45 thresholds. Current version uses **65/50** to be more selective:

```python
TIER_SCORE_BOUNDS = {
    'invest': (65.0, 100.0),   # Raised from 60.0
    'monitor': (50.0, 64.9),   # Raised from 45.0
    'avoid': (0.0, 49.9),
}
```

### Expected Distribution

With **strict scoring disabled normalization**, the natural distribution typically shows:

- **10-20% Invest tier**: Only genuinely strong opportunities
- **30-40% Monitor tier**: Solid but not exceptional
- **40-60% Avoid tier**: Significant concerns or early-stage uncertainty

**Note:** Distribution normalization was intentionally **DISABLED** (as of 2025-10-01 schema version) to allow natural scoring based on actual company quality rather than forcing artificial percentages.

---

## 5. Scoring Components Breakdown

In addition to the overall attractiveness score, the system calculates **detailed component scores** for transparency:

### Financial Score

```python
financial_score = (
    funding_factor × 0.35 +
    valuation_factor × 0.35 +
    funding_efficiency × 0.30
) × 100
```

- **Funding Factor**: Log-normalized funding amount (ref: $20M)
- **Valuation Factor**: Log-normalized valuation (ref: $100M)
- **Funding Efficiency**: Valuation / Funding ratio (capped)

### Market Score

```python
market_score = (
    market_size_norm × 0.60 +
    (1 - competition_norm) × 0.40
) × 100
```

- **Market Size**: Log-normalized TAM (ref: $50B)
- **Competition**: Inverted 10-point scale (low competition → high score)

### Team Score

```python
team_score = (
    team_size_norm × 0.50 +
    experience_factor × 0.50
) × 100
```

- **Team Size**: Log-normalized headcount (ref: 150)
- **Experience**: Years operating / 10 (capped at 1.0)

### Growth Score

```python
growth_score = (
    investor_count_norm × 0.40 +
    funding_round_progress × 0.30 +
    industry_strength × 0.30
) × 100
```

- **Investor Count**: Log-normalized (ref: 12)
- **Funding Round**: Categorical progress (Seed → Series D+)
- **Industry Strength**: Sector-specific success rates

These component scores are displayed in the UI to help users understand **what drives** each company's overall rating.

---

## 6. Probability Calibration & Coherence

### Tier-Probability Coherence Policy

To ensure consistency, the system enforces **coherence between tiers and probabilities**:

```python
TIER_PROBABILITY_BOUNDS = {
    'invest': (0.60, 1.00),    # 60-100% success probability
    'monitor': (0.40, 0.65),   # 40-65% success probability
    'avoid': (0.00, 0.45),     # 0-45% success probability
}
```

If a company's tier (based on score) and probability band conflict, the system:

1. **Chooses the riskier tier** (higher risk rank)
2. **Adjusts probability** if beyond tolerance (±1.5%)
3. **Aligns score** to the final tier's bounds

This prevents misleading situations like "Invest tier with 30% success probability."

### Probability Band Labels

Qualitative labels help communicate uncertainty:

| Probability Range | Band Label | Description |
|-------------------|------------|-------------|
| 60-100% | Strong Outlook | High confidence in success |
| 45-60% | Moderate Outlook | Reasonable chance of success |
| 0-45% | Uncertain Outlook | Significant execution risks |

---

## 7. Data Processing Pipeline

### Feature Engineering (44+ Features)

The system generates a rich feature set from raw company data:

**Derived Financial Metrics:**
- `funding_efficiency` = valuation / funding
- `funding_per_employee` = funding / team_size
- `funding_amount_log` = log(1 + funding)
- `valuation_log` = log(1 + valuation)

**Categorical Encodings:**
- Industry (12 consolidated categories + Other)
- Region (8 geographic regions)
- Funding Round (Seed, Series A-D+)
- Company Status (Operating, Acquired, IPO, Closed)

**Binned Categories:**
- Age: Startup (<1y), Early (1-3y), Growth (3-5y), Mature (5-10y), Established (10y+)
- Team Size: Small (<10), Medium (10-50), Large (50-100), Very Large (100-500), Enterprise (500+)
- Competition: Low (0-3), Medium (3-6), High (6-8), Very High (8-10)

**One-Hot Encoding:** All categorical features are one-hot encoded with `drop_first=True` to avoid multicollinearity.

### Scaling & Standardization

Numerical features are **standardized** using `StandardScaler`:

```python
scaled_feature = (feature - mean) / std_dev
```

This ensures all features contribute proportionally to model predictions regardless of their original scale.

### Robust Inference Pipeline

The system uses **feature bundle binding** to prevent mismatches:

1. During training, the exact feature columns, numerical columns, and scaler are **bound to the classifier**
2. During inference, features are aligned to match the training schema exactly
3. Missing dummy variables are filled with zeros
4. Prevents errors when concurrent background training updates globals

---

## Model Performance Metrics

### Classification Performance

- **Accuracy:** 75-85% (varies by data source)
- **Cross-Validation:** 3-fold CV during grid search
- **Threshold Tuning:** Decision boundary optimized beyond default 0.5

### Regression Performance

- **Funding Predictor R²:** Typically 80-85%
- **Valuation Predictor R²:** Typically 80-85%

### Cache & Performance

- **Model Caching:** Trained models cached to `.model_cache/` directory
- **Cache Validation:** SHA-256 hash of training data + schema version
- **Precomputation:** Investment tiers precomputed for instant filtering
- **Startup Time:** <1 second with cached models, 10-30 seconds for full training

---

## Scoring Schema Version

The current scoring schema version is: **`2025-10-01-stricter-tiers`**

This version includes:
- ✅ Raised tier thresholds (65/50 vs 60/45)
- ✅ Stricter success probability normalization (0.25-0.85 range)
- ✅ Disabled distribution normalization override
- ✅ Enhanced gating rules (sp<0.40 → Avoid, sp<0.50 → Monitor cap)
- ✅ Lower base success rates (operating: 28% vs 40%)
- ✅ Conservative probability shrinkage policy

Cache invalidation occurs when the schema version changes to ensure consistency.

---

## Configuration Options

### Environment Variables

The scoring system respects several configuration flags:

- `KAGGLE_MAX_ROWS`: Limit data loading (default: 400 for faster startup)
- `PRECOMPUTE_MAX_ROWS`: Limit tier precomputation (default: 400)
- `SKIP_KAGGLE`: Force synthetic data mode (default: false)
- `AUTO_TRAIN_ON_IMPORT`: Train immediately on module load (default: false)
- `BOOTSTRAP_FAST`: Use quick bootstrap models (default: true)
- `LAZY_BACKGROUND_TRAIN`: Train in background thread (default: true)
- `SHRINK_PROBABILITY_INTERACTIVE`: Apply shrinkage in interactive mode (default: true)
- `FORCE_RETRAIN`: Bypass model cache (default: false)

### Adjustable Parameters

Success rate targets can be adjusted programmatically:

```python
adjust_success_rate(target_rate=0.25)  # 25% success rate (current)
adjust_success_rate(target_rate=0.35)  # 35% success rate (more lenient)
```

This automatically recalculates `operating_base_rate` to achieve the target distribution.

---

## Summary

Deal Scout's scoring methodology combines:

1. **State-of-the-art ML models** (ensemble selection from 5+ classifiers)
2. **Strict, bounded normalization** (prevents score inflation)
3. **Conservative probability calibration** (shrinkage prevents overconfidence)
4. **Multi-factor weighted scoring** (70% ML prediction + 30% rule-based)
5. **Hard gating rules** (prevents gaming the system)
6. **Tier-probability coherence** (ensures consistency)

The result is a **robust, interpretable, and well-calibrated** investment scoring system that reflects real-world VC success rates and helps investors make data-driven decisions.

---

## References

- Scikit-learn Documentation: https://scikit-learn.org/
- Random Forest Classifier: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
- Histogram Gradient Boosting: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html
- Probability Calibration: https://scikit-learn.org/stable/modules/calibration.html

