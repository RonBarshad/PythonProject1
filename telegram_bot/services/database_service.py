"""
Database Service
Handles all database operations with data validation
"""

import logging
import pymysql
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from telegram_bot.config.settings import DATABASE_CONFIG
from telegram_bot.utils.validators import validate_user_data, validate_event_data

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service for handling all database operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database service with configuration
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.connection = None
    
    async def get_connection(self):
        """
        Get database connection with error handling
        
        Returns:
            Database connection
        """
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    user=self.config['user'],
                    password=self.config['password'],
                    database=self.config['database'],
                    charset=self.config['charset'],
                    autocommit=True
                )
            return self.connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def close_connection(self):
        """Close database connection"""
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None
    
    async def execute_query(self, query: str, params: Tuple = None) -> List[Dict]:
        """
        Execute a SELECT query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            conn = await self.get_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    async def execute_update(self, query: str, params: Tuple = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            conn = await self.get_connection()
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                conn.commit()
                return affected_rows
        except Exception as e:
            logger.error(f"Update execution error: {e}")
            raise
    
    # Analysis Data Methods
    
    async def get_latest_ticker_data(self, ticker: str) -> Optional[Dict]:
        """
        Get latest daily data for a ticker
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Latest ticker data or None
        """
        query = """
            SELECT * FROM fact_ticker_daily_data 
            WHERE company_ticker = %s 
            ORDER BY event_date DESC 
            LIMIT 1
        """
        results = await self.execute_query(query, (ticker.upper(),))
        return results[0] if results else None
    
    async def get_ticker_data_for_period(self, ticker: str, days: int = 30) -> List[Dict]:
        """
        Get ticker data for a specific period
        
        Args:
            ticker: Ticker symbol
            days: Number of days to fetch
            
        Returns:
            List of ticker data
        """
        query = """
            SELECT * FROM fact_ticker_daily_data 
            WHERE company_ticker = %s 
            ORDER BY event_date DESC 
            LIMIT %s
        """
        return await self.execute_query(query, (ticker.upper(), days))
    
    async def get_ticker_analysis(self, ticker: str, analysis_type: str = None) -> List[Dict]:
        """
        Get AI analysis for a ticker
        
        Args:
            ticker: Ticker symbol
            analysis_type: Type of analysis (optional)
            
        Returns:
            List of analysis data
        """
        if analysis_type:
            query = """
                SELECT * FROM self_ai_analysis_ticker 
                WHERE company_ticker = %s AND analysis_type = %s
                ORDER BY insertion_time DESC 
                LIMIT 5
            """
            params = (ticker.upper(), analysis_type)
        else:
            query = """
                SELECT * FROM self_ai_analysis_ticker 
                WHERE company_ticker = %s
                ORDER BY insertion_time DESC 
                LIMIT 5
            """
            params = (ticker.upper(),)
        
        return await self.execute_query(query, params)
    
    async def get_latest_analysis(self, ticker: str, analysis_type: str = None) -> Optional[Dict]:
        """
        Get latest analysis for a ticker
        
        Args:
            ticker: Ticker symbol
            analysis_type: Type of analysis (optional)
            
        Returns:
            Latest analysis or None
        """
        analyses = await self.get_ticker_analysis(ticker, analysis_type)
        return analyses[0] if analyses else None
    
    async def check_ticker_exists(self, ticker: str) -> bool:
        """
        Check if ticker exists in the database
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            True if ticker exists, False otherwise
        """
        query = """
            SELECT COUNT(*) as count FROM fact_ticker_daily_data 
            WHERE company_ticker = %s
        """
        results = await self.execute_query(query, (ticker.upper(),))
        return results[0]['count'] > 0 if results else False
    
    async def get_ticker_price_change(self, ticker: str, days: int = 1) -> Optional[Dict]:
        """
        Get price change for a ticker over specified days
        
        Args:
            ticker: Ticker symbol
            days: Number of days to compare
            
        Returns:
            Price change data or None
        """
        query = """
            SELECT 
                company_ticker,
                close_price,
                LAG(close_price, %s) OVER (ORDER BY event_date) as previous_price,
                ((close_price - LAG(close_price, %s) OVER (ORDER BY event_date)) / LAG(close_price, %s) OVER (ORDER BY event_date)) * 100 as change_percent
            FROM fact_ticker_daily_data 
            WHERE company_ticker = %s 
            ORDER BY event_date DESC 
            LIMIT 1
        """
        results = await self.execute_query(query, (days, days, days, ticker.upper()))
        return results[0] if results else None
    
    # User Management Methods
    
    async def get_user_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get user by Telegram ID"""
        try:
            logger.info(f"=== DATABASE: GET USER BY TELEGRAM ID ===")
            logger.info(f"Telegram ID: {telegram_id}")
            
            query = """
                SELECT * FROM fact_users_data_table 
                WHERE telegram_user_id = %s AND status = 'active'
            """
            
            logger.info("Executing database query...")
            result = await self.execute_query(query, (telegram_id,))
            
            if result:
                user_data = result[0]
                logger.info(f"User found - ID: {user_data.get('user_id')}, Email: {user_data.get('email')}")
                logger.info("=== DATABASE: USER RETRIEVED SUCCESSFULLY ===")
                return user_data
            else:
                logger.info("No user found with this Telegram ID")
                logger.info("=== DATABASE: NO USER FOUND ===")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by Telegram ID: {e}")
            logger.error(f"Telegram ID: {telegram_id}")
            return None
    
    async def create_user(self, user_data: Dict) -> bool:
        """Create new user"""
        try:
            logger.info(f"=== DATABASE: CREATE USER ===")
            logger.info(f"User Data: {user_data}")
            
            # Generate unique user_id
            import uuid
            user_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO fact_users_data_table (
                    user_id, full_name, email, phone_number, password_hash,
                    telegram_user_id, plan_type, amount_tickers_allowed,
                    amount_tickers_have, status, creation_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                user_id,
                f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                user_data.get('email', ''),
                '',  # phone_number
                '',  # password_hash
                user_data['telegram_id'],
                user_data.get('plan', 'free'),
                3,  # amount_tickers_allowed for free plan
                0,  # amount_tickers_have
                'active',
                datetime.now()
            )
            
            logger.info("Executing user creation query...")
            result = await self.execute_update(query, values)
            
            if result:
                logger.info("User created successfully")
                logger.info("=== DATABASE: USER CREATION SUCCESSFUL ===")
                return True
            else:
                logger.error("Failed to create user")
                logger.error("=== DATABASE: USER CREATION FAILED ===")
                return False
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            logger.error(f"User data: {user_data}")
            return False
    
    async def update_user(self, user_id: str, updates: Dict) -> bool:
        """
        Update user data with validation
        
        Args:
            user_id: User ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate update data
            if not validate_user_data(updates, is_update=True):
                logger.error("Invalid user update data")
                return False
            
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ['full_name', 'email', 'phone_number', 'plan_type', 
                           'amount_tickers_allowed', 'amount_tickers_have', 
                           'tickers', 'user_weights', 'preferences']:
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("update_time = %s")
            set_clauses.append("update_amount = update_amount + 1")
            params.append(datetime.now())
            
            query = f"""
                UPDATE fact_users_data_table 
                SET {', '.join(set_clauses)}
                WHERE user_id = %s
            """
            params.append(user_id)
            
            affected_rows = await self.execute_update(query, tuple(params))
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def get_user_plan_info(self, user_id: str) -> Optional[Dict]:
        """
        Get user's plan information
        
        Args:
            user_id: User ID
            
        Returns:
            Plan information dictionary
        """
        query = """
            SELECT plan_type, plan_end_time, amount_tickers_allowed, 
                   amount_tickers_have, status
            FROM fact_users_data_table 
            WHERE user_id = %s
        """
        results = await self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    async def is_plan_active(self, user_id: str) -> bool:
        """
        Check if user's plan is active
        
        Args:
            user_id: User ID
            
        Returns:
            True if plan is active, False otherwise
        """
        plan_info = await self.get_user_plan_info(user_id)
        if not plan_info:
            return False
        
        # Free plan is always active
        if plan_info['plan_type'] == 'free':
            return True
        
        # Check if plan has expired
        if plan_info['plan_end_time'] and plan_info['plan_end_time'] < datetime.now():
            return False
        
        return plan_info['status'] == 'active'
    
    async def get_user_tickers(self, user_id: str) -> List[str]:
        """
        Get user's tickers list
        
        Args:
            user_id: User ID
            
        Returns:
            List of ticker symbols
        """
        query = """
            SELECT tickers FROM fact_users_data_table 
            WHERE user_id = %s
        """
        results = await self.execute_query(query, (user_id,))
        
        if results and results[0]['tickers']:
            return [ticker.strip() for ticker in results[0]['tickers'].split(',')]
        return []
    
    async def add_user_ticker(self, user_id: str, ticker: str) -> bool:
        """
        Add ticker to user's portfolio
        
        Args:
            user_id: User ID
            ticker: Ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current tickers
            current_tickers = await self.get_user_tickers(user_id)
            
            # Check if ticker already exists
            if ticker.upper() in [t.upper() for t in current_tickers]:
                return False
            
            # Get user plan limits
            plan_info = await self.get_user_plan_info(user_id)
            if not plan_info:
                return False
            
            # Check if user can add more tickers
            if len(current_tickers) >= plan_info['amount_tickers_allowed']:
                return False
            
            # Add ticker
            current_tickers.append(ticker.upper())
            new_tickers = ','.join(current_tickers)
            
            # Update database
            query = """
                UPDATE fact_users_data_table 
                SET tickers = %s, amount_tickers_have = %s, update_time = %s
                WHERE user_id = %s
            """
            params = (new_tickers, len(current_tickers), datetime.now(), user_id)
            
            affected_rows = await self.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error adding ticker: {e}")
            return False
    
    async def remove_user_ticker(self, user_id: str, ticker: str) -> bool:
        """
        Remove ticker from user's portfolio
        
        Args:
            user_id: User ID
            ticker: Ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current tickers
            current_tickers = await self.get_user_tickers(user_id)
            
            # Remove ticker
            current_tickers = [t for t in current_tickers if t.upper() != ticker.upper()]
            new_tickers = ','.join(current_tickers)
            
            # Update database
            query = """
                UPDATE fact_users_data_table 
                SET tickers = %s, amount_tickers_have = %s, update_time = %s
                WHERE user_id = %s
            """
            params = (new_tickers, len(current_tickers), datetime.now(), user_id)
            
            affected_rows = await self.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error removing ticker: {e}")
            return False
    
    # Event Tracking Methods
    
    async def log_event(self, event_data: Dict) -> bool:
        """Log event to database"""
        try:
            logger.info(f"=== DATABASE: LOGGING EVENT ===")
            logger.info(f"Event Type: {event_data.get('event_type')}")
            logger.info(f"User ID: {event_data.get('user_id')}")
            logger.info(f"Event Time: {event_data.get('event_time')}")
            
            query = """
                INSERT INTO fact_telegram_bot_actions (
                    user_id, telegram_id, event_time, event_type, user_email,
                    user_device, user_plan, kpi, settings_action_trigger,
                    function_call_type, before_change, after_change, product_purchase
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                event_data.get('user_id'),
                event_data.get('telegram_id'),
                event_data.get('event_time'),
                event_data.get('event_type'),
                event_data.get('user_email'),
                event_data.get('user_device'),
                event_data.get('user_plan'),
                event_data.get('kpi'),
                event_data.get('settings_action_trigger'),
                event_data.get('function_call_type'),
                event_data.get('before_change'),
                event_data.get('after_change'),
                event_data.get('product_purchase')
            )
            
            logger.info("Executing event logging query...")
            result = await self.execute_update(query, values)
            
            if result:
                logger.info("Event logged successfully")
                logger.info("=== DATABASE: EVENT LOGGED SUCCESSFULLY ===")
                return True
            else:
                logger.error("Failed to log event")
                logger.error("=== DATABASE: EVENT LOGGING FAILED ===")
                return False
                
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            logger.error(f"Event data: {event_data}")
            return False
    
    async def get_user_state(self, telegram_id: str) -> Optional[str]:
        """Get user state"""
        try:
            logger.info(f"=== DATABASE: GETTING USER STATE ===")
            logger.info(f"Telegram ID: {telegram_id}")
            
            # For now, return None as the state is not stored in the database
            # This can be implemented later if needed
            logger.info("User state not stored in database, returning None")
            logger.info("=== DATABASE: NO USER STATE FOUND ===")
            return None
                
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            logger.error(f"Telegram ID: {telegram_id}")
            return None
    
    async def set_user_state(self, telegram_id: str, state: str) -> bool:
        """Set user state"""
        try:
            logger.info(f"=== DATABASE: SETTING USER STATE ===")
            logger.info(f"Telegram ID: {telegram_id}")
            logger.info(f"New State: {state}")
            
            # For now, just log the state change as it's not stored in the database
            # This can be implemented later if needed
            logger.info("User state change logged (not stored in database)")
            logger.info("=== DATABASE: USER STATE SET SUCCESSFULLY ===")
            return True
                
        except Exception as e:
            logger.error(f"Error setting user state: {e}")
            logger.error(f"Telegram ID: {telegram_id}, State: {state}")
            return False
    
    # Product Management Methods
    
    async def get_available_products(self) -> List[Dict]:
        """
        Get available products from fact_prodacts_available table
        
        Returns:
            List of product dictionaries
        """
        query = """
            SELECT * FROM fact_prodacts_available 
            WHERE product_valid_time > %s OR product_valid_time IS NULL
            ORDER BY price_shown_usd ASC
        """
        return await self.execute_query(query, (datetime.now(),))
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """
        Get product by ID
        
        Args:
            product_id: Product ID
            
        Returns:
            Product dictionary or None
        """
        query = """
            SELECT * FROM fact_prodacts_available 
            WHERE product_id = %s
        """
        results = await self.execute_query(query, (product_id,))
        return results[0] if results else None
    
    # Analytics Methods
    
    async def get_user_events(self, user_id: str, event_type: str = None, 
                             limit: int = 100) -> List[Dict]:
        """
        Get user events for analytics
        
        Args:
            user_id: User ID
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        if event_type:
            query = """
                SELECT * FROM fact_telegram_bot_actions 
                WHERE user_id = %s AND event_type = %s
                ORDER BY event_time DESC 
                LIMIT %s
            """
            params = (user_id, event_type, limit)
        else:
            query = """
                SELECT * FROM fact_telegram_bot_actions 
                WHERE user_id = %s
                ORDER BY event_time DESC 
                LIMIT %s
            """
            params = (user_id, limit)
        
        return await self.execute_query(query, params)
    
    async def get_daily_active_users(self, date: datetime = None) -> int:
        """
        Get number of daily active users
        
        Args:
            date: Date to check (defaults to today)
            
        Returns:
            Number of active users
        """
        if date is None:
            date = datetime.now().date()
        
        query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM fact_telegram_bot_actions 
            WHERE DATE(event_time) = %s
        """
        results = await self.execute_query(query, (date,))
        return results[0]['active_users'] if results else 0 