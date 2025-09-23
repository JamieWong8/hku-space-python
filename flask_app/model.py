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
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, r2_score
import warnings
warnings.filterwarnings('ignore')

# Kaggle API integration - completely optional
KAGGLE_AVAILABLE = False
kaggle = None

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
    'target_success_rate': 0.35,  # Target 35% overall success rate (adjustable)
    'acquired_ipo_rate': 1.0,     # Companies marked as acquired/IPO are always successful
    'operating_base_rate': 0.4,   # Base rate for operating companies
    'closed_success_rate': 0.1,   # Some closed companies might have been successful exits
    'unknown_status_rate': 0.5,   # Companies with unknown status
    'funding_boost_threshold': 1000000,  # $1M+ funding boosts success probability
    'high_funding_boost_threshold': 5000000,  # $5M+ funding gets extra boost
    'enable_industry_boost': True,  # Whether to boost certain industries
    'enable_location_boost': True,  # Whether to boost certain locations
}

# Global models and data (initialized when module loads)
startup_classifier = None
startup_regressor = None
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
                
                # Extract and clean funding amount
                funding_amount = 1000000  # Default 1M
                if 'funding_total_usd' in row and pd.notna(row['funding_total_usd']):
                    funding_str = str(row['funding_total_usd']).strip()
                    if funding_str:
                        # Clean up funding string - remove commas and spaces
                        funding_clean = funding_str.replace(',', '').replace(' ', '').replace('"', '')
                        try:
                            funding_amount = float(funding_clean)
                            if funding_amount <= 0:
                                funding_amount = 1000000
                        except:
                            funding_amount = 1000000
                
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
                    is_successful = 1 if np.random.random() < SUCCESS_RATE_CONFIG['operating_rate'] else 0
                else:
                    is_successful = 1 if np.random.random() < SUCCESS_RATE_CONFIG['other_rate'] else 0
                
                # Create startup data entry
                company_data = {
                    'company_id': f'vc_{idx:04d}',
                    'company_name': real_company_name,
                    'industry': industry,
                    'location': location,
                    'funding_round': np.random.choice(['Seed', 'Series A', 'Series B', 'Series C']),
                    'funding_amount_usd': funding_amount,
                    'valuation_usd': funding_amount * np.random.uniform(3.0, 15.0),
                    'revenue_usd': funding_amount * np.random.uniform(0.1, 2.0),
                    'team_size': int(np.random.uniform(5, 200)),
                    'years_since_founding': np.random.uniform(0.5, 15.0),
                    'num_investors': int(np.random.uniform(1, 10)),
                    'competition_level': int(np.random.uniform(1, 10)),
                    'market_size_billion_usd': np.random.uniform(1.0, 50.0),
                    'status': status,
                    'is_successful': is_successful,
                    'success_score': float(is_successful)
                }
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
            
            if os.path.exists(local_csv):
                print(f"Loading: Loading failsafe data from investments_VC.csv...")
                
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(local_csv, low_memory=False, encoding=encoding, nrows=2000)
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
                        
                        # Extract and clean funding amount
                        funding_amount = 1000000  # Default 1M
                        if 'funding_total_usd' in row and pd.notna(row['funding_total_usd']):
                            funding_str = str(row['funding_total_usd']).strip()
                            if funding_str:
                                # Clean up funding string - remove commas and spaces
                                funding_clean = funding_str.replace(',', '').replace(' ', '').replace('"', '')
                                try:
                                    funding_amount = float(funding_clean)
                                    if funding_amount <= 0:
                                        funding_amount = 1000000
                                except:
                                    funding_amount = 1000000
                        
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
                            'valuation_usd': funding_amount * np.random.uniform(5, 15),
                            'revenue_usd': funding_amount * np.random.uniform(0.05, 0.3),
                            'team_size': np.random.randint(5, 100),
                            'years_since_founding': np.random.uniform(1, 8),
                            'num_investors': np.random.randint(1, 10),
                            'competition_level': np.random.randint(1, 10),
                            'market_size_billion_usd': np.random.uniform(1.0, 50.0),
                            'status': status,
                            'is_successful': is_successful,
                            'success_score': float(is_successful)
                        }
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
                        
                        if os.path.exists(investments_vc_path):
                            try:
                                print("   Loading data from investments_VC.csv using kagglehub...")
                                # Load the main dataset file directly
                                df = pd.read_csv(investments_vc_path, low_memory=False, nrows=2000)  # Limit for speed
                                
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
                        
                        if os.path.exists(objects_path) and os.path.exists(investments_path):
                            try:
                                # Load company information with real names
                                print("   Loading company data from objects.csv...")
                                objects_df = pd.read_csv(objects_path, low_memory=False, nrows=5000)  # Limit rows for speed
                                companies_df = objects_df[objects_df['entity_type'] == 'Company'].copy()
                                
                                # Load investment data
                                print("   Loading investment data from investments.csv...")
                                investments_df = pd.read_csv(investments_path, nrows=5000)  # Limit for speed
                                
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
        thread.join(timeout=30)  # 30 second timeout
        
        if thread.is_alive():
            print("Warning: Kaggle data loading timed out after 30 seconds")
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
    df_features['revenue_per_employee'] = df_features['revenue_usd'] / (df_features['team_size'] + 1)
    df_features['funding_per_employee'] = df_features['funding_amount_usd'] / (df_features['team_size'] + 1)
    df_features['market_penetration'] = df_features['revenue_usd'] / (df_features['market_size_billion_usd'] * 1e9 + 1)
    
    # Age categories
    df_features['age_category'] = pd.cut(df_features['years_since_founding'], 
                                       bins=[0, 1, 3, 5, 10, 100], 
                                       labels=['Startup', 'Early', 'Growth', 'Mature', 'Established'])
    
    # Team size categories
    df_features['team_size_category'] = pd.cut(df_features['team_size'], 
                                             bins=[0, 10, 50, 100, 500, 10000], 
                                             labels=['Small', 'Medium', 'Large', 'Very Large', 'Enterprise'])
    
    # Log transforms
    df_features['funding_amount_log'] = np.log1p(df_features['funding_amount_usd'])
    df_features['valuation_log'] = np.log1p(df_features['valuation_usd'])
    df_features['revenue_log'] = np.log1p(df_features['revenue_usd'])
    
    # Revenue flag
    df_features['has_revenue'] = (df_features['revenue_usd'] > 0).astype(int)
    
    # Competition categories
    df_features['competition_category'] = pd.cut(df_features['competition_level'], 
                                               bins=[0, 3, 6, 8, 10], 
                                               labels=['Low', 'Medium', 'High', 'Very High'])
    
    # Encode categorical variables
    categorical_columns = ['industry', 'location', 'funding_round', 'status', 
                          'age_category', 'team_size_category', 'competition_category']
    
    encoded_features = pd.get_dummies(df_features[categorical_columns], 
                                     prefix=categorical_columns, drop_first=True)
    
    # Numerical features
    numerical_columns = ['funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding', 
                        'revenue_usd', 'num_investors', 'competition_level', 'market_size_billion_usd',
                        'funding_efficiency', 'revenue_per_employee', 'funding_per_employee', 
                        'market_penetration', 'funding_amount_log', 'valuation_log', 'revenue_log', 'has_revenue']
    
    # Combine features
    X_features = pd.concat([df_features[numerical_columns], encoded_features], axis=1)
    
    # Scale numerical features
    scaler = StandardScaler()
    X_scaled = X_features.copy()
    X_scaled[numerical_columns] = scaler.fit_transform(X_features[numerical_columns])
    
    # Target variables
    y_classification = df_features['is_successful']
    y_regression = df_features['funding_amount_usd']
    
    return {
        'feature_matrix': X_scaled,
        'scaler': scaler,
        'numerical_columns': numerical_columns,
        'y_classification': y_classification,
        'y_regression': y_regression,
        'feature_names': list(X_scaled.columns)
    }

