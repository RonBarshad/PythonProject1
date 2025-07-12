"""
database/schema.py
Mission: This module provides utility functions to perform schema changes on the MySQL database, such as adding/removing columns, creating tables, renaming columns, and creating indexes. It is designed for database maintenance and evolution tasks.
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
from config.config import get
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def get_db_credentials():
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

def add_column(table: str, column_name: str, column_type: str) -> None:
    """
    Mission: Add a new column to an existing table.
    """
    sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type};"
    _execute_sql(sql, f"Added column {column_name} to {table}")

def remove_column(table: str, column_name: str) -> None:
    """
    Mission: Remove a column from an existing table.
    """
    sql = f"ALTER TABLE {table} DROP COLUMN {column_name};"
    _execute_sql(sql, f"Removed column {column_name} from {table}")

def create_table_from_df(table: str, df: pd.DataFrame) -> None:
    """
    Mission: Create a new table based on the structure of a given DataFrame (no data insertion).
    """
    col_defs = []
    dtype_map = {
        'int64': 'INT',
        'float64': 'FLOAT',
        'object': 'VARCHAR(255)',
        'datetime64[ns]': 'DATETIME',
        'bool': 'BOOLEAN'
    }
    for col, dtype in df.dtypes.items():
        sql_type = dtype_map.get(str(dtype), 'VARCHAR(255)')
        col_defs.append(f"{col} {sql_type}")
    sql = f"CREATE TABLE {table} ({', '.join(col_defs)});"
    _execute_sql(sql, f"Created table {table} from DataFrame structure")

def rename_column(table: str, old_name: str, new_name: str, column_type: str) -> None:
    """
    Mission: Rename a column in a table. MySQL requires specifying the column type when renaming.
    """
    sql = f"ALTER TABLE {table} CHANGE COLUMN {old_name} {new_name} {column_type};"
    _execute_sql(sql, f"Renamed column {old_name} to {new_name} in {table}")

def create_index(table: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    """
    Mission: Create a new (optionally unique) index for a table.
    """
    unique_str = "UNIQUE " if unique else ""
    cols = ', '.join(columns)
    sql = f"CREATE {unique_str}INDEX {index_name} ON {table} ({cols});"
    _execute_sql(sql, f"Created {'unique ' if unique else ''}index {index_name} on {table}({cols})")


def create_ai_analysis_table(table_name: str = "ai_analysis") -> None:
    """
    Mission: Create a table to collect all AI analysis results for stocks, with columns for event date, insertion time, ticker, analysis type, weights, grade, text analysis, model, and token usage.
    """
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        event_date TIMESTAMP,
        insertion_time TIMESTAMP,
        company_ticker VARCHAR(32),
        analysis_type VARCHAR(64),
        wights JSON,
        grade FLOAT,
        text_analysis TEXT,
        AI_model VARCHAR(64),
        prompt_tokens INT,
        excution_tokens INT
    );
    """
    _execute_sql(sql, f"Created AI analysis table: {table_name}")

def _execute_sql(sql: str, action_desc: str) -> None:
    """
    Mission: Internal helper to execute a SQL statement and log the action.
    """
    creds = get_db_credentials()
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        logging.info(action_desc)
    except Error as e:
        logging.error(f"SQL error during {action_desc}: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close() 