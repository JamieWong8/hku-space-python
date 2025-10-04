#!/usr/bin/env python3
"""
Deal Scout - Machine Learning Models and Data Processing
Extracted from Jupyter notebook for Flask web application
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
import json
import threading
import joblib
import hashlib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, HistGradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, r2_score
import warnings
warnings.filterwarnings('ignore')

# Kaggle API integration - completely optional
KAGGLE_AVAILABLE = False
kaggle = None

# Bump this when scoring/normalization logic meaningfully changes to invalidate caches
SCORING_SCHEMA_VERSION = '2025-10-01-stricter-tiers'

# Tier/probability coherence policy (kept close to schema version for easy invalidation)
TIER_DISPLAY_LABELS = {'invest': 'Invest', 'monitor': 'Monitor', 'avoid': 'Avoid'}
TIER_RISK_ORDER = {'invest': 0, 'monitor': 1, 'avoid': 2}
TIER_PROBABILITY_BOUNDS = {
    'invest': (0.60, 1.00),    # Raised from 0.55 to be more selective
    'monitor': (0.40, 0.65),   # Raised from 0.35 to be more selective
    'avoid': (0.00, 0.45),     # Adjusted upper bound from 0.45 to match monitor
}
TIER_SCORE_BOUNDS = {
    'invest': (65.0, 100.0),   # Raised from 60.0 to be more selective
    'monitor': (50.0, 64.9),   # Raised from 45.0 to be more selective
    'avoid': (0.0, 49.9),      # Adjusted from 44.9 to match monitor
}
COHERENCE_TOLERANCE = 0.015

def initialize_kaggle():
    """Initialize Kaggle API only when needed"""
    global KAGGLE_AVAILABLE, kaggle
    
    if kaggle is not None:
        return KAGGLE_AVAILABLE
    
    try:
        # Only try to import kaggle when explicitly requested
        # This will not be called during module import
        print("Loading: Attempting to initialize Kaggle API...")
        import kaggle as kaggle_module
        kaggle = kaggle_module
        KAGGLE_AVAILABLE = True
        print("Success: Kaggle API module loaded successfully")
        return True
    except ImportError:
        print("Warning: Kaggle package not available. Install with: pip install kaggle")
        return False
    except Exception as e:
        print(f"Warning: Kaggle initialization error: {e}")
        print("   This is normal if you haven't set up Kaggle credentials yet.")
        return False

# Global constants
INDUSTRIES = ['Fintech', 'Healthcare', 'E-commerce', 'SaaS', 'AI/ML', 'Biotech', 
              'EdTech', 'Gaming', 'Cybersecurity', 'IoT', 'Blockchain', 'Marketing']

LOCATIONS = ['San Francisco', 'New York', 'London', 'Singapore', 'Boston', 
             'Los Angeles', 'Seattle', 'Austin', 'Berlin', 'Toronto', 'Sydney', 'Tel Aviv']

FUNDING_ROUNDS = ['Seed', 'Series A', 'Series B', 'Series C', 'Series D+']

# Success rate configuration
SUCCESS_RATE_CONFIG = {
    'target_success_rate': 0.25,  # Target 25% overall success rate (more realistic for VC)
    'acquired_ipo_rate': 1.0,     # Companies marked as acquired/IPO are always successful
    'operating_base_rate': 0.28,  # Lower base rate for operating companies (more selective)
    'closed_success_rate': 0.05,  # Fewer closed companies were successful exits
    'unknown_status_rate': 0.35,  # Lower success rate for unknown status
    'funding_boost_threshold': 2000000,  # $2M+ funding boosts success probability (higher threshold)
    'high_funding_boost_threshold': 10000000,  # $10M+ funding gets extra boost (higher threshold)
    'enable_industry_boost': True,  # Whether to boost certain industries
    'enable_location_boost': True,  # Whether to boost certain locations
}

# Global models and data (initialized when module loads)
startup_classifier = None
startup_regressor = None
startup_valuation_regressor = None
feature_scaler = None
feature_columns = None
sample_data = None
# Persist training-time numerical feature names for robust prediction-time alignment
training_numerical_columns = None
# Lightweight cache for analysis results keyed by company_id
ANALYSIS_CACHE = {}
data_source = "synthetic"  # Track current data source
grouped_industries = None  # unique consolidated industries
regions = None  # unique region groups (formerly 'continents')
# Deprecated alias maintained temporarily for backwards compatibility
continents = None  # DEPRECATED: use 'regions' instead


def _bind_feature_bundle_to_classifier(clf, feat_cols, numericals, scaler):
    """Bind feature/scale metadata to a classifier (and its base_estimator if wrapped).

    This lets inference retrieve the exact expected feature columns and scaler
    irrespective of concurrent background model updates.
    """
    try:
        setattr(clf, '_ds_feature_columns', list(feat_cols) if feat_cols is not None else [])
        setattr(clf, '_ds_numerical_columns', list(numericals) if numericals is not None else [])
        setattr(clf, '_ds_scaler', scaler)
        base = getattr(clf, 'base_estimator', None)
        if base is not None:
            try:
                setattr(base, '_ds_feature_columns', list(feat_cols) if feat_cols is not None else [])
                setattr(base, '_ds_numerical_columns', list(numericals) if numericals is not None else [])
                setattr(base, '_ds_scaler', scaler)
            except Exception:
                pass
    except Exception:
        pass


def _parse_money_to_usd(value) -> tuple[float, bool]:
    """Parse a money string like "$1.2M", "800k", "2B", "1,000,000", or 1000000 into a float USD.

    Returns (amount, has_amount_flag), where has_amount_flag indicates if an authoritative funding_total_usd
    was present and parsed as a positive number.
    """
    try:
        if value is None:
            return 0.0, False
        s = str(value).strip()
        if not s or s in {'-', '—', 'None', 'null', 'NaN', 'nan', 'N/A'}:
            return 0.0, False
        s_up = s.upper().replace('USD', '').replace('US$', '').replace('U$D', '')
        # Remove common currency symbols and commas/spaces/quotes
        for ch in ['$', '€', '£', ',', ' ', '"']:
            s_up = s_up.replace(ch, '')
        # Detect suffix multipliers
        mult = 1.0
        if len(s_up) >= 1 and s_up[-1] in {'K', 'M', 'B'}:
            suffix = s_up[-1]
            s_up = s_up[:-1]
            if suffix == 'K':
                mult = 1e3
            elif suffix == 'M':
                mult = 1e6
            elif suffix == 'B':
                mult = 1e9
        # Some strings might still include trailing plus or tilde; strip non-numeric trailing chars
        while len(s_up) > 0 and not (s_up[-1].isdigit() or s_up[-1] == '.' ):
            s_up = s_up[:-1]
        # Likewise leading
        while len(s_up) > 0 and not (s_up[0].isdigit() or s_up[0] == '.' ):
            s_up = s_up[1:]
        amount = float(s_up) if s_up else 0.0
        amount *= mult
        if np.isfinite(amount) and amount > 0:
            return float(amount), True
        return 0.0, False
    except Exception:
        return 0.0, False


def _find_funding_total_column(columns) -> str | None:
    """Return the column name from a sequence of columns that represents funding_total_usd,
    being robust to spaces, punctuation, and line breaks in the header.
    """
    try:
        for col in columns:
            norm = ''.join(ch for ch in str(col).lower() if ch.isalnum())
            if norm == 'fundingtotalusd':
                return col
        return None
    except Exception:
        return None


class ThresholdedClassifier:
    """Lightweight wrapper to apply a tuned decision threshold to any probabilistic classifier.

    - Keeps predict_proba passthrough intact for downstream consumers.
    - Overrides predict() to use the tuned threshold instead of 0.5.
    - Does not alter the underlying estimator; purely a wrapper.
    """
    def __init__(self, base_estimator, threshold: float = 0.5):
        self.base_estimator = base_estimator
        self.threshold = float(threshold)

    def fit(self, X, y):
        self.base_estimator.fit(X, y)
        return self

    def predict_proba(self, X):
        return self.base_estimator.predict_proba(X)

    def predict(self, X):
        proba = self.predict_proba(X)
        # Use probability of positive class (column 1) with tuned threshold
        return (proba[:, 1] >= self.threshold).astype(int)

    # Convenience accessors
    @property
    def classes_(self):
        return getattr(self.base_estimator, 'classes_', None)

    def __repr__(self):
        base = repr(self.base_estimator)
        return f"ThresholdedClassifier(base={base}, threshold={self.threshold:.3f})"

# -----------------------------
# Model caching utilities
# -----------------------------

def _compute_data_signature(df: pd.DataFrame) -> str:
    """Compute a lightweight signature of the training data to validate cache.

    Uses row/col counts and coarse sums of key numeric columns.
    """
    try:
        cols = df.columns
        acc = f"schema={SCORING_SCHEMA_VERSION}|rows={len(df)}|cols={len(cols)}"
        for c in ['funding_amount_usd', 'valuation_usd', 'team_size', 'num_investors']:
            if c in cols and df[c].notna().any():
                s = float(pd.to_numeric(df[c], errors='coerce').fillna(0.0).sum())
                acc += f"|{c}={int(s)}"
        return hashlib.sha256(acc.encode('utf-8')).hexdigest()
    except Exception:
        return hashlib.sha256(f"schema={SCORING_SCHEMA_VERSION}|fallback={len(df)}x{len(df.columns)}".encode('utf-8')).hexdigest()


def _get_model_cache_dir() -> Path:
    here = Path(__file__).resolve().parent
    cache_dir = here / '.model_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _load_models_from_cache(sig: str):
    cache = _get_model_cache_dir()
    meta_path = cache / 'meta.json'
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if meta.get('data_signature') != sig:
            return None
        payload = {
            'startup_classifier': joblib.load(cache / 'startup_classifier.pkl'),
            'startup_regressor': joblib.load(cache / 'startup_regressor.pkl'),
            'startup_valuation_regressor': joblib.load(cache / 'startup_valuation_regressor.pkl'),
            'feature_scaler': joblib.load(cache / 'feature_scaler.pkl'),
            'feature_columns': json.loads((cache / 'feature_columns.json').read_text(encoding='utf-8')),
            'training_numerical_columns': json.loads((cache / 'training_numerical_columns.json').read_text(encoding='utf-8')),
        }
        print(f"Cache: Loaded trained models from {cache}")
        return payload
    except Exception as e:
        print(f"Cache: Failed to load models from cache: {e}")
        return None


def _save_models_to_cache(sig: str, classifier, regressor, val_regressor, scaler, feat_cols, train_num_cols):
    cache = _get_model_cache_dir()
    try:
        joblib.dump(classifier, cache / 'startup_classifier.pkl')
        joblib.dump(regressor, cache / 'startup_regressor.pkl')
        joblib.dump(val_regressor, cache / 'startup_valuation_regressor.pkl')
        joblib.dump(scaler, cache / 'feature_scaler.pkl')
        (cache / 'feature_columns.json').write_text(json.dumps(list(feat_cols)), encoding='utf-8')
        (cache / 'training_numerical_columns.json').write_text(json.dumps(list(train_num_cols)), encoding='utf-8')
        meta = {
            'data_signature': sig,
            'sklearn_version': __import__('sklearn').__version__,
        }
        (cache / 'meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        print(f"Cache: Saved trained models to {cache}")
    except Exception as e:
        print(f"Cache: Failed to save models to cache: {e}")


def _precompute_cache_paths(sig: str):
    cache = _get_model_cache_dir()
    return {
        'precomputed_df': cache / f'precompute_{sig}.pkl',
        'analysis_cache': cache / f'analysis_cache_{sig}.pkl',
    }


def _load_precompute_from_cache(sig: str) -> bool:
    """Try to load precomputed tier columns and ANALYSIS_CACHE from cache into sample_data.
    Returns True if applied.
    """
    global sample_data, ANALYSIS_CACHE
    try:
        paths = _precompute_cache_paths(sig)
        if not (paths['precomputed_df'].exists() and paths['analysis_cache'].exists()):
            return False
        pre_df = joblib.load(paths['precomputed_df'])
        if 'company_id' not in pre_df.columns or 'company_id' not in sample_data.columns:
            return False
        # Merge precomputed columns by company_id
        cols = [c for c in pre_df.columns if c != 'company_id']
        sample_data = sample_data.merge(pre_df[['company_id'] + cols], on='company_id', how='left', suffixes=(None, None))
        ANALYSIS_CACHE = joblib.load(paths['analysis_cache'])
        print("Cache: Loaded precomputed tiers from cache")
        return True
    except Exception as e:
        print(f"Cache: Failed to load precomputed tiers: {e}")
        return False


def _save_precompute_to_cache(sig: str):
    """Persist current precomputed columns and ANALYSIS_CACHE to cache."""
    try:
        paths = _precompute_cache_paths(sig)
        cols = [
            'company_id',
            'precomputed_attractiveness_score',
            'precomputed_investment_tier',
            'precomputed_investment_tier_norm',
            'precomputed_recommendation',
            'precomputed_risk_level',
        ]
        avail = [c for c in cols if c in sample_data.columns]
        if 'company_id' in avail and len(avail) > 1:
            pre_df = sample_data[avail].copy()
            joblib.dump(pre_df, paths['precomputed_df'])
            joblib.dump(ANALYSIS_CACHE, paths['analysis_cache'])
            print("Cache: Saved precomputed tiers to cache")
    except Exception as e:
        print(f"Cache: Failed to save precomputed tiers: {e}")

# -----------------------------
# Normalization & grouping utils
# -----------------------------

def consolidate_industry(raw_industry: str) -> str:
    """Map raw industry strings into a consolidated set of categories.

    Returns one of:
    ['Fintech','Healthcare','E-commerce','SaaS','AI/ML','Biotech','EdTech','Gaming','Cybersecurity','IoT','Blockchain','Marketing','Other']
    """
    if not isinstance(raw_industry, str) or not raw_industry.strip():
        return 'Other'
    s = raw_industry.strip().lower()

    # Keyword groupings
    groups = [
        ('Fintech', ['fintech', 'finance', 'payment', 'payments', 'remittance', 'bank', 'insurtech', 'lending', 'wealth']),
        ('Healthcare', ['health', 'med', 'medtech', 'clinic', 'care', 'pharma-care']),
        ('E-commerce', ['e-commerce', 'ecommerce', 'commerce', 'retail', 'marketplace', 'shop', 'shopping']),
        ('SaaS', ['saas', 'software', 'enterprise software', 'b2b software', 'crm', 'erp', 'collaboration']),
        ('AI/ML', ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'genai', 'computer vision', 'nlp']),
        ('Biotech', ['biotech', 'bio', 'genomic', 'genomics', 'drug', 'therapeutic', 'life science']),
        ('EdTech', ['edtech', 'education', 'learning', 'tutoring', 'mooc']),
        ('Gaming', ['gaming', 'games', 'game', 'esports']),
        ('Cybersecurity', ['cyber', 'security', 'infosec', 'endpoint', 'siem']),
        ('IoT', ['iot', 'internet of things', 'smart home', 'embedded', 'hardware', 'sensor']),
        ('Blockchain', ['blockchain', 'crypto', 'web3', 'defi', 'nft']),
        ('Marketing', ['marketing', 'adtech', 'advertis', 'martech', 'growth'])
    ]

    for label, keywords in groups:
        for kw in keywords:
            if kw in s:
                return label

    # Specific direct mappings from common labels
    direct = {
        'technology': 'SaaS',
        'software': 'SaaS',
        'mobile': 'SaaS',
        'social media': 'Marketing',
        'cleantech': 'Other',
        'green tech': 'Other',
        'agritech': 'Other',
        'proptech': 'Other',
    }
    if s in direct:
        return direct[s]

    return 'Other'


def map_location_to_region(raw_location: str) -> str:
    """Map a country code/name or common city to a region bucket.

    Returns one of: ['North America','Europe','Asia','South America','Africa','Oceania','Middle East','Other']
    """
    if not isinstance(raw_location, str) or not raw_location.strip():
        return 'Other'
    s = raw_location.strip()
    s_up = s.upper()
    s_low = s.lower()

    # ISO-like country code mapping (2/3 letters and common names)
    # North America (includes Central America per policy)
    na = {
        'US', 'USA', 'UNITED STATES',
        'CAN', 'CA', 'CANADA',
        'MEX', 'MX', 'MEXICO',
        # Clarified
        'CRI', 'COSTA RICA',
        'PAN', 'PANAMA',
    }
    # Europe
    eu = {
        'GB', 'GBR', 'UK', 'UNITED KINGDOM', 'ENG',
        'DE', 'DEU', 'GERMANY',
        'FR', 'FRA', 'FRANCE',
        'ES', 'ESP', 'SPAIN',
        'IT', 'ITA', 'ITALY',
        'NL', 'NLD', 'NETHERLANDS',
        'SE', 'SWE', 'SWEDEN',
        # Added based on dataset
        'DNK', 'DENMARK',
        'IRL', 'IRELAND',
        'CHE', 'SWITZERLAND',
        'BEL', 'BELGIUM',
        'FIN', 'FINLAND',
        'LTU', 'LITHUANIA',
        'NOR', 'NORWAY',
        'PRT', 'PORTUGAL',
        'POL', 'POLAND',
        'CZE', 'CZECHIA', 'CZECH REPUBLIC',
        'ROM', 'ROU', 'ROMANIA',
        'AUT', 'AUSTRIA',
        'EST', 'ESTONIA',
        'HRV', 'CROATIA',
        'HUN', 'HUNGARY',
        'BGR', 'BULGARIA',
        'LVA', 'LATVIA',
        'ISL', 'ICELAND',
        'UKR', 'UKRAINE',
        # Clarified: Russia as Europe per policy
        'RUS', 'RUSSIA',
    }
    # Asia
    asia = {
        'CN', 'CHN', 'CHINA',
        'IN', 'IND', 'INDIA',
        'JP', 'JPN', 'JAPAN',
        'SG', 'SGP', 'SINGAPORE',
        'KR', 'KOR', 'SOUTH KOREA', 'KOREA, REPUBLIC OF',
        # Added based on dataset / clarification
        'HKG', 'HONG KONG',
        'TWN', 'TAIWAN',
        'THA', 'THAILAND',
        'PHL', 'PHILIPPINES',
        'VNM', 'VIETNAM',
        'IDN', 'INDONESIA',
        'KHM', 'CAMBODIA',
    }
    # South America
    sa = {
        'BR', 'BRA', 'BRAZIL',
        'AR', 'ARG', 'ARGENTINA',
        'CL', 'CHL', 'CHILE',
        # Added
        'PER', 'PERU',
        'URY', 'URUGUAY',
        'COL', 'COLOMBIA',
    }
    # Africa
    af = {
        'ZA', 'ZAF', 'SOUTH AFRICA',
        'NG', 'NGA', 'NIGERIA',
        'EG', 'EGY', 'EGYPT',
        'KE', 'KEN', 'KENYA',
        # Added
        'GHA', 'GHANA',
        'BWA', 'BOTSWANA',
    }
    # Oceania
    oc = {'AU', 'AUS', 'AUSTRALIA', 'NZ', 'NZL', 'NEW ZEALAND'}
    # Middle East (per policy includes Turkey and Jordan)
    me = {
        'AE', 'ARE', 'UAE', 'UNITED ARAB EMIRATES',
        'SA', 'SAU', 'SAUDI ARABIA',
        'IL', 'ISR', 'ISRAEL',
        'TUR', 'TURKEY',
        'JOR', 'JORDAN',
    }

    if s_up in na:
        return 'North America'
    if s_up in eu:
        return 'Europe'
    if s_up in asia:
        return 'Asia'
    if s_up in sa:
        return 'South America'
    if s_up in af:
        return 'Africa'
    if s_up in oc:
        return 'Oceania'
    if s_up in me:
        return 'Middle East'

    # City-name heuristics (cover common cities in our constants and dataset)
    city_to_continent = {
        # North America
        'san francisco': 'North America', 'new york': 'North America', 'boston': 'North America',
        'los angeles': 'North America', 'seattle': 'North America', 'austin': 'North America', 'toronto': 'North America',
        # Europe
        'london': 'Europe', 'berlin': 'Europe', 'paris': 'Europe', 'amsterdam': 'Europe', 'stockholm': 'Europe',
        # Asia
        'singapore': 'Asia', 'tokyo': 'Asia', 'bangalore': 'Asia', 'bengaluru': 'Asia', 'beijing': 'Asia', 'shanghai': 'Asia',
        # Oceania
        'sydney': 'Oceania', 'melbourne': 'Oceania',
        # Middle East
        'tel aviv': 'Middle East', 'dubai': 'Middle East', 'abu dhabi': 'Middle East'
    }
    if s_low in city_to_continent:
        return city_to_continent[s_low]

    return 'Other'

# Backwards compatibility alias (temporary)
def map_location_to_continent(raw_location: str) -> str:  # pragma: no cover - transitional alias
    return map_location_to_region(raw_location)

def adjust_success_rate(target_rate=0.35):
    """
    Adjust the target success rate configuration.
    
    Args:
        target_rate (float): Desired overall success rate (0.0 to 1.0)
                           0.25 = 25% success rate
                           0.35 = 35% success rate (default)
                           0.50 = 50% success rate
    """
    global SUCCESS_RATE_CONFIG
    
    SUCCESS_RATE_CONFIG['target_success_rate'] = target_rate
    
    # Adjust operating base rate to achieve target
    if target_rate <= 0.2:
        SUCCESS_RATE_CONFIG['operating_base_rate'] = 0.2
    elif target_rate <= 0.3:
        SUCCESS_RATE_CONFIG['operating_base_rate'] = 0.35
    elif target_rate <= 0.4:
        SUCCESS_RATE_CONFIG['operating_base_rate'] = 0.45
    elif target_rate <= 0.5:
        SUCCESS_RATE_CONFIG['operating_base_rate'] = 0.55
    else:
        SUCCESS_RATE_CONFIG['operating_base_rate'] = 0.65
    
    print(f"Success: Success rate target adjusted to {target_rate:.1%}")
    print(f"   Operating companies base rate: {SUCCESS_RATE_CONFIG['operating_base_rate']:.1%}")

def setup_kaggle_credentials():
    """
    Set up Kaggle API credentials from various sources.
    """
    if not initialize_kaggle():
        return False
    
    # Check for credentials in multiple locations
    credential_locations = [
        "kaggle.json",  # Current directory
        "kaggle_template.json",  # Template file (user should rename and fill)
        os.path.expanduser("~/.kaggle/kaggle.json"),  # Standard location
        os.path.join(os.path.dirname(__file__), "kaggle.json"),  # Flask app directory
    ]
    
    for cred_file in credential_locations:
        if os.path.exists(cred_file):
            try:
                with open(cred_file, 'r') as f:
                    creds = json.load(f)
                
                # Check if it's the template file (with placeholder values)
                if creds.get('username') == 'your_kaggle_username':
                    print(f"Warning: Found template file {cred_file}. Please update with your actual Kaggle credentials.")
                    continue
                
                # Set environment variables for Kaggle API
                os.environ['KAGGLE_USERNAME'] = creds['username']
                os.environ['KAGGLE_KEY'] = creds['key']
                
                # Try to authenticate
                try:
                    kaggle.api.authenticate()
                    print(f"Success: Kaggle credentials loaded from {cred_file}")
                    return True
                except Exception as auth_error:
                    print(f"Warning: Failed to authenticate with {cred_file}: {auth_error}")
                    continue
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Invalid credentials file {cred_file}: {e}")
                continue
    
    print("Warning: No valid Kaggle credentials found. Using synthetic data.")
    return False

def merge_startup_datasets(companies_df, investments_df, funding_df=None):
    """
    Merge company, investment, and funding data to create comprehensive startup dataset with real names.
    """
    try:
        print(f"   Merging {len(companies_df)} companies with {len(investments_df)} investments...")
        
        # Sample companies for performance (take first 5000 companies)
        if len(companies_df) > 5000:
            companies_sample = companies_df.head(5000).copy()
            print(f"   Sampling {len(companies_sample)} companies for performance")
        else:
            companies_sample = companies_df.copy()
        
        # Create startup data with real company names
        startup_data = []
        
        for idx, company in companies_sample.iterrows():
            if pd.isna(company.get('name')) or company.get('name') == '':
                continue
                
            # Extract basic company info
            company_data = {
                'company_id': f"crunchbase_{company['entity_id']}",
                'company_name': str(company['name']).strip(),
                'industry': company.get('category_code', '').title() if pd.notna(company.get('category_code')) else np.random.choice(INDUSTRIES),
                'location': company.get('city', '') if pd.notna(company.get('city')) else np.random.choice(LOCATIONS),
                'status': company.get('status', 'operating').title() if pd.notna(company.get('status')) else 'Operating',
            }
            
            # Parse founded date
            founded_at = company.get('founded_at')
            if pd.notna(founded_at):
                try:
                    founded_date = pd.to_datetime(founded_at)
                    current_year = pd.Timestamp.now().year
                    years_since_founding = max(0.1, current_year - founded_date.year)
                    company_data['years_since_founding'] = min(years_since_founding, 50)  # Cap at 50 years
                except:
                    company_data['years_since_founding'] = np.random.uniform(0.5, 10)
            else:
                company_data['years_since_founding'] = np.random.uniform(0.5, 10)
            
            # Add funding information if available
            funding_total = company.get('funding_total_usd')
            if pd.notna(funding_total) and funding_total > 0:
                company_data['funding_amount_usd'] = float(funding_total)
            else:
                # Generate realistic funding based on age and industry
                base_funding = np.random.uniform(100000, 20000000)
                company_data['funding_amount_usd'] = base_funding
            
            # Generate valuation (typically 8-20x funding)
            valuation_multiplier = np.random.uniform(8, 20)
            company_data['valuation_usd'] = company_data['funding_amount_usd'] * valuation_multiplier
            
            # Generate other realistic metrics
            company_data.update({
                'funding_round': np.random.choice(FUNDING_ROUNDS),
                'team_size': max(1, int(np.random.uniform(5, 200))),
                'revenue_usd': max(0, np.random.uniform(0, company_data['funding_amount_usd'] / 2)),
                'num_investors': max(1, int(np.random.uniform(1, 15))),
                'competition_level': np.random.randint(1, 11),
                'market_size_billion_usd': np.random.uniform(0.5, 100),
            })
            
            # Determine success based on status and realistic factors
            status_lower = company_data['status'].lower()
            if status_lower in ['acquired', 'ipo']:
                company_data['is_successful'] = 1
                company_data['success_score'] = 1.0
            elif status_lower in ['closed', 'dead']:
                company_data['is_successful'] = 0
                company_data['success_score'] = 0.0
            else:
                # For operating companies, use probabilistic success based on factors
                success_prob = 0.4  # Base probability
                
                # Adjust based on factors
                if company_data['years_since_founding'] > 5:
                    success_prob += 0.1
                if company_data['funding_amount_usd'] > 5000000:
                    success_prob += 0.1
                if company_data['revenue_usd'] > 1000000:
                    success_prob += 0.2
                
                company_data['is_successful'] = 1 if np.random.random() < success_prob else 0
                company_data['success_score'] = success_prob
            
            startup_data.append(company_data)
            
            # Stop if we have enough data for performance
            if len(startup_data) >= 2000:
                break
        
        if len(startup_data) == 0:
            print("   No valid startup data could be created from merged datasets")
            return None
        
        merged_df = pd.DataFrame(startup_data)
        print(f"   Successfully created merged dataset with {len(merged_df)} companies")
        print(f"   Sample company names: {merged_df['company_name'].head(3).tolist()}")
        
        return merged_df
        
    except Exception as e:
        print(f"   Error merging startup datasets: {e}")
        return None

def process_investments_vc_data(df):
    """Process investments_VC.csv data from kagglehub download"""
    try:
        print(f"   Processing {len(df)} rows from investments_VC.csv...")
        
        startup_data = []
        for idx, row in df.head(2000).iterrows():  # Limit for performance
            try:
                # Extract real company name from the CSV
                real_company_name = None
                if 'name' in row and pd.notna(row['name']) and str(row['name']).strip():
                    real_company_name = str(row['name']).strip()
                elif 'company_name' in row and pd.notna(row['company_name']) and str(row['company_name']).strip():
                    real_company_name = str(row['company_name']).strip()
                
                if not real_company_name:
                    continue  # Skip rows without company names
                
                # Extract real industry/market info
                industry = 'Technology'  # Default
                if 'market' in row and pd.notna(row['market']) and str(row['market']).strip():
                    market_str = str(row['market']).strip()
                    if market_str and market_str != ' ':
                        industry = market_str
                elif 'category_list' in row and pd.notna(row['category_list']):
                    cat_str = str(row['category_list']).strip()
                    if cat_str and '|' in cat_str:
                        # Extract first category from |Entertainment|Politics|Social Media|
                        categories = [c.strip() for c in cat_str.split('|') if c.strip()]
                        if categories:
                            industry = categories[0]
                
                # Extract location info
                location = 'US'  # Default
                if 'country_code' in row and pd.notna(row['country_code']):
                    location = str(row['country_code']).strip()
                elif 'city' in row and pd.notna(row['city']):
                    location = str(row['city']).strip()
                
                # Extract and clean funding amount from funding_total_usd (robust parser)
                funding_amount = 0.0
                has_funding_total = False
                ft_col = _find_funding_total_column(df.columns)
                if ft_col and ft_col in row and pd.notna(row[ft_col]):
                    funding_amount, has_funding_total = _parse_money_to_usd(row[ft_col])
                
                # Extract status
                status = 'Operating'  # Default
                if 'status' in row and pd.notna(row['status']):
                    status_str = str(row['status']).strip().title()
                    if status_str:
                        status = status_str
                
                # Determine success based on status with configurable criteria
                is_successful = 0
                
                if status.lower() in ['acquired', 'ipo']:
                    is_successful = 1 if np.random.random() < SUCCESS_RATE_CONFIG['acquired_ipo_rate'] else 0
                elif status.lower() in ['operating', 'active']:
                    # Use configured base rate for operating companies
                    is_successful = 1 if np.random.random() < SUCCESS_RATE_CONFIG['operating_base_rate'] else 0
                else:
                    # Unknown/other statuses
                    is_successful = 1 if np.random.random() < SUCCESS_RATE_CONFIG['unknown_status_rate'] else 0
                
                # Create startup data entry (initialize; valuation computed after factors)
                company_data = {
                    'company_id': f'vc_{idx:04d}',
                    'company_name': real_company_name,
                    'industry': industry,
                    'location': location,
                    'funding_round': np.random.choice(['Seed', 'Series A', 'Series B', 'Series C']),
                    'funding_amount_usd': funding_amount,
                    # revenue retained only for internal signals; UI omits
                    'revenue_usd': funding_amount * np.random.uniform(0.1, 2.0),
                    'team_size': int(np.random.uniform(5, 200)),
                    'years_since_founding': np.random.uniform(0.5, 15.0),
                    'num_investors': int(np.random.uniform(1, 10)),
                    'competition_level': int(np.random.uniform(1, 10)),
                    'market_size_billion_usd': np.random.uniform(1.0, 50.0),
                    'status': status,
                    'is_successful': is_successful,
                    'success_score': float(is_successful),
                    # Track whether this row had a valid funding_total_usd to allow downstream filtering
                    'has_funding_total_usd': bool(has_funding_total),
                    # Keep raw field for diagnostics if present
                    'funding_total_usd_raw': str(row[ft_col]).strip() if ft_col and ft_col in row and pd.notna(row[ft_col]) else ''
                }
                # Compute valuation using funding and other scoring criteria
                # Base multiplier anchored to stage and fundamentals
                stage = company_data['funding_round']
                stage_factor = {
                    'Seed': 6.0, 'Series A': 10.0, 'Series B': 14.0, 'Series C': 18.0
                }.get(stage, 8.0)
                market_adj = min(4.0, company_data['market_size_billion_usd'] / 10.0)  # up to +4
                team_adj = min(2.0, company_data['team_size'] / 100.0 * 2.0)  # up to +2
                comp_adj = - min(2.0, company_data['competition_level'] / 10.0 * 2.0)  # up to -2
                # Ensure valuation only computed if funding known; else remain 0 (will be excluded from display)
                if company_data['funding_amount_usd'] > 0:
                    multiplier = max(3.0, stage_factor + market_adj + team_adj + comp_adj)
                    company_data['valuation_usd'] = float(company_data['funding_amount_usd'] * multiplier)
                else:
                    company_data['valuation_usd'] = 0.0
                startup_data.append(company_data)
            except Exception as e:
                print(f"   Error processing row {idx}: {e}")
                continue
        
        if startup_data:
            result_df = pd.DataFrame(startup_data)
            print(f"Success: Processed {len(result_df)} companies from kagglehub download")
            return (result_df, "kaggle:arindam235/startup-investments-crunchbase")
        
        return None
    except Exception as e:
        print(f"Error: Failed to process investments_VC.csv data: {e}")
        return None

def download_kaggle_startup_data():
    """
    Download real startup datasets from Kaggle using kagglehub with timeout and failsafe.
    """
    import threading
    import time
    
    def load_local_investments_vc():
        """Failsafe: Load from local investments_VC.csv"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_csv = os.path.join(script_dir, 'kaggle_data', 'investments_VC.csv')
            
            # Get max rows from environment variable (default 400)
            max_rows = int(os.environ.get('KAGGLE_MAX_ROWS', '400'))
            
            if os.path.exists(local_csv):
                print(f"Loading: Loading failsafe data from investments_VC.csv (max {max_rows} rows)...")
                
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(local_csv, low_memory=False, encoding=encoding, nrows=max_rows)
                        print(f"Success: Successfully loaded with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"   Failed with {encoding}: {e}")
                        continue
                
                if df is None:
                    print("Error: Could not load CSV with any encoding")
                    return None
                
                # Convert to startup format using real company names
                startup_data = []
                for idx, row in df.head(max_rows).iterrows():  # Use max_rows limit for performance
                    try:
                        # Extract real company name from the CSV
                        real_company_name = None
                        if 'name' in row and pd.notna(row['name']) and str(row['name']).strip():
                            real_company_name = str(row['name']).strip()
                        elif 'company_name' in row and pd.notna(row['company_name']) and str(row['company_name']).strip():
                            real_company_name = str(row['company_name']).strip()
                        
                        if not real_company_name:
                            continue  # Skip rows without company names
                        
                        # Extract real industry/market info
                        industry = 'Technology'  # Default
                        if 'market' in row and pd.notna(row['market']) and str(row['market']).strip():
                            market_str = str(row['market']).strip()
                            if market_str and market_str != ' ':
                                industry = market_str
                        elif 'category_list' in row and pd.notna(row['category_list']):
                            cat_str = str(row['category_list']).strip()
                            if cat_str and '|' in cat_str:
                                # Extract first category from |Entertainment|Politics|Social Media|
                                categories = [c.strip() for c in cat_str.split('|') if c.strip()]
                                if categories:
                                    industry = categories[0]
                        
                        # Extract location info
                        location = 'US'  # Default
                        if 'country_code' in row and pd.notna(row['country_code']):
                            location = str(row['country_code']).strip()
                        elif 'city' in row and pd.notna(row['city']):
                            location = str(row['city']).strip()
                        
                        # Extract and clean funding amount from funding_total_usd and track presence
                        funding_amount = 0.0
                        has_funding_total = False
                        raw_funding_str = ''
                        ft_col = _find_funding_total_column(df.columns)
                        if ft_col and ft_col in row and pd.notna(row[ft_col]):
                            funding_str = str(row[ft_col]).strip()
                            raw_funding_str = funding_str
                            parsed, flag = _parse_money_to_usd(funding_str)
                            if flag:
                                funding_amount = parsed
                                has_funding_total = True
                        
                        # Extract status
                        status = 'Operating'  # Default
                        if 'status' in row and pd.notna(row['status']):
                            status_str = str(row['status']).strip().title()
                            if status_str:
                                status = status_str
                        
                        # Determine success based on status with configurable criteria
                        is_successful = 0
                        
                        if status.lower() in ['acquired', 'ipo']:
                            is_successful = 1 if np.random.random() < SUCCESS_RATE_CONFIG['acquired_ipo_rate'] else 0
                        elif status.lower() in ['operating']:
                            # Start with base success rate for operating companies
                            success_probability = SUCCESS_RATE_CONFIG['operating_base_rate']
                            
                            # Boost probability based on funding amount
                            if funding_amount > SUCCESS_RATE_CONFIG['high_funding_boost_threshold']:
                                success_probability += 0.2
                            elif funding_amount > SUCCESS_RATE_CONFIG['funding_boost_threshold']:
                                success_probability += 0.1
                            
                            # Industry-based boost
                            if SUCCESS_RATE_CONFIG['enable_industry_boost']:
                                high_success_industries = ['software', 'saas', 'fintech', 'healthcare', 'ai/ml', 'technology']
                                medium_success_industries = ['electronics', 'mobile', 'games', 'e-commerce']
                                
                                if any(ind in industry.lower() for ind in high_success_industries):
                                    success_probability += 0.15
                                elif any(ind in industry.lower() for ind in medium_success_industries):
                                    success_probability += 0.1
                            
                            # Location-based boost
                            if SUCCESS_RATE_CONFIG['enable_location_boost']:
                                major_tech_hubs = ['USA', 'US', 'GBR', 'UK', 'CAN', 'DEU', 'FRA']
                                if location.upper() in major_tech_hubs:
                                    success_probability += 0.1
                            
                            # Cap probability and make decision
                            success_probability = min(0.85, success_probability)
                            is_successful = np.random.choice([0, 1], p=[1-success_probability, success_probability])
                            
                        elif status.lower() in ['closed']:
                            is_successful = np.random.choice([0, 1], p=[1-SUCCESS_RATE_CONFIG['closed_success_rate'], SUCCESS_RATE_CONFIG['closed_success_rate']])
                        else:
                            # Empty or unknown status
                            is_successful = np.random.choice([0, 1], p=[1-SUCCESS_RATE_CONFIG['unknown_status_rate'], SUCCESS_RATE_CONFIG['unknown_status_rate']])
                        
                        company_data = {
                            'company_id': f"vc_{idx:04d}",
                            'company_name': real_company_name,
                            'industry': industry,
                            'location': location,
                            'funding_round': np.random.choice(['Seed', 'Series A', 'Series B', 'Series C']),
                            'funding_amount_usd': funding_amount,
                            # valuation computed below using funding + factors
                            'valuation_usd': 0.0,
                            'revenue_usd': funding_amount * np.random.uniform(0.05, 0.3),
                            'team_size': np.random.randint(5, 100),
                            'years_since_founding': np.random.uniform(1, 8),
                            'num_investors': np.random.randint(1, 10),
                            'competition_level': np.random.randint(1, 10),
                            'market_size_billion_usd': np.random.uniform(1.0, 50.0),
                            'status': status,
                            'is_successful': is_successful,
                            'success_score': float(is_successful),
                            # Track authoritative funding presence for downstream filtering
                            'has_funding_total_usd': bool(has_funding_total),
                            'funding_total_usd_raw': raw_funding_str
                        }
                        # Compute valuation using funding and other scoring criteria (align with primary path)
                        stage = company_data['funding_round']
                        stage_factor = {
                            'Seed': 6.0, 'Series A': 10.0, 'Series B': 14.0, 'Series C': 18.0
                        }.get(stage, 8.0)
                        market_adj = min(4.0, company_data['market_size_billion_usd'] / 10.0)  # up to +4
                        team_adj = min(2.0, company_data['team_size'] / 100.0 * 2.0)  # up to +2
                        comp_adj = - min(2.0, company_data['competition_level'] / 10.0 * 2.0)  # up to -2
                        if company_data['funding_amount_usd'] > 0:
                            multiplier = max(3.0, stage_factor + market_adj + team_adj + comp_adj)
                            company_data['valuation_usd'] = float(company_data['funding_amount_usd'] * multiplier)
                        startup_data.append(company_data)
                    except Exception as e:
                        print(f"   Error processing row {idx}: {e}")
                        continue
                
                if startup_data:
                    result_df = pd.DataFrame(startup_data)
                    print(f"Success: Successfully loaded {len(result_df)} companies from investments_VC.csv")
                    return result_df, "local:investments_VC"
            
            return None
        except Exception as e:
            print(f"Error: Failed to load local investments_VC.csv: {e}")
            return None
    
    def load_with_timeout():
        """Load Kaggle data with timeout using threading"""
        result = [None]
        
        def target():
            try:
                # Try downloading from Kaggle using kagglehub
                try:
                    import kagglehub
                    print("   Using kagglehub to download dataset...")
                    
                    # Download latest version - this returns the path to downloaded files
                    path = kagglehub.dataset_download("arindam235/startup-investments-crunchbase")
                    print(f"   Downloaded to: {path}")
                    
                    # Check for CSV files in downloaded path
                    if os.path.exists(path):
                        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
                        print(f"   Found {len(csv_files)} CSV files in downloaded data")
                        
                        if csv_files:
                            # Copy files to our local kaggle_data directory for caching
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            local_data_dir = os.path.join(script_dir, 'kaggle_data')
                            os.makedirs(local_data_dir, exist_ok=True)
                            
                            import shutil
                            for csv_file in csv_files:
                                src = os.path.join(path, csv_file)
                                dst = os.path.join(local_data_dir, csv_file)
                                if not os.path.exists(dst):  # Only copy if not already cached
                                    shutil.copy2(src, dst)
                                    print(f"   Cached {csv_file} locally")
                            
                            # Now load from the downloaded path
                            data_dir = path
                        else:
                            print("   No CSV files found in downloaded data")
                            # Fall back to checking local cache
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            data_dir = os.path.join(script_dir, 'kaggle_data')
                    else:
                        print("   Download path doesn't exist")
                        # Fall back to local cache
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        data_dir = os.path.join(script_dir, 'kaggle_data')
                
                except Exception as kagglehub_error:
                    print(f"   kagglehub download failed: {kagglehub_error}")
                    # Fall back to checking local cache
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    data_dir = os.path.join(script_dir, 'kaggle_data')
                
                # Check if we have data (either downloaded or cached locally)
                if os.path.exists(data_dir):
                    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                    
                    if csv_files:
                        print(f"   Found existing downloaded data with {len(csv_files)} CSV files")
                        
                        # Check for investments_VC.csv (main dataset file)
                        investments_vc_path = os.path.join(data_dir, 'investments_VC.csv')
                        
                        # Get max rows from environment variable (default 400)
                        max_rows = int(os.environ.get('KAGGLE_MAX_ROWS', '400'))
                        
                        if os.path.exists(investments_vc_path):
                            try:
                                print(f"   Loading data from investments_VC.csv using kagglehub (max {max_rows} rows)...")
                                # Load the main dataset file directly
                                df = pd.read_csv(investments_vc_path, low_memory=False, nrows=max_rows)  # Limit for speed
                                
                                if len(df) > 100:
                                    # Process this data using our existing failsafe logic
                                    processed_data = process_investments_vc_data(df)
                                    if processed_data:
                                        result[0] = processed_data
                                        return
                                
                            except Exception as load_error:
                                print(f"   Failed to load investments_VC.csv: {load_error}")
                        
                        # Fallback: Look for other common dataset files
                        objects_path = os.path.join(data_dir, 'objects.csv')
                        investments_path = os.path.join(data_dir, 'investments.csv')
                        funding_rounds_path = os.path.join(data_dir, 'funding_rounds.csv')
                        
                        # Get max rows from environment variable (default 400)
                        max_rows = int(os.environ.get('KAGGLE_MAX_ROWS', '400'))
                        
                        if os.path.exists(objects_path) and os.path.exists(investments_path):
                            try:
                                # Load company information with real names
                                print(f"   Loading company data from objects.csv (max {max_rows} rows)...")
                                objects_df = pd.read_csv(objects_path, low_memory=False, nrows=max_rows)  # Limit rows for speed
                                companies_df = objects_df[objects_df['entity_type'] == 'Company'].copy()
                                
                                # Load investment data
                                print(f"   Loading investment data from investments.csv (max {max_rows} rows)...")
                                investments_df = pd.read_csv(investments_path, nrows=max_rows)  # Limit for speed
                                
                                # Load funding rounds data if available
                                funding_df = None
                                if os.path.exists(funding_rounds_path):
                                    print("   Loading funding rounds data...")
                                    funding_df = pd.read_csv(funding_rounds_path, low_memory=False, nrows=5000)
                                
                                # Merge datasets to create comprehensive startup data with real names
                                merged_df = merge_startup_datasets(companies_df, investments_df, funding_df)
                                
                                if merged_df is not None and len(merged_df) > 100:
                                    print(f"Success: Successfully created merged dataset with real company names")
                                    print(f"   Dataset shape: {merged_df.shape}")
                                    print(f"   Sample companies: {merged_df['company_name'].head(3).tolist()}")
                                    result[0] = (merged_df, "arindam235/startup-investments-crunchbase")
                                    return
                                else:
                                    print(f"   Merged dataset was too small or None")
                            
                            except Exception as merge_error:
                                print(f"   Failed to merge datasets: {merge_error}")
                
            except Exception as e:
                print(f"   Error in data loading thread: {e}")
        
        # Run the loading in a separate thread with timeout
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=90)  # 90 second timeout to allow kagglehub download
        
        if thread.is_alive():
            print("Warning: Kaggle data loading timed out after 90 seconds")
            return None
        
        return result[0]
    
    try:
        print("Loading: Attempting to download startup dataset using kagglehub...")
        
        # Try loading with timeout
        kaggle_result = load_with_timeout()
        if kaggle_result:
            return kaggle_result
        
        # If Kaggle loading failed or timed out, try failsafe
        print("Loading: Trying failsafe loading from investments_VC.csv...")
        failsafe_result = load_local_investments_vc()
        if failsafe_result:
            return failsafe_result
            
        return None
    
    except Exception as e:
        print(f"Error: Critical error in download_kaggle_startup_data: {e}")
        # Try failsafe as last resort
        try:
            print("Loading: Last resort: trying failsafe loading...")
            failsafe_result = load_local_investments_vc()
            if failsafe_result:
                return failsafe_result
        except Exception as failsafe_error:
            print(f"Error: Failsafe also failed: {failsafe_error}")
        
        return None