def train_models():
    """
    Train ML models and store globally.
    """
    global startup_classifier, startup_regressor, feature_scaler, feature_columns, sample_data, training_numerical_columns
    
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
    
    # Store for later use
    feature_scaler = feature_data['scaler']
    feature_columns = feature_data['feature_names']
    training_numerical_columns = feature_data.get('numerical_columns', [
        'funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding',
        'revenue_usd', 'num_investors', 'competition_level', 'market_size_billion_usd',
        'funding_efficiency', 'revenue_per_employee', 'funding_per_employee',
        'market_penetration', 'funding_amount_log', 'valuation_log', 'revenue_log', 'has_revenue'
    ])
    
    # Split data
    X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(
        X, y_class, test_size=0.2, random_state=42, stratify=y_class)
    
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X, y_reg, test_size=0.2, random_state=42)
    
    # Train classification model
    startup_classifier = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_split=5,
        min_samples_leaf=2, max_features='sqrt', random_state=42, n_jobs=-1)
    startup_classifier.fit(X_train_class, y_train_class)
    
    # Train regression model
    startup_regressor = RandomForestRegressor(
        n_estimators=100, max_depth=12, min_samples_split=5,
        min_samples_leaf=2, max_features='sqrt', random_state=42, n_jobs=-1)
    startup_regressor.fit(X_train_reg, y_train_reg)
    
    # Print performance
    class_accuracy = accuracy_score(y_test_class, startup_classifier.predict(X_test_class))
    reg_r2 = r2_score(y_test_reg, startup_regressor.predict(X_test_reg))
    
    print(f"AI: ML Models trained successfully!")
    print(f"   Classification accuracy: {class_accuracy:.1%}")
    print(f"   Regression R²: {reg_r2:.1%}")

    # Precompute investment tiers and attractiveness to speed up API filtering and UI rendering
    # Make this controllable via environment variables for faster startup during development
    #   PRECOMPUTE_DISABLE=true|1  -> skip precomputation
    #   PRECOMPUTE_MAX_ROWS=N      -> limit precomputation to first N rows
    try:
        _disable = os.environ.get('PRECOMPUTE_DISABLE', 'false').lower() in {'1', 'true', 'yes', 'y'}
        _max_rows_env = os.environ.get('PRECOMPUTE_MAX_ROWS', '').strip()
        _max_rows = None
        if _max_rows_env.isdigit():
            try:
                _max_rows = int(_max_rows_env)
            except Exception:
                _max_rows = None
        if _disable:
            print("Info: Skipping precompute_investment_tiers due to PRECOMPUTE_DISABLE")
        else:
            if _max_rows is not None:
                print(f"Info: Limiting precompute_investment_tiers to {_max_rows} rows via PRECOMPUTE_MAX_ROWS")
            precompute_investment_tiers(max_rows=_max_rows)
    except Exception as _pc_err:
        print(f"Warning: Failed to precompute investment tiers: {_pc_err}")

