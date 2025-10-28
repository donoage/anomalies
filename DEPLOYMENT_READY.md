# 🚀 Deployment Ready - Anomalies Project

## ✅ Setup Complete!

Your stock market anomaly detection system is now fully configured and ready for Railway deployment!

### What's Working

- ✅ **Flat Files Integration**: Successfully downloading from Polygon.io S3
- ✅ **S3 Credentials**: Configured and tested
- ✅ **Database**: SQLite (local) / PostgreSQL (Railway)
- ✅ **Scheduler**: Configured for 11:00 AM ET daily runs
- ✅ **Web Dashboard**: Interactive UI with charts
- ✅ **API Endpoints**: Full REST API
- ✅ **Automated Processing**: Daily data fetch + anomaly detection

### Test Results

```
✓ Successfully processed 11,632 tickers from flat file for 2025-10-27
✓ Flat Files connection working
✓ S3 credentials valid
✓ Data parsing successful
```

## 📊 Current Configuration

### Data Source
- **Method**: Flat Files (S3)
- **Schedule**: 11:00 AM ET daily
- **Data Type**: Day Aggregates (all market data - lit + dark pool combined)
- **Lookback**: 5 trading days
- **Z-Score Threshold**: 3.0

### Important Note: Dark Pool Filtering

**Current Status**: Day aggregates provide **combined** lit pool + dark pool data. They don't separate by venue.

**To get dark pool only data**, you would need to:
1. Use **Trades Flat Files** (not Day Aggregates)
2. Filter by exchange codes (TRF, ADF for dark pools)
3. Manually aggregate the data
4. Much larger files and slower processing

**Recommendation**: Start with day aggregates (current setup) to detect anomalies in total market activity, then add dark pool filtering later if needed.

## 🚂 Railway Deployment Steps

### 1. Environment Variables to Set on Railway

```bash
# Required
POLYGON_API_KEY=S08ktzv3Ip5XAMeu6FewW37BJ_2YOIsn
POLYGON_S3_ACCESS_KEY=f8c82963-4aab-4ee4-9c1e-7659fa26c337
POLYGON_S3_SECRET_KEY=S08ktzv3Ip5XAMeu6FewW37BJ_2YOIsn
FLASK_SECRET_KEY=<generate with: openssl rand -hex 32>

# Configuration
USE_FLAT_FILES=true
DARK_POOL_ONLY=false
USE_TRADES_FILES=false
EOD_SCHEDULE_TIME=11:00
TIMEZONE=America/New_York
LOOKBACK_DAYS=5
Z_SCORE_THRESHOLD=3.0
PORT=8888
```

### 2. Add PostgreSQL Database

In Railway dashboard:
1. Click "+ New"
2. Select "Database"
3. Choose "PostgreSQL"
4. `DATABASE_URL` will be auto-set

### 3. Deploy

Railway will automatically:
- Detect `Procfile` and `requirements.txt`
- Install dependencies
- Start the application with Gunicorn
- Run the scheduler

### 4. Initialize Database

After first deployment:
```bash
railway run python init_db.py
```

### 5. Backfill Historical Data (Optional)

```bash
# Backfill 30 days to establish baseline
railway run python backfill_30days.py
```

Or let it run naturally - it will fetch data daily at 11 AM ET.

## 📅 How It Works

### Daily Automated Process (11 AM ET)

1. **Fetch Data**: Downloads yesterday's flat file from S3 (~11,000 tickers)
2. **Build Lookup Table**: Calculates 5-day rolling averages and std dev
3. **Detect Anomalies**: Identifies tickers with Z-score > 3.0
4. **Store Results**: Saves to PostgreSQL database
5. **Web Dashboard**: Displays anomalies with interactive charts

### What Gets Detected

Anomalies are flagged when:
- Number of trades is > 3 standard deviations above 5-day average
- Indicates unusual trading activity
- Could signal: news events, earnings, volatility, etc.

### Example Output

```
Ticker    Trades      Avg (5d)    Z-Score    Price Chg    Close
AAPL      450,000     125,000     3.85       +2.5%        $175.50
TSLA      890,000     200,000     5.20       -3.2%        $245.30
```

## 🎯 Accessing Your App

After deployment:

1. **Web Dashboard**: `https://your-app.railway.app`
2. **API**: `https://your-app.railway.app/api/anomalies`
3. **Health Check**: `https://your-app.railway.app/health`

## 📁 Project Files

### Core Application
- `app.py` - Flask web server
- `scheduler.py` - Daily job scheduler
- `anomaly_detector.py` - Z-score detection algorithm
- `flatfile_fetcher.py` - S3 flat files downloader
- `data_fetcher.py` - REST API fallback
- `database.py` - PostgreSQL/SQLite models

### Configuration
- `config.py` - Environment configuration
- `.env` - Local environment variables
- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment config

### Utilities
- `init_db.py` - Database initialization
- `backfill_30days.py` - Historical data backfill
- `process_yesterday.py` - Manual processing script
- `test_flatfiles.py` - S3 connection test

### Documentation
- `README.md` - Project overview
- `SETUP.md` - Detailed setup guide
- `FLATFILES_SETUP.md` - Flat files configuration
- `DEPLOYMENT_READY.md` - This file

## 🔄 Continuous Deployment

Railway is configured for continuous deployment:
- Push to `main` branch → automatic deployment
- Database persists across deployments
- Scheduler runs automatically
- No manual intervention needed

## 🐛 Troubleshooting

### If No Anomalies Detected

1. **Check Data**: Verify backfill completed
   ```bash
   railway run python -c "from database import db, DailyAggregate; session = db.get_session(); print(session.query(DailyAggregate).count())"
   ```

2. **Lower Threshold**: Try `Z_SCORE_THRESHOLD=2.0`

3. **Check Logs**: `railway logs`

### If Flat Files Fail

The system will automatically fall back to REST API if flat files fail.

To force REST API:
```bash
USE_FLAT_FILES=false
```

## 📊 Monitoring

### View Logs
```bash
railway logs
```

### Check Stats
```bash
curl https://your-app.railway.app/api/stats
```

### Manual EOD Job
```bash
curl -X POST https://your-app.railway.app/api/run-eod
```

## 🎉 You're Ready!

Everything is configured and tested. Just:

1. Push to GitHub (if not already done)
2. Connect to Railway
3. Set environment variables
4. Add PostgreSQL
5. Deploy!

The system will automatically:
- ✅ Fetch data daily at 11 AM ET
- ✅ Detect anomalies
- ✅ Update the dashboard
- ✅ Store everything in PostgreSQL

Happy anomaly hunting! 🔍📈

---

**Note**: Remember to add dark pool filtering later if needed by using trades flat files instead of day aggregates.

