"""
PayAttention Telegram Bot

Track trending meme coins on Solana and Base.
Commands:
  /trending - Choose chain and view top trending coins
  /start - Welcome message
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://solana-trends-backend-production.up.railway.app")
DEXSCREENER_URL = "https://api.dexscreener.com"


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


async def fetch_trending_from_dexscreener(chain: str, time_period: str = "h24", limit: int = 10) -> list:
    """Fetch trending tokens from DexScreener for a specific chain and time period.

    time_period: 'm5', 'h1', 'h6', 'h24' for 5min, 1hr, 6hr, 24hr
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            all_tokens = []
            seen = set()

            # Search multiple popular terms to get diverse tokens
            search_terms = ["pump", "pepe", "dog", "cat", "ai", "meme", "moon", "inu", "wojak", "chad"]

            for term in search_terms[:5]:  # Limit searches to avoid rate limits
                try:
                    response = await client.get(
                        f"{DEXSCREENER_URL}/latest/dex/search",
                        params={"q": term}
                    )
                    response.raise_for_status()
                    data = response.json()

                    for pair in data.get("pairs", []):
                        if pair.get("chainId") != chain:
                            continue

                        base = pair.get("baseToken", {})
                        address = base.get("address", "")

                        if address in seen:
                            continue
                        seen.add(address)

                        price_changes = pair.get("priceChange", {})
                        change_val = price_changes.get(time_period)

                        # Only include tokens with valid change data
                        if change_val is None:
                            continue

                        all_tokens.append({
                            "token_address": address,
                            "name": base.get("name", "Unknown"),
                            "symbol": base.get("symbol", "???"),
                            "market_cap": pair.get("marketCap"),
                            "liquidity": pair.get("liquidity", {}).get("usd"),
                            "price": pair.get("priceUsd"),
                            "change_m5": price_changes.get("m5"),
                            "change_h1": price_changes.get("h1"),
                            "change_h6": price_changes.get("h6"),
                            "change_h24": price_changes.get("h24"),
                            "change_pct": change_val,
                            "volume_24h": pair.get("volume", {}).get("h24"),
                            "pair_address": pair.get("pairAddress"),
                        })
                except Exception as e:
                    print(f"Search error for '{term}': {e}")
                    continue

            # Also get boosted tokens for variety
            try:
                boost_response = await client.get(f"{DEXSCREENER_URL}/token-boosts/top/v1")
                boost_response.raise_for_status()
                boost_data = boost_response.json()

                chain_boosts = [t for t in boost_data if t.get("chainId") == chain][:20]
                addresses = [t.get("tokenAddress") for t in chain_boosts if t.get("tokenAddress")]

                if addresses:
                    addr_str = ",".join(addresses[:30])
                    pairs_resp = await client.get(f"{DEXSCREENER_URL}/latest/dex/tokens/{addr_str}")
                    pairs_resp.raise_for_status()

                    for pair in pairs_resp.json().get("pairs", []):
                        if pair.get("chainId") != chain:
                            continue

                        base = pair.get("baseToken", {})
                        address = base.get("address", "")

                        if address in seen:
                            continue
                        seen.add(address)

                        price_changes = pair.get("priceChange", {})
                        change_val = price_changes.get(time_period)

                        if change_val is None:
                            continue

                        all_tokens.append({
                            "token_address": address,
                            "name": base.get("name", "Unknown"),
                            "symbol": base.get("symbol", "???"),
                            "market_cap": pair.get("marketCap"),
                            "liquidity": pair.get("liquidity", {}).get("usd"),
                            "price": pair.get("priceUsd"),
                            "change_pct": change_val,
                            "volume_24h": pair.get("volume", {}).get("h24"),
                            "pair_address": pair.get("pairAddress"),
                        })
            except Exception as e:
                print(f"Boost fetch error: {e}")

            # Sort by the selected time period's change (top gainers first)
            all_tokens.sort(key=lambda x: float(x.get("change_pct") or -999), reverse=True)

            print(f"[DexScreener] Found {len(all_tokens)} tokens for {chain}/{time_period}")
            return all_tokens[:limit]

        except Exception as e:
            print(f"Error fetching from DexScreener: {e}")
            return []


