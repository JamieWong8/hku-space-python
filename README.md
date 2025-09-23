# 🚀 Startup Deal Evaluator

A comprehensive machine learning application for investment firms to evaluate startup deals using predictive analytics and interactive visualizations. **Now available as both Jupyter notebook and professional Flask web application!**

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-web--app-blue.svg)
![Jupyter](https://img.shields.io/badge/jupyter-notebook-orange.svg)
![Kaggle](https://img.shields.io/badge/kaggle-data--integration-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-machine--learning-red.svg)

## 🎯 Overview

This project provides investment firms with a powerful tool to evaluate startup investment opportunities using machine learning. Available as both a Jupyter notebook for analysis and a **production-ready Flask web application** for real-time deal evaluation.

## ✨ Features

### 🌐 Flask Web Application (NEW!)
- **Professional Web Interface**: Bootstrap-based responsive UI at http://localhost:5000
- **Real-time API**: RESTful endpoints for deal evaluation and data integration  
- **Kaggle Integration**: Optional real startup data from Kaggle datasets
- **Interactive Dashboard**: Live charts and visualizations
- **Example Companies**: Pre-loaded startup profiles for testing
- **Data Source Flexibility**: Synthetic data by default, real data with Kaggle credentials

### 🤖 Machine Learning Models
- **Random Forest Classification**: Predicts startup success probability (98% accuracy)
- **Random Forest Regression**: Estimates appropriate funding amounts (99% R² score)
- **Feature Engineering**: Creates 56+ engineered features from raw startup data
- **Cross-validation**: Robust model validation with statistical confidence

### 📊 Interactive Analytics
- **Real-time Deal Evaluation**: Input startup details and get instant ML predictions
- **Investment Recommendations**: Clear buy/hold/avoid guidance based on quantitative analysis
- **Visual Analytics**: 6-panel comprehensive analysis dashboard
- **Industry Benchmarking**: Compare startups against industry averages
- **Risk-Return Positioning**: Visualize investment opportunities in risk-return space

## 📁 Project Structure

```
startup-deal-evaluator/
├── startup_deal_evaluator.ipynb    # Original Jupyter notebook
├── flask_app/                      # Production Flask web application
│   ├── app.py                      # Main Flask application
│   ├── model.py                    # ML models and data processing
│   ├── templates/                  # HTML templates
│   ├── static/                     # CSS, JS, images
│   ├── requirements.txt            # Flask app dependencies
│   └── Dockerfile                  # Container deployment
├── requirements.txt                 # Notebook dependencies
├── KAGGLE_INTEGRATION_GUIDE.md     # Kaggle setup instructions
├── DEPLOYMENT_GUIDE.md             # Flask deployment guide
└── docs/                           # Additional documentation
    ├── user_guide.md               # Detailed user guide
    └── technical_specs.md          # Technical specifications
```

## 🚀 Quick Start

### Option 1: Flask Web Application (Recommended)
```bash
# Navigate to Flask app
cd flask_app

# Install dependencies  
pip install -r requirements.txt

# Run the web application
python app.py

# Open browser to http://localhost:5000
```

### Option 2: Jupyter Notebook
```bash
# Install dependencies
pip install -r requirements.txt

# Start Jupyter
jupyter notebook startup_deal_evaluator.ipynb
```

### Prerequisites
- Python 3.8 or higher
- Jupyter Notebook or JupyterLab
- Git (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/startup-deal-evaluator.git
   cd startup-deal-evaluator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch Jupyter Notebook**
   ```bash
   jupyter notebook startup_deal_evaluator.ipynb
   ```

4. **Run all cells**
   - Execute all cells from top to bottom to set up the environment
   - The system will automatically generate synthetic data for demonstration

### Using Real Data (Optional)

To use real startup datasets from Kaggle:

1. Create a Kaggle account and generate API credentials
2. Place your `kaggle.json` file in `~/.kaggle/` directory
3. The notebook will automatically download real datasets when available

## 🎮 Usage

### Interactive Dashboard

1. **Run the notebook**: Execute all cells to initialize the ML models
2. **Navigate to Section K**: Find the interactive dashboard
3. **Input startup details**:
   - Industry and location
   - Funding round and team size
   - Financial metrics (funding, revenue, market size)
   - Competition level and investor count
4. **Click "Evaluate Deal"**: Get instant ML-powered insights
5. **Review results**: Analyze the attractiveness score, success probability, and visualizations

### Example Evaluation

```python
# Example: Evaluate a FinTech startup
evaluation = evaluate_startup_deal(
    industry='Fintech',
    location='San Francisco',
    funding_round='Series A',
    team_size=45,
    years_founded=2.5,
    funding_amount=8_000_000,
    revenue=1_500_000,
    market_size=25.0,
    competition_level=7,
    num_investors=4
)

print(f"Attractiveness Score: {evaluation['attractiveness_score']:.1f}/100")
print(f"Success Probability: {evaluation['success_probability']:.1%}")
```

## � Kaggle Integration

The Flask web application supports real startup data from Kaggle for enhanced accuracy:

### Data Sources
- **Synthetic Data** (Default): High-quality generated data with realistic patterns
- **Kaggle Data** (Optional): Real startup datasets with actual outcomes

### Setup Kaggle (Optional)
1. Get Kaggle API credentials from [kaggle.com/account](https://www.kaggle.com/account)
2. Place `kaggle.json` in `~/.kaggle/` or the flask_app directory
3. Restart the Flask app - it will automatically detect and use real data

### Supported Datasets
- peopleanalytics1/startup-success-prediction
- yagnesh97/startup-dataset  
- justinas/startup-investments
- hossaingh/startup-company-data

**See `KAGGLE_INTEGRATION_GUIDE.md` for detailed setup instructions.**

## �📊 Model Performance

| Model | Metric | Score |
|-------|--------|-------|
| Classification | Accuracy | 98-99% |
| Classification | Precision | 99-100% |
| Classification | Recall | 97-98% |
| Classification | AUC-ROC | 99-100% |
| Regression | R² Score | 99% |
| Regression | RMSE | $4.2M |
| Regression | MAE | $1.7M |

*Performance varies slightly between synthetic and real Kaggle data*

## 🔧 Key Success Factors

The ML models identify these critical factors for startup success:

1. **Operating Status** (43% importance) - Current operational state
2. **Company Closure** (11% importance) - Risk indicators
3. **IPO Potential** (10% importance) - Exit opportunity indicators
4. **Funding Amount** (3% importance) - Capital availability
5. **Company Age** (2.5% importance) - Maturity and experience

## 🎨 Visualizations

The system provides comprehensive visualizations including:

- **Deal Attractiveness Gauge**: 0-100 scoring with risk categories
- **Success Probability Charts**: Comparison with industry benchmarks
- **Feature Contribution Analysis**: Understanding model decisions
- **Industry Landscape Mapping**: Competitive positioning
- **Risk-Return Quadrants**: Investment opportunity classification
- **Market Factor Analysis**: Business fundamentals assessment

## 🔄 Customization

### Adding New Industries
```python
# Update the synthetic data generator
industries = ['Fintech', 'Healthcare', 'Your New Industry']
```

### Adjusting Scoring Weights
```python
# Modify the attractiveness score calculation
attractiveness_score = (
    success_probability * 40 +      # Success weight (40%)
    revenue_factor * 20 +           # Revenue weight (20%)
    market_opportunity * 20 +       # Market weight (20%)
    team_factor * 10 +              # Team weight (10%)
    investor_interest * 10          # Investor weight (10%)
)
```

### Model Hyperparameters
```python
# Tune Random Forest parameters
rf_classifier = RandomForestClassifier(
    n_estimators=100,    # Number of trees
    max_depth=10,        # Maximum tree depth
    min_samples_split=5, # Minimum samples to split
    random_state=42
)
```

## 📈 Use Cases

### For Investment Firms
- **Deal Screening**: Quickly evaluate multiple startup opportunities
- **Risk Assessment**: Understand key risk factors and mitigation strategies
- **Portfolio Optimization**: Compare deals across industries and stages

### For Startup Accelerators
- **Application Review**: Streamline startup selection process
- **Mentorship Focus**: Identify areas where startups need support
- **Success Prediction**: Allocate resources to highest-potential companies

### For Entrepreneurs
- **Self-Assessment**: Understand how investors might evaluate your startup
- **Improvement Areas**: Identify factors to increase investor attractiveness
- **Market Positioning**: Compare against industry benchmarks

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Scikit-learn** for machine learning capabilities
- **Pandas** for data manipulation and analysis
- **Matplotlib & Seaborn** for data visualization
- **Jupyter** for the interactive notebook environment
- **IPywidgets** for interactive dashboard components

## 📞 Support

If you have any questions or need support:

1. Check the [User Guide](docs/user_guide.md) for detailed instructions
2. Review the [Technical Specifications](docs/technical_specs.md) for implementation details
3. Open an issue on GitHub for bug reports or feature requests

## 🔮 Future Enhancements

- [ ] Real-time data integration with startup databases
- [ ] Sector-specific evaluation models
- [ ] Advanced ensemble methods for improved accuracy
- [ ] Web application deployment
- [ ] API endpoints for programmatic access
- [ ] Enhanced visualization with interactive plots
- [ ] Multi-language support
- [ ] Integration with investment management platforms

---

**⭐ If you find this project useful, please consider giving it a star on GitHub!**