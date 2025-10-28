# Stock Market Anomaly Detection - Setup Guide

This application detects short-lived statistical anomalies in stock market data using the Polygon.io API.

## Features

- 📊 Real-time anomaly detection using Z-score analysis
- 📈 Interactive web dashboard with charts
- 🔄 Automated daily data fetching and analysis
- 📉 Historical data visualization
- 🎯 Configurable detection thresholds

## Prerequisites

- Python 3.11+
- Polygon.io API key (Stocks paid plan required for grouped daily aggregates)
- PostgreSQL database (for production) or SQLite (for local development)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd anomalies
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Polygon.io API key:

```
POLYGON_API_KEY=your_actual_api_key_here
FLASK_SECRET_KEY=generate_a_random_secret_key
```

### 5. Initialize Database

```bash
python init_db.py
```

### 6. Backfill Historical Data (Optional)

To populate the database with historical data:

```python
from data_fetcher import DataFetcher
from anomaly_detector import AnomalyDetector

# Fetch last 30 days of data
fetcher = DataFetcher()
fetcher.backfill_data(days=30)

# Build lookup table
detector = AnomalyDetector()
detector.build_lookup_table()
```

Or use the API endpoint:

```bash
curl -X POST http://localhost:8888/api/backfill -H "Content-Type: application/json" -d '{"days": 30}'
```

### 7. Run the Application

```bash
python app.py
```

Visit `http://localhost:8888` in your browser.

## Railway Deployment

### 1. Prerequisites

- Railway account (https://railway.app)
- GitHub repository with your code
- Polygon.io API key

### 2. Deploy to Railway

1. **Create New Project**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository

2. **Add PostgreSQL Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically provide `DATABASE_URL`

3. **Configure Environment Variables**
   
   In Railway project settings, add these variables:
   
   ```
   POLYGON_API_KEY=your_polygon_api_key_here
   FLASK_SECRET_KEY=generate_a_random_secret_key
   EOD_SCHEDULE_TIME=16:30
   TIMEZONE=America/New_York
   LOOKBACK_DAYS=5
   Z_SCORE_THRESHOLD=3.0
   PORT=8888
   ```

4. **Deploy**
   - Railway will automatically detect the `Procfile` and deploy
   - Wait for deployment to complete
   - Click on the generated URL to access your app

### 3. Initialize Database on Railway

After deployment, initialize the database:

```bash
# Using Railway CLI
railway run python init_db.py

# Or trigger via API
curl -X POST https://your-app.railway.app/api/backfill -H "Content-Type: application/json" -d '{"days": 30}'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POLYGON_API_KEY` | Your Polygon.io API key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///anomalies.db` |
| `FLASK_SECRET_KEY` | Flask session secret | Required |
| `PORT` | Application port | `8888` |
| `EOD_SCHEDULE_TIME` | Daily job time (HH:MM) | `16:30` |
| `TIMEZONE` | Timezone for scheduling | `America/New_York` |
| `LOOKBACK_DAYS` | Days for rolling average | `5` |
| `Z_SCORE_THRESHOLD` | Minimum Z-score for anomaly | `3.0` |

### Anomaly Detection Parameters

- **Lookback Days**: Number of days to calculate rolling average (default: 5)
- **Z-Score Threshold**: Minimum Z-score to flag as anomaly (default: 3.0)
  - Higher values = fewer, more extreme anomalies
  - Lower values = more anomalies detected

## API Endpoints

### GET `/api/anomalies`
Get anomalies for a specific date

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format
- `min_z_score` (optional): Minimum Z-score filter

**Response:**
```json
{
  "date": "2024-10-28",
  "count": 15,
  "anomalies": [...]
}
```

### GET `/api/anomalies/dates`
Get list of dates with detected anomalies

### GET `/api/ticker/<ticker>`
Get detailed information for a specific ticker

**Query Parameters:**
- `date` (required): Date in YYYY-MM-DD format

### GET `/api/ticker/<ticker>/intraday`
Get intraday data for a specific ticker and date

### GET `/api/stats`
Get overall statistics

### POST `/api/run-eod`
Manually trigger end-of-day job

### POST `/api/backfill`
Backfill historical data

**Body:**
```json
{
  "days": 30
}
```

### GET `/health`
Health check endpoint

## How It Works

1. **Data Collection**: Daily aggregates are fetched from Polygon.io API
2. **Baseline Calculation**: Rolling averages and standard deviations are computed for each ticker
3. **Anomaly Detection**: Z-scores are calculated to identify unusual trading activity
4. **Visualization**: Web interface displays anomalies with interactive charts

### Z-Score Calculation

```
Z-Score = (Current Trades - Average Trades) / Standard Deviation
```

A Z-score > 3.0 indicates the number of trades is more than 3 standard deviations above the average, suggesting unusual activity.

## Scheduled Jobs

The application runs an end-of-day job at the configured time (default: 4:30 PM ET) to:

1. Fetch previous day's market data
2. Update lookup table with rolling statistics
3. Detect and store anomalies
4. Log top anomalies

## Troubleshooting

### Database Connection Issues

If using PostgreSQL on Railway, ensure the `DATABASE_URL` is properly set. Railway provides this automatically.

### API Rate Limits

Polygon.io has rate limits based on your plan:
- Free tier: 5 requests/minute
- Paid plans: Higher limits

The backfill function includes rate limiting delays.

### No Anomalies Detected

- Ensure data has been backfilled for at least `LOOKBACK_DAYS`
- Try lowering `Z_SCORE_THRESHOLD`
- Check that market data is available for the date

## Development

### Project Structure

```
anomalies/
├── app.py                 # Flask application
├── config.py             # Configuration
├── database.py           # Database models
├── data_fetcher.py       # Polygon.io data fetching
├── anomaly_detector.py   # Anomaly detection logic
├── scheduler.py          # Scheduled jobs
├── init_db.py           # Database initialization
├── requirements.txt      # Python dependencies
├── Procfile             # Railway/Heroku deployment
├── runtime.txt          # Python version
├── railway.json         # Railway configuration
├── templates/           # HTML templates
│   └── index.html
└── static/             # Static assets
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

### Running Tests

```bash
# Test database connection
python init_db.py

# Test data fetching
python -c "from data_fetcher import DataFetcher; DataFetcher().fetch_daily_aggregates('2024-10-25')"

# Test anomaly detection
python -c "from anomaly_detector import AnomalyDetector; AnomalyDetector().detect_anomalies('2024-10-25')"
```

## Credits

Based on the tutorial: [Hunting Anomalies in the Stock Market](https://polygon.io/blog/hunting-anomalies-in-the-stock-market)

## License

MIT License - See LICENSE file for details

