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
                token = TokenData(
                    token_address=item.get("tokenAddress", ""),
                    name=item.get("name", "Unknown"),
                    symbol=item.get("symbol", "???"),
                    created_at=datetime.fromisoformat(
                        item.get("createdAt", datetime.utcnow().isoformat())
                    ),
                    market_cap_usd=item.get("marketCapUsd"),
                    liquidity_usd=item.get("liquidityUsd"),
                    price_usd=item.get("priceUsd"),
                    metadata=item,
                )
                tokens.append(token)

            return tokens

        except httpx.HTTPError as e:
            print(f"Error fetching tokens from Moralis: {e}")
            # Fallback to mock data on error
            return self._generate_mock_tokens(limit)

    async def get_token_price(
        self,
        token_address: str
    ) -> Optional[Dict[str, float]]:
        """
        Get current price and market data for a token.

        Args:
            token_address: Solana token address

        Returns:
            Dictionary with price, market_cap, liquidity or None
        """
        if self.use_mock:
            return self._generate_mock_price()

        try:
            endpoint = f"/token/mainnet/{token_address}/price"
            data = await self._make_request(endpoint)

            return {
                "price_usd": data.get("usdPrice", 0),
                "market_cap_usd": data.get("marketCap", 0),
                "liquidity_usd": data.get("liquidity", 0),
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

    def _generate_mock_price(self) -> Dict[str, float]:
        """Generate mock price data."""
        market_cap = random.uniform(1000, 10000000)
        return {
            "price_usd": random.uniform(0.0000001, 0.01),
            "market_cap_usd": market_cap,
            "liquidity_usd": market_cap * random.uniform(0.01, 0.3),
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
