#!/usr/bin/env python3
"""
Deal Scout - Flask Web Application
AI-powered startup investment analysis tool
"""

import os
import sys
import io
import base64
import json
import time
import traceback
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
# Ensure local imports work whether run as a script or imported as a package
try:
    sys.path.insert(0, os.path.dirname(__file__))
except Exception:
    pass

# Import model module itself to access dynamic globals
import model
from model import (
    generate_startup_data,
    analyze_company_comprehensive,
    create_analysis_dashboard,
    INDUSTRIES,
    LOCATIONS,
    FUNDING_ROUNDS,
    # Added: use canonical mappers to guarantee grouped filters even if globals are missing
    consolidate_industry,
    map_location_to_region,
    TIER_PROBABILITY_BOUNDS,
    COHERENCE_TOLERANCE,
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

# Cache for filter options to avoid recomputing on every request
_FILTER_OPTIONS_CACHE = {
    'data': None,
    'timestamp': 0,
    'ttl': 300  # 5 minutes cache
}

def get_cached_filter_options():
    """Get cached filter options or compute if expired"""
    import time
    current_time = time.time()
    
    # Check if cache is valid
    if (_FILTER_OPTIONS_CACHE['data'] is not None and 
        current_time - _FILTER_OPTIONS_CACHE['timestamp'] < _FILTER_OPTIONS_CACHE['ttl']):
        return _FILTER_OPTIONS_CACHE['data']
    
    # Recompute filter options
    try:
        if model.sample_data is None or len(model.sample_data) == 0:
            return None
            
        all_industries = sorted([str(x) for x in model.sample_data['industry'].dropna().unique() if str(x) != 'nan'])
        all_locations = sorted([str(x) for x in model.sample_data['location'].dropna().unique() if str(x) != 'nan'])
        all_funding_rounds = sorted([str(x) for x in model.sample_data['funding_round'].dropna().unique() if str(x) != 'nan'])
        all_statuses = sorted([str(x) for x in model.sample_data['status'].dropna().unique() if str(x) != 'nan'])

        # Grouped filters
        if model.grouped_industries and len(model.grouped_industries) > 0:
            all_industry_groups = sorted(list(model.grouped_industries))
        else:
            try:
                all_industry_groups = sorted(model.sample_data['industry'].apply(consolidate_industry).unique().tolist())
            except Exception:
                all_industry_groups = ['Technology', 'Healthcare', 'Financial Services', 'Consumer', 'Other']

        # Regions
        if model.regions and len(model.regions) > 0:
            computed_regions = sorted(list(model.regions))
        else:
            try:
                computed_regions = sorted(model.sample_data['location'].apply(map_location_to_region).unique().tolist())
            except Exception:
                computed_regions = ['Africa', 'Asia', 'Europe', 'Middle East', 'North America', 'Oceania', 'South America']

        all_regions = [r for r in computed_regions if r and r != 'Other']
        if not all_regions:
            all_regions = ['Africa', 'Asia', 'Europe', 'Middle East', 'North America', 'Oceania', 'South America']
        
        filter_data = {
            'industries': all_industries,
            'locations': all_locations,
            'funding_rounds': all_funding_rounds,
            'statuses': all_statuses,
            'industry_groups': all_industry_groups,
            'regions': all_regions
        }
        
        # Update cache
        _FILTER_OPTIONS_CACHE['data'] = filter_data
        _FILTER_OPTIONS_CACHE['timestamp'] = current_time
        
        return filter_data
    except Exception as e:
        print(f"[API] Error computing filter options: {e}")
        return None

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

@app.route('/api/diagnostics/training-status')
def training_status():
    """Quick view of model bootstrap and background training status for instant-start mode."""
    try:
        from model import (
            data_source, sample_data, startup_classifier, startup_regressor, startup_valuation_regressor,
            _bg_thread
        )
        clf_name = type(getattr(startup_classifier, 'base_estimator', startup_classifier)).__name__
        
        # Check precomputation status
        precomputed_available = False
        precomputed_count = 0
        if sample_data is not None and 'precomputed_attractiveness_score' in sample_data.columns:
            precomputed_count = int(sample_data['precomputed_attractiveness_score'].notna().sum())
            precomputed_available = precomputed_count > 0
        
        status = {
            'build_id': BUILD_ID,
            'data_source': data_source,
            'bootstrap_rows': 0 if sample_data is None else int(len(sample_data)),
            'classifier': clf_name,
            'regressors_ready': bool(startup_regressor is not None and startup_valuation_regressor is not None),
            'background_training_alive': bool(_bg_thread is not None and _bg_thread.is_alive()),
            'precomputed_available': precomputed_available,
            'precomputed_count': precomputed_count,
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'Failed to get training status: {str(e)}', 'build_id': BUILD_ID}), 500

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
        source_info = {
            'data_source': model.data_source,
            'dataset_size': len(model.sample_data) if model.sample_data is not None else 0,
            'success_rate': model.sample_data['is_successful'].mean() if model.sample_data is not None else 0,
            'is_kaggle_data': model.data_source.startswith('kaggle:'),
            'kaggle_dataset': model.data_source.split(':', 1)[1] if model.data_source.startswith('kaggle:') else None
        }
        
        if source_info['is_kaggle_data']:
            source_info['status'] = '[OK] Using real Kaggle startup data'
            source_info['description'] = f"Training on {source_info['dataset_size']} real companies from {source_info['kaggle_dataset']}"
        else:
            source_info['status'] = '[INFO] Using high-quality synthetic data'
            source_info['description'] = f"Training on {source_info['dataset_size']} synthetic companies with realistic patterns"
        
        return jsonify(source_info)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get data source info: {str(e)}'}), 500