def preprocess_kaggle_data(df, dataset_name):
    """
    Preprocess Kaggle datasets to match our expected format.
    """
    try:
        # Create standardized column mapping
        processed_df = pd.DataFrame()
        
        # Detect and map common startup data columns (enhanced for Crunchbase data)
        column_mappings = {
            # Company info
            'company_name': ['name', 'company_name', 'startup_name', 'company', 'organization_name', 'entity_name'],
            'industry': ['industry', 'sector', 'category', 'vertical', 'category_code', 'market', 'primary_role'],
            'location': ['location', 'city', 'state', 'country', 'headquarters', 'country_code', 'region'],
            
            # Funding info
            'funding_round': ['funding_round', 'round', 'stage', 'series', 'funding_round_type', 'investment_type'],
            'funding_amount_usd': ['funding_amount', 'raised_amount_usd', 'funding', 'amount', 'raised_amount', 'money_raised_usd'],
            'valuation_usd': ['valuation', 'pre_money_valuation', 'post_money_valuation', 'company_valuation'],
            
            # Company metrics
            'team_size': ['team_size', 'employees', 'employee_count', 'headcount', 'employee_range'],
            'years_since_founding': ['age', 'founded_year', 'years_active', 'company_age', 'founded_at'],
            'revenue_usd': ['revenue', 'annual_revenue', 'revenue_usd', 'revenue_range'],
            
            # Market data
            'num_investors': ['investor_count', 'investors', 'num_investors', 'participant_count'],
            'market_size_billion_usd': ['market_size', 'tam', 'addressable_market'],
            
            # Success indicators
            'status': ['status', 'outcome', 'exit_status', 'current_status', 'state', 'operating_status'],
            'is_successful': ['success', 'successful', 'is_success', 'exit_success', 'ipo', 'acquired']
        }
        
        # Map columns
        for target_col, possible_cols in column_mappings.items():
            for col in possible_cols:
                if col in df.columns:
                    processed_df[target_col] = df[col]
                    break
        
        # Fill missing required columns with defaults or derived values
        if 'company_name' not in processed_df.columns:
            # Check if we have a 'name' column (common in Crunchbase data)
            if 'name' in df.columns:
                processed_df['company_name'] = df['name'].astype(str)
                print(f"   Using 'name' column for company names")
            else:
                processed_df['company_name'] = [f"Company_{i}" for i in range(len(df))]
                print(f"   Generated generic company names")
        else:
            print(f"   Using existing company_name column")
        
        if 'industry' not in processed_df.columns:
            processed_df['industry'] = np.random.choice(INDUSTRIES, len(df))
        
        if 'location' not in processed_df.columns:
            processed_df['location'] = np.random.choice(LOCATIONS, len(df))
        
        if 'funding_round' not in processed_df.columns:
            processed_df['funding_round'] = np.random.choice(FUNDING_ROUNDS, len(df))
        
        # Convert and clean numeric columns
        numeric_columns = ['funding_amount_usd', 'valuation_usd', 'team_size', 
                          'years_since_founding', 'revenue_usd', 'num_investors']
        
        for col in numeric_columns:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            else:
                # Generate reasonable defaults based on other columns
                if col == 'funding_amount_usd':
                    processed_df[col] = np.random.uniform(100000, 50000000, len(df))
                elif col == 'valuation_usd':
                    processed_df[col] = processed_df.get('funding_amount_usd', 5000000) * np.random.uniform(5, 20, len(df))
                elif col == 'team_size':
                    processed_df[col] = np.random.randint(5, 200, len(df))
                elif col == 'years_since_founding':
                    processed_df[col] = np.random.uniform(0.5, 10, len(df))
                elif col == 'revenue_usd':
                    processed_df[col] = np.random.uniform(0, 10000000, len(df))
                elif col == 'num_investors':
                    processed_df[col] = np.random.randint(1, 10, len(df))
        
        # Handle founded_year to years_since_founding conversion
        if 'years_since_founding' not in processed_df.columns:
            founded_cols = ['founded_year', 'founded_at', 'founded_on']
            for founded_col in founded_cols:
                if founded_col in df.columns:
                    try:
                        # Convert founded year/date to years since founding
                        founded_data = pd.to_datetime(df[founded_col], errors='coerce')
                        current_year = pd.Timestamp.now().year
                        processed_df['years_since_founding'] = current_year - founded_data.dt.year
                        # Cap at reasonable values
                        processed_df['years_since_founding'] = processed_df['years_since_founding'].clip(0, 50)
                        break
                    except:
                        continue
            
            # If still no years_since_founding, generate random values
            if 'years_since_founding' not in processed_df.columns:
                processed_df['years_since_founding'] = np.random.uniform(0.5, 10, len(df))
        
        # Add missing columns with defaults
        if 'competition_level' not in processed_df.columns:
            processed_df['competition_level'] = np.random.randint(1, 11, len(df))
        
        if 'market_size_billion_usd' not in processed_df.columns:
            processed_df['market_size_billion_usd'] = np.random.uniform(1, 100, len(df))
        
        # Handle success indicators
        if 'is_successful' not in processed_df.columns:
            if 'status' in processed_df.columns:
                # Infer success from status
                success_statuses = ['acquired', 'ipo', 'successful', 'exit']
                processed_df['is_successful'] = processed_df['status'].str.lower().isin(success_statuses).astype(int)
            else:
                # Random success based on realistic probability
                processed_df['is_successful'] = np.random.choice([0, 1], len(df), p=[0.6, 0.4])
        
        if 'status' not in processed_df.columns:
            # Generate status based on success
            statuses = []
            for success in processed_df['is_successful']:
                if success:
                    statuses.append(np.random.choice(['Acquired', 'IPO', 'Operating'], p=[0.4, 0.1, 0.5]))
                else:
                    statuses.append(np.random.choice(['Operating', 'Closed'], p=[0.3, 0.7]))
            processed_df['status'] = statuses
        
        # Add company IDs
        processed_df['company_id'] = [f"kaggle_{i:04d}" for i in range(len(processed_df))]
        
        # Calculate success score
        processed_df['success_score'] = processed_df['is_successful'].astype(float)
        
        # Clean data
        processed_df = processed_df.dropna(subset=['funding_amount_usd', 'valuation_usd'])
        processed_df = processed_df[processed_df['funding_amount_usd'] > 0]
        processed_df = processed_df[processed_df['valuation_usd'] > 0]
        
        # Sample data for performance if dataset is too large
        if len(processed_df) > 20000:
            print(f"Risk: Dataset is large ({len(processed_df)} records), sampling 20,000 for performance...")
            processed_df = processed_df.sample(n=20000, random_state=42)
        
        print(f"Success: Preprocessed Kaggle data: {len(processed_df)} records")
        print(f"   Success rate: {processed_df['is_successful'].mean():.1%}")
        
        return processed_df
        
    except Exception as e:
        print(f"Error: Error preprocessing Kaggle data: {e}")
        return None

