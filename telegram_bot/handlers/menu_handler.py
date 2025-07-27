"""
Menu Handler
Handles main menu display and navigation with inline keyboard buttons
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram_bot.config.messages import get_message
from telegram_bot.utils.validators import sanitize_input

logger = logging.getLogger(__name__)

class MenuHandler:
    """
    Handles main menu and navigation with interactive buttons
    """
    
    def __init__(self, db_service):
        """
        Initialize menu handler
        
        Args:
            db_service: Database service instance
        """
        self.db_service = db_service
    
    async def show_main_menu(self, update: Update, context: CallbackContext):
        """Show main menu to user"""
        try:
            user = update.effective_user
            logger.info(f"=== SHOWING MAIN MENU ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Username: {user.username}")
            
            # Get user data from database
            logger.info("Retrieving user data from database...")
            user_data = await self.db_service.get_user_by_telegram_id(str(user.id))
            if user_data:
                logger.info(f"User found - ID: {user_data.get('id')}, Plan: {user_data.get('plan')}")
            else:
                logger.warning("User not found in database")
            
            # Send main menu
            logger.info("Sending main menu to user...")
            await self._send_main_menu_buttons(update, context)
            
            # Log menu sent event
            logger.info("Logging menu sent event to database...")
            event_data = {
                'user_id': str(user.id),
                'telegram_id': str(user.id),
                'event_time': datetime.now(),
                'event_type': 'menu_sent',
                'user_email': user_data.get('email') if user_data else None,
                'user_device': None,
                'user_plan': user_data.get('plan') if user_data else None,
                'kpi': None,
                'settings_action_trigger': None,
                'function_call_type': None,
                'before_change': None,
                'after_change': None,
                'product_purchase': None
            }
            await self.db_service.log_event(event_data)
            logger.info("Menu sent event logged successfully")
            
            logger.info("=== MAIN MENU DISPLAYED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            await self._send_error_message(update, context)
    
    async def _send_main_menu_buttons(self, update: Update, context: CallbackContext):
        """Send main menu with inline keyboard buttons"""
        try:
            logger.info("=== SENDING MAIN MENU BUTTONS ===")
            
            # Create keyboard
            logger.info("Creating main menu keyboard...")
            keyboard = [
                [
                    InlineKeyboardButton("📊 Stock Analysis", callback_data="analysis_stock"),
                    InlineKeyboardButton("📈 Technical Analysis", callback_data="analysis_technical")
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                    InlineKeyboardButton("💳 Payment", callback_data="payment")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info("Main menu keyboard created successfully")
            
            # Get menu message
            logger.info("Getting menu message text...")
            message_text = get_message('menu', 'en')
            logger.info(f"Menu message: {message_text[:50]}...")
            
            # Send or edit message
            logger.info("Determining message sending method...")
            if hasattr(update, 'callback_query') and update.callback_query:
                logger.info("Editing message for callback query")
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
                logger.info("Message edited successfully")
            else:
                logger.info("Sending new message")
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
                logger.info("Message sent successfully")
            
            logger.info("=== MAIN MENU BUTTONS SENT SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error sending main menu buttons: {e}")
            await self._send_error_message(update, context)
    
    async def handle_callback_query(self, update: Update, context: CallbackContext):
        """
        Handle callback queries for menu actions
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            query = update.callback_query
            await query.answer()  # Answer the callback query
            
            data = query.data
            logger.info(f"Menu handler received callback: {data}")
            
            if data == "analysis_stock":
                await self._handle_stock_analysis_request(update, context)
            elif data == "analysis_technical":
                await self._handle_technical_analysis_request(update, context)
            elif data == "settings":
                logger.info("Menu handler processing settings callback")
                await self._handle_settings_request(update, context)
            elif data == "payment":
                await self._handle_payment_request(update, context)
            elif data == "back_to_menu":
                await self._handle_back_to_menu(update, context)
            elif data.startswith("ticker_"):
                # Handle ticker selection
                ticker = data.replace("ticker_", "")
                await self._handle_ticker_selection(update, context, ticker)
            else:
                logger.warning(f"Unknown callback data in menu handler: {data}")
                await query.edit_message_text("Invalid option selected.")
                
        except Exception as e:
            logger.error(f"Error in menu handler callback query: {e}")
            await self._send_error_message(update, context)
    
    async def handle_menu_selection(self, update: Update, context: CallbackContext):
        """
        Handle menu selection from user (fallback for text input)
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            message_text = sanitize_input(update.message.text.lower())
            
            # Parse menu selection
            if '1' in message_text or 'analysis' in message_text:
                await self._handle_stock_analysis_request(update, context)
            elif '2' in message_text or 'technical' in message_text:
                await self._handle_technical_analysis_request(update, context)
            elif '3' in message_text or 'settings' in message_text:
                await self._handle_settings_request(update, context)
            elif '4' in message_text or 'payment' in message_text:
                await self._handle_payment_request(update, context)
            else:
                # Default: show menu again
                await self.show_main_menu(update, context)
                
        except Exception as e:
            logger.error(f"Error handling menu selection: {e}")
            await update.message.reply_text(
                get_message('errors.general', 'en')
            )
    
    async def _handle_stock_analysis_request(self, update: Update, context: CallbackContext):
        """
        Handle stock analysis menu selection
        
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
            
            # Get user's tickers
            tickers = await self.db_service.get_user_tickers(user_data['user_id'])
            
            if not tickers:
                await self._send_ticker_input_prompt(update, context, "stock_analysis")
            else:
                # Show ticker selection buttons
                await self._send_ticker_selection_buttons(update, context, tickers, "stock_analysis")
                
        except Exception as e:
            logger.error(f"Error handling stock analysis request: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_technical_analysis_request(self, update: Update, context: CallbackContext):
        """
        Handle technical analysis menu selection
        
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
            
            # Check if user has access to technical analysis
            if user_data['plan_type'] == 'free':
                await self._send_premium_required_message(update, context)
                return
            
            # Get user's tickers
            tickers = await self.db_service.get_user_tickers(user_data['user_id'])
            
            if not tickers:
                await self._send_ticker_input_prompt(update, context, "technical_analysis")
            else:
                # Show ticker selection buttons
                await self._send_ticker_selection_buttons(update, context, tickers, "technical_analysis")
                
        except Exception as e:
            logger.error(f"Error handling technical analysis request: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_settings_request(self, update: Update, context: CallbackContext):
        """
        Handle settings menu selection
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            logger.info("Settings button pressed - _handle_settings_request called")
            user = update.effective_user
            telegram_id = str(user.id)
            
            # Get user data
            user_data = await self.db_service.get_user_by_telegram_id(telegram_id)
            if not user_data:
                logger.error(f"User data not found for telegram_id: {telegram_id}")
                await self._send_error_message(update, context)
                return
            
            logger.info(f"User data found, calling settings handler for user: {telegram_id}")
            # Call settings handler to show settings menu
            from telegram_bot.handlers.settings_handler import SettingsHandler
            settings_handler = SettingsHandler(self.db_service)
            await settings_handler._send_settings_buttons(update, context, user_data)
            
        except Exception as e:
            logger.error(f"Error handling settings request: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_payment_request(self, update: Update, context: CallbackContext):
        """
        Handle payment menu selection
        
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
            
            # Check if plan is active
            is_active = await self.db_service.is_plan_active(user_data['user_id'])
            
            if is_active:
                # Show current plan info with buttons
                await self._send_payment_buttons(update, context, user_data)
            else:
                # Plan expired, show upgrade options
                await self._send_upgrade_buttons(update, context)
            
        except Exception as e:
            logger.error(f"Error handling payment request: {e}")
            await self._send_error_message(update, context)
    
    async def _send_ticker_selection_buttons(self, update: Update, context: CallbackContext, 
                                           tickers: list, analysis_type: str):
        """
        Send ticker selection buttons
        
        Args:
            update: Telegram update object
            context: Callback context
            tickers: List of user's tickers
            analysis_type: Type of analysis (stock_analysis or technical_analysis)
        """
        keyboard = []
        
        # Add ticker buttons (2 per row)
        for i in range(0, len(tickers), 2):
            row = []
            row.append(InlineKeyboardButton(tickers[i], callback_data=f"ticker_{tickers[i]}_{analysis_type}"))
            if i + 1 < len(tickers):
                row.append(InlineKeyboardButton(tickers[i + 1], callback_data=f"ticker_{tickers[i + 1]}_{analysis_type}"))
            keyboard.append(row)
        
        # Add "Enter New Ticker" button
        keyboard.append([InlineKeyboardButton("➕ Enter New Ticker", callback_data=f"new_ticker_{analysis_type}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = f"📊 Select a ticker for {analysis_type.replace('_', ' ').title()}:"
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    async def _send_ticker_input_prompt(self, update: Update, context: CallbackContext, analysis_type: str):
        """
        Send ticker input prompt
        
        Args:
            update: Telegram update object
            context: Callback context
            analysis_type: Type of analysis
        """
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = get_message('analysis.ticker_prompt', 'en')
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
        
        # Set context for analysis flow
        context.user_data['analysis_flow'] = analysis_type
        await self.db_service.set_user_state(str(update.effective_user.id), 'analysis_flow')
    
    async def _send_payment_buttons(self, update: Update, context: CallbackContext, user_data: Dict):
        """
        Send payment menu buttons
        
        Args:
            update: Telegram update object
            context: Callback context
            user_data: User data
        """
        # Get plan info
        plan_info = await self.db_service.get_user_plan_info(user_data['user_id'])
        
        plan_message = f"📋 Current Plan: {plan_info['plan_type'].title()}\n"
        plan_message += f"Tickers: {plan_info['amount_tickers_have']}/{plan_info['amount_tickers_allowed']}\n"
        
        if plan_info['plan_end_time']:
            plan_message += f"Expires: {plan_info['plan_end_time'].strftime('%Y-%m-%d')}\n"
        
        plan_message += "\nChoose an option:"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 View Plan", callback_data="payment_view"),
                InlineKeyboardButton("⬆️ Upgrade", callback_data="payment_upgrade")
            ],
            [
                InlineKeyboardButton("🎫 Coupon", callback_data="payment_coupon"),
                InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(plan_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(plan_message, reply_markup=reply_markup)
        
        # Set context for payment flow
        context.user_data['payment_flow'] = True
        await self.db_service.set_user_state(str(update.effective_user.id), 'payment_flow')
    
    async def _send_upgrade_buttons(self, update: Update, context: CallbackContext):
        """
        Send upgrade buttons for expired plans
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        keyboard = [
            [InlineKeyboardButton("⬆️ Upgrade Now", callback_data="payment_upgrade")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = get_message('payment.plan_expired', 'en')
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    async def _send_premium_required_message(self, update: Update, context: CallbackContext):
        """
        Send premium required message
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        keyboard = [
            [InlineKeyboardButton("�� Upgrade to Premium", callback_data="payment_upgrade")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "⚠️ Technical analysis is available in premium plans. Please upgrade to access advanced indicators."
        
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
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = get_message('errors.general', 'en')
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
    
    async def _handle_ticker_selection(self, update: Update, context: CallbackContext, ticker: str):
        """
        Handle ticker selection from buttons
        
        Args:
            update: Telegram update object
            context: Callback context
            ticker: Selected ticker
        """
        try:
            # Extract analysis type from callback data
            callback_data = update.callback_query.data
            analysis_type = callback_data.split('_')[-1]  # Get last part after ticker
            
            # Set the ticker in context for analysis handler
            context.user_data['selected_ticker'] = ticker
            context.user_data['analysis_flow'] = analysis_type
            
            # Send to analysis handler
            from handlers.analysis_handler import AnalysisHandler
            analysis_handler = AnalysisHandler(self.db_service)
            
            if analysis_type == "stock_analysis":
                await analysis_handler._handle_stock_analysis(update, context, ticker)
            elif analysis_type == "technical_analysis":
                await analysis_handler._handle_technical_analysis(update, context, ticker)
                
        except Exception as e:
            logger.error(f"Error handling ticker selection: {e}")
            await self._send_error_message(update, context)
    
    async def _handle_back_to_menu(self, update: Update, context: CallbackContext):
        """
        Handle back to menu request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            # Clear any flow states
            context.user_data.clear()
            await self.db_service.set_user_state(str(update.effective_user.id), None)
            
            # Show main menu using the existing method that handles both callback queries and messages
            await self._send_main_menu_buttons(update, context)
            
        except Exception as e:
            logger.error(f"Error handling back to menu: {e}")
            await self._send_error_message(update, context)
    
    async def _log_menu_event(self, user_id: str, telegram_id: str):
        """
        Log menu sent event
        
        Args:
            user_id: User ID
            telegram_id: Telegram user ID
        """
        try:
            event_data = {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'event_type': 'menu_sent',
                'event_time': datetime.now(),
                'user_device': 'telegram'
            }
            
            await self.db_service.log_event(event_data)
            
        except Exception as e:
            logger.error(f"Error logging menu event: {e}") 