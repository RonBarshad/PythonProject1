"""
users/user_manager.py

Mission: Manage user data in the database. This module provides functions to insert new users (with unique user_id), check for existing users, and update user data (tickers or private info). It is designed for robust, production-grade user management.

Features:
- Insert a new user with a randomly generated user_id (UUID4) if not already present (by email or phone number).
- Update user data (tickers, private info, etc.) for a given user_id.
- Handles serialization of preferences (as JSON) and tickers (as comma-separated string).
- Uses MySQL for persistent storage.

Usage:
    from users.user_manager import insert_user, update_user
    
    # Insert a new user
    insert_user(
        full_name="Alice Example",
        email="alice@example.com",
        phone_number="+1234567890",
        password_hash="...",
        tickers=["AAPL", "MSFT"],
        preferences={"theme": "dark"}
    )
    
    # Update user data
    update_user("user_id", {"tickers": "AAPL,MSFT,GOOG"})
"""

import mysql.connector
from mysql.connector import Error
from config.config import get
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json

USER_TABLE = "fact_users_data_table"

def get_db_credentials() -> Dict[str, str]:
    """
    Retrieve database credentials from the configuration file.
    Returns:
        dict: Database connection parameters.
    """
    return {
        'host': get("database.host"),
        'user': get("database.user"),
        'password': get("database.password"),
        'database': get("database.name")
    }

def insert_user(full_name: str, email: str, phone_number: str, password_hash: str, tickers: Optional[str] = None, preferences: Optional[dict] = None) -> bool:
    """
    Insert a new user if not already exists (by email or phone number).
    - user_id is generated as a UUID4 string.
    - tickers can be a list or comma-separated string.
    - preferences (dict) are stored as JSON.
    Args:
        full_name (str): User's full name.
        email (str): User's email address (must be unique).
        phone_number (str): User's phone number (must be unique).
        password_hash (str): Hashed password (never store plain passwords).
        tickers (Optional[str|list]): List or comma-separated string of tickers.
        preferences (Optional[dict]): User preferences/settings.
    Returns:
        bool: True if inserted, False if user already exists or error.
    """
    creds = get_db_credentials()
    conn = None
    cursor = None
    user_id = str(uuid.uuid4())
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        # Check if user exists
        cursor.execute(f"SELECT user_id FROM {USER_TABLE} WHERE email=%s OR phone_number=%s", (email, phone_number))
        if cursor.fetchone():
            print(f"User already exists: {email} / {phone_number}")
            return False
        # Convert tickers list to string if needed
        if isinstance(tickers, list):
            tickers = ",".join(tickers)
        # Insert new user
        sql = f"""
        INSERT INTO {USER_TABLE} (user_id, creation_time, update_time, full_name, email, phone_number, password_hash, tickers, preferences, status, update_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
        """
        now = datetime.now()
        cursor.execute(sql, (
            user_id,
            now,
            now,
            full_name,
            email,
            phone_number,
            password_hash,
            tickers,
            json.dumps(preferences) if preferences else None,
            'active'
        ))
        conn.commit()
        print(f"Inserted new user: {user_id}")
        return True
    except Error as e:
        print(f"DB error inserting user: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def update_user(user_id: str, update_fields: Dict[str, Any]) -> bool:
    """
    Update user data (tickers or private info) for a given user_id.
    Args:
        user_id (str): The user's unique ID.
        update_fields (dict): Columns and values to update (e.g., {'tickers': 'AAPL,MSFT', 'full_name': 'New Name'})
    Returns:
        bool: True if update succeeded, False otherwise.
    """
    if not update_fields:
        print("No fields to update.")
        return False
    # Convert tickers list to string if needed
    if "tickers" in update_fields and isinstance(update_fields["tickers"], list):
        update_fields["tickers"] = ",".join(update_fields["tickers"])
    # Convert preferences dict to JSON string if needed
    if "preferences" in update_fields and isinstance(update_fields["preferences"], dict):
        import json
        update_fields["preferences"] = json.dumps(update_fields["preferences"])
    creds = get_db_credentials()
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        set_clause = ', '.join([f"{k}=%s" for k in update_fields.keys()])
        sql = f"UPDATE {USER_TABLE} SET {set_clause}, update_time=%s, update_amount=update_amount+1 WHERE user_id=%s"
        values = list(update_fields.values()) + [datetime.now(), user_id]
        cursor.execute(sql, values)
        conn.commit()
        print(f"Updated user {user_id}: {update_fields}")
        return True
    except Error as e:
        print(f"DB error updating user: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close() 