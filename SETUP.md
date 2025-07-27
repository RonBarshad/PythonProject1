# Stock Bot Setup Guide

## 🔐 Environment Variables Setup

This project uses environment variables to keep sensitive data secure. Follow these steps to set up your environment:

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Environment File
Create a `.env` file in the project root with your actual API keys and credentials:

```env
# OpenAI API Key
OPENAI_API_KEY=your_actual_openai_api_key_here

# Finnhub API Key
FINNHUB_API_KEY=your_actual_finnhub_api_key_here

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY=your_actual_alpha_vantage_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_database_password_here
DB_NAME=Stocks_data

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_app_password_here

# Telegram Configuration
TELEGRAM_APP_ID=your_telegram_app_id_here
TELEGRAM_API_HASH=your_telegram_api_hash_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_BOT_NAME=Daily_stock_alert
TELEGRAM_BOT_USERNAME=your_bot_username_here
```

### Step 3: Get Your API Keys

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

#### Finnhub API Key
1. Go to [Finnhub](https://finnhub.io/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Copy the key to your `.env` file

#### Alpha Vantage API Key
1. Go to [Alpha Vantage](https://www.alphavantage.co/)
2. Sign up for a free API key
3. Copy the key to your `.env` file

#### Gmail App Password (for SMTP)
1. Go to your Google Account settings
2. Enable 2-factor authentication
3. Generate an App Password for "Mail"
4. Use this password in your `.env` file

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Get your bot token
4. Copy the token to your `.env` file

### Step 4: Database Setup
1. Install MySQL on your system
2. Create a database named `Stocks_data`
3. Update the database credentials in your `.env` file

### Step 5: Test Your Setup
```bash
python -c "from config.config import get; print('Setup successful!')"
```

## 🔒 Security Notes

- **Never commit your `.env` file** to version control
- **Never share your API keys** publicly
- The `config.json` file contains placeholder values only
- Your actual credentials are stored in the `.env` file

## 🚀 Running the Application

Once your environment is set up, you can run the stock bot:

```bash
python main.py
```

## 📁 File Structure

- `.env` - Your actual API keys and credentials (not in version control)
- `config/config.json` - Template with placeholder values
- `config/config.template.json` - Example structure for reference
- `SETUP.md` - This setup guide

## 🆘 Troubleshooting

If you get import errors:
1. Make sure `python-dotenv` is installed: `pip install python-dotenv`
2. Check that your `.env` file is in the project root
3. Verify all required API keys are set in the `.env` file

If you get database connection errors:
1. Make sure MySQL is running
2. Verify database credentials in `.env`
3. Check that the `Stocks_data` database exists 