@app.route('/api/diagnostics/score-distribution')
def api_score_distribution():
    """Return attractiveness score distribution and tier counts for diagnostics.

    Uses precomputed columns when available; otherwise computes a small sample on the fly
    to keep latency low.
    """
    try:
        import numpy as _np

        if model.sample_data is None or len(model.sample_data) == 0:
            return jsonify({'error': 'No company data available'}), 404

        df = model.sample_data.copy()
        n = len(df)

        # Prefer precomputed scores
        if 'precomputed_attractiveness_score' in df.columns:
            s = df['precomputed_attractiveness_score'].dropna().astype(float)
        else:
            # Compute a capped subset for responsiveness
            subset = df.head(min(400, n))
            vals = []
            for _, row in subset.iterrows():
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
                    analysis = analyze_company_comprehensive(eval_data, precompute_mode=True)
                    vals.append(float(analysis.get('attractiveness_score', 0.0)))
                except Exception:
                    continue
            s = pd.Series(vals, dtype=float)

        if s.empty:
            return jsonify({'error': 'No attractiveness scores available'}), 500

        # Compute tier counts using 3-tier thresholds (aligned with model.py TIER_SCORE_BOUNDS)
        def _tier(x: float) -> str:
            return 'invest' if x >= 65 else ('monitor' if x >= 50 else 'avoid')
        tiers = s.apply(_tier).value_counts().to_dict()
        dist = {
            'count': int(s.count()),
            'mean': float(s.mean()),
            'std': float(s.std(ddof=0)),
            'min': float(s.min()),
            'p25': float(s.quantile(0.25)),
            'p50': float(s.quantile(0.50)),
            'p75': float(s.quantile(0.75)),
            'max': float(s.max()),
        }
        return jsonify({'distribution': dist, 'tiers': tiers, 'total_dataset_rows': n, 'build_id': BUILD_ID})
    except Exception as e:
        return jsonify({'error': f'Failed to compute score distribution: {str(e)}'}), 500

