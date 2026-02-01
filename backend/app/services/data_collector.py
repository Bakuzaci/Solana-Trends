"""
Data collection service for fetching Solana token data.

Uses Moralis API for real data or generates mock data when
no API key is configured. Falls back to web-discovered tokens
for more realistic mock data.
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

import httpx

from ..config import settings
from .web_token_discovery import (
    discover_tokens_from_web,
    get_real_token_addresses,
    get_cached_tokens,
    DiscoveredToken,
)


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
    metadata: Dict[str, Any] = field(default_factory=dict)


class MoralisClient:
    """
    Client for fetching Solana token data from Moralis API.

    Falls back to mock data generation when no API key is configured.
    """

    BASE_URL = "https://solana-gateway.moralis.io"
    PUMPFUN_ENDPOINT = "/token/mainnet/exchange/pumpfun/new"
    PUMPFUN_GRADUATED_ENDPOINT = "/token/mainnet/exchange/pumpfun/graduated"
    BONDING_STATUS_ENDPOINT = "/token/mainnet/{address}/bonding-status"
    TOKEN_PAIRS_ENDPOINT = "/token/mainnet/{address}/pairs"
    AGGREGATED_PAIR_STATS_ENDPOINT = "/token/mainnet/{address}/pairs/stats"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Moralis client.

        Args:
            api_key: Moralis API key. If None, uses settings or mock mode.
        """
        self.api_key = api_key or settings.moralis_api_key
        self.use_mock = not self.api_key

        if self.use_mock:
            print("Warning: No Moralis API key configured. Using mock data.")

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the Moralis API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        if self.use_mock:
            raise ValueError("Cannot make API request without API key")

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_new_pumpfun_tokens(
        self,
        limit: int = 100
    ) -> List[TokenData]:
        """
        Fetch new tokens from PumpFun exchange.

        Args:
            limit: Maximum number of tokens to fetch

        Returns:
            List of TokenData objects
        """
        if self.use_mock:
            # Use async mock generation with real web-discovered tokens
            return await self._generate_mock_tokens_async(limit)

        try:
            data = await self._make_request(
                self.PUMPFUN_ENDPOINT,
                params={"limit": limit}
            )

            tokens = []
            for item in data.get("result", []):
                # Parse numeric values - API returns strings for some fields
                fdv = item.get("fullyDilutedValuation")
                liquidity = item.get("liquidity")
                price = item.get("priceUsd")

                # Parse datetime with timezone handling
                created_at_str = item.get("createdAt")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    except ValueError:
                        created_at = datetime.utcnow()
                else:
                    created_at = datetime.utcnow()

                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name=item.get("name", "Unknown"),
                    symbol=item.get("symbol", "???"),
                    created_at=created_at,
                    # fullyDilutedValuation is the market cap for these tokens
                    market_cap_usd=float(fdv) if fdv else None,
                    liquidity_usd=float(liquidity) if liquidity else None,
                    price_usd=float(price) if price else None,
                    metadata=item,
                )
                tokens.append(token)

            return tokens

        except httpx.HTTPError as e:
            print(f"Error fetching tokens from Moralis: {e}")
            # Fallback to web-discovered tokens on error
            return await self._generate_mock_tokens_async(limit)

    async def get_graduated_pumpfun_tokens(
        self,
        limit: int = 100
    ) -> List[TokenData]:
        """
        Fetch graduated tokens from PumpFun exchange.

        Graduated tokens have completed the bonding curve and migrated
        to Raydium with real liquidity.

        Args:
            limit: Maximum number of tokens to fetch

        Returns:
            List of TokenData objects for graduated tokens
        """
        if self.use_mock:
            # Return mock tokens marked as graduated
            tokens = self._generate_mock_tokens(limit)
            for t in tokens:
                t.metadata["is_graduated"] = True
            return tokens

        try:
            data = await self._make_request(
                self.PUMPFUN_GRADUATED_ENDPOINT,
                params={"limit": limit}
            )

            tokens = []
            for item in data.get("result", []):
                # Parse numeric values - API returns strings for some fields
                fdv = item.get("fullyDilutedValuation")
                liquidity = item.get("liquidity")
                price = item.get("priceUsd")

                # Graduated endpoint uses graduatedAt, not createdAt
                created_at_str = item.get("createdAt") or item.get("graduatedAt")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    except ValueError:
                        created_at = datetime.utcnow()
                else:
                    created_at = datetime.utcnow()

                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name=item.get("name", "Unknown"),
                    symbol=item.get("symbol", "???"),
                    created_at=created_at,
                    market_cap_usd=float(fdv) if fdv else None,
                    liquidity_usd=float(liquidity) if liquidity else None,
                    price_usd=float(price) if price else None,
                    metadata={**item, "is_graduated": True},
                )
                tokens.append(token)

            print(f"Parsed {len(tokens)} graduated tokens with liquidity data")
            return tokens

        except httpx.HTTPError as e:
            print(f"Error fetching graduated tokens from Moralis: {e}")
            return []

    async def get_token_bonding_status(
        self,
        token_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get bonding status for a token.

        Returns information about whether the token is still on bonding curve
        or has graduated to a DEX.

        Args:
            token_address: Solana token address

        Returns:
            Dictionary with bonding status info or None
        """
        if self.use_mock:
            # Mock: 30% chance of being graduated
            return {
                "is_graduated": random.random() > 0.7,
                "bonding_curve_progress": random.uniform(0, 100),
            }

        try:
            endpoint = self.BONDING_STATUS_ENDPOINT.format(address=token_address)
            data = await self._make_request(endpoint)
            return data
        except httpx.HTTPError as e:
            print(f"Error fetching bonding status for {token_address[:8]}...: {e}")
            return None

    async def check_graduation_status(
        self,
        token_addresses: List[str]
    ) -> Dict[str, bool]:
        """
        Check graduation status for multiple tokens.

        Args:
            token_addresses: List of token addresses

        Returns:
            Dictionary mapping addresses to graduation status (True = graduated)
        """
        results = {}

        # Batch requests to avoid rate limiting
        batch_size = 10
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            tasks = [self.get_token_bonding_status(addr) for addr in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for addr, result in zip(batch, batch_results):
                if isinstance(result, dict):
                    # Check various possible response formats
                    is_graduated = (
                        result.get("is_graduated", False) or
                        result.get("isGraduated", False) or
                        result.get("status") == "graduated" or
                        result.get("bondingStatus") == "completed"
                    )
                    results[addr] = is_graduated
                else:
                    results[addr] = False

            # Small delay between batches
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(0.5)

        return results

    async def get_token_pairs(
        self,
        token_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get all DEX pairs for a token.

        Returns pair data including liquidity, price, volume, and price changes.

        Response includes for each pair:
        - pairAddress: Liquidity pool address
        - exchangeName: DEX name (Raydium, Meteora, etc.)
        - usdPrice: Current USD price
        - usdPrice24hrPercentChange: 24h price change percentage
        - volume24hrUsd: 24h trading volume in USD
        - liquidityUsd: Total liquidity in USD

        Args:
            token_address: Solana token address

        Returns:
            Dictionary with pairs data or None
        """
        if self.use_mock:
            return {
                "pairs": [{
                    "liquidityUsd": random.uniform(1000, 1000000),
                    "volume24hrUsd": random.uniform(100, 100000),
                    "usdPrice24hrPercentChange": random.uniform(-50, 100),
                    "usdPrice": random.uniform(0.0000001, 0.01),
                }]
            }

        try:
            endpoint = self.TOKEN_PAIRS_ENDPOINT.format(address=token_address)
            data = await self._make_request(endpoint)
            return data
        except httpx.HTTPError as e:
            print(f"Error fetching pairs for {token_address[:8]}...: {e}")
            return None

    async def get_token_price(
        self,
        token_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current price and comprehensive market data for a token.

        Uses the pairs endpoint for the most accurate data including:
        - Price from highest liquidity pair
        - 24h price change percentage (usdPrice24hrPercentChange)
        - 24h volume (volume24hrUsd)
        - Liquidity (liquidityUsd)

        Args:
            token_address: Solana token address

        Returns:
            Dictionary with price, market_cap, liquidity, price_change_24h, volume_24h or None
        """
        if self.use_mock:
            return self._generate_mock_price()

        try:
            # Initialize values
            price_usd = 0.0
            market_cap = 0.0
            liquidity = 0.0
            price_change_24h = None
            volume_24h = None

            # Get pairs data - this has the most accurate trading data
            pairs_data = await self.get_token_pairs(token_address)
            if pairs_data and pairs_data.get("pairs"):
                # Use the first pair (highest liquidity is usually first)
                pairs = pairs_data.get("pairs", [])
                if pairs:
                    # Find the pair with highest liquidity
                    best_pair = max(pairs, key=lambda p: float(p.get("liquidityUsd", 0) or 0))

                    # Extract data from best pair
                    price_usd = float(best_pair.get("usdPrice", 0) or 0)
                    liquidity = float(best_pair.get("liquidityUsd", 0) or 0)

                    # 24h price change - this is the key field
                    pchange = best_pair.get("usdPrice24hrPercentChange")
                    if pchange is not None:
                        price_change_24h = float(pchange)

                    # 24h volume
                    vol = best_pair.get("volume24hrUsd")
                    if vol is not None:
                        volume_24h = float(vol)

            # Note: We skip the /price and /metadata endpoints for tokens
            # without pairs data as they often return 401 Unauthorized.
            # The pairs endpoint provides all necessary trading data for active tokens.
            # Tokens without pairs are likely still on bonding curve and we have their
            # data from the pumpfun/new or pumpfun/graduated endpoints.

            return {
                "price_usd": price_usd,
                "market_cap_usd": market_cap,
                "liquidity_usd": liquidity,
                "price_change_24h": price_change_24h,
                "volume_24h": volume_24h,
            }

        except httpx.HTTPError as e:
            print(f"Error fetching token price: {e}")
            return None

    async def get_multiple_token_prices(
        self,
        token_addresses: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Get prices for multiple tokens concurrently.

        Args:
            token_addresses: List of token addresses

        Returns:
            Dictionary mapping addresses to price data
        """
        results = {}

        # Batch requests to avoid rate limiting
        batch_size = 10
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            tasks = [self.get_token_price(addr) for addr in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for addr, result in zip(batch, batch_results):
                if isinstance(result, dict):
                    results[addr] = result
                else:
                    results[addr] = self._generate_mock_price()

            # Small delay between batches
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(0.5)

        return results

    async def _generate_mock_tokens_async(self, count: int = 100) -> List[TokenData]:
        """
        Generate mock token data using web-discovered real tokens.

        Uses real Solana token addresses discovered from DexScreener,
        Jupiter, and other sources to make mock data realistic.

        Args:
            count: Number of mock tokens to generate

        Returns:
            List of mock TokenData objects with real addresses
        """
        # Discover real tokens from web sources
        discovered = await discover_tokens_from_web()
        real_addresses = get_real_token_addresses()

        tokens = []
        now = datetime.utcnow()

        # First, add discovered tokens with real data
        for i, disc_token in enumerate(discovered[:min(count, len(discovered))]):
            # Use discovered market cap or generate realistic one
            if disc_token.market_cap:
                market_cap = disc_token.market_cap * random.uniform(0.8, 1.2)
            else:
                market_cap = random.uniform(100000, 50000000)

            liquidity = market_cap * random.uniform(0.01, 0.3)
            price = random.uniform(0.0000001, 0.01)

            # Random creation time in the last 7 days
            created_at = now - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            token = TokenData(
                token_address=disc_token.address or self._generate_random_address(),
                name=disc_token.name,
                symbol=disc_token.symbol,
                created_at=created_at,
                market_cap_usd=market_cap,
                liquidity_usd=liquidity,
                price_usd=price,
                metadata={"source": disc_token.source}
            )
            tokens.append(token)

        # If we need more tokens, generate additional ones with themed names
        remaining = count - len(tokens)
        if remaining > 0:
            additional = self._generate_themed_tokens(remaining, real_addresses)
            tokens.extend(additional)

        print(f"Generated {len(tokens)} tokens ({len(discovered)} from web sources)")
        return tokens

    def _generate_random_address(self) -> str:
        """Generate a random Solana-like address."""
        return "".join(random.choices(
            "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
            k=44
        ))

    def _generate_themed_tokens(
        self,
        count: int,
        real_addresses: Dict[str, str]
    ) -> List[TokenData]:
        """Generate themed mock tokens with varied names."""
        themes = {
            "dogs": [
                ("Shiba Sol", "SHIBSOL"), ("Doge King", "DOGEKING"), ("Puppy Moon", "PUPMOON"),
                ("Woof Finance", "WOOFFI"), ("Corgi Cash", "CORGICASH"),
            ],
            "cats": [
                ("Kitty Coin", "KITTY"), ("Meow Money", "MEOWMONEY"), ("Cat Lord", "CATLORD"),
                ("Whiskers Finance", "WHISKFI"), ("Nyan Token", "NYANTOKEN"),
            ],
            "frogs": [
                ("Frog King", "FROGKING"), ("Pepe Classic", "PEPEC"), ("Kek Token", "KEK"),
                ("Toad Lord", "TOADLORD"), ("Ribbit Finance", "RIBBITFI"),
            ],
            "ai": [
                ("Neural Net", "NEURALNET"), ("AI Agent", "AIAGENT"), ("Bot Token", "BOTTOKEN"),
                ("GPT Coin", "GPTCOIN"), ("Deep Mind Sol", "DEEPSOL"),
            ],
            "politics": [
                ("Freedom Coin", "FREEDOM"), ("Vote Token", "VOTE"), ("Democracy Sol", "DEMO"),
                ("Liberty Coin", "LIBERTY"), ("Republic Token", "REPUBLIC"),
            ],
            "food": [
                ("Pizza Token", "PIZZATOKEN"), ("Burger Coin", "BURGERCOIN"), ("Taco Sol", "TACOSOL"),
                ("Ramen Finance", "RAMENFI"), ("Sushi Moon", "SUSHIMOON"),
            ],
            "abstract": [
                ("Moon Shot", "MOONSHOT"), ("Rocket Fuel", "ROCKETFUEL"), ("Diamond Sol", "DIAMONDSOL"),
                ("Gem Hunter", "GEMHUNTER"), ("Star Token", "STARTOKEN"),
            ],
        }

        tokens = []
        now = datetime.utcnow()
        all_names = []
        for theme_names in themes.values():
            all_names.extend(theme_names)

        for i in range(count):
            if i < len(all_names):
                name, symbol = all_names[i]
            else:
                idx = random.randint(0, len(all_names) - 1)
                base_name, base_symbol = all_names[idx]
                suffix = random.randint(1, 999)
                name = f"{base_name} {suffix}"
                symbol = f"{base_symbol}{suffix}"

            # Use real address if available, otherwise generate random
            address = real_addresses.get(symbol, self._generate_random_address())

            # Random creation time in the last 24 hours
            created_at = now - timedelta(
                hours=random.randint(0, 24),
                minutes=random.randint(0, 59)
            )

            # Random market data
            market_cap = random.uniform(1000, 10000000)
            liquidity = market_cap * random.uniform(0.01, 0.3)
            price = random.uniform(0.0000001, 0.01)

            token = TokenData(
                token_address=address,
                name=name,
                symbol=symbol,
                created_at=created_at,
                market_cap_usd=market_cap,
                liquidity_usd=liquidity,
                price_usd=price,
            )
            tokens.append(token)

        return tokens

    def _generate_mock_tokens(self, count: int = 100) -> List[TokenData]:
        """
        Synchronous wrapper for backward compatibility.
        Uses cached tokens if available, otherwise generates basic mocks.
        """
        # Use cached web-discovered tokens if available
        cached = get_cached_tokens()
        real_addresses = get_real_token_addresses()

        tokens = []
        now = datetime.utcnow()

        # First use cached real tokens
        for i, disc_token in enumerate(cached[:min(count, len(cached))]):
            if disc_token.market_cap:
                market_cap = disc_token.market_cap * random.uniform(0.8, 1.2)
            else:
                market_cap = random.uniform(100000, 50000000)

            liquidity = market_cap * random.uniform(0.01, 0.3)
            price = random.uniform(0.0000001, 0.01)

            created_at = now - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            token = TokenData(
                token_address=disc_token.address or self._generate_random_address(),
                name=disc_token.name,
                symbol=disc_token.symbol,
                created_at=created_at,
                market_cap_usd=market_cap,
                liquidity_usd=liquidity,
                price_usd=price,
                metadata={"source": disc_token.source}
            )
            tokens.append(token)

        # Generate additional themed tokens if needed
        remaining = count - len(tokens)
        if remaining > 0:
            additional = self._generate_themed_tokens(remaining, real_addresses)
            tokens.extend(additional)

        return tokens

    def _generate_mock_price(self) -> Dict[str, Any]:
        """Generate mock price data."""
        market_cap = random.uniform(1000, 10000000)
        return {
            "price_usd": random.uniform(0.0000001, 0.01),
            "market_cap_usd": market_cap,
            "liquidity_usd": market_cap * random.uniform(0.01, 0.3),
            "price_change_24h": random.uniform(-50, 100),
            "volume_24h": random.uniform(100, 100000),
        }


# Create a default client instance
default_client = MoralisClient()


async def fetch_new_tokens(limit: int = 100) -> List[TokenData]:
    """
    Convenience function to fetch new tokens using the default client.

    Args:
        limit: Maximum number of tokens to fetch

    Returns:
        List of TokenData objects
    """
    return await default_client.get_new_pumpfun_tokens(limit)


async def fetch_token_prices(addresses: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Convenience function to fetch token prices using the default client.

    Args:
        addresses: List of token addresses

    Returns:
        Dictionary mapping addresses to price data
    """
    return await default_client.get_multiple_token_prices(addresses)


async def fetch_graduated_tokens(limit: int = 100) -> List[TokenData]:
    """
    Convenience function to fetch graduated tokens using the default client.

    Args:
        limit: Maximum number of tokens to fetch

    Returns:
        List of TokenData objects for graduated tokens
    """
    return await default_client.get_graduated_pumpfun_tokens(limit)


async def check_token_graduation(addresses: List[str]) -> Dict[str, bool]:
    """
    Convenience function to check graduation status for tokens.

    Args:
        addresses: List of token addresses

    Returns:
        Dictionary mapping addresses to graduation status
    """
    return await default_client.check_graduation_status(addresses)
