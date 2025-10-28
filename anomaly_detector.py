import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from config import Config
from database import db, DailyAggregate, LookupTable, Anomaly
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self):
        self.lookback_days = Config.LOOKBACK_DAYS
        self.threshold = Config.Z_SCORE_THRESHOLD
    
    def build_lookup_table(self, target_date=None):
        """
        Build lookup table with rolling averages for all tickers
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        logger.info(f"Building lookup table for {target_date}")
        
        session = db.get_session()
        try:
            # Get historical data for lookback period
            start_date = target_date - timedelta(days=self.lookback_days * 2)  # Extra buffer
            
            # Fetch all aggregates in date range
            aggregates = session.query(DailyAggregate).filter(
                DailyAggregate.date >= start_date,
                DailyAggregate.date <= target_date
            ).order_by(DailyAggregate.ticker, DailyAggregate.date).all()
            
            # Organize by ticker
            ticker_data = defaultdict(list)
            for agg in aggregates:
                ticker_data[agg.ticker].append({
                    'date': agg.date,
                    'transactions': agg.transactions or 0,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            # Calculate rolling statistics for each ticker
            count = 0
            for ticker, records in ticker_data.items():
                if len(records) < self.lookback_days:
                    continue
                
                # Convert to DataFrame for easier manipulation
                df = pd.DataFrame(records)
                df = df.sort_values('date')
                
                # Calculate rolling averages and std dev
                df['avg_trades'] = df['transactions'].rolling(
                    window=self.lookback_days, 
                    min_periods=self.lookback_days
                ).mean()
                
                df['std_trades'] = df['transactions'].rolling(
                    window=self.lookback_days, 
                    min_periods=self.lookback_days
                ).std()
                
                # Calculate price change
                df['prev_close'] = df['close'].shift(1)
                df['price_diff'] = ((df['close'] - df['prev_close']) / df['prev_close'] * 100)
                
                # Store in lookup table
                for _, row in df.iterrows():
                    if pd.notna(row['avg_trades']):
                        # Check if exists
                        existing = session.query(LookupTable).filter_by(
                            ticker=ticker,
                            date=row['date']
                        ).first()
                        
                        if existing:
                            existing.avg_trades = float(row['avg_trades'])
                            existing.std_trades = float(row['std_trades']) if pd.notna(row['std_trades']) else 0
                            existing.close_price = float(row['close'])
                            existing.price_diff = float(row['price_diff']) if pd.notna(row['price_diff']) else 0
                        else:
                            lookup = LookupTable(
                                ticker=ticker,
                                date=row['date'],
                                avg_trades=float(row['avg_trades']),
                                std_trades=float(row['std_trades']) if pd.notna(row['std_trades']) else 0,
                                close_price=float(row['close']),
                                price_diff=float(row['price_diff']) if pd.notna(row['price_diff']) else 0
                            )
                            session.add(lookup)
                
                count += 1
                if count % 100 == 0:
                    session.commit()
                    logger.info(f"Processed {count} tickers...")
            
            session.commit()
            logger.info(f"Lookup table built successfully for {count} tickers")
            return count
            
        except Exception as e:
            logger.error(f"Error building lookup table: {e}")
            session.rollback()
            raise
        finally:
            db.close_session()
    
    def detect_anomalies(self, target_date=None):
        """
        Detect anomalies for a specific date using the lookup table
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        logger.info(f"Detecting anomalies for {target_date}")
        
        session = db.get_session()
        try:
            # Get today's data
            daily_data = session.query(DailyAggregate).filter_by(
                date=target_date
            ).all()
            
            anomalies = []
            
            for data in daily_data:
                # Get lookup table data
                lookup = session.query(LookupTable).filter_by(
                    ticker=data.ticker,
                    date=target_date
                ).first()
                
                if not lookup or not lookup.std_trades or lookup.std_trades == 0:
                    continue
                
                # Calculate z-score
                trades = data.transactions or 0
                z_score = (trades - lookup.avg_trades) / lookup.std_trades
                
                # Check if anomaly
                if z_score > self.threshold:
                    # Check if already exists
                    existing = session.query(Anomaly).filter_by(
                        ticker=data.ticker,
                        date=target_date
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.trades = trades
                        existing.avg_trades = lookup.avg_trades
                        existing.std_trades = lookup.std_trades
                        existing.z_score = z_score
                        existing.close_price = data.close
                        existing.price_diff = lookup.price_diff
                        existing.volume = data.volume
                    else:
                        # Create new anomaly
                        anomaly = Anomaly(
                            ticker=data.ticker,
                            date=target_date,
                            trades=trades,
                            avg_trades=lookup.avg_trades,
                            std_trades=lookup.std_trades,
                            z_score=z_score,
                            close_price=data.close,
                            price_diff=lookup.price_diff,
                            volume=data.volume
                        )
                        session.add(anomaly)
                        anomalies.append(anomaly)
            
            session.commit()
            logger.info(f"Detected {len(anomalies)} new anomalies for {target_date}")
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            session.rollback()
            raise
        finally:
            db.close_session()
    
    def get_anomalies(self, target_date=None, min_z_score=None):
        """
        Get anomalies for a specific date
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        if min_z_score is None:
            min_z_score = self.threshold
        
        session = db.get_session()
        try:
            query = session.query(Anomaly).filter(
                Anomaly.date == target_date,
                Anomaly.z_score >= min_z_score
            ).order_by(Anomaly.z_score.desc())
            
            anomalies = query.all()
            return [a.to_dict() for a in anomalies]
            
        finally:
            db.close_session()

