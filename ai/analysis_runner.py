"""
ai/analysis_runner.py
Mission: This module provides functions to run AI analysis on stock data for multiple tickers and data sources (technical, analysts, news). It fetches data from the database, runs AI analysis using OpenAI, and collects results in a DataFrame matching the ai_analysis table schema.
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import json
from datetime import datetime
from config.config import get
import ai.connector as gpt_connector
import database.models as models
import database.connection as db_connection
import logging
import time
from typing import Dict, Any, List, Optional
import ast
import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)
from utils.metrics import api_calls, api_duration

def get_db_credentials() -> Dict[str, str]:
    """Get database credentials from config."""
    return {
        'host': get("database.host"),
        'user': get("database.user"),
        'password': get("database.password"),
        'database': get("database.name")
    }

def replace_nan_with_none(obj):
    """Recursively replace NaN values with None in nested structures."""
    if isinstance(obj, float) and obj != obj:  # NaN check
        return None
    elif isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(item) for item in obj]
    else:
        return obj

def parse_text_analysis_column(x):
    """Parse text analysis column to extract structured data."""
    if isinstance(x, str) and x.strip().startswith('{'):
        try:
            return ast.literal_eval(x)
        except Exception:
            return x  # Keep as is if parsing fails
    return x  # Keep as is for all other cases

def _run_openai_analysis(system_message: str, user_message: str, model: str):
    """
    Mission: Run an AI analysis using OpenAI API with the given system and user messages. Returns score, explanation, prompt_tokens, execution_tokens.
    """
    client = OpenAI(api_key=get('api_key_gpt'))
    try:
        t0 = time.perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            max_tokens=256
        )
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info("openai_ok", extra={"op": "chat.completions", "duration_ms": round(duration_ms, 2)})
        try:
            api_calls.labels(service="openai", op="chat.completions").inc()
            api_duration.labels(service="openai", op="chat.completions").observe(duration_ms)
        except Exception:
            pass
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        execution_tokens = usage.completion_tokens if usage else 0
        # Get the response content
        content = response.choices[0].message.content
        
        # Try to parse the response as JSON first
        try:
            if content is None:
                score = float('nan')
                explanation = "No response received"
            else:
                parsed_response = json.loads(content)
                if isinstance(parsed_response, dict):
                    score = parsed_response.get('score', float('nan'))
                    explanation = parsed_response.get('explanation', content)
                else:
                    score = float('nan')
                    explanation = content
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, try the existing parse_text_analysis_column function
            parsed_response = parse_text_analysis_column(content)
            if isinstance(parsed_response, dict):
                score = parsed_response.get('score', float('nan'))
                explanation = parsed_response.get('explanation', content)
            else:
                score = float('nan')
                explanation = content
            
        return score, explanation, prompt_tokens, execution_tokens
    except Exception as e:
        logger.error(f"OpenAI analysis error: {e}")
        return float('nan'), str(e), 0, 0

def run_ai_analysis_for_tickers(
    tickers: list[str],
    window: int
) -> pd.DataFrame:
    """
    Mission: For each ticker and each data source (technical, analysts, news), fetch data, run AI analysis, and collect results in a DataFrame matching the ai_analysis table schema.
    User can override model_map, system_message_map, and table_map; defaults are used if not provided.
    """
    # Convert single string ticker to list if needed
    if isinstance(tickers, str):
        tickers = [tickers]
        logging.info(f"Converted single ticker string to list: {tickers}")
    
    results = []
    now = datetime.now()

    # 1) Define model, system_message, and table maps
    model_map = {
        'technical_analysis': get('technical_analysis.model'),
        'analysts_rating': get('analyst_opinion.model'),
        'news_analysis': get('news_analysis.model'),
    }

    system_message_map = {
        'technical_analysis': get('technical_analysis.system_message'),
        'analysts_rating': get('analyst_opinion.system_message'),
        'news_analysis': get('news_analysis.system_message'),
    }

    table_map = {
        'technical_analysis': get('database.table.daily_stock'),
        'analysts_rating': get('database.table.analyst_rating'),
        'news_analysis': get('database.table.news_rating'),
    }

    # 2) Get data from DB
    for ticker in tickers:
        for analysis_type, table in table_map.items():
            df = db_connection.get_data(ticker, table, window)
            if df.empty:
                continue
            # Use the most recent event_date for this analysis
            event_date = df['event_date'].max() if 'event_date' in df.columns else now
            user_message = df.to_json(orient='records')
            if user_message is None:
                continue
            system_message = system_message_map[analysis_type]
            model = model_map[analysis_type]
            score, explanation, prompt_tokens, execution_tokens = _run_openai_analysis(system_message, user_message, model)
            results.append({
                'event_date': str(event_date),
                'insertion_time': now.isoformat(sep=' '),
                'company_ticker': ticker,
                'analysis_type': analysis_type,
                'weight': None,
                'grade': score,
                'text_analysis': explanation,
                'AI_model': model,
                'prompt_tokens': prompt_tokens,
                'execution_tokens': execution_tokens
            })
    
    # 3) Parse the results
    nan = float('nan')
    # Step 1: Create DataFrame
    df = pd.DataFrame(results)
    
    # Check if DataFrame is empty (no data found)
    if df.empty:
        logging.warning("No AI analysis results found - DataFrame is empty")
        return df
    
    # Step 2: Parse text_analysis column
    df['parsed'] = df['text_analysis'].apply(parse_text_analysis_column)
    # Step 3: Extract 'score' and 'explanation' if parsed is a dict
    df['grade'] = df['parsed'].apply(lambda d: d.get('score') if isinstance(d, dict) else None)
    df['text_analysis'] = df['parsed'].apply(lambda d: d.get('explanation') if isinstance(d, dict) else d)
    # Step 4: Drop the helper column
    df = df.drop(columns=['parsed'])
    
    # Step 5: Replace NaN with None at the end
    df = df.where(pd.notnull(df), None)
    
    return df

def _fetch_ai_analysis_data(ticker: str, table_name: str, window: int) -> pd.DataFrame:
    """
    Mission: Fetch AI analysis data for a specific ticker from the ai_analysis table.
    """
    creds = get_db_credentials()
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        
        # Query to get data for the ticker within the time window
        query = f"""
        SELECT event_date, company_ticker, analysis_type, grade, text_analysis
        FROM {table_name}
        WHERE company_ticker = %s
        AND event_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY event_date DESC
        """
        
        cursor.execute(query, (ticker, window))
        rows = cursor.fetchall()
        
        if cursor.description:
            columns = [str(d[0]) for d in cursor.description]
            df = pd.DataFrame(rows, columns=pd.Index(columns))
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logging.error(f"Database error fetching data for {ticker}: {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def _create_consolidated_system_message(weights: dict) -> str:
    """
    Mission: Create a system message for consolidated analysis that includes weights.
    """
    return get("system_message_last") + "\n" + f"  - weights: {weights}"

def run_consolidated_ai_analysis(
    tickers: list[str],
    window: int,
    model: str = "gpt-3.5-turbo"
) -> pd.DataFrame:
    """
    Mission: For each ticker, fetch AI analysis data from the ai_analysis table for the given time window,
    consolidate all analysis types for each ticker, and run a final AI analysis with weights.
    
    Parameters:
    -----------
    tickers : list[str]
        List of stock tickers to analyze
    window : int
        Time window in days to fetch data
    model : str
        GPT model to use for analysis (default: gpt-3.5-turbo)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with consolidated analysis results for each ticker
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    results = []
    now = datetime.now()
    
    # Get weights from config
    weights = get("deffualt_weights")
    
    # Get table name
    table_name = get("database.other_tables.ai_analysis")
    
    for ticker in tickers:
        try:
            # Fetch data for this ticker from ai_analysis table
            df = _fetch_ai_analysis_data(ticker, table_name, window)
            
            if df.empty:
                logging.warning(f"No AI analysis data found for ticker {ticker}")
                continue
            
            # Prepare data for GPT analysis
            user_message = df.to_json(orient='records')
            if user_message is None:
                continue
            
            # Create system message with weights
            system_message = _create_consolidated_system_message(weights)
            
            # Run OpenAI analysis
            score, explanation, prompt_tokens, execution_tokens = _run_openai_analysis(
                system_message, user_message, model
            )
            
            # Get the most recent event_date from the data
            event_date = df['event_date'].max() if 'event_date' in df.columns else now
            
            results.append({
                'event_date': str(event_date),
                'insertion_time': now.isoformat(sep=' '),
                'company_ticker': ticker,
                'analysis_type': 'all',
                'weight': json.dumps(weights),
                'grade': score,
                'text_analysis': explanation,
                'AI_model': model,
                'prompt_tokens': prompt_tokens,
                'execution_tokens': execution_tokens
            })
            
            logging.info(f"Completed consolidated analysis for {ticker}")
            
        except Exception as e:
            logging.error(f"Error processing ticker {ticker}: {e}")
            continue
    
    # Create DataFrame from results
    if results:
        df = pd.DataFrame(results)
        df = df.where(pd.notnull(df), None)
        return df
    else:
        return pd.DataFrame()

