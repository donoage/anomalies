import schedule
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from config import Config
from data_fetcher import DataFetcher
from anomaly_detector import AnomalyDetector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EODScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=Config.TIMEZONE)
        self.data_fetcher = DataFetcher()
        self.anomaly_detector = AnomalyDetector()
        self.timezone = pytz.timezone(Config.TIMEZONE)
    
    def eod_job(self):
        """
        End-of-day job to fetch data and detect anomalies
        """
        logger.info("Starting EOD job...")
        
        try:
            # Get yesterday's date (market data is available next day)
            yesterday = (datetime.now(self.timezone) - timedelta(days=1)).date()
            
            # Skip weekends
            if yesterday.weekday() >= 5:
                logger.info(f"Skipping weekend date: {yesterday}")
                return
            
            logger.info(f"Processing data for {yesterday}")
            
            # Step 1: Fetch daily aggregates
            logger.info("Step 1: Fetching daily aggregates...")
            count = self.data_fetcher.fetch_daily_aggregates(yesterday)
            logger.info(f"Fetched {count} ticker aggregates")
            
            # Step 2: Build/update lookup table
            logger.info("Step 2: Building lookup table...")
            self.anomaly_detector.build_lookup_table(yesterday)
            
            # Step 3: Detect anomalies
            logger.info("Step 3: Detecting anomalies...")
            anomalies = self.anomaly_detector.detect_anomalies(yesterday)
            
            logger.info(f"EOD job complete. Found {len(anomalies)} anomalies for {yesterday}")
            
            # Log top anomalies
            if anomalies:
                logger.info("Top 10 anomalies:")
                sorted_anomalies = sorted(anomalies, key=lambda x: x.z_score, reverse=True)[:10]
                for a in sorted_anomalies:
                    logger.info(
                        f"  {a.ticker}: {a.trades} trades "
                        f"(avg: {a.avg_trades:.0f}, z-score: {a.z_score:.2f}, "
                        f"price change: {a.price_diff:.2f}%)"
                    )
        
        except Exception as e:
            logger.error(f"Error in EOD job: {e}", exc_info=True)
    
    def start(self):
        """
        Start the scheduler
        """
        # Parse schedule time (e.g., "16:30")
        hour, minute = map(int, Config.EOD_SCHEDULE_TIME.split(':'))
        
        # Schedule EOD job
        self.scheduler.add_job(
            self.eod_job,
            CronTrigger(
                hour=hour,
                minute=minute,
                timezone=self.timezone
            ),
            id='eod_job',
            name='End of Day Data Fetch and Anomaly Detection',
            replace_existing=True
        )
        
        logger.info(f"Scheduled EOD job for {Config.EOD_SCHEDULE_TIME} {Config.TIMEZONE}")
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """
        Stop the scheduler
        """
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """
        Run the EOD job immediately (for testing)
        """
        logger.info("Running EOD job immediately...")
        self.eod_job()

