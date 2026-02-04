"""
PumpFun Token Collector using GeckoTerminal API.

Fetches comprehensive Solana memecoin data including:
- Trending pools (highest activity)
- New pools (freshest tokens)
- Token details with market data

GeckoTerminal is free, no auth required, and provides accurate real-time data.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx

GECKO_BASE_URL = "https://api.geckoterminal.com/api/v2"

# Rate limit: be respectful
RATE_LIMIT_DELAY = 0.5  # seconds between requests


@dataclass
class TokenData:
    """Standardized token data structure."""
    token_address: str
    name: str
    symbol: str
    market_cap_usd: float
    liquidity_usd: float
    volume_24h: float
    price_usd: float
    price_change_24h: float
    created_at: Optional[datetime] = None
    is_pumpfun: bool = False
    # Social links
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON from URL with error handling."""
    try:
        resp = await client.get(url, timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
        print(f"  [GeckoTerminal] {url} returned {resp.status_code}")
        return None
    except Exception as e:
        print(f"  [GeckoTerminal] Error fetching {url}: {e}")
        return None


def _parse_pool(pool_data: Dict[str, Any]) -> Optional[TokenData]:
    """Parse a pool from GeckoTerminal API response."""
    try:
        attr = pool_data.get("attributes", {})
        relationships = pool_data.get("relationships", {})
        
        # Get base token address from relationships
        base_token_data = relationships.get("base_token", {}).get("data", {})
        token_id = base_token_data.get("id", "")
        # Token ID format: "solana_<address>"
        token_address = token_id.replace("solana_", "") if token_id.startswith("solana_") else ""
        
        if not token_address:
            return None
        
        name = attr.get("name", "Unknown").split(" / ")[0]  # "TOKEN / SOL" -> "TOKEN"
        
        # Get price and volume data
        fdv = attr.get("fdv_usd")
        market_cap = float(fdv) if fdv else 0.0
        
        reserve = attr.get("reserve_in_usd")
        liquidity = float(reserve) if reserve else 0.0
        
        vol_data = attr.get("volume_usd", {})
        volume_24h = float(vol_data.get("h24", 0) or 0)
        
        price_str = attr.get("base_token_price_usd")
        price_usd = float(price_str) if price_str else 0.0
        
        # Price changes
        price_changes = attr.get("price_change_percentage", {})
        price_change_24h = float(price_changes.get("h24", 0) or 0)
        
        # Pool creation time
        created_str = attr.get("pool_created_at")
        created_at = None
        if created_str:
            try:
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except:
                pass
        
        # Check if PumpFun token (address ends with 'pump')
        is_pumpfun = token_address.lower().endswith("pump")
        
        return TokenData(
            token_address=token_address,
            name=name,
            symbol=name,  # GeckoTerminal uses name as symbol in pool names
            market_cap_usd=market_cap,
            liquidity_usd=liquidity,
            volume_24h=volume_24h,
            price_usd=price_usd,
            price_change_24h=price_change_24h,
            created_at=created_at,
            is_pumpfun=is_pumpfun,
        )
    except Exception as e:
        print(f"  [GeckoTerminal] Error parsing pool: {e}")
        return None


async def _fetch_token_details(client: httpx.AsyncClient, addresses: List[str]) -> Dict[str, Dict]:
    """Fetch detailed token info including social links."""
    details = {}
    
    # GeckoTerminal has a tokens endpoint
    for addr in addresses[:50]:  # Limit batch size
        url = f"{GECKO_BASE_URL}/networks/solana/tokens/{addr}"
        data = await _fetch_json(client, url)
        await asyncio.sleep(RATE_LIMIT_DELAY)
        
        if data and "data" in data:
            token_attr = data["data"].get("attributes", {})
            details[addr] = {
                "name": token_attr.get("name"),
                "symbol": token_attr.get("symbol"),
                "description": token_attr.get("description"),
                "websites": token_attr.get("websites", []),
                "twitter_handle": token_attr.get("twitter_handle"),
            }
    
    return details


async def fetch_pumpfun_tokens(
    limit: int = 500,
    min_volume: float = 100,
    include_bonding_curve: bool = True,
    min_market_cap: float = 0,
) -> List[TokenData]:
    """
    Fetch PumpFun tokens from GeckoTerminal.
    
    Args:
        limit: Maximum number of tokens to return
        min_volume: Minimum 24h volume in USD
        include_bonding_curve: Include tokens still on bonding curve (fresh tokens)
        min_market_cap: Minimum market cap filter
    
    Returns:
        List of TokenData objects
    """
    print(f"[PumpFun Collector] Fetching tokens via GeckoTerminal...")
    print(f"  limit={limit}, min_vol=${min_volume}, bonding_curve={include_bonding_curve}")
    
    tokens: Dict[str, TokenData] = {}  # Dedupe by address
    
    async with httpx.AsyncClient() as client:
        # 1. Fetch trending pools (multiple pages)
        print("  Fetching trending pools...")
        for page in range(1, 6):  # 5 pages = 100 trending pools
            url = f"{GECKO_BASE_URL}/networks/solana/trending_pools?page={page}"
            data = await _fetch_json(client, url)
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
            if not data:
                break
                
            pools = data.get("data", [])
            if not pools:
                break
                
            for pool in pools:
                token = _parse_pool(pool)
                if token and token.token_address not in tokens:
                    # Filter PumpFun tokens
                    if token.is_pumpfun:
                        tokens[token.token_address] = token
            
            print(f"    Page {page}: found {len(pools)} pools, {len(tokens)} PumpFun tokens total")
        
        # 2. Fetch new pools (for fresh/bonding curve tokens)
        if include_bonding_curve:
            print("  Fetching new pools...")
            for page in range(1, 11):  # 10 pages = 200 new pools
                url = f"{GECKO_BASE_URL}/networks/solana/new_pools?page={page}"
                data = await _fetch_json(client, url)
                await asyncio.sleep(RATE_LIMIT_DELAY)
                
                if not data:
                    break
                    
                pools = data.get("data", [])
                if not pools:
                    break
                    
                for pool in pools:
                    token = _parse_pool(pool)
                    if token and token.token_address not in tokens:
                        if token.is_pumpfun:
                            tokens[token.token_address] = token
                
                print(f"    Page {page}: {len(tokens)} PumpFun tokens total")
        
        # 3. Fetch pools by volume for established tokens
        print("  Fetching top volume pools...")
        for page in range(1, 6):
            url = f"{GECKO_BASE_URL}/networks/solana/pools?page={page}&sort=h24_volume_usd_desc"
            data = await _fetch_json(client, url)
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
            if not data:
                break
                
            pools = data.get("data", [])
            if not pools:
                break
                
            for pool in pools:
                token = _parse_pool(pool)
                if token and token.token_address not in tokens:
                    if token.is_pumpfun:
                        tokens[token.token_address] = token
            
            print(f"    Page {page}: {len(tokens)} PumpFun tokens total")
    
    # Convert to list and filter
    result = list(tokens.values())
    
    # Apply filters
    if min_volume > 0:
        result = [t for t in result if t.volume_24h >= min_volume]
    
    if min_market_cap > 0:
        result = [t for t in result if t.market_cap_usd >= min_market_cap]
    
    # Sort by volume (most active first)
    result.sort(key=lambda t: t.volume_24h, reverse=True)
    
    # Limit results
    result = result[:limit]
    
    print(f"[PumpFun Collector] Returning {len(result)} tokens")
    if result:
        top = result[0]
        print(f"  Top token: {top.name} (${top.market_cap_usd:,.0f} mcap, ${top.volume_24h:,.0f} vol)")
    
    return result


# For backward compatibility
async def fetch_tokens_from_dexscreener(*args, **kwargs) -> List[TokenData]:
    """Deprecated: Use fetch_pumpfun_tokens instead."""
    return await fetch_pumpfun_tokens(*args, **kwargs)