def load_data():
    """
    Load startup data from Kaggle if available, otherwise generate synthetic data.
    """
    global data_source
    
    # Check environment variable to determine if we should skip Kaggle
    SKIP_KAGGLE = os.environ.get('SKIP_KAGGLE', 'False').lower() in ['true', '1', 'yes']
    
    # Get max rows to load from Kaggle data (default 400 for faster loading)
    KAGGLE_MAX_ROWS = int(os.environ.get('KAGGLE_MAX_ROWS', '400'))
    
    if not SKIP_KAGGLE:
        # Try to load Kaggle data first
        print("Attempting to load real data from Kaggle...")
        try:
            kaggle_result = download_kaggle_startup_data()
            
            if kaggle_result:
                kaggle_df, dataset_name = kaggle_result
                
                # If data comes from our local investments_VC.csv, skip preprocessing 
                # as it's already formatted correctly with real company names
                if "investments_VC" in dataset_name:
                    data_source = f"kaggle:{dataset_name}"
                    print(f"Success: Using real Kaggle data from {dataset_name}")
                    return kaggle_df
                else:
                    # For other Kaggle datasets, apply preprocessing
                    processed_df = preprocess_kaggle_data(kaggle_df, dataset_name)
                    
                    if processed_df is not None and len(processed_df) > 100:  # Need sufficient data
                        data_source = f"kaggle:{dataset_name}"
                        print(f"Success: Using real Kaggle data from {dataset_name}")
                        return processed_df
        
        except Exception as e:
            print(f"Warning: Error during Kaggle data loading: {e}")
    else:
        print("Loading: Skipping Kaggle data loading for faster startup...")
    
    # Fallback to synthetic data
    print("Loading: Generating synthetic startup data...")
    data_source = "synthetic"
    return generate_startup_data()

