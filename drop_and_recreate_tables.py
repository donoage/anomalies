#!/usr/bin/env python3
"""
Drop and recreate all tables with correct schema
"""
from database import Base, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(db.engine)
    logger.info("✓ Tables dropped")
    
    logger.info("Creating all tables with new schema...")
    Base.metadata.create_all(db.engine)
    logger.info("✓ Tables created with BIGINT volume column")
    
    logger.info("\nDatabase is ready!")

if __name__ == '__main__':
    main()

