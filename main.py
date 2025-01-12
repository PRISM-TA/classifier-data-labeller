from lib.db.session import create_db_session
from lib.models.MarketData import MarketData
from lib.models.EquityIndicators import EquityIndicators

from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime


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

def plot_price_and_ema(df: pd.DataFrame, ticker: str, start_idx: int, window_size: int = 20):
    window_df = df.iloc[start_idx:start_idx + window_size]
    
    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        shared_xaxes=True
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=window_df.index,
            open=window_df['open'],
            high=window_df['high'],
            low=window_df['low'],
            close=window_df['close'],
            name='OHLC',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add EMAs
    colors = {
        'ema_20': '#FF4500',
        'ema_50': '#9370DB',
        'ema_200': '#CD853F'
    }
    
    for ema in ['ema_20', 'ema_50', 'ema_200']:
        fig.add_trace(
            go.Scatter(
                x=window_df.index,
                y=window_df[ema],
                name=ema.upper(),
                line=dict(color=colors[ema], width=1),
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Add volume bars
    colors = ['red' if row['close'] < row['open'] else 'green' 
             for _, row in window_df.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=window_df.index,
            y=window_df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.3,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{ticker} Price and EMAs',
            font=dict(size=24)
        ),
        plot_bgcolor='white',
        height=800,
        margin=dict(t=50, b=30),
        xaxis_rangeslider_visible=False  # Disable rangeslider
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Update x-axis
    fig.update_xaxes(
        showgrid=True,
        gridcolor='lightgrey',
        gridwidth=0.5,
        row=2, col=1
    )
    
    # Update y-axes grids
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgrey',
        gridwidth=0.5,
        row=1, col=1
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgrey',
        gridwidth=0.5,
        row=2, col=1
    )
    
    return fig

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

def load_labels(filename: str = "labels.csv") -> dict:
    """Load labels from a CSV file"""
    try:
        df = pd.read_csv(filename)
        # Convert DataFrame back to dictionary
        labels = {}
        for _, row in df.iterrows():
            key = row['key']
            labels[key] = {
                'ticker': row['ticker'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'pattern': row['pattern'],
                'timestamp': row['timestamp']
            }
        return labels
    except FileNotFoundError:
        return {}

def find_earliest_unlabeled_index(df: pd.DataFrame, labels: dict, ticker: str) -> int:
    """Find the earliest unlabeled date index in the dataframe"""
    for idx, date in enumerate(df.index):
        key = f"{ticker}_{date.strftime('%Y-%m-%d')}"
        if key not in labels:
            return idx
    return 0  # Return 0 if all dates are labeled

def main():
    # Initialize session state
    if 'current_idx' not in st.session_state:
        st.session_state['current_idx'] = 0
    if 'df' not in st.session_state:
        st.session_state['df'] = None
    if 'max_idx' not in st.session_state:
        st.session_state['max_idx'] = 0
    if 'labels' not in st.session_state:
        st.session_state['labels'] = load_labels()
    if 'current_ticker' not in st.session_state:
        st.session_state['current_ticker'] = None

    def get_nearby_labels(current_date, ticker, window=5):
        """Get labels for dates before and after the current date"""
        current_idx = st.session_state['df'].index.get_loc(current_date)
        start_idx = max(0, current_idx - window)
        end_idx = min(len(st.session_state['df']), current_idx + window + 1)
        
        nearby_dates = st.session_state['df'].index[start_idx:end_idx]
        nearby_labels = {}
        
        for date in nearby_dates:
            key = f"{ticker}_{date.strftime('%Y-%m-%d')}"
            if key in st.session_state['labels']:
                nearby_labels[date] = st.session_state['labels'][key]['pattern']
        
        return nearby_labels

    # Create containers
    graph_container = st.container()
    input_container = st.container()
    
    with input_container:
        st.title('Stock Price Pattern Labeling')
        ticker = st.text_input('Enter ticker symbol:', 'AAPL').upper()
    
    if st.button('Show Data') or (ticker != st.session_state['current_ticker'] and st.session_state['current_ticker'] is not None):
        df = load_data(ticker)
        if df is not None:
            st.session_state['df'] = df
            st.session_state['max_idx'] = len(df) - 20
            st.session_state['current_ticker'] = ticker
            
            # Find the earliest unlabeled date
            earliest_unlabeled = find_earliest_unlabeled_index(df, st.session_state['labels'], ticker)
            st.session_state['current_idx'] = earliest_unlabeled
            
            # Show information about where we're starting
            if earliest_unlabeled > 0:
                st.info(f"Continuing from the earliest unlabeled date: {df.index[earliest_unlabeled].strftime('%Y-%m-%d')}")
    
    # Display the graph
    with graph_container:
        if st.session_state['df'] is not None:

            # Display the plot
            fig = plot_price_and_ema(
                st.session_state['df'],
                ticker,
                st.session_state['current_idx']
            )
            st.plotly_chart(fig, use_container_width=True)
            
            start_date = st.session_state['df'].index[st.session_state['current_idx']].strftime('%Y-%m-%d')
            end_date = st.session_state['df'].index[
                min(st.session_state['current_idx'] + 19, len(st.session_state['df']) - 1)
            ].strftime('%Y-%m-%d')
            
            # Show progress information
            total_days = len(st.session_state['df'])
            labeled_days = sum(1 for date in st.session_state['df'].index 
                             if f"{ticker}_{date.strftime('%Y-%m-%d')}" in st.session_state['labels'])
            progress = (labeled_days / total_days) * 100
            
            st.info(f'Window: {start_date} to {end_date} | Progress: {labeled_days}/{total_days} ({progress:.1f}%)')

            # Get current label if it exists
            key = f"{ticker}_{start_date}"
            current_label = st.session_state['labels'].get(key, None)
            if current_label:
                st.write(f"Current label: {current_label['pattern']}")

            # Labeling buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button('⬆️ Uptrend', key='uptrend'):
                    st.session_state['labels'][key] = {
                        'ticker': ticker,
                        'start_date': start_date,
                        'end_date': end_date,
                        'pattern': 'uptrend',
                        'timestamp': datetime.now().isoformat()
                    }
                    save_labels(st.session_state['labels'])
                    if not current_label:  # Only auto-advance if this was a new label
                        next_unlabeled = find_earliest_unlabeled_index(
                            st.session_state['df'],
                            st.session_state['labels'],
                            ticker
                        )
                        st.session_state['current_idx'] = min(next_unlabeled, st.session_state['max_idx'])
                    st.rerun()

            with col2:
                if st.button('➡️ Sideways', key='sideways'):
                    st.session_state['labels'][key] = {
                        'ticker': ticker,
                        'start_date': start_date,
                        'end_date': end_date,
                        'pattern': 'sideways',
                        'timestamp': datetime.now().isoformat()
                    }
                    save_labels(st.session_state['labels'])
                    if not current_label:
                        next_unlabeled = find_earliest_unlabeled_index(
                            st.session_state['df'],
                            st.session_state['labels'],
                            ticker
                        )
                        st.session_state['current_idx'] = min(next_unlabeled, st.session_state['max_idx'])
                    st.rerun()

            with col3:
                if st.button('⬇️ Downtrend', key='downtrend'):
                    st.session_state['labels'][key] = {
                        'ticker': ticker,
                        'start_date': start_date,
                        'end_date': end_date,
                        'pattern': 'downtrend',
                        'timestamp': datetime.now().isoformat()
                    }
                    save_labels(st.session_state['labels'])
                    if not current_label:
                        next_unlabeled = find_earliest_unlabeled_index(
                            st.session_state['df'],
                            st.session_state['labels'],
                            ticker
                        )
                        st.session_state['current_idx'] = min(next_unlabeled, st.session_state['max_idx'])
                    st.rerun()

            # Add delete button for existing labels
            if current_label:
                if st.button('🗑️ Delete Label'):
                    del st.session_state['labels'][key]
                    save_labels(st.session_state['labels'])
                    st.rerun()

            # Historical labels display with compact layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader('Nearby Labels')
                current_date = st.session_state['df'].index[st.session_state['current_idx']]
                nearby_labels = get_nearby_labels(current_date, ticker)
                
                if nearby_labels:
                    history_df = pd.DataFrame(
                        [(date.strftime('%Y-%m-%d'), pattern) for date, pattern in nearby_labels.items()],
                        columns=['Date', 'Pattern']
                    )
                    # Create a style function that checks the date directly
                    def highlight_current(row):
                        if row['Date'] == current_date.strftime('%Y-%m-%d'):
                            return ['background-color: yellow'] * len(row)
                        return [''] * len(row)
                    
                    st.dataframe(
                        history_df.style.apply(highlight_current, axis=1),
                        height=200
                    )
                else:
                    st.write("No nearby labels found")
            
            with col2:
                st.subheader('Quick Jump')
                all_labeled_dates = [
                    date for date in st.session_state['df'].index
                    if f"{ticker}_{date.strftime('%Y-%m-%d')}" in st.session_state['labels']
                ]
                
                if all_labeled_dates:
                    selected_date = st.selectbox(
                        'Jump to labeled date:',
                        options=all_labeled_dates,
                        format_func=lambda x: x.strftime('%Y-%m-%d'),
                        index=0
                    )
                    
                    if st.button('Jump'):
                        selected_idx = st.session_state['df'].index.get_loc(selected_date)
                        st.session_state['current_idx'] = selected_idx
                        st.rerun()

            # Display current statistics
            st.subheader('Labeling Statistics')
            if st.session_state['labels']:
                labels_df = pd.DataFrame(st.session_state['labels'].values())
                ticker_labels = labels_df[labels_df['ticker'] == ticker]
                stats = ticker_labels['pattern'].value_counts()
                st.write(f"Total labels for {ticker}: {len(ticker_labels)}")
                st.write("Pattern distribution:")
                st.write(stats)

if __name__ == "__main__":
    main()