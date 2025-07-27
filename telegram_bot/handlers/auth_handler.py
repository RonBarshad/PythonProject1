"""
Authentication Handler
Handles user sign-up, sign-in, and authentication flow
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from telegram import Update
from telegram.ext import CallbackContext
from telegram_bot.config.messages import get_message
from telegram_bot.config.settings import BOT_SETTINGS
from telegram_bot.utils.validators import validate_email, validate_phone_number, sanitize_input

logger = logging.getLogger(__name__)

class AuthHandler:
    """
    Handles user authentication and account management
    """
    
    def __init__(self, db_service):
        """
        Initialize authentication handler
        
        Args:
            db_service: Database service instance
        """
        self.db_service = db_service
        self.auth_attempts = {}  # Track authentication attempts
    
    async def handle_first_connection(self, update: Update, context: CallbackContext):
        """
        Handle first-time user connection
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            # Check if user already exists
            existing_user = await self.db_service.get_user_by_telegram_id(telegram_id)
            
            if existing_user:
                # User exists, log the connection
                await self._log_event(existing_user['user_id'], telegram_id, 'first_connection')
                await update.message.reply_text(
                    get_message('welcome', 'en')
                )
                return
            
            # Create new user
            user_id = str(uuid.uuid4())
            user_data = {
                'user_id': user_id,
                'telegram_user_id': telegram_id,
                'full_name': user.full_name or '',
                'plan_type': 'free',
                'amount_tickers_allowed': 3,
                'amount_tickers_have': 0,
                'status': 'active'
            }
            
            success = await self.db_service.create_user(user_data)
            
            if success:
                await self._log_event(user_id, telegram_id, 'first_connection')
                await update.message.reply_text(
                    get_message('first_connection', 'en')
                )
            else:
                await update.message.reply_text(
                    get_message('errors.general', 'en')
                )
                
        except Exception as e:
            logger.error(f"Error in first connection: {e}")
            await update.message.reply_text(
                get_message('errors.general', 'en')
            )
    
    async def is_user_authenticated(self, telegram_id: int) -> bool:
        """Check if user is authenticated"""
        try:
            logger.info(f"=== CHECKING USER AUTHENTICATION ===")
            logger.info(f"Telegram ID: {telegram_id}")
            
            user_data = await self.db_service.get_user_by_telegram_id(str(telegram_id))
            is_authenticated = user_data is not None
            
            logger.info(f"User found in database: {is_authenticated}")
            if user_data:
                logger.info(f"User ID: {user_data.get('id')}")
                logger.info(f"User Email: {user_data.get('email')}")
                logger.info(f"User Plan: {user_data.get('plan')}")
            
            logger.info(f"=== AUTHENTICATION CHECK COMPLETE: {is_authenticated} ===")
            return is_authenticated
            
        except Exception as e:
            logger.error(f"Error checking user authentication: {e}")
            return False
    
    async def handle_authentication(self, update: Update, context: CallbackContext):
        """Handle user authentication"""
        try:
            user = update.effective_user
            logger.info(f"=== AUTHENTICATION FLOW START ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Username: {user.username}")
            logger.info(f"First Name: {user.first_name}")
            logger.info(f"Last Name: {user.last_name}")
            
            # Check if user already exists
            logger.info("Checking if user already exists in database...")
            existing_user = await self.db_service.get_user_by_telegram_id(str(user.id))
            
            if existing_user:
                logger.info("User already exists in database")
                logger.info(f"Existing User ID: {existing_user.get('id')}")
                logger.info(f"Existing User Email: {existing_user.get('email')}")
                
                # Check if plan is active
                logger.info("Checking if user plan is active...")
                is_active = await self.db_service.is_plan_active(existing_user['user_id'])
                logger.info(f"Plan Active: {is_active}")
                
                if is_active:
                    logger.info("User has active plan, showing main menu")
                    await update.message.reply_text("Welcome to StockBot! Please use /start to begin.")
                else:
                    logger.info("User plan not active, showing payment options")
                    await self.payment_handler.show_payment_options(update, context)
            else:
                logger.info("User not found in database, creating new user...")
                # Create new user
                user_data = {
                    'telegram_id': str(user.id),
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': None,
                    'plan': 'free',
                    'created_at': datetime.now()
                }
                
                logger.info("Inserting new user into database...")
                new_user_id = await self.db_service.create_user(user_data)
                logger.info(f"New user created with ID: {new_user_id}")
                
                # Show welcome message and main menu
                logger.info("Showing welcome message and main menu")
                await update.message.reply_text("Welcome to StockBot! Please use /start to begin.")
            
            logger.info("=== AUTHENTICATION FLOW COMPLETE ===")
            
        except Exception as e:
            logger.error(f"Error in authentication handler: {e}")
            await update.message.reply_text("An error occurred during authentication. Please try again.")
    
    async def _start_auth_flow(self, update: Update, context: CallbackContext):
        """
        Start authentication flow
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        telegram_id = str(update.effective_user.id)
        
        # Check if user exists
        existing_user = await self.db_service.get_user_by_telegram_id(telegram_id)
        
        if existing_user:
            # User exists, prompt for sign in
            context.user_data['auth_state'] = 'email'
            context.user_data['auth_mode'] = 'sign_in'
            context.user_data['existing_user'] = existing_user
            
            await update.message.reply_text(
                get_message('authentication.sign_in_prompt', 'en')
            )
        else:
            # New user, prompt for sign up
            context.user_data['auth_state'] = 'email'
            context.user_data['auth_mode'] = 'sign_up'
            
            await update.message.reply_text(
                get_message('authentication.sign_up_prompt', 'en')
            )
    
    async def _handle_email_input(self, update: Update, context: CallbackContext):
        """
        Handle email input during authentication
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        email = sanitize_input(update.message.text)
        
        if not validate_email(email):
            await update.message.reply_text(
                get_message('errors.invalid_input', 'en')
            )
            return
        
        context.user_data['email'] = email
        context.user_data['auth_state'] = 'phone'
        
        await update.message.reply_text(
            get_message('authentication.phone_prompt', 'en')
        )
    
    async def _handle_phone_input(self, update: Update, context: CallbackContext):
        """
        Handle phone input during authentication
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        phone = sanitize_input(update.message.text)
        
        if not validate_phone_number(phone):
            await update.message.reply_text(
                get_message('errors.invalid_input', 'en')
            )
            return
        
        context.user_data['phone'] = phone
        context.user_data['auth_state'] = 'verification'
        
        # For now, we'll skip actual verification and proceed
        # In production, you'd send a verification code
        await self._complete_authentication(update, context)
    
    async def _handle_verification(self, update: Update, context: CallbackContext):
        """
        Handle verification code input
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        # For now, accept any verification code
        # In production, you'd validate the actual code
        await self._complete_authentication(update, context)
    
    async def _complete_authentication(self, update: Update, context: CallbackContext):
        """
        Complete authentication process
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            telegram_id = str(update.effective_user.id)
            auth_mode = context.user_data.get('auth_mode')
            
            if auth_mode == 'sign_up':
                # Create new user
                user_id = str(uuid.uuid4())
                user_data = {
                    'user_id': user_id,
                    'telegram_user_id': telegram_id,
                    'full_name': update.effective_user.full_name or '',
                    'email': context.user_data.get('email', ''),
                    'phone_number': context.user_data.get('phone', ''),
                    'plan_type': 'free',
                    'amount_tickers_allowed': 3,
                    'amount_tickers_have': 0,
                    'status': 'active'
                }
                
                success = await self.db_service.create_user(user_data)
                
                if success:
                    await self._log_event(user_id, telegram_id, 'sign_up_granted')
                    await update.message.reply_text(
                        get_message('authentication.success', 'en')
                    )
                    # Clear auth state
                    context.user_data.clear()
                else:
                    await self._handle_auth_failure(update, context)
                    
            elif auth_mode == 'sign_in':
                # Update existing user
                existing_user = context.user_data.get('existing_user')
                if existing_user:
                    updates = {
                        'email': context.user_data.get('email', ''),
                        'phone_number': context.user_data.get('phone', ''),
                        'last_login': datetime.now()
                    }
                    
                    success = await self.db_service.update_user(existing_user['user_id'], updates)
                    
                    if success:
                        await self._log_event(existing_user['user_id'], telegram_id, 'sign_in_granted')
                        await update.message.reply_text(
                            get_message('authentication.success', 'en')
                        )
                        # Clear auth state
                        context.user_data.clear()
                    else:
                        await self._handle_auth_failure(update, context)
                else:
                    await self._handle_auth_failure(update, context)
                    
        except Exception as e:
            logger.error(f"Error completing authentication: {e}")
            await self._handle_auth_failure(update, context)
    
    async def _handle_auth_failure(self, update: Update, context: CallbackContext):
        """
        Handle authentication failure
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        telegram_id = str(update.effective_user.id)
        
        # Increment failure count
        if telegram_id not in self.auth_attempts:
            self.auth_attempts[telegram_id] = {'count': 0, 'last_attempt': datetime.now()}
        
        self.auth_attempts[telegram_id]['count'] += 1
        self.auth_attempts[telegram_id]['last_attempt'] = datetime.now()
        
        # Check if user should be put in cooldown
        if self.auth_attempts[telegram_id]['count'] >= BOT_SETTINGS['max_retry_attempts']:
            await self._log_event(None, telegram_id, 'cooldown_attempts')
            await update.message.reply_text(
                get_message('authentication.cooldown', 'en')
            )
        else:
            await update.message.reply_text(
                get_message('authentication.failed', 'en')
            )
            # Reset auth state to start
            context.user_data['auth_state'] = 'start'
    
    async def _is_in_cooldown(self, telegram_id: str) -> bool:
        """
        Check if user is in cooldown period
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            True if in cooldown, False otherwise
        """
        if telegram_id not in self.auth_attempts:
            return False
        
        last_attempt = self.auth_attempts[telegram_id]['last_attempt']
        cooldown_duration = timedelta(minutes=BOT_SETTINGS['cooldown_minutes'])
        
        return datetime.now() - last_attempt < cooldown_duration
    
    async def _log_event(self, user_id: str, telegram_id: str, event_type: str):
        """
        Log authentication event
        
        Args:
            user_id: User ID (can be None for new users)
            telegram_id: Telegram user ID
            event_type: Event type to log
        """
        try:
            event_data = {
                'user_id': user_id or f"temp_{telegram_id}",
                'telegram_id': telegram_id,
                'event_type': event_type,
                'event_time': datetime.now(),
                'user_device': 'telegram',
                'user_plan': 'free'  # Default for new users
            }
            
            await self.db_service.log_event(event_data)
            
        except Exception as e:
            logger.error(f"Error logging authentication event: {e}")
    
    async def reset_auth_attempts(self, telegram_id: str):
        """
        Reset authentication attempts for user
        
        Args:
            telegram_id: Telegram user ID
        """
        if telegram_id in self.auth_attempts:
            del self.auth_attempts[telegram_id] 