def run_consolidated_analysis_process():
    """
    Mission: Run consolidated AI analysis for all tickers using the new consolidated analysis function.
    This will fetch existing AI analysis data and create a final weighted analysis for each ticker.
    """
    try:
        # Get configuration
        tickers = get("tickers")
        window = get("technical_analysis.window_day")  # Use same window as technical analysis
        model = get("technical_analysis.model")  # Use same model as technical analysis
        
        print(f"Running consolidated AI analysis for tickers: {tickers}")
        print(f"Window: {window} days, Model: {model}")
        
        # Run the consolidated analysis
        consolidated_df = run_consolidated_ai_analysis(tickers, window, model)
        
        if not consolidated_df.empty:
            print("\nConsolidated AI Analysis Results:")
            print("=" * 50)
            print(consolidated_df)
            
            # Print summary for each ticker
            print("\nSummary by Ticker:")
            print("-" * 30)
            for _, row in consolidated_df.iterrows():
                print(f"{row['company_ticker']}: Grade {row['grade']:.3f} - {row['text_analysis'][:100]}...")
        else:
            print("No consolidated analysis results found.")
            
        return consolidated_df
        
    except Exception as e:
        logging.error(f"Consolidated analysis process failed: {e}")
        return pd.DataFrame()

# Legacy functions for backward compatibility
def parse_ai_response(response_text: str) -> Dict[str, Any]:
    """Parse AI response text into a structured dictionary."""
    try:
        # Try to parse as JSON first
        if response_text.strip().startswith('{'):
            return json.loads(response_text)
        
        # If not JSON, try to extract grade and analysis
        lines = response_text.strip().split('\n')
        result = {'grade': 0.5, 'analysis': response_text}
        
        for line in lines:
            line = line.strip().lower()
            if 'grade:' in line or 'score:' in line or 'rating:' in line:
                try:
                    # Extract numeric value
                    import re
                    numbers = re.findall(r'\d+\.?\d*', line)
                    if numbers:
                        grade = float(numbers[0])
                        if 0 <= grade <= 1:
                            result['grade'] = grade
                except:
                    pass
        
        return result
        
    except Exception as e:
        logging.error(f"Error parsing AI response: {e}")
        return {'grade': None, 'analysis': response_text}

