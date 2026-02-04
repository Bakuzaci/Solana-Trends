"""
PumpFun token collector using DexScreener API.

Fetches Solana tokens from DexScreener (free, no auth required),
filters for PumpFun tokens, and enriches with market data.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

import httpx


@dataclass
class TokenData:
    """Represents token data from the API."""
    token_address: str
    name: str
    symbol: str
    created_at: datetime
    market_cap_usd: Optional[float] = None
    liquidity_usd: Optional[float] = None
    price_usd: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_pumpfun(self) -> bool:
        """Check if token is from PumpFun (address ends in 'pump')."""
        return self.token_address.lower().endswith('pump')


class PumpFunCollector:
    """
    Collects PumpFun token data from DexScreener.
    
    DexScreener is free and provides real market data.
    PumpFun tokens are identified by addresses ending in 'pump'.
    """
    
    BASE_URL = "https://api.dexscreener.com"
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()
    
    async def _ensure_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_latest_tokens(self, limit: int = 100) -> List[TokenData]:
        """
        Fetch latest Solana token profiles from DexScreener.
        
        Returns tokens that have recently created profiles (active projects).
        """
        await self._ensure_client()
        tokens = []
        
        try:
            response = await self.client.get(f"{self.BASE_URL}/token-profiles/latest/v1")
            response.raise_for_status()
            data = response.json()
            
            # Filter for Solana tokens
            solana_tokens = [t for t in data if t.get("chainId") == "solana"][:limit]
            
            for item in solana_tokens:
                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name="",  # Will be enriched
                    symbol="",  # Will be enriched
                    created_at=datetime.utcnow(),
                    metadata={
                        "source": "dexscreener_profiles",
                        "description": item.get("description", ""),
                        "links": item.get("links", []),
                    }
                )
                tokens.append(token)
            
            print(f"[PumpFunCollector] Fetched {len(tokens)} latest profiles")
            
        except Exception as e:
            print(f"[PumpFunCollector] Error fetching latest: {e}")
        
        return tokens
    
    async def fetch_boosted_tokens(self, limit: int = 50) -> List[TokenData]:
        """
        Fetch boosted/trending Solana tokens from DexScreener.
        
        These are tokens with paid promotion (indicates active community).
        """
        await self._ensure_client()
        tokens = []
        
        try:
            response = await self.client.get(f"{self.BASE_URL}/token-boosts/top/v1")
            response.raise_for_status()
            data = response.json()
            
            # Filter for Solana tokens
            solana_tokens = [t for t in data if t.get("chainId") == "solana"][:limit]
            
            for item in solana_tokens:
                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name="",
                    symbol="",
                    created_at=datetime.utcnow(),
                    metadata={
                        "source": "dexscreener_boosts",
                        "description": item.get("description", ""),
                        "boost_amount": item.get("totalAmount", 0),
                    }
                )
                tokens.append(token)
            
            print(f"[PumpFunCollector] Fetched {len(tokens)} boosted tokens")
            
        except Exception as e:
            print(f"[PumpFunCollector] Error fetching boosted: {e}")
        
        return tokens
    
    async def search_tokens(self, query: str, limit: int = 50) -> List[TokenData]:
        """
        Search for Solana tokens by keyword.
        
        Useful for finding tokens in specific categories.
        """
        await self._ensure_client()
        tokens = []
        seen_addresses: Set[str] = set()
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/latest/dex/search",
                params={"q": query}
            )
            response.raise_for_status()
            data = response.json()
            
            pairs = data.get("pairs", [])
            solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
            
            for pair in solana_pairs[:limit]:
                base_token = pair.get("baseToken", {})
                address = base_token.get("address", "")
                
                if address in seen_addresses:
                    continue
                seen_addresses.add(address)
                
                token = TokenData(
                    token_address=address,
                    name=base_token.get("name", "Unknown"),
                    symbol=base_token.get("symbol", "???"),
                    created_at=datetime.utcnow(),
                    market_cap_usd=pair.get("marketCap"),
                    liquidity_usd=pair.get("liquidity", {}).get("usd"),
                    price_usd=float(pair.get("priceUsd", 0) or 0),
                    price_change_24h=pair.get("priceChange", {}).get("h24"),
                    volume_24h=pair.get("volume", {}).get("h24"),
                    metadata={
                        "source": "dexscreener_search",
                        "query": query,
                        "pair_address": pair.get("pairAddress"),
                        "dex": pair.get("dexId"),
                    }
                )
                tokens.append(token)
            
            print(f"[PumpFunCollector] Search '{query}' found {len(tokens)} tokens")
            
        except Exception as e:
            print(f"[PumpFunCollector] Error searching '{query}': {e}")
        
        return tokens
    
    async def enrich_with_market_data(self, tokens: List[TokenData]) -> List[TokenData]:
        """
        Enrich tokens with market data from DexScreener pairs endpoint.
        
        Fetches price, market cap, volume, and 24h change for each token.
        """
        if not tokens:
            return tokens
        
        await self._ensure_client()
        
        # Batch addresses (DexScreener allows up to 30 per request)
        addresses = [t.token_address for t in tokens if t.token_address]
        batch_size = 30
        enriched_data: Dict[str, Dict] = {}
        
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            address_str = ",".join(batch)
            
            try:
                response = await self.client.get(
                    f"{self.BASE_URL}/latest/dex/tokens/{address_str}"
                )
                response.raise_for_status()
                data = response.json()
                
                for pair in data.get("pairs", []):
                    if pair.get("chainId") != "solana":
                        continue
                    
                    base_token = pair.get("baseToken", {})
                    address = base_token.get("address", "")
                    
                    # Keep best pair per token (highest liquidity)
                    new_liq = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                    if address in enriched_data:
                        existing_liq = enriched_data[address].get("liquidity_usd", 0) or 0
                        if new_liq <= existing_liq:
                            continue
                    
                    enriched_data[address] = {
                        "name": base_token.get("name"),
                        "symbol": base_token.get("symbol"),
                        "market_cap_usd": pair.get("marketCap"),
                        "liquidity_usd": new_liq if new_liq > 0 else None,
                        "price_usd": float(pair.get("priceUsd", 0) or 0),
                        "price_change_24h": pair.get("priceChange", {}).get("h24"),
                        "volume_24h": pair.get("volume", {}).get("h24"),
                        "pair_created_at": pair.get("pairCreatedAt"),
                    }
                
            except Exception as e:
                print(f"[PumpFunCollector] Error enriching batch: {e}")
            
            # Small delay between batches
            if i + batch_size < len(addresses):
                await asyncio.sleep(0.3)
        
        # Update tokens with enriched data
        for token in tokens:
            if token.token_address in enriched_data:
                data = enriched_data[token.token_address]
                token.name = data.get("name") or token.name or "Unknown"
                token.symbol = data.get("symbol") or token.symbol or "???"
                token.market_cap_usd = data.get("market_cap_usd")
                token.liquidity_usd = data.get("liquidity_usd")
                token.price_usd = data.get("price_usd")
                token.price_change_24h = data.get("price_change_24h")
                token.volume_24h = data.get("volume_24h")
                
                # Parse creation time if available
                created_ms = data.get("pair_created_at")
                if created_ms:
                    try:
                        token.created_at = datetime.fromtimestamp(created_ms / 1000)
                    except:
                        pass
        
        print(f"[PumpFunCollector] Enriched {len(enriched_data)} tokens with market data")
        return tokens
    
    async def fetch_all(
        self,
        limit: int = 100,
        pumpfun_only: bool = True,
        min_volume: float = 0,
        min_mcap: float = 0,
    ) -> List[TokenData]:
        """
        Fetch and combine tokens from multiple sources.
        
        Args:
            limit: Maximum tokens to return
            pumpfun_only: Only return PumpFun tokens (address ends in 'pump')
            min_volume: Minimum 24h volume filter
            min_mcap: Minimum market cap filter
        
        Returns:
            List of TokenData with market data, sorted by volume
        """
        await self._ensure_client()
        
        # Collect from multiple sources in parallel
        latest_task = self.fetch_latest_tokens(limit)
        boosted_task = self.fetch_boosted_tokens(limit // 2)
        
        latest, boosted = await asyncio.gather(latest_task, boosted_task)
        
        # Combine and deduplicate
        seen_addresses: Set[str] = set()
        all_tokens: List[TokenData] = []
        
        for token in boosted + latest:  # Prioritize boosted
            if token.token_address and token.token_address not in seen_addresses:
                seen_addresses.add(token.token_address)
                all_tokens.append(token)
        
        # Filter for PumpFun if requested
        if pumpfun_only:
            all_tokens = [t for t in all_tokens if t.is_pumpfun]
            print(f"[PumpFunCollector] {len(all_tokens)} PumpFun tokens after filter")
        
        # Enrich with market data
        all_tokens = await self.enrich_with_market_data(all_tokens)
        
        # Apply volume/mcap filters
        if min_volume > 0:
            all_tokens = [t for t in all_tokens if (t.volume_24h or 0) >= min_volume]
        if min_mcap > 0:
            all_tokens = [t for t in all_tokens if (t.market_cap_usd or 0) >= min_mcap]
        
        # Sort by volume (most active first)
        all_tokens.sort(key=lambda t: t.volume_24h or 0, reverse=True)
        
        # Remove tokens with no name (failed enrichment)
        all_tokens = [t for t in all_tokens if t.name and t.name != "Unknown"]
        
        print(f"[PumpFunCollector] Returning {len(all_tokens[:limit])} tokens")
        return all_tokens[:limit]


# Convenience functions
async def fetch_pumpfun_tokens(
    limit: int = 100,
    min_volume: float = 0,
    min_mcap: float = 0,
    include_bonding_curve: bool = True,
) -> List[TokenData]:
    """
    Fetch PumpFun tokens with market data.
    
    This is the main entry point for the data collector.
    
    Args:
        limit: Maximum tokens to return
        min_volume: Minimum 24h volume filter
        min_mcap: Minimum market cap filter  
        include_bonding_curve: If True, includes tokens still on bonding curve
                              (no liquidity yet). These are the freshest tokens.
    """
    async with PumpFunCollector() as collector:
        tokens = await collector.fetch_all(
            limit=limit,
            pumpfun_only=True,
            min_volume=min_volume,
            min_mcap=min_mcap,
        )
        
        if not include_bonding_curve:
            # Filter out tokens without liquidity (still on bonding curve)
            tokens = [t for t in tokens if t.liquidity_usd and t.liquidity_usd > 0]
        
        return tokens


async def fetch_all_solana_tokens(
    limit: int = 100,
    min_volume: float = 0,
) -> List[TokenData]:
    """
    Fetch all trending Solana tokens (not just PumpFun).
    """
    async with PumpFunCollector() as collector:
        return await collector.fetch_all(
            limit=limit,
            pumpfun_only=False,
            min_volume=min_volume,
        )


async def search_category_tokens(
    keywords: List[str],
    limit_per_keyword: int = 20,
) -> List[TokenData]:
    """
    Search for tokens matching specific category keywords.
    
    Useful for finding tokens in emerging trends.
    """
    async with PumpFunCollector() as collector:
        all_tokens: List[TokenData] = []
        seen_addresses: Set[str] = set()
        
        for keyword in keywords:
            tokens = await collector.search_tokens(keyword, limit_per_keyword)
            for token in tokens:
                if token.token_address not in seen_addresses:
                    seen_addresses.add(token.token_address)
                    all_tokens.append(token)
            await asyncio.sleep(0.2)  # Rate limiting
        
        # Enrich all at once
        all_tokens = await collector.enrich_with_market_data(all_tokens)
        
        # Filter for PumpFun and sort by volume
        all_tokens = [t for t in all_tokens if t.is_pumpfun]
        all_tokens.sort(key=lambda t: t.volume_24h or 0, reverse=True)
        
        return all_tokens
