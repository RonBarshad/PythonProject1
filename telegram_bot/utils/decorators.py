"""
Decorators for authentication, logging, and rate limiting
"""

import logging
import functools
from typing import Callable, Any
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from telegram_bot.config.messages import get_message

logger = logging.getLogger(__name__)

def log_event(event_type: str = None):
    """
    Decorator to log bot events
    
    Args:
        event_type: Event type to log (if not provided, function name is used)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            try:
                # Get event type
                event_name = event_type or func.__name__
                
                # Log the event
                if update and update.effective_user:
                    logger.info(f"Event: {event_name} - User: {update.effective_user.id}")
                
                # Call the original function
                result = await func(update, context, *args, **kwargs)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        get_message('errors.general', 'en')
                    )
                raise
        
        return wrapper
    return decorator

def require_auth(func: Callable) -> Callable:
    """
    Decorator to require user authentication
    
    Args:
        func: Function to decorate
    """
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: CallbackContext, *args, **kwargs):
        try:
            # Check if user is authenticated
            if not hasattr(self, 'db_service'):
                logger.error("Database service not available")
                return
            
            user_id = update.effective_user.id
            user = await self.db_service.get_user_by_telegram_id(str(user_id))
            
            if not user:
                # User not authenticated, redirect to auth
                await self.auth_handler.handle_authentication(update, context)
                return
            
            # Check if plan is active
            if not await self.db_service.is_plan_active(user['user_id']):
                await update.effective_message.reply_text(
                    get_message('payment.plan_expired', 'en')
                )
                return
            
            # Call the original function
            result = await func(self, update, context, *args, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Authentication error in {func.__name__}: {e}")
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    get_message('errors.general', 'en')
                )
            raise
    
    return wrapper

def rate_limit(max_requests: int, window_seconds: int = 60):
    """
    Decorator to implement rate limiting
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        # Store request counts (in production, use Redis or database)
        request_counts = {}
        
        @functools.wraps(func)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            try:
                user_id = update.effective_user.id
                current_time = datetime.now()
                
                # Clean old entries
                request_counts = {k: v for k, v in request_counts.items() 
                               if (current_time - v['timestamp']).seconds < window_seconds}
                
                # Check rate limit
                if user_id in request_counts:
                    if request_counts[user_id]['count'] >= max_requests:
                        await update.effective_message.reply_text(
                            get_message('errors.rate_limit', 'en')
                        )
                        return
                    request_counts[user_id]['count'] += 1
                else:
                    request_counts[user_id] = {
                        'count': 1,
                        'timestamp': current_time
                    }
                
                # Call the original function
                result = await func(update, context, *args, **kwargs)
                return result
                
            except Exception as e:
                logger.error(f"Rate limit error in {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator

def validate_input(validation_func: Callable):
    """
    Decorator to validate user input
    
    Args:
        validation_func: Function to validate input
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            try:
                # Get user input
                user_input = update.message.text if update.message else ""
                
                # Validate input
                if not validation_func(user_input):
                    await update.effective_message.reply_text(
                        get_message('errors.invalid_input', 'en')
                    )
                    return
                
                # Call the original function
                result = await func(update, context, *args, **kwargs)
                return result
                
            except Exception as e:
                logger.error(f"Input validation error in {func.__name__}: {e}")
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        get_message('errors.general', 'en')
                    )
                raise
        
        return wrapper
    return decorator

def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors gracefully
    
    Args:
        func: Function to decorate
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            result = await func(update, context, *args, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            
            # Send user-friendly error message
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        get_message('errors.general', 'en')
                    )
                except Exception as reply_error:
                    logger.error(f"Error sending error message: {reply_error}")
            
            # Re-raise for logging purposes
            raise
    
    return wrapper

def log_database_operation(operation: str):
    """
    Decorator to log database operations
    
    Args:
        operation: Description of the database operation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"Database operation: {operation}")
                result = await func(*args, **kwargs)
                logger.info(f"Database operation completed: {operation}")
                return result
                
            except Exception as e:
                logger.error(f"Database operation failed: {operation} - {e}")
                raise
        
        return wrapper
    return decorator 