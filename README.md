# 📊 Stock Market Anomaly Detection

A real-time stock market anomaly detection system that identifies unusual trading patterns using statistical analysis. Built with Flask, Polygon.io API, and deployed on Railway.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Features

- **Real-time Anomaly Detection**: Identifies unusual trading activity using Z-score analysis
- **Interactive Dashboard**: Beautiful web interface with real-time charts
- **Automated Data Collection**: Daily scheduled jobs to fetch and analyze market data
- **Historical Analysis**: View 30-day trading patterns and price movements
- **Configurable Thresholds**: Customize detection sensitivity
- **RESTful API**: Full API access for programmatic integration

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Polygon.io API key](https://polygon.io/) (Stocks paid plan)
- Railway account (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/anomalies.git
   cd anomalies
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your POLYGON_API_KEY
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Visit** `http://localhost:8888`

## 🚂 Railway Deployment

### Option 1: Using Railway CLI

```bash
# Login to Railway
railway login

# Initialize project (already done)
railway init --name anomalies

# Add PostgreSQL database
railway add
# Select: Database → PostgreSQL

# Set environment variables
railway variables set POLYGON_API_KEY=your_api_key_here
railway variables set FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Deploy
railway up

# Generate domain
railway domain

# Initialize database
railway run python init_db.py
```

### Option 2: Using Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app)
2. Create new project from GitHub repo
3. Add PostgreSQL database
4. Set environment variables (see `.env.example`)
5. Deploy automatically

See [SETUP.md](SETUP.md) for detailed instructions.

## 📖 How It Works

### Anomaly Detection Algorithm

1. **Data Collection**: Fetches daily market aggregates from Polygon.io
2. **Baseline Calculation**: Computes rolling averages and standard deviations
3. **Z-Score Analysis**: Identifies outliers using statistical thresholds
4. **Visualization**: Displays anomalies with interactive charts

### Z-Score Formula

```
Z-Score = (Current Trades - Average Trades) / Standard Deviation
```

A Z-score > 3.0 indicates trading activity more than 3 standard deviations above normal, suggesting unusual market behavior.

## 🔧 Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `POLYGON_API_KEY` | Your Polygon.io API key | Required |
| `DATABASE_URL` | Database connection string | Auto-set by Railway |
| `LOOKBACK_DAYS` | Days for rolling average | 5 |
| `Z_SCORE_THRESHOLD` | Minimum Z-score for anomaly | 3.0 |
| `EOD_SCHEDULE_TIME` | Daily job time (HH:MM ET) | 16:30 |

## 📡 API Endpoints

- `GET /api/anomalies` - Get anomalies for a date
- `GET /api/anomalies/dates` - List dates with anomalies
- `GET /api/ticker/<ticker>` - Get ticker details
- `GET /api/ticker/<ticker>/intraday` - Get intraday data
- `GET /api/stats` - Get system statistics
- `POST /api/backfill` - Backfill historical data
- `POST /api/run-eod` - Trigger end-of-day job
- `GET /health` - Health check

## 🏗️ Project Structure

```
anomalies/
├── app.py                 # Flask application & routes
├── config.py             # Configuration management
├── database.py           # SQLAlchemy models
├── data_fetcher.py       # Polygon.io API integration
├── anomaly_detector.py   # Detection algorithm
├── scheduler.py          # Scheduled jobs
├── init_db.py           # Database initialization
├── requirements.txt      # Python dependencies
├── Procfile             # Railway deployment config
├── railway.json         # Railway settings
├── templates/           # HTML templates
│   └── index.html
└── static/             # CSS & JavaScript
    ├── css/style.css
    └── js/app.js
```

## 🎨 Screenshots

### Main Dashboard
View detected anomalies with key metrics and filters.

### Ticker Details
Interactive charts showing 30-day trading volume and price history.

## 🔍 Example Anomalies

Recent examples of detected anomalies:

- **VTAK** (2024-10-18): 460,548 trades vs 6,291 avg → +106.49% price change
- **PEGY** (2024-10-18): 387,360 trades vs 15,769 avg → +47.91% price change
- **NFLX** (2024-10-18): 378,687 trades vs 125,174 avg → +11.09% price change

## 🛠️ Development

### Running Tests

```bash
# Test database
python init_db.py

# Test data fetching
python -c "from data_fetcher import DataFetcher; DataFetcher().fetch_daily_aggregates('2024-10-25')"

# Test anomaly detection
python -c "from anomaly_detector import AnomalyDetector; AnomalyDetector().detect_anomalies('2024-10-25')"
```

### Backfilling Data

```bash
# Via Python
python -c "from data_fetcher import DataFetcher; DataFetcher().backfill_data(30)"

# Via API
curl -X POST http://localhost:8888/api/backfill -H "Content-Type: application/json" -d '{"days": 30}'
```

## 📚 Resources

- [Polygon.io Blog Post](https://polygon.io/blog/hunting-anomalies-in-the-stock-market) - Original tutorial
- [Polygon.io API Docs](https://polygon.io/docs) - API documentation
- [Railway Docs](https://docs.railway.app) - Deployment guide

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. It is not financial advice. Trading stocks involves risk, and you should do your own research before making any investment decisions.

## 🙏 Credits

Based on the tutorial [Hunting Anomalies in the Stock Market](https://polygon.io/blog/hunting-anomalies-in-the-stock-market) by Polygon.io.

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

Made with ❤️ using Flask, Polygon.io, and Railway