async def fetch_native_price(coin_id: str) -> dict | None:
    """Fetch native token price from CoinGecko."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true"
                }
            )
            response.raise_for_status()
            data = response.json()
            return {
                "price": data[coin_id]["usd"],
                "change_24h": data[coin_id].get("usd_24h_change", 0)
            }
        except Exception as e:
            print(f"Error fetching {coin_id} price: {e}")
            return None


def get_trade_link(chain: str, address: str) -> str:
    """Get the appropriate DEX link for a token."""
    if chain == "solana":
        return f"https://dexscreener.com/solana/{address}"
    elif chain == "base":
        return f"https://dexscreener.com/base/{address}"
    return f"https://dexscreener.com/{chain}/{address}"


def format_coin_entry(rank: int, coin: dict, chain: str) -> str:
    """Format a single coin entry for display."""
    symbol = coin.get("symbol", "???")[:10]
    market_cap = coin.get("market_cap") or 0
    change_pct = coin.get("change_pct") or 0
    address = coin.get("token_address", "")

    rank_emoji = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"{rank}."

    if change_pct and change_pct > 0:
        change_str = f"🟢 +{change_pct:.1f}%"
    elif change_pct and change_pct < 0:
        change_str = f"🔴 {change_pct:.1f}%"
    else:
        change_str = "⚪ 0%"

    trade_link = f"<a href='{get_trade_link(chain, address)}'>Chart</a>"
    return f"{rank_emoji} <b>{symbol}</b> | {format_currency(market_cap)} | {change_str} | {trade_link}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_text = """
🚀 <b>PayAttention Bot</b>

Track trending meme coins on <b>Solana</b> and <b>Base</b>!

<b>Commands:</b>
/trending - Choose chain and view top coins
/sol - Solana trending coins
/base - Base trending coins

