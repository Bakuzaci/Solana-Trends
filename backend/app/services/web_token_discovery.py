"""
Web-based token discovery service using search to find real Solana tokens.

This service periodically searches for trending Solana meme coins to get
real token data when the Moralis API limits are hit.
"""
import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
import random

import httpx


@dataclass
class DiscoveredToken:
    """Token discovered from web search."""
    name: str
    symbol: str
    address: Optional[str] = None
    market_cap: Optional[float] = None
    source: str = "web_search"
    discovered_at: datetime = field(default_factory=datetime.utcnow)


# Cache for discovered tokens to avoid repeated searches
_token_cache: Dict[str, DiscoveredToken] = {}
_last_search_time: Optional[datetime] = None
_search_interval_minutes: int = 30  # Search every 30 minutes


# Well-known Solana meme tokens with verified addresses
KNOWN_TOKENS = [
    # === AI AGENT TOKENS (HOT) ===
    DiscoveredToken(
        name="ai16z",
        symbol="AI16Z",
        address="HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",
        market_cap=2000000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Goatseus Maximus",
        symbol="GOAT",
        address="CzLSujWBLFsSjncfkh59rUFqvafWcY5tzedWJSuypump",
        market_cap=400000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Zerebro",
        symbol="ZEREBRO",
        address="8x5VqbHA8D7NkD52uNuS5nnt3PwA8pLD34ymskeSo2Wn",
        market_cap=45000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="OpenClaw",
        symbol="OPENCLAW",
        address="CxoaKHTGYAUkHwzK5dazVYuG3vvEXExrGznMwX1ipump",
        market_cap=700000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Griffain",
        symbol="GRIFFAIN",
        address="KENJSUYLASHUMfHyy5o4Hp2FdNqZg1AsUPhfH2kYvEP",
        market_cap=150000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Arc",
        symbol="ARC",
        address="61V8vBaqAGMpgDQi4JcAwo1dmBGHsyhzodcPqnEVpump",
        market_cap=100000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="DegenAI",
        symbol="DEGENAI",
        address="Gu3LDkn7Vx3bmCzLafYNKcDxv2mH7YN44NJZFXnypump",
        market_cap=50000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Moltbot",
        symbol="MOLT",
        address="81U1Pe815Ui1ttvDAJa1DusPEUTBn3yurk8GUGwhpump",
        market_cap=17000,
        source="known_token"
    ),

    # === TOP MEME COINS ===
    DiscoveredToken(
        name="Bonk",
        symbol="BONK",
        address="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        market_cap=1500000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="dogwifhat",
        symbol="WIF",
        address="EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
        market_cap=2000000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="cat in a dogs world",
        symbol="MEW",
        address="MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5",
        market_cap=500000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Popcat",
        symbol="POPCAT",
        address="7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
        market_cap=800000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Official Trump",
        symbol="TRUMP",
        address="6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
        market_cap=3000000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Fartcoin",
        symbol="FARTCOIN",
        address="9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        market_cap=400000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Book of Meme",
        symbol="BOME",
        address="ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82",
        market_cap=600000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Slerf",
        symbol="SLERF",
        address="7BgBvyjrZX1YKz4oh9mjb8ZScatkkwb8DzFx7LoiVkM3",
        market_cap=100000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Moo Deng",
        symbol="MOODENG",
        address="ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY",
        market_cap=300000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Peanut the Squirrel",
        symbol="PNUT",
        address="2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump",
        market_cap=250000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Gigachad",
        symbol="GIGA",
        address="63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9",
        market_cap=150000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Ponke",
        symbol="PONKE",
        address="5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC",
        market_cap=90000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Myro",
        symbol="MYRO",
        address="HhJpBhRRn4g56VsyLuT8DL5Bv31HkXqsrahTTUCZeZg4",
        market_cap=80000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Wen",
        symbol="WEN",
        address="WENWENvqqNya429ubCdR81ZmD69brwQaaBYY6p3LCpk",
        market_cap=70000000,
        source="known_token"
    ),

    # === DEFI TOKENS ===
    DiscoveredToken(
        name="Jupiter",
        symbol="JUP",
        address="JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
        market_cap=1200000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Raydium",
        symbol="RAY",
        address="4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        market_cap=800000000,
        source="known_token"
    ),
    DiscoveredToken(
        name="Jito",
        symbol="JTO",
        address="jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
        market_cap=500000000,
        source="known_token"
    ),
]


# Search queries to find trending Solana tokens
SEARCH_QUERIES = [
    "trending Solana meme coins today",
    "new Solana token pump.fun",
    "Solana meme coin pump 100x",
    "best Solana meme coins to buy",
    "viral Solana tokens this week",
    "Solana token Raydium new listing",
    "dog meme coin Solana",
    "cat meme coin Solana",
    "AI meme coin Solana",
    "political meme coin Solana",
]


def _parse_solana_address(text: str) -> Optional[str]:
    """Extract a Solana address from text."""
    # Solana addresses are base58-encoded and typically 32-44 characters
    pattern = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'
    matches = re.findall(pattern, text)
    for match in matches:
        # Filter out common non-address strings
        if not any(x in match.lower() for x in ['http', 'www', 'com', 'org']):
            return match
    return None


def _parse_market_cap(text: str) -> Optional[float]:
    """Parse market cap from text like '$1.5M' or '$2B'."""
    pattern = r'\$([0-9,.]+)\s*([KMBkmb])?'
    match = re.search(pattern, text)
    if match:
        value = float(match.group(1).replace(',', ''))
        multiplier = match.group(2)
        if multiplier:
            multiplier = multiplier.upper()
            if multiplier == 'K':
                value *= 1_000
            elif multiplier == 'M':
                value *= 1_000_000
            elif multiplier == 'B':
                value *= 1_000_000_000
        return value
    return None