@app.route('/api/diagnostics/coherence-audit')
def api_coherence_audit():
    """Audit coherence between success probability, attractiveness tier, and risk labels.

    Returns counts of contradictory cases, e.g., Avoid tier with very high probability,
    and ensures risk_level matches tier policy when available.
    Query params (optional):
      - max_rows: int, limit rows for responsiveness
      - prob_high: float, threshold for "very high" probability (default 0.85)
    """
    try:
        if model.sample_data is None or len(model.sample_data) == 0:
            return jsonify({'error': 'No company data available'}), 404

        max_rows = request.args.get('max_rows', type=int)
        prob_high = request.args.get('prob_high', default=0.85, type=float)

        df = model.sample_data.copy()
        if isinstance(max_rows, int) and max_rows > 0:
            df = df.head(max_rows)

        total = int(len(df))
        audited = 0
        avoid_high_prob = 0
        risk_mismatch = 0
        invest_low_prob = 0
        monitor_extreme_prob = 0

        samples = []

        for _, row in df.iterrows():
            try:
                cid = str(row.get('company_id', ''))
                # Prefer cached precompute snapshot
                snap = model.ANALYSIS_CACHE.get(cid, {}) if isinstance(model.ANALYSIS_CACHE, dict) else {}
                score = None
                tier = None
                reco = None
                risk = None
                prob = None

                if snap:
                    score = float(snap.get('attractiveness_score', np.nan))
                    tier = str(snap.get('investment_tier', '') or '')
                    reco = str(snap.get('recommendation', '') or '')
                    risk = str(snap.get('risk_level', '') or '')
                    prob = float(snap.get('success_probability', np.nan))
                else:
                    if 'precomputed_attractiveness_score' in row.index and pd.notna(row.get('precomputed_attractiveness_score')):
                        score = float(row.get('precomputed_attractiveness_score'))
                        tier = str(row.get('precomputed_investment_tier', '') or '')
                        risk = str(row.get('precomputed_risk_level', '') or '')
                    # No reliable probability without a live compute; skip prob checks if missing

                if score is None or not np.isfinite(score):
                    continue

                # Normalize tier label into {'invest','monitor','avoid'}
                ts = (tier or '').lower()
                if 'avoid' in ts or 'tier 4' in ts:
                    tn = 'avoid'
                elif 'invest' in ts or 'buy' in ts or 'tier 1' in ts or 'tier 2' in ts:
                    tn = 'invest'
                elif 'monitor' in ts or 'hold' in ts or 'tier 3' in ts:
                    tn = 'monitor'
                else:
                    tn = 'invest' if score >= 65 else ('monitor' if score >= 50 else 'avoid')

                # Risk expected from score policy (aligned with model.py TIER_SCORE_BOUNDS)
                risk_expected = 'Low' if score >= 65 else ('Medium' if score >= 50 else 'High')
                if risk and risk.strip() and risk.strip() != risk_expected:
                    risk_mismatch += 1

                # Probability edge checks when prob is available
                if prob is not None and np.isfinite(prob):
                    bounds = TIER_PROBABILITY_BOUNDS.get(tn, (0.0, 1.0))

                    # Allow caller override for avoid high threshold while keeping policy bounds as floor
                    avoid_upper = min(bounds[1], prob_high) if tn == 'avoid' else bounds[1]

                    if tn == 'avoid' and prob > avoid_upper + COHERENCE_TOLERANCE:
                        avoid_high_prob += 1
                        if len(samples) < 10:
                            samples.append({'company_id': cid, 'tier': tn, 'probability': float(prob), 'score': float(score)})
                    if tn == 'invest' and prob < bounds[0] - COHERENCE_TOLERANCE:
                        invest_low_prob += 1
                    if tn == 'monitor' and (prob < bounds[0] - COHERENCE_TOLERANCE or prob > bounds[1] + COHERENCE_TOLERANCE):
                        monitor_extreme_prob += 1

                audited += 1
            except Exception:
                continue

        return jsonify({
            'audited_rows': audited,
            'total_rows_seen': total,
            'avoid_with_high_probability': avoid_high_prob,
            'invest_with_low_probability': invest_low_prob,
            'monitor_with_extreme_probability': monitor_extreme_prob,
            'risk_label_mismatch': risk_mismatch,
            'samples': samples,
            'build_id': BUILD_ID
        })
    except Exception as e:
        return jsonify({'error': f'Failed coherence audit: {str(e)}'}), 500

@app.route('/api/admin/precompute', methods=['POST'])
def api_admin_precompute():
    """Trigger precomputation of attractiveness scores and tiers and optionally persist to cache.

    Body JSON (all optional):
      - max_rows: int limit for faster runs
      - save_to_disk: bool, default true, save precomputed artifacts to cache
    """
    try:
        payload = request.get_json(silent=True) or {}
        max_rows = payload.get('max_rows')
        save_to_disk = bool(payload.get('save_to_disk', True))

        from model import (
            sample_data,
            precompute_investment_tiers,
            _compute_data_signature,
            _save_precompute_to_cache,
        )

        if sample_data is None or len(sample_data) == 0:
            return jsonify({'error': 'No company data available to precompute'}), 400

        # Run precompute (fast path uses classification only)
        precompute_investment_tiers(
            max_rows=max_rows if isinstance(max_rows, int) else None,
            force_refresh=True
        )

        # Summarize tier counts
        df = sample_data
        counts = {}
        try:
            if 'precomputed_attractiveness_score' in df.columns:
                s = df['precomputed_attractiveness_score'].dropna().astype(float)
                counts = {
                    'total_scored': int(s.count()),
                    'invest': int((s >= 65).sum()),
                    'monitor': int(((s >= 50) & (s < 65)).sum()),
                    'avoid': int((s < 50).sum()),
                }
        except Exception:
            counts = {}

        saved = False
        signature = None
        if save_to_disk:
            try:
                signature = _compute_data_signature(df)
                _save_precompute_to_cache(signature)
                saved = True
            except Exception as _cache_err:
                return jsonify({
                    'warning': f'Precompute completed but cache save failed: {_cache_err}',
                    'counts': counts,
                    'build_id': BUILD_ID
                }), 200

        # Clear filter options cache after precompute
        _FILTER_OPTIONS_CACHE['data'] = None
        _FILTER_OPTIONS_CACHE['timestamp'] = 0

        return jsonify({
            'status': 'ok',
            'counts': counts,
            'saved_to_cache': saved,
            'data_signature': signature,
            'build_id': BUILD_ID
        })
    except Exception as e:
        return jsonify({'error': f'Failed to precompute tiers: {str(e)}'}), 500

