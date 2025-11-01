from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from config import Config
from database import db, Anomaly, DailyAggregate
from anomaly_detector import AnomalyDetector
from data_fetcher import DataFetcher
from scheduler import EODScheduler
from polygon import RESTClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize components
anomaly_detector = AnomalyDetector()
data_fetcher = DataFetcher()
scheduler = EODScheduler()
polygon_client = RESTClient(Config.POLYGON_API_KEY)


@app.route('/')
def index():
    """
    Main dashboard page
    """
    return render_template('index.html')


@app.route('/api/anomalies')
def get_anomalies():
    """
    Get anomalies for a specific date
    """
    date_str = request.args.get('date')
    min_z_score = request.args.get('min_z_score', type=float)
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        # Get most recent date with anomalies
        session = db.get_session()
        try:
            latest = session.query(Anomaly).order_by(Anomaly.date.desc()).first()
            if latest:
                target_date = latest.date
            else:
                target_date = datetime.now().date() - timedelta(days=1)
        finally:
            db.close_session()
    
    anomalies = anomaly_detector.get_anomalies(target_date, min_z_score)
    
    return jsonify({
        'date': target_date.isoformat(),
        'count': len(anomalies),
        'anomalies': anomalies
    })


@app.route('/api/anomalies/dates')
def get_anomaly_dates():
    """
    Get list of dates with anomalies
    """
    min_z_score = request.args.get('min_z_score', type=float)
    
    session = db.get_session()
    try:
        query = session.query(Anomaly.date).distinct()
        if min_z_score:
            # Only include dates that have at least one anomaly above the threshold
            query = query.filter(Anomaly.z_score >= min_z_score)
        dates = query.order_by(Anomaly.date.desc()).limit(30).all()
        return jsonify({
            'dates': [d[0].isoformat() for d in dates]
        })
    finally:
        db.close_session()


@app.route('/api/ticker/<ticker>')
def get_ticker_details(ticker):
    """
    Get detailed information for a specific ticker
    """
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    session = db.get_session()
    try:
        # Get anomaly data
        anomaly = session.query(Anomaly).filter_by(
            ticker=ticker.upper(),
            date=target_date
        ).first()
        
        if not anomaly:
            return jsonify({'error': 'Anomaly not found'}), 404
        
        # Get historical data (30 days)
        start_date = target_date - timedelta(days=30)
        historical = session.query(DailyAggregate).filter(
            DailyAggregate.ticker == ticker.upper(),
            DailyAggregate.date >= start_date,
            DailyAggregate.date <= target_date
        ).order_by(DailyAggregate.date).all()
        
        return jsonify({
            'anomaly': anomaly.to_dict(),
            'historical': [h.to_dict() for h in historical]
        })
    
    finally:
        db.close_session()


@app.route('/api/ticker/<ticker>/intraday')
def get_ticker_intraday(ticker):
    """
    Get intraday data for a specific ticker and date
    """
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter required'}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    try:
        # Fetch intraday bars from Polygon
        aggs = polygon_client.get_aggs(
            ticker=ticker.upper(),
            multiplier=5,
            timespan="minute",
            from_=target_date.isoformat(),
            to=target_date.isoformat(),
            adjusted=True
        )
        
        bars = []
        for agg in aggs:
            bars.append({
                'timestamp': agg.timestamp,
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close,
                'volume': agg.volume,
                'transactions': agg.transactions if hasattr(agg, 'transactions') else None
            })
        
        return jsonify({
            'ticker': ticker.upper(),
            'date': target_date.isoformat(),
            'bars': bars
        })
    
    except Exception as e:
        logger.error(f"Error fetching intraday data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """
    Get overall statistics
    """
    min_z_score = request.args.get('min_z_score', type=float)
    
    session = db.get_session()
    try:
        # Get latest date
        latest_anomaly = session.query(Anomaly).order_by(Anomaly.date.desc()).first()
        latest_date = latest_anomaly.date if latest_anomaly else None
        
        # Count anomalies for latest date (filtered by z-score if provided)
        if latest_date:
            query = session.query(Anomaly).filter_by(date=latest_date)
            if min_z_score:
                query = query.filter(Anomaly.z_score >= min_z_score)
            anomaly_count = query.count()
        else:
            anomaly_count = 0
        
        # Total tickers tracked
        total_tickers = session.query(DailyAggregate.ticker).distinct().count()
        
        # Total anomalies detected (filtered by z-score if provided)
        query = session.query(Anomaly)
        if min_z_score:
            query = query.filter(Anomaly.z_score >= min_z_score)
        total_anomalies = query.count()
        
        return jsonify({
            'latest_date': latest_date.isoformat() if latest_date else None,
            'anomaly_count_today': anomaly_count,
            'total_tickers': total_tickers,
            'total_anomalies': total_anomalies
        })
    
    finally:
        db.close_session()


@app.route('/api/run-eod', methods=['POST'])
def run_eod():
    """
    Manually trigger EOD job (for testing)
    """
    try:
        scheduler.run_now()
        return jsonify({'status': 'success', 'message': 'EOD job started'})
    except Exception as e:
        logger.error(f"Error running EOD job: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/backfill', methods=['POST'])
def backfill():
    """
    Backfill historical data and detect anomalies
    """
    days = request.json.get('days', 30)
    
    try:
        logger.info(f"Starting backfill for {days} days...")
        
        # Fetch historical data
        data_fetcher.backfill_data(days)
        logger.info(f"✓ Data fetched for {days} days")
        
        # Build lookup table for all dates
        logger.info("Building lookup tables...")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Skip weekends
                try:
                    anomaly_detector.build_lookup_table(current_date)
                except Exception as e:
                    logger.warning(f"Could not build lookup for {current_date}: {e}")
            current_date += timedelta(days=1)
        
        logger.info("✓ Lookup tables built")
        
        # Detect anomalies for recent dates (last 2 days)
        logger.info("Detecting anomalies...")
        anomaly_count = 0
        for days_back in range(2):
            target_date = end_date - timedelta(days=days_back)
            if target_date.weekday() < 5:  # Skip weekends
                try:
                    anomalies = anomaly_detector.detect_anomalies(target_date)
                    anomaly_count += len(anomalies)
                    logger.info(f"✓ Detected {len(anomalies)} anomalies for {target_date}")
                except Exception as e:
                    logger.warning(f"Could not detect anomalies for {target_date}: {e}")
        
        logger.info(f"✓ Backfill complete! Detected {anomaly_count} total anomalies")
        
        return jsonify({
            'status': 'success',
            'message': f'Backfilled {days} days and detected {anomaly_count} anomalies'
        })
    except Exception as e:
        logger.error(f"Error backfilling data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health')
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


def init_app():
    """
    Initialize the application
    """
    # Start scheduler
    scheduler.start()
    logger.info("Application initialized")


if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=False)

