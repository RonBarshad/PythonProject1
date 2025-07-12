"""
data_processing/analysts.py
Mission: This module handles analyst rating data processing, including fetching analyst ratings from financial APIs and calculating average ratings for stocks.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from config.config import get
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

SCORE = {
    'strongBuy':   1,
    'buy':         0.75,
    'hold':        0.5,
    'sell':       0.25,
    'strongSell':  0
}

def avg_analyst_rating(tickers: list) -> pd.DataFrame:
    """
    Mission: Fetch analyst ratings for a list of tickers and calculate average ratings.
    Returns a DataFrame with ticker, event_date, and avg_rating columns.
    """
    all_results = []
    
    for ticker in tickers:
        try:
            # Fetch analyst rating data
            rating_data = fetch_analyst_rating(ticker)
            
            if rating_data:
                # Calculate average ratings for each period
                period_ratings = calculate_average_rating(rating_data, ticker)
                
                if not period_ratings.empty:
                    all_results.append(period_ratings)
                    logging.info(f"Processed analyst rating for {ticker}: {len(period_ratings)} periods")
                else:
                    logging.warning(f"No valid analyst rating data found for {ticker}")
            else:
                logging.warning(f"No analyst rating data found for {ticker}")
                
        except Exception as e:
            logging.error(f"Error processing analyst rating for {ticker}: {e}")
            continue
    
    # Combine all results
    if all_results:
        return pd.concat(all_results, ignore_index=True)
    else:
        return pd.DataFrame(data=[], columns=['company_ticker', 'event_date', 'avg_rating'])

def fetch_analyst_rating(ticker: str) -> list:
    """
    Mission: Fetch analyst rating data for a specific ticker from financial APIs.
    """
    try:
        # This is a placeholder for actual API call
        # In a real implementation, you would call a financial API here
        api_key = get("api_key_finnhub")  # or other API key
        
        # Example API call (replace with actual implementation)
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else []
        else:
            logging.error(f"API call failed for {ticker}: {response.status_code}")
            return []
            
    except Exception as e:
        logging.error(f"Error fetching analyst rating for {ticker}: {e}")
        return []

def calculate_average_rating(rating_data: list, ticker: str) -> pd.DataFrame:
    """
    Mission: Calculate average analyst rating from rating data for each period.
    Returns a DataFrame with company_ticker, event_date, and avg_rating columns.
    """
    try:
        results = []
        
        # rating_data is a list of dictionaries, each containing period data
        for period_data in rating_data:
            if not isinstance(period_data, dict):
                continue
                
            period = period_data.get('period')
            if not period:
                continue
            
            # Calculate weighted average for this period
            total_weight = 0
            weighted_sum = 0
            
            for rating_type, count in period_data.items():
                if rating_type in SCORE and isinstance(count, (int, float)):
                    weighted_sum += count * SCORE[rating_type]
                    total_weight += count
            
            if total_weight > 0:
                avg_rating = weighted_sum / total_weight
                
                # Convert period string to date
                try:
                    event_date = datetime.strptime(period, '%Y-%m-%d').date()
                except ValueError:
                    # Try different date format if needed
                    event_date = datetime.now().date()
                
                results.append({
                    'company_ticker': ticker,
                    'event_date': event_date,
                    'avg_rating': avg_rating
                })
        
        return pd.DataFrame(results)
        
    except Exception as e:
        logging.error(f"Error calculating average rating: {e}")
        return pd.DataFrame(data=[], columns=['company_ticker', 'event_date', 'avg_rating']) 