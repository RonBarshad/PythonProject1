from typing import Tuple
import mysql.connector
from mysql.connector import Error
from config.config import get
import json
import numpy as np
import pandas as pd
from datetime import date, datetime
from typing import List, Optional


HOST = get("database.host")
USER = get("database.user")
PASSWORD = get("database.password")
DATABASE_NAME = get("database.name")
TABLE = get("database.table.daily_stock")



def _fetch_df(cursor, query: str, params: Tuple) -> pd.DataFrame:
    """Run query via an *existing* cursor → DataFrame with correct column names."""
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description] if cursor.description else []
    return pd.DataFrame(rows, columns=cols)

def get_most_recent_data(ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Return three DataFrames with ALL rows for *the latest day that exists*
    in each fact table for the given ticker.
        1. fact_ticker_daily_data
        2. fact_avg_analyst_rating
        3. fact_news_data   (uses calendar-day of latest timestamp)
    Order of return: (prices_df, analyst_df, news_df).
    """
    # ---- Queries ---------------------------------------------------------
    q_price = """
        SELECT *
        FROM   fact_ticker_daily_data
        WHERE  company_ticker = %s
          AND  event_date = (
                 SELECT MAX(event_date)
                 FROM   fact_ticker_daily_data
                 WHERE  company_ticker = %s
               )
    """

    q_rating = """
        SELECT *
        FROM   fact_avg_analyst_rating
        WHERE  company_ticker = %s
          AND  event_date = (
                 SELECT MAX(event_date)
                 FROM   fact_avg_analyst_rating
                 WHERE  company_ticker = %s
               )
    """

    q_news = """
        SELECT *
        FROM   fact_news_data
        WHERE  company_ticker = %s
          AND  DATE(event_date_published) = (
                 SELECT DATE(MAX(event_date_published))
                 FROM   fact_news_data
                 WHERE  company_ticker = %s
               )
    """
    # ---- One connection for the three pulls ------------------------------
    conn = cursor = None
    try:
        conn = mysql.connector.connect(
            host     = HOST,
            user     = USER,
            password = PASSWORD,
            database = DATABASE_NAME
        )
        cursor = conn.cursor()

        prices_df  = _fetch_df(cursor, q_price,  (ticker, ticker))
        analyst_df = _fetch_df(cursor, q_rating, (ticker, ticker))
        news_df    = _fetch_df(cursor, q_news,   (ticker, ticker))

        return prices_df, analyst_df, news_df

    except Error as err:
        print("[get_most_recent_data] MySQL error:", err)
        return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def dfs_list_to_json(
        dfs: List[pd.DataFrame],
        names: Optional[List[str]] = None
) -> str:
    """
    Convert a list of DataFrames (of any shape & schema) into a single JSON blob.

    Parameters
    ----------
    dfs : List[pd.DataFrame]
        Your DataFrames in any order.
    names : List[str], optional
        Human-friendly names for each table.  If omitted or too short,
        defaults to "table_0", "table_1", etc.

    Returns
    -------
    str
        A JSON string like:
        {
          "tables": [
            {
              "name": "prices",
              "columns": {"open_price": "float64", "event_date": "object", …},
              "rows": [
                {"open_price": 190.1, "event_date": "2025-06-20", …},
                …
              ]
            },
            …
          ]
        }
    """
    tables = []
    for idx, df in enumerate(dfs):
        tbl_name = names[idx] if names and idx < len(names) else f"table_{idx}"
        # Column metadata
        cols_meta = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # Row data
        rows = []
        for _, row in df.iterrows():
            rec = {}
            for col, val in row.items():
                if pd.isna(val):
                    rec[col] = None
                elif isinstance(val, (np.generic,)):
                    rec[col] = val.item()
                elif isinstance(val, (pd.Timestamp, datetime, date)):
                    rec[col] = val.isoformat()
                else:
                    rec[col] = val
            rows.append(rec)

        tables.append({
            "name": tbl_name,
            "columns": cols_meta,
            "rows": rows
        })

    blob = {"tables": tables}
    return json.dumps(blob, ensure_ascii=False) 