@app.route('/api/admin/precompute/status', methods=['GET'])
def api_admin_precompute_status():
    """Check the status of precomputed data availability."""
    try:
        
        if model.sample_data is None or len(model.sample_data) == 0:
            return jsonify({
                'available': False,
                'message': 'No company data loaded',
                'total_companies': 0,
                'precomputed_count': 0
            })
        
        total_companies = len(model.sample_data)
        precomputed_count = 0
        
        if 'precomputed_attractiveness_score' in model.sample_data.columns:
            precomputed_count = int(model.sample_data['precomputed_attractiveness_score'].notna().sum())
        
        available = precomputed_count > 0
        coverage_pct = (precomputed_count / total_companies * 100) if total_companies > 0 else 0
        
        return jsonify({
            'available': available,
            'total_companies': total_companies,
            'precomputed_count': precomputed_count,
            'coverage_percentage': round(coverage_pct, 1),
            'message': f'{precomputed_count}/{total_companies} companies have precomputed scores' if available else 'Precomputed data not available - filtering may be slow'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to check precompute status: {str(e)}'}), 500
    """Clear in-memory analysis cache and optionally delete on-disk model/precompute cache.

    Body JSON (optional):
      - scope: 'precompute' | 'models' | 'all' (currently treated the same for disk)
      - disk: bool, default False. If true, delete files from the model cache directory.
    """
    try:
        payload = request.get_json(silent=True) or {}
        disk = bool(payload.get('disk', False))
        scope = str(payload.get('scope', 'all')).lower()

        from model import _get_model_cache_dir
        
        # Clear in-memory analysis cache
        try:
            model.ANALYSIS_CACHE.clear()
        except Exception:
            pass

        # Drop precomputed columns in-place on the shared DataFrame
        dropped_cols = []
        try:
            if model.sample_data is not None and len(model.sample_data) > 0:
                cols = [
                    'precomputed_attractiveness_score',
                    'precomputed_investment_tier',
                    'precomputed_investment_tier_norm',
                    'precomputed_recommendation',
                    'precomputed_risk_level',
                ]
                existing = [c for c in cols if c in model.sample_data.columns]
                if existing:
                    # In-place drop to mutate the module-global DataFrame instance
                    model.sample_data.drop(columns=existing, inplace=True, errors='ignore')
                    dropped_cols = existing
        except Exception:
            pass

        deleted_files = 0
        cache_dir_path = None
        if disk:
            try:
                from pathlib import Path
                cache_dir = _get_model_cache_dir()
                cache_dir_path = str(cache_dir)
                for p in cache_dir.glob('*'):
                    try:
                        if p.is_file() or p.is_symlink():
                            p.unlink()
                            deleted_files += 1
                        elif p.is_dir():
                            # Shallow delete subdirs
                            for child in p.rglob('*'):
                                try:
                                    if child.is_file() or child.is_symlink():
                                        child.unlink()
                                    else:
                                        try:
                                            child.rmdir()
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                            try:
                                p.rmdir()
                                deleted_files += 1
                            except Exception:
                                pass
                    except Exception:
                        continue
            except Exception as _disk_err:
                return jsonify({
                    'warning': f'Cleared memory caches but disk cache removal failed: {_disk_err}',
                    'dropped_columns': dropped_cols,
                    'deleted_files': deleted_files,
                    'cache_dir': cache_dir_path,
                    'build_id': BUILD_ID
                }), 200

        return jsonify({
            'status': 'ok',
            'dropped_columns': dropped_cols,
            'deleted_files': deleted_files,
            'cache_dir': cache_dir_path,
            'scope': scope,
            'build_id': BUILD_ID
        })
    except Exception as e:
        return jsonify({'error': f'Failed to clear caches: {str(e)}'}), 500

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
        # Access sample_data from model module to get latest reference
        # Basic debug line to confirm code version and inbound tier param
        incoming_tier = request.args.get('tier', '')
        print(f"[API] /api/companies called build={BUILD_ID} tier_raw='{incoming_tier}'")
        
        if model.sample_data is None or len(model.sample_data) == 0:
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
        
        # Start with all companies - use view instead of copy for better performance
        # We'll only copy when we need to modify the DataFrame
        filtered_companies = model.sample_data
        needs_copy = False

        # Guarantee consolidated columns exist for robust filtering regardless of training-time globals
        try:
            if 'industry_group' not in filtered_companies.columns or 'region' not in filtered_companies.columns:
                # Need to add columns, so make a copy first
                if not needs_copy:
                    filtered_companies = model.sample_data.copy()
                    needs_copy = True
                    
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
        
        # Exclude companies missing authoritative funding_total_usd (display requirement)
        try:
            if 'has_funding_total_usd' in filtered_companies.columns:
                before = len(filtered_companies)
                fc = filtered_companies[filtered_companies['has_funding_total_usd'] == True]
                if len(fc) == 0:
                    # Dataset may have missing authoritative flag; degrade gracefully to funding>0 to avoid empty UI
                    print(f"[API] Notice: has_funding_total_usd present but no rows true; falling back to funding_amount_usd>0 (before={before})")
                    if 'funding_amount_usd' in filtered_companies.columns:
                        fc = filtered_companies[filtered_companies['funding_amount_usd'].fillna(0) > 0]
                filtered_companies = fc
            else:
                # Fallback: ensure funding positive
                if 'funding_amount_usd' in filtered_companies.columns:
                    filtered_companies = filtered_companies[filtered_companies['funding_amount_usd'].fillna(0) > 0]
        except Exception as _fund_filter_err:
            print(f"[API] Warning: funding filter failed: {_fund_filter_err}")

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
                # FAST PATH: If precomputed columns exist, filter directly
                if 'precomputed_investment_tier_norm' in filtered_companies.columns:
                    filtered_companies = filtered_companies[filtered_companies['precomputed_investment_tier_norm'] == tier_filter_norm]
                    tier_post_count = len(filtered_companies)
                    tier_applied = True
                    print(f"[API] Precomputed tier filter matched {tier_post_count} rows")
                # FALLBACK: Use attractiveness score thresholds for fast approximation (aligned with model.py)
                elif 'precomputed_attractiveness_score' in filtered_companies.columns:
                    print(f"[API] Using score-based tier approximation (precomputed_investment_tier_norm not available)")
                    score_col = filtered_companies['precomputed_attractiveness_score']
                    if tier_filter_norm == 'invest':
                        filtered_companies = filtered_companies[score_col >= 65]
                    elif tier_filter_norm == 'monitor':
                        filtered_companies = filtered_companies[(score_col >= 50) & (score_col < 65)]
                    else:  # avoid
                        filtered_companies = filtered_companies[score_col < 50]
                    tier_post_count = len(filtered_companies)
                    tier_applied = True
                    print(f"[API] Score-based tier filter matched {tier_post_count} rows")
                else:
                    # NO PRECOMPUTED DATA: Skip tier filtering to avoid massive slowdown
                    print(f"[API] WARNING: No precomputed tier data available - skipping tier filter to maintain performance")
                    print(f"[API] Please run precomputation to enable tier filtering")
                    tier_post_count = initial_len
                    tier_applied = False
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
                    # Use precomputed columns for performance (no fallback computation)
                    if 'precomputed_attractiveness_score' in page_companies.columns:
                        val = company.get('precomputed_attractiveness_score', None)
                        if val is not None and pd.notna(val):
                            company_dict['attractiveness_score'] = float(val)
                        else:
                            # Provide reasonable default instead of computing
                            company_dict['attractiveness_score'] = 50.0
                    else:
                        company_dict['attractiveness_score'] = 50.0
                        
                    if 'precomputed_investment_tier' in page_companies.columns:
                        tier_val = company.get('precomputed_investment_tier', None)
                        if tier_val:
                            company_dict['investment_tier'] = str(tier_val)
                        else:
                            company_dict['investment_tier'] = 'Monitor'
                    else:
                        company_dict['investment_tier'] = 'Monitor'
                        
                    if 'precomputed_recommendation' in page_companies.columns:
                        reco_val = company.get('precomputed_recommendation', None)
                        if reco_val:
                            company_dict['recommendation'] = str(reco_val)
                        else:
                            company_dict['recommendation'] = '🟡 MONITOR - Moderate investment, monitor closely'
                    else:
                        company_dict['recommendation'] = '🟡 MONITOR - Moderate investment, monitor closely'
                        
                    if 'precomputed_risk_level' in page_companies.columns:
                        risk_val = company.get('precomputed_risk_level', None)
                        if risk_val:
                            company_dict['risk_level'] = str(risk_val)
                        else:
                            company_dict['risk_level'] = 'Medium'
                    else:
                        company_dict['risk_level'] = 'Medium'
                except Exception as enrichment_error:
                    print(f"[API] Warning: Failed to enrich company data: {enrichment_error}")
                    # Provide defaults on error
                    company_dict.setdefault('attractiveness_score', 50.0)
                    company_dict.setdefault('investment_tier', 'Monitor')
                    company_dict.setdefault('recommendation', '🟡 MONITOR - Moderate investment, monitor closely')
                    company_dict.setdefault('risk_level', 'Medium')
                companies_list.append(company_dict)
            except Exception as conversion_error:
                print(f"Error converting company data: {conversion_error}")
                print(f"Company data: {company.to_dict()}")
                continue
        
        # Get filter options for frontend using cache
        filter_options = get_cached_filter_options()
        if filter_options is None:
            # Fallback if cache fails
            filter_options = {
                'industries': [],
                'locations': [],
                'funding_rounds': [],
                'statuses': [],
                'industry_groups': [],
                'regions': ['Africa', 'Asia', 'Europe', 'Middle East', 'North America', 'Oceania', 'South America']
            }
        
        response = {
            'companies': companies_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            },
            'filters': filter_options,
            'dataset_info': {
                'data_source': model.data_source,
                'total_companies': len(model.sample_data)
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
        print(f"[INFO] Company detail request for ID: {company_id}")
        
        if model.sample_data is None or len(model.sample_data) == 0:
            print("[ERROR] No sample data available")
            return jsonify({'error': 'No company data available'}), 404
        
        # Find the company
        company_row = model.sample_data[model.sample_data['company_id'] == company_id]
        
        if len(company_row) == 0:
            print(f"[ERROR] Company not found: {company_id}")
            return jsonify({'error': 'Company not found'}), 404
        
        company = company_row.iloc[0] if not company_row.empty else None
        print(f"[OK] Found company: {company.get('company_name', 'Unknown')}")
        
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
            
            print(f"[OK] Company detail response ready with {len(company_detail)} fields")
            return jsonify(company_detail)
            
        except Exception as data_error:  # Handle any errors during data processing
            # Fallback to basic company info if detailed processing fails
            print(f"[WARN] Error processing company detail data: {data_error}")
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
            print(f"[OK] Returning basic company info fallback")
            return jsonify(basic_company)
        
    except Exception as e:  # Handle any errors during the API call
        print(f"[ERROR] Error in company detail endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get company details: {str(e)}'}), 500

def api_company_quick_analyze(company_id):
    """Get quick analysis for a specific company - simplified version"""
    try:
        print(f"[INFO] Quick analysis request for ID: {company_id}")
        
        if model.sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Find the company
        company_row = model.sample_data[model.sample_data['company_id'] == company_id]
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
        
        print(f"[OK] Quick analysis complete: {ml_result.get('attractiveness_score', 0):.1f}% attractiveness")
        return jsonify(analysis)
        
    except Exception as e:
        print(f"[ERROR] Error in quick analysis endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to analyze company: {str(e)}'}), 500

@app.route('/api/companies/compare', methods=['POST'])
def api_companies_compare():
    """Compare multiple companies"""
    try:
        print("[INFO] Company comparison request received")
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        
        if not company_ids:
            return jsonify({'error': 'No company IDs provided'}), 400
        
        print(f"   Comparing {len(company_ids)} companies: {company_ids}")
        
        if model.sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Get detailed data for each company
        companies_data = []
        for company_id in company_ids:
            company_row = model.sample_data[model.sample_data['company_id'] == company_id]
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

        print(f"[OK] Successfully prepared comparison data for {len(companies_data)} companies")

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
        print(f"[ERROR] Error in company comparison endpoint: {e}")
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
            'funding_amount_usd': 0,
            'valuation_usd': 0,
            'team_size': 0,
            'years_since_founding': 0,
            'revenue_usd': 0,
            'num_investors': 0,
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
            
        import numpy as np
        
        if model.sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Find the company
        company_row = model.sample_data[model.sample_data['company_id'] == company_id]
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
        
        # Check if we have precomputed values for this company first (for consistency with list view)
        use_precomputed = False
        precomputed_data = None
        try:
            if 'precomputed_attractiveness_score' in company.index and pd.notna(company.get('precomputed_attractiveness_score')):
                # ALWAYS prioritize precomputed DataFrame columns over cache for consistency with list view
                # Build precomputed data from DataFrame columns (these are the source of truth for the list view)
                precomputed_data = {
                    'attractiveness_score': float(company.get('precomputed_attractiveness_score', 0)),
                }
                if 'precomputed_investment_tier' in company.index:
                    precomputed_data['investment_tier'] = str(company.get('precomputed_investment_tier', 'Monitor'))
                if 'precomputed_recommendation' in company.index:
                    precomputed_data['recommendation'] = str(company.get('precomputed_recommendation', ''))
                if 'precomputed_risk_level' in company.index:
                    precomputed_data['risk_level'] = str(company.get('precomputed_risk_level', 'Medium'))
                # Get component scores if available from columns
                for field in ['market_score', 'team_score', 'financial_score', 'growth_score', 'success_probability']:
                    col_name = f'precomputed_{field}'
                    if col_name in company.index and pd.notna(company.get(col_name)):
                        precomputed_data[field] = float(company.get(col_name))
                use_precomputed = True
                with open('debug_log.txt', 'a') as f:
                    f.write(f"   Using precomputed values from dataset columns for consistency (score={precomputed_data['attractiveness_score']:.2f})\n")
                    f.flush()
        except Exception as pre_err:
            with open('debug_log.txt', 'a') as f:
                f.write(f"   Could not load precomputed data: {pre_err}\n")
                f.flush()
        
        # Run ML evaluation to get comprehensive analysis
        try:
            with open('debug_log.txt', 'a') as f:
                f.write(f"   Calling analyze_company_comprehensive...\n")
                f.flush()
            ml_result = analyze_company_comprehensive(eval_data)
            
            # If we have precomputed data, override the core fields for consistency with list view
            if use_precomputed and precomputed_data:
                with open('debug_log.txt', 'a') as f:
                    f.write(f"   Applying precomputed values to ensure consistency with company list\n")
                    f.flush()
                # Override core scoring fields with precomputed values
                for key in ['attractiveness_score', 'investment_tier', 'recommendation', 'risk_level',
                           'market_score', 'team_score', 'financial_score', 'growth_score', 'success_probability']:
                    if key in precomputed_data:
                        ml_result[key] = precomputed_data[key]
                ml_result['__source'] = 'precomputed_for_consistency'
            
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
        industry_companies = model.sample_data[model.sample_data['industry'] == industry]
        
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
        
        # 3. Feature Contribution Analysis (Pie Chart) - revenue removed
        feature_contribution = {
            'type': 'pie',
            'data': {
                'labels': ['Market Size', 'Team Strength', 'Competition', 'Funding Efficiency', 'Investors'],
                'datasets': [{
                    'data': [24, 22, 18, 18, 18],  # Simulated importance weights without revenue
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
        # Use attractiveness score as proxy for return to avoid exposing probability in UI
        return_score = ml_result['attractiveness_score']
        
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
                    'y': {'title': {'display': True, 'text': 'Attractiveness Score'}}
                },
                'plugins': {
                    'title': {'display': True, 'text': 'Risk-Return Positioning'}
                }
            }
        }
        
        # 6. Business Fundamentals Radar Chart (revenue -> valuation)
        factors = ['Market Size', 'Competition', 'Team Size', 'Valuation', 'Funding']
        scores = [
            min(100, eval_data.get('market_size_billion_usd', 10) * 5),
            100 - eval_data.get('competition_level', 5) * 10,
            min(100, eval_data.get('team_size', 25) * 2),
            min(100, eval_data.get('valuation_usd', 0) / 2000000),
            min(100, eval_data.get('funding_amount_usd', 0) / 200000)
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
        print("[INFO] Company analysis request received")
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        
        if not company_ids:
            return jsonify({'error': 'No company IDs provided'}), 400
        
        print(f"   Analyzing {len(company_ids)} companies: {company_ids}")
        
        if model.sample_data is None:
            return jsonify({'error': 'No company data available'}), 404
        
        # Analyze each company using ML models
        analysis_results = []
        for company_id in company_ids:
            company_row = model.sample_data[model.sample_data['company_id'] == company_id]
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
                # Prefer precomputed cache/columns to ensure consistency with list view
                try:
                    if 'precomputed_attractiveness_score' in company.index and pd.notna(company.get('precomputed_attractiveness_score')):
                        pre_s = float(company.get('precomputed_attractiveness_score'))
                        try:
                            from model import ANALYSIS_CACHE
                            cached = model.ANALYSIS_CACHE.get(str(company_id))
                        except Exception:
                            cached = None
                        if isinstance(cached, dict) and cached:
                            # Merge only core coherence fields; preserve commentary/insights
                            preserve_keys = {'investment_commentary', 'insights'}
                            core_merge_keys = {
                                'attractiveness_score', 'investment_tier', 'recommendation', 'risk_level',
                                'market_score', 'team_score', 'financial_score', 'growth_score', 'success_probability'
                            }
                            for k, v in cached.items():
                                if k in preserve_keys:
                                    continue
                                if k in {'predicted_funding', 'predicted_valuation'} and (v is None):
                                    continue
                                if k in core_merge_keys or k in {'predicted_funding', 'predicted_valuation'}:
                                    ml_result[k] = v
                            ml_result['__source'] = 'precomputed_cache'
                        else:
                            ml_result['attractiveness_score'] = pre_s
                            try:
                                norm = str(company.get('precomputed_investment_tier_norm', '')).lower().strip()
                            except Exception:
                                norm = ''
                            if norm in {'invest', 'monitor', 'avoid'}:
                                ml_result['investment_tier'] = 'Invest' if norm == 'invest' else ('Monitor' if norm == 'monitor' else 'Avoid')
                            else:
                                ml_result['investment_tier'] = 'Invest' if pre_s >= 65 else ('Monitor' if pre_s >= 50 else 'Avoid')
                            if 'precomputed_recommendation' in company.index and isinstance(company.get('precomputed_recommendation'), str):
                                ml_result['recommendation'] = str(company.get('precomputed_recommendation'))
                            if 'precomputed_risk_level' in company.index and isinstance(company.get('precomputed_risk_level'), str):
                                ml_result['risk_level'] = str(company.get('precomputed_risk_level'))
                            ml_result['__source'] = 'precomputed_columns'
                except Exception:
                    pass
                ml_result['company_id'] = company_id
                analysis_results.append(ml_result)

        print(f"[OK] Successfully analyzed {len(analysis_results)} companies")
        
        return jsonify({
            'analysis_results': analysis_results,
            'summary': {
                'total_analyzed': len(analysis_results),
                'avg_attractiveness': sum(r['attractiveness_score'] for r in analysis_results) / len(analysis_results) if analysis_results else 0,
                'recommended_count': len([r for r in analysis_results if r['attractiveness_score'] >= 65])
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Error in company analysis endpoint: {e}")
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
    # Check if we're in development mode
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("Starting Deal Scout Web Application")
    print("=" * 50)
    print(f"ML Models: Loaded and ready")
    print(f"Web Interface: http://localhost:5000")
    print(f"API Endpoints: /api/companies")
    print(f"Debug Mode: {debug_mode}")
    print("=" * 50)
    
    # Auto-precompute on startup if not already available
    def ensure_precomputed_data():
        """Ensure precomputed data is available before serving requests"""
        try:
            import time
            # Wait for background training to potentially complete and run its auto-precompute
            print("🔄 Waiting for background training to complete...")
            time.sleep(10)  # Give background thread time to finish
            
            # Check if precomputed data exists
            if model.sample_data is not None and len(model.sample_data) > 0:
                has_precomputed = 'precomputed_attractiveness_score' in model.sample_data.columns
                if has_precomputed:
                    non_null_count = model.sample_data['precomputed_attractiveness_score'].notna().sum()
                    if non_null_count > 0:
                        print(f"✅ Precomputed data available: {non_null_count} / {len(model.sample_data)} companies")
                        return
                
                # Precomputed data not available, trigger it now
                print("⚠️  Precomputed data not found. Auto-triggering precomputation...")
                from model import precompute_investment_tiers
                
                try:
                    precompute_investment_tiers(max_rows=400)  # Limit to 400 for faster startup
                    # Check if precomputation succeeded by looking at the data
                    if 'precomputed_attractiveness_score' in model.sample_data.columns:
                        non_null_count = model.sample_data['precomputed_attractiveness_score'].notna().sum()
                        if non_null_count > 0:
                            print(f"✅ Auto-precompute completed: {non_null_count} companies scored")
                            # Count tiers
                            if 'precomputed_investment_tier' in model.sample_data.columns:
                                tier_counts = model.sample_data['precomputed_investment_tier'].value_counts()
                                invest_ct = tier_counts.get('Invest', 0)
                                monitor_ct = tier_counts.get('Monitor', 0)
                                avoid_ct = tier_counts.get('Avoid', 0)
                                print(f"   🟢 Invest: {invest_ct}, 🟡 Monitor: {monitor_ct}, 🔴 Avoid: {avoid_ct}")
                        else:
                            print("⚠️  Auto-precompute completed but no scores generated")
                    else:
                        print("⚠️  Auto-precompute completed but column not found")
                except Exception as precomp_err:
                    print(f"⚠️  Auto-precompute failed: {precomp_err}")
                    print("   Scores may show as 50% until manually triggered via /api/admin/precompute")
        except Exception as e:
            print(f"⚠️  Error in auto-precompute: {e}")
            print("   Scores may show as 50% until manually triggered via /api/admin/precompute")
    
    # Run precompute check in a separate thread to not block server startup
    import threading
    precompute_thread = threading.Thread(target=ensure_precomputed_data, daemon=True)
    precompute_thread.start()
    
    # Run the Flask app with error handling
    try:
        app.run(
            debug=True,  # Enable debug mode to force template reloading
            host='0.0.0.0',  # Listen on all interfaces
            port=5000,
            threaded=True,
            use_reloader=False  # Disable auto-reloader to prevent crashes
        )
    except KeyboardInterrupt:
        print("\n[STOP] Flask application stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error running Flask application: {e}")
        import traceback
        traceback.print_exc()