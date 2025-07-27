FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY telegram_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY telegram_bot/ ./telegram_bot/
COPY config/ ./config/

# Run the bot
CMD ["python", "-m", "telegram_bot.main"] 