def prepare_features_for_prediction(data):
    """
    Prepare input data for ML prediction.
    """
    # Create DataFrame with single row
    df = pd.DataFrame([data])
    
    # Add derived features
    df['funding_efficiency'] = df['valuation_usd'] / (df['funding_amount_usd'] + 1)
    df['revenue_per_employee'] = df['revenue_usd'] / (df['team_size'] + 1)
    df['funding_per_employee'] = df['funding_amount_usd'] / (df['team_size'] + 1)
    df['market_penetration'] = df['revenue_usd'] / (df['market_size_billion_usd'] * 1e9 + 1)
    
    # Age categories
    df['age_category'] = pd.cut(df['years_since_founding'], 
                               bins=[0, 1, 3, 5, 10, 100], 
                               labels=['Startup', 'Early', 'Growth', 'Mature', 'Established'])
    
    # Team size categories
    df['team_size_category'] = pd.cut(df['team_size'], 
                                     bins=[0, 10, 50, 100, 500, 10000], 
                                     labels=['Small', 'Medium', 'Large', 'Very Large', 'Enterprise'])
    
    # Log transforms
    df['funding_amount_log'] = np.log1p(df['funding_amount_usd'])
    df['valuation_log'] = np.log1p(df['valuation_usd'])
    df['revenue_log'] = np.log1p(df['revenue_usd'])
    
    # Revenue flag
    df['has_revenue'] = (df['revenue_usd'] > 0).astype(int)
    
    # Competition categories
    df['competition_category'] = pd.cut(df['competition_level'], 
                                       bins=[0, 3, 6, 8, 10], 
                                       labels=['Low', 'Medium', 'High', 'Very High'])
    
    # Add status for encoding (dummy value)
    df['status'] = 'Operating'
    
    # Encode categorical variables
    categorical_columns = ['industry', 'location', 'funding_round', 'status', 
                          'age_category', 'team_size_category', 'competition_category']
    
    encoded_features = pd.get_dummies(df[categorical_columns], 
                                     prefix=categorical_columns, drop_first=True)
    
    # Numerical features (prefer the exact set used during training)
    default_numerical_columns = ['funding_amount_usd', 'valuation_usd', 'team_size', 'years_since_founding', 
                        'revenue_usd', 'num_investors', 'competition_level', 'market_size_billion_usd',
                        'funding_efficiency', 'revenue_per_employee', 'funding_per_employee', 
                        'market_penetration', 'funding_amount_log', 'valuation_log', 'revenue_log', 'has_revenue']
    numerical_columns = training_numerical_columns or default_numerical_columns
    
    # Drop any dummy columns not seen during training to avoid estimator feature name mismatches
    if feature_columns is not None:
        encoded_features = encoded_features[[c for c in encoded_features.columns if c in feature_columns]]
    
    # Combine features, then align to the exact training feature set in one vectorized step
    X_features = pd.concat([df[numerical_columns], encoded_features], axis=1)
    # Reindex once to avoid O(N^2) per-column inserts which can be extremely slow
    X_features = X_features.reindex(columns=list(feature_columns), fill_value=0)
    
    # Scale numerical features with safeguards
    X_scaled = X_features.copy()
    try:
        X_scaled[numerical_columns] = feature_scaler.transform(X_features[numerical_columns])
    except KeyError as ke:
        # If a KeyError occurs (e.g., unknown or missing columns), align strictly and retry
        missing = [c for c in numerical_columns if c not in X_features.columns]
        extra = [c for c in X_features.columns if c not in (feature_columns or [])]
        print(f"Warning: Feature alignment issue during scaling: {ke}. Missing numericals: {missing}. Extra cols dropped: {extra}.")
        aligned = X_features.reindex(columns=list(feature_columns), fill_value=0)
        X_scaled = aligned.copy()
        X_scaled[numerical_columns] = feature_scaler.transform(aligned[numerical_columns])
    except Exception as e:
        # Absolute fallback: return zeros except leave numericals unscaled (best-effort)
        print(f"Warning: Unexpected scaling error: {e}. Falling back to unscaled numericals.")
        X_scaled = X_features.copy()
    
    return X_scaled

