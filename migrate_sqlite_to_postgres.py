#!/usr/bin/env python3
"""
Migrate data from local SQLite to Railway PostgreSQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import DailyAggregate, LookupTable, Anomaly
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Source: SQLite
SQLITE_URL = 'sqlite:///anomalies.db'

# Target: Railway PostgreSQL
POSTGRES_URL = 'postgresql://postgres:DmIgtjgkgadzTxtzwEdALZgsMyMIGfTe@maglev.proxy.rlwy.net:52703/railway'

def migrate():
    logger.info("Connecting to SQLite (source)...")
    sqlite_engine = create_engine(SQLITE_URL)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()
    
    logger.info("Connecting to PostgreSQL (target)...")
    postgres_engine = create_engine(POSTGRES_URL)
    PostgresSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgresSession()
    
    try:
        # Migrate DailyAggregate
        logger.info("\n=== Migrating DailyAggregate ===")
        daily_aggs = sqlite_session.query(DailyAggregate).all()
        logger.info(f"Found {len(daily_aggs)} daily aggregates in SQLite")
        
        batch_size = 1000
        for i in range(0, len(daily_aggs), batch_size):
            batch = daily_aggs[i:i+batch_size]
            for agg in batch:
                # Check if exists
                existing = postgres_session.query(DailyAggregate).filter_by(
                    ticker=agg.ticker,
                    date=agg.date
                ).first()
                
                if not existing:
                    new_agg = DailyAggregate(
                        ticker=agg.ticker,
                        date=agg.date,
                        volume=agg.volume,
                        open=agg.open,
                        close=agg.close,
                        high=agg.high,
                        low=agg.low,
                        transactions=agg.transactions,
                        created_at=agg.created_at
                    )
                    postgres_session.add(new_agg)
            
            postgres_session.commit()
            logger.info(f"Migrated {min(i+batch_size, len(daily_aggs))}/{len(daily_aggs)} daily aggregates")
        
        logger.info("✓ DailyAggregate migration complete")
        
        # Migrate LookupTable
        logger.info("\n=== Migrating LookupTable ===")
        lookup_entries = sqlite_session.query(LookupTable).all()
        logger.info(f"Found {len(lookup_entries)} lookup table entries in SQLite")
        
        for i in range(0, len(lookup_entries), batch_size):
            batch = lookup_entries[i:i+batch_size]
            for entry in batch:
                # Check if exists
                existing = postgres_session.query(LookupTable).filter_by(
                    ticker=entry.ticker,
                    date=entry.date
                ).first()
                
                if not existing:
                    new_entry = LookupTable(
                        ticker=entry.ticker,
                        date=entry.date,
                        avg_transactions=entry.avg_transactions,
                        std_transactions=entry.std_transactions,
                        created_at=entry.created_at
                    )
                    postgres_session.add(new_entry)
            
            postgres_session.commit()
            logger.info(f"Migrated {min(i+batch_size, len(lookup_entries))}/{len(lookup_entries)} lookup entries")
        
        logger.info("✓ LookupTable migration complete")
        
        # Migrate Anomaly
        logger.info("\n=== Migrating Anomaly ===")
        anomalies = sqlite_session.query(Anomaly).all()
        logger.info(f"Found {len(anomalies)} anomalies in SQLite")
        
        for i in range(0, len(anomalies), batch_size):
            batch = anomalies[i:i+batch_size]
            for anomaly in batch:
                # Check if exists
                existing = postgres_session.query(Anomaly).filter_by(
                    ticker=anomaly.ticker,
                    date=anomaly.date
                ).first()
                
                if not existing:
                    new_anomaly = Anomaly(
                        ticker=anomaly.ticker,
                        date=anomaly.date,
                        transactions=anomaly.transactions,
                        avg_transactions=anomaly.avg_transactions,
                        std_transactions=anomaly.std_transactions,
                        z_score=anomaly.z_score,
                        close_price=anomaly.close_price,
                        volume=anomaly.volume,
                        created_at=anomaly.created_at
                    )
                    postgres_session.add(new_anomaly)
            
            postgres_session.commit()
            logger.info(f"Migrated {min(i+batch_size, len(anomalies))}/{len(anomalies)} anomalies")
        
        logger.info("✓ Anomaly migration complete")
        
        logger.info("\n" + "="*60)
        logger.info("MIGRATION COMPLETE!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        postgres_session.rollback()
        raise
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == '__main__':
    migrate()

