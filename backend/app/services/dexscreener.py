"""
DexScreener API client for fetching real Solana token data.

Free API, no authentication required.
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TokenData:
    """Represents token data from DexScreener."""
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


class DexScreenerClient:
    """Client for fetching Solana token data from DexScreener API."""

    BASE_URL = "https://api.dexscreener.com"

    async def get_trending_solana_tokens(self, limit: int = 50) -> List[TokenData]:
        """
        Fetch trending Solana tokens from DexScreener.

        Uses the token boosts endpoint for trending tokens,
        then enriches with pair data.
        """
        tokens = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get top boosted/trending tokens
                response = await client.get(f"{self.BASE_URL}/token-boosts/top/v1")
                response.raise_for_status()
                data = response.json()

                # Filter for Solana tokens
                solana_tokens = [
                    t for t in data
                    if t.get("chainId") == "solana"
                ][:limit]

                for item in solana_tokens:
                    token = TokenData(
                        token_address=item.get("tokenAddress", ""),
                        name=item.get("name") or item.get("description", "Unknown")[:30],
                        symbol=item.get("symbol", "???"),
                        created_at=datetime.utcnow(),
                        metadata={"source": "dexscreener_boosts"}
                    )
                    tokens.append(token)

                # Enrich with price data
                if tokens:
                    tokens = await self._enrich_with_pair_data(client, tokens)

                print(f"[DexScreener] Fetched {len(tokens)} trending tokens")
                return tokens

            except Exception as e:
                print(f"[DexScreener] Error fetching trending tokens: {e}")
                return []

    async def get_new_solana_pairs(self, limit: int = 50) -> List[TokenData]:
        """
        Fetch newest Solana token pairs from DexScreener.

        This gives us recently created/listed tokens.
        """
        tokens = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get latest profiles (new tokens)
                response = await client.get(f"{self.BASE_URL}/token-profiles/latest/v1")
                response.raise_for_status()
                data = response.json()

                # Filter for Solana tokens
                solana_tokens = [
                    t for t in data
                    if t.get("chainId") == "solana"
                ][:limit]

                for item in solana_tokens:
                    token = TokenData(
                        token_address=item.get("tokenAddress", ""),
                        name=item.get("name") or item.get("description", "Unknown")[:30],
                        symbol=item.get("symbol", "???"),
                        created_at=datetime.utcnow(),
                        metadata={"source": "dexscreener_profiles"}
                    )
                    tokens.append(token)

                # Enrich with price data
                if tokens:
                    tokens = await self._enrich_with_pair_data(client, tokens)

                print(f"[DexScreener] Fetched {len(tokens)} new token profiles")
                return tokens

            except Exception as e:
                print(f"[DexScreener] Error fetching new pairs: {e}")
                return []

    async def search_solana_tokens(self, query: str = "pump", limit: int = 50) -> List[TokenData]:
        """
        Search for Solana tokens on DexScreener.
        """
        tokens = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/latest/dex/search",
                    params={"q": query}
                )
                response.raise_for_status()
                data = response.json()

                pairs = data.get("pairs", [])
                # Filter for Solana pairs
                solana_pairs = [p for p in pairs if p.get("chainId") == "solana"][:limit]

                seen_addresses = set()
                for pair in solana_pairs:
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
                        metadata={"source": "dexscreener_search", "pair": pair.get("pairAddress")}
                    )
                    tokens.append(token)

                print(f"[DexScreener] Search '{query}' found {len(tokens)} tokens")
                return tokens

            except Exception as e:
                print(f"[DexScreener] Error searching tokens: {e}")
                return []

    async def get_token_info(self, token_address: str) -> Optional[TokenData]:
        """Get detailed info for a specific token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/latest/dex/tokens/{token_address}"
                )
                response.raise_for_status()
                data = response.json()

                pairs = data.get("pairs", [])
                if not pairs:
                    return None

                # Use the pair with highest liquidity
                best_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
                base_token = best_pair.get("baseToken", {})

                return TokenData(
                    token_address=token_address,
                    name=base_token.get("name", "Unknown"),
                    symbol=base_token.get("symbol", "???"),
                    created_at=datetime.utcnow(),
                    market_cap_usd=best_pair.get("marketCap"),
                    liquidity_usd=best_pair.get("liquidity", {}).get("usd"),
                    price_usd=float(best_pair.get("priceUsd", 0) or 0),
                    price_change_24h=best_pair.get("priceChange", {}).get("h24"),
                    volume_24h=best_pair.get("volume", {}).get("h24"),
                    metadata={"source": "dexscreener"}
                )

            except Exception as e:
                print(f"[DexScreener] Error fetching token {token_address[:8]}...: {e}")
                return None

    async def _enrich_with_pair_data(
        self,
        client: httpx.AsyncClient,
        tokens: List[TokenData]
    ) -> List[TokenData]:
        """Enrich tokens with price/market data from pairs endpoint."""
        # Batch token addresses (API accepts multiple)
        addresses = [t.token_address for t in tokens if t.token_address]

        if not addresses:
            return tokens

        # DexScreener allows up to 30 addresses per request
        enriched = {}
        batch_size = 30

        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            address_str = ",".join(batch)

            try:
                response = await client.get(
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
                    if address in enriched:
                        existing_liq = enriched[address].get("liquidity", 0) or 0
                        new_liq = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                        if new_liq <= existing_liq:
                            continue

                    enriched[address] = {
                        "name": base_token.get("name"),
                        "symbol": base_token.get("symbol"),
                        "market_cap": pair.get("marketCap"),
                        "liquidity": pair.get("liquidity", {}).get("usd"),
                        "price": pair.get("priceUsd"),
                        "price_change_24h": pair.get("priceChange", {}).get("h24"),
                        "volume_24h": pair.get("volume", {}).get("h24"),
                    }
            except Exception as e:
                print(f"[DexScreener] Error enriching batch: {e}")

        # Update tokens with enriched data
        for token in tokens:
            if token.token_address in enriched:
                data = enriched[token.token_address]
                token.name = data.get("name") or token.name
                token.symbol = data.get("symbol") or token.symbol
                token.market_cap_usd = data.get("market_cap")
                token.liquidity_usd = data.get("liquidity")
                token.price_usd = float(data.get("price", 0) or 0)
                token.price_change_24h = data.get("price_change_24h")
                token.volume_24h = data.get("volume_24h")

        return tokens


# Default client instance
dexscreener_client = DexScreenerClient()


async def fetch_trending_tokens(limit: int = 50) -> List[TokenData]:
    """Fetch trending Solana tokens from DexScreener."""
    return await dexscreener_client.get_trending_solana_tokens(limit)


async def fetch_new_tokens(limit: int = 50) -> List[TokenData]:
    """Fetch new Solana tokens from DexScreener."""
    return await dexscreener_client.get_new_solana_pairs(limit)


async def search_tokens(query: str, limit: int = 50) -> List[TokenData]:
    """Search for Solana tokens on DexScreener."""
    return await dexscreener_client.search_solana_tokens(query, limit)