def calculate_attractiveness_score(success_probability, revenue, market_size, competition_level, team_size, num_investors):
        """
        Calculate deal attractiveness score (0-100) with normalized scoring.

        Rationale for weights/caps:
        - Prior version allowed non-ML components (revenue/market/team/investors) to add up to 60 points,
            making "Avoid" nearly impossible even with very low success probability. We rebalance to ensure
            ML-driven success probability is the dominant factor while still rewarding fundamentals.

        Weights (sum to 100):
            - Success probability: 50%
            - Revenue: 15% (caps at $2M instead of $1M)
            - Market opportunity: 15% (softer scaling: (market_size - competition)/20)
            - Team size: 10% (caps at 100 people)
            - Investor count: 10% (caps at 10 investors)
        """
        # Normalize success probability to [0, 1]: map ~0.1 -> 0.0 and 0.9 -> 1.0
        normalized_success_prob = min(1.0, max(0.0, (success_probability - 0.1) * 1.25))

        # Normalize fundamentals with higher caps to avoid easy saturation
        revenue_norm = min(1.0, (revenue or 0.0) / 2_000_000.0)           # 0..1 at $2M
        market_norm = min(1.0, max(0.0, ((market_size or 0.0) - (competition_level or 0.0)) / 20.0))
        team_norm = min(1.0, (team_size or 0.0) / 100.0)                  # 0..1 at 100
        investors_norm = min(1.0, (num_investors or 0.0) / 10.0)          # 0..1 at 10

        score = (
                normalized_success_prob * 50 +
                revenue_norm * 15 +
                market_norm * 15 +
                team_norm * 10 +
                investors_norm * 10
        )
        return score

