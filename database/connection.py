"""
database/connection.py
Mission: This module manages all database interactions for the stock bot, including inserting and retrieving stock, analyst, and news data. It provides functions to insert data into the database, fetch data for specific tickers and tables, and coordinate the data ingestion process for different data types.
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
from config.config import get
import ai.connector as gpt_connector
import data_processing.analysts as analysts_rating
import data_processing.news as company_news
from typing import Optional, Dict
import data_processing.technical as stocks_technical_analysis
import datetime
import time
import logging

logger = logging.getLogger(__name__)
from utils.metrics import db_queries, db_duration

def get_db_credentials() -> Dict[str, str]:
    """
    Mission: Retrieve database credentials from the configuration file.
    Returns a dictionary with host, user, password, and database name.
    """
    return {
        'host': get("database.host"),
        'user': get("database.user"),
        'password': get("database.password"),
        'database': get("database.name")
    }

def insert_data(df: pd.DataFrame, table: str, col_map: Optional[Dict[str, str]] = None) -> None:
    """
    Mission: Insert a DataFrame into the specified database table with optional column mapping.
    """
    df = df.where(pd.notnull(df), None)
    if df.empty:
        logging.info("[insert_stock_data] got empty DataFrame → nothing to do.")
        return

    # Table-specific data type handling
    if table == get("database.table.daily_stock"):
        if not isinstance(col_map, dict):
            logging.error("col_map must be a dict for daily_stock table.")
            return
        required_cols = [str(c) for c in (["company_ticker", "event_date"] + list(col_map.values()))]
        if not all(col in df.columns for col in required_cols):
            logging.error(f"Missing required columns for daily_stock: {required_cols}")
            return
        df2 = df[required_cols]

    elif table == get("database.table.analyst_rating"):
        df2 = df.copy()
        if "event_date" in df2.columns:
            df2["event_date"] = (
                pd.to_datetime(df2["event_date"])
                .dt.date
            )

    elif table == get("database.table.news_rating"):
        if not isinstance(col_map, dict):
            logging.error("col_map must be a dict for news_rating table.")
            return
        df2 = df.rename(columns=col_map)
        if "event_date" in df2.columns:
            df2["event_date"] = (
                 pd.to_datetime(df2["event_date"], format="%Y%m%dT%H%M%S", utc=True)
                 .dt.tz_localize(None)
            )
            df2["event_date"] = df2["event_date"].values.astype('datetime64[us]')
        
        # Truncate headline column to 500 characters to prevent "Data too long" errors
        if "headline" in df2.columns:
            df2["headline"] = df2["headline"].astype(str).str[:500]

    elif table == get("database.other_tables.ai_analysis"):
        if not isinstance(col_map, dict):
            logging.error("col_map must be a dict for ai_analysis table.")
            return
        df2 = df.copy()
        df2 = df2.rename(columns=col_map)
        
        # Special handling for ai_analysis table - ensure all NaN values are None in ALL columns
        df2 = df2.replace([np.nan, float('nan'), 'nan', 'NaN'], None)
        
        # Additional check for ALL columns to ensure no NaN values remain
        for col in df2.columns:
            df2[col] = df2[col].apply(lambda x: None if pd.isna(x) or x == 'nan' or x == 'NaN' else x)

    else:
        # Default handling for other tables
        if col_map:
            df2 = df.rename(columns=col_map)
        else:
            df2 = df

    creds = get_db_credentials()
    conn = None
    cursor = None

    try:
        t0 = time.perf_counter()
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()

        # Convert datetime columns to strings for MySQL compatibility
        for col in df2.select_dtypes(include=['datetime64[ns]']).columns:
            df2[col] = df2[col].astype(str)

        # Convert NaN values to None for MySQL compatibility
        df2 = df2.where(pd.notnull(df2), None)
        
        # Remove duplicate rows to prevent database constraint violations
        df2 = df2.drop_duplicates()

        # Prepare data for insertion
        columns = df2.columns.tolist()
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT IGNORE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # Convert DataFrame to list of tuples
        data = [tuple(row) for row in df2.values]

        # Execute batch insert (INSERT IGNORE will skip duplicates)
        cursor.executemany(insert_query, data)
        conn.commit()
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "db_insert_ok",
            extra={"op": "insert", "table": table, "duration_ms": round(duration_ms, 2)}
        )
        try:
            db_queries.labels(op="insert", table=table).inc()
            db_duration.labels(op="insert", table=table).observe(duration_ms)
        except Exception:
            pass

    except Error as e:
        logger.error(f"[insert_stock_data] ERROR: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_data(ticker: str, table: str, window: int) -> pd.DataFrame:
    """
    Mission: Fetch data for a specific ticker from the specified table within the given time window.
    """
    creds = get_db_credentials()
    conn = None
    cursor = None

    try:
        t0 = time.perf_counter()
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()

        # Query to get data for the ticker within the time window
        query = f"""
        SELECT *
        FROM {table}
        WHERE company_ticker = %s
        AND event_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY event_date DESC
        """
        
        cursor.execute(query, (ticker, window))
        rows = cursor.fetchall()
        
        if cursor.description:
            columns = [d[0] for d in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            duration_ms = (time.perf_counter() - t0) * 1000
            logger.info(
                "db_select_ok",
                extra={"op": "select", "table": table, "duration_ms": round(duration_ms, 2)}
            )
            try:
                db_queries.labels(op="select", table=table).inc()
                db_duration.labels(op="select", table=table).observe(duration_ms)
            except Exception:
                pass
            return df
        else:
            return pd.DataFrame()

    except Error as e:
        logger.error(f"Database error fetching data for {ticker} from {table}: {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def stock_data_brain(tickers: list) -> None:
    """
    Mission: For each ticker, fetch technical stock data, process it, and insert it into the database.
    """

    for item in tickers:
        df, db_table, col_map = stocks_technical_analysis.get_stock_data(
            item,
            period="6mo",
            interval="1d",
            table=get("database.table.daily_stock"),
            col_map=get("technical_analysis.col_map")
        )
        insert_data(df, db_table, col_map)
        logging.info(f"finish uploading {item}")

def analysts_data_brain(tickers: list) -> None:
    """
    Mission: Fetch and insert analyst ratings data for a list of tickers into the database.
    """
    db_table = get("database.table.analyst_rating")
    df = analysts_rating.avg_analyst_rating(tickers)
    insert_data(df, db_table)

def company_news_data_brain(tickers: list) -> None:
    """
    Mission: Fetch and insert company news sentiment data for a list of tickers into the database.
    """
    dfs = []
    for ticker in tickers:
        data = company_news.av_get_json(
            function=get("news_analysis.api_function_news"),
            api_key=get("api_key_alpha_vantage"),
            ticker=ticker
        )
        feed = data.get("feed") if isinstance(data, dict) else []
        if feed is None:
            logging.warning(f"No feed found for ticker {ticker}")
            continue
        df = company_news.news_to_df_single(feed=feed, ticker=ticker)
        dfs.append(df)
    final_df = company_news.merge_dfs_no_dupes(dfs=dfs)
    insert_data(
        df=final_df,
        table=get("database.table.news_rating"),
        col_map=get("news_analysis.col_map")
    ) 