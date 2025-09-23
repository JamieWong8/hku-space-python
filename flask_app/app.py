#!/usr/bin/env python3
"""
Deal Scout - Flask Web Application
AI-powered startup investment analysis tool
"""

import os
import io
import base64
import json
from flask import Flask, render_template, request, jsonify, send_file, make_response
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our ML model and functions
from model import (
    generate_startup_data,
    analyze_company_comprehensive,
    create_analysis_dashboard,
    INDUSTRIES,
    LOCATIONS,
    FUNDING_ROUNDS,
    # Added: use canonical mappers to guarantee grouped filters even if globals are missing
    consolidate_industry,
    map_location_to_region
)

# Configure Flask app
app = Flask(__name__)
# Simple build identifier to verify running code version in API responses
BUILD_ID = f"app.py@{int(datetime.now().timestamp())}"
app.config['SECRET_KEY'] = 'startup-deal-evaluator-secret-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
app.jinja_env.auto_reload = True  # Force template reloading
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    # CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    # Strong no-cache headers to ensure latest templates/static are served
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Configure matplotlib for web use
plt.style.use('default')
sns.set_palette("husl")

@app.route('/')
def index():
    """Main dashboard page"""
    # Compute a simple template version based on file mtime to aid cache-busting and diagnostics
    try:
        template_path = os.path.join(app.root_path, 'templates', 'index.html')
        template_mtime = os.path.getmtime(template_path)
        template_version = f"index.html@{int(template_mtime)}"
    except Exception:
        template_version = 'unknown'

    print(f"[INDEX] Rendering templates/index.html (version: {template_version})")
    return render_template(
        'index.html',
        industries=INDUSTRIES,
        locations=LOCATIONS,
        funding_rounds=FUNDING_ROUNDS,
        template_version=template_version,
    )

@app.route('/__debug/info')
def debug_info():
    """Provide diagnostic info about templates and runtime for troubleshooting caching issues"""
    try:
        templates_dir = os.path.join(app.root_path, 'templates')
        index_path = os.path.join(templates_dir, 'index.html')
        index_exists = os.path.exists(index_path)
        index_mtime = os.path.getmtime(index_path) if index_exists else None
        info = {
            'templates_dir': templates_dir,
            'index_path': index_path,
            'index_exists': index_exists,
            'index_mtime_epoch': int(index_mtime) if index_mtime else None,
            'templates_auto_reload': app.config.get('TEMPLATES_AUTO_RELOAD', False),
            'send_file_max_age_default': app.config.get('SEND_FILE_MAX_AGE_DEFAULT', None),
            'debug_mode': app.debug,
            'build_id': BUILD_ID,
        }
    except Exception as e:
        info = {'error': str(e)}

    resp = make_response(json.dumps(info, indent=2))
    resp.mimetype = 'application/json'
    return resp

@app.route('/about')
def about():
    """About page with project information"""
    return render_template('about.html')

@app.route('/documentation')
def documentation():
    """Documentation page"""
    return render_template('documentation.html')

@app.route('/__build')
def build_info():
    """Return build identifier for diagnostics"""
    return jsonify({'build_id': BUILD_ID, 'timestamp': datetime.now().isoformat()})

