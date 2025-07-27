"""
Analysis Handler
Handles stock analysis and technical analysis requests
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from telegram import Update
from telegram.ext import CallbackContext
from telegram_bot.config.messages import get_message
from telegram_bot.utils.validators import validate_ticker, sanitize_input

logger = logging.getLogger(__name__)

class AnalysisHandler:
    """
    Handles stock analysis and technical analysis requests
    """
    
    def __init__(self, db_service):
        """
        Initialize analysis handler
        
        Args:
            db_service: Database service instance
        """
        self.db_service = db_service
    
    async def handle_analysis_message(self, update: Update, context: CallbackContext):
        """
        Handle analysis-related messages
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        try:
            message_text = sanitize_input(update.message.text)
            analysis_flow = context.user_data.get('analysis_flow')
            
            if analysis_flow == 'stock_analysis':
                await self._handle_stock_analysis(update, context, message_text)
            elif analysis_flow == 'technical_analysis':
                await self._handle_technical_analysis(update, context, message_text)
            else:
                # Default to stock analysis
                await self._handle_stock_analysis(update, context, message_text)
                
        except Exception as e:
            logger.error(f"Error handling analysis message: {e}")
            await update.message.reply_text(
                get_message('errors.general', 'en')
            )
    
    async def _handle_stock_analysis(self, update: Update, context: CallbackContext, ticker: str):
        """
        Handle stock analysis request
        
        Args:
            update: Telegram update object
            context: Callback context
            ticker: Ticker symbol
        """
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            # Get user data
            user_data = await self.db_service.get_user_by_telegram_id(telegram_id)
            if not user_data:
                await update.message.reply_text(
                    get_message('errors.general', 'en')
                )
                return
            
            # Validate ticker
            if not validate_ticker(ticker):
                await update.message.reply_text(
                    get_message('errors.invalid_input', 'en')
                )
                return
            
            # Check if ticker exists in user's portfolio
            available_tickers = context.user_data.get('available_tickers', [])
            
            # If user provided a number, get ticker from available list
            if ticker.isdigit():
                try:
                    index = int(ticker) - 1
                    if 0 <= index < len(available_tickers):
                        ticker = available_tickers[index]
                    else:
                        await update.message.reply_text(
                            get_message('errors.invalid_input', 'en')
                        )
                        return
                except (ValueError, IndexError):
                    await update.message.reply_text(
                        get_message('errors.invalid_input', 'en')
                    )
                    return
            
            # Check if ticker exists in database
            ticker_exists = await self.db_service.check_ticker_exists(ticker)
            if not ticker_exists:
                await update.message.reply_text(
                    get_message('analysis.ticker_not_found', 'en', ticker=ticker)
                )
                return
            
            # Perform stock analysis using real database data
            analysis_result = await self._perform_stock_analysis(ticker)
            
            if analysis_result:
                # Format analysis result
                analysis_text = self._format_stock_analysis(analysis_result)
                
                await update.message.reply_text(
                    get_message('analysis.analysis_ready', 'en', 
                              ticker=ticker, analysis_text=analysis_text)
                )
                
                # Log the analysis event
                await self._log_analysis_event(user_data['user_id'], telegram_id, 
                                            'stock_analysis_pushed', ticker)
            else:
                await update.message.reply_text(
                    get_message('analysis.ticker_not_found', 'en', ticker=ticker)
                )
            
            # Clear analysis flow
            context.user_data.pop('analysis_flow', None)
            context.user_data.pop('available_tickers', None)
            await self.db_service.set_user_state(telegram_id, None)
            
        except Exception as e:
            logger.error(f"Error in stock analysis: {e}")
            await update.message.reply_text(
                get_message('errors.general', 'en')
            )
    
    async def _handle_technical_analysis(self, update: Update, context: CallbackContext, ticker: str):
        """
        Handle technical analysis request
        
        Args:
            update: Telegram update object
            context: Callback context
            ticker: Ticker symbol
        """
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            # Get user data
            user_data = await self.db_service.get_user_by_telegram_id(telegram_id)
            if not user_data:
                await update.message.reply_text(
                    get_message('errors.general', 'en')
                )
                return
            
            # Validate ticker
            if not validate_ticker(ticker):
                await update.message.reply_text(
                    get_message('errors.invalid_input', 'en')
                )
                return
            
            # Check if user has access to technical analysis
            if user_data['plan_type'] == 'free':
                await update.message.reply_text(
                    get_message('settings.weights_not_available', 'en')
                )
                return
            
            # Check if ticker exists in database
            ticker_exists = await self.db_service.check_ticker_exists(ticker)
            if not ticker_exists:
                await update.message.reply_text(
                    get_message('analysis.ticker_not_found', 'en', ticker=ticker)
                )
                return
            
            # Perform technical analysis using real database data
            analysis_result = await self._perform_technical_analysis(ticker)
            
            if analysis_result:
                # Format technical analysis result
                analysis_text = self._format_technical_analysis(analysis_result)
                
                await update.message.reply_text(
                    get_message('analysis.technical_analysis', 'en', 
                              ticker=ticker, analysis_text=analysis_text)
                )
                
                # Log the analysis event
                await self._log_analysis_event(user_data['user_id'], telegram_id, 
                                            'function_write_call', ticker)
            else:
                await update.message.reply_text(
                    get_message('analysis.ticker_not_found', 'en', ticker=ticker)
                )
            
            # Clear analysis flow
            context.user_data.pop('analysis_flow', None)
            await self.db_service.set_user_state(telegram_id, None)
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            await update.message.reply_text(
                get_message('errors.general', 'en')
            )
    
    async def _perform_stock_analysis(self, ticker: str) -> Optional[Dict]:
        """
        Perform stock analysis using real database data
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Analysis result dictionary or None
        """
        try:
            # Get latest ticker data
            latest_data = await self.db_service.get_latest_ticker_data(ticker)
            if not latest_data:
                return None
            
            # Get price change data
            price_change = await self.db_service.get_ticker_price_change(ticker, 1)
            
            # Get AI analysis
            ai_analysis = await self.db_service.get_latest_analysis(ticker)
            
            # Calculate volume in millions
            volume_millions = latest_data['volume'] / 1000000 if latest_data['volume'] else 0
            
            # Calculate market cap (placeholder - you may need to get this from another source)
            market_cap = latest_data['close_price'] * (latest_data['volume'] or 0) if latest_data['close_price'] else 0
            
            return {
                'ticker': ticker,
                'current_price': latest_data['close_price'],
                'change_percent': price_change['change_percent'] if price_change else 0,
                'volume': latest_data['volume'],
                'volume_millions': volume_millions,
                'market_cap': market_cap,
                'high_price': latest_data['high_price'],
                'low_price': latest_data['low_price'],
                'open_price': latest_data['open_price'],
                'ai_analysis': ai_analysis['text_analysis'] if ai_analysis else None,
                'ai_grade': ai_analysis['grade'] if ai_analysis else None,
                'event_date': latest_data['event_date']
            }
        except Exception as e:
            logger.error(f"Error performing stock analysis: {e}")
            return None
    
    async def _perform_technical_analysis(self, ticker: str) -> Optional[Dict]:
        """
        Perform technical analysis using real database data
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Technical analysis result dictionary or None
        """
        try:
            # Get latest ticker data with technical indicators
            latest_data = await self.db_service.get_latest_ticker_data(ticker)
            if not latest_data:
                return None
            
            # Get historical data for trend analysis
            historical_data = await self.db_service.get_ticker_data_for_period(ticker, 20)
            
            # Determine trend based on moving averages
            trend = "Sideways"
            if latest_data['sma20'] and latest_data['sma50']:
                if latest_data['sma20'] > latest_data['sma50']:
                    trend = "Uptrend"
                elif latest_data['sma20'] < latest_data['sma50']:
                    trend = "Downtrend"
            
            # Determine RSI status
            rsi_status = "Neutral"
            if latest_data['rsi14']:
                if latest_data['rsi14'] > 70:
                    rsi_status = "Overbought"
                elif latest_data['rsi14'] < 30:
                    rsi_status = "Oversold"
            
            # Determine MACD status
            macd_status = "Neutral"
            if latest_data['macd'] and latest_data['macd_signal']:
                if latest_data['macd'] > latest_data['macd_signal']:
                    macd_status = "Bullish"
                else:
                    macd_status = "Bearish"
            
            # Calculate support and resistance levels
            support_levels = []
            resistance_levels = []
            
            if historical_data:
                prices = [d['close_price'] for d in historical_data if d['close_price']]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    current_price = latest_data['close_price']
                    
                    # Simple support/resistance calculation
                    support_levels = [min_price, min_price * 0.95, min_price * 0.90]
                    resistance_levels = [max_price, max_price * 1.05, max_price * 1.10]
            
            return {
                'ticker': ticker,
                'rsi': latest_data['rsi14'],
                'rsi_status': rsi_status,
                'macd': latest_data['macd'],
                'macd_signal': latest_data['macd_signal'],
                'macd_status': macd_status,
                'moving_averages': {
                    'sma_20': latest_data['sma20'],
                    'sma_50': latest_data['sma50'],
                    'sma_200': latest_data['sma200'],
                    'ema_20': latest_data['ema20']
                },
                'support_levels': support_levels,
                'resistance_levels': resistance_levels,
                'trend': trend,
                'current_price': latest_data['close_price'],
                'swing_high': latest_data['swing_high_20'],
                'swing_low': latest_data['swing_low_20'],
                'event_date': latest_data['event_date']
            }
        except Exception as e:
            logger.error(f"Error performing technical analysis: {e}")
            return None
    
    def _format_stock_analysis(self, analysis: Dict) -> str:
        """
        Format stock analysis result for display
        
        Args:
            analysis: Analysis result dictionary
            
        Returns:
            Formatted analysis text
        """
        try:
            text = f"📊 Stock Analysis for {analysis['ticker']}\n\n"
            text += f"💰 Current Price: ${analysis['current_price']:.2f}\n"
            text += f"📈 Change: {analysis['change_percent']:.2f}%\n"
            text += f"📊 Volume: {analysis['volume_millions']:.1f}M\n"
            text += f"📈 High: ${analysis['high_price']:.2f}\n"
            text += f"📉 Low: ${analysis['low_price']:.2f}\n"
            text += f"🔄 Open: ${analysis['open_price']:.2f}\n"
            
            if analysis['ai_analysis']:
                text += f"\n🤖 AI Analysis:\n{analysis['ai_analysis']}\n"
                if analysis['ai_grade']:
                    text += f"Grade: {analysis['ai_grade']:.1f}/10\n"
            
            text += f"\n📅 Date: {analysis['event_date']}"
            
            return text
        except Exception as e:
            logger.error(f"Error formatting stock analysis: {e}")
            return "Error formatting analysis result."
    
    def _format_technical_analysis(self, analysis: Dict) -> str:
        """
        Format technical analysis result for display
        
        Args:
            analysis: Technical analysis result dictionary
            
        Returns:
            Formatted technical analysis text
        """
        try:
            text = f"📊 Technical Analysis for {analysis['ticker']}\n\n"
            
            # RSI
            if analysis['rsi']:
                text += f"📈 RSI (14): {analysis['rsi']:.1f} ({analysis['rsi_status']})\n"
            
            # MACD
            if analysis['macd'] and analysis['macd_signal']:
                text += f"📊 MACD: {analysis['macd']:.3f}\n"
                text += f"📊 Signal: {analysis['macd_signal']:.3f}\n"
                text += f"📊 Status: {analysis['macd_status']}\n"
            
            # Moving Averages
            text += f"📈 Moving Averages:\n"
            ma = analysis['moving_averages']
            if ma['sma_20']:
                text += f"  • SMA 20: ${ma['sma_20']:.2f}\n"
            if ma['sma_50']:
                text += f"  • SMA 50: ${ma['sma_50']:.2f}\n"
            if ma['sma_200']:
                text += f"  • SMA 200: ${ma['sma_200']:.2f}\n"
            if ma['ema_20']:
                text += f"  • EMA 20: ${ma['ema_20']:.2f}\n"
            
            # Support/Resistance
            if analysis['support_levels']:
                text += f"\n🎯 Support Levels: {', '.join([f'${level:.2f}' for level in analysis['support_levels']])}\n"
            if analysis['resistance_levels']:
                text += f"🚀 Resistance Levels: {', '.join([f'${level:.2f}' for level in analysis['resistance_levels']])}\n"
            
            # Swing levels
            if analysis['swing_high']:
                text += f"📈 Swing High: ${analysis['swing_high']:.2f}\n"
            if analysis['swing_low']:
                text += f"📉 Swing Low: ${analysis['swing_low']:.2f}\n"
            
            text += f"\n📈 Trend: {analysis['trend']}\n"
            text += f"💰 Current Price: ${analysis['current_price']:.2f}\n"
            text += f"📅 Date: {analysis['event_date']}"
            
            return text
        except Exception as e:
            logger.error(f"Error formatting technical analysis: {e}")
            return "Error formatting technical analysis result."
    
    async def _log_analysis_event(self, user_id: str, telegram_id: str, 
                                event_type: str, ticker: str):
        """
        Log analysis event
        
        Args:
            user_id: User ID
            telegram_id: Telegram user ID
            event_type: Event type
            ticker: Ticker symbol
        """
        try:
            event_data = {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'event_type': event_type,
                'event_time': datetime.now(),
                'user_device': 'telegram',
                'kpi': ticker,
                'function_call_type': 'stock_analysis'
            }
            
            await self.db_service.log_event(event_data)
            
        except Exception as e:
            logger.error(f"Error logging analysis event: {e}")
    
    async def get_user_portfolio_analysis(self, user_id: str) -> List[Dict]:
        """
        Get analysis for all user's tickers
        
        Args:
            user_id: User ID
            
        Returns:
            List of analysis results
        """
        try:
            tickers = await self.db_service.get_user_tickers(user_id)
            analyses = []
            
            for ticker in tickers:
                analysis = await self._perform_stock_analysis(ticker)
                if analysis:
                    analyses.append(analysis)
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error getting portfolio analysis: {e}")
            return [] 