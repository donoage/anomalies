from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from config import Config

Base = declarative_base()

class Anomaly(Base):
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    trades = Column(Integer, nullable=False)
    avg_trades = Column(Float, nullable=False)
    std_trades = Column(Float, nullable=False)
    z_score = Column(Float, nullable=False)
    close_price = Column(Float)
    price_diff = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'date': self.date.isoformat() if self.date else None,
            'trades': self.trades,
            'avg_trades': round(self.avg_trades, 2),
            'std_trades': round(self.std_trades, 2),
            'z_score': round(self.z_score, 2),
            'close_price': round(self.close_price, 2) if self.close_price else None,
            'price_diff': round(self.price_diff, 2) if self.price_diff else None,
            'volume': self.volume,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DailyAggregate(Base):
    __tablename__ = 'daily_aggregates'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    volume = Column(Integer)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    transactions = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'ticker': self.ticker,
            'date': self.date.isoformat() if self.date else None,
            'volume': self.volume,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'transactions': self.transactions
        }


class LookupTable(Base):
    __tablename__ = 'lookup_table'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    avg_trades = Column(Float)
    std_trades = Column(Float)
    close_price = Column(Float)
    price_diff = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def get_session(self):
        return self.Session()
    
    def close_session(self):
        self.Session.remove()


# Global database instance
db = Database()

