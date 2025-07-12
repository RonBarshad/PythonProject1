"""
data_processing/technical.py
Mission: This module provides functions to fetch, process, and engineer technical analysis features for stock data using yfinance and pandas-ta. It includes utilities to download OHLCV data, compute technical indicators, and prepare data for AI analysis and database insertion.
"""

import yfinance as yf
import pandas as pd
import ta  # https://github.com/twopirllc/pandas-ta
from datetime import datetime, timedelta
from config.config import get
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def get_stock_data(ticker: str, period: str = "6mo", interval: str = "1d", 
                   table: str = None, col_map: dict = None) -> tuple:
    """
    Mission: Download OHLCV data for a ticker, compute technical indicators, and prepare a tidy DataFrame for database insertion.
    Returns the DataFrame, table name, and column mapping.
    """
    # define the schema for an "empty" return
    empty_cols = [
        'company_ticker', 'event_date',
        'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'
    ]

    try:
        # 1. Download
        df = yf.download(ticker, interval=interval, period=period, auto_adjust=True)

        # 2. Fail early if nothing came back
        if df.empty:
            raise ValueError(f"No data returned for ticker {ticker!r}")

        # 3. If yfinance gave us a MultiIndex (ticker-level), drop that extra level
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # 4. Turn the index into a column and rename to 'event_date'
        df = df.reset_index().rename(columns={'Date': 'event_date'})
        df['event_date'] = pd.to_datetime(df['event_date']).dt.date

        # 5. Insert 'company_ticker' as the very first column
        df.insert(0, 'company_ticker', ticker)

        close = df["Close"]

        # Moving Averages
        df["SMA20"] = close.rolling(20).mean()
        df["SMA50"] = close.rolling(50).mean()
        df["SMA200"] = close.rolling(200).mean()
        df["EMA20"] = close.ewm(span=20, adjust=False).mean()

        # RSI (14-day)
        df["RSI14"] = ta.momentum.rsi(close, window=14)

        # MACD and signal line
        macd = ta.trend.macd(close, window_fast=12, window_slow=26)
        macd_signal = ta.trend.macd_signal(close, window_fast=12, window_slow=26, window_sign=9)
        df["MACD"] = macd
        df["MACD_signal"] = macd_signal
        df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

        # Optional helper columns for hand-drawn trendlines
        df["Swing_High_20"] = df["High"].rolling(20).max()
        df["Swing_Low_20"] = df["Low"].rolling(20).min()


        df = df.replace({np.nan: None})
        df = df.rename(columns=col_map)

        logging.info(f"Successfully processed technical data for {ticker}: {len(df)} rows")
        return df, table, col_map

    except Exception as e:
        # Log the problem and return an empty DataFrame with the right columns
        logging.error(f"[Error] get_stock_data({ticker!r}): {e}")
        return pd.DataFrame(columns=empty_cols), table, col_map

    finally:
        # Always runs, whether success or failure
        logging.info(f"[Info] get_stock_data completed for ticker={ticker!r}") 