def get_recommendation(score):
    """
    Get investment recommendation based on normalized score using a 3-tier system:
      - Invest (green)
      - Monitor (yellow)
      - Avoid (red)
    Thresholds: Invest >= 60, Monitor >= 45, else Avoid.
    """
    if score >= 60:
        return "🟢 INVEST - High-conviction opportunity"
    elif score >= 45:
        return "🟡 MONITOR - Promising but requires observation"
    else:
        return "🔴 AVOID - Risk outweighs return"

def generate_insights(data, success_probability, predicted_funding):
    """
    Generate business insights.
    """
    insights = []
    
    # Success probability insights
    if success_probability > 0.8:
        insights.append("Exceptional success indicators - strong fundamentals across all metrics")
    elif success_probability > 0.6:
        insights.append("Above-average success probability with solid business foundation")
    elif success_probability > 0.4:
        insights.append("Moderate success potential - consider risk mitigation strategies")
    else:
        insights.append("Below-average success indicators - significant risk factors present")
    
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
    
    # Financial health analysis
    revenue = data['revenue_usd']
    funding = data['funding_amount_usd']
    valuation = data['valuation_usd']
    
    if component_scores['financial_score'] >= 70:
        if revenue > 2000000:  # $2M+ revenue
            commentary.append(f"Revenue: Strong financial position with ${revenue/1e6:.1f}M annual revenue and ${funding/1e6:.1f}M funding raised, demonstrating proven market traction and efficient capital deployment.")
        else:
            commentary.append(f"Strong: Solid funding position of ${funding/1e6:.1f}M provides adequate runway, though revenue generation (${revenue/1e6:.1f}M) offers room for acceleration.")
    elif component_scores['financial_score'] >= 40:
        if revenue < 500000:
            commentary.append(f"Loading: Limited revenue traction (${revenue/1e6:.1f}M) relative to ${funding/1e6:.1f}M funding suggests the company is still in early market validation phase.")
        else:
            commentary.append(f"Balance: Moderate financial health with ${revenue/1e6:.1f}M revenue and ${funding/1e6:.1f}M funding, indicating steady but not exceptional progress.")
    else:
        funding_efficiency = valuation / max(funding, 1)
        if funding_efficiency < 5:
            commentary.append(f"Alert: Concerning valuation efficiency - ${valuation/1e6:.1f}M valuation on ${funding/1e6:.1f}M funding may indicate overvaluation or limited investor confidence.")
        else:
            commentary.append(f"Finance: Weak financial metrics with ${revenue/1e6:.1f}M revenue requiring significant improvement to justify current ${funding/1e6:.1f}M funding level.")
    
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
        commentary.append(f"Growth: Excellent growth trajectory supported by {num_investors} investor validation and strong position in the {industry} sector, with ML models predicting {success_probability:.1%} success probability.")
    elif component_scores['growth_score'] >= 40:
        commentary.append(f"Analysis: Moderate growth potential in {industry} with {num_investors} investors, though {success_probability:.1%} success probability suggests execution risks remain.")
    else:
        if success_probability < 0.3:
            commentary.append(f"Risk: Limited growth prospects with only {success_probability:.1%} predicted success probability despite {num_investors} investor backing in {industry}.")
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
        commentary.append(f"Focus: Recommendation: STRONG BUY - Multiple positive factors align to create compelling risk-adjusted returns with {success_probability:.1%} success probability.")
    elif attractiveness_score >= 60:
        commentary.append(f"Success: Recommendation: BUY - Solid fundamentals outweigh risks, though monitor competitive dynamics and execution milestones closely.")
    elif attractiveness_score >= 40:
        commentary.append(f"Balance: Recommendation: HOLD - Mixed signals require deeper due diligence on team execution and market positioning before commitment.")
    else:
        commentary.append(f"Stop: Recommendation: AVOID - Current risk factors and {success_probability:.1%} success probability do not justify investment at this valuation.")
    
    return commentary

