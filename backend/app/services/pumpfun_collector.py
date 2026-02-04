"""
PumpFun & Solana Meme Token Collector using CoinGecko API.

CoinGecko provides:
- Pre-categorized meme tokens (pump-fun, solana-meme-coins, ai-meme-coins, etc.)
- Accurate market data (mcap, volume, price changes)
- Social links and metadata
- Free tier: 30 calls/minute

This is WAY better than scraping DexScreener or GeckoTerminal.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# CoinGecko categories relevant to Solana memecoins
MEME_CATEGORIES = [
    "pump-fun",           # PumpFun ecosystem tokens
    "solana-meme-coins",  # All Solana memes
    "ai-meme-coins",      # AI agent tokens
]

# Rate limit: 30/min for free tier, so ~2 seconds between calls
RATE_LIMIT_DELAY = 2.0


@dataclass
class TokenData:
    """Standardized token data structure."""
    token_address: str
    name: str
    symbol: str
    market_cap_usd: float
    liquidity_usd: float  # Not directly available from CG, use volume as proxy
    volume_24h: float
    price_usd: float
    price_change_24h: float
    created_at: Optional[datetime] = None
    is_pumpfun: bool = False
    # Category from CoinGecko
    coingecko_category: Optional[str] = None
    coingecko_id: Optional[str] = None
    # Social links
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    # Image
    image_url: Optional[str] = None


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON from URL with error handling."""
    try:
        resp = await client.get(url, timeout=30.0)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            print(f"  [CoinGecko] Rate limited, waiting...")
            await asyncio.sleep(60)
            return None
        print(f"  [CoinGecko] {url} returned {resp.status_code}")
        return None
    except Exception as e:
        print(f"  [CoinGecko] Error fetching {url}: {e}")
        return None


def _parse_coin(coin: Dict[str, Any], category: str) -> Optional[TokenData]:
    """Parse a coin from CoinGecko markets endpoint."""
    try:
        cg_id = coin.get("id", "")
        
        # CoinGecko doesn't give us the on-chain address directly in markets
        # We'll use the coingecko ID as a temporary address and fetch real address later if needed
        # For now, use CG ID with a prefix to distinguish
        token_address = coin.get("id", "")  # Will be replaced with real address
        
        name = coin.get("name", "Unknown")
        symbol = coin.get("symbol", "???").upper()
        
        market_cap = float(coin.get("market_cap") or 0)
        volume_24h = float(coin.get("total_volume") or 0)
        price_usd = float(coin.get("current_price") or 0)
        price_change_24h = float(coin.get("price_change_percentage_24h") or 0)
        
        image_url = coin.get("image")
        
        # Determine if it's a PumpFun token based on category
        is_pumpfun = category == "pump-fun"
        
        return TokenData(
            token_address=token_address,
            name=name,
            symbol=symbol,
            market_cap_usd=market_cap,
            liquidity_usd=volume_24h * 0.1,  # Rough proxy: 10% of daily volume
            volume_24h=volume_24h,
            price_usd=price_usd,
            price_change_24h=price_change_24h,
            is_pumpfun=is_pumpfun,
            coingecko_category=category,
            coingecko_id=cg_id,
            image_url=image_url,
        )
    except Exception as e:
        print(f"  [CoinGecko] Error parsing coin: {e}")
        return None


async def _fetch_token_details(client: httpx.AsyncClient, cg_id: str) -> Optional[Dict]:
    """Fetch detailed token info including contract address and social links."""
    url = f"{COINGECKO_BASE}/coins/{cg_id}"
    params = "?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false"
    
    data = await _fetch_json(client, url + params)
    if not data:
        return None
    
    # Extract Solana contract address
    platforms = data.get("platforms", {})
    solana_address = platforms.get("solana")
    
    # Extract social links
    links = data.get("links", {})
    twitter = links.get("twitter_screen_name")
    telegram = links.get("telegram_channel_identifier")
    websites = links.get("homepage", [])
    website = websites[0] if websites and websites[0] else None
    
    description = data.get("description", {}).get("en", "")
    
    return {
        "solana_address": solana_address,
        "twitter_url": f"https://twitter.com/{twitter}" if twitter else None,
        "telegram_url": f"https://t.me/{telegram}" if telegram else None,
        "website_url": website,
        "description": description[:500] if description else None,
    }


