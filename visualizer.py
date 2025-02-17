import streamlit as st
from lib.db.session import create_db_session
from lib.models.MarketData import MarketData
from lib.models.EquityIndicators import EquityIndicators
from lib.models.SupervisedClassifierDataset import SupervisedClassifierDataset

from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
import pandas as pd

def get_data(db_session: Session, ticker: str) -> tuple[List[Tuple], List[SupervisedClassifierDataset]]:
    """Get market data and labels for a specific ticker."""
    # Market data query
    market_query = (
        select(MarketData, EquityIndicators)
        .join(
            EquityIndicators,
            (MarketData.ticker == EquityIndicators.ticker) &
            (MarketData.report_date == EquityIndicators.report_date)
        )
        .where(MarketData.ticker == ticker)
        .order_by(MarketData.report_date)
    )
    
    # Labels query
    labels_query = (
        select(SupervisedClassifierDataset)
        .where(SupervisedClassifierDataset.ticker == ticker)
        .order_by(SupervisedClassifierDataset.start_date)
    )
    
    market_data = db_session.execute(market_query).all()
    labels = db_session.execute(labels_query).scalars().all()
    
    return market_data, labels

def prepare_data(market_data, labels):
    """Prepare market data and labels for plotting."""
    # Convert market data to DataFrame
    records = []
    for market, indicators in market_data:
        record = {
            'date': market.report_date,
            'close': market.close,
            'open': market.open,
            'high': market.high,
            'low': market.low,
            'volume': market.volume,
            'ema_20': indicators.ema_20,
            'ema_50': indicators.ema_50,
            'ema_200': indicators.ema_200
        }
        records.append(record)
    
    market_df = pd.DataFrame(records)
    market_df.set_index('date', inplace=True)
    
    # Convert labels to DataFrame
    labels_df = pd.DataFrame([{
        'start_date': label.start_date,
        'end_date': label.end_date,
        'label': label.label
    } for label in labels])
    
    return market_df, labels_df

def plot_data(market_df: pd.DataFrame, labels_df: pd.DataFrame, ticker: str, start_idx: int, window_size: int = 100):
    """Create a plot with market data and labels."""
    # Get the window of data to display
    window_df = market_df.iloc[start_idx:start_idx + window_size]
    
    # Create figure with subplots
    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.6, 0.2, 0.2],
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
            name='OHLC'
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
                line=dict(color=colors[ema], width=1)
            ),
            row=1, col=1
        )
    
    # Add volume
    colors = ['red' if row['close'] < row['open'] else 'green' 
             for _, row in window_df.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=window_df.index,
            y=window_df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.3
        ),
        row=2, col=1
    )
    
    # Add labels visualization: use end_date labels
    if not labels_df.empty:
        window_start_date = window_df.index[0]
        window_end_date = window_df.index[-1]
        
        # Filter labels where end_date falls within our window
        window_labels = labels_df[
            (labels_df['end_date'] >= window_start_date) & 
            (labels_df['end_date'] <= window_end_date)
        ].copy()
        
        label_colors = {
            0: 'red',    # downtrend
            1: 'gray',   # sideways
            2: 'green'   # uptrend
        }
        
        # Create points for each end_date
        for _, row in window_labels.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row['end_date']],
                    y=[row['label']],
                    mode='markers',
                    marker=dict(
                        color=label_colors[row['label']],
                        size=10
                    ),
                    showlegend=False  # Remove from legend
                ),
                row=3, col=1
            )
    
    # Update layout
    fig.update_layout(
        title=f'{ticker} Price, Volume, and Labels (Days {start_idx} to {start_idx + window_size})',
        height=1000,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    # Update axes labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="Labels", row=3, col=1)
    
    # Update grids
    for i in range(1, 4):
        fig.update_xaxes(showgrid=True, gridcolor='lightgrey', gridwidth=0.5, row=i, col=1)
        fig.update_yaxes(showgrid=True, gridcolor='lightgrey', gridwidth=0.5, row=i, col=1)
    
    # Set y-axis range and ticks for labels, only showing on right side
    fig.update_yaxes(
        range=[-0.5, 2.5], 
        tickmode='array', 
        tickvals=[0, 1, 2],
        title_text='Labels',  
        side='left',     # Move ticks to right side
        showgrid=True,
        row=3, col=1
    )
    
    return fig

def main():
    st.set_page_config(layout="wide")
    st.title("Stock Data Visualization with Labels")

    # Initialize session state for current index if it doesn't exist
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = 0

    # Sidebar for ticker input
    with st.sidebar:
        ticker = st.text_input("Enter Ticker Symbol:", value="MSFT").upper()
        st.write("Label Legend:")
        st.markdown("🔴 0 = Downtrend")
        st.markdown("⚫ 1 = Sideways")
        st.markdown("🟢 2 = Uptrend")
        
        window_size = st.slider("Window Size (days)", min_value=50, max_value=200, value=100)

    load_dotenv()

    db_config = {
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD"),
        'host': os.getenv("DB_HOST"),
        'database': os.getenv("DB_NAME"),
        'port': os.getenv("DB_PORT", "5432")
    }

    try:
        db_context = create_db_session(
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database']
        )
        
        with db_context() as session:
            market_data, labels = get_data(session, ticker)
            
            if market_data:
                market_df, labels_df = prepare_data(market_data, labels)
                
                # Navigation controls
                col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
                
                with col1:
                    if st.button("⏮️ Start"):
                        st.session_state.current_idx = 0
                
                with col2:
                    if st.button("⬅️ Previous") and st.session_state.current_idx >= window_size:
                        st.session_state.current_idx -= window_size
                
                with col3:
                    st.write(f"Showing days {st.session_state.current_idx} to {st.session_state.current_idx + window_size}")
                
                with col4:
                    if st.button("Next ➡️") and st.session_state.current_idx + window_size < len(market_df):
                        st.session_state.current_idx += window_size
                
                # Display data statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Market Data Points", len(market_data))
                with col2:
                    st.metric("Total Labels", len(labels))

                # Create and display plot
                fig = plot_data(market_df, labels_df, ticker, st.session_state.current_idx, window_size)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display label distribution if there are labels
                if not labels_df.empty:
                    st.subheader("Label Distribution")
                    label_counts = labels_df['label'].value_counts().sort_index()
                    label_names = {0: "Downtrend", 1: "Sideways", 2: "Uptrend"}
                    cols = st.columns(3)
                    for i, (label, count) in enumerate(label_counts.items()):
                        with cols[i]:
                            st.metric(label_names[label], count)
                
            else:
                st.error(f"No data found for ticker {ticker}")

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()