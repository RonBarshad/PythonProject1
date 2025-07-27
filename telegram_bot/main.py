"""
Telegram Bot Main Entry Point
Handles bot initialization and message routing
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

from telegram_bot.config.settings import  *
from telegram_bot.config.messages import MESSAGES
from telegram_bot.handlers.auth_handler import AuthHandler
from telegram_bot.handlers.menu_handler import MenuHandler
from telegram_bot.handlers.analysis_handler import AnalysisHandler
from telegram_bot.handlers.settings_handler import SettingsHandler
from telegram_bot.handlers.payment_handler import PaymentHandler
from telegram_bot.services.database_service import DatabaseService
from telegram_bot.utils.decorators import require_auth, log_event

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """
    Main bot class that orchestrates all handlers and services
    """
    
    def __init__(self):
        """Initialize the Telegram bot"""
        logger.info("=== BOT INITIALIZATION START ===")
        
        # Load configuration
        logger.info("Loading bot configuration...")
        self.bot_token = BOT_TOKEN
        if not self.bot_token:
            logger.error("Bot token not found in configuration!")
            raise ValueError("Bot token is required")
        logger.info(f"Bot token loaded: {self.bot_token[:10]}...")
        
        # Initialize database service
        logger.info("Initializing database service...")
        self.db_service = DatabaseService(DATABASE_CONFIG)
        logger.info("Database service initialized successfully")
        
        # Initialize handlers
        logger.info("Initializing bot handlers...")
        self.auth_handler = AuthHandler(self.db_service)
        self.menu_handler = MenuHandler(self.db_service)
        self.analysis_handler = AnalysisHandler(self.db_service)
        self.settings_handler = SettingsHandler(self.db_service)
        self.payment_handler = PaymentHandler(self.db_service)
        logger.info("All handlers initialized successfully")
        
        # Create application
        logger.info("Creating Telegram application...")
        self.app = Application.builder().token(self.bot_token).build()
        logger.info("Telegram application created successfully")
        
        # Setup handlers
        logger.info("Setting up application handlers...")
        self._setup_handlers()
        logger.info("Application handlers setup completed")
        
        logger.info("=== BOT INITIALIZATION COMPLETE ===")
    
    def _is_coupon_code(self, message_text: str) -> bool:
        """Check if message is a coupon code"""
        try:
            # Import validator here to avoid circular imports
            from telegram_bot.utils.validators import validate_coupon_code
            
            # Check if message looks like a coupon code
            if len(message_text) >= 3 and len(message_text) <= 30:
                # Check for common coupon patterns
                if '_' in message_text or '-' in message_text:
                    return True
                # Check if it's alphanumeric with common coupon keywords
                if any(keyword in message_text.lower() for keyword in ['coupon', 'discount', 'promo', 'code', 'offer', 'pct', 'percent']):
                    return True
                # Check if it matches coupon format (alphanumeric with special chars)
                if validate_coupon_code(message_text):
                    return True
                # Check for percentage patterns (e.g., "25pct", "10percent")
                if any(pattern in message_text.lower() for pattern in ['pct', 'percent', '%']):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking coupon code: {e}")
            return False
    
    def _is_numeric_menu_selection(self, message_text: str) -> bool:
        """Check if message is a numeric menu selection (1-9)"""
        try:
            num = int(message_text)
            return 1 <= num <= 9
        except ValueError:
            return False
    
    def _setup_handlers(self):
        """Setup all bot handlers"""
        logger.info("=== SETTING UP BOT HANDLERS ===")
        
        try:
            # Command handlers
            logger.info("Registering command handlers...")
            self.app.add_handler(CommandHandler("start", self._handle_start))
            logger.info("Command handlers registered successfully")
            
            # Message handlers
            logger.info("Registering message handlers...")
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            logger.info("Message handlers registered successfully")
            
            # Callback query handlers
            logger.info("Registering callback query handlers...")
            self.app.add_handler(CallbackQueryHandler(self._handle_callback_query))
            logger.info("Callback query handlers registered successfully")
            
            # Error handlers
            logger.info("Registering error handlers...")
            self.app.add_error_handler(self._handle_error)
            logger.info("Error handlers registered successfully")
            
            logger.info("=== ALL HANDLERS SETUP COMPLETE ===")
            
        except Exception as e:
            logger.error(f"Error setting up handlers: {e}")
            raise
    
    async def _handle_start(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        try:
            user = update.effective_user
            logger.info(f"=== START COMMAND RECEIVED ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Username: {user.username}")
            logger.info(f"First Name: {user.first_name}")
            logger.info(f"Last Name: {user.last_name}")
            
            # Log event to database
            logger.info("Logging start command event to database...")
            event_data = {
                'user_id': str(user.id),
                'telegram_id': str(user.id),
                'event_time': datetime.now(),
                'event_type': 'start_command',
                'user_email': None,
                'user_device': None,
                'user_plan': None,
                'kpi': None,
                'settings_action_trigger': None,
                'function_call_type': None,
                'before_change': None,
                'after_change': None,
                'product_purchase': None
            }
            await self.db_service.log_event(event_data)
            logger.info("Start command event logged successfully")
            
            # Check authentication
            logger.info("Checking user authentication...")
            if await self.auth_handler.is_user_authenticated(user.id):
                logger.info("User is authenticated, showing main menu")
                await self.menu_handler.show_main_menu(update, context)
            else:
                logger.info("User not authenticated, starting authentication flow")
                await self.auth_handler.handle_authentication(update, context)
            
            logger.info("=== START COMMAND HANDLED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error in start command handler: {e}")
            await update.message.reply_text("An error occurred. Please try again.")
    
    async def _handle_callback_query(self, update: Update, context: CallbackContext):
        """Handle callback queries from inline keyboard buttons"""
        try:
            query = update.callback_query
            data = query.data
            user = update.effective_user
            
            logger.info(f"=== CALLBACK QUERY RECEIVED ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Callback Data: {data}")
            logger.info(f"Message ID: {query.message.message_id if query.message else 'N/A'}")
            logger.info(f"Chat ID: {query.message.chat.id if query.message else 'N/A'}")
            
            # Log callback event to database
            logger.info("Logging callback query event to database...")
            event_data = {
                'user_id': str(user.id),
                'telegram_id': str(user.id),
                'event_time': datetime.now(),
                'event_type': 'callback_query',
                'user_email': None,
                'user_device': None,
                'user_plan': None,
                'kpi': data,
                'settings_action_trigger': None,
                'function_call_type': None,
                'before_change': None,
                'after_change': None,
                'product_purchase': None
            }
            await self.db_service.log_event(event_data)
            logger.info("Callback query event logged successfully")
            
            # Route callback queries to appropriate handlers
            logger.info("Routing callback query to appropriate handler...")
            if data.startswith(("analysis_", "ticker_", "new_ticker_")):
                logger.info("Routing to menu handler (analysis/ticker callbacks)")
                await self.menu_handler.handle_callback_query(update, context)
            elif data.startswith("settings_"):
                logger.info("Routing to settings handler")
                await self.settings_handler.handle_callback_query(update, context)
            elif data.startswith("payment_"):
                logger.info("Routing to payment handler")
                await self.payment_handler.handle_callback_query(update, context)
            elif data in ["settings", "payment", "back_to_menu"]:
                logger.info(f"Routing to menu handler for callback: {data}")
                await self.menu_handler.handle_callback_query(update, context)
            else:
                logger.warning(f"Unknown callback data: {data}")
                await query.answer("Invalid option selected.")
            
            logger.info("=== CALLBACK QUERY HANDLED SUCCESSFULLY ===")
                
        except Exception as e:
            logger.error(f"Error in callback query handler: {e}")
            logger.error(f"Callback data that caused error: {data if 'data' in locals() else 'Unknown'}")
            if update.callback_query:
                await update.callback_query.answer("Error occurred. Please try again.")
    
    async def _handle_message(self, update: Update, context: CallbackContext):
        """Handle all text messages from users"""
        try:
            user = update.effective_user
            message_text = update.message.text
            
            logger.info(f"=== TEXT MESSAGE RECEIVED ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Username: {user.username}")
            logger.info(f"Message Text: {message_text}")
            logger.info(f"Message ID: {update.message.message_id}")
            logger.info(f"Chat ID: {update.message.chat.id}")
            logger.info(f"Chat Type: {update.message.chat.type}")
            
            # Log the incoming message
            logger.info("Logging message event to database...")
            event_data = {
                'user_id': str(user.id) if user else None,
                'telegram_id': str(user.id) if user else None,
                'event_time': datetime.now(),
                'event_type': 'message_received',
                'user_email': None,
                'user_device': None,
                'user_plan': None,
                'kpi': message_text,
                'settings_action_trigger': None,
                'function_call_type': None,
                'before_change': None,
                'after_change': None,
                'product_purchase': None
            }
            await self.db_service.log_event(event_data)
            logger.info("Message event logged successfully")
            
            # Check if user is authenticated
            logger.info("Checking user authentication...")
            if not await self.auth_handler.is_user_authenticated(user.id):
                logger.info("User not authenticated, starting authentication flow")
                await self.auth_handler.handle_authentication(update, context)
                return
            
            logger.info("User is authenticated, routing message...")
            # Route message based on context
            await self._route_message(update, context)
            
            logger.info("=== TEXT MESSAGE HANDLED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            logger.error(f"Message that caused error: {message_text if 'message_text' in locals() else 'Unknown'}")
            await update.message.reply_text("An error occurred. Please try again.")
    
    async def _route_message(self, update: Update, context: CallbackContext):
        """Route messages to appropriate handlers based on user state"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text.lower()
            
            logger.info(f"=== MESSAGE ROUTING START ===")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Message Text (lowercase): {message_text}")
            
            # Get user state from database
            logger.info("Retrieving user state from database...")
            user_state = await self.db_service.get_user_state(user_id)
            logger.info(f"User State: {user_state}")
            
            # Route based on state and message
            if user_state == "payment_flow":
                logger.info("Routing to payment handler (payment_flow state)")
                await self.payment_handler.handle_payment_message(update, context)
            elif user_state == "settings_flow":
                logger.info("Routing to settings handler (settings_flow state)")
                await self.settings_handler.handle_settings_message(update, context)
            elif user_state == "analysis_flow":
                logger.info("Routing to analysis handler (analysis_flow state)")
                await self.analysis_handler.handle_analysis_message(update, context)
            elif message_text in ["menu", "start", "/menu"]:
                logger.info("Routing to menu handler (menu command)")
                await self.menu_handler.show_main_menu(update, context)
            elif self._is_coupon_code(message_text):
                logger.info("Detected coupon code, routing to payment handler")
                await self.payment_handler.handle_coupon_code(update, context, message_text)
            elif self._is_numeric_menu_selection(message_text):
                logger.info("Detected numeric menu selection, routing to menu handler")
                await self.menu_handler.handle_menu_selection(update, context)
            else:
                logger.info("Routing to menu handler (default/unrecognized message)")
                # Default: show menu for any unrecognized message
                await self.menu_handler.show_main_menu(update, context)
            
            logger.info("=== MESSAGE ROUTING COMPLETE ===")
            
        except Exception as e:
            logger.error(f"Error in message routing: {e}")
            logger.error(f"User ID: {user_id if 'user_id' in locals() else 'Unknown'}")
            logger.error(f"Message: {message_text if 'message_text' in locals() else 'Unknown'}")
            await update.message.reply_text("An error occurred while processing your message.")
    
    async def _handle_error(self, update: Update, context: CallbackContext):
        """Handle errors in bot operations"""
        logger.error(f"=== BOT ERROR OCCURRED ===")
        logger.error(f"Error: {context.error}")
        logger.error(f"Update: {update}")
        logger.error(f"Context: {context}")
        
        if update and hasattr(update, 'effective_message') and update.effective_message:
            logger.info("Sending error message to user")
            await update.effective_message.reply_text("An error occurred. Please try again.")
        else:
            logger.warning("Could not send error message to user (no effective message)")
    
    def run(self):
        """Start the bot"""
        logger.info("=== STARTING TELEGRAM BOT ===")
        try:
            logger.info("Starting bot polling...")
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            logger.info("Bot polling started successfully")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            logger.error("Bot failed to start")
            raise


def main():
    """Main function to start the bot"""
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()