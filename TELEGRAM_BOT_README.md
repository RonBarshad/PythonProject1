# Telegram Stock Bot - User Guide

## 🤖 Bot Features

Your Telegram stock bot now includes the following enhanced features:

### 📊 Daily Analysis Messages
- **Automatic daily messages** at a specific time
- **Interactive ticker selection** with your available stocks
- **Quick access buttons** for popular tickers
- **Clear instructions** on how to get analysis

### 🎯 Smart Ticker Analysis
- **Type any ticker symbol** (e.g., "AAPL", "MSFT", "GOOG")
- **Automatic validation** against your stock list
- **Real-time analysis** using AI
- **Error handling** for invalid tickers

### 🔒 Security Features
- **Input validation** to prevent malicious code
- **Message length limits** (max 100 characters)
- **Character filtering** (alphanumeric + basic punctuation only)
- **Ticker format validation** (1-5 letters)

### 💬 Smart Message Handling
- **Greeting recognition** ("hello", "hi", "hey")
- **Thank you responses** ("thanks", "thank you")
- **Random message handling** - shows most recent analysis
- **Helpful error messages** for invalid inputs

## 📱 How to Use

### Getting Started
1. **Start the bot** with `/start`
2. **View your stocks** with `/stocks`
3. **Get daily analysis** with `/menu`

### Requesting Analysis
**Method 1: Type the ticker**
```
AAPL
MSFT
GOOG
```

**Method 2: Use buttons**
- Click the ticker buttons in daily messages
- Use the menu for more options

**Method 3: Natural language**
```
I want to see AAPL analysis
What about MSFT?
Show me GOOGL
```

### Daily Analysis Message
The bot sends a daily message containing:
- 📅 Current date
- 🎯 Your available tickers list
- 💡 Instructions on how to get analysis
- 🚀 Quick access buttons

### Random Messages
If you send any random message, the bot will:
1. **Validate your input** for security
2. **Check if it's a ticker request**
3. **Show your most recent analysis** with the message:
   > "📊 **Hey, this is your most recent analysis**"

## 🔧 Technical Implementation

### Input Validation
```python
def _is_valid_input(self, message: str) -> bool:
    # Length check, character validation, security filtering

def _extract_ticker_from_message(self, message: str) -> str:
    # Regex pattern matching, ticker extraction
```

### Ticker Extraction
```python
def _extract_ticker_from_message(self, message: str) -> str:
    # Clean and uppercase message
    # Regex pattern matching (1-5 letters)
    # Return first valid ticker found
```

### Security Features
- **XSS Prevention**: Blocks script tags and special characters
- **Length Limits**: Prevents message flooding
- **Character Filtering**: Only allows safe characters
- **Ticker Validation**: Ensures valid stock symbols

### Error Handling
- **Invalid ticker**: Shows available tickers list
- **No stocks**: Prompts to add stocks to portfolio
- **Analysis failure**: Graceful error messages
- **Network issues**: Fallback responses

## 🚀 Running the Bot

### Prerequisites
1. **Environment variables** set up in `.env`
2. **Telegram bot token** configured
3. **Python dependencies** installed

### Start the Bot
```bash
python notifications/telegram_sender.py
```

### Test the Bot
```bash
python test_telegram_bot.py
```

## 📋 Configuration

### Environment Variables
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_APP_ID=your_app_id_here
TELEGRAM_API_HASH=your_api_hash_here
```

### Available Tickers
The bot uses tickers from your config:
```json
"admin_tickers": ["IONQ","NVDA","QBTS", "RGTI", "AAPL","IONQ","QBTS","RGTI"]
```

## 🛠️ Customization

### Adding New Tickers
1. Update `admin_tickers` in `config.json`
2. Restart the bot

### Changing Daily Message Time
1. Modify the scheduling logic in `main.py`
2. Set up a cron job or scheduler

### Customizing Messages
1. Edit message templates in `telegram_sender.py`
2. Update welcome and help messages

## 🔍 Troubleshooting

### Common Issues
1. **Bot not responding**: Check bot token and API credentials
2. **No analysis**: Verify AI API keys are set
3. **Invalid ticker**: Ensure ticker is in admin_tickers list
4. **Database errors**: Check MySQL connection

### Debug Mode
Enable debug logging by setting log level to DEBUG in the bot code.

## 📞 Support

For issues or questions:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Test with the provided test script
4. Review the [Telegram Bot API documentation](https://core.telegram.org/bots/api)

---

**Happy trading! 📈🚀** 