Stay ahead of the metas! 🔥
"""
    await update.message.reply_html(welcome_text)


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - show chain selection."""
    keyboard = [
        [
            InlineKeyboardButton("☀️ Solana", callback_data="chain_solana"),
            InlineKeyboardButton("🔵 Base", callback_data="chain_base"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔥 <b>Choose a chain:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def chain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chain selection callback - show time period selection."""
    query = update.callback_query
    await query.answer()

    chain = query.data.replace("chain_", "")

    # Show time period selection
    keyboard = [
        [
            InlineKeyboardButton("⚡ 1H", callback_data=f"period_{chain}_h1"),
            InlineKeyboardButton("📊 6H", callback_data=f"period_{chain}_h6"),
            InlineKeyboardButton("📅 24H", callback_data=f"period_{chain}_h24"),
        ],
        [InlineKeyboardButton("« Back to chains", callback_data="back_to_chains")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chain_emoji = "☀️" if chain == "solana" else "🔵"
    chain_name = chain.upper()

    await query.edit_message_text(
        f"{chain_emoji} <b>{chain_name}</b>\n\nSelect time period for top gainers:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time period selection callback - show trending coins."""
    query = update.callback_query
    await query.answer()

    # Parse callback data: period_solana_h24
    parts = query.data.replace("period_", "").split("_")
    chain = parts[0]
    time_period = parts[1]

    await query.edit_message_text("⏳ Fetching trending coins...")

    # Chain config
    chain_config = {
        "solana": {"emoji": "☀️", "name": "SOLANA", "native": "solana", "native_symbol": "SOL"},
        "base": {"emoji": "🔵", "name": "BASE", "native": "ethereum", "native_symbol": "ETH"},
    }

    time_labels = {
        "h1": "1 Hour",
        "h6": "6 Hours",
        "h24": "24 Hours",
    }

    config = chain_config.get(chain, chain_config["solana"])
    time_label = time_labels.get(time_period, "24 Hours")

    # Fetch trending tokens sorted by selected time period
    coins = await fetch_trending_from_dexscreener(chain, time_period=time_period, limit=10)

    message_parts = [f"{config['emoji']} <b>TOP GAINERS ON {config['name']}</b>"]
    message_parts.append(f"<i>By {time_label} change</i>\n")
    message_parts.append("─" * 28)

    if not coins:
        message_parts.append("\n<i>No trending coins found</i>")
    else:
        for i, coin in enumerate(coins[:10], 1):
            message_parts.append(format_coin_entry(i, coin, chain))

    # Add native token price
    native_data = await fetch_native_price(config["native"])
    if native_data:
        change = native_data["change_24h"]
        emoji = "🟢" if change >= 0 else "🔴"
        sign = "+" if change >= 0 else ""
        message_parts.append(f"\n\n💎 <b>{config['native_symbol']}:</b> ${native_data['price']:.2f} {emoji} {sign}{change:.1f}%")

    message_parts.append(f"\n🕐 {datetime.utcnow().strftime('%H:%M UTC')}")

    # Navigation buttons
    other_chain = "base" if chain == "solana" else "solana"
    other_config = chain_config[other_chain]

    keyboard = [
        [
            InlineKeyboardButton("⚡ 1H", callback_data=f"period_{chain}_h1"),
            InlineKeyboardButton("📊 6H", callback_data=f"period_{chain}_h6"),
            InlineKeyboardButton("📅 24H", callback_data=f"period_{chain}_h24"),
        ],
        [InlineKeyboardButton(f"Switch to {other_config['emoji']} {other_config['name']}", callback_data=f"chain_{other_chain}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "\n".join(message_parts),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )


async def back_to_chains_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to chain selection."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("☀️ Solana", callback_data="chain_solana"),
            InlineKeyboardButton("🔵 Base", callback_data="chain_base"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🔥 <b>Choose a chain:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def sol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct command for Solana trending (24h gainers)."""
    await update.message.reply_text("⏳ Fetching Solana top gainers...")

    coins = await fetch_trending_from_dexscreener("solana", time_period="h24", limit=10)

    message_parts = ["☀️ <b>TOP GAINERS ON SOLANA</b>", "<i>By 24H change</i>\n", "─" * 28]

    if not coins:
        message_parts.append("\n<i>No trending coins found</i>")
    else:
        for i, coin in enumerate(coins[:10], 1):
            message_parts.append(format_coin_entry(i, coin, "solana"))

    native_data = await fetch_native_price("solana")
    if native_data:
        change = native_data["change_24h"]
        emoji = "🟢" if change >= 0 else "🔴"
        sign = "+" if change >= 0 else ""
        message_parts.append(f"\n\n💎 <b>SOL:</b> ${native_data['price']:.2f} {emoji} {sign}{change:.1f}%")

    message_parts.append(f"\n🕐 {datetime.utcnow().strftime('%H:%M UTC')}")

    await update.message.reply_html("\n".join(message_parts), disable_web_page_preview=True)


async def base_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct command for Base trending (24h gainers)."""
    await update.message.reply_text("⏳ Fetching Base top gainers...")

    coins = await fetch_trending_from_dexscreener("base", time_period="h24", limit=10)

    message_parts = ["🔵 <b>TOP GAINERS ON BASE</b>", "<i>By 24H change</i>\n", "─" * 28]

    if not coins:
        message_parts.append("\n<i>No trending coins found</i>")
    else:
        for i, coin in enumerate(coins[:10], 1):
            message_parts.append(format_coin_entry(i, coin, "base"))

    native_data = await fetch_native_price("ethereum")
    if native_data:
        change = native_data["change_24h"]
        emoji = "🟢" if change >= 0 else "🔴"
        sign = "+" if change >= 0 else ""
        message_parts.append(f"\n\n💎 <b>ETH:</b> ${native_data['price']:.2f} {emoji} {sign}{change:.1f}%")

    message_parts.append(f"\n🕐 {datetime.utcnow().strftime('%H:%M UTC')}")

    await update.message.reply_html("\n".join(message_parts), disable_web_page_preview=True)


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set!")
        return

    print("🚀 Starting PayAttention Telegram Bot...")
    print(f"📡 Backend API: {API_URL}")
    print("🔗 Using DexScreener for real-time data")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("trending", trending_command))
    app.add_handler(CommandHandler("sol", sol_command))
    app.add_handler(CommandHandler("base", base_command))
    app.add_handler(CallbackQueryHandler(chain_callback, pattern="^chain_"))
    app.add_handler(CallbackQueryHandler(period_callback, pattern="^period_"))
    app.add_handler(CallbackQueryHandler(back_to_chains_callback, pattern="^back_to_chains$"))

    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
