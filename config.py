import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///anomalies.db')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT = int(os.getenv('PORT', 8888))
    
    # Anomaly Detection Configuration
    LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', 5))
    Z_SCORE_THRESHOLD = float(os.getenv('Z_SCORE_THRESHOLD', 3.0))
    
    # Scheduling Configuration
    EOD_SCHEDULE_TIME = os.getenv('EOD_SCHEDULE_TIME', '16:30')  # 4:30 PM ET
    TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')
    
    # Data Configuration
    DATA_DIR = os.getenv('DATA_DIR', './data')
    CACHE_DIR = os.path.join(DATA_DIR, 'cache')

