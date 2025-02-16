from lib.models.MarketData import MarketData
from lib.models.EquityIndicators import EquityIndicators
from typing import List, Tuple
from sqlalchemy import select
from lib.db.session import create_db_session
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import pandas as pd

def get_ticker_data(db_session: Session, ticker: str) -> List[Tuple[MarketData, EquityIndicators]]:
    """
    Get combined market data and equity indicators for a specific ticker.
    
    Args:
        db_session: SQLAlchemy database session
        ticker: Stock ticker symbol
        
    Returns:
        List of tuples containing joined MarketData and EquityIndicators records
    """
    # Create a query that joins MarketData and EquityIndicators tables
    query = (
        select(MarketData, EquityIndicators)
        .join(
            EquityIndicators,
            (MarketData.ticker == EquityIndicators.ticker) &
            (MarketData.report_date == EquityIndicators.report_date)
        )
        .where(MarketData.ticker == ticker)
        .order_by(MarketData.report_date)
    )
    
    # Execute the query and return results
    result = db_session.execute(query).all()
    return result

def load_data(ticker: str):
    """Load and prepare data for the given ticker"""
    load_dotenv()
    
    db_context = create_db_session(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )
    
    with db_context() as session:
        data = get_ticker_data(session, ticker)
        
        if not data:
            return None
            
        # Convert to DataFrame
        records = []
        for market_data, indicators in data:
            record = {
                'date': market_data.report_date,
                'close': market_data.close,
                'open': market_data.open,  # Add open
                'high': market_data.high,  # Add high
                'low': market_data.low,    # Add low
                'volume': market_data.volume,  # Added volume
                'ema_20': indicators.ema_20,
                'ema_50': indicators.ema_50,
                'ema_200': indicators.ema_200
            }
            records.append(record)
            
        df = pd.DataFrame(records)
        df.set_index('date', inplace=True)
        return df
    
def save_labels(labels: dict, filename: str = "labels.csv"):
    """Save labels to a CSV file"""
    # Convert dictionary to DataFrame
    records = []
    for key, value in labels.items():
        record = {
            'key': key,
            'ticker': value['ticker'],
            'start_date': value['start_date'],
            'end_date': value['end_date'],
            'pattern': value['pattern'],
            'timestamp': value['timestamp']
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)