def generate_startup_data(n_samples=1000):
    """
    Generate realistic synthetic startup data for ML training.
    """
    np.random.seed(42)
    
    statuses = ['Operating', 'Acquired', 'IPO', 'Closed']
    
    data = []
    for i in range(n_samples):
        # Company basics
        company_id = f"startup_{i+1:04d}"
        company_name = f"Company_{i+1}"
        industry = np.random.choice(INDUSTRIES)
        location = np.random.choice(LOCATIONS)
        
        # Funding details
        funding_round = np.random.choice(FUNDING_ROUNDS)
        
        # Funding amounts based on round (realistic ranges)
        funding_multipliers = {'Seed': (0.1, 2), 'Series A': (2, 15), 'Series B': (10, 50), 
                              'Series C': (25, 100), 'Series D+': (50, 500)}
        min_funding, max_funding = funding_multipliers[funding_round]
        funding_amount = np.random.uniform(min_funding, max_funding) * 1_000_000
        
        # Valuation (typically 10-20x funding amount)
        valuation_multiplier = np.random.uniform(8, 25)
        valuation = funding_amount * valuation_multiplier
        
        # Team size (correlated with funding round)
        round_team_sizes = {'Seed': (2, 15), 'Series A': (10, 50), 'Series B': (25, 100), 
                           'Series C': (50, 200), 'Series D+': (100, 500)}
        min_team, max_team = round_team_sizes[funding_round]
        team_size = np.random.randint(min_team, max_team)
        
        # Years since founding
        years_since_founding = np.random.uniform(0.5, 10)
        
        # Revenue (some companies have revenue, others don't)
        has_revenue = np.random.choice([True, False], p=[0.7, 0.3])
        revenue = np.random.uniform(0.1, funding_amount/500_000) * 1_000_000 if has_revenue else 0
        
        # Number of investors
        num_investors = np.random.randint(1, 15)
        
        # Competition level (1-10 scale)
        competition_level = np.random.randint(1, 11)
        
        # Market size (billion USD)
        market_size = np.random.uniform(0.5, 100)
        
        # Determine success based on realistic factors
        success_probability = 0.5  # Base probability
        
        # Adjust based on factors
        if industry in ['Fintech', 'Healthcare', 'AI/ML', 'SaaS']:
            success_probability += 0.1
        if location in ['San Francisco', 'New York', 'Boston', 'Seattle']:
            success_probability += 0.1
        if team_size >= 20:
            success_probability += 0.1
        if revenue > 1_000_000:
            success_probability += 0.2
        if funding_round in ['Series B', 'Series C', 'Series D+']:
            success_probability += 0.1
        if competition_level <= 5:
            success_probability += 0.05
        
        # Ensure probability is between 0 and 1
        success_probability = np.clip(success_probability, 0.1, 0.9)
        
        # Determine status based on success probability
        is_successful = np.random.choice([True, False], p=[success_probability, 1-success_probability])
        if is_successful:
            status = np.random.choice(['Operating', 'Acquired', 'IPO'], p=[0.6, 0.3, 0.1])
        else:
            status = np.random.choice(['Operating', 'Closed'], p=[0.3, 0.7])
        
        # Binary success indicator
        success_score = 1 if status in ['Acquired', 'IPO'] else (0.5 if status == 'Operating' else 0)
        
        data.append({
            'company_id': company_id,
            'company_name': company_name,
            'industry': industry,
            'location': location,
            'funding_round': funding_round,
            'funding_amount_usd': funding_amount,
            'valuation_usd': valuation,
            'team_size': team_size,
            'years_since_founding': years_since_founding,
            'revenue_usd': revenue,
            'num_investors': num_investors,
            'competition_level': competition_level,
            'market_size_billion_usd': market_size,
            'status': status,
            'success_score': success_score,
            'is_successful': 1 if status in ['Acquired', 'IPO'] else 0
        })
    
    return pd.DataFrame(data)

def engineer_features(df):
    """
    Create features for machine learning.
    """
    df_features = df.copy()
    
    # Create derived features
    df_features['funding_efficiency'] = df_features['valuation_usd'] / (df_features['funding_amount_usd'] + 1)
    df_features['funding_per_employee'] = df_features['funding_amount_usd'] / (df_features['team_size'] + 1)
    
    # Age categories
    df_features['age_category'] = pd.cut(df_features['years_since_founding'], 
                                       bins=[0, 1, 3, 5, 10, 100], 
                                       labels=['Startup', 'Early', 'Growth', 'Mature', 'Established']).astype(str)
    
    # Team size categories
    df_features['team_size_category'] = pd.cut(df_features['team_size'], 
                                             bins=[0, 10, 50, 100, 500, 10000], 
                                             labels=['Small', 'Medium', 'Large', 'Very Large', 'Enterprise']).astype(str)
    
    # Log transforms
    df_features['funding_amount_log'] = np.log1p(df_features['funding_amount_usd'])
    df_features['valuation_log'] = np.log1p(df_features['valuation_usd'])
    
    # Competition categories
    df_features['competition_category'] = pd.cut(df_features['competition_level'], 
                                               bins=[0, 3, 6, 8, 10], 
                                               labels=['Low', 'Medium', 'High', 'Very High']).astype(str)
    
    # Ensure consolidated grouping columns exist (used as categorical features)
    if 'industry_group' not in df_features.columns:
        try:
            df_features['industry_group'] = df_features['industry'].apply(consolidate_industry)
        except Exception:
            df_features['industry_group'] = 'Other'
    if 'region' not in df_features.columns:
        try:
            df_features['region'] = df_features['location'].apply(map_location_to_region)
        except Exception:
            df_features['region'] = 'Other'
    
    # Encode categorical variables (include consolidated groupings)
    categorical_columns = ['industry', 'industry_group', 'location', 'region', 'funding_round', 'status', 
                          'age_category', 'team_size_category', 'competition_category']
    
    encoded_features = pd.get_dummies(df_features[categorical_columns], 
                                     prefix=categorical_columns, drop_first=True)
    
    # Numerical features
    numerical_columns = ['funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding', 
                        'num_investors', 'competition_level', 'market_size_billion_usd',
                        'funding_efficiency', 'funding_per_employee',
                        'funding_amount_log', 'valuation_log']
    
    # Combine features
    X_features = pd.concat([df_features[numerical_columns], encoded_features], axis=1)
    
    # Scale numerical features
    scaler = StandardScaler()
    X_scaled = X_features.copy()
    X_scaled[numerical_columns] = scaler.fit_transform(X_features[numerical_columns])
    
    # Target variables
    y_classification = df_features['is_successful']
    y_regression = df_features['funding_amount_usd']
    y_valuation = df_features['valuation_usd']
    
    return {
        'feature_matrix': X_scaled,
        'scaler': scaler,
        'numerical_columns': numerical_columns,
        'y_classification': y_classification,
        'y_regression': y_regression,
        'y_valuation': y_valuation,
        'feature_names': list(X_scaled.columns)
    }

