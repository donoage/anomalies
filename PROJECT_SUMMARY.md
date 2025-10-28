# 📊 Anomalies Project - Setup Complete!

## ✅ What's Been Set Up

### 1. **Local Development Environment**
- ✅ Git repository initialized
- ✅ All source code organized and modularized
- ✅ Configuration files created
- ✅ Environment variables template (`.env.example`)

### 2. **GitHub Repository**
- ✅ Repository created: **https://github.com/donoage/anomalies**
- ✅ Initial commit pushed
- ✅ Comprehensive README.md
- ✅ Setup documentation (SETUP.md)
- ✅ Deployment guide (DEPLOYMENT_STEPS.md)

### 3. **Railway Project**
- ✅ Project created: **https://railway.com/project/cbfff9ab-b927-47fb-bfed-0fd2723089aa**
- ✅ Deployment configuration (`Procfile`, `railway.json`)
- ✅ Docker configuration (`.dockerignore`)
- ✅ Runtime specification (`runtime.txt`)

### 4. **Application Features**
- ✅ Flask web application with modern UI
- ✅ Polygon.io API integration (unlimited plan - no rate limiting)
- ✅ Z-score based anomaly detection
- ✅ PostgreSQL/SQLite database support
- ✅ Automated daily scheduling (EOD jobs)
- ✅ RESTful API endpoints
- ✅ Interactive charts (Chart.js)
- ✅ Responsive design

### 5. **Helper Scripts**
- ✅ `setup_railway.sh` - Railway setup guide
- ✅ `railway_helper.sh` - Quick Railway commands
- ✅ `init_db.py` - Database initialization

## 🎯 Next Steps (Manual Actions Required)

Since Railway CLI requires interactive mode for some operations, complete these steps via the Railway dashboard:

### Step 1: Add PostgreSQL Database
1. Visit: https://railway.com/project/cbfff9ab-b927-47fb-bfed-0fd2723089aa
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**

### Step 2: Connect GitHub Repository
1. Click **"+ New"** → **"GitHub Repo"**
2. Select **"donoage/anomalies"**
3. Railway will auto-detect configuration and deploy

### Step 3: Set Environment Variables
In Railway project → Variables, add:
```
POLYGON_API_KEY=your_actual_polygon_api_key
FLASK_SECRET_KEY=<generate with: openssl rand -hex 32>
EOD_SCHEDULE_TIME=16:30
TIMEZONE=America/New_York
LOOKBACK_DAYS=5
Z_SCORE_THRESHOLD=3.0
```

### Step 4: Generate Domain
Click **"Generate Domain"** in your service settings

### Step 5: Initialize & Populate Database
```bash
# Initialize database tables
railway run python init_db.py

# Backfill 30 days of historical data
railway run python -c "from data_fetcher import DataFetcher; DataFetcher().backfill_data(30)"

# Build lookup table
railway run python -c "from anomaly_detector import AnomalyDetector; AnomalyDetector().build_lookup_table()"
```

## 🚀 Quick Start Commands

### Using Railway Helper Script
```bash
cd /Users/stephenbae/Projects/anomalies

# View all available commands
./railway_helper.sh help

# Check project status
./railway_helper.sh status

# View logs
./railway_helper.sh logs

# Open dashboard
./railway_helper.sh open

# Deploy
./railway_helper.sh deploy

# Initialize database
./railway_helper.sh initdb

# Backfill data
./railway_helper.sh backfill
```

### Direct Railway Commands
```bash
cd /Users/stephenbae/Projects/anomalies

# Open Railway dashboard
railway open

# View project status
railway status

# View logs
railway logs

# Deploy
railway up

# Run commands
railway run <command>
```

## 📁 Project Structure

