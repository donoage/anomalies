#!/usr/bin/env python3
"""
Migration script to change volume column from INTEGER to BIGINT
"""
from sqlalchemy import create_engine, text
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Connecting to database...")
    engine = create_engine(Config.DATABASE_URL)
    
    with engine.connect() as conn:
        logger.info("Altering volume column to BIGINT...")
        
        # For PostgreSQL
        if 'postgresql' in Config.DATABASE_URL:
            conn.execute(text("ALTER TABLE daily_aggregates ALTER COLUMN volume TYPE BIGINT"))
            conn.commit()
            logger.info("✓ Successfully migrated volume column to BIGINT")
        
        # For SQLite (recreate table)
        elif 'sqlite' in Config.DATABASE_URL:
            logger.info("SQLite detected - recreating table...")
            conn.execute(text("""
                CREATE TABLE daily_aggregates_new (
                    id INTEGER PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    volume BIGINT,
                    open FLOAT,
                    close FLOAT,
                    high FLOAT,
                    low FLOAT,
                    transactions INTEGER,
                    created_at TIMESTAMP
                )
            """))
            conn.execute(text("""
                INSERT INTO daily_aggregates_new 
                SELECT * FROM daily_aggregates
            """))
            conn.execute(text("DROP TABLE daily_aggregates"))
            conn.execute(text("ALTER TABLE daily_aggregates_new RENAME TO daily_aggregates"))
            conn.execute(text("CREATE INDEX ix_daily_aggregates_ticker ON daily_aggregates(ticker)"))
            conn.execute(text("CREATE INDEX ix_daily_aggregates_date ON daily_aggregates(date)"))
            conn.commit()
            logger.info("✓ Successfully migrated volume column to BIGINT")
        
        else:
            logger.error("Unknown database type")

if __name__ == '__main__':
    migrate()