async def fetch_pumpfun_tokens(
    limit: int = 500,
    min_volume: float = 0,
    include_bonding_curve: bool = True,
    min_market_cap: float = 0,
    categories: List[str] = None,
) -> List[TokenData]:
    """
    Fetch Solana meme tokens from CoinGecko.
    
    Args:
        limit: Maximum number of tokens to return
        min_volume: Minimum 24h volume in USD
        include_bonding_curve: Ignored (CG doesn't have bonding curve data)
        min_market_cap: Minimum market cap filter
        categories: Which CoinGecko categories to fetch (default: all meme categories)
    
    Returns:
        List of TokenData objects sorted by market cap
    """
    if categories is None:
        categories = MEME_CATEGORIES
    
    print(f"[CoinGecko Collector] Fetching tokens from categories: {categories}")
    
    tokens: Dict[str, TokenData] = {}  # Dedupe by coingecko_id
    
    async with httpx.AsyncClient() as client:
        for category in categories:
            print(f"  Fetching {category}...")
            
            # Fetch up to 250 tokens per category (CG limit)
            for page in range(1, 4):  # 3 pages × 100 = 300 per category
                url = f"{COINGECKO_BASE}/coins/markets"
                params = f"?vs_currency=usd&category={category}&order=market_cap_desc&per_page=100&page={page}"
                
                data = await _fetch_json(client, url + params)
                await asyncio.sleep(RATE_LIMIT_DELAY)
                
                if not data or len(data) == 0:
                    break
                
                for coin in data:
                    token = _parse_coin(coin, category)
                    if token and token.coingecko_id not in tokens:
                        tokens[token.coingecko_id] = token
                
                print(f"    Page {page}: {len(tokens)} tokens total")
        
        # Fetch detailed info for top tokens (contract addresses, social links)
        print(f"  Fetching details for top {min(50, len(tokens))} tokens...")
        top_tokens = sorted(tokens.values(), key=lambda t: t.market_cap_usd, reverse=True)[:50]
        
        for token in top_tokens:
            details = await _fetch_token_details(client, token.coingecko_id)
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
            if details:
                if details.get("solana_address"):
                    token.token_address = details["solana_address"]
                token.twitter_url = details.get("twitter_url")
                token.telegram_url = details.get("telegram_url")
                token.website_url = details.get("website_url")
                token.description = details.get("description")
    
    # Convert to list and apply filters
    result = list(tokens.values())
    
    if min_volume > 0:
        result = [t for t in result if t.volume_24h >= min_volume]
    
    if min_market_cap > 0:
        result = [t for t in result if t.market_cap_usd >= min_market_cap]
    
    # Sort by market cap
    result.sort(key=lambda t: t.market_cap_usd, reverse=True)
    result = result[:limit]
    
    print(f"[CoinGecko Collector] Returning {len(result)} tokens")
    if result:
        top = result[0]
        print(f"  Top: {top.name} ({top.symbol}) - ${top.market_cap_usd:,.0f} mcap")
    
    return result


async def fetch_category_tokens(category: str, limit: int = 100) -> List[TokenData]:
    """Fetch tokens from a specific CoinGecko category."""
    return await fetch_pumpfun_tokens(limit=limit, categories=[category])


# Convenience functions for specific categories
async def fetch_ai_agent_tokens(limit: int = 100) -> List[TokenData]:
    """Fetch AI meme/agent tokens."""
    return await fetch_category_tokens("ai-meme-coins", limit)


async def fetch_solana_memes(limit: int = 100) -> List[TokenData]:
    """Fetch all Solana meme tokens."""
    return await fetch_category_tokens("solana-meme-coins", limit)
