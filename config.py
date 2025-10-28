import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    
    # S3 Flat Files Configuration (get from https://polygon.io/dashboard)
    # These are different from your regular API key!
    POLYGON_S3_ACCESS_KEY = os.getenv('POLYGON_S3_ACCESS_KEY', os.getenv('POLYGON_API_KEY'))
    POLYGON_S3_SECRET_KEY = os.getenv('POLYGON_S3_SECRET_KEY', os.getenv('POLYGON_API_KEY'))
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///anomalies.db')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT = int(os.getenv('PORT', 8888))
    
    # Anomaly Detection Configuration
    LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', 5))
    Z_SCORE_THRESHOLD = float(os.getenv('Z_SCORE_THRESHOLD', 3.0))
    
    # Data Source Configuration
    USE_FLAT_FILES = os.getenv('USE_FLAT_FILES', 'true').lower() == 'true'
    DARK_POOL_ONLY = os.getenv('DARK_POOL_ONLY', 'true').lower() == 'true'
    USE_TRADES_FILES = os.getenv('USE_TRADES_FILES', 'false').lower() == 'true'  # Slower but allows dark pool filtering
    
    # Scheduling Configuration
    # Flat files are available at 11 AM ET according to Polygon.io docs
    EOD_SCHEDULE_TIME = os.getenv('EOD_SCHEDULE_TIME', '11:00')  # 11:00 AM ET (when flat files are available)
    TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')
    
    # Data Configuration
    DATA_DIR = os.getenv('DATA_DIR', './data')
    CACHE_DIR = os.path.join(DATA_DIR, 'cache')