def train_models():
    """
    Train ML models and store globally.
    """
    global startup_classifier, startup_regressor, startup_valuation_regressor, feature_scaler, feature_columns, sample_data, training_numerical_columns
    
    # Load data (try Kaggle first, fallback to synthetic)
    df = load_data()
    # Add consolidated columns for filters
    try:
        df = df.copy()
        df['industry_group'] = df['industry'].apply(consolidate_industry)
        # Use new 'region' terminology (formerly 'continent')
        df['region'] = df['location'].apply(map_location_to_region)
    except Exception as _e:
        print(f"Warning: Failed to add consolidated columns: {_e}")
    sample_data = df.copy()
    
    # Prepare grouped filter lists
    global grouped_industries, regions, continents
    try:
        grouped_industries = sorted([str(x) for x in sample_data['industry_group'].dropna().unique()])
        regions = sorted([str(x) for x in sample_data['region'].dropna().unique()])
        # Deprecated alias synchronized for back-compat
        continents = list(regions)
    except Exception as _e:
        print(f"Warning: Failed to compute grouped filter lists: {_e}")
        grouped_industries = ['Fintech','Healthcare','E-commerce','SaaS','AI/ML','Biotech','EdTech','Gaming','Cybersecurity','IoT','Blockchain','Marketing','Other']
        regions = ['North America','Europe','Asia','South America','Africa','Oceania','Middle East','Other']
        continents = list(regions)

    print(f"Analysis: Training models on {len(df)} companies from {data_source} data source")
    
    # Engineer features
    feature_data = engineer_features(df)
    
    X = feature_data['feature_matrix']
    y_class = feature_data['y_classification']
    y_reg = feature_data['y_regression']
    y_val = feature_data['y_valuation']
    
    # Store for later use
    feature_scaler = feature_data['scaler']
    feature_columns = feature_data['feature_names']
    training_numerical_columns = feature_data.get('numerical_columns', [
        'funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding',
        'num_investors', 'competition_level', 'market_size_billion_usd',
        'funding_efficiency', 'funding_per_employee',
        'funding_amount_log', 'valuation_log'
    ])

    # Try cache (skip training when valid)
    try:
        use_cache = os.environ.get('CACHE_MODELS', 'true').strip().lower() in {'1','true','yes','y'}
        force_retrain = os.environ.get('FORCE_RETRAIN', 'false').strip().lower() in {'1','true','yes','y'}
    except Exception:
        use_cache, force_retrain = True, False

    data_sig = _compute_data_signature(df)
    if use_cache and not force_retrain:
        cached = _load_models_from_cache(data_sig)
        if cached is not None:
            globals()['startup_classifier'] = cached['startup_classifier']
            globals()['startup_regressor'] = cached['startup_regressor']
            globals()['startup_valuation_regressor'] = cached['startup_valuation_regressor']
            globals()['feature_scaler'] = cached['feature_scaler']
            globals()['feature_columns'] = cached['feature_columns']
            globals()['training_numerical_columns'] = cached['training_numerical_columns']
            # Bind bundle to classifier to ensure consistent inference alignment
            try:
                _bind_feature_bundle_to_classifier(
                    globals()['startup_classifier'],
                    globals()['feature_columns'],
                    globals()['training_numerical_columns'],
                    globals()['feature_scaler']
                )
            except Exception:
                pass
            # Light evaluation for log
            try:
                X_tr, X_te, y_tr, y_te = train_test_split(X, y_class, test_size=0.2, random_state=42, stratify=y_class)
                acc = accuracy_score(y_te, cached['startup_classifier'].predict(X_te))
                print(f"AI: Loaded cached ML models. Test accuracy: {acc:.1%}")
            except Exception:
                print("AI: Loaded cached ML models.")
            # Precompute tiers as usual
            try:
                _disable = os.environ.get('PRECOMPUTE_DISABLE', 'false').lower() in {'1', 'true', 'yes', 'y'}
                if _disable:
                    print("Info: Skipping precompute_investment_tiers due to PRECOMPUTE_DISABLE")
                else:
                    _max_rows_env = os.environ.get('PRECOMPUTE_MAX_ROWS', '').strip()
                    _max_rows = int(_max_rows_env) if _max_rows_env else None
                    precompute_investment_tiers(max_rows=_max_rows)
            except Exception as _pc_err:
                print(f"Warning: Failed to precompute investment tiers: {_pc_err}")
            return
    
    # Split data
    X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(
        X, y_class, test_size=0.2, random_state=42, stratify=y_class)
    
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X, y_reg, test_size=0.2, random_state=42)
    
    # Train classification models and pick the best by validation accuracy
    from sklearn.model_selection import GridSearchCV

    # 1) RandomForest with modest grid
    rf_base = RandomForestClassifier(random_state=42, n_jobs=-1, class_weight='balanced_subsample')
    rf_param_grid = {
        'n_estimators': [200, 400],
        'max_depth': [None, 12, 20],
        'min_samples_leaf': [1, 2],
        'max_features': ['sqrt', 0.5]
    }
    rf_grid = GridSearchCV(rf_base, rf_param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=0)
    rf_grid.fit(X_train_class, y_train_class)
    rf_best = rf_grid.best_estimator_

    # 2) Histogram Gradient Boosting (often stronger on tabular)
    # Use a compact grid to keep training time reasonable
    hgb_best = None
    try:
        hgb_base = HistGradientBoostingClassifier(
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            class_weight='balanced'
        )
        hgb_param_grid = {
            'learning_rate': [0.05, 0.1],
            'max_leaf_nodes': [31, 63],
            'min_samples_leaf': [10, 20],
            'max_depth': [None, 12]
        }
        hgb_grid = GridSearchCV(hgb_base, hgb_param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=0)
        hgb_grid.fit(X_train_class, y_train_class)
        hgb_best = hgb_grid.best_estimator_
    except Exception as _hgb_err:
        print(f"Warning: HGBClassifier training failed or unavailable: {_hgb_err}")

    # 3) ExtraTrees (Extremely Randomized Trees) can outperform RF on some tabular problems
    etc_best = None
    try:
        etc_base = ExtraTreesClassifier(random_state=42, n_jobs=-1, class_weight='balanced')
        etc_param_grid = {
            'n_estimators': [300, 600],
            'max_depth': [None, 12, 20],
            'min_samples_leaf': [1, 2],
            'max_features': ['sqrt', 0.5]
        }
        etc_grid = GridSearchCV(etc_base, etc_param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=0)
        etc_grid.fit(X_train_class, y_train_class)
        etc_best = etc_grid.best_estimator_
    except Exception as _etc_err:
        print(f"Warning: ExtraTreesClassifier training failed or unavailable: {_etc_err}")

    # 4) Logistic Regression (strong linear baseline with balanced classes)
    lr_best = None
    try:
        lr_base = LogisticRegression(
            solver='lbfgs',
            max_iter=200,
            class_weight='balanced',
            n_jobs=None,
            random_state=42
        )
        # Compact grid over C only
        from sklearn.model_selection import GridSearchCV as _Grid
        lr_param_grid = {
            'C': [0.1, 1.0, 10.0]
        }
        lr_grid = _Grid(lr_base, lr_param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=0)
        lr_grid.fit(X_train_class, y_train_class)
        lr_best = lr_grid.best_estimator_
    except Exception as _lr_err:
        print(f"Warning: LogisticRegression training failed or unavailable: {_lr_err}")

    # 5) Soft Voting Ensemble using available probabilistic base models
    voting_best = None
    try:
        estimators = []
        if rf_best is not None:
            estimators.append(('rf', rf_best))
        if hgb_best is not None:
            estimators.append(('hgb', hgb_best))
        if etc_best is not None:
            estimators.append(('etc', etc_best))
        if lr_best is not None:
            estimators.append(('lr', lr_best))
        if len(estimators) >= 2:
            voting = VotingClassifier(estimators=estimators, voting='soft', n_jobs=-1, weights=None)
            voting.fit(X_train_class, y_train_class)
            voting_best = voting
    except Exception as _vote_err:
        print(f"Warning: VotingClassifier training failed or unavailable: {_vote_err}")

    # Evaluate on held-out test set and select the best classifier
    rf_acc = accuracy_score(y_test_class, rf_best.predict(X_test_class)) if rf_best is not None else 0.0
    hgb_acc = accuracy_score(y_test_class, hgb_best.predict(X_test_class)) if hgb_best is not None else -1.0
    etc_acc = accuracy_score(y_test_class, etc_best.predict(X_test_class)) if etc_best is not None else -1.0
    lr_acc = accuracy_score(y_test_class, lr_best.predict(X_test_class)) if lr_best is not None else -1.0
    vote_acc = accuracy_score(y_test_class, voting_best.predict(X_test_class)) if voting_best is not None else -1.0

    # Select the top performer by held-out accuracy
    candidate_accs = [
        ('RandomForestClassifier', rf_best, rf_acc),
        ('HistGradientBoostingClassifier', hgb_best, hgb_acc),
        ('ExtraTreesClassifier', etc_best, etc_acc),
        ('LogisticRegression', lr_best, lr_acc),
        ('VotingSoftEnsemble', voting_best, vote_acc),
    ]
    # Filter out None models
    candidate_accs = [(n, m, a) for (n, m, a) in candidate_accs if m is not None and a >= 0]
    if not candidate_accs:
        # Fallback to RF if everything failed
        startup_classifier = rf_best
        selected_name, selected_acc = 'RandomForestClassifier', rf_acc
        alt_name, alt_acc = 'HistGradientBoostingClassifier', hgb_acc
    else:
        candidate_accs.sort(key=lambda t: t[2], reverse=True)
        selected_name, selected_model, selected_acc = candidate_accs[0]
        # Keep the best alternative for reporting
        if len(candidate_accs) > 1:
            alt_name, alt_model, alt_acc = candidate_accs[1]
        else:
            alt_name, alt_acc = '(none)', -1.0
        startup_classifier = selected_model
    
    # Train regression models (funding and valuation)
    startup_regressor = RandomForestRegressor(
        n_estimators=300, max_depth=None, min_samples_split=4,
        min_samples_leaf=2, max_features='sqrt', random_state=42, n_jobs=-1)
    startup_regressor.fit(X_train_reg, y_train_reg)

    startup_valuation_regressor = RandomForestRegressor(
        n_estimators=300, max_depth=None, min_samples_split=4,
        min_samples_leaf=2, max_features='sqrt', random_state=42, n_jobs=-1)
    # Train valuation regressor on valuation target
    X_train_val, X_test_val, y_train_val, y_test_val = train_test_split(X, y_val, test_size=0.2, random_state=42)
    startup_valuation_regressor.fit(X_train_val, y_train_val)
    
    # Optional: tune decision threshold on held-out validation to maximize accuracy
    tuned_threshold = 0.5
    try:
        if hasattr(startup_classifier, 'predict_proba'):
            proba = startup_classifier.predict_proba(X_test_class)[:, 1]
            thresholds = np.linspace(0.25, 0.75, 101)
            accs = []
            for t in thresholds:
                preds = (proba >= t).astype(int)
                accs.append(accuracy_score(y_test_class, preds))
            best_idx = int(np.argmax(accs))
            tuned_threshold = float(thresholds[best_idx])
            tuned_acc = float(accs[best_idx])
            # Wrap the classifier with tuned threshold for downstream use
            startup_classifier = ThresholdedClassifier(startup_classifier, threshold=tuned_threshold)
        else:
            tuned_acc = selected_acc
    except Exception as _thr_err:
        print(f"Warning: Threshold tuning failed: {_thr_err}")
        tuned_acc = selected_acc

    # Bind feature bundle to the final classifier to prevent feature-mismatch at inference
    try:
        _bind_feature_bundle_to_classifier(
            startup_classifier,
            feature_columns,
            training_numerical_columns,
            feature_scaler
        )
    except Exception:
        pass

    # Print performance (report both untuned and tuned if applicable)
    class_accuracy = accuracy_score(y_test_class, startup_classifier.predict(X_test_class))
    reg_r2 = r2_score(y_test_reg, startup_regressor.predict(X_test_reg))
    val_r2 = r2_score(y_test_val, startup_valuation_regressor.predict(X_test_val))
    
    print(f"AI: ML Models trained successfully!")
    if 'tuned_acc' in locals() and abs(tuned_acc - selected_acc) > 1e-9:
        print(f"   Classification accuracy: {class_accuracy:.1%} with tuned threshold={tuned_threshold:.2f} ({selected_name}; untuned {selected_acc:.1%}, alt {alt_name}: {alt_acc:.1%})")
    else:
        print(f"   Classification accuracy: {class_accuracy:.1%} ({selected_name}; alt {alt_name}: {alt_acc:.1%})")
    print(f"   Regression R² (funding): {reg_r2:.1%}")
    print(f"   Regression R² (valuation): {val_r2:.1%}")

    # Save models to cache for faster subsequent startups
    try:
        if os.environ.get('CACHE_MODELS', 'true').strip().lower() in {'1','true','yes','y'}:
            _save_models_to_cache(data_sig, startup_classifier, startup_regressor, startup_valuation_regressor,
                                  feature_scaler, feature_columns, training_numerical_columns)
    except Exception:
        pass

    # Auto-precompute investment tiers for instant UI responsiveness
    # Precomputation runs automatically after training completes
    try:
        # Attempt to load precomputed tiers from cache first
        loaded = _load_precompute_from_cache(data_sig)
        if not loaded:
            # Respect optional limit via PRECOMPUTE_MAX_ROWS; empty/missing means no limit
            _max_rows_env = os.environ.get('PRECOMPUTE_MAX_ROWS', '').strip()
            _max_rows = None
            if _max_rows_env:
                try:
                    _max_rows = int(_max_rows_env)
                except ValueError:
                    print(f"Info: Ignoring non-integer PRECOMPUTE_MAX_ROWS='{_max_rows_env}', proceeding without limit")
                    _max_rows = None
            print(f"Info: Auto-precomputing investment tiers (max_rows={_max_rows or 'all'})...")
            precompute_investment_tiers(max_rows=_max_rows)
            # Save results for next startup
            _save_precompute_to_cache(data_sig)
            print("Success: Auto-precompute completed and cached")
    except Exception as _pc_err:
        print(f"Warning: Failed to precompute investment tiers: {_pc_err}")

    # Final step: publish the freshly trained suite atomically to globals to avoid race conditions
    try:
        globals()['startup_classifier'] = startup_classifier
        globals()['startup_regressor'] = startup_regressor
        globals()['startup_valuation_regressor'] = startup_valuation_regressor
        globals()['feature_scaler'] = feature_scaler
        globals()['feature_columns'] = feature_columns
        globals()['training_numerical_columns'] = training_numerical_columns
    except Exception:
        pass

def prepare_features_for_prediction(data, active_classifier=None):
    """
    Prepare input data for ML prediction.

    Uses the feature/scale bundle attached to the provided classifier (or the
    current global classifier) to guarantee column alignment and avoid
    feature-name mismatches when background training updates globals.
    """
    # Create DataFrame with single row
    df = pd.DataFrame([data])
    
    # Add derived features
    df['funding_efficiency'] = df['valuation_usd'] / (df['funding_amount_usd'] + 1)
    df['funding_per_employee'] = df['funding_amount_usd'] / (df['team_size'] + 1)
    
    # Age categories - handle edge case for single-row DataFrames
    try:
        df['age_category'] = pd.cut(df['years_since_founding'], 
                                   bins=[0, 1, 3, 5, 10, 100], 
                                   labels=['Startup', 'Early', 'Growth', 'Mature', 'Established']).astype(str)
    except (ValueError, IndexError):
        # Fallback for single-row edge case
        age = df['years_since_founding'].iloc[0]
        if age <= 1:
            df['age_category'] = 'Startup'
        elif age <= 3:
            df['age_category'] = 'Early'
        elif age <= 5:
            df['age_category'] = 'Growth'
        elif age <= 10:
            df['age_category'] = 'Mature'
        else:
            df['age_category'] = 'Established'
    
    # Team size categories - handle edge case for single-row DataFrames
    try:
        df['team_size_category'] = pd.cut(df['team_size'], 
                                         bins=[0, 10, 50, 100, 500, 10000], 
                                         labels=['Small', 'Medium', 'Large', 'Very Large', 'Enterprise']).astype(str)
    except (ValueError, IndexError):
        # Fallback for single-row edge case
        size = df['team_size'].iloc[0]
        if size <= 10:
            df['team_size_category'] = 'Small'
        elif size <= 50:
            df['team_size_category'] = 'Medium'
        elif size <= 100:
            df['team_size_category'] = 'Large'
        elif size <= 500:
            df['team_size_category'] = 'Very Large'
        else:
            df['team_size_category'] = 'Enterprise'
    
    # Log transforms
    df['funding_amount_log'] = np.log1p(df['funding_amount_usd'])
    df['valuation_log'] = np.log1p(df['valuation_usd'])
    
    # Competition categories - handle edge case for single-row DataFrames
    try:
        df['competition_category'] = pd.cut(df['competition_level'], 
                                           bins=[0, 3, 6, 8, 10], 
                                           labels=['Low', 'Medium', 'High', 'Very High']).astype(str)
    except (ValueError, IndexError):
        # Fallback for single-row edge case
        comp = df['competition_level'].iloc[0]
        if comp <= 3:
            df['competition_category'] = 'Low'
        elif comp <= 6:
            df['competition_category'] = 'Medium'
        elif comp <= 8:
            df['competition_category'] = 'High'
        else:
            df['competition_category'] = 'Very High'
    
    # Add status for encoding (dummy value)
    df['status'] = 'Operating'
    
    # Ensure consolidated grouping columns exist for inference
    try:
        if 'industry_group' not in df.columns or pd.isna(df.get('industry_group', [None])[0]):
            df['industry_group'] = df['industry'].apply(consolidate_industry)
    except Exception:
        df['industry_group'] = 'Other'
    try:
        if 'region' not in df.columns or pd.isna(df.get('region', [None])[0]):
            df['region'] = df['location'].apply(map_location_to_region)
    except Exception:
        df['region'] = 'Other'
    
    # Encode categorical variables (match training including consolidated groupings)
    categorical_columns = ['industry', 'industry_group', 'location', 'region', 'funding_round', 'status', 
                          'age_category', 'team_size_category', 'competition_category']
    
    encoded_features = pd.get_dummies(df[categorical_columns], 
                                     prefix=categorical_columns, drop_first=True)
    
    # Determine the active bundle (prefer attributes bound to the classifier)
    clf = active_classifier if active_classifier is not None else startup_classifier
    base = getattr(clf, 'base_estimator', clf)
    # Columns expected by this classifier
    expected_candidates = [
        getattr(clf, '_ds_feature_columns', None),
        getattr(base, '_ds_feature_columns', None),
        getattr(base, 'feature_names_in_', None),
        feature_columns
    ]
    expected_cols = None
    for candidate in expected_candidates:
        if candidate is None:
            continue
        if isinstance(candidate, (np.ndarray, pd.Index)):
            values = candidate.tolist()
        elif isinstance(candidate, (list, tuple)):
            values = list(candidate)
        else:
            # Skip falsy strings/iterables; otherwise cast appropriately
            if isinstance(candidate, str):
                if not candidate.strip():
                    continue
                values = [candidate]
            else:
                try:
                    if not candidate:
                        continue
                except Exception:
                    pass
                values = list(candidate)
        if values:
            expected_cols = [str(col) for col in values]
            break
    if expected_cols is None:
        # Last-resort defensive default (should not happen)
        expected_cols = []

    # Numerical features (prefer the exact set used during training of this classifier)
    default_numerical_columns = ['funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding',
                                 'num_investors', 'competition_level', 'market_size_billion_usd',
                                 'funding_efficiency', 'funding_per_employee',
                                 'funding_amount_log', 'valuation_log']
    raw_numerical_columns = (
        getattr(clf, '_ds_numerical_columns', None)
        or getattr(base, '_ds_numerical_columns', None)
        or training_numerical_columns
        or default_numerical_columns
    )
    if isinstance(raw_numerical_columns, (pd.Index, np.ndarray)):
        numerical_columns = [str(col) for col in raw_numerical_columns.tolist()]
    elif raw_numerical_columns is None:
        numerical_columns = list(default_numerical_columns)
    else:
        numerical_columns = [str(col) for col in list(raw_numerical_columns)]
    if not numerical_columns:
        numerical_columns = list(default_numerical_columns)
    else:
        # Preserve order while enforcing uniqueness to avoid duplicate scaling requests
        seen = set()
        ordered = []
        for col in numerical_columns:
            if col not in seen:
                ordered.append(col)
                seen.add(col)
        numerical_columns = ordered

    # Drop any dummy columns not seen during this classifier's training
    encoded_features = encoded_features[[c for c in encoded_features.columns if c in expected_cols]]

    # Combine features, then align strictly to expected columns
    numeric_frame = df.reindex(columns=numerical_columns, fill_value=0).copy()
    X_features = pd.concat([numeric_frame, encoded_features], axis=1)
    X_features = X_features.reindex(columns=list(expected_cols), fill_value=0)

    # Scale numerical features using the scaler bound to the classifier if available
    scaler = (
        getattr(clf, '_ds_scaler', None)
        or getattr(base, '_ds_scaler', None)
        or feature_scaler
    )
    X_scaled = X_features.copy()
    try:
        if scaler is not None and len(numerical_columns) > 0:
            X_scaled.loc[:, numerical_columns] = scaler.transform(numeric_frame[numerical_columns])
    except KeyError as ke:
        # If a KeyError occurs (e.g., unknown or missing columns), align strictly and retry
        missing = [c for c in numerical_columns if c not in X_features.columns]
        extra = [c for c in X_features.columns if c not in (expected_cols or [])]
        print(f"Warning: Feature alignment issue during scaling: {ke}. Missing numericals: {missing}. Extra cols dropped: {extra}.")
        aligned = X_features.reindex(columns=list(expected_cols), fill_value=0)
        X_scaled = aligned.copy()
        if scaler is not None and len(numerical_columns) > 0:
            fallback_numeric = aligned.reindex(columns=numerical_columns, fill_value=0)
            X_scaled.loc[:, numerical_columns] = scaler.transform(fallback_numeric[numerical_columns])
    except Exception as e:
        # Absolute fallback: return zeros except leave numericals unscaled (best-effort)
        print(f"Warning: Unexpected scaling error: {e}. Falling back to unscaled numericals.")
        X_scaled = X_features.copy()

    # Convert to numpy array to avoid pandas sparse accessor issues with sklearn
    return X_scaled.values

def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + np.exp(-x))
    except Exception:
        return 0.5


def _log_norm(x: float, ref_max: float) -> float:
    """Log-based normalization to [0,1] that resists saturation.
    ref_max represents an upper reference value where the score approaches 1.
    """
    try:
        x = max(0.0, float(x or 0.0))
        ref_max = max(1.0, float(ref_max))
        return float(min(1.0, np.log1p(x) / np.log1p(ref_max)))
    except Exception:
        return 0.0


def _normalize_market(market_size: float, competition_level: float) -> float:
    """Normalize market opportunity using a logistic transform of (market - 2*competition).
    Keeps results in (0,1) without saturating too early.
    """
    try:
        market_size = float(market_size or 0.0)
        competition_level = float(competition_level or 0.0)
        # Scale: subtract 2x competition; divide by 5 to get a reasonable spread
        x = (market_size - 2.0 * competition_level) / 5.0
        return float(_sigmoid(x))  # 0..1
    except Exception:
        return 0.5


def calculate_attractiveness_score(success_probability, market_size, competition_level, team_size, num_investors):
    """
    Calculate deal attractiveness score (0-100) with stricter, properly bounded normalization.

    Changes vs previous version:
      - Success probability dominates (70%) and is mapped more strictly: 0.25 -> 0, 0.85 -> 1
      - Market opportunity uses a logistic transform on (market - 2*competition)
      - Team and investors use log-normalization to prevent early saturation
      - Stricter gating to push more companies into Avoid tier

    Weights (sum to 100):
      - Success probability: 70%
      - Market opportunity: 15%
      - Team size: 8%
      - Investor count: 7%
    """
    # Much stricter linear mapping for success probability: below 25% -> 0, above 85% -> 1
    try:
        sp = float(success_probability)
    except Exception:
        sp = 0.0
    sp_norm = max(0.0, min(1.0, (sp - 0.25) / 0.60))

    market_norm = _normalize_market(market_size, competition_level)
    team_norm = _log_norm(team_size, 200.0)           # approaches 1 near ~200 people (harder)
    investors_norm = _log_norm(num_investors, 15.0)   # approaches 1 near ~15 investors (harder)

    score = (
        sp_norm * 70.0 +
        market_norm * 15.0 +
        team_norm * 8.0 +
        investors_norm * 7.0
    )
    # Stricter gating caps by success probability to avoid overly lenient scores
    if sp < 0.40:
        score = min(score, 49.0)  # hard Avoid if sp < 40%
    elif sp < 0.50:
        score = min(score, 64.0)  # at most Monitor if sp < 50%
    return float(score)