def insert_ai_analysis(ticker: str, analysis_type: str, weights: Optional[Dict[str, Optional[float]]], 
                      grade: Optional[float], text_analysis: str, model: str, 
                      prompt_tokens: int, completion_tokens: int) -> None:
    """Insert AI analysis results into the database."""
    creds = get_db_credentials()
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        
        # Convert weights dict to JSON string
        weights_json = json.dumps(weights) if weights else None
        
        # Handle None grade
        grade_value = grade if grade is not None else 0.0
        
        insert_query = """
        INSERT INTO ai_analysis 
        (event_date, insertion_time, company_ticker, analysis_type, wights, 
         grade, text_analysis, AI_model, prompt_tokens, excution_tokens)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            datetime.now(),
            datetime.now(),
            ticker,
            analysis_type,
            weights_json,
            grade_value,
            text_analysis,
            model,
            prompt_tokens,
            completion_tokens
        ))
        
        conn.commit()
        logging.info(f"Inserted AI analysis for {ticker} - {analysis_type}")
        
    except Error as e:
        logging.error(f"Database error inserting AI analysis: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def run_single_analysis(ticker: str, analysis_type: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Run a single type of analysis for a ticker."""
    try:
        # Get data from database
        prices_df, analyst_df, news_df = models.get_most_recent_data(ticker)
        
        if prices_df.empty and analyst_df.empty and news_df.empty:
            logging.warning(f"No data found for ticker {ticker}")
            return {}
        
        # Prepare data for analysis
        dfs = []
        names = []
        
        if not prices_df.empty:
            dfs.append(prices_df)
            names.append("stock_prices")
        
        if not analyst_df.empty:
            dfs.append(analyst_df)
            names.append("analyst_ratings")
        
        if not news_df.empty:
            dfs.append(news_df)
            names.append("news_data")
        
        # Convert to JSON
        data_json = models.dfs_list_to_json(dfs, names)
        
        # Run AI analysis
        result = gpt_connector.analyze_with_gpt(data_json, analysis_type, model)
        
        if result['response'].startswith('Error:'):
            logging.error(f"AI analysis failed for {ticker}: {result['response']}")
            return {}
        
        # Parse response
        parsed_result = parse_ai_response(result['response'])
        
        # Store results
        insert_ai_analysis(
            ticker=ticker,
            analysis_type=analysis_type,
            weights=None,  # Set weight to None
            grade=parsed_result.get('grade', None),
            text_analysis=parsed_result.get('analysis', result['response']),
            model=model,
            prompt_tokens=result['prompt_tokens'],
            completion_tokens=result['completion_tokens']
        )
        
        return {
            'ticker': ticker,
            'analysis_type': analysis_type,
            'grade': parsed_result.get('grade', None),
            'analysis': parsed_result.get('analysis', result['response']),
            'tokens_used': result['total_tokens']
        }
        
    except Exception as e:
        logging.error(f"Error in run_single_analysis for {ticker}: {e}")
        return {}

