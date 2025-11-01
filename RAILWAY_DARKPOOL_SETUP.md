# Railway Dark Pool Backfill Setup

## Overview
This guide explains how to run the dark pool backfill on Railway using a **Cron Job** service to avoid HTTP timeouts.

## Setup Instructions

### 1. Push Your Code to Railway

First, commit and push all changes:

```bash
git add .
git commit -m "Add dark pool backfill with trades files"
git push origin main
```

### 2. Create a Cron Job Service on Railway

1. Go to your Railway project dashboard
2. Click **"+ New"** → **"Empty Service"**
3. Name it: `darkpool-backfill`
4. Connect it to your GitHub repository (same repo as main app)

### 3. Configure the Cron Service

In the `darkpool-backfill` service settings:

#### **Environment Variables**
Copy all environment variables from your main app service:
- `POLYGON_API_KEY`
- `POLYGON_S3_ACCESS_KEY`
- `POLYGON_S3_SECRET_KEY`
- `DATABASE_URL` (use the same Postgres database)
- `DARK_POOL_ONLY=true`
- `USE_TRADES_FILES=true`
- `MIN_TRADE_SIZE=1000`
- `LOOKBACK_DAYS=20`
- `Z_SCORE_THRESHOLD=1.5`

#### **Start Command**
Set the start command to:
```bash
python railway_backfill_darkpool.py 30
```
(The `30` means backfill 30 days - adjust as needed)

#### **Cron Schedule**
In the service settings, find **"Cron Schedule"** and set it to:
```
@once
```

This will run the backfill **once** when you deploy, then stop.

### 4. Deploy the Service

Click **"Deploy"** on the cron service. It will:
1. Start the backfill process
2. Download trades files from S3
3. Filter for dark pool trades (exchange=4 + trf_id)
4. Filter for trades ≥ 1,000 shares
5. Build lookup tables
6. Detect anomalies
7. Exit cleanly when complete

### 5. Monitor Progress

Watch the logs in Railway to see:
- Download progress
- Number of tickers processed
- Anomalies detected per day
- Total completion status

Expected runtime: **Several hours** (trades files are large)

### 6. After Backfill Completes

Once the backfill is done:
1. The cron service will automatically stop
2. Your main web app will have the dark pool data available
3. The scheduler will continue detecting new anomalies daily

### 7. Optional: Remove the Cron Service

After backfill completes, you can:
- Delete the `darkpool-backfill` service (no longer needed)
- Or keep it and change the cron schedule to run weekly for re-backfills

## Alternative: Run Multiple Days in Batches

If you want to backfill in smaller batches to avoid long-running jobs:

1. Set cron schedule to: `0 0 * * *` (daily at midnight)
2. Change the command to: `python railway_backfill_darkpool.py 1`
3. Let it run for 30 days to gradually backfill

## Troubleshooting

### "Out of Memory" Error
- Reduce the backfill days: `python railway_backfill_darkpool.py 7`
- Run multiple times for different date ranges

### "Access Denied" to S3
- Verify `POLYGON_S3_ACCESS_KEY` and `POLYGON_S3_SECRET_KEY` are correct
- Check your Polygon.io plan includes Flat Files access
- Trades files may require a higher tier plan

### No Anomalies Detected
- Dark pool trades are sparse - this is normal
- Try lowering `Z_SCORE_THRESHOLD` to 1.0
- Check that `MIN_TRADE_SIZE` isn't too high (try 500)

## Configuration Summary

Current settings for dark pool detection:
- **Exchange**: ID = 4 (with trf_id field)
- **Min Trade Size**: 1,000 shares (block trades only)
- **Lookback Period**: 20 days
- **Z-Score Threshold**: 1.5 standard deviations

These settings focus on **meaningful institutional dark pool activity**.