@app.route('/__routes')
def list_routes():
    """List registered Flask routes for diagnostics"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'rule': str(rule),
            'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'}))
        })
    return jsonify({'routes': sorted(routes, key=lambda r: r['rule']), 'build_id': BUILD_ID})

@app.route('/api/visualizations/<startup_id>')
def api_visualizations(startup_id):
    """Generate visualization dashboard for a startup"""
    try:
        # Get startup data from session or form
        data = request.args.to_dict()
        
        # Convert numeric fields
        numeric_fields = [
            'funding_amount_usd', 'valuation_usd', 'team_size',
            'years_since_founding', 'revenue_usd', 'num_investors',
            'competition_level', 'market_size_billion_usd'
        ]
        
        for field in numeric_fields:
            if field in data:
                try:
                    if field in ['team_size', 'num_investors', 'competition_level']:
                        data[field] = int(float(data[field]))
                    else:
                        data[field] = float(data[field])
                except (ValueError, TypeError):
                    data[field] = 0
        
        # Generate visualization
        img_buffer = create_analysis_dashboard(data)
        img_buffer.seek(0)
        
        return send_file(img_buffer, mimetype='image/png')
        
    except Exception as e:
        # Return error image
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'Error generating visualization:\n{str(e)}', 
                ha='center', va='center', fontsize=12, color='red')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return send_file(img_buffer, mimetype='image/png')

@app.route('/api/data-source')
def api_data_source():
    """Get information about the current data source"""
    try:
        from model import data_source, sample_data
        
        source_info = {
            'data_source': data_source,
            'dataset_size': len(sample_data) if sample_data is not None else 0,
            'success_rate': sample_data['is_successful'].mean() if sample_data is not None else 0,
            'is_kaggle_data': data_source.startswith('kaggle:'),
            'kaggle_dataset': data_source.split(':', 1)[1] if data_source.startswith('kaggle:') else None
        }
        
        if source_info['is_kaggle_data']:
            source_info['status'] = '✅ Using real Kaggle startup data'
            source_info['description'] = f"Training on {source_info['dataset_size']} real companies from {source_info['kaggle_dataset']}"
        else:
            source_info['status'] = '🔄 Using high-quality synthetic data'
            source_info['description'] = f"Training on {source_info['dataset_size']} synthetic companies with realistic patterns"
        
        return jsonify(source_info)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get data source info: {str(e)}'}), 500

@app.route('/api/market-data')
def api_market_data():
    """Get market analysis data"""
    try:
        # Generate sample market data
        market_data = {
            'industry_success_rates': {
                'Fintech': 0.68,
                'Healthcare': 0.62,
                'E-commerce': 0.45,
                'SaaS': 0.71,
                'AI/ML': 0.59,
                'Blockchain': 0.34,
                'Gaming': 0.41,
                'EdTech': 0.53,
                'Green Tech': 0.48,
                'Biotech': 0.39
            },
            'funding_trends': {
                'Q1 2024': 2.3,
                'Q2 2024': 2.8,
                'Q3 2024': 3.1,
                'Q4 2024': 2.9,
                'Q1 2025': 3.4,
                'Q2 2025': 3.7
            },
            'avg_valuations': {
                'Seed': 8.5,
                'Series A': 45.2,
                'Series B': 120.8,
                'Series C': 285.3,
                'Series D+': 650.7
            }
        }
        return jsonify(market_data)
    except Exception as e:
        return jsonify({'error': f'Failed to get market data: {str(e)}'}), 500

@app.route('/api/companies')
def api_companies():
    """Browse companies from the Kaggle dataset"""
    try:
        from model import sample_data, data_source, grouped_industries, regions
        # Basic debug line to confirm code version and inbound tier param
        incoming_tier = request.args.get('tier', '')
        print(f"[API] /api/companies called build={BUILD_ID} tier_raw='{incoming_tier}'")
        
        if sample_data is None or len(sample_data) == 0:
            return jsonify({'error': 'No company data available'}), 404
        
        # Get query parameters for filtering and pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        # Guard against invalid per_page values (e.g., 0 or negative)
        if per_page < 1:
            per_page = 1
        search = request.args.get('search', '').lower()
        industry = request.args.get('industry', '')  # raw industry exact match (back-compat)
        location = request.args.get('location', '')  # raw location exact match (back-compat)
        # New consolidated filters
        industry_group = request.args.get('industry_group', '')
        # New consolidated region filter (formerly 'continent'); accept old param for back-compat
        region = request.args.get('region', '')
        if not region:
            # Back-compat shim: honor 'continent' if provided by older UI
            region = request.args.get('continent', '')
        funding_round = request.args.get('funding_round', '')
        status = request.args.get('status', '')
        # New: filter by computed investment tier across dataset
        tier_raw = request.args.get('tier', '')
        tier_filter = tier_raw.lower().strip()
        # Normalize tier variants from UI (e.g., "Tier 4 (Avoid)", "tier-1", "TIER2", numeric, etc.)
        def _normalize_tier(s: str) -> str:
            s = (s or '').lower().strip()
            if not s:
                return ''
            # Common aliases
            if 'avoid' in s or 'tier 4' in s or s in {'4', 'tier4', 't4'}:
                return 'avoid'
            # Three-tier mapping
            if 'invest' in s or 'buy' in s or 'strong buy' in s or 'tier 1' in s or 'tier 2' in s or s in {'1', '2', 'tier1', 'tier2', 't1', 't2'}:
                return 'invest'
            if 'monitor' in s or 'hold' in s or 'tier 3' in s or s in {'3', 'tier3', 't3'}:
                return 'monitor'
            # Fallback: accept new exact keys
            if s in {'invest', 'monitor', 'avoid'}:
                return s
            return ''
        tier_filter_norm = _normalize_tier(tier_filter)
        
        # Start with all companies
        filtered_companies = sample_data.copy()

        # Guarantee consolidated columns exist for robust filtering regardless of training-time globals
        try:
            if 'industry_group' not in filtered_companies.columns:
                filtered_companies['industry_group'] = (
                    filtered_companies['industry'].astype(str).apply(consolidate_industry)
                )
            if 'region' not in filtered_companies.columns:
                filtered_companies['region'] = (
                    filtered_companies['location'].astype(str).apply(map_location_to_region)
                )
        except Exception as _ensure_cols_err:
            print(f"[API] Warning: Failed to ensure consolidated columns: {_ensure_cols_err}")
        
        # Apply filters
        if search:
            filtered_companies = filtered_companies[
                filtered_companies['company_name'].str.lower().str.contains(search, na=False)
            ]
        
        if industry:
            filtered_companies = filtered_companies[filtered_companies['industry'] == industry]
        if industry_group and 'industry_group' in filtered_companies.columns:
            filtered_companies = filtered_companies[filtered_companies['industry_group'] == industry_group]
        
        if location:
            filtered_companies = filtered_companies[filtered_companies['location'] == location]
        if region and 'region' in filtered_companies.columns:
            filtered_companies = filtered_companies[filtered_companies['region'] == region]
        
        if funding_round:
            filtered_companies = filtered_companies[
                filtered_companies['funding_round'] == funding_round
            ]
        
        if status:
            if status == 'successful':
                filtered_companies = filtered_companies[filtered_companies['is_successful'] == 1]
            elif status == 'unsuccessful':
                filtered_companies = filtered_companies[filtered_companies['is_successful'] == 0]
        
        # Track filter diagnostics
        tier_pre_count = len(filtered_companies)
        tier_post_count = None
        tier_applied = False

        # If tier filtering requested, prefer precomputed columns for performance
        if tier_filter_norm in {"invest", "monitor", "avoid"}:
            initial_len = len(filtered_companies)
            print(f"[API] Applying tier filter (precomputed if available): '{tier_filter_norm}' (raw='{tier_raw}') on {initial_len} rows before pagination")
            try:
                # If precomputed columns exist, filter directly; otherwise fall back to on-the-fly computation
                if 'precomputed_investment_tier_norm' in filtered_companies.columns:
                    filtered_companies = filtered_companies[filtered_companies['precomputed_investment_tier_norm'] == tier_filter_norm]
                    tier_post_count = len(filtered_companies)
                    tier_applied = True
                    print(f"[API] Precomputed tier filter matched {tier_post_count} rows")
                else:
                    from model import analyze_company_comprehensive
                    computed_rows = []
                    for idx, row in filtered_companies.iterrows():
                        try:
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
                            inv_tier = analysis.get('investment_tier', 'Monitor')
                            itl = inv_tier.lower()
                            # Map legacy strings and new scheme to three buckets
                            if 'avoid' in itl or 'tier 4' in itl:
                                inv_tier_norm = 'avoid'
                            elif 'invest' in itl or 'buy' in itl or 'tier 1' in itl or 'tier 2' in itl:
                                inv_tier_norm = 'invest'
                            else:
                                inv_tier_norm = 'monitor'
                            if inv_tier_norm == tier_filter_norm:
                                rdict = row.to_dict()
                                rdict['_computed_attractiveness_score'] = float(analysis.get('attractiveness_score', 0.0))
                                rdict['_computed_investment_tier'] = inv_tier
                                rdict['_computed_recommendation'] = str(analysis.get('recommendation', ''))
                                rdict['_computed_risk_level'] = str(analysis.get('risk_level', 'Medium'))
                                computed_rows.append(rdict)
                        except Exception as _row_err:
                            continue
                    filtered_companies = pd.DataFrame(computed_rows) if computed_rows else filtered_companies.iloc[0:0].copy()
                    tier_post_count = len(filtered_companies)
                    tier_applied = True
                    print(f"[API] Fallback tier filter matched {tier_post_count} rows (from {initial_len})")
            except Exception as _tier_err:
                print(f"[API] Warning: tier filtering failed: {_tier_err}")
                tier_post_count = None
                tier_applied = False

        # Calculate pagination after any tier filtering
        total_count = len(filtered_companies)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # Get page of results
        page_companies = filtered_companies.iloc[start_idx:end_idx]
        
        # Convert to dict format for JSON response
        companies_list = []
        for _, company in page_companies.iterrows():
            try:
                company_dict = {
                    'company_id': str(company.get('company_id', '')),
                    'company_name': str(company.get('company_name', '')),
                    'industry': str(company.get('industry', '')),
                    'location': str(company.get('location', '')),
                    # expose consolidated groups for UI filters (keep detailed values too)
                    'industry_group': str(company.get('industry_group', 'Other')) if 'industry_group' in page_companies.columns else 'Other',
                    'region': str(company.get('region', 'Other')) if 'region' in page_companies.columns else 'Other',
                    'funding_round': str(company.get('funding_round', '')),
                    'funding_amount_usd': float(company.get('funding_amount_usd', 0)) if pd.notna(company.get('funding_amount_usd')) else 0.0,
                    'valuation_usd': float(company.get('valuation_usd', 0)) if pd.notna(company.get('valuation_usd')) else 0.0,
                    'team_size': int(float(company.get('team_size', 0))) if pd.notna(company.get('team_size')) else 0,
                    'years_since_founding': float(company.get('years_since_founding', 0)) if pd.notna(company.get('years_since_founding')) else 0.0,
                    'revenue_usd': float(company.get('revenue_usd', 0)) if pd.notna(company.get('revenue_usd')) else 0.0,
                    'status': str(company.get('status', '')),
                    'is_successful': int(float(company.get('is_successful', 0))) if pd.notna(company.get('is_successful')) else 0,
                    'success_score': float(company.get('success_score', 0)) if pd.notna(company.get('success_score')) else 0.0
                }

                # Provide additional raw fields for consistent frontend calc if needed
                company_dict['num_investors'] = int(float(company.get('num_investors', 0))) if pd.notna(company.get('num_investors')) else 0
                company_dict['competition_level'] = int(float(company.get('competition_level', 5))) if pd.notna(company.get('competition_level')) else 5
                company_dict['market_size_billion_usd'] = float(company.get('market_size_billion_usd', 1.0)) if pd.notna(company.get('market_size_billion_usd')) else 1.0

                # Enrich with backend-calculated attractiveness and tier so cards match analysis
                try:
                    # Prefer precomputed columns if available
                    if 'precomputed_attractiveness_score' in page_companies.columns:
                        val = company.get('precomputed_attractiveness_score', None)
                        if val is not None and pd.notna(val):
                            company_dict['attractiveness_score'] = float(val)
                    if 'precomputed_investment_tier' in page_companies.columns:
                        tier_val = company.get('precomputed_investment_tier', None)
                        if tier_val:
                            company_dict['investment_tier'] = str(tier_val)
                    if 'precomputed_recommendation' in page_companies.columns:
                        reco_val = company.get('precomputed_recommendation', None)
                        if reco_val:
                            company_dict['recommendation'] = str(reco_val)
                    if 'precomputed_risk_level' in page_companies.columns:
                        risk_val = company.get('precomputed_risk_level', None)
                        if risk_val:
                            company_dict['risk_level'] = str(risk_val)

                    # If still missing, compute on the fly as a fallback
                    if 'attractiveness_score' not in company_dict or 'investment_tier' not in company_dict:
                        from model import analyze_company_comprehensive
                        analysis = analyze_company_comprehensive({
                            'company_name': company_dict['company_name'],
                            'industry': company_dict['industry'],
                            'location': company_dict['location'],
                            'funding_round': company_dict['funding_round'],
                            'funding_amount_usd': company_dict['funding_amount_usd'],
                            'valuation_usd': company_dict['valuation_usd'],
                            'team_size': company_dict['team_size'],
                            'years_since_founding': company_dict['years_since_founding'],
                            'revenue_usd': company_dict['revenue_usd'],
                            'num_investors': company_dict['num_investors'],
                            'competition_level': company_dict['competition_level'],
                            'market_size_billion_usd': company_dict['market_size_billion_usd'],
                        })
                        company_dict['attractiveness_score'] = float(analysis.get('attractiveness_score', 0.0))
                        company_dict['investment_tier'] = str(analysis.get('investment_tier', 'Monitor'))
                        company_dict['recommendation'] = str(analysis.get('recommendation', '🟡 MONITOR - Moderate investment, monitor closely'))
                        company_dict['risk_level'] = str(analysis.get('risk_level', 'Medium'))
                except Exception:
                    pass
                companies_list.append(company_dict)
            except Exception as conversion_error:
                print(f"Error converting company data: {conversion_error}")
                print(f"Company data: {company.to_dict()}")
                continue
        
        # Get filter options for frontend
        try:
            # Handle mixed data types by converting to string first and filtering out nulls
            all_industries = sorted([str(x) for x in sample_data['industry'].dropna().unique() if str(x) != 'nan'])
            all_locations = sorted([str(x) for x in sample_data['location'].dropna().unique() if str(x) != 'nan'])
            all_funding_rounds = sorted([str(x) for x in sample_data['funding_round'].dropna().unique() if str(x) != 'nan'])
            all_statuses = sorted([str(x) for x in sample_data['status'].dropna().unique() if str(x) != 'nan'])

            # Grouped filters: compute on the fly if globals are missing/empty
            if grouped_industries and len(grouped_industries) > 0:
                all_industry_groups = grouped_industries
            else:
                try:
                    all_industry_groups = sorted(
                        [
                            str(x) for x in sample_data['industry'].astype(str)
                            .apply(consolidate_industry).dropna().unique()
                        ]
                    )
                except Exception:
                    all_industry_groups = []

            # Regions: prefer precomputed globals, else compute; hide 'Other' from options
            if regions and len(regions) > 0:
                computed_regions = regions
            else:
                try:
                    # Ensure we can derive a consolidated region list even if training-time column is missing
                    if 'region' in sample_data.columns:
                        region_series = sample_data['region'].astype(str)
                    else:
                        region_series = sample_data['location'].astype(str).apply(map_location_to_region)
                    computed_regions = sorted([str(x) for x in region_series.dropna().unique()])
                except Exception:
                    computed_regions = []

            # Remove 'Other' bucket from selectable options if present
            all_regions = [r for r in computed_regions if r and r != 'Other']
            # If for any reason empty, provide canonical region set to keep UI grouped
            if not all_regions:
                all_regions = ['Africa', 'Asia', 'Europe', 'Middle East', 'North America', 'Oceania', 'South America']
        except Exception as filter_error:
            print(f"Error creating filter options: {filter_error}")
            # Fallback to empty lists
            all_industries = []
            all_locations = []
            all_funding_rounds = []
            all_statuses = []
            all_industry_groups = []
            all_regions = ['Africa', 'Asia', 'Europe', 'Middle East', 'North America', 'Oceania', 'South America']
        
        response = {
            'companies': companies_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            },
            'filters': {
                'industries': all_industries,
                'locations': all_locations,
                'funding_rounds': all_funding_rounds,
                'statuses': all_statuses,
                'industry_groups': all_industry_groups,
                'regions': all_regions
            },
            'dataset_info': {
                'data_source': data_source,
                'total_companies': len(sample_data)
            },
            'applied_filters': {
                'tier_raw': tier_raw,
                'tier': tier_filter_norm,
                'tier_filter_applied': tier_applied,
                'tier_pre_count': tier_pre_count,
                'tier_post_count': tier_post_count
            },
            'build_id': BUILD_ID
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get companies: {str(e)}'}), 500

@app.route('/api/companies/<company_id>')
def api_company_detail(company_id):
    """Get detailed information for a specific company"""
    try:
        print(f"🔍 Company detail request for ID: {company_id}")
        from model import sample_data
        
        if sample_data is None:
            print("❌ No sample data available")
            return jsonify({'error': 'No company data available'}), 404
        
        # Find the company
        company_row = sample_data[sample_data['company_id'] == company_id]
        
        if len(company_row) == 0:
            print(f"❌ Company not found: {company_id}")
            return jsonify({'error': 'Company not found'}), 404
        
        company = company_row.iloc[0]
        print(f"✅ Found company: {company.get('company_name', 'Unknown')}")
        
        # Create detailed company profile with safe data access
        try:
            company_detail = {
                'company_id': str(company.get('company_id', '')),
                'company_name': str(company.get('company_name', '')),
                'industry': str(company.get('industry', '')),
                'location': str(company.get('location', '')),
                'funding_round': str(company.get('funding_round', '')),
                'funding_amount_usd': float(company.get('funding_amount_usd', 0)) if pd.notna(company.get('funding_amount_usd')) else 0.0,
                'valuation_usd': float(company.get('valuation_usd', 0)) if pd.notna(company.get('valuation_usd')) else 0.0,
                'team_size': int(float(company.get('team_size', 0))) if pd.notna(company.get('team_size')) else 0,
                'years_since_founding': float(company.get('years_since_founding', 0)) if pd.notna(company.get('years_since_founding')) else 0.0,
                'revenue_usd': float(company.get('revenue_usd', 0)) if pd.notna(company.get('revenue_usd')) else 0.0,
                'num_investors': int(float(company.get('num_investors', 0))) if pd.notna(company.get('num_investors')) else 0,
                'competition_level': int(float(company.get('competition_level', 0))) if pd.notna(company.get('competition_level')) else 5,
                'market_size_billion_usd': float(company.get('market_size_billion_usd', 0)) if pd.notna(company.get('market_size_billion_usd')) else 1.0,
                'status': str(company.get('status', 'Operating')),
                'is_successful': int(float(company.get('is_successful', 0))) if pd.notna(company.get('is_successful')) else 0,
                'success_score': float(company.get('success_score', 0)) if pd.notna(company.get('success_score')) else 0.0,
            }
            
            # Calculate derived metrics safely
            funding_amount = company_detail['funding_amount_usd']
            valuation = company_detail['valuation_usd']
            team_size = max(company_detail['team_size'], 1)
            revenue = company_detail['revenue_usd']
            market_size = max(company_detail['market_size_billion_usd'] * 1e9, 1)
            
            company_detail.update({
                'funding_efficiency': float(valuation / max(funding_amount, 1)),
                'revenue_per_employee': float(revenue / team_size),
                'funding_per_employee': float(funding_amount / team_size),
                'market_penetration': float(revenue / market_size)
            })
            
            print(f"✅ Company detail response ready with {len(company_detail)} fields")
            return jsonify(company_detail)
            
        except Exception as data_error:
            # Fallback to basic company info if detailed processing fails
            print(f"⚠️ Error processing company detail data: {data_error}")
            basic_company = {
                'company_id': str(company.get('company_id', '')),
                'company_name': str(company.get('company_name', 'Unknown Company')),
                'industry': str(company.get('industry', 'Unknown')),
                'location': str(company.get('location', 'Unknown')),
                'funding_round': str(company.get('funding_round', 'Unknown')),
                'funding_amount_usd': 0.0,
                'valuation_usd': 0.0,
                'team_size': 0,
                'years_since_founding': 0.0,
                'revenue_usd': 0.0,
                'num_investors': 0,
                'competition_level': 5,
                'market_size_billion_usd': 1.0,
                'status': 'Operating',
                'is_successful': 0,
                'success_score': 0.0,
                'funding_efficiency': 0.0,
                'revenue_per_employee': 0.0,
                'funding_per_employee': 0.0,
                'market_penetration': 0.0
            }
            print(f"✅ Returning basic company info fallback")
            return jsonify(basic_company)
        
    except Exception as e:
        print(f"❌ Error in company detail endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get company details: {str(e)}'}), 500

def api_company_quick_analyze(company_id):
    """Get quick analysis for a specific company - simplified version"""
    try:
        print(f"🔍 Quick analysis request for ID: {company_id}")
        from model import sample_data
        
        if sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Find the company
        company_row = sample_data[sample_data['company_id'] == company_id]
        if len(company_row) == 0:
            return jsonify({'error': 'Company not found'}), 404
        
        company = company_row.iloc[0]
        print(f"   Quick analyzing company: {company.get('company_name', 'Unknown')}")
        
        # Prepare data for ML evaluation - simplified
        eval_data = {
            'company_name': str(company.get('company_name', '')),
            'industry': str(company.get('industry', '')),
            'location': str(company.get('location', '')),
            'funding_round': str(company.get('funding_round', '')),
            'funding_amount_usd': float(company.get('funding_amount_usd', 0)) if pd.notna(company.get('funding_amount_usd')) else 1000000.0,
            'valuation_usd': float(company.get('valuation_usd', 0)) if pd.notna(company.get('valuation_usd')) else 5000000.0,
            'team_size': int(float(company.get('team_size', 0))) if pd.notna(company.get('team_size')) else 10,
            'years_since_founding': float(company.get('years_since_founding', 0)) if pd.notna(company.get('years_since_founding')) else 2.0,
            'revenue_usd': float(company.get('revenue_usd', 0)) if pd.notna(company.get('revenue_usd')) else 100000.0,
            'num_investors': int(float(company.get('num_investors', 0))) if pd.notna(company.get('num_investors')) else 3,
            'competition_level': int(float(company.get('competition_level', 0))) if pd.notna(company.get('competition_level')) else 5,
            'market_size_billion_usd': float(company.get('market_size_billion_usd', 0)) if pd.notna(company.get('market_size_billion_usd')) else 1.0,
        }
        
        # Run ML evaluation
        ml_result = analyze_company_comprehensive(eval_data)
        
        # Create simple analysis response
        analysis = {
            'company_id': company_id,
            'company_info': {
                'name': eval_data['company_name'],
                'industry': eval_data['industry'],
                'location': eval_data['location'],
                'funding_round': eval_data['funding_round'],
                'status': str(company.get('status', 'Operating'))
            },
            'ml_predictions': ml_result,
            'key_metrics': eval_data
        }
        
        print(f"✅ Quick analysis complete: {ml_result.get('attractiveness_score', 0):.1f}% attractiveness")
        return jsonify(analysis)
        
    except Exception as e:
        print(f"❌ Error in quick analysis endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to analyze company: {str(e)}'}), 500

@app.route('/api/companies/compare', methods=['POST'])
def api_companies_compare():
    """Compare multiple companies"""
    try:
        print("🔍 Company comparison request received")
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        
        if not company_ids:
            return jsonify({'error': 'No company IDs provided'}), 400
        
        print(f"   Comparing {len(company_ids)} companies: {company_ids}")
        
        from model import sample_data
        if sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Get detailed data for each company
        companies_data = []
        for company_id in company_ids:
            company_row = sample_data[sample_data['company_id'] == company_id]
            if len(company_row) > 0:
                company = company_row.iloc[0]
                company_detail = {
                    'company_id': str(company.get('company_id', '')),
                    'company_name': str(company.get('company_name', '')),
                    'industry': str(company.get('industry', '')),
                    'location': str(company.get('location', '')),
                    'funding_round': str(company.get('funding_round', '')),
                    'funding_amount_usd': float(company.get('funding_amount_usd', 0)) if pd.notna(company.get('funding_amount_usd')) else 0.0,
                    'valuation_usd': float(company.get('valuation_usd', 0)) if pd.notna(company.get('valuation_usd')) else 0.0,
                    'team_size': int(float(company.get('team_size', 0))) if pd.notna(company.get('team_size')) else 0,
                    'years_since_founding': float(company.get('years_since_founding', 0)) if pd.notna(company.get('years_since_founding')) else 0.0,
                    'revenue_usd': float(company.get('revenue_usd', 0)) if pd.notna(company.get('revenue_usd')) else 0.0,
                    'num_investors': int(float(company.get('num_investors', 0))) if pd.notna(company.get('num_investors')) else 0,
                    'competition_level': int(float(company.get('competition_level', 0))) if pd.notna(company.get('competition_level')) else 5,
                    'market_size_billion_usd': float(company.get('market_size_billion_usd', 0)) if pd.notna(company.get('market_size_billion_usd')) else 1.0,
                    'status': str(company.get('status', 'Operating')),
                    'is_successful': int(float(company.get('is_successful', 0))) if pd.notna(company.get('is_successful')) else 0,
                    'success_score': float(company.get('success_score', 0)) if pd.notna(company.get('success_score')) else 0.0,
                }
                companies_data.append(company_detail)
        
        print(f"✅ Successfully prepared comparison data for {len(companies_data)} companies")
        
        return jsonify({
            'companies': companies_data,
            'comparison_metrics': {
                'total_companies': len(companies_data),
                'avg_funding': sum(c['funding_amount_usd'] for c in companies_data) / len(companies_data) if companies_data else 0,
                'avg_valuation': sum(c['valuation_usd'] for c in companies_data) / len(companies_data) if companies_data else 0,
                'success_rate': sum(c['is_successful'] for c in companies_data) / len(companies_data) if companies_data else 0
            }
        })
        
    except Exception as e:
        print(f"❌ Error in company comparison endpoint: {e}")
        return jsonify({'error': f'Failed to compare companies: {str(e)}'}), 500

@app.route('/api/test-analyze')
def test_analyze_endpoint():
    """Test endpoint to verify route registration"""
    return jsonify({'status': 'Analyze endpoints working!', 'timestamp': str(pd.Timestamp.now()), 'build_id': BUILD_ID})

@app.route('/api/test-investment-commentary')
def test_investment_commentary():
    """Test endpoint to verify investment commentary generation"""
    try:
        # Test with a simple company data
        test_data = {
            'company_name': 'Test Company',
            'industry': 'Technology',
            'location': 'CA',
            'funding_round': 'Series A',
            'funding_amount_usd': 1000000,
            'valuation_usd': 5000000,
            'team_size': 15,
            'years_since_founding': 2,
            'revenue_usd': 500000,
            'num_investors': 3,
            'competition_level': 4,
            'market_size_billion_usd': 10
        }
        
        result = analyze_company_comprehensive(test_data)
        
        return jsonify({
            'status': 'Investment commentary test successful',
            'has_investment_commentary': 'investment_commentary' in result,
            'commentary_count': len(result.get('investment_commentary', [])),
            'commentary_sample': result.get('investment_commentary', [])[:2] if 'investment_commentary' in result else [],
            'attractiveness_score': result.get('attractiveness_score', 'N/A')
        })
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'Investment commentary test failed',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/companies/<company_id>/analyze', methods=['GET'])
def api_company_analyze(company_id):
    """Get comprehensive analysis for a specific company with enhanced dashboard visualizations"""
    try:
        # Write to file for debugging
        with open('debug_log.txt', 'a') as f:
            f.write(f"DEBUG: Company analysis request for ID: {company_id}\n")
            f.flush()
            
        from model import sample_data
        import numpy as np
        
        if sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Find the company
        company_row = sample_data[sample_data['company_id'] == company_id]
        if len(company_row) == 0:
            return jsonify({'error': 'Company not found'}), 404
        
        company = company_row.iloc[0]
        with open('debug_log.txt', 'a') as f:
            f.write(f"   Analyzing company: {company.get('company_name', 'Unknown')}\n")
            f.flush()
        
        # Prepare data for ML evaluation
        eval_data = {
            'company_name': str(company.get('company_name', '')),
            'industry': str(company.get('industry', '')),
            'location': str(company.get('location', '')),
            'funding_round': str(company.get('funding_round', '')),
            'funding_amount_usd': float(company.get('funding_amount_usd', 0)) if pd.notna(company.get('funding_amount_usd')) else 0.0,
            'valuation_usd': float(company.get('valuation_usd', 0)) if pd.notna(company.get('valuation_usd')) else 0.0,
            'team_size': int(float(company.get('team_size', 0))) if pd.notna(company.get('team_size')) else 0,
            'years_since_founding': float(company.get('years_since_founding', 0)) if pd.notna(company.get('years_since_founding')) else 0.0,
            'revenue_usd': float(company.get('revenue_usd', 0)) if pd.notna(company.get('revenue_usd')) else 0.0,
            'num_investors': int(float(company.get('num_investors', 0))) if pd.notna(company.get('num_investors')) else 0,
            'competition_level': int(float(company.get('competition_level', 0))) if pd.notna(company.get('competition_level')) else 5,
            'market_size_billion_usd': float(company.get('market_size_billion_usd', 0)) if pd.notna(company.get('market_size_billion_usd')) else 1.0,
        }
        
        # Run ML evaluation to get comprehensive analysis
        try:
            with open('debug_log.txt', 'a') as f:
                f.write(f"   Calling analyze_company_comprehensive...\n")
                f.flush()
            ml_result = analyze_company_comprehensive(eval_data)
            with open('debug_log.txt', 'a') as f:
                f.write("   Analysis completed successfully\n")
                f.write(f"   Investment commentary present: {'investment_commentary' in ml_result}\n")
                f.flush()
        except Exception as analysis_error:
            with open('debug_log.txt', 'a') as f:
                f.write(f"   ERROR in analyze_company_comprehensive: {analysis_error}\n")
                f.flush()
            return jsonify({
                'error': 'Analysis failed',
                'details': str(analysis_error),
                'company_id': company_id,
                'eval_data': eval_data
            }), 500
        
        # Generate industry comparison data
        industry = company.get('industry', 'Unknown')
        industry_companies = sample_data[sample_data['industry'] == industry]
        
        # Calculate industry averages
        industry_stats = {
            'avg_funding': float(industry_companies['funding_amount_usd'].mean()) if len(industry_companies) > 0 else 0,
            'avg_valuation': float(industry_companies['valuation_usd'].mean()) if len(industry_companies) > 0 else 0,
            'avg_team_size': float(industry_companies['team_size'].mean()) if len(industry_companies) > 0 else 0,
            'avg_revenue': float(industry_companies['revenue_usd'].mean()) if len(industry_companies) > 0 else 0,
            'avg_success_score': float(industry_companies['success_score'].mean()) if len(industry_companies) > 0 else 0,
            'total_companies': len(industry_companies)
        }
        
        # Create enhanced chart data leveraging dashboard functionality
        chart_data = generate_enhanced_dashboard_charts(company, industry_stats, ml_result, eval_data)
        
        # Calculate risk factors
        risk_factors = calculate_risk_factors(company, industry_stats)
        
        # Build comprehensive analysis response with dashboard data
        analysis = {
            'company_id': company_id,
            'company_info': {
                'name': str(company.get('company_name', '')),
                'industry': str(company.get('industry', '')),
                'location': str(company.get('location', '')),
                'funding_round': str(company.get('funding_round', '')),
                'status': str(company.get('status', 'Operating'))
            },
            'ml_predictions': ml_result,
            'industry_comparison': industry_stats,
            'risk_factors': risk_factors,
            'dashboard_charts': chart_data,
            'key_metrics': {
                'funding_amount': eval_data['funding_amount_usd'],
                'valuation': eval_data['valuation_usd'],
                'team_size': eval_data['team_size'],
                'revenue': eval_data['revenue_usd'],
                'years_operating': eval_data['years_since_founding'],
                'num_investors': eval_data['num_investors'],
                'market_size': eval_data['market_size_billion_usd']
            }
        }
        
        with open('debug_log.txt', 'a') as f:
            f.write(f"   Successfully analyzed company: {analysis['ml_predictions'].get('attractiveness_score', 'N/A')}% attractiveness\n")
            f.flush()
        return jsonify(analysis)
        
    except Exception as e:
        with open('debug_log.txt', 'a') as f:
            f.write(f"ERROR in analyze endpoint: {e}\n")
            import traceback
            f.write(f"Traceback: {traceback.format_exc()}\n")
            f.flush()
        return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        print(f"❌ Error in company analysis endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to analyze company: {str(e)}'}), 500

def generate_enhanced_dashboard_charts(company, industry_stats, ml_result, eval_data):
    """Generate enhanced chart data leveraging dashboard visualizations from evaluate_startup_deal"""
    try:
        import numpy as np
        
        # 1. Deal Attractiveness Gauge
        attractiveness_gauge = {
            'type': 'doughnut',
            'data': {
                'labels': ['Attractiveness Score', 'Room for Improvement'],
                'datasets': [{
                    'data': [ml_result['attractiveness_score'], 100 - ml_result['attractiveness_score']],
                    'backgroundColor': [
                        '#00dd00' if ml_result['attractiveness_score'] >= 80 else
                        '#88dd00' if ml_result['attractiveness_score'] >= 60 else
                        '#ffaa00' if ml_result['attractiveness_score'] >= 40 else
                        '#ff8800' if ml_result['attractiveness_score'] >= 20 else '#ff4444',
                        '#e9ecef'
                    ],
                    'borderWidth': 0
                }]
            },
            'options': {
                'cutout': '70%',
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': 'Deal Attractiveness Gauge'}
                }
            }
        }
        
        # 2. Success Probability Comparison
        success_comparison = {
            'type': 'bar',
            'data': {
                'labels': ['This Deal', 'Industry Avg', 'Top Quartile'],
                'datasets': [{
                    'label': 'Success Probability',
                    'data': [
                        ml_result['success_probability'] * 100,
                        45,  # Industry average
                        75   # Top quartile
                    ],
                    'backgroundColor': [
                        '#4ecdc4' if ml_result['success_probability'] >= 0.5 else '#ff6b6b',
                        '#95a5a6',
                        '#2ecc71'
                    ],
                    'borderWidth': 1
                }]
            },
            'options': {
                'indexAxis': 'y',
                'scales': {
                    'x': {'max': 100, 'min': 0}
                },
                'plugins': {
                    'title': {'display': True, 'text': 'Success Probability Benchmarking'}
                }
            }
        }
        
        # 3. Feature Contribution Analysis (Pie Chart)
        feature_contribution = {
            'type': 'pie',
            'data': {
                'labels': ['Revenue Growth', 'Market Size', 'Team Strength', 'Competition', 'Funding Efficiency'],
                'datasets': [{
                    'data': [25, 20, 18, 15, 12],  # Simulated importance weights
                    'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
                    'borderWidth': 1
                }]
            },
            'options': {
                'plugins': {
                    'title': {'display': True, 'text': 'Key Success Factors'}
                }
            }
        }
        
        # 4. Industry Success Rates
        industry_success = {
            'type': 'bar',
            'data': {
                'labels': ['Fintech', 'Healthcare', 'SaaS', 'E-commerce', 'AI/ML'],
                'datasets': [{
                    'label': 'Success Rate (%)',
                    'data': [68, 62, 71, 45, 59],
                    'backgroundColor': [
                        '#e74c3c' if eval_data['industry'] == industry else '#bdc3c7' 
                        for industry in ['Fintech', 'Healthcare', 'SaaS', 'E-commerce', 'AI/ML']
                    ],
                    'borderWidth': 1
                }]
            },
            'options': {
                'indexAxis': 'y',
                'scales': {
                    'x': {'max': 80, 'min': 0}
                },
                'plugins': {
                    'title': {'display': True, 'text': 'Industry Success Rates'}
                }
            }
        }
        
        # 5. Risk-Return Analysis (Scatter Plot)
        risk_score = 100 - ml_result['attractiveness_score']
        return_score = ml_result['success_probability'] * 100
        
        # Generate peer data for context
        np.random.seed(42)
        peer_risk = np.random.uniform(20, 80, 15).tolist()
        peer_return = np.random.uniform(30, 90, 15).tolist()
        
        risk_return_analysis = {
            'type': 'scatter',
            'data': {
                'datasets': [
                    {
                        'label': 'Industry Peers',
                        'data': [{'x': r, 'y': ret} for r, ret in zip(peer_risk, peer_return)],
                        'backgroundColor': 'rgba(128, 128, 128, 0.6)',
                        'borderColor': 'rgba(128, 128, 128, 0.8)',
                        'pointRadius': 5
                    },
                    {
                        'label': 'This Deal',
                        'data': [{'x': risk_score, 'y': return_score}],
                        'backgroundColor': 'rgba(255, 0, 0, 0.8)',
                        'borderColor': 'rgba(255, 0, 0, 1)',
                        'pointRadius': 12,
                        'pointStyle': 'star'
                    }
                ]
            },
            'options': {
                'scales': {
                    'x': {'title': {'display': True, 'text': 'Risk Score'}},
                    'y': {'title': {'display': True, 'text': 'Expected Return Score'}}
                },
                'plugins': {
                    'title': {'display': True, 'text': 'Risk-Return Positioning'}
                }
            }
        }
        
        # 6. Business Fundamentals Radar Chart
        factors = ['Market Size', 'Competition', 'Team Size', 'Revenue', 'Funding']
        scores = [
            min(100, eval_data.get('market_size_billion_usd', 10) * 5),
            100 - eval_data.get('competition_level', 5) * 10,
            min(100, eval_data.get('team_size', 25) * 2),
            min(100, eval_data.get('revenue_usd', 500000) / 50000),
            min(100, eval_data.get('funding_amount_usd', 5000000) / 200000)
        ]
        
        # Normalize scores to 0-100
        scores = [min(100, max(0, score)) for score in scores]
        
        business_fundamentals = {
            'type': 'radar',
            'data': {
                'labels': factors,
                'datasets': [{
                    'label': 'Business Fundamentals',
                    'data': scores,
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 2,
                    'pointBackgroundColor': 'rgba(54, 162, 235, 1)',
                    'pointBorderColor': '#fff',
                    'pointHoverBackgroundColor': '#fff',
                    'pointHoverBorderColor': 'rgba(54, 162, 235, 1)'
                }]
            },
            'options': {
                'scales': {
                    'r': {
                        'beginAtZero': True,
                        'max': 100
                    }
                },
                'plugins': {
                    'title': {'display': True, 'text': 'Business Fundamentals'}
                }
            }
        }
        
        # 7. Component Scores Breakdown
        component_scores = {
            'type': 'bar',
            'data': {
                'labels': ['Market Score', 'Team Score', 'Financial Score', 'Growth Score'],
                'datasets': [{
                    'label': 'Component Scores',
                    'data': [
                        ml_result.get('market_score', 25),
                        ml_result.get('team_score', 25),
                        ml_result.get('financial_score', 25),
                        ml_result.get('growth_score', 25)
                    ],
                    'backgroundColor': ['#007bff', '#28a745', '#ffc107', '#17a2b8'],
                    'borderWidth': 1
                }]
            },
            'options': {
                'scales': {
                    'y': {'max': 100, 'min': 0}
                },
                'plugins': {
                    'title': {'display': True, 'text': 'Investment Component Analysis'}
                }
            }
        }
        
        return {
            'attractiveness_gauge': attractiveness_gauge,
            'success_comparison': success_comparison,
            'feature_contribution': feature_contribution,
            'industry_success': industry_success,
            'risk_return_analysis': risk_return_analysis,
            'business_fundamentals': business_fundamentals,
            'component_scores': component_scores
        }
        
    except Exception as e:
        print(f"Error generating enhanced dashboard charts: {e}")
        return {}

def normalize_value(value, benchmark):
    """Normalize a value against a benchmark (benchmark = 100)"""
    if benchmark == 0:
        return 0
    return min(200, max(0, (value / benchmark) * 100))

def calculate_risk_factors(company, industry_stats):
    """Calculate risk factors for the company"""
    try:
        risk_factors = []
        
        # Funding risk
        company_funding = float(company.get('funding_amount_usd', 0))
        if company_funding < industry_stats['avg_funding'] * 0.5:
            risk_factors.append({
                'factor': 'Low Funding',
                'severity': 'high',
                'description': 'Company funding is significantly below industry average'
            })
        
        # Team size risk
        team_size = float(company.get('team_size', 0))
        if team_size < 5:
            risk_factors.append({
                'factor': 'Small Team',
                'severity': 'medium',
                'description': 'Small team size may limit execution capability'
            })
        
        # Revenue risk
        revenue = float(company.get('revenue_usd', 0))
        if revenue == 0:
            risk_factors.append({
                'factor': 'No Revenue',
                'severity': 'high',
                'description': 'Company has not yet generated revenue'
            })
        
        # Competition risk
        competition_level = int(float(company.get('competition_level', 5)))
        if competition_level >= 8:
            risk_factors.append({
                'factor': 'High Competition',
                'severity': 'medium',
                'description': 'Operating in a highly competitive market'
            })
        
        # Age risk
        years_operating = float(company.get('years_since_founding', 0))
        if years_operating > 10:
            risk_factors.append({
                'factor': 'Mature Company',
                'severity': 'low',
                'description': 'Limited growth potential for mature company'
            })
        elif years_operating < 1:
            risk_factors.append({
                'factor': 'Very Early Stage',
                'severity': 'medium',
                'description': 'High uncertainty due to early stage'
            })
        
        return risk_factors
        
    except Exception as e:
        print(f"Error calculating risk factors: {e}")
        return []

@app.route('/api/companies/analyze', methods=['POST'])
def api_companies_analyze():
    """Analyze companies using ML models"""
    try:
        print("🔍 Company analysis request received")
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        
        if not company_ids:
            return jsonify({'error': 'No company IDs provided'}), 400
        
        print(f"   Analyzing {len(company_ids)} companies: {company_ids}")
        
        from model import sample_data
        if sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Analyze each company using ML models
        analysis_results = []
        for company_id in company_ids:
            company_row = sample_data[sample_data['company_id'] == company_id]
            if len(company_row) > 0:
                company = company_row.iloc[0]
                
                # Prepare data for ML evaluation
                eval_data = {
                    'company_name': str(company.get('company_name', '')),
                    'industry': str(company.get('industry', '')),
                    'location': str(company.get('location', '')),
                    'funding_round': str(company.get('funding_round', '')),
                    'funding_amount_usd': float(company.get('funding_amount_usd', 0)) if pd.notna(company.get('funding_amount_usd')) else 0.0,
                    'valuation_usd': float(company.get('valuation_usd', 0)) if pd.notna(company.get('valuation_usd')) else 0.0,
                    'team_size': int(float(company.get('team_size', 0))) if pd.notna(company.get('team_size')) else 0,
                    'years_since_founding': float(company.get('years_since_founding', 0)) if pd.notna(company.get('years_since_founding')) else 0.0,
                    'revenue_usd': float(company.get('revenue_usd', 0)) if pd.notna(company.get('revenue_usd')) else 0.0,
                    'num_investors': int(float(company.get('num_investors', 0))) if pd.notna(company.get('num_investors')) else 0,
                    'competition_level': int(float(company.get('competition_level', 0))) if pd.notna(company.get('competition_level')) else 5,
                    'market_size_billion_usd': float(company.get('market_size_billion_usd', 0)) if pd.notna(company.get('market_size_billion_usd')) else 1.0,
                }
                
                # Run ML evaluation
                ml_result = analyze_company_comprehensive(eval_data)
                ml_result['company_id'] = company_id
                analysis_results.append(ml_result)
        
        print(f"✅ Successfully analyzed {len(analysis_results)} companies")
        
        return jsonify({
            'analysis_results': analysis_results,
            'summary': {
                'total_analyzed': len(analysis_results),
                'avg_attractiveness': sum(r['attractiveness_score'] for r in analysis_results) / len(analysis_results) if analysis_results else 0,
                'avg_success_probability': sum(r['success_probability'] for r in analysis_results) / len(analysis_results) if analysis_results else 0,
                'recommended_count': len([r for r in analysis_results if r['attractiveness_score'] >= 60])
            }
        })
        
    except Exception as e:
        print(f"❌ Error in company analysis endpoint: {e}")
        return jsonify({'error': f'Failed to analyze companies: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    import traceback
    # Write error details to file for debugging
    with open('error_debug.txt', 'a') as f:
        f.write(f"500 Error: {error}\n")
        f.write(f"Traceback: {traceback.format_exc()}\n")
        f.write("=" * 50 + "\n")
        f.flush()
    
    # Return detailed error in development
    if app.debug:
        return jsonify({
            'error': '500 Internal Server Error',
            'details': str(error),
            'traceback': traceback.format_exc()
        }), 500
    else:
        return render_template('error.html',
                             error_code=500, 
                             error_message="Internal server error"), 500

if __name__ == '__main__':
    try:
        # Check if we're in development mode
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        
        print("Starting Deal Scout Web Application")
        print("=" * 50)
        print(f"ML Models: Loaded and ready")
        print(f"Web Interface: http://localhost:5000")
        print(f"API Endpoints: /api/companies")
        print(f"Debug Mode: {debug_mode}")
        print("=" * 50)
        
        # Run the Flask app with error handling
        app.run(
            debug=True,  # Enable debug mode to force template reloading
            host='127.0.0.1',  # Use localhost specifically
            port=5000,
            threaded=True,
            use_reloader=False  # Disable auto-reloader to prevent crashes
        )
    except KeyboardInterrupt:
        print("\n🛑 Flask application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running Flask application: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Flask application shutdown complete")