async def _fetch_dexscreener_trending() -> List[DiscoveredToken]:
    """Fetch trending tokens from DexScreener API."""
    tokens = []
    try:
        async with httpx.AsyncClient() as client:
            # DexScreener search endpoint for Solana tokens
            response = await client.get(
                "https://api.dexscreener.com/latest/dex/search?q=solana",
                timeout=15.0,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])[:20]
                for pair in pairs:
                    base_token = pair.get("baseToken", {})
                    name = base_token.get("name", "Unknown")
                    symbol = base_token.get("symbol", "???")
                    address = base_token.get("address", "")

                    if address and len(address) >= 32:
                        # Get market cap from FDV or calculate from liquidity
                        fdv = pair.get("fdv")
                        liquidity = pair.get("liquidity", {}).get("usd", 0)
                        market_cap = fdv if fdv else (liquidity * 2 if liquidity else None)

                        tokens.append(DiscoveredToken(
                            name=name,
                            symbol=symbol,
                            address=address,
                            market_cap=market_cap,
                            source="dexscreener"
                        ))
    except Exception as e:
        print(f"Error fetching from DexScreener: {e}")

    return tokens


async def _fetch_jupiter_tokens() -> List[DiscoveredToken]:
    """Fetch verified tokens from Jupiter aggregator."""
    tokens = []
    try:
        async with httpx.AsyncClient() as client:
            # Jupiter strict token list (verified tokens)
            response = await client.get(
                "https://token.jup.ag/strict",
                timeout=15.0,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                # Get some random meme-looking tokens
                for token in random.sample(data, min(30, len(data))):
                    name = token.get("name", "Unknown")
                    symbol = token.get("symbol", "???")
                    address = token.get("address", "")

                    # Filter for meme-like tokens (short symbols, fun names)
                    if address and len(symbol) <= 10:
                        tokens.append(DiscoveredToken(
                            name=name,
                            symbol=symbol,
                            address=address,
                            market_cap=None,  # Jupiter doesn't provide market cap
                            source="jupiter"
                        ))
    except Exception as e:
        print(f"Error fetching from Jupiter: {e}")

    return tokens


async def _fetch_birdeye_trending() -> List[DiscoveredToken]:
    """Try to fetch trending tokens from Birdeye (public endpoint)."""
    tokens = []
    try:
        async with httpx.AsyncClient() as client:
            # Birdeye has some public endpoints
            response = await client.get(
                "https://public-api.birdeye.so/public/tokenlist?sort_by=v24hUSD&sort_type=desc&offset=0&limit=20",
                timeout=15.0,
                headers={
                    "Accept": "application/json",
                    "x-chain": "solana"
                }
            )
            if response.status_code == 200:
                data = response.json()
                for token in data.get("data", {}).get("tokens", [])[:20]:
                    name = token.get("name", "Unknown")
                    symbol = token.get("symbol", "???")
                    address = token.get("address", "")
                    mc = token.get("mc")

                    if address:
                        tokens.append(DiscoveredToken(
                            name=name,
                            symbol=symbol,
                            address=address,
                            market_cap=mc,
                            source="birdeye"
                        ))
    except Exception as e:
        print(f"Error fetching from Birdeye: {e}")

    return tokens


async def discover_tokens_from_web() -> List[DiscoveredToken]:
    """
    Discover real Solana tokens using multiple sources.

    Returns a list of discovered tokens with real addresses.
    """
    global _last_search_time, _token_cache

    now = datetime.utcnow()

    # Check if we should search (rate limit)
    if _last_search_time:
        time_since_search = (now - _last_search_time).total_seconds() / 60
        if time_since_search < _search_interval_minutes:
            # Return cached + known tokens
            cached = list(_token_cache.values())
            if cached:
                print(f"Using {len(cached)} cached tokens (last search {time_since_search:.1f} min ago)")
                return cached + KNOWN_TOKENS

    print("Discovering tokens from web sources...")
    _last_search_time = now

    all_tokens: List[DiscoveredToken] = []

    # Fetch from multiple sources in parallel
    results = await asyncio.gather(
        _fetch_dexscreener_trending(),
        _fetch_jupiter_tokens(),
        _fetch_birdeye_trending(),
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, list):
            all_tokens.extend(result)
        elif isinstance(result, Exception):
            print(f"Source fetch error: {result}")

    # Deduplicate by address
    seen_addresses = set()
    unique_tokens = []
    for token in all_tokens:
        if token.address and token.address not in seen_addresses:
            seen_addresses.add(token.address)
            unique_tokens.append(token)
            _token_cache[token.address] = token

    print(f"Discovered {len(unique_tokens)} unique tokens from web sources")

    # Always include known tokens
    for known in KNOWN_TOKENS:
        if known.address not in seen_addresses:
            unique_tokens.append(known)

    return unique_tokens


def get_real_token_addresses() -> Dict[str, str]:
    """
    Get a mapping of symbol -> address for real tokens.

    This is used to make mock data more realistic by using
    real addresses that link to actual tokens on Axiom/Solscan.
    """
    addresses = {}

    # Start with known tokens
    for token in KNOWN_TOKENS:
        if token.address:
            addresses[token.symbol] = token.address

    # Add cached tokens
    for token in _token_cache.values():
        if token.address and token.symbol not in addresses:
            addresses[token.symbol] = token.address

    return addresses


def get_cached_tokens() -> List[DiscoveredToken]:
    """Get all cached discovered tokens."""
    return list(_token_cache.values()) + KNOWN_TOKENS


async def refresh_token_cache():
    """Force refresh the token cache."""
    global _last_search_time
    _last_search_time = None  # Reset to force new search
    return await discover_tokens_from_web()
