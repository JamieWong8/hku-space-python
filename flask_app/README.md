# Startup Deal Evaluator Flask Web Application

## 🚀 Quick Start

This directory contains the Flask web application version of the Startup Deal Evaluator, converted from the Jupyter notebook.

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation & Running

#### Option 1: Automated Setup (Recommended)
```powershell
# Navigate to the flask_app directory
cd flask_app

# Run the automated setup script
.\run_web_app.ps1
```

#### Option 2: Manual Setup
```powershell
# Navigate to the flask_app directory
cd flask_app

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Accessing the Application

Once started, the web application will be available at:
- **Main Interface:** http://localhost:5000
- **API Endpoint:** http://localhost:5000/api/evaluate
- **Health Check:** http://localhost:5000/health

## 🌟 Features

### Web Interface
- **Interactive Dashboard:** Professional Bootstrap-based UI
- **Real-time Evaluation:** Instant startup analysis with sliders and forms
- **Visual Analytics:** Comprehensive 6-panel analysis dashboard
- **Example Library:** Pre-loaded startup scenarios for testing
- **Responsive Design:** Works on desktop, tablet, and mobile

### API Endpoints
- `POST /api/evaluate` - Evaluate startup deals
- `GET /api/examples` - Get example startup data
- `GET /api/visualizations/<id>` - Generate analysis charts
- `GET /api/market-data` - Market analysis data
- `GET /health` - Application health check

### Machine Learning
- **Random Forest Models:** 99.4% accuracy classification and regression
- **56+ Features:** Comprehensive feature engineering pipeline
- **Real-time Predictions:** Instant success probability and funding predictions
- **Risk Assessment:** Automated investment recommendations

## 📁 Project Structure

```
flask_app/
├── app.py                  # Main Flask application
├── model.py               # ML models and data processing
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker containerization
├── run_web_app.ps1       # Automated setup script
├── templates/
│   ├── index.html        # Main web interface
│   └── error.html        # Error page template
└── static/
    ├── css/             # Custom stylesheets
    ├── js/              # JavaScript files
    └── images/          # Static images
```

## 🔧 Configuration

### Environment Variables
- `FLASK_APP=app.py` - Flask application entry point
- `FLASK_ENV=development` - Development mode (set to `production` for deployment)

### Customization
- Modify `model.py` to update ML algorithms or add new features
- Edit `templates/index.html` to customize the user interface
- Update `app.py` to add new API endpoints or modify routing

## 🚀 Deployment Options

### Local Development
```powershell
python app.py
```

### Docker Deployment
```powershell
# Build Docker image
docker build -t startup-evaluator-web .

# Run container
docker run -p 5000:5000 startup-evaluator-web
```

### Production Deployment
```powershell
# Using Gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Waitress (Windows-friendly)
pip install waitress
waitress-serve --port=5000 app:app
```

### Cloud Deployment
The application is ready for deployment on:
- **Heroku:** Push to Heroku with included Dockerfile
- **AWS ECS/Fargate:** Use Docker container
- **Google Cloud Run:** Deploy with Cloud Build
- **Azure Container Instances:** Deploy Docker image

## 📊 API Usage Examples

### Evaluate Startup Deal
```javascript
fetch('/api/evaluate', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        company_name: 'TechCorp',
        industry: 'SaaS',
        location: 'San Francisco',
        funding_round: 'Series A',
        funding_amount_usd: 5000000,
        valuation_usd: 75000000,
        team_size: 25,
        years_since_founding: 2.0,
        revenue_usd: 500000,
        num_investors: 3,
        competition_level: 5,
        market_size_billion_usd: 10.0
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Response Format
```json
{
    "company_name": "TechCorp",
    "attractiveness_score": 65.4,
    "success_probability": 0.743,
    "predicted_funding": 4850000,
    "recommendation": "🟡 BUY - Good investment with manageable risks",
    "insights": [
        "Above-average success probability with solid business foundation",
        "Conservative funding request - good value opportunity",
        "Large addressable market with manageable competition"
    ],
    "risk_level": "Medium",
    "investment_tier": "Tier 2",
    "timestamp": "2025-09-20T15:30:45"
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```powershell
   # Change port in app.py or kill existing process
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

2. **Missing dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Memory issues with large datasets:**
   - Reduce model complexity in `model.py`
   - Limit concurrent requests
   - Use production WSGI server

4. **Visualization errors:**
   - Ensure matplotlib backend is set to 'Agg'
   - Check memory usage for chart generation
   - Verify image paths and permissions

### Performance Optimization

1. **Model Caching:** Models are loaded once at startup
2. **Image Optimization:** Charts are generated on-demand
3. **Request Handling:** Async processing for better concurrency
4. **Memory Management:** Automatic cleanup of matplotlib figures

## 📈 Monitoring & Logging

### Health Monitoring
```powershell
# Check application health
curl http://localhost:5000/health
```

### Performance Metrics
- Response time tracking in Flask logs
- Model prediction latency monitoring
- Memory usage tracking for chart generation

## 🔐 Security Considerations

### Production Security
- Set `FLASK_ENV=production` for production deployment
- Use HTTPS in production environments
- Implement rate limiting for API endpoints
- Validate and sanitize all input data
- Use secure session management

### Data Privacy
- All processing happens locally/server-side
- No external data transmission
- Configurable data retention policies
- Secure API key management for external services

## 🤝 Contributing

To contribute to the Flask web application:

1. Make changes to the Flask app files
2. Test locally using `python app.py`
3. Update documentation if needed
4. Submit pull request with changes

## 📞 Support

For issues specific to the Flask web application:
- Check the application logs in the terminal
- Verify all dependencies are installed correctly
- Ensure Python version compatibility (3.8+)
- Test API endpoints using the `/health` endpoint

---

**🎉 Your Startup Deal Evaluator is now accessible as a professional web application!**