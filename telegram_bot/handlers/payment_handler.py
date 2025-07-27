"""
Payment Handler
Handles payment and subscription management
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram_bot.config.messages import get_message
from telegram_bot.config.plans import get_all_plans, get_plan_by_name
from telegram_bot.utils.validators import validate_coupon_code, sanitize_input

logger = logging.getLogger(__name__)

class PaymentHandler:
    """
    Handles payment and subscription management
    """
    
    def __init__(self, db_service):
        """
        Initialize payment handler
        
        Args:
            db_service: Database service instance
        """
        self.db_service = db_service
    
    async def handle_callback_query(self, update: Update, context: CallbackContext):
        """
        Handle callback queries for payment buttons
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            query = update.callback_query
            await query.answer()  # Answer the callback query
            
            data = query.data
            
            if data == "payment_view":
                await self._handle_view_current_plan(update, context)
            elif data == "payment_upgrade":
                await self._handle_upgrade_plan(update, context)
            elif data == "payment_coupon":
                await self._handle_coupon_entry(update, context)
            elif data == "back_to_menu":
                await self._handle_back_to_menu(update, context)
            elif data.startswith("plan_select_"):
                plan_name = data.replace("plan_select_", "")
                # Logic to initiate payment for selected plan
                await query.edit_message_text(f"You selected {plan_name.title()} plan. Payment integration coming soon!")
                await self._send_payment_buttons(update, context, await self.db_service.get_user_by_telegram_id(str(update.effective_user.id)))
            else:
                await query.edit_message_text("Invalid option selected.")
                
        except Exception as e:
            logger.error(f"Error handling payment callback query: {e}")
            await update.callback_query.answer("Error occurred. Please try again.")

    async def handle_payment_message(self, update: Update, context: CallbackContext):
        """
        Handle payment-related messages
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            message_text = sanitize_input(update.message.text.lower())
            
            # Parse payment selection
            if '1' in message_text or 'view' in message_text:
                await self._handle_view_current_plan(update, context)
            elif '2' in message_text or 'upgrade' in message_text:
                await self._handle_upgrade_plan(update, context)
            elif '3' in message_text or 'coupon' in message_text:
                await self._handle_coupon_entry(update, context)
            elif '4' in message_text or 'back' in message_text:
                await self._handle_back_to_menu(update, context)
            else:
                # Show payment menu again
                await update.message.reply_text(
                    get_message('payment.menu', 'en')
                )
                
        except Exception as e:
            logger.error(f"Error handling payment message: {e}")
            await update.message.reply_text(
                get_message('errors.general', 'en')
            )
    
    async def _handle_view_current_plan(self, update: Update, context: CallbackContext):
        """
        Handle view current plan request
        
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
                error_message = get_message('errors.general', 'en')
                if hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.edit_message_text(error_message)
                else:
                    await update.message.reply_text(error_message)
                return
            
            # Get plan info
            plan_info = await self.db_service.get_user_plan_info(user_data['user_id'])
            
            if plan_info:
                plan_message = f"📋 Current Plan: {plan_info['plan_type'].title()}\n"
                plan_message += f"Tickers: {plan_info['amount_tickers_have']}/{plan_info['amount_tickers_allowed']}\n"
                
                if plan_info['plan_end_time']:
                    plan_message += f"Expires: {plan_info['plan_end_time'].strftime('%Y-%m-%d')}\n"
                
                plan_message += "\n" + get_message('payment.menu', 'en')
                
                # Check if this is a callback query or regular message
                if hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.edit_message_text(plan_message)
                else:
                    await update.message.reply_text(plan_message)
            else:
                error_message = get_message('errors.general', 'en')
                if hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.edit_message_text(error_message)
                else:
                    await update.message.reply_text(error_message)
            
        except Exception as e:
            logger.error(f"Error handling view current plan: {e}")
            error_message = get_message('errors.general', 'en')
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
    
    async def _handle_upgrade_plan(self, update: Update, context: CallbackContext):
        """
        Handle upgrade plan request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            # Get available plans
            plans = get_all_plans()
            
            # Format plans list
            plans_list = ""
            for plan_id, plan in plans.items():
                if plan_id != 'free':  # Don't show free plan as upgrade option
                    plans_list += f"• {plan['name']}: ${plan['price']}/month\n"
                    plans_list += f"  Features: {', '.join(plan['features'][:3])}...\n\n"
            
            message_text = get_message('payment.available_plans', 'en', plans_list=plans_list)
            
            # Check if this is a callback query or regular message
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text)
            else:
                await update.message.reply_text(message_text)
            
            context.user_data['payment_action'] = 'upgrade_plan'
            context.user_data['available_plans'] = list(plans.keys())
            
        except Exception as e:
            logger.error(f"Error handling upgrade plan: {e}")
            error_message = get_message('errors.general', 'en')
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
    
    async def _handle_coupon_entry(self, update: Update, context: CallbackContext):
        """
        Handle coupon entry request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            message_text = get_message('payment.coupon_prompt', 'en')
            
            # Check if this is a callback query or regular message
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text)
            else:
                await update.message.reply_text(message_text)
                
            context.user_data['payment_action'] = 'coupon_entry'
            
        except Exception as e:
            logger.error(f"Error handling coupon entry: {e}")
            error_message = get_message('errors.general', 'en')
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
    
    async def _handle_back_to_menu(self, update: Update, context: CallbackContext):
        """
        Handle back to menu request
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            # Clear payment context
            context.user_data.clear()
            await self.db_service.set_user_state(str(update.effective_user.id), None)
            
            # Show main menu
            message_text = get_message('menu', 'en')
            
            # Check if this is a callback query or regular message
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(message_text)
            else:
                await update.message.reply_text(message_text)
            
        except Exception as e:
            logger.error(f"Error handling back to menu: {e}")
            error_message = get_message('errors.general', 'en')
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
    
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

    async def _log_payment_event(self, user_id: str, telegram_id: str, 
                               event_type: str, product_purchase: str = None):
        """
        Log payment event
        
        Args:
            user_id: User ID
            telegram_id: Telegram user ID
            event_type: Event type
            product_purchase: Product purchased
        """
        try:
            event_data = {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'event_type': event_type,
                'event_time': datetime.now(),
                'user_device': 'telegram',
                'product_purchase': product_purchase
            }
            
            await self.db_service.log_event(event_data)
            
        except Exception as e:
            logger.error(f"Error logging payment event: {e}") 

    async def show_payment_options(self, update: Update, context: CallbackContext):
        """Show payment options to user"""
        try:
            user = update.effective_user
            logger.info(f"=== SHOWING PAYMENT OPTIONS ===")
            logger.info(f"User ID: {user.id}")
            logger.info(f"Username: {user.username}")
            
            # Get user data
            logger.info("Retrieving user data from database...")
            user_data = await self.db_service.get_user_by_telegram_id(str(user.id))
            if user_data:
                logger.info(f"User found - ID: {user_data.get('id')}, Plan: {user_data.get('plan')}")
            else:
                logger.warning("User not found in database")
            
            # Create payment options message
            logger.info("Creating payment options message...")
            message_text = get_message('payment.options', 'en')
            logger.info(f"Payment message: {message_text[:50]}...")
            
            # Create keyboard
            logger.info("Creating payment options keyboard...")
            keyboard = [
                [
                    InlineKeyboardButton("💳 Upgrade to Premium", callback_data="payment_upgrade")
                ],
                [
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info("Payment options keyboard created successfully")
            
            # Send or edit message
            logger.info("Determining message sending method...")
            if hasattr(update, 'callback_query') and update.callback_query:
                logger.info("Editing message for callback query")
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
                logger.info("Payment options message edited successfully")
            else:
                logger.info("Sending new message")
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
                logger.info("Payment options message sent successfully")
            
            # Set user state
            logger.info("Setting user state to payment_flow...")
            await self.db_service.set_user_state(str(user.id), 'payment_flow')
            logger.info("User state set to payment_flow")
            
            logger.info("=== PAYMENT OPTIONS DISPLAYED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error showing payment options: {e}")
            await self._send_error_message(update, context) 

    async def handle_coupon_code(self, update: Update, context: CallbackContext, coupon_code: str):
        """Handle coupon code entered by user"""
        try:
            logger.info(f"=== HANDLING COUPON CODE ===")
            user = update.effective_user
            logger.info(f"User ID: {user.id}")
            logger.info(f"Coupon Code: {coupon_code}")
            
            # Validate coupon code
            logger.info("Validating coupon code...")
            from telegram_bot.utils.validators import validate_coupon_code
            if not validate_coupon_code(coupon_code):
                logger.warning("Invalid coupon code format")
                await update.message.reply_text(
                    get_message('payment.coupon_invalid', 'en')
                )
                return
            
            # Check if coupon exists in database
            logger.info("Checking coupon in database...")
            coupon_info = await self._get_coupon_info(coupon_code)
            
            if not coupon_info:
                logger.warning("Coupon not found in database")
                await update.message.reply_text(
                    get_message('payment.coupon_invalid', 'en')
                )
                return
            
            # Check if coupon is valid for this user
            logger.info("Validating coupon for user...")
            validation_result = await self._validate_coupon_for_user(coupon_code, str(user.id))
            
            if not validation_result['valid']:
                logger.warning(f"Coupon validation failed: {validation_result['reason']}")
                await update.message.reply_text(
                    get_message('payment.coupon_invalid', 'en')
                )
                return
            
            # Apply coupon
            logger.info("Applying coupon...")
            await self._apply_coupon_to_user(coupon_code, str(user.id))
            
            # Show success message
            discount_percent = coupon_info.get('discount_percent', 0)
            logger.info(f"Coupon applied successfully with {discount_percent}% discount")
            
            success_message = get_message('payment.coupon_applied', 'en').format(
                discount=discount_percent
            )
            
            await update.message.reply_text(success_message)
            
            # Show payment options
            logger.info("Showing payment options after coupon application...")
            await self.show_payment_options(update, context)
            
            logger.info("=== COUPON CODE HANDLED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"Error handling coupon code: {e}")
            await update.message.reply_text(
                get_message('payment.coupon_invalid', 'en')
            ) 

    async def _get_coupon_info(self, coupon_code: str) -> Optional[Dict]:
        """Get coupon information from database"""
        try:
            logger.info(f"Getting coupon info for: {coupon_code}")
            
            # For now, implement basic coupon logic
            # In production, this would query the database
            valid_coupons = {
                'friends_first_time_25pct': {
                    'discount_percent': 100,
                    'valid_until': '2025-12-31',
                    'max_uses': 100,
                    'used_count': 0
                },
                'welcome_10pct': {
                    'discount_percent': 10,
                    'valid_until': '2025-12-31',
                    'max_uses': 50,
                    'used_count': 0
                }
            }
            
            if coupon_code in valid_coupons:
                logger.info(f"Coupon found: {valid_coupons[coupon_code]}")
                return valid_coupons[coupon_code]
            else:
                logger.info("Coupon not found in valid coupons list")
                return None
                
        except Exception as e:
            logger.error(f"Error getting coupon info: {e}")
            return None
    
    async def _validate_coupon_for_user(self, coupon_code: str, telegram_id: str) -> Dict:
        """Validate if coupon can be used by this user"""
        try:
            logger.info(f"Validating coupon {coupon_code} for user {telegram_id}")
            
            # For now, return valid for all users
            # In production, check if user has already used this coupon
            return {
                'valid': True,
                'reason': None
            }
            
        except Exception as e:
            logger.error(f"Error validating coupon for user: {e}")
            return {
                'valid': False,
                'reason': 'Validation error'
            }
    
    async def _apply_coupon_to_user(self, coupon_code: str, telegram_id: str) -> bool:
        """Apply coupon to user account"""
        try:
            logger.info(f"Applying coupon {coupon_code} to user {telegram_id}")
            
            # For now, just log the application
            # In production, this would update the database
            logger.info("Coupon applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying coupon to user: {e}")
            return False 