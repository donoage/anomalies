# Flat Files Setup Guide

## Current Status

✅ **Flat Files Implementation**: Complete  
⚠️ **Access Issue**: Getting 403 Forbidden error  
✅ **REST API Fallback**: Working  
✅ **Railway Deployment**: Ready  
✅ **Automated Scheduling**: Configured for 11 AM ET  

## The Issue

The flat files implementation is complete, but we're getting a **403 Forbidden** error when trying to access Polygon.io's S3 bucket. This typically means:

1. **Your plan may not include Flat Files access**
   - Check your Polygon.io plan at https://polygon.io/dashboard
   - Flat Files require **Stocks Starter** plan or higher
   - See: https://polygon.io/docs/flat-files/stocks/day-aggregates

2. **Authentication method may need adjustment**
   - Polygon.io uses custom S3 authentication
   - May require special configuration

## Two Approaches Implemented

### Option 1: REST API (Currently Working) ✅

**File**: `data_fetcher.py`  
**Method**: `get_grouped_daily_aggs()`  
**Pros**:
- ✅ Works right now
- ✅ Simple, no S3 setup
- ✅ Fast for daily updates
- ✅ Unlimited plan = no rate limits

**Cons**:
- ❌ No dark pool filtering
- ❌ Returns combined lit + dark pool data

**Configuration**:
```bash
USE_FLAT_FILES=false
```

### Option 2: Flat Files (Ready, needs access) ⚠️

**File**: `flatfile_fetcher.py`  
**Method**: Downloads CSV files from S3  
**Pros**:
- ✅ More efficient for bulk data
- ✅ Can filter dark pool (with trades files)
- ✅ Lower API usage

**Cons**:
- ❌ Requires Flat Files plan access
- ❌ 403 error currently
- ❌ More complex setup

**Configuration**:
```bash
USE_FLAT_FILES=true
DARK_POOL_ONLY=true  # Only works with trades files
USE_TRADES_FILES=true  # Required for dark pool filtering
```

## Dark Pool Filtering

### Current Limitation

**Day Aggregates** (both REST API and Flat Files) provide **combined** lit + dark pool data. They don't separate by venue.

### Solution for Dark Pool Only

To get **dark pool only** data, you need:

1. **Trades Flat Files** (not Day Aggregates)
   - Path: `us_stocks_sip/trades_v1/YYYY/MM/YYYY-MM-DD.csv.gz`
   - Contains individual trades with `exchange` field
   - Much larger files (GBs vs MBs)

2. **Filter by Exchange**:
   ```python
   DARK_POOL_EXCHANGES = {
       'TRF',  # FINRA Trade Reporting Facility
       'ADF',  # Alternative Display Facility
   }
   ```

3. **Aggregate Manually**:
   - Group trades by ticker
   - Calculate OHLCV
   - Count transactions

**Note**: This is implemented in `flatfile_fetcher.py` but requires Flat Files access.

## Recommended Setup for Railway

### For Now (REST API)

Since Flat Files access needs verification, use REST API:

```bash
# .env on Railway
USE_FLAT_FILES=false
DARK_POOL_ONLY=false
EOD_SCHEDULE_TIME=11:00
```

**What you get**:
- ✅ Automated daily updates at 11 AM ET
- ✅ Anomaly detection on total market activity
- ✅ Works immediately
- ❌ No dark pool filtering

### Future (Flat Files + Dark Pool)

Once Flat Files access is confirmed:

```bash
# .env on Railway  
USE_FLAT_FILES=true
DARK_POOL_ONLY=true
USE_TRADES_FILES=true
EOD_SCHEDULE_TIME=11:00
```

**What you get**:
- ✅ Automated daily updates at 11 AM ET
- ✅ Dark pool only anomaly detection
- ✅ More efficient data fetching
- ⚠️ Slower processing (trades files are large)

## Verifying Flat Files Access

### Method 1: Check Your Plan

1. Go to https://polygon.io/dashboard
2. Check your subscription
3. Verify "Flat Files" is included

### Method 2: Test with MinIO CLI

According to the [Polygon.io blog](https://polygon.io/blog/hunting-anomalies-in-the-stock-market):

```bash
# Install MinIO client
brew install minio/stable/mc

# Configure
mc alias set s3polygon https://files.polygon.io YOUR_API_KEY YOUR_API_KEY

# Test access
mc ls s3polygon/flatfiles/us_stocks_sip/day_aggs_v1/2025/10/
```

If this works, the Python implementation should work too.

### Method 3: Contact Polygon Support

If you have a paid plan but getting 403:
- Email: support@polygon.io
- Mention: "403 error accessing Flat Files via S3"
- Provide: Your API key and plan type

## Current Configuration

The system is configured to:
1. ✅ Try Flat Files first (if `USE_FLAT_FILES=true`)
2. ✅ Fall back to REST API if needed
3. ✅ Run daily at 11 AM ET
4. ✅ Deploy to Railway automatically
5. ✅ Detect anomalies in trading activity

## Files Created

- ✅ `flatfile_fetcher.py` - Boto3 S3 implementation
- ✅ `flatfile_fetcher_minio_backup.py` - MinIO implementation (backup)
- ✅ `data_fetcher.py` - REST API implementation (working)
- ✅ `test_flatfiles.py` - Test script
- ✅ `scheduler.py` - Updated to support both methods
- ✅ `config.py` - Configuration options

## Next Steps

### Immediate (Use REST API)

1. Set `USE_FLAT_FILES=false` in Railway
2. Deploy and let it run
3. Anomalies will be detected (combined lit + dark pool)

### When Flat Files Access Confirmed

1. Verify access with MinIO CLI
2. Set `USE_FLAT_FILES=true` in Railway
3. Optionally set `USE_TRADES_FILES=true` for dark pool filtering
4. Redeploy

## Summary

| Feature | REST API | Flat Files (Day Aggs) | Flat Files (Trades) |
|---------|----------|----------------------|---------------------|
| **Status** | ✅ Working | ⚠️ 403 Error | ⚠️ 403 Error |
| **Speed** | Fast | Fast | Slow (large files) |
| **Dark Pool Filter** | ❌ No | ❌ No | ✅ Yes |
| **Setup Complexity** | Easy | Medium | Hard |
| **API Usage** | Higher | Lower | Lowest |
| **Recommended For** | Quick start | Production | Dark pool analysis |

**Current Recommendation**: Use REST API until Flat Files access is verified, then switch to Flat Files with trades for dark pool filtering.

