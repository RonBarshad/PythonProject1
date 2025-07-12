# Users Module

## Overview
This folder contains all code related to user management for the stock bot system. It provides robust, production-grade utilities for creating, updating, and managing user data in the database.

## Main Features
- **Insert New Users:** Automatically generates a unique user_id (UUID4) for each new user. Prevents duplicate users by checking email and phone number.
- **Update User Data:** Allows updating any user field, including tickers (as a list or string) and preferences (as a dict or JSON string). Handles serialization automatically.
- **Database Integration:** Uses MySQL for persistent storage, with all credentials and connection details loaded from the main config.

## File: `user_manager.py`

### Functions

#### `insert_user(full_name, email, phone_number, password_hash, tickers=None, preferences=None)`
- **Purpose:** Insert a new user if not already present (by email or phone number).
- **Arguments:**
  - `full_name` (str): User's full name.
  - `email` (str): User's email address (must be unique).
  - `phone_number` (str): User's phone number (must be unique).
  - `password_hash` (str): Hashed password (never store plain passwords).
  - `tickers` (Optional[list or str]): List or comma-separated string of tickers the user follows.
  - `preferences` (Optional[dict]): User preferences/settings (stored as JSON).
- **Returns:** `True` if inserted, `False` if user already exists or error.
- **Notes:**
  - `user_id` is generated automatically as a UUID4 string.
  - Handles serialization of tickers and preferences.

#### `update_user(user_id, update_fields)`
- **Purpose:** Update user data (tickers, preferences, or private info) for a given user_id.
- **Arguments:**
  - `user_id` (str): The user's unique ID.
  - `update_fields` (dict): Columns and values to update (e.g., `{ 'tickers': ['AAPL', 'MSFT'], 'full_name': 'New Name' }`).
- **Returns:** `True` if update succeeded, `False` otherwise.
- **Notes:**
  - Converts tickers list to string and preferences dict to JSON automatically.
  - Updates `update_time` and increments `update_amount`.

## Usage Example
```python
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
update_user("user_id", {"tickers": ["AAPL", "MSFT", "GOOG"], "full_name": "Alice Updated"})
```

## Database Table: `fact_users_data_table`
- `user_id` (VARCHAR, PK): Unique user identifier (UUID4)
- `creation_time` (TIMESTAMP): When the user was created
- `update_time` (TIMESTAMP): Last update time
- `update_amount` (INT): Number of updates
- `full_name` (VARCHAR): User's name
- `email` (VARCHAR, unique): User's email
- `phone_number` (VARCHAR, unique): User's phone
- `password_hash` (VARCHAR): Hashed password
- `tickers` (VARCHAR): Comma-separated tickers
- `preferences` (JSON): User preferences/settings
- `status` (ENUM): User status (e.g., active)

## Extending
- Add more user-related utilities (deletion, password reset, etc.) as needed.
- Integrate with authentication and notification systems.

---

**For any questions or improvements, see the code comments or contact the project maintainer.** 