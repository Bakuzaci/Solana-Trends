# Moralis Solana API Reference

## Overview

The Moralis Solana API provides comprehensive token data for Solana blockchain, including PumpFun tokens, DEX pairs, and market analytics.

## Base URL

```
https://solana-gateway.moralis.io
```

## Authentication

All requests require the `X-API-Key` header with your Moralis API key.

---

## Token API Endpoints

### New PumpFun Tokens

Get newly created tokens on PumpFun.

```
GET /token/mainnet/exchange/pumpfun/new
```

**Parameters:**
- `limit` - Number of results (default 100)
- `cursor` - Pagination cursor

**Response Schema:**
```json
{
  "result": [
    {
      "tokenAddress": "string",
      "name": "string",
      "symbol": "string",
      "logo": "string | null",
      "decimals": 9,
      "priceNative": "string",
      "priceUsd": "string",
      "liquidity": "string",
      "fullyDilutedValuation": "string",
      "createdAt": "ISO timestamp"
    }
  ],
  "cursor": "string"
}
```

### Graduated PumpFun Tokens

Get tokens that completed bonding curve and migrated to Raydium.

```
GET /token/mainnet/exchange/pumpfun/graduated
```

**Parameters:**
- `limit` - Number of results
- `cursor` - Pagination cursor

**Response:** Same schema as new tokens with `is_graduated: true`

### Bonding Tokens

Get tokens still in bonding phase.

```
GET /token/mainnet/exchange/pumpfun/bonding
```

### Token Bonding Status

Check if a specific token is graduated or still on bonding curve.

```
GET /token/mainnet/{tokenAddress}/bonding-status
```

**Response:**
```json
{
  "status": "graduated" | "bonding",
  "bondingProgress": 0-100,
  "isGraduated": true | false
}
```

---

## Price API Endpoints

### Token Price

Get current price for a token.

```
GET /token/{network}/{address}/price
```

**Response Schema:**
```json
{
  "tokenAddress": "string",
  "pairAddress": "string",
  "exchangeName": "Raydium" | "Meteora DLMM" | etc,
  "exchangeAddress": "string",
  "nativePrice": {
    "value": "string",
    "symbol": "WSOL",
    "name": "Wrapped Solana",
    "decimals": 9
  },
  "usdPrice": 0.2435
}
```

**Note:** Price is the last traded price from the highest liquidity DEX pair.

### Multiple Token Prices

```
POST /token/{network}/prices
```

**Request Body:**
```json
{
  "tokens": [
    {"tokenAddress": "address1"},
    {"tokenAddress": "address2"}
  ]
}
```

---

## Pair & Trading Data Endpoints

### Token Pairs

Get all DEX pairs for a token. **This is the best endpoint for comprehensive trading data.**

```
GET /token/{network}/{address}/pairs
```

**Response Schema:**
```json
{
  "pairs": [
    {
      "exchangeAddress": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
      "exchangeName": "Raydium AMM v4",
      "exchangeLogo": "https://entities-logos.s3.amazonaws.com/raydium.png",
      "pairAddress": "Bzc9NZfMqkXR6fz1DBph7BDf9BroyEf6pnzESP7v5iiw",
      "pairLabel": "Fartcoin/SOL",
      "usdPrice": 1.199318671,
      "usdPrice24hrPercentChange": 22.664745257790372,
      "volume24hrUsd": 63991693.95772195,
      "volume24hrNative": 273987.170173767,
      "liquidityUsd": 25907004.26453429,
      "baseToken": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
      "quoteToken": "So11111111111111111111111111111111111111112",
      "inactivePair": false,
      "pair": [
        {
          "tokenAddress": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
          "tokenName": "Fartcoin",
          "tokenSymbol": "Fartcoin",
          "tokenDecimals": "6",
          "pairTokenType": "token0",
          "liquidityUsd": 12937540.20684488
        }
      ]
    }
  ]
}
```

**Key Fields:**
| Field | Description |
|-------|-------------|
| `usdPrice` | Current USD price |
| `usdPrice24hrPercentChange` | 24-hour price change percentage |
| `volume24hrUsd` | 24-hour trading volume in USD |
| `liquidityUsd` | Total liquidity in USD |
| `exchangeName` | DEX name (Raydium, Meteora, Orca, etc.) |
| `pairAddress` | Trading pair contract address |

### Pair Statistics

Get detailed stats for a specific pair.

```
GET /token/{network}/pairs/{pairAddress}/stats
```

**Response includes:**
- `pairTotalLiquidityUsd` - Total liquidity in USD
- `volume24h` - 24-hour trading volume
- `buyVolume24h` - Buy-side volume
- `sellVolume24h` - Sell-side volume
- `priceChange24h` - 24-hour price change percentage
- `transactions24h` - Number of trades

### Aggregated Pair Stats

Get combined stats across all pairs for a token.

```
GET /token/{network}/{address}/pairs/stats
```

### Swaps by Pair

Get recent swaps for a trading pair.

```
GET /token/{network}/pairs/{pairAddress}/swaps
```

### OHLCV Candlesticks

Get price history for charts.

```
GET /token/{network}/pairs/{pairAddress}/ohlcv
```

**Parameters:**
- `timeframe` - 1m, 5m, 15m, 1h, 4h, 1d
- `limit` - Number of candles

---

## Token Analytics

### Token Analytics

Get comprehensive analytics for a token.

```
GET /api/v2.2/tokens/{address}/analytics
```

### Trending Tokens

Get currently trending tokens.

```
GET /api/v2.2/tokens/trending
```

### Token Score

Get a quality/risk score for a token.

```
GET /api/v2.2/tokens/{tokenAddress}/score
```

---

## Holder Data

### Top Holders

```
GET /token/mainnet/holders/{address}
```

### Historical Holders

```
GET /token/mainnet/holders/{address}/historical
```

---

## Price Calculation Notes

1. **Price Source:** Last traded price from swap log events
2. **Pool Selection:** Highest 24h volume pool is used
3. **Liquidity Thresholds:**
   - Ethereum: $500 minimum
   - Other chains: $150 minimum
   - Solana: No minimum threshold
4. **pairTotalLiquidityUsd:** Calculated as:
   - (token A locked amount × USD price) + (token B locked amount × USD price)

---

## Common Response Fields

| Field | Description |
|-------|-------------|
| `tokenAddress` | Solana mint address |
| `priceUsd` | Current USD price |
| `priceNative` | Price in SOL |
| `liquidity` | Available liquidity |
| `fullyDilutedValuation` | Market cap if all tokens circulated |
| `pairTotalLiquidityUsd` | Total liquidity in the trading pair |
| `volume24h` | 24-hour trading volume |
| `priceChange24h` | 24-hour price change % |

---

## Error Codes

- `404` - Token not found or no liquidity pool
- `429` - Rate limit exceeded
- `500` - Server error

---

## Rate Limits

Free tier limits apply. Consider batching requests and adding delays between calls.
