FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System deps (optional; kept minimal for now)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose web and metrics ports
EXPOSE 8000
EXPOSE 9100

# Default to running the bot; can be overridden by docker-compose for web
CMD ["python", "-m", "stock_bot.main"]