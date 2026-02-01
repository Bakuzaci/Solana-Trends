"""
API endpoints for trending coins data.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import Token, Snapshot, TrendAggregate

router = APIRouter()

TimeWindowType = Literal["1h", "12h", "24h", "72h", "168h", "7d"]


def get_time_delta(time_window: str) -> timedelta:
    """Convert time window string to timedelta."""
    mapping = {
        "1h": timedelta(hours=1),
        "12h": timedelta(hours=12),
        "24h": timedelta(hours=24),
        "72h": timedelta(hours=72),
        "168h": timedelta(hours=168),
        "7d": timedelta(days=7),
    }
    return mapping.get(time_window, timedelta(hours=24))


@router.get("/coins")
async def get_trending_coins(
    time_window: TimeWindowType = Query("24h", description="Time window"),
    limit: int = Query(10, ge=1, le=50, description="Number of coins to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top trending coins by market cap change percentage.

    Returns coins with the highest market cap growth in the specified time window.
    """
    now = datetime.utcnow()
    past_time = now - get_time_delta(time_window)

    # Get the latest snapshot for each token
    latest_snapshot_subq = (
        select(
            Snapshot.token_address,
            func.max(Snapshot.snapshot_time).label("max_time")
        )
        .group_by(Snapshot.token_address)
        .subquery()
    )

    # Get current snapshots
    current_snapshots_query = (
        select(Snapshot)
        .join(
            latest_snapshot_subq,
            and_(
                Snapshot.token_address == latest_snapshot_subq.c.token_address,
                Snapshot.snapshot_time == latest_snapshot_subq.c.max_time,
            )
        )
    )

    result = await db.execute(current_snapshots_query)
    current_snapshots = {s.token_address: s for s in result.scalars().all()}

    if not current_snapshots:
        return []

    # Get past snapshots for comparison
    past_snapshot_subq = (
        select(
            Snapshot.token_address,
            func.max(Snapshot.snapshot_time).label("max_time")
        )
        .where(Snapshot.snapshot_time <= past_time)
        .group_by(Snapshot.token_address)
        .subquery()
    )

    past_snapshots_query = (
        select(Snapshot)
        .join(
            past_snapshot_subq,
            and_(
                Snapshot.token_address == past_snapshot_subq.c.token_address,
                Snapshot.snapshot_time == past_snapshot_subq.c.max_time,
            )
        )
    )

    result = await db.execute(past_snapshots_query)
    past_snapshots = {s.token_address: s for s in result.scalars().all()}

    # Get token info
    token_addresses = list(current_snapshots.keys())
    tokens_query = select(Token).where(Token.token_address.in_(token_addresses))
    result = await db.execute(tokens_query)
    tokens = {t.token_address: t for t in result.scalars().all()}

    # Calculate changes and build response
    coins_with_change = []

    for address, current in current_snapshots.items():
        token = tokens.get(address)
        if not token:
            continue

        current_cap = current.market_cap_usd or 0
        past = past_snapshots.get(address)
        past_cap = past.market_cap_usd if past else current_cap

        # Calculate percentage change
        if past_cap and past_cap > 0:
            change_pct = ((current_cap - past_cap) / past_cap) * 100
        else:
            change_pct = 0

        coins_with_change.append({
            "token_address": address,
            "name": token.name,
            "symbol": token.symbol,
            "market_cap": current_cap,
            "prev_market_cap": past_cap,
            "change_pct": round(change_pct, 2),
            "liquidity": current.liquidity_usd,
            "price": current.price_usd,
            "category": token.primary_category,
            "sub_category": token.sub_category,
        })

    # Sort by change percentage (descending) and return top N
    coins_with_change.sort(key=lambda x: x["change_pct"], reverse=True)

    return coins_with_change[:limit]


@router.get("/movers")
async def get_top_movers(
    time_window: TimeWindowType = Query("24h", description="Time window"),
    limit: int = Query(10, ge=1, le=50, description="Number of coins per category"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top gainers and losers.

    Returns separate lists of top gaining and top losing coins.
    """
    coins = await get_trending_coins(time_window, limit * 2, db)

    gainers = [c for c in coins if c["change_pct"] > 0][:limit]
    losers = sorted([c for c in coins if c["change_pct"] < 0], key=lambda x: x["change_pct"])[:limit]

    return {
        "gainers": gainers,
        "losers": losers,
        "time_window": time_window,
    }