def run_consolidated_analysis(ticker: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Run consolidated analysis combining multiple analysis types."""
    try:
        # Get data from database
        prices_df, analyst_df, news_df = models.get_most_recent_data(ticker)
        
        if prices_df.empty and analyst_df.empty and news_df.empty:
            logging.warning(f"No data found for ticker {ticker}")
            return {}
        
        # Prepare data for analysis
        dfs = []
        names = []
        
        if not prices_df.empty:
            dfs.append(prices_df)
            names.append("stock_prices")
        
        if not analyst_df.empty:
            dfs.append(analyst_df)
            names.append("analyst_ratings")
        
        if not news_df.empty:
            dfs.append(news_df)
            names.append("news_data")
        
        # Convert to JSON
        data_json = models.dfs_list_to_json(dfs, names)
        
        # Get consolidated system message
        system_message = get("consolidated_analysis.system_message")
        if not system_message:
            logging.error("No consolidated analysis system message configured")
            return {}
        
        # Run AI analysis
        result = gpt_connector.send_to_gpt(system_message, data_json, model)
        
        if result['response'].startswith('Error:'):
            logging.error(f"Consolidated analysis failed for {ticker}: {result['response']}")
            return {}
        
        # Parse response
        parsed_result = parse_ai_response(result['response'])
        
        # Get weights from config
        weights = get("consolidated_analysis.weights", {})
        
        # Store results
        insert_ai_analysis(
            ticker=ticker,
            analysis_type="consolidated",
            weights=weights,
            grade=parsed_result.get('grade', 0.5),
            text_analysis=parsed_result.get('analysis', result['response']),
            model=model,
            prompt_tokens=result['prompt_tokens'],
            completion_tokens=result['completion_tokens']
        )
        
        return {
            'ticker': ticker,
            'analysis_type': 'consolidated',
            'grade': parsed_result.get('grade', 0.5),
            'analysis': parsed_result.get('analysis', result['response']),
            'tokens_used': result['total_tokens']
        }
        
    except Exception as e:
        logging.error(f"Error in run_consolidated_analysis for {ticker}: {e}")
        return {}

def write_consolidated_to_csv(ticker: str, output_file: str = "consolidated_analysis.csv") -> None:
    """Write consolidated analysis results to CSV for testing."""
    try:
        result = run_consolidated_analysis(ticker)
        
        if result:
            df = pd.DataFrame([result])
            df.to_csv(output_file, index=False)
            logging.info(f"Consolidated analysis written to {output_file}")
        else:
            logging.warning(f"No consolidated analysis results for {ticker}")
            
    except Exception as e:
        logging.error(f"Error writing consolidated analysis to CSV: {e}")

def insert_raw_data_only(tickers: List[str]) -> None:
    """Insert raw data (stock, analyst, news) without AI analysis."""
    try:
        # Insert stock data
        db_connection.stock_data_brain(tickers)
        
        # Insert analyst data
        db_connection.analysts_data_brain(tickers)
        
        # Insert news data
        db_connection.company_news_data_brain(tickers)
        
        logging.info(f"Raw data inserted for {len(tickers)} tickers")
        
    except Exception as e:
        logging.error(f"Error inserting raw data: {e}") 