def get_recommendation(score):
    """
    Get investment recommendation based on normalized score using a 3-tier system:
      - Invest (green): Score >= 65
      - Monitor (yellow): Score >= 50
      - Avoid (red): Score < 50
    Thresholds updated to be more selective and realistic for VC outcomes.
    """
    if score >= 65:
        return "🟢 INVEST - High-conviction opportunity"
    elif score >= 50:
        return "🟡 MONITOR - Promising but requires observation"
    else:
        return "🔴 AVOID - Risk outweighs return"

def generate_insights(data, success_probability, predicted_funding):
    """
    Generate business insights.
    """
    insights = []
    
    # Success outlook insights (no explicit probability shown)
    if success_probability > 0.8:
        insights.append("Exceptional success outlook — strong fundamentals across all metrics")
    elif success_probability > 0.6:
        insights.append("Above-average success outlook with solid business foundation")
    elif success_probability > 0.4:
        insights.append("Moderate success potential — consider risk mitigation strategies")
    else:
        insights.append("Below-average success indicators — significant risk factors present")
    
    # Funding insights
    funding_ratio = data['funding_amount_usd'] / predicted_funding if predicted_funding > 0 else 1
    if funding_ratio > 1.2:
        insights.append("Current funding request exceeds ML prediction - may be overvalued")
    elif funding_ratio < 0.8:
        insights.append("Conservative funding request - good value opportunity")
    else:
        insights.append("Funding request aligns well with predicted optimal amount")
    
    # Market insights
    if data['market_size_billion_usd'] > 10 and data['competition_level'] <= 5:
        insights.append("Large addressable market with manageable competition - excellent positioning")
    elif data['competition_level'] > 8:
        insights.append("Highly competitive market - differentiation strategy critical")
    
    # Team insights
    if data['team_size'] < 10 and data['funding_round'] in ['Series A', 'Series B']:
        insights.append("Lean team for funding stage - efficient execution or scaling concerns")
    elif data['team_size'] > 100 and data['funding_round'] == 'Seed':
        insights.append("Large team for early stage - strong initial traction but high burn rate")
    
    return insights[:3]  # Return top 3 insights

def generate_investment_commentary(data, success_probability, attractiveness_score, component_scores, predicted_funding):
    """
    Generate detailed commentary explaining the investment attractiveness rating.
    """
    commentary = []
    company_name = data['company_name']
    
    # Overall assessment opening
    if attractiveness_score >= 75:
        commentary.append(f"**  {company_name} presents an exceptional investment opportunity with strong fundamentals across all key metrics.")
    elif attractiveness_score >= 60:
        commentary.append(f"Success: {company_name} shows solid investment potential with several compelling strengths.")
    elif attractiveness_score >= 40:
        commentary.append(f"Warning: {company_name} presents a moderate investment opportunity with mixed signals requiring careful consideration.")
    else:
        commentary.append(f"🔴 {company_name} shows significant investment risks that outweigh potential returns at this time.")
    
    # Market analysis
    market_size = data['market_size_billion_usd']
    competition = data['competition_level']
    if component_scores['market_score'] >= 70:
        if market_size >= 20:
            commentary.append(f"Market: The company operates in a massive ${market_size:.1f}B market with manageable competition (level {competition}/10), indicating strong growth potential and market opportunity.")
        else:
            commentary.append(f"Growth: Despite a smaller ${market_size:.1f}B addressable market, low competition (level {competition}/10) creates favorable positioning for market share capture.")
    elif component_scores['market_score'] >= 40:
        commentary.append(f"Business: The ${market_size:.1f}B market presents decent opportunities, though competition level {competition}/10 may create challenges for rapid scaling.")
    else:
        if competition >= 8:
            commentary.append(f"Competition: High competition (level {competition}/10) in the ${market_size:.1f}B market will require exceptional execution and differentiation to succeed.")
        else:
            commentary.append(f"Risk: The limited ${market_size:.1f}B market size constrains long-term growth potential despite manageable competition.")
    
    # Financial health analysis (revenue removed)
    funding = data['funding_amount_usd']
    valuation = data['valuation_usd']

    if component_scores['financial_score'] >= 70:
        commentary.append(f"Strong: Solid financial position with ${funding/1e6:.1f}M funding and ${valuation/1e6:.1f}M valuation, indicating efficient capital deployment and strong investor confidence.")
    elif component_scores['financial_score'] >= 40:
        funding_efficiency = valuation / max(funding, 1)
        commentary.append(f"Balance: Moderate financial health with ${funding/1e6:.1f}M funding at ~{funding_efficiency:.1f}x efficiency to valuation; steady but with room for improvement.")
    else:
        funding_efficiency = valuation / max(funding, 1)
        if funding_efficiency < 5:
            commentary.append(f"Alert: Concerning valuation efficiency - ${valuation/1e6:.1f}M valuation on ${funding/1e6:.1f}M funding may indicate overvaluation or limited investor conviction.")
        else:
            commentary.append(f"Finance: Weak financial metrics with insufficient funding (${funding/1e6:.1f}M) to justify current ${valuation/1e6:.1f}M valuation; revisit capital strategy.")
    
    # Team and execution analysis
    team_size = data['team_size']
    years_operating = data['years_since_founding']
    
    if component_scores['team_score'] >= 70:
        if team_size >= 50:
            commentary.append(f"Team: Well-scaled team of {team_size} employees with {years_operating:.1f} years operating experience demonstrates strong execution capability and organizational maturity.")
        else:
            commentary.append(f"Focus: Lean but experienced team of {team_size} members operating for {years_operating:.1f} years shows efficient execution and focused product development.")
    elif component_scores['team_score'] >= 40:
        commentary.append(f"Staff: Team size of {team_size} with {years_operating:.1f} years experience is adequate for current stage, though scaling challenges may emerge with growth.")
    else:
        if team_size < 10:
            commentary.append(f"Warning: Small team of {team_size} members may struggle to execute ambitious growth plans, particularly given {years_operating:.1f} years of limited scaling.")
        else:
            commentary.append(f"Debug: Large team of {team_size} relative to operating history ({years_operating:.1f} years) suggests potential efficiency concerns or premature scaling.")
    
    # Growth potential and investor validation
    num_investors = data['num_investors']
    industry = data['industry']
    
    if component_scores['growth_score'] >= 70:
        commentary.append(f"Growth: Excellent growth trajectory supported by {num_investors} investor validation and strong position in the {industry} sector.")
    elif component_scores['growth_score'] >= 40:
        commentary.append(f"Analysis: Moderate growth potential in {industry} with {num_investors} investors, though execution risks remain.")
    else:
        if success_probability < 0.3:
            commentary.append(f"Risk: Limited growth prospects given low modeled success likelihood despite {num_investors} investor backing in {industry}.")
        else:
            commentary.append(f"Review: Modest investor validation ({num_investors} backers) in competitive {industry} sector requires stronger differentiation for breakthrough growth.")
    
    # Funding recommendation context
    funding_ratio = funding / max(predicted_funding, 1)
    if abs(funding_ratio - 1) > 0.3:  # More than 30% difference
        if funding_ratio > 1.3:
            commentary.append(f"Insight: Current ${funding/1e6:.1f}M funding exceeds ML-predicted optimal amount (${predicted_funding/1e6:.1f}M), suggesting potential for capital efficiency improvements.")
        else:
            commentary.append(f"Value: Current ${funding/1e6:.1f}M funding is conservative compared to ML-predicted optimal (${predicted_funding/1e6:.1f}M), indicating potential value opportunity.")
    
    # Risk factors and final recommendation context
    if attractiveness_score >= 75:
        commentary.append(f"Focus: Recommendation: STRONG BUY - Multiple positive factors align to create compelling risk-adjusted returns.")
    elif attractiveness_score >= 60:
        commentary.append(f"Success: Recommendation: BUY - Solid fundamentals outweigh risks, though monitor competitive dynamics and execution milestones closely.")
    elif attractiveness_score >= 40:
        commentary.append(f"Balance: Recommendation: HOLD - Mixed signals require deeper due diligence on team execution and market positioning before commitment.")
    else:
        commentary.append(f"Stop: Recommendation: AVOID - Current risk factors do not justify investment at this valuation.")
    
    return commentary

def _shrink_success_probability(p: float, data: dict | None = None) -> float:
    """Apply a conservative shrinkage to probabilities for bulk precompute.

    This mitigates overconfident in-sample probabilities by:
      1) Temperature scaling in logit space with tau>1 (flattens extremes)
      2) Blending with a base prior (default 0.4)
    """
    try:
        tau = float(os.environ.get('PRECOMPUTE_PROBA_TAU', '1.75'))
        base = float(os.environ.get('PRECOMPUTE_PROBA_PRIOR', '0.40'))
        alpha = float(os.environ.get('PRECOMPUTE_PROBA_ALPHA', '0.80'))
    except Exception:
        tau, base, alpha = 1.75, 0.40, 0.80

    try:
        p = float(p)
        p = min(max(p, 1e-6), 1 - 1e-6)
        logit = np.log(p / (1 - p))
        p_temp = 1.0 / (1.0 + np.exp(-logit / max(1e-3, tau)))
        p_blend = alpha * p_temp + (1 - alpha) * base
        return float(min(1.0, max(0.0, p_blend)))
    except Exception:
        return float(p)


def _apply_probability_policy(raw_probability: float, data: dict | None = None, *, context: str = 'interactive') -> tuple[float, bool]:
    """Return the probability value that should drive scoring along with a flag if tempering applied.

    Context values:
      - 'precompute': always apply shrinkage policy for dataset-wide scoring
      - 'interactive': apply shrinkage unless explicitly disabled via SHRINK_PROBABILITY_INTERACTIVE=false
    """
    try:
        prob = float(raw_probability)
    except Exception:
        prob = 0.5

    applied = False
    try:
        if context == 'precompute':
            prob_shrunk = _shrink_success_probability(prob, data)
            applied = abs(prob_shrunk - prob) > 1e-9
            return prob_shrunk, applied

        # Interactive / modal analysis path
        flag = os.environ.get('SHRINK_PROBABILITY_INTERACTIVE', 'true').strip().lower()
        if flag in {'1', 'true', 'yes', 'y'}:
            prob_shrunk = _shrink_success_probability(prob, data)
            applied = abs(prob_shrunk - prob) > 1e-9
            return prob_shrunk, applied
    except Exception:
        pass

    return prob, applied


def _probability_band_summary(probability: float) -> tuple[str, str]:
    """Return (band_key, band_label) describing qualitative success likelihood."""
    try:
        p = float(probability)
    except Exception:
        return 'unknown', 'Unknown'
    if p >= 0.60:
        return 'high', 'High'
    if p >= 0.45:
        return 'moderate', 'Moderate'
    return 'low', 'Low'


def _cohere_probability_tier(probability: float, score: float, tier_label: str) -> dict:
    """Enforce coherence between probability bands, attractiveness score, and tier labels.

    Returns a dict with adjusted probability, score, normalized tier key, display tier label,
    probability band metadata, and a flag indicating whether the probability was adjusted.
    """
    try:
        prob = float(probability)
    except Exception:
        prob = 0.5
    try:
        score_val = float(score)
    except Exception:
        score_val = 50.0

    normalized_tier = _normalize_investment_tier_label(tier_label)
    if not normalized_tier:
        if score_val >= TIER_SCORE_BOUNDS['invest'][0]:
            normalized_tier = 'invest'
        elif score_val >= TIER_SCORE_BOUNDS['monitor'][0]:
            normalized_tier = 'monitor'
        else:
            normalized_tier = 'avoid'

    probability_tier = 'invest'
    if prob < TIER_PROBABILITY_BOUNDS['monitor'][0]:
        probability_tier = 'avoid'
    elif prob < TIER_PROBABILITY_BOUNDS['invest'][0]:
        probability_tier = 'monitor'

    # Choose the riskier of the two tiers (higher risk rank) to avoid over-promising.
    tier_key = normalized_tier
    if TIER_RISK_ORDER[probability_tier] > TIER_RISK_ORDER.get(tier_key, 1):
        tier_key = probability_tier

    bounds = TIER_PROBABILITY_BOUNDS[tier_key]
    adjusted_prob = prob
    probability_adjusted = False
    if prob < bounds[0] - COHERENCE_TOLERANCE:
        adjusted_prob = bounds[0]
        probability_adjusted = True
    elif prob > bounds[1] + COHERENCE_TOLERANCE:
        adjusted_prob = bounds[1]
        probability_adjusted = True

    # Align score with the final tier window to avoid crossing thresholds inconsistently.
    score_bounds = TIER_SCORE_BOUNDS[tier_key]
    adjusted_score = score_val
    if tier_key == 'avoid':
        adjusted_score = min(score_val, score_bounds[1])
    elif tier_key == 'monitor':
        adjusted_score = min(score_bounds[1], max(score_bounds[0], score_val))
    else:  # invest
        adjusted_score = max(score_bounds[0], score_val)

    band_key, band_label = _probability_band_summary(adjusted_prob)
    lo_pct = int(round(bounds[0] * 100))
    hi_pct = int(round(bounds[1] * 100))
    range_note = f"Aligned with {TIER_DISPLAY_LABELS[tier_key]} tier ({lo_pct}–{hi_pct}% window)"

    return {
        'probability': float(adjusted_prob),
        'probability_band': band_key,
        'probability_band_label': f"{band_label} (~{adjusted_prob * 100:.0f}%)",
        'probability_range_note': range_note,
        'tier_key': tier_key,
        'tier_display': TIER_DISPLAY_LABELS[tier_key],
        'probability_adjusted': probability_adjusted,
        'score': float(adjusted_score),
    }