def analyze_company_comprehensive(company_data):
    """
    Comprehensive company analysis with ML predictions and investment commentary.
    Replacement for evaluate_startup_deal function.
    """
    try:
        # Prepare features for ML prediction
        X = prepare_features_for_prediction(company_data)
        
        # Make ML predictions
        success_probability = startup_classifier.predict_proba(X)[0][1]
        predicted_funding = startup_regressor.predict(X)[0]
        
        # Calculate attractiveness score
        attractiveness_score = calculate_attractiveness_score(
            success_probability=success_probability,
            revenue=company_data['revenue_usd'],
            market_size=company_data['market_size_billion_usd'],
            competition_level=company_data['competition_level'],
            team_size=company_data['team_size'],
            num_investors=company_data['num_investors']
        )
        
        # Generate recommendation
        recommendation = get_recommendation(attractiveness_score)
        
        # Generate business insights
        insights = generate_insights(company_data, success_probability, predicted_funding)
        
        # Calculate component scores for detailed breakdown
        component_scores = calculate_component_scores_detailed(company_data, success_probability)
        
        # Generate detailed investment commentary
        investment_commentary = generate_investment_commentary(
            company_data, success_probability, attractiveness_score, component_scores, predicted_funding
        )
        
        # Determine risk level and investment tier using 3-tier scheme
        risk_level = 'High' if attractiveness_score < 45 else 'Medium' if attractiveness_score < 60 else 'Low'
        # 3-tier: Invest, Monitor, Avoid
        if attractiveness_score >= 60:
            investment_tier = 'Invest'
        elif attractiveness_score >= 45:
            investment_tier = 'Monitor'
        else:
            investment_tier = 'Avoid'
        
        return {
            'company_name': company_data['company_name'],
            'attractiveness_score': attractiveness_score,
            'success_probability': success_probability,
            'predicted_funding': predicted_funding,
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
            'predicted_funding': company_data.get('funding_amount_usd', 1000000),
            'recommendation': "🟡 MONITOR - Analysis error, manual review required",
            'insights': ["Analysis error occurred", "Manual review recommended", "Data validation needed"],
            'investment_commentary': ["Warning: Analysis system encountered an error during evaluation.", "Debug: Manual review of company fundamentals is recommended.", "📋 Please verify data accuracy and rerun analysis."],
            'risk_level': 'High',
            'investment_tier': 'Monitor',
            'market_score': 25.0,
            'team_score': 25.0,
            'financial_score': 25.0,
            'growth_score': 25.0
        }

