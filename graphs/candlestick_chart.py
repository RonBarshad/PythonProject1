"""
graphs/candlestick_chart.py
Mission: Generate candlestick charts for stock data visualization.
This module provides functions to create professional candlestick charts from stock data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import logging
from typing import Optional, List
import database.connection as db_connection
from config.config import get
import io
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def generate_candlestick_chart(ticker: str, days: int = 60) -> Optional[bytes]:
    """
    Generate a candlestick chart for a given ticker and return it as image data.
    
    This function:
    1. Fetches stock data from the database for the specified ticker
    2. Creates a professional candlestick chart using matplotlib
    3. Returns the chart as image bytes (no file saved to disk)
    
    Parameters:
    -----------
    ticker : str
        The stock ticker symbol (e.g., 'AAPL', 'MSFT')
    days : int, optional
        Number of days of data to include in the chart (default: 60)
        
    Returns:
    --------
    bytes or None
        Image data as bytes if successful, None if failed
        
    Example:
    --------
    >>> image_data = generate_candlestick_chart('AAPL', 60)
    >>> if image_data:
    >>>     # Use image_data directly in email or save to file
    >>>     with open('chart.png', 'wb') as f:
    >>>         f.write(image_data)
    """
    try:
        # Validate input
        if not ticker or not isinstance(ticker, str):
            logger.error("Invalid ticker provided")
            return None
            
        if days <= 0 or days > 365:
            logger.error("Days must be between 1 and 365")
            return None
        
        logger.info(f"Generating candlestick chart for {ticker} ({days} days)")
        
        # Step 1: Fetch data from database
        stock_data = _fetch_stock_data(ticker, days)
        if stock_data.empty:
            logger.error(f"No data found for ticker {ticker}")
            return None
        
        # Step 2: Create the candlestick chart
        image_data = _create_candlestick_chart(stock_data, ticker)
        
        if image_data:
            logger.info(f"✅ Candlestick chart generated successfully for {ticker}")
            return image_data
        else:
            logger.error("Failed to create candlestick chart")
            return None
            
    except Exception as e:
        logger.error(f"Error generating candlestick chart for {ticker}: {e}")
        return None

def _fetch_stock_data(ticker: str, days: int) -> pd.DataFrame:
    """
    Fetch stock data from the database for the specified ticker and time period.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    days : int
        Number of days of data to fetch
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing OHLCV data
    """
    try:
        # Get the table name from config
        table_name = get("database.table.daily_stock")
        
        # Fetch data using the existing database connection
        df = db_connection.get_data(ticker, table_name, days)
        
        if df.empty:
            logger.warning(f"No data found for {ticker} in the last {days} days")
            return df
        
        # Ensure we have the required columns
        required_columns = ['event_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return pd.DataFrame()
        
        # Sort by date to ensure chronological order
        df = df.sort_values('event_date')
        
        logger.info(f"Fetched {len(df)} records for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def _create_candlestick_chart(df: pd.DataFrame, ticker: str) -> Optional[bytes]:
    """
    Create a candlestick chart from the provided data and return as image bytes.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing OHLCV data
    ticker : str
        Stock ticker symbol for the chart title
        
    Returns:
    --------
    bytes or None
        Image data as bytes if successful, None if failed
    """
    try:
        # Set up the plot style
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Convert dates to matplotlib format
        dates = pd.to_datetime(df['event_date'])
        
        # Create candlestick chart
        _plot_candlesticks(ax, dates, df)
        
        # Customize the chart
        _customize_chart(ax, ticker, dates)
        
        # Save the chart to bytes buffer instead of file

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Get the image data as bytes
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
        
    except Exception as e:
        logger.error(f"Error creating candlestick chart: {e}")
        return None

def generate_candlestick_with_kpis(ticker: str, days: int, kpis: List[str]) -> Optional[bytes]:
    """Generate candlestick with KPI overlays and return as image bytes.

    KPI names must correspond to columns in `fact_ticker_daily_data`. Unknown
    columns are ignored gracefully.
    """
    try:
        df = _fetch_stock_data(ticker, days)
        if df.empty:
            return None

        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        dates = pd.to_datetime(df['event_date'])
        _plot_candlesticks(ax, dates, df)

        # Overlay KPIs as lines
        plotted = []
        for kpi in kpis:
            col = str(kpi).strip()
            if col in df.columns:
                ax.plot(dates, df[col], label=col, linewidth=1.3)
                plotted.append(col)

        _customize_chart(ax, ticker, dates)
        if plotted:
            ax.legend(loc='upper left', fontsize=9, frameon=False)

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error creating candlestick with KPIs: {e}")
        return None

def _plot_candlesticks(ax, dates, df):
    """
    Plot candlestick chart on the given axes.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        The axes to plot on
    dates : pandas.Series
        Date series for x-axis
    df : pd.DataFrame
        DataFrame containing OHLCV data
    """
    # Calculate candlestick properties
    opens = df['open_price']
    highs = df['high_price']
    lows = df['low_price']
    closes = df['close_price']
    
    # Determine colors for candlesticks
    colors = ['green' if close >= open else 'red' for open, close in zip(opens, closes)]
    
    # Plot candlesticks
    for i, (date, open_price, high, low, close, color) in enumerate(zip(dates, opens, highs, lows, closes, colors)):
        # Plot the body (rectangle)
        body_height = abs(close - open_price)
        body_bottom = min(open_price, close)
        
        ax.bar(date, body_height, bottom=body_bottom, width=0.6, 
               color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Plot the wick (line)
        ax.plot([date, date], [low, high], color='black', linewidth=1)
        
        # Add small horizontal lines at the ends of wicks
        ax.plot([date - timedelta(hours=2), date + timedelta(hours=2)], [low, low], 
                color='black', linewidth=1)
        ax.plot([date - timedelta(hours=2), date + timedelta(hours=2)], [high, high], 
                color='black', linewidth=1)

def _customize_chart(ax, ticker: str, dates):
    """
    Customize the chart appearance.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        The axes to customize
    ticker : str
        Stock ticker symbol for the title
    dates : pandas.Series
        Date series for x-axis formatting
    """
    # Set title
    ax.set_title(f'{ticker} Daily', fontsize=16, fontweight='bold', pad=20)
    
    # Set labels
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Set background color
    ax.set_facecolor('#f8f9fa')
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout() 