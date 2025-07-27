"""
Settings Handler
Handles user settings management with inline keyboard buttons
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram_bot.config.messages import get_message
from telegram_bot.config.plans import has_feature
from telegram_bot.utils.validators import validate_ticker, validate_weights, sanitize_input

logger = logging.getLogger(__name__)


class SettingsHandler:
    """
    Handles user settings management with interactive buttons
    """
    
    def __init__(self, db_service):
        """
        Initialize settings handler
        
        Args:
            db_service: Database service instance
        """
        self.db_service = db_service
    
    async def handle_callback_query(self, update: Update, context: CallbackContext):
        """Handle settings callback queries"""
        try:
            query = update.callback_query
            data = query.data
            user = update.effective_user
            
            logger.info(f"=== SETTINGS CALLBACK QUERY RECEIVED ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Callback Data: {data}")
            logger.info(f"Message ID: {query.message.message_id if query.message else 'N/A'}")
            
            # Answer the callback query
            logger.info("Answering callback query...")
            await query.answer()
            logger.info("Callback query answered successfully")
            
            # Route to appropriate handler
            logger.info("Routing settings callback to appropriate handler...")
            if data == "settings_language":
                logger.info("Handling language settings")
                await self._handle_language_change(update, context)
            elif data == "settings_stocks":
                logger.info("Handling stocks settings")
                await self._handle_stocks_management(update, context)
            elif data == "settings_details":
                logger.info("Handling account details")
                await self._handle_details_change(update, context)
            elif data == "settings_back":
                logger.info("Handling back to settings")
                await self._handle_back_to_settings(update, context)
            elif data == "back_to_menu":
                logger.info("Handling back to menu")
                await self._handle_back_to_menu(update, context)
            else:
                logger.warning(f"Unknown settings callback: {data}")
                await query.edit_message_text("Invalid settings option.")
            
            logger.info("=== SETTINGS CALLBACK QUERY HANDLED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error in settings callback query handler: {e}")
            logger.error(f"Callback data that caused error: {data if 'data' in locals() else 'Unknown'}")
            await self._send_error_message(update, context)
    
    async def handle_settings_message(self, update: Update, context: CallbackContext):
        """
        Handle settings-related messages (fallback for text input)
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            message_text = sanitize_input(update.message.text.lower())
            
            # Parse settings selection
            if '1' in message_text or 'language' in message_text:
                await self._handle_language_change(update, context)
            elif '2' in message_text or 'details' in message_text:
                await self._handle_details_change(update, context)
            elif '3' in message_text or 'stocks' in message_text:
                await self._handle_stocks_management(update, context)
            elif '4' in message_text or 'weights' in message_text:
                await self._handle_weights_change(update, context)
            elif '5' in message_text or 'back' in message_text:
                await self._handle_back_to_menu(update, context)
            else:
                # Show settings menu again
                await self._send_settings_buttons(update, context)
                
        except Exception as e:
            logger.error(f"Error handling settings message: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_language_change(self, update: Update, context: CallbackContext):
        """
        Handle language change request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            keyboard = [
                [
                    InlineKeyboardButton("🇺🇸 English", callback_data="language_en"),
                    InlineKeyboardButton("🇮🇱 עברית", callback_data="language_he")
                ],
                [InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            message_text = "🌐 Choose your language:"
            
            if hasattr(update, 'callback_query'):
                await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message_text, reply_markup=reply_markup)
            
            context.user_data['settings_action'] = 'language_change'
            
        except Exception as e:
            logger.error(f"Error handling language change: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_details_change(self, update: Update, context: CallbackContext):
        """
        Handle user details change request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message_text = "Please enter your new details (email, phone, etc.):"
            
            if hasattr(update, 'callback_query'):
                await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message_text, reply_markup=reply_markup)
            
            context.user_data['settings_action'] = 'details_change'
            
        except Exception as e:
            logger.error(f"Error handling details change: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_stocks_management(self, update: Update, context: CallbackContext):
        """
        Handle stocks management request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            # Get user data
            user_data = await self.db_service.get_user_by_telegram_id(telegram_id)
            if not user_data:
                await self._send_error_message(update, context)
                return
            
            # Get current tickers
            tickers = await self.db_service.get_user_tickers(user_data['user_id'])
            
            if not tickers:
                await self._send_add_ticker_prompt(update, context)
            else:
                # Show ticker management buttons
                await self._send_ticker_management_buttons(update, context, tickers)
            
        except Exception as e:
            logger.error(f"Error handling stocks management: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_weights_change(self, update: Update, context: CallbackContext):
        """
        Handle weights change request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            # Get user data
            user_data = await self.db_service.get_user_by_telegram_id(telegram_id)
            if not user_data:
                await self._send_error_message(update, context)
                return
            
            # Check if user has access to weights
            if not has_feature(user_data['plan_type'], 'portfolio_weights'):
                await self._send_premium_required_message(update, context)
                return
            
            # Get user's tickers
            tickers = await self.db_service.get_user_tickers(user_data['user_id'])
            
            if not tickers:
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                message_text = "You need to add tickers to your portfolio before setting weights."
                
                if hasattr(update, 'callback_query'):
                    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
                else:
                    await update.message.reply_text(message_text, reply_markup=reply_markup)
                return
            
            # Show weights prompt
            tickers_list = "\n".join([f"• {ticker}" for ticker in tickers])
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = get_message('settings.weights_prompt', 'en', tickers_list=tickers_list)
            
            if hasattr(update, 'callback_query'):
                await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message_text, reply_markup=reply_markup)
            
            context.user_data['settings_action'] = 'weights_change'
            context.user_data['tickers_for_weights'] = tickers
            
        except Exception as e:
            logger.error(f"Error handling weights change: {e}")
            await self._send_error_message(update, context)
    
    async def _send_settings_buttons(self, update: Update, context: CallbackContext, user_data: Dict):
        """
        Send settings menu with inline keyboard buttons
        
        Args:
            update: Telegram update object
            context: Callback context
            user_data: User data dictionary
        """
        try:
            logger.info("Settings handler _send_settings_buttons called")
            
            # Get user's current settings
            language = user_data.get('language', 'en')
            stocks = user_data.get('stocks', [])
            
            # Create settings message
            message_text = get_message('settings.ticker_add_prompt', language)
            if stocks:
                message_text += f"\n\n📊 Current stocks: {', '.join(stocks)}"
            
            # Create keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🌐 Language", callback_data="settings_language"),
                    InlineKeyboardButton("📊 My Stocks", callback_data="settings_stocks")
                ],
                [
                    InlineKeyboardButton("ℹ️ Account Details", callback_data="settings_details"),
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Check if this is a callback query or regular message
            if hasattr(update, 'callback_query') and update.callback_query:
                logger.info("Editing message for callback query")
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
            else:
                logger.info("Sending new message")
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
            
            logger.info("Settings buttons sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending settings buttons: {e}")
            await self._send_error_message(update, context)
    
    async def _send_add_ticker_prompt(self, update: Update, context: CallbackContext):
        """
        Send add ticker prompt
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = get_message('settings.ticker_add_prompt', 'en')
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
        
        context.user_data['settings_action'] = 'add_ticker'
    
    async def _send_ticker_management_buttons(self, update: Update, context: CallbackContext, tickers: list):
        """
        Send ticker management buttons
        
        Args:
            update: Telegram update object
            context: Callback context
            tickers: List of user's tickers
        """
        keyboard = []
        
        # Add ticker buttons (2 per row)
        for i in range(0, len(tickers), 2):
            row = []
            row.append(InlineKeyboardButton(f"❌ {tickers[i]}", callback_data=f"remove_ticker_{tickers[i]}"))
            if i + 1 < len(tickers):
                row.append(InlineKeyboardButton(f"❌ {tickers[i + 1]}", callback_data=f"remove_ticker_{tickers[i + 1]}"))
            keyboard.append(row)
        
        # Add "Add New Ticker" button
        keyboard.append([InlineKeyboardButton("➕ Add New Ticker", callback_data="add_new_ticker")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="settings_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📈 Your Current Tickers:\n\nClick to remove a ticker or add a new one:"
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
        
        context.user_data['current_tickers'] = tickers
    
    async def _send_premium_required_message(self, update: Update, context: CallbackContext):
        """
        Send premium required message
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        keyboard = [
            [InlineKeyboardButton("💳 Upgrade to Premium", callback_data="payment_upgrade")],
            [InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = get_message('settings.weights_not_available', 'en')
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    async def _send_error_message(self, update: Update, context: CallbackContext):
        """
        Send error message with back button
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = get_message('errors.general', 'en')
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    async def _handle_back_to_menu(self, update: Update, context: CallbackContext):
        """
        Handle back to menu request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            # Clear settings context
            context.user_data.clear()
            await self.db_service.set_user_state(str(update.effective_user.id), None)
            
            # Show main menu
            from handlers.menu_handler import MenuHandler
            menu_handler = MenuHandler(self.db_service)
            await menu_handler._send_main_menu_buttons(update, context)
            
        except Exception as e:
            logger.error(f"Error handling back to menu: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_back_to_settings(self, update: Update, context: CallbackContext):
        """Handle back to settings request"""
        try:
            logger.info("=== HANDLING BACK TO SETTINGS ===")
            user = update.effective_user
            logger.info(f"User ID: {user.id}")
            
            # Clear settings context
            logger.info("Clearing settings context...")
            context.user_data.clear()
            await self.db_service.set_user_state(str(user.id), None)
            
            # Get user data and show settings menu
            logger.info("Getting user data for settings menu...")
            user_data = await self.db_service.get_user_by_telegram_id(str(user.id))
            if user_data:
                logger.info("Showing settings menu...")
                await self._send_settings_buttons(update, context, user_data)
                logger.info("=== BACK TO SETTINGS HANDLED SUCCESSFULLY ===")
            else:
                logger.error("User not found, sending error message")
                await self._send_error_message(update, context)
            
        except Exception as e:
            logger.error(f"Error handling back to settings: {e}")
            await self._send_error_message(update, context)
    
    async def _log_settings_event(self, user_id: str, telegram_id: str, 
                                action: str, before_change: str = None, 
                                after_change: str = None):
        """
        Log settings change event
        
        Args:
            user_id: User ID
            telegram_id: Telegram user ID
            action: Settings action
            before_change: Value before change
            after_change: Value after change
        """
        try:
            event_data = {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'event_type': 'details_changed',
                'event_time': datetime.now(),
                'user_device': 'telegram',
                'settings_action_trigger': action,
                'before_change': before_change,
                'after_change': after_change
            }
            
            await self.db_service.log_event(event_data)
            
        except Exception as e:
            logger.error(f"Error logging settings event: {e}") 