```
anomalies/
├── app.py                    # Main Flask application
├── config.py                 # Configuration management
├── database.py              # SQLAlchemy models (Anomaly, DailyAggregate, LookupTable)
├── data_fetcher.py          # Polygon.io API integration (no rate limiting)
├── anomaly_detector.py      # Z-score detection algorithm
├── scheduler.py             # EOD scheduled jobs (4:30 PM ET)
├── init_db.py              # Database initialization script
├── requirements.txt         # Python dependencies
├── Procfile                # Railway/Heroku deployment
├── railway.json            # Railway configuration
├── runtime.txt             # Python 3.11.9
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── .dockerignore           # Docker ignore rules
├── README.md               # Project documentation
├── SETUP.md                # Detailed setup guide
├── DEPLOYMENT_STEPS.md     # Step-by-step deployment
├── PROJECT_SUMMARY.md      # This file
├── setup_railway.sh        # Railway setup script
├── railway_helper.sh       # Railway helper commands
├── templates/
│   └── index.html         # Main dashboard UI
└── static/
    ├── css/
    │   └── style.css      # Modern gradient design
    └── js/
        └── app.js         # Interactive charts & API calls
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Value |
|----------|-------------|-------|
| `POLYGON_API_KEY` | Polygon.io API key | Your unlimited plan key |
| `DATABASE_URL` | Database connection | Auto-set by Railway |
| `FLASK_SECRET_KEY` | Session secret | Random 32-byte hex |
| `EOD_SCHEDULE_TIME` | Daily job time | 16:30 (4:30 PM ET) |
| `TIMEZONE` | Job timezone | America/New_York |
| `LOOKBACK_DAYS` | Rolling average window | 5 days |
| `Z_SCORE_THRESHOLD` | Anomaly threshold | 3.0 |
| `PORT` | Application port | 8888 |

### Detection Algorithm
- **Lookback Period**: 5 trading days
- **Z-Score Threshold**: 3.0 (3 standard deviations)
- **Metric**: Number of trades (transactions)
- **Update Frequency**: Daily at 4:30 PM ET

## 📊 How It Works

1. **Data Collection** (4:30 PM ET daily)
   - Fetches previous day's market data from Polygon.io
   - Stores daily aggregates (OHLCV + transactions)

2. **Baseline Calculation**
   - Computes 5-day rolling average of trades
   - Calculates standard deviation
   - Stores in lookup table

3. **Anomaly Detection**
   - Calculates Z-score: `(current - average) / std_dev`
   - Flags if Z-score > 3.0
   - Stores anomalies with metadata

4. **Visualization**
   - Web dashboard displays anomalies
   - Interactive charts show 30-day history
   - Real-time filtering and navigation

## 🎨 Features

### Dashboard
- Real-time statistics
- Date navigation (skip weekends)
- Z-score filtering
- Anomaly cards with key metrics

### Ticker Details Modal
- 30-day volume chart (bar + line)
- Price history chart
- Detailed anomaly metrics
- Price change percentage

### API Endpoints
- `GET /api/anomalies` - List anomalies
- `GET /api/ticker/<ticker>` - Ticker details
- `GET /api/stats` - System statistics
- `POST /api/backfill` - Backfill data
- `POST /api/run-eod` - Trigger EOD job
- `GET /health` - Health check

## 📈 Example Anomalies

Recent detections (from tutorial):
- **VTAK**: 460K trades vs 6K avg → +106% price change
- **PEGY**: 387K trades vs 16K avg → +48% price change
- **NFLX**: 379K trades vs 125K avg → +11% price change

## 🔍 Monitoring

### Health Check
```bash
curl https://your-app.railway.app/health
```

### View Logs
```bash
railway logs
# or
./railway_helper.sh logs
```

### Check Stats
```bash
curl https://your-app.railway.app/api/stats
```

## 🛠️ Development Workflow

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run locally
python app.py

# Visit http://localhost:8888
```

### Deploy Changes
```bash
# Commit changes
git add .
git commit -m "Your changes"
git push

# Railway auto-deploys from main branch
```

### Test Locally
```bash
# Test database
python init_db.py

# Test data fetching
python -c "from data_fetcher import DataFetcher; DataFetcher().fetch_daily_aggregates('2024-10-25')"

# Test detection
python -c "from anomaly_detector import AnomalyDetector; AnomalyDetector().detect_anomalies('2024-10-25')"
```

## 📚 Resources

- **GitHub**: https://github.com/donoage/anomalies
- **Railway**: https://railway.com/project/cbfff9ab-b927-47fb-bfed-0fd2723089aa
- **Polygon.io Tutorial**: https://polygon.io/blog/hunting-anomalies-in-the-stock-market
- **Polygon.io Docs**: https://polygon.io/docs
- **Railway Docs**: https://docs.railway.app

## ⚠️ Important Notes

1. **Unlimited API Plan**: Rate limiting has been removed from `data_fetcher.py` since you have unlimited access
2. **Market Hours**: EOD job runs at 4:30 PM ET (after market close)
3. **Weekends**: Automatically skipped in data fetching and navigation
4. **Database**: PostgreSQL for production, SQLite for local dev
5. **Continuous Deployment**: Push to main → auto-deploy on Railway

## 🎉 You're All Set!

Everything is configured and ready to deploy. Just complete the manual steps above and you'll have a fully functional stock market anomaly detection system!

### Quick Checklist
- [ ] Add PostgreSQL to Railway project
- [ ] Connect GitHub repo to Railway
- [ ] Set environment variables
- [ ] Generate domain
- [ ] Initialize database
- [ ] Backfill historical data
- [ ] Verify deployment

Happy anomaly hunting! 🔍📈

