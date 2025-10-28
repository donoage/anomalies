# Implementation Notes

## Current Implementation Status

### ✅ Completed Features
1. **REST API Integration**: Using Polygon.io's `get_grouped_daily_aggs()` endpoint
2. **Automated Scheduling**: Configured to run at 11:00 AM ET daily (when data is available)
3. **Z-Score Anomaly Detection**: 5-day rolling average with configurable threshold
4. **Web Dashboard**: Interactive UI with charts
5. **Database**: PostgreSQL (Railway) / SQLite (local)
6. **Unlimited API Plan**: No rate limiting

### ⚠️ Current Limitations

#### 1. Dark Pool vs Lit Pool Filtering
**Issue**: The current implementation uses `get_grouped_daily_aggs()` which returns **combined** lit pool + dark pool data.

**Why**: The Polygon.io REST API's grouped daily aggregates endpoint doesn't provide a parameter to filter by venue type (dark pool vs lit pool).

**Solutions**:
- **Option A (Recommended)**: Use [Flat Files with Trades Data](https://polygon.io/docs/flat-files/stocks/trades)
  - Download daily trades flat files
  - Filter by `exchange` field for dark pool venues (TRF, ADF, etc.)
  - Aggregate manually
  - More complex but gives full control

- **Option B**: Use [Trades API](https://polygon.io/docs/stocks/get_v3_trades__stockticker) with filtering
  - Query trades endpoint for each ticker
  - Filter by exchange/venue
  - Much slower, may hit rate limits even with unlimited plan
  - Not practical for market-wide analysis

- **Option C**: Accept combined data
  - Current implementation
  - Faster and simpler
  - Still detects anomalies, just not dark-pool-specific

**Recommendation**: If dark pool filtering is critical, implement Option A using Flat Files. This requires:
1. S3/MinIO client setup
2. Daily file download and parsing
3. Exchange code filtering
4. Custom aggregation logic

#### 2. Flat Files vs REST API
**Current**: Using REST API (`get_grouped_daily_aggs`)
**Tutorial Suggests**: Using [Flat Files](https://polygon.io/docs/flat-files/stocks/day-aggregates)

**Why REST API**:
- ✅ Simpler implementation
- ✅ No S3 setup required
- ✅ Works with unlimited plan
- ✅ Automatic aggregation
- ❌ No venue filtering
- ❌ Slightly slower for bulk downloads

**Why Flat Files**:
- ✅ More efficient for bulk data
- ✅ Can filter by venue (if using trades files)
- ✅ Lower API usage
- ❌ Requires S3/MinIO setup
- ❌ More complex parsing
- ❌ Need to handle file downloads

### 📊 Data Availability

According to [Polygon.io Flat Files docs](https://polygon.io/docs/flat-files/stocks/day-aggregates):
- **Availability**: End-of-day (files updated at 11 AM ET for previous day)
- **Current Schedule**: 11:00 AM ET daily
- **Lookback**: 5 trading days
- **Detection**: Runs automatically on Railway

### 🔄 Railway Deployment

The scheduler is configured to run automatically on Railway:
1. **Schedule**: 11:00 AM ET daily
2. **Process**: Fetch yesterday's data → Build lookup table → Detect anomalies
3. **Storage**: PostgreSQL database (persistent)
4. **No manual intervention required**

### 🎯 Next Steps for Dark Pool Implementation

If you want dark-pool-only anomaly detection:

1. **Install MinIO client** (for S3 access):
```bash
pip install minio
```

2. **Download trades flat files** instead of aggregates:
```python
# Use trades files: us_stocks_sip/trades_v1/
# Filter by exchange codes for dark pools:
# - TRF (Trade Reporting Facility)
# - ADF (Alternative Display Facility)  
# - etc.
```

3. **Aggregate manually** by ticker:
```python
# Group trades by ticker
# Sum volume, count transactions
# Calculate OHLC
```

4. **Update data_fetcher.py** to use flat files instead of REST API

### 📚 References

- [Polygon.io Blog: Hunting Anomalies](https://polygon.io/blog/hunting-anomalies-in-the-stock-market)
- [Flat Files: Day Aggregates](https://polygon.io/docs/flat-files/stocks/day-aggregates)
- [Flat Files: Trades](https://polygon.io/docs/flat-files/stocks/trades) (for dark pool filtering)
- [Exchange Codes](https://polygon.io/docs/stocks/get_v3_trades__stockticker) (see `exchange` parameter)

### 💡 Current Behavior

The system currently:
1. ✅ Fetches all market data (lit + dark pool combined)
2. ✅ Detects anomalies in total trading activity
3. ✅ Runs automatically at 11 AM ET
4. ✅ Works on Railway without manual intervention
5. ❌ Does NOT filter for dark pool only

**Bottom Line**: The anomaly detection works correctly, but detects anomalies in **total market activity** (lit + dark pool combined), not dark pool activity specifically.

