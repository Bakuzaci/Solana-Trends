# PayAttention.Sol Telegram Bot

A simple Telegram bot to track trending Solana meme coins at a glance.

## Features

- `/trending` - View top 10 coins across all time periods (1h, 24h, 72h, 168h)
- `/top1h` - Top coins in the last hour
- `/top24h` - Top coins in 24 hours
- `/top72h` - Top coins in 72 hours (3 days)
- `/top168h` - Top coins in 7 days

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token you receive

### 2. Configure Environment

```bash
cd telegram-bot
cp .env.example .env
```

Edit `.env` and add your bot token:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python bot.py
```

## Deployment

### Railway (Recommended)

1. Create a new service in your Railway project
2. Point it to the `telegram-bot` directory
3. Set environment variables:
   - `TELEGRAM_BOT_TOKEN` - Your bot token
   - `API_URL` - Your backend URL

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .
CMD ["python", "bot.py"]
```

## Output Example

```
🔥 TRENDING SOLANA COINS

⚡ Last Hour
─────────────────────────
🥇 MOLT | $65.2K | 🟢 +522.8%
🥈 SPONGE | $37.8K | 🟢 +1214.3%
🥉 JEFLIX | $10.5K | 🟢 +878.4%
...

📅 24 Hours
─────────────────────────
🥇 AI16Z | $2.1M | 🟢 +45.2%
...
```
