# Vertigo DEX API Documentation

## Overview

Vertigo is a Solana DEX with anti-bot/anti-sniping features. Website: https://vertigo.sh

## Token Page URL Format

```
https://vertigo.sh/tokens/{token_address}
```

Example: `https://vertigo.sh/tokens/So11111111111111111111111111111111111111112`

---

## Coingecko-Compatible API

Base URL: `https://coingecko-api.vertigo.sh`

### Endpoints

#### GET /latest-block
Returns the most recent valid block number and timestamp.

**Response:**
```json
{
  "blockNumber": 123456789,
  "blockTimestamp": 1234567890
}
```

#### GET /asset?id={ASSET_ID}
Retrieves information for a specific asset.

**Response includes:**
- name, symbol, decimals
- supply metrics
- metadata

#### GET /pair?id={PAIR_ID}
Fetches data for a specific trading pair.

**Response includes:**
- dex key
- asset IDs
- creation details
- fee information in basis points

#### GET /events?fromBlock={FROM}&toBlock={TO}
Queries events within a block range.

**Event Types:**
- "Join" - liquidity creation
- "Swap" - trading activity

**Response includes:**
- transaction details
- event metadata
- amount information

#### GET /pools?mint={MINT_ID}
Lists pools, optionally filtered by mint address.

**Response includes:**
- pool addresses
- cluster information
- owner details
- creation metadata

---

## Vertigo SDK v2

### Installation

```bash
npm install @vertigo-amm/vertigo-sdk
```

**Required dependencies:**
- `@coral-xyz/anchor`
- `@solana/web3.js`
- `@solana/spl-token`

### Setup

**Read-only initialization:**
```typescript
const vertigo = await Vertigo.loadReadOnly(connection, "devnet");
```

**Wallet-enabled mode (for transactions):**
```typescript
const vertigo = await Vertigo.load({
  connection,
  wallet: walletKeypair,
  network: "devnet", // or "mainnet"
});
```

### Core Client Modules

- **Swap Client** (`vertigo.swap`): Quote retrieval, token purchases/sales, transaction simulation
- **Pool Client** (`vertigo.pools`): Pool data fetching, creation, fee claims, statistics
- **Pool Authority Client** (`vertigo.poolAuthority`): Advanced management for authorized operators
- **API Client** (`vertigo.api`): Analytics, trending pools, metadata, WebSocket subscriptions

---

## Swap Operations

### Core Methods

1. **`swap()`** - Execute token swaps with automatic buy/sell detection
2. **`getQuote()`** - Get pricing estimates including slippage calculations
3. **`simulateSwap()`** - Test transactions before committing on-chain
4. **`buildSwapTransaction()`** - Manual transaction construction for advanced use

### Parameters

**Common parameters:**
- `inputMint`: Public key of the token being traded away
- `outputMint`: Public key of the token being acquired
- `amount`: Quantity in base units (accounting for token decimals)
- `slippageBps`: Slippage tolerance in basis points (default: 50 = 0.5%)

**Swap options:**
- `priorityFee`: Set to "auto" or specify micro-lamports value
- `wrapSol`: Auto-wrap SOL if needed (default: true)
- `simulateFirst`: Simulate before executing (default: true)

### Buying Tokens

```typescript
import { NATIVE_MINT } from "@solana/spl-token";

const result = await vertigo.swap.swap({
  inputMint: NATIVE_MINT,      // Paying with SOL
  outputMint: tokenMint,        // Token to buy
  amount: solAmount,            // Amount in lamports
  options: {
    slippageBps: 100,           // 1% slippage
    priorityFee: "auto"
  }
});
```

### Selling Tokens

```typescript
import { NATIVE_MINT } from "@solana/spl-token";

const result = await vertigo.swap.swap({
  inputMint: tokenMint,         // Token to sell
  outputMint: NATIVE_MINT,      // Receiving SOL
  amount: sellAmount,           // Amount in token units
  options: {
    slippageBps: 100,
    priorityFee: "auto"
  }
});
```

### Getting a Quote

```typescript
const quote = await vertigo.swap.getQuote({
  inputMint: tokenMint,
  outputMint: NATIVE_MINT,
  amount: sellAmount,
  slippageBps: 50
});
```

### Error Codes

- `SLIPPAGE_EXCEEDED`
- `INSUFFICIENT_FUNDS`
- `POOL_NOT_FOUND`

---

## Key Features

- **Anti-sniping**: Protects against bot front-running
- **No liquidity burn required**: One-sided pool mechanics
- **LP fee capture**: Better fee economics for creators
- **Fully transparent**: Open security model

---

## Rate Limits

The API implements rate limiting. For higher limits, contact: deals@vertigo.sh

## Resources

- Website: https://vertigo.sh
- Docs: https://docs.vertigo.sh
- Twitter: https://x.com/vertigodex
