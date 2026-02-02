"""
PayAttention.Sol Telegram Bot

Simple bot to view trending Solana meme coins at a glance.
Commands:
  /trending - Show top 10 trending coins across all time periods
  /start - Welcome message
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://solana-trends-backend-production.up.railway.app")

# Time windows to display
TIME_WINDOWS = ["1h", "24h", "72h", "168h"]


def format_currency(value: float) -> str:
    """Format currency values for display."""
    if value is None:
        return "-"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


def format_change(current: float, previous: float) -> str:
    """Format market cap change with absolute and percentage."""
    if current is None or previous is None or previous == 0:
        return "- (N/A)"

    change = current - previous
    pct_change = (change / previous) * 100

    sign = "+" if change >= 0 else ""
    emoji = "🟢" if change >= 0 else "🔴"

    return f"{emoji} {sign}{format_currency(abs(change))} ({sign}{pct_change:.1f}%)"


async def fetch_trending_coins(time_window: str) -> list:
    """Fetch top trending coins from the API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"{API_URL}/api/trending/coins"
            print(f"[DEBUG] Fetching: {url} with time_window={time_window}")
            response = await client.get(
                url,
                params={"time_window": time_window, "limit": 10}
            )
            print(f"[DEBUG] Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            print(f"[DEBUG] Got {len(data)} coins for {time_window}")
            return data
        except httpx.HTTPStatusError as e:
            print(f"[DEBUG] HTTP error: {e.response.status_code}")
            if e.response.status_code == 404:
                # Fallback: fetch from acceleration endpoint
                return await fetch_from_acceleration(client, time_window)
            raise
        except Exception as e:
            print(f"Error fetching trending coins: {e}")
            return []


async def fetch_from_acceleration(client: httpx.AsyncClient, time_window: str) -> list:
    """Fallback: fetch top accelerating coins."""
    try:
        response = await client.get(
            f"{API_URL}/api/acceleration/top-coins",
            params={"time_window": time_window, "limit": 10}
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def format_coin_entry(rank: int, coin: dict) -> str:
    """Format a single coin entry for display."""
    name = coin.get("name", "Unknown")[:15]
    symbol = coin.get("symbol", "???")[:8]
    market_cap = coin.get("market_cap") or coin.get("market_cap_usd") or 0
    change_pct = coin.get("change_pct") or coin.get("price_change_24h") or 0
    address = coin.get("token_address") or coin.get("address") or ""

    # Emoji based on rank
    rank_emoji = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"{rank}."

    # Change indicator
    if change_pct > 0:
        change_str = f"🟢 +{change_pct:.1f}%"
    elif change_pct < 0:
        change_str = f"🔴 {change_pct:.1f}%"
    else:
        change_str = "⚪ 0%"

    # Vertigo link
    if address:
        vertigo_link = f"<a href='https://vertigo.sh/tokens/{address}'>Trade</a>"
        return f"{rank_emoji} <b>{symbol}</b> | {format_currency(market_cap)} | {change_str} | {vertigo_link}"

    return f"{rank_emoji} <b>{symbol}</b> | {format_currency(market_cap)} | {change_str}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_text = """
🚀 <b>PayAttention.Sol Bot</b>

Track trending Solana meme coins in real-time!

<b>Commands:</b>
/trending - View top 5 coins for each time period
/top1h - Top 5 coins in the last hour
/top24h - Top 5 coins in 24 hours
/top72h - Top 5 coins in 72 hours
/top168h - Top 5 coins in 7 days

Stay ahead of the metas! 🔥
"""
    await update.message.reply_html(welcome_text)


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - show top 5 coins for each time period."""
    await update.message.reply_text("⏳ Fetching trending coins...")

    message_parts = ["🔥 <b>TRENDING SOLANA COINS</b>\n"]

    for tw in TIME_WINDOWS:
        coins = await fetch_trending_coins(tw)

        tw_label = {
            "1h": "⚡ Last Hour",
            "24h": "📅 24 Hours",
            "72h": "📊 72 Hours (3 Days)",
            "168h": "📈 168 Hours (7 Days)"
        }.get(tw, tw)

        message_parts.append(f"\n<b>{tw_label}</b>")
        message_parts.append("─" * 25)

        if not coins:
            message_parts.append("<i>No data available</i>")
        else:
            for i, coin in enumerate(coins[:5], 1):
                message_parts.append(format_coin_entry(i, coin))

    message_parts.append(f"\n\n🕐 Updated: {datetime.utcnow().strftime('%H:%M UTC')}")
    message_parts.append("💜 <a href='https://payattentiondotsol.vercel.app'>PayAttention.Sol</a>")

    await update.message.reply_html("\n".join(message_parts), disable_web_page_preview=True)


async def top_coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE, time_window: str):
    """Handle individual time window commands."""
    await update.message.reply_text(f"⏳ Fetching top coins for {time_window}...")

    coins = await fetch_trending_coins(time_window)

    tw_label = {
        "1h": "⚡ Last Hour",
        "24h": "📅 24 Hours",
        "72h": "📊 72 Hours (3 Days)",
        "168h": "📈 168 Hours (7 Days)"
    }.get(time_window, time_window)

    message_parts = [
        f"🔥 <b>TOP 5 COINS - {tw_label}</b>",
        "─" * 30,
        ""
    ]

    if not coins:
        message_parts.append("<i>No data available for this time period</i>")
    else:
        for i, coin in enumerate(coins[:5], 1):
            name = coin.get("name", "Unknown")
            symbol = coin.get("symbol", "???")
            market_cap = coin.get("market_cap") or coin.get("market_cap_usd") or 0
            prev_cap = coin.get("prev_market_cap") or market_cap
            change_pct = coin.get("change_pct") or coin.get("price_change_24h") or 0

            rank_emoji = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."

            if change_pct > 0:
                change_emoji = "🟢"
                change_str = f"+{change_pct:.1f}%"
            elif change_pct < 0:
                change_emoji = "🔴"
                change_str = f"{change_pct:.1f}%"
            else:
                change_emoji = "⚪"
                change_str = "0%"

            message_parts.append(
                f"{rank_emoji} <b>{symbol}</b>\n"
                f"   📊 {format_currency(market_cap)}\n"
                f"   {change_emoji} {change_str}\n"
            )

    message_parts.append(f"🕐 {datetime.utcnow().strftime('%H:%M UTC')}")
    message_parts.append("💜 <a href='https://payattentiondotsol.vercel.app'>PayAttention.Sol</a>")

    await update.message.reply_html("\n".join(message_parts), disable_web_page_preview=True)


# Command handlers for each time window
async def top1h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await top_coins_command(update, context, "1h")

async def top24h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await top_coins_command(update, context, "24h")

async def top72h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await top_coins_command(update, context, "72h")

async def top168h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await top_coins_command(update, context, "168h")


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set!")
        print("Create a .env file with your bot token from @BotFather")
        return

    print("🚀 Starting PayAttention.Sol Telegram Bot...")
    print(f"📡 API URL: {API_URL}")

    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("trending", trending_command))
    app.add_handler(CommandHandler("top1h", top1h))
    app.add_handler(CommandHandler("top24h", top24h))
    app.add_handler(CommandHandler("top72h", top72h))
    app.add_handler(CommandHandler("top168h", top168h))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
