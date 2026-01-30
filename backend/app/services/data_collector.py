"""
Data collection service for fetching Solana token data.

Uses Moralis API for real data or generates mock data when
no API key is configured.
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

import httpx

from ..config import settings


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
            return self._generate_mock_tokens(limit)

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

                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name=item.get("name", "Unknown"),
                    symbol=item.get("symbol", "???"),
                    created_at=datetime.fromisoformat(
                        item.get("createdAt", datetime.utcnow().isoformat())
                    ),
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
            # Fallback to mock data on error
            return self._generate_mock_tokens(limit)

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

                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name=item.get("name", "Unknown"),
                    symbol=item.get("symbol", "???"),
                    created_at=datetime.fromisoformat(
                        item.get("createdAt", datetime.utcnow().isoformat())
                    ),
                    market_cap_usd=float(fdv) if fdv else None,
                    liquidity_usd=float(liquidity) if liquidity else None,
                    price_usd=float(price) if price else None,
                    metadata={**item, "is_graduated": True},
                )
                tokens.append(token)

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

    async def get_aggregated_pair_stats(
        self,
        token_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregated pair statistics for a token across all DEX pairs.

        Returns volume, liquidity, and price change data.

        Args:
            token_address: Solana token address

        Returns:
            Dictionary with aggregated stats or None
        """
        if self.use_mock:
            return {
                "totalLiquidityUsd": random.uniform(1000, 1000000),
                "volume24h": random.uniform(100, 100000),
                "priceChange24h": random.uniform(-50, 100),
            }

        try:
            endpoint = self.AGGREGATED_PAIR_STATS_ENDPOINT.format(address=token_address)
            data = await self._make_request(endpoint)
            return data
        except httpx.HTTPError as e:
            print(f"Error fetching pair stats for {token_address[:8]}...: {e}")
            return None

    async def get_token_price(
        self,
        token_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current price and comprehensive market data for a token.

        Fetches price, pair stats, and metadata to get complete data.

        Args:
            token_address: Solana token address

        Returns:
            Dictionary with price, market_cap, liquidity, price_change_24h, volume_24h or None
        """
        if self.use_mock:
            return self._generate_mock_price()

        try:
            # Fetch price data
            price_endpoint = f"/token/mainnet/{token_address}/price"
            price_data = await self._make_request(price_endpoint)

            price_usd = float(price_data.get("usdPrice", 0) or 0)

            # Initialize values
            market_cap = 0.0
            liquidity = 0.0
            price_change_24h = None
            volume_24h = None

            # Get aggregated pair stats for liquidity, volume, and price change
            try:
                pair_stats = await self.get_aggregated_pair_stats(token_address)
                if pair_stats:
                    # Extract values from pair stats - handle both string and numeric values
                    liq = pair_stats.get("totalLiquidityUsd") or pair_stats.get("pairTotalLiquidityUsd")
                    if liq:
                        liquidity = float(liq)

                    vol = pair_stats.get("volume24h") or pair_stats.get("totalVolume24h")
                    if vol:
                        volume_24h = float(vol)

                    pchange = pair_stats.get("priceChange24h") or pair_stats.get("pricePercentChange24h")
                    if pchange is not None:
                        price_change_24h = float(pchange)
            except Exception as e:
                print(f"Could not fetch pair stats for {token_address[:8]}...: {e}")

            # Get market cap from metadata
            try:
                metadata_endpoint = f"/token/mainnet/{token_address}/metadata"
                metadata = await self._make_request(metadata_endpoint)

                # Try fullyDilutedValue first
                fdv = metadata.get("fullyDilutedValuation") or metadata.get("fullyDilutedValue")
                if fdv:
                    market_cap = float(fdv)
                else:
                    # Calculate from price * supply
                    total_supply = metadata.get("totalSupplyFormatted") or metadata.get("totalSupply")
                    if total_supply and price_usd:
                        market_cap = float(total_supply) * price_usd
            except Exception as e:
                print(f"Could not fetch metadata for {token_address[:8]}...: {e}")

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

    def _generate_mock_tokens(self, count: int = 100) -> List[TokenData]:
        """
        Generate mock token data for testing.

        Args:
            count: Number of mock tokens to generate

        Returns:
            List of mock TokenData objects
        """
        mock_names = [
            # Dogs
            ("DogeCoin", "DOGE"), ("ShibaSol", "SHIB"), ("PuppyCoin", "PUPPY"),
            ("WoofToken", "WOOF"), ("CorgiMoon", "CORGI"),
            # Cats
            ("CatCoin", "CAT"), ("KittyMeme", "KITTY"), ("MeowToken", "MEOW"),
            ("WhiskersCoin", "WHISK"), ("NyanSol", "NYAN"),
            # Frogs
            ("PepeCoin", "PEPE"), ("FrogMoon", "FROG"), ("KermitToken", "KERMIT"),
            ("ToadCoin", "TOAD"), ("RibbitSol", "RIBBIT"),
            # Memes
            ("WojakCoin", "WOJAK"), ("ChadToken", "CHAD"), ("BasedCoin", "BASED"),
            ("StonksMoon", "STONKS"), ("HodlToken", "HODL"),
            # AI
            ("GPTCoin", "GPT"), ("AIToken", "AI"), ("BotMoon", "BOT"),
            ("NeuralCoin", "NEURAL"), ("ChatToken", "CHAT"),
            # Celebrities
            ("ElonCoin", "ELON"), ("TrumpToken", "TRUMP"), ("MuskMoon", "MUSK"),
            # Food
            ("PizzaCoin", "PIZZA"), ("BurgerToken", "BURGER"), ("TacoMoon", "TACO"),
            # Abstract
            ("MoonCoin", "MOON"), ("RocketToken", "ROCKET"), ("DiamondHands", "DIAMOND"),
            ("GemToken", "GEM"), ("StarMoon", "STAR"),
            # Random
            ("YoloCoin", "YOLO"), ("BruhToken", "BRUH"), ("VibeCoin", "VIBE"),
            ("LolToken", "LOL"), ("MemeKing", "MEME"),
        ]

        tokens = []
        now = datetime.utcnow()

        for i in range(count):
            # Select a random base name or generate a new one
            if i < len(mock_names):
                name, symbol = mock_names[i]
            else:
                idx = random.randint(0, len(mock_names) - 1)
                base_name, base_symbol = mock_names[idx]
                suffix = random.randint(1, 999)
                name = f"{base_name}{suffix}"
                symbol = f"{base_symbol}{suffix}"

            # Generate random address
            address = "".join(random.choices("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", k=44))

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