def calculate_component_scores_detailed(data, success_probability):
    """Calculate detailed component scores for attractiveness breakdown"""
    try:
        # Market opportunity score (0-100)
        market_size = data['market_size_billion_usd']
        competition = data['competition_level']
        
        market_score = min(100, (market_size * 15) - (competition * 8) + 40)
        market_score = max(0, market_score)
        
        # Team & execution score (0-100)
        team_size = data['team_size']
        years_operating = data['years_since_founding']
        
        team_score = min(100, (team_size * 2.5) + (years_operating * 12) + 25)
        team_score = max(0, team_score)
        
        # Financial health score (0-100)
        revenue = data['revenue_usd']
        funding = data['funding_amount_usd']
        valuation = data['valuation_usd']
        
        revenue_score = min(50, revenue / 200000)  # $200k revenue = 50 points
        funding_score = min(30, funding / 2000000 * 30)  # $2M funding = 30 points
        valuation_score = min(20, valuation / 20000000 * 20)  # $20M valuation = 20 points
        
        financial_score = revenue_score + funding_score + valuation_score
        financial_score = max(0, min(100, financial_score))
        
        # Growth potential score (0-100) - based on success probability and metrics
        num_investors = data['num_investors']
        funding_efficiency = valuation / max(funding, 1)
        
        investor_score = min(35, num_investors * 7)  # Each investor = 7 points, max 35
        efficiency_score = min(35, funding_efficiency * 8)  # Efficiency multiplier
        probability_bonus = success_probability * 0.3  # Success probability contributes 30%
        
        growth_score = investor_score + efficiency_score + probability_bonus
        growth_score = max(0, min(100, growth_score))
        
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
    Create comprehensive analysis dashboard as image.
    """
    # Set up the plot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Growth: Startup Deal Analysis Dashboard', fontsize=20, fontweight='bold', y=0.95)
    
    # Evaluate the startup
    evaluation = analyze_company_comprehensive(data)
    
    # 1. Deal Attractiveness Gauge
    ax1 = axes[0, 0]
    score = evaluation['attractiveness_score']
    colors = ['#ff4444', '#ff8800', '#ffaa00', '#88dd00', '#00dd00']
    color_idx = min(int(score / 20), 4)
    
    # Create gauge chart
    theta = np.linspace(0, np.pi, 100)
    r = np.ones_like(theta)
    ax1.plot(theta, r, 'k-', linewidth=2)
    
    # Fill gauge based on score
    fill_theta = np.linspace(0, np.pi * score / 100, 50)
    fill_r = np.ones_like(fill_theta)
    ax1.fill_between(fill_theta, 0, fill_r, color=colors[color_idx], alpha=0.7)
    
    ax1.set_ylim(0, 1.2)
    ax1.set_xlim(-0.2, np.pi + 0.2)
    ax1.text(np.pi/2, 0.5, f'{score:.1f}', ha='center', va='center', fontsize=24, fontweight='bold')
    ax1.text(np.pi/2, 0.2, 'Attractiveness Score', ha='center', va='center', fontsize=12)
    ax1.set_title('Deal Attractiveness Gauge', fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    # 2. Success Probability Comparison
    ax2 = axes[0, 1]
    categories = ['This Deal', 'Industry Avg', 'Top Quartile']
    probabilities = [evaluation['success_probability'], 0.45, 0.75]
    colors_bar = ['#ff6b6b' if probabilities[0] < 0.5 else '#4ecdc4', '#95a5a6', '#2ecc71']
    
    bars = ax2.bar(categories, probabilities, color=colors_bar, alpha=0.8)
    ax2.set_ylabel('Success Probability', fontsize=12)
    ax2.set_title('Success Probability Benchmarking', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 1)
    
    # Add value labels on bars
    for bar, prob in zip(bars, probabilities):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{prob:.1%}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Feature Contribution Analysis
    ax3 = axes[0, 2]
    
    # Simulated feature importance for visualization
    features = ['Revenue Growth', 'Market Size', 'Team Strength', 'Competition', 'Funding Eff.']
    importance = [0.25, 0.20, 0.18, 0.15, 0.12]
    
    wedges, texts, autotexts = ax3.pie(importance, labels=features, autopct='%1.1f%%', 
                                      colors=plt.cm.Set3.colors, startangle=90)
    ax3.set_title('Key Success Factors', fontsize=14, fontweight='bold')
    
    # 4. Industry Landscape
    ax4 = axes[1, 0]
    
    # Simulated industry data
    industries = ['Fintech', 'Healthcare', 'SaaS', 'E-commerce', 'AI/ML']
    success_rates = [0.68, 0.62, 0.71, 0.45, 0.59]
    current_industry = data.get('industry', 'SaaS')
    
    colors_industry = ['#e74c3c' if ind == current_industry else '#bdc3c7' for ind in industries]
    bars = ax4.barh(industries, success_rates, color=colors_industry, alpha=0.8)
    ax4.set_xlabel('Average Success Rate', fontsize=12)
    ax4.set_title('Industry Success Rates', fontsize=14, fontweight='bold')
    ax4.set_xlim(0, 0.8)
    
    # Highlight current industry
    for bar, rate in zip(bars, success_rates):
        ax4.text(rate + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{rate:.1%}', va='center', fontweight='bold')
    
    # 5. Risk-Return Analysis
    ax5 = axes[1, 1]
    
    # Plot this deal vs. benchmarks
    risk_score = 100 - evaluation['attractiveness_score']
    return_score = evaluation['success_probability'] * 100
    
    # Simulated peer data
    np.random.seed(42)
    peer_risk = np.random.uniform(20, 80, 20)
    peer_return = np.random.uniform(30, 90, 20)
    
    ax5.scatter(peer_risk, peer_return, alpha=0.6, s=50, color='lightgray', label='Industry Peers')
    ax5.scatter(risk_score, return_score, s=200, color='red', marker='*', 
               label='This Deal', edgecolor='black', linewidth=2)
    
    ax5.set_xlabel('Risk Score', fontsize=12)
    ax5.set_ylabel('Expected Return Score', fontsize=12)
    ax5.set_title('Risk-Return Positioning', fontsize=14, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Add quadrant labels
    ax5.text(75, 85, 'High Risk\nHigh Return', ha='center', va='center', 
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    ax5.text(25, 85, 'Low Risk\nHigh Return', ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='green', alpha=0.3))
    ax5.text(25, 35, 'Low Risk\nLow Return', ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='gray', alpha=0.3))
    ax5.text(75, 35, 'High Risk\nLow Return', ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
    
    # 6. Market Factors Analysis
    ax6 = axes[1, 2]
    
    factors = ['Market Size', 'Competition', 'Team Size', 'Revenue', 'Funding']
    scores = [
        min(100, data.get('market_size_billion_usd', 10) * 5),
        100 - data.get('competition_level', 5) * 10,
        min(100, data.get('team_size', 25) * 2),
        min(100, data.get('revenue_usd', 500000) / 50000),
        min(100, data.get('funding_amount_usd', 5000000) / 200000)
    ]
    
    # Normalize scores to 0-100
    scores = [min(100, max(0, score)) for score in scores]
    
    # Create radar chart
    angles = np.linspace(0, 2 * np.pi, len(factors), endpoint=False).tolist()
    scores_plot = scores + [scores[0]]  # Complete the circle
    angles_plot = angles + [angles[0]]
    
    ax6.plot(angles_plot, scores_plot, 'o-', linewidth=2, color='blue', alpha=0.8)
    ax6.fill(angles_plot, scores_plot, alpha=0.25, color='blue')
    ax6.set_xticks(angles)
    ax6.set_xticklabels(factors)
    ax6.set_ylim(0, 100)
    ax6.set_title('Business Fundamentals', fontsize=14, fontweight='bold')
    ax6.grid(True)
    
    plt.tight_layout()
    
    # Save to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
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

def precompute_investment_tiers(max_rows: int | None = None):
    """Precompute analysis for all companies and cache results on the DataFrame.

    Adds columns to sample_data:
      - precomputed_attractiveness_score (float)
      - precomputed_investment_tier (str)
      - precomputed_investment_tier_norm (str: {'tier1','tier2','tier3','avoid'})
      - precomputed_recommendation (str)
      - precomputed_risk_level (str)
    and populates ANALYSIS_CACHE[company_id] with the full analysis dict.
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
    for idx, row in sample_data.head(n_limit).iterrows():
        try:
            company_id = str(row.get('company_id', ''))
            if not company_id:
                continue
            # Skip if already cached
            cached = ANALYSIS_CACHE.get(company_id)
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
                analysis = analyze_company_comprehensive(eval_data)
                ANALYSIS_CACHE[company_id] = analysis
            else:
                analysis = cached

            inv_tier = str(analysis.get('investment_tier', ''))
            inv_norm = _normalize_investment_tier_label(inv_tier)
            sample_data.at[idx, 'precomputed_attractiveness_score'] = float(analysis.get('attractiveness_score', np.nan))
            sample_data.at[idx, 'precomputed_investment_tier'] = inv_tier
            sample_data.at[idx, 'precomputed_investment_tier_norm'] = inv_norm
            sample_data.at[idx, 'precomputed_recommendation'] = str(analysis.get('recommendation', ''))
            sample_data.at[idx, 'precomputed_risk_level'] = str(analysis.get('risk_level', ''))
            processed += 1
            if processed % 200 == 0:
                print(f"   Precomputed {processed}/{n_limit} companies...")
        except Exception as _e:
            # Continue on individual row failures
            continue
    print(f"Success: Precomputed tiers for {processed} companies (of {n_limit})")

# Initialize models when module is imported (can be disabled via env)
print("Initializing ML models for Deal Scout...")
_auto_train = os.environ.get('AUTO_TRAIN_ON_IMPORT', 'true').strip().lower() in ['true','1','yes']
if _auto_train:
    train_models()
    print("Models ready for web application!")
else:
    print("Skipping auto training on import due to AUTO_TRAIN_ON_IMPORT=false")