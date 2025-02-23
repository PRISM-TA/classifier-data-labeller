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
                'rsi_1': indicators.rsi_1,  # Add RSI 1
                'rsi_2': indicators.rsi_2,  # Add RSI 2
                'rsi_3': indicators.rsi_3,  # Add RSI 3
                'rsi_4': indicators.rsi_4,  # Add RSI 4
                'rsi_5': indicators.rsi_5,  # Add RSI 5
                'rsi_6': indicators.rsi_6,  # Add RSI 6
                'rsi_7': indicators.rsi_7,  # Add RSI 7
                'rsi_8': indicators.rsi_8,  # Add RSI 8
                'rsi_9': indicators.rsi_9,  # Add RSI 9
                'rsi_10': indicators.rsi_10,  # Add RSI 10
                'rsi_11': indicators.rsi_11,  # Add RSI 11
                'rsi_12': indicators.rsi_12,  # Add RSI 12
                'rsi_13': indicators.rsi_13,  # Add RSI 13
                'rsi_14': indicators.rsi_14,  # Add RSI 14
                'rsi_15': indicators.rsi_15,  # Add RSI 15
                'rsi_16': indicators.rsi_16,  # Add RSI 16
                'rsi_17': indicators.rsi_17,  # Add RSI 17
                'rsi_18': indicators.rsi_18,  # Add RSI 18
                'rsi_19': indicators.rsi_19,  # Add RSI 19
                'rsi_20': indicators.rsi_20,  # Add RSI 20
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