def analyze_company_comprehensive(company_data, precompute_mode: bool = False):
    """
    Comprehensive company analysis with ML predictions and investment commentary.
    Replacement for evaluate_startup_deal function.
    """
    try:
        # Prepare features for ML prediction
        X = prepare_features_for_prediction(company_data, active_classifier=startup_classifier)

        # Make ML predictions (probability always needed)
        raw_success_probability = float(startup_classifier.predict_proba(X)[0][1])
        probability_context = 'precompute' if precompute_mode else 'interactive'
        success_probability, shrink_applied = _apply_probability_policy(
            raw_success_probability,
            company_data,
            context=probability_context
        )
        probability_adjusted = bool(shrink_applied)
        if precompute_mode:
            # Fast path for precompute: skip expensive regressions and narrative generation
            attractiveness_score = calculate_attractiveness_score(
                success_probability=success_probability,
                market_size=company_data['market_size_billion_usd'],
                competition_level=company_data['competition_level'],
                team_size=company_data['team_size'],
                num_investors=company_data['num_investors']
            )
            tier_label = 'Invest' if attractiveness_score >= 60 else ('Monitor' if attractiveness_score >= 45 else 'Avoid')
            coherence = _cohere_probability_tier(success_probability, attractiveness_score, tier_label)
            success_probability = coherence['probability']
            probability_adjusted = probability_adjusted or coherence['probability_adjusted']
            attractiveness_score = coherence['score']
            investment_tier = coherence['tier_display']
            probability_band = coherence['probability_band']
            probability_band_label = coherence['probability_band_label']
            probability_range_note = coherence['probability_range_note']
            component_scores = calculate_component_scores_detailed(company_data, success_probability)
            risk_level = 'High' if attractiveness_score < 45 else 'Medium' if attractiveness_score < 60 else 'Low'
            # Return only minimal fields used by precompute/cache and API list views
            return {
                'company_name': company_data['company_name'],
                'attractiveness_score': attractiveness_score,
                'success_probability': success_probability,
                'raw_success_probability': raw_success_probability,
                'probability_tempering_applied': probability_adjusted,
                'probability_band': probability_band,
                'probability_band_label': probability_band_label,
                'probability_range_note': probability_range_note,
                'predicted_funding': None,
                'predicted_valuation': None,
                'recommendation': get_recommendation(attractiveness_score),
                'insights': [],
                'investment_commentary': [],
                'risk_level': risk_level,
                'investment_tier': investment_tier,
                'market_score': component_scores['market_score'],
                'team_score': component_scores['team_score'],
                'financial_score': component_scores['financial_score'],
                'growth_score': component_scores['growth_score']
            }

        # Full analysis path (interactive evaluation)
        predicted_funding = startup_regressor.predict(X)[0]
        try:
            predicted_valuation = startup_valuation_regressor.predict(X)[0]
        except Exception:
            predicted_valuation = max(0.0, predicted_funding * 10.0)

        attractiveness_score = calculate_attractiveness_score(
            success_probability=success_probability,
            market_size=company_data['market_size_billion_usd'],
            competition_level=company_data['competition_level'],
            team_size=company_data['team_size'],
            num_investors=company_data['num_investors']
        )
        tier_label = 'Invest' if attractiveness_score >= 60 else ('Monitor' if attractiveness_score >= 45 else 'Avoid')
        # Optional, env-tunable: if probability is extreme but attractiveness is Avoid, temper for presentation consistency
        try:
            enable = os.environ.get('PROB_TEMPER_ENABLE', 'true').strip().lower() in {'1','true','yes','y'}
            trip = float(os.environ.get('PROB_TEMPER_TRIP', '0.85'))  # trigger threshold
            cap_max = float(os.environ.get('PROB_TEMPER_MAX', '0.85'))
            floor = float(os.environ.get('PROB_TEMPER_MIN', '0.50'))
            only_avoid = os.environ.get('PROB_TEMPER_ONLY_AVOID', 'true').strip().lower() in {'1','true','yes','y'}
            apply_temper = enable and success_probability > trip and (not only_avoid or attractiveness_score < 45)
            if apply_temper:
                # Linear blend that nudges probability back toward cap_max when it exceeds trip
                # Keep monotonicity: higher raw prob => higher tempered prob, but bounded by [floor, cap_max]
                over = max(0.0, min(1.0, (success_probability - trip) / max(1e-6, 1.0 - trip)))
                tempered = cap_max - 0.15 * (1.0 - over)  # small spread below cap
                success_probability = float(max(floor, min(cap_max, tempered)))
                probability_adjusted = True
        except Exception:
            pass
        coherence = _cohere_probability_tier(success_probability, attractiveness_score, tier_label)
        success_probability = coherence['probability']
        probability_adjusted = probability_adjusted or coherence['probability_adjusted']
        attractiveness_score = coherence['score']
        investment_tier = coherence['tier_display']
        probability_band = coherence['probability_band']
        probability_band_label = coherence['probability_band_label']
        probability_range_note = coherence['probability_range_note']
        recommendation = get_recommendation(attractiveness_score)
        insights = generate_insights(company_data, success_probability, predicted_funding)
        component_scores = calculate_component_scores_detailed(company_data, success_probability)
        investment_commentary = generate_investment_commentary(
            company_data, success_probability, attractiveness_score, component_scores, predicted_funding
        )
        # Risk is tied to final attractiveness
        risk_level = 'High' if attractiveness_score < 45 else 'Medium' if attractiveness_score < 60 else 'Low'

        return {
            'company_name': company_data['company_name'],
            'attractiveness_score': attractiveness_score,
            'success_probability': success_probability,
            'raw_success_probability': raw_success_probability,
            'probability_tempering_applied': probability_adjusted,
            'probability_band': probability_band,
            'probability_band_label': probability_band_label,
            'probability_range_note': probability_range_note,
            'predicted_funding': predicted_funding,
            'predicted_valuation': predicted_valuation,
            'recommendation': recommendation,
            'insights': insights,
            'investment_commentary': investment_commentary,
            'risk_level': risk_level,
            'investment_tier': investment_tier,
            'market_score': component_scores['market_score'],
            'team_score': component_scores['team_score'],
            'financial_score': component_scores['financial_score'],
            'growth_score': component_scores['growth_score']
        }

    except Exception as e:
        print(f"Error: Error in company analysis: {e}")
        import traceback
        traceback.print_exc()

        # Return fallback analysis
        return {
            'company_name': company_data.get('company_name', 'Unknown Company'),
            'attractiveness_score': 50.0,
            'success_probability': 0.5,
            'raw_success_probability': raw_success_probability if 'raw_success_probability' in locals() else 0.5,
            'probability_tempering_applied': False,
            # If regressor isn't available, fall back to current funding (or 0 if unknown)
            'predicted_funding': company_data.get('funding_amount_usd', 0),
            'recommendation': "🟡 MONITOR - Analysis error, manual review required",
            'insights': ["Analysis error occurred", "Manual review recommended", "Data validation needed"],
            'investment_commentary': ["Warning: Analysis system encountered an error during evaluation.", "Debug: Manual review of company fundamentals is recommended.", "📋 Please verify data accuracy and rerun analysis."],
            'risk_level': 'High',
            'investment_tier': 'Monitor',
            'probability_band': 'moderate',
            'probability_band_label': 'Moderate (~50%)',
            'probability_range_note': 'Alignment unavailable due to analysis fallback',
            'market_score': 25.0,
            'team_score': 25.0,
            'financial_score': 25.0,
            'growth_score': 25.0
        }

def calculate_component_scores_detailed(data, success_probability):
    """Calculate detailed component scores for attractiveness breakdown with bounded normalization.

    This avoids early saturation at 100 and yields a wider, relative spread across companies.
    """
    try:
        # Market opportunity (logistic on market minus competition pressure)
        market_norm = _normalize_market(
            data.get('market_size_billion_usd', 0.0),
            data.get('competition_level', 5.0)
        )
        market_score = float(100.0 * market_norm)

        # Team & execution (log-normalized team size and linear years factor)
        team_norm = 0.7 * _log_norm(data.get('team_size', 0.0), 150.0) \
                    + 0.3 * min(1.0, max(0.0, float(data.get('years_since_founding', 0.0)) / 12.0))
        team_score = float(100.0 * min(1.0, max(0.0, team_norm)))

        # Financial health: funding and valuation log-normalized
        funding = float(data.get('funding_amount_usd', 0.0) or 0.0)
        valuation = float(data.get('valuation_usd', 0.0) or 0.0)
        funding_norm = _log_norm(funding, 20_000_000.0)      # approaches 1 near ~$20M
        valuation_norm = _log_norm(valuation, 200_000_000.0)  # approaches 1 near ~$200M
        financial_norm = 0.6 * funding_norm + 0.4 * valuation_norm
        financial_score = float(100.0 * min(1.0, max(0.0, financial_norm)))

        # Growth potential: investor base, efficiency, and predicted success
        num_investors = float(data.get('num_investors', 0.0) or 0.0)
        investor_norm = _log_norm(num_investors, 12.0)
        # Efficiency as valuation/funding; guard for zero/low funding
        eff = (valuation / funding) if funding > 0 else 0.0
        efficiency_norm = min(1.0, max(0.0, eff / 20.0))  # 20x ratio ~ strong upper bound
        success_norm = max(0.0, min(1.0, float(success_probability)))
        growth_norm = 0.35 * investor_norm + 0.35 * efficiency_norm + 0.30 * success_norm
        growth_score = float(100.0 * min(1.0, max(0.0, growth_norm)))

        return {
            'market_score': round(market_score, 1),
            'team_score': round(team_score, 1),
            'financial_score': round(financial_score, 1),
            'growth_score': round(growth_score, 1)
        }

    except Exception as e:
        print(f"Error calculating component scores: {e}")
        return {
            'market_score': 25,
            'team_score': 25,
            'financial_score': 25,
            'growth_score': 25
        }

def create_analysis_dashboard(data):
    """
    Create comprehensive analysis dashboard as image with enhanced, distinctive visualizations.
    """
    # Set up the plot with improved styling
    fig = plt.figure(figsize=(20, 13))
    fig.patch.set_facecolor('#f8f9fa')  # Light background
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3, top=0.92, bottom=0.08, left=0.08, right=0.95)
    
    # Modern title with gradient effect simulation
    fig.suptitle('📊 Startup Deal Analysis Dashboard', fontsize=24, fontweight='bold', 
                 color='#2c3e50', y=0.97, family='sans-serif')
    
    # Evaluate the startup
    evaluation = analyze_company_comprehensive(data)
    
    # 1. Deal Attractiveness Gauge - Enhanced with gradient and shadow
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#ffffff')
    score = evaluation['attractiveness_score']
    
    # Enhanced color palette with gradients
    if score >= 75:
        gauge_color = '#2ecc71'  # Vibrant green
        score_color = '#27ae60'
    elif score >= 65:
        gauge_color = '#3498db'  # Bright blue
        score_color = '#2980b9'
    elif score >= 50:
        gauge_color = '#f39c12'  # Warm orange
        score_color = '#e67e22'
    else:
        gauge_color = '#e74c3c'  # Strong red
        score_color = '#c0392b'
    
    # Create enhanced gauge chart
    theta = np.linspace(0, np.pi, 100)
    r = np.ones_like(theta)
    
    # Background arc (unfilled portion)
    ax1.plot(theta, r, color='#ecf0f1', linewidth=14, solid_capstyle='round', zorder=1)
    
    # Filled portion with shadow effect
    fill_theta = np.linspace(0, np.pi * score / 100, 50)
    fill_r = np.ones_like(fill_theta)
    
    # Shadow
    ax1.fill_between(fill_theta, 0, fill_r * 1.05, color='black', alpha=0.1, zorder=2)
    # Main gauge fill
    ax1.fill_between(fill_theta, 0, fill_r, color=gauge_color, alpha=0.85, zorder=3)
    # Border
    ax1.plot(fill_theta, fill_r, color=score_color, linewidth=3, solid_capstyle='round', zorder=4)
    
    ax1.set_ylim(0, 1.3)
    ax1.set_xlim(-0.3, np.pi + 0.3)
    
    # Score text with shadow
    ax1.text(np.pi/2 + 0.02, 0.52, f'{score:.1f}', ha='center', va='center', 
             fontsize=36, fontweight='bold', color='black', alpha=0.15, zorder=5)
    ax1.text(np.pi/2, 0.5, f'{score:.1f}', ha='center', va='center', 
             fontsize=36, fontweight='bold', color=score_color, zorder=6)
    
    # Label with background box
    ax1.text(np.pi/2, 0.15, 'Attractiveness Score', ha='center', va='center', 
             fontsize=11, fontweight='600', color='#34495e',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#bdc3c7', linewidth=1.5))
    
    ax1.set_title('📈 Deal Attractiveness', fontsize=15, fontweight='bold', 
                  color='#2c3e50', pad=15)
    ax1.axis('off')
    
    # 2. Success Probability Comparison - Enhanced with gradients and borders
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#ffffff')
    
    categories = ['This Deal', 'Industry\nAverage', 'Top\nQuartile']
    probabilities = [evaluation['success_probability'], 0.45, 0.75]
    
    # Distinct color scheme with borders
    colors_bar = [
        '#3498db' if probabilities[0] >= 0.6 else '#f39c12' if probabilities[0] >= 0.4 else '#e74c3c',
        '#95a5a6',  # Gray for average
        '#2ecc71'   # Green for top quartile
    ]
    edge_colors = [
        '#2980b9' if probabilities[0] >= 0.6 else '#e67e22' if probabilities[0] >= 0.4 else '#c0392b',
        '#7f8c8d',
        '#27ae60'
    ]
    
    # Create bars with borders and shadow
    bars = ax2.bar(categories, probabilities, color=colors_bar, alpha=0.85, 
                   edgecolor=edge_colors, linewidth=2.5, width=0.6)
    
    # Add shadow effect
    for i, bar in enumerate(bars):
        shadow = ax2.bar(i, probabilities[i], color='black', alpha=0.1, 
                        width=bar.get_width(), bottom=0.01, zorder=1)
    
    ax2.set_ylabel('Success Probability', fontsize=12, fontweight='600', color='#34495e')
    ax2.set_title('🎯 Success Probability Benchmark', fontsize=15, fontweight='bold', 
                  color='#2c3e50', pad=15)
    ax2.set_ylim(0, 1.05)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#bdc3c7')
    ax2.spines['bottom'].set_color('#bdc3c7')
    ax2.tick_params(colors='#34495e')
    ax2.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.8, color='#bdc3c7')
    
    # Enhanced value labels with background boxes
    for i, (bar, prob) in enumerate(zip(bars, probabilities)):
        label_color = edge_colors[i]
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03, 
                f'{prob:.0%}', ha='center', va='bottom', fontsize=13,
                fontweight='bold', color=label_color,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                         edgecolor=label_color, linewidth=1.5, alpha=0.95))
    
    # 3. Feature Contribution Analysis - Enhanced donut chart with distinct colors
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor('#ffffff')
    
    # Simulated feature importance for visualization
    features = ['Market Size', 'Team Strength', 'Competition', 'Funding Eff.', 'Investors']
    importance = [0.24, 0.22, 0.18, 0.18, 0.18]
    
    # Distinct, vibrant color palette
    pie_colors = ['#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
    explode = [0.05, 0.02, 0, 0, 0]  # Slightly explode top slices
    
    # Create donut chart with enhanced styling
    wedges, texts, autotexts = ax3.pie(importance, labels=features, autopct='%1.1f%%',
                                       colors=pie_colors, startangle=90, explode=explode,
                                       wedgeprops=dict(width=0.5, edgecolor='white', linewidth=3),
                                       textprops=dict(fontsize=10, fontweight='600', color='#2c3e50'))
    
    # Style percentage labels
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
    
    # Add center circle for donut effect with label
    centre_circle = plt.Circle((0, 0), 0.50, fc='#f8f9fa', edgecolor='#bdc3c7', linewidth=2)
    ax3.add_artist(centre_circle)
    ax3.text(0, 0, 'Key\nFactors', ha='center', va='center', fontsize=12, 
             fontweight='bold', color='#34495e')
    
    ax3.set_title('🔑 Success Factor Distribution', fontsize=15, fontweight='bold', 
                  color='#2c3e50', pad=15)
    
    # 4. Industry Landscape - Enhanced horizontal bars with gradient
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.set_facecolor('#ffffff')
    
    # Simulated industry data
    industries = ['Fintech', 'Healthcare', 'SaaS', 'E-commerce', 'AI/ML']
    success_rates = [0.68, 0.62, 0.71, 0.45, 0.59]
    current_industry = data.get('industry', 'SaaS')
    
    # Distinct colors with highlight for current industry
    colors_industry = []
    edge_colors_industry = []
    for ind, rate in zip(industries, success_rates):
        if ind == current_industry:
            colors_industry.append('#e74c3c')  # Red highlight for current
            edge_colors_industry.append('#c0392b')
        else:
            # Gradient based on success rate
            if rate >= 0.65:
                colors_industry.append('#2ecc71')
                edge_colors_industry.append('#27ae60')
            elif rate >= 0.55:
                colors_industry.append('#3498db')
                edge_colors_industry.append('#2980b9')
            else:
                colors_industry.append('#95a5a6')
                edge_colors_industry.append('#7f8c8d')
    
    # Create horizontal bars with enhanced styling
    bars = ax4.barh(industries, success_rates, color=colors_industry, alpha=0.85,
                   edgecolor=edge_colors_industry, linewidth=2, height=0.6)
    
    # Add subtle shadow
    for i, bar in enumerate(bars):
        ax4.barh(i, success_rates[i], color='black', alpha=0.08, 
                height=bar.get_height(), left=0.005, zorder=1)
    
    ax4.set_xlabel('Average Success Rate', fontsize=12, fontweight='600', color='#34495e')
    ax4.set_title('🏢 Industry Success Benchmark', fontsize=15, fontweight='bold', 
                  color='#2c3e50', pad=15)
    ax4.set_xlim(0, 0.85)
    ax4.spines['top'].set_visible(False)
    ax4.spines['right'].set_visible(False)
    ax4.spines['left'].set_color('#bdc3c7')
    ax4.spines['bottom'].set_color('#bdc3c7')
    ax4.tick_params(colors='#34495e')
    ax4.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.8, color='#bdc3c7')
    
    # Enhanced value labels with icons
    for i, (bar, rate, ind) in enumerate(zip(bars, success_rates, industries)):
        icon = '⭐' if ind == current_industry else ''
        ax4.text(rate + 0.02, bar.get_y() + bar.get_height()/2, 
                f'{icon} {rate:.0%}', va='center', fontsize=11,
                fontweight='bold', color=edge_colors_industry[i])
    
    # 5. Risk-Return Analysis - Enhanced scatter with quadrant styling
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.set_facecolor('#ffffff')
    
    # Plot this deal vs. benchmarks
    risk_score = 100 - evaluation['attractiveness_score']
    return_score = evaluation['success_probability'] * 100
    
    # Simulated peer data
    np.random.seed(42)
    peer_risk = np.random.uniform(20, 80, 20)
    peer_return = np.random.uniform(30, 90, 20)
    
    # Add colored quadrant backgrounds
    ax5.axhspan(50, 100, xmin=0, xmax=0.5, facecolor='#d5f4e6', alpha=0.3, zorder=1)  # Low Risk, High Return
    ax5.axhspan(50, 100, xmin=0.5, xmax=1, facecolor='#fff3cd', alpha=0.3, zorder=1)  # High Risk, High Return
    ax5.axhspan(0, 50, xmin=0, xmax=0.5, facecolor='#e8e8e8', alpha=0.3, zorder=1)   # Low Risk, Low Return
    ax5.axhspan(0, 50, xmin=0.5, xmax=1, facecolor='#f8d7da', alpha=0.3, zorder=1)   # High Risk, Low Return
    
    # Plot peer companies with enhanced styling
    ax5.scatter(peer_risk, peer_return, alpha=0.4, s=80, color='#95a5a6', 
               label='Industry Peers', edgecolor='#7f8c8d', linewidth=1, zorder=2)
    
    # Plot this deal with prominent styling
    ax5.scatter(risk_score, return_score, s=400, color='#e74c3c', marker='*', 
               label='This Deal', edgecolor='#c0392b', linewidth=3, zorder=5)
    # Add glow effect
    ax5.scatter(risk_score, return_score, s=600, color='#e74c3c', marker='*', 
               alpha=0.2, edgecolor='none', zorder=4)
    
    ax5.set_xlabel('Risk Score', fontsize=12, fontweight='600', color='#34495e')
    ax5.set_ylabel('Expected Return Score', fontsize=12, fontweight='600', color='#34495e')
    ax5.set_title('⚖️ Risk-Return Matrix', fontsize=15, fontweight='bold', 
                  color='#2c3e50', pad=15)
    ax5.set_xlim(0, 100)
    ax5.set_ylim(0, 100)
    
    # Style the axes
    ax5.spines['top'].set_visible(False)
    ax5.spines['right'].set_visible(False)
    ax5.spines['left'].set_color('#bdc3c7')
    ax5.spines['bottom'].set_color('#bdc3c7')
    ax5.tick_params(colors='#34495e')
    
    # Add center crosshairs
    ax5.axhline(50, color='#34495e', linestyle='--', linewidth=1.5, alpha=0.5, zorder=3)
    ax5.axvline(50, color='#34495e', linestyle='--', linewidth=1.5, alpha=0.5, zorder=3)
    
    # Enhanced quadrant labels with distinct styling
    ax5.text(75, 88, '⚠️ High Risk\nHigh Return', ha='center', va='center', fontsize=10,
            fontweight='bold', color='#d68910',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#fff3cd', 
                     edgecolor='#f39c12', linewidth=2, alpha=0.9))
    ax5.text(25, 88, '✅ Low Risk\nHigh Return', ha='center', va='center', fontsize=10,
            fontweight='bold', color='#196f3d',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#d5f4e6', 
                     edgecolor='#2ecc71', linewidth=2, alpha=0.9))
    ax5.text(25, 12, '💤 Low Risk\nLow Return', ha='center', va='center', fontsize=10,
            fontweight='bold', color='#5d6d7e',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#e8e8e8', 
                     edgecolor='#95a5a6', linewidth=2, alpha=0.9))
    ax5.text(75, 12, '🚨 High Risk\nLow Return', ha='center', va='center', fontsize=10,
            fontweight='bold', color='#943126',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#f8d7da', 
                     edgecolor='#e74c3c', linewidth=2, alpha=0.9))
    
    # Enhanced legend
    ax5.legend(loc='upper right', frameon=True, fancybox=True, shadow=True,
              fontsize=10, edgecolor='#bdc3c7', facecolor='white')
    
    # 6. Market Factors Analysis - Enhanced radar chart with gradient fill
    ax6 = fig.add_subplot(gs[1, 2], projection='polar')
    ax6.set_facecolor('#ffffff')
    
    factors = ['Market\nSize', 'Competition', 'Team\nSize', 'Valuation', 'Funding']
    scores = [
        min(100, data.get('market_size_billion_usd', 10) * 5),
        100 - data.get('competition_level', 5) * 10,
        min(100, data.get('team_size', 25) * 2),
        min(100, data.get('valuation_usd', 0) / 2000000),
        min(100, data.get('funding_amount_usd', 0) / 200000)
    ]
    
    # Normalize scores to 0-100
    scores = [min(100, max(0, score)) for score in scores]
    
    # Create radar chart with enhanced styling
    angles = np.linspace(0, 2 * np.pi, len(factors), endpoint=False).tolist()
    scores_plot = scores + [scores[0]]  # Complete the circle
    angles_plot = angles + [angles[0]]
    
    # Add reference circles with distinct colors
    ax6.plot(angles_plot, [25]*len(angles_plot), 'o-', linewidth=1, color='#e74c3c', 
            alpha=0.3, linestyle=':', zorder=1)
    ax6.plot(angles_plot, [50]*len(angles_plot), 'o-', linewidth=1, color='#f39c12', 
            alpha=0.3, linestyle=':', zorder=1)
    ax6.plot(angles_plot, [75]*len(angles_plot), 'o-', linewidth=1, color='#2ecc71', 
            alpha=0.3, linestyle=':', zorder=1)
    
    # Main data plot with shadow
    ax6.plot(angles_plot, scores_plot, 'o-', linewidth=3, color='#34495e', 
            alpha=0.15, markersize=8, zorder=2)  # Shadow
    ax6.plot(angles_plot, scores_plot, 'o-', linewidth=2.5, color='#3498db', 
            alpha=0.9, markersize=8, markerfacecolor='#2980b9', 
            markeredgecolor='white', markeredgewidth=2, zorder=3)
    
    # Gradient fill effect using multiple alpha layers
    ax6.fill(angles_plot, scores_plot, alpha=0.15, color='#3498db', zorder=2)
    ax6.fill(angles_plot, scores_plot, alpha=0.10, color='#5dade2', zorder=1)
    
    # Styling
    ax6.set_xticks(angles)
    ax6.set_xticklabels(factors, fontsize=10, fontweight='600', color='#2c3e50')
    ax6.set_ylim(0, 100)
    ax6.set_yticks([25, 50, 75, 100])
    ax6.set_yticklabels(['25', '50', '75', '100'], fontsize=8, color='#7f8c8d')
    ax6.grid(True, linestyle='--', linewidth=0.8, alpha=0.4, color='#bdc3c7')
    ax6.set_theta_offset(np.pi / 2)
    ax6.set_theta_direction(-1)
    
    # Add title with icon
    ax6.set_title('💼 Business Fundamentals', fontsize=15, fontweight='bold', 
                  color='#2c3e50', pad=25, y=1.1)
    
    # Save to buffer with high quality
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight', 
                facecolor='#f8f9fa', edgecolor='none', pad_inches=0.3)
    plt.close()
    
    return img_buffer

def _normalize_investment_tier_label(label: str) -> str:
    """Normalize investment tier string to one of {'invest','monitor','avoid'}.

    Backwards compatible with legacy labels: 'tier 1'/'tier1' and 'tier 2' map to 'invest',
    'tier 3' maps to 'monitor', and any 'avoid' or 'tier 4' maps to 'avoid'.
    """
    try:
        s = (label or '').lower().strip()
        if not s:
            return ''
        if 'avoid' in s or 'tier 4' in s or s in {'4', 'tier4', 't4'}:
            return 'avoid'
        if 'invest' in s or 'buy' in s or 'strong buy' in s or 'tier 1' in s or 'tier 2' in s or s in {'1', '2', 'tier1', 'tier2', 't1', 't2'}:
            return 'invest'
        if 'monitor' in s or 'hold' in s or 'tier 3' in s or s in {'3', 'tier3', 't3'}:
            return 'monitor'
        return ''
    except Exception:
        return ''

def precompute_investment_tiers(max_rows: int | None = None, *, force_refresh: bool = False):
    """Precompute analysis for all companies and cache results on the DataFrame.

    Adds columns to sample_data:
      - precomputed_attractiveness_score (float)
      - precomputed_investment_tier (str)
      - precomputed_investment_tier_norm (str: {'tier1','tier2','tier3','avoid'})
      - precomputed_recommendation (str)
      - precomputed_risk_level (str)
    and populates ANALYSIS_CACHE[company_id] with the full analysis dict. When force_refresh=True,
    cached analyses for the targeted rows are recomputed to reflect updated policies.
    """
    global sample_data, ANALYSIS_CACHE
    if sample_data is None or len(sample_data) == 0:
        return
    n_total = len(sample_data)
    n_limit = min(n_total, max_rows) if isinstance(max_rows, int) and max_rows is not None else n_total
    print(f"Loading: Precomputing investment tiers for {n_limit} companies...")
    # Prepare empty columns if not present
    for col, default in [
        ('precomputed_attractiveness_score', np.nan),
        ('precomputed_investment_tier', ''),
        ('precomputed_investment_tier_norm', ''),
        ('precomputed_recommendation', ''),
        ('precomputed_risk_level', ''),
    ]:
        if col not in sample_data.columns:
            sample_data[col] = default

    processed = 0
    processed_indices = []
    for idx, row in sample_data.head(n_limit).iterrows():
        try:
            company_id = str(row.get('company_id', ''))
            if not company_id:
                continue
            # Skip recomputation unless forced or cache missing
            cached = ANALYSIS_CACHE.get(company_id)
            if force_refresh and company_id in ANALYSIS_CACHE:
                ANALYSIS_CACHE.pop(company_id, None)
                cached = None
            if cached is None or not cached.get('investment_tier'):
                eval_data = {
                    'company_name': str(row.get('company_name', '')),
                    'industry': str(row.get('industry', '')),
                    'location': str(row.get('location', '')),
                    'funding_round': str(row.get('funding_round', '')),
                    'funding_amount_usd': float(row.get('funding_amount_usd', 0)) if pd.notna(row.get('funding_amount_usd')) else 0.0,
                    'valuation_usd': float(row.get('valuation_usd', 0)) if pd.notna(row.get('valuation_usd')) else 0.0,
                    'team_size': int(float(row.get('team_size', 0))) if pd.notna(row.get('team_size')) else 0,
                    'years_since_founding': float(row.get('years_since_founding', 0)) if pd.notna(row.get('years_since_founding')) else 0.0,
                    'revenue_usd': float(row.get('revenue_usd', 0)) if pd.notna(row.get('revenue_usd')) else 0.0,
                    'num_investors': int(float(row.get('num_investors', 0))) if pd.notna(row.get('num_investors')) else 0,
                    'competition_level': int(float(row.get('competition_level', 5))) if pd.notna(row.get('competition_level')) else 5,
                    'market_size_billion_usd': float(row.get('market_size_billion_usd', 1.0)) if pd.notna(row.get('market_size_billion_usd')) else 1.0,
                }
                analysis = analyze_company_comprehensive(eval_data, precompute_mode=True)
                ANALYSIS_CACHE[company_id] = analysis
            else:
                analysis = cached

            inv_tier = str(analysis.get('investment_tier', ''))
            inv_norm = _normalize_investment_tier_label(inv_tier)
            score_val = float(analysis.get('attractiveness_score', np.nan))
            sample_data.at[idx, 'precomputed_attractiveness_score'] = score_val
            sample_data.at[idx, 'precomputed_investment_tier'] = inv_tier
            sample_data.at[idx, 'precomputed_investment_tier_norm'] = inv_norm
            sample_data.at[idx, 'precomputed_recommendation'] = str(analysis.get('recommendation', ''))
            sample_data.at[idx, 'precomputed_risk_level'] = str(analysis.get('risk_level', ''))
            processed += 1
            processed_indices.append(idx)
            if processed % 200 == 0:
                print(f"   Precomputed {processed}/{n_limit} companies...")
        except Exception as _e:
            # Continue on individual row failures
            continue
    # DISABLED: Distribution-aware normalization that was overriding strict scoring
    # The normalization was forcing a fixed distribution (30% Invest, 45% Monitor, 25% Avoid)
    # regardless of actual company quality. With stricter scoring, we want natural distribution.
    # The strict scoring algorithm (lower base rates, tighter thresholds, stronger gating)
    # will naturally produce more companies in the Avoid tier without artificial remapping.
    try:
        if processed_indices:
            s = sample_data.loc[processed_indices, 'precomputed_attractiveness_score'].astype(float)
            # Report the NATURAL distribution from strict scoring
            def _tier(x: float) -> str:
                return 'invest' if x >= 65 else ('monitor' if x >= 50 else 'avoid')
            actual_tiers = s.apply(_tier).value_counts()
            invest_pct = (actual_tiers.get('invest', 0) / len(s)) * 100
            monitor_pct = (actual_tiers.get('monitor', 0) / len(s)) * 100
            avoid_pct = (actual_tiers.get('avoid', 0) / len(s)) * 100
            print(f"Info: Natural distribution from strict scoring → Invest: {invest_pct:.0f}%, Monitor: {monitor_pct:.0f}%, Avoid: {avoid_pct:.0f}%")
    except Exception as _norm_err:
        print(f"Warning: Distribution reporting skipped due to error: {_norm_err}")
    print(f"Success: Precomputed tiers for {processed} companies (of {n_limit})")

#############################
# Fast bootstrap + lazy train
#############################

def _fast_bootstrap_models(n_samples: int = 300):
    """Train a tiny, fast baseline on synthetic data so the app can serve immediately.

    - Uses LogisticRegression (balanced) for classification
    - Small RandomForestRegressor for funding/valuation
    - Sets a small sample_data for list endpoints
    - Auto-precomputes tiers for instant filtering
    - Completes in well under a second on typical laptops
    """
    global startup_classifier, startup_regressor, startup_valuation_regressor, feature_scaler, feature_columns, sample_data, training_numerical_columns, data_source
    try:
        df = generate_startup_data(max(100, int(n_samples)))
        data_source = "bootstrap:synthetic"
        # Engineer features quickly
        feat = engineer_features(df)
        X = feat['feature_matrix']
        y_class = feat['y_classification']
        y_reg = feat['y_regression']
        y_val = feat['y_valuation']

        # Store feature metadata
        feature_scaler = feat['scaler']
        feature_columns = feat['feature_names']
        training_numerical_columns = feat.get('numerical_columns', [
            'funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding',
            'num_investors', 'competition_level', 'market_size_billion_usd',
            'funding_efficiency', 'funding_per_employee',
            'funding_amount_log', 'valuation_log'
        ])

        # Very fast baseline models
        from sklearn.linear_model import LogisticRegression
        startup_classifier = ThresholdedClassifier(
            LogisticRegression(max_iter=100, class_weight='balanced', n_jobs=None, solver='lbfgs'),
            threshold=0.5
        )
        startup_classifier.base_estimator.fit(X, y_class)

        # Bind feature bundle to classifier for stable inference
        _bind_feature_bundle_to_classifier(
            startup_classifier,
            feature_columns,
            training_numerical_columns,
            feature_scaler
        )

        from sklearn.ensemble import RandomForestRegressor
        startup_regressor = RandomForestRegressor(n_estimators=80, max_depth=None, random_state=42, n_jobs=-1)
        startup_regressor.fit(X, y_reg)
        startup_valuation_regressor = RandomForestRegressor(n_estimators=80, max_depth=None, random_state=42, n_jobs=-1)
        startup_valuation_regressor.fit(X, y_val)

        # Keep a small sample for UI list views
        sample_df = df.copy()
        try:
            sample_df['industry_group'] = sample_df['industry'].apply(consolidate_industry)
            sample_df['region'] = sample_df['location'].apply(map_location_to_region)
        except Exception:
            pass
        sample_data = sample_df.head(300).copy()
        
        # Auto-precompute tiers for instant filtering
        try:
            print("Bootstrap: Auto-precomputing tiers for instant filtering...")
            precompute_investment_tiers(max_rows=300)
            print("Bootstrap: Fast baseline models ready with precomputed tiers")
        except Exception as _pc_err:
            print(f"Bootstrap: Fast baseline models ready (precompute warning: {_pc_err})")
    except Exception as _boot_err:
        print(f"Bootstrap: Failed to build fast models: {_boot_err}")


_bg_thread = None

def _background_train_worker():
    """Background worker that performs full training and automatically precomputes tiers.

    Tier precomputation happens automatically after training completes for instant UI filtering.
    """
    try:
        # Auto-precompute is now the default; PRECOMPUTE_DISABLE honored if explicitly set
        _precompute_after = os.environ.get('PRECOMPUTE_DISABLE', 'false').lower() not in {'1', 'true', 'yes', 'y'}
        if not _precompute_after:
            # Override: disable precompute in background training when explicitly requested
            os.environ['PRECOMPUTE_DISABLE'] = 'true'
        
        train_models()
        
        if _precompute_after:
            print("Background: Auto-precomputing tiers after full training...")
            try:
                # Trigger automatic precomputation for 400 companies (fast and reasonable)
                precompute_investment_tiers(max_rows=400)
                print("Background: Auto-precompute completed successfully (400 companies)")
            except Exception as precomp_err:
                print(f"Background: Auto-precompute failed (non-fatal): {precomp_err}")
        
        print("Background: Full models trained and ready")
    except Exception as e:
        print(f"Background: Training failed: {e}")


def kickoff_background_training():
    """Start background training exactly once."""
    global _bg_thread
    if _bg_thread is None or not _bg_thread.is_alive():
        import threading as _th
        _bg_thread = _th.Thread(target=_background_train_worker, daemon=True)
        _bg_thread.start()
        print("Background: Training thread started")


# Initialize models when module is imported (optimized for instant startup)
print("Initializing Deal Scout models (instant-start mode)...")

# Default: do NOT heavy-train on import. Provide fast bootstrap and train in background.
_auto_train = os.environ.get('AUTO_TRAIN_ON_IMPORT', 'false').strip().lower() in ['true','1','yes']
_do_bootstrap = os.environ.get('BOOTSTRAP_FAST', 'true').strip().lower() in ['true','1','yes']
_lazy_bg = os.environ.get('LAZY_BACKGROUND_TRAIN', 'true').strip().lower() in ['true','1','yes']

if _auto_train:
    train_models()
    print("Models ready for web application!")
else:
    if _do_bootstrap:
        _fast_bootstrap_models(n_samples=300)
    else:
        # As a last resort, ensure we at least have some data and trivial models
        _fast_bootstrap_models(n_samples=150)
    if _lazy_bg:
        kickoff_background_training()
    else:
        print("Info: Background training disabled (LAZY_BACKGROUND_TRAIN=false)")