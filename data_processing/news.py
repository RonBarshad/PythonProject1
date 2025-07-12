"""
data_processing/news.py
Mission: This module handles company news data processing, including fetching news from APIs and processing sentiment analysis.
"""

import requests
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
from config.config import get
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def av_get_json(function: str, api_key: str, ticker: str) -> dict:
    """
    Mission: Fetch news data from Alpha Vantage API for a specific ticker.
    """
    try:
        url = f"https://www.alphavantage.co/query?function={function}&tickers={ticker}&apikey={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Alpha Vantage API call failed: {response.status_code}")
            return {}
            
    except Exception as e:
        logging.error(f"Error fetching news data for {ticker}: {e}")
        return {}


def news_to_df_single(
    feed: List[Dict[str, Any]],
    ticker: str,
    *,
    min_relevance: float = 0.20,
) -> pd.DataFrame:
    """
    Mission: Flatten Alpha Vantage NEWS_SENTIMENT payload for one ticker into a DataFrame.
    Filters out rows below the minimum relevance threshold and returns a DataFrame with relevant columns.
    """
    try:
        ticker = ticker.upper()
        rows: List[Dict[str, Any]] = []
        for art in feed:
            t_pub = art["time_published"]
            for ts in art["ticker_sentiment"]:
                if (
                    ts["ticker"].upper() == ticker
                    and float(ts["relevance_score"]) >= min_relevance
                ):
                    rows.append(
                        {
                            "time_published": t_pub,
                            "ticker": ticker,
                            "relevance_score": float(ts["relevance_score"]),
                            "sentiment_score": float(ts["ticker_sentiment_score"]),
                            "sentiment_label": ts["ticker_sentiment_label"],
                            "headline": art["title"],
                            "url": art["url"],
                            "source": art["source"],
                            "overall_sentiment_score": float(art["overall_sentiment_score"]),
                        }
                    )
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["time_published"] = (
            pd.to_datetime(df["time_published"], format="%Y%m%dT%H%M%S", utc=True)
            .dt.tz_localize(None)
        )
        df.drop_duplicates(subset=["ticker", "time_published", "url"], inplace=True)
        df.rename(columns={"time_published": "event_date"}, inplace=True)
        return df.reset_index(drop=True)
    except Exception as e:
        logging.error(f"Error processing news data for {ticker}: {e}")
        return pd.DataFrame()


def merge_dfs_no_dupes(dfs: list) -> pd.DataFrame:
    """
    Mission: Merge multiple DataFrames and remove duplicates.
    """
    try:
        if not dfs:
            return pd.DataFrame()
        
        # Concatenate all DataFrames
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates based on all columns to ensure no duplicate records
        merged_df = merged_df.drop_duplicates()
        
        return merged_df
        
    except Exception as e:
        logging.error(f"Error merging DataFrames: {e}")
        return pd.DataFrame() 