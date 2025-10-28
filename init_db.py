"""
Database initialization script
Run this to create all necessary database tables
"""
from database import db, Base
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with all tables"""
    try:
        logger.info(f"Initializing database at: {Config.DATABASE_URL}")
        Base.metadata.create_all(db.engine)
        logger.info("Database initialized successfully!")
        
        # Print table info
        tables = Base.metadata.tables.keys()
        logger.info(f"Created tables: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == '__main__':
    init_database()

