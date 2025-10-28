# 🚀 Deployment Steps

## ✅ Completed Steps

1. ✅ Git repository initialized
2. ✅ Initial commit created
3. ✅ GitHub repository created: https://github.com/donoage/anomalies
4. ✅ Railway project created: https://railway.com/project/cbfff9ab-b927-47fb-bfed-0fd2723089aa

## 📋 Next Steps (Manual)

### Step 1: Add PostgreSQL Database to Railway

Since Railway CLI requires interactive mode for adding services, please do this via the dashboard:

1. Open Railway project: https://railway.com/project/cbfff9ab-b927-47fb-bfed-0fd2723089aa
2. Click **"+ New"** button
3. Select **"Database"**
4. Choose **"Add PostgreSQL"**
5. Wait for database to provision

### Step 2: Connect GitHub Repository to Railway

1. In your Railway project dashboard
2. Click **"+ New"** button
3. Select **"GitHub Repo"**
4. Choose **"donoage/anomalies"**
5. Railway will automatically detect the configuration from `Procfile` and `railway.json`

### Step 3: Set Environment Variables

In Railway project settings → Variables, add:

```bash
POLYGON_API_KEY=your_polygon_api_key_here
FLASK_SECRET_KEY=generate_random_secret_key
EOD_SCHEDULE_TIME=16:30
TIMEZONE=America/New_York
LOOKBACK_DAYS=5
Z_SCORE_THRESHOLD=3.0
```

**Note**: `DATABASE_URL` is automatically provided by Railway when you add PostgreSQL

To generate a secure secret key:
```bash
openssl rand -hex 32
```

### Step 4: Deploy

Railway will automatically deploy when you connect the GitHub repo. You can also trigger manual deployments:

```bash
cd /Users/stephenbae/Projects/anomalies
railway up
```

### Step 5: Generate Public Domain

```bash
railway domain
```

Or via dashboard:
1. Go to your service settings
2. Click **"Generate Domain"**
3. Copy the generated URL

### Step 6: Initialize Database

After deployment is successful:

```bash
railway run python init_db.py
```

This will create all necessary database tables.

### Step 7: Backfill Historical Data

Populate the database with historical market data:

```bash
# Backfill last 30 days
railway run python -c "from data_fetcher import DataFetcher; DataFetcher().backfill_data(30)"
```

Or use the API endpoint after the app is running:

```bash
curl -X POST https://your-app.railway.app/api/backfill \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

### Step 8: Build Lookup Table

After backfilling data, build the lookup table:

```bash
railway run python -c "from anomaly_detector import AnomalyDetector; AnomalyDetector().build_lookup_table()"
```

### Step 9: Verify Deployment

1. Visit your Railway app URL
2. Check the dashboard loads
3. Verify stats are displayed
4. Check that anomalies are detected

Health check endpoint:
```bash
curl https://your-app.railway.app/health
```

## 🔄 Continuous Deployment

Railway is now configured for continuous deployment:

- Any push to the `main` branch will trigger automatic deployment
- Railway will rebuild and redeploy your application
- Database and environment variables persist across deployments

## 📊 Monitoring

### View Logs

```bash
railway logs
```

Or view in Railway dashboard → Deployments → Select deployment → Logs

### Check Status

```bash
railway status
```

### View Variables

```bash
railway variables
```

## 🛠️ Useful Commands

```bash
# Open Railway dashboard
railway open

# Run commands in Railway environment
railway run <command>

# Connect to PostgreSQL
railway connect postgres

# Redeploy latest version
railway redeploy

# View deployment history
railway deployment list
```

## 🔧 Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Verify PostgreSQL is added to your project
2. Check that `DATABASE_URL` is set (should be automatic)
3. Ensure database is running (check Railway dashboard)

### API Rate Limiting

With unlimited Polygon.io plan, rate limiting is removed. If you see API errors:

1. Verify your API key is correct
2. Check your Polygon.io plan status
3. Review API logs in Railway

### Scheduler Not Running

The EOD scheduler runs at 4:30 PM ET by default. To test:

```bash
# Trigger manually via API
curl -X POST https://your-app.railway.app/api/run-eod
```

### No Anomalies Detected

1. Ensure data has been backfilled
2. Verify lookup table is built
3. Try lowering `Z_SCORE_THRESHOLD`
4. Check that market data exists for the date

## 📝 Environment-Specific Notes

### Production (Railway)
- Uses PostgreSQL database
- Runs on Gunicorn
- Automatic SSL/HTTPS
- Scheduled jobs run automatically

### Local Development
- Uses SQLite database
- Runs on Flask development server
- No SSL (http://localhost:8888)
- Manual job triggering

## 🎉 Success!

Once all steps are complete, your anomaly detection system will be:

- ✅ Running on Railway with PostgreSQL
- ✅ Automatically fetching daily market data
- ✅ Detecting anomalies in real-time
- ✅ Accessible via public URL
- ✅ Continuously deployed from GitHub

Visit your app and start hunting anomalies! 🔍📈

