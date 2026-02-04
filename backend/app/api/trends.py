"""
API endpoints for trend data.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import Token, Snapshot, TrendAggregate
from ..schemas import (
    TrendResponse,
    TrendSummary,
    CoinResponse,
    CategoryTrend,
    PaginatedResponse,
)
from ..services.categorizer import get_category_emoji

router = APIRouter()


TimeWindowType = Literal["12h", "24h", "7d"]
SortByType = Literal["acceleration", "market_cap", "coin_count"]


def get_time_delta(time_window: str) -> timedelta:
    """Convert time window string to timedelta."""
    mapping = {
        "12h": timedelta(hours=12),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
    }
    return mapping.get(time_window, timedelta(hours=24))


@router.get("", response_model=List[CategoryTrend])
async def get_trends(
    time_window: TimeWindowType = Query("24h", description="Time window for trends"),
    sort_by: SortByType = Query("acceleration", description="Sort field"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of trends"),
    graduated_only: bool = Query(False, description="Only include graduated tokens (with liquidity)"),
    db: AsyncSession = Depends(get_db),
) -> List[CategoryTrend]:
    """
    Get all trends with aggregated stats.

    Returns trends sorted by the specified field within the given time window.
    """
    # Get the most recent snapshot time
    latest_snapshot_query = select(func.max(TrendAggregate.snapshot_time))
    result = await db.execute(latest_snapshot_query)
    latest_time = result.scalar()

    if not latest_time:
        return []

    # Query trend aggregates for the latest snapshot
    query = (
        select(TrendAggregate)
        .where(
            and_(
                TrendAggregate.snapshot_time == latest_time,
                TrendAggregate.time_window == time_window,
            )
        )
    )

    # Apply sorting
    if sort_by == "acceleration":
        query = query.order_by(desc(TrendAggregate.acceleration_score))
    elif sort_by == "market_cap":
        query = query.order_by(desc(TrendAggregate.total_market_cap))
    elif sort_by == "coin_count":
        query = query.order_by(desc(TrendAggregate.coin_count))

    query = query.limit(limit)

    result = await db.execute(query)
    trends = result.scalars().all()

    # Convert to response model
    response = []
    for trend in trends:
        # Calculate change percentages by comparing to previous snapshots
        change_1h = await _calculate_change(
            db, trend.category, trend.sub_category, time_window, hours=1
        )
        change_24h = await _calculate_change(
            db, trend.category, trend.sub_category, time_window, hours=24
        )

        response.append(
            CategoryTrend(
                category=trend.category,
                sub_category=trend.sub_category,
                emoji=get_category_emoji(trend.category, trend.sub_category),
                coin_count=trend.coin_count or 0,
                total_market_cap=trend.total_market_cap or 0.0,
                acceleration_score=trend.acceleration_score or 0.0,
                is_breakout_meta=trend.is_breakout_meta,
                change_1h=change_1h,
                change_24h=change_24h,
            )
        )

    return response


@router.get("/{category}/{sub_category}/coins", response_model=List[CoinResponse])
async def get_trend_coins(
    category: str,
    sub_category: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of coins"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    graduated_only: bool = Query(False, description="Only include graduated tokens (with liquidity)"),
    db: AsyncSession = Depends(get_db),
) -> List[CoinResponse]:
    """
    Get individual coins within a trend, sorted by market_cap desc.

    Returns coins belonging to the specified category/sub_category.
    """
    # URL decode the path parameters (FastAPI handles this automatically)
    # Handle "all" as a special case for sub_category
    if sub_category.lower() == "all":
        # Get all coins in the primary category
        if graduated_only:
            token_query = (
                select(Token)
                .where(and_(Token.primary_category == category, Token.is_graduated == True))
                .offset(offset)
                .limit(limit)
            )
        else:
            token_query = (
                select(Token)
                .where(Token.primary_category == category)
                .offset(offset)
                .limit(limit)
            )
    else:
        if graduated_only:
            token_query = (
                select(Token)
                .where(
                    and_(
                        Token.primary_category == category,
                        Token.sub_category == sub_category,
                        Token.is_graduated == True,
                    )
                )
                .offset(offset)
                .limit(limit)
            )
        else:
            token_query = (
                select(Token)
                .where(
                    and_(
                        Token.primary_category == category,
                        Token.sub_category == sub_category,
                    )
                )
                .offset(offset)
                .limit(limit)
            )

    result = await db.execute(token_query)
    tokens = result.scalars().all()

    if not tokens:
        return []

    # Get latest snapshots for these tokens
    token_addresses = [t.token_address for t in tokens]

    # Subquery to get the latest snapshot time for each token
    latest_snapshot_subq = (
        select(
            Snapshot.token_address,
            func.max(Snapshot.snapshot_time).label("max_time")
        )
        .where(Snapshot.token_address.in_(token_addresses))
        .group_by(Snapshot.token_address)
        .subquery()
    )

    # Get the latest snapshots
    snapshot_query = (
        select(Snapshot)
        .join(
            latest_snapshot_subq,
            and_(
                Snapshot.token_address == latest_snapshot_subq.c.token_address,
                Snapshot.snapshot_time == latest_snapshot_subq.c.max_time,
            )
        )
    )

    snapshot_result = await db.execute(snapshot_query)
    snapshots = {s.token_address: s for s in snapshot_result.scalars().all()}

    # Build response with market data - use price_change_24h from snapshot directly
    response = []
    for token in tokens:
        snapshot = snapshots.get(token.token_address)

        coin = CoinResponse(
            id=token.id,
            token_address=token.token_address,
            name=token.name,
            symbol=token.symbol,
            created_at=token.created_at,
            first_seen_at=token.first_seen_at,
            primary_category=token.primary_category,
            sub_category=token.sub_category,
            detected_keywords=token.detected_keywords,
            is_breakout_meta=token.is_breakout_meta,
            breakout_meta_cluster=token.breakout_meta_cluster,
            market_cap_usd=snapshot.market_cap_usd if snapshot else None,
            liquidity_usd=snapshot.liquidity_usd if snapshot else None,
            price_usd=snapshot.price_usd if snapshot else None,
            price_change_24h=snapshot.price_change_24h if snapshot else None,
            volume_24h=snapshot.volume_24h if snapshot else None,
            # Social links
            twitter_url=getattr(token, 'twitter_url', None),
            telegram_url=getattr(token, 'telegram_url', None),
            website_url=getattr(token, 'website_url', None),
            description=getattr(token, 'description', None),
        )
        response.append(coin)

    # Sort by market cap descending
    response.sort(key=lambda x: x.market_cap_usd or 0, reverse=True)

    return response


async def _calculate_change(
    db: AsyncSession,
    category: str,
    sub_category: Optional[str],
    time_window: str,
    hours: int,
) -> Optional[float]:
    """
    Calculate percentage change in market cap over the specified hours.
    """
    now = datetime.utcnow()
    past_time = now - timedelta(hours=hours)

    # Get the trend aggregate closest to the past time
    if sub_category:
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category == sub_category,
                    TrendAggregate.time_window == time_window,
                    TrendAggregate.snapshot_time <= past_time,
                )
            )
            .order_by(desc(TrendAggregate.snapshot_time))
            .limit(1)
        )
    else:
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category.is_(None),
                    TrendAggregate.time_window == time_window,
                    TrendAggregate.snapshot_time <= past_time,
                )
            )
            .order_by(desc(TrendAggregate.snapshot_time))
            .limit(1)
        )

    result = await db.execute(query)
    past_trend = result.scalar()

    if not past_trend or not past_trend.total_market_cap:
        return None

    # Get current market cap from the latest trend
    current_query = (
        select(TrendAggregate)
        .where(
            and_(
                TrendAggregate.category == category,
                TrendAggregate.sub_category == sub_category if sub_category else TrendAggregate.sub_category.is_(None),
                TrendAggregate.time_window == time_window,
            )
        )
        .order_by(desc(TrendAggregate.snapshot_time))
        .limit(1)
    )

    current_result = await db.execute(current_query)
    current_trend = current_result.scalar()

    if not current_trend or not current_trend.total_market_cap:
        return None

    # Calculate percentage change
    if past_trend.total_market_cap > 0:
        change = (
            (current_trend.total_market_cap - past_trend.total_market_cap)
            / past_trend.total_market_cap
            * 100
        )
        return round(change, 2)

    return None


async def _calculate_price_changes(
    db: AsyncSession,
    token_addresses: List[str],
) -> dict:
    """
    Calculate 24h price changes for a list of tokens.
    """
    if not token_addresses:
        return {}

    now = datetime.utcnow()
    past_time = now - timedelta(hours=24)

    changes = {}

    for address in token_addresses:
        # Get current price
        current_query = (
            select(Snapshot)
            .where(Snapshot.token_address == address)
            .order_by(desc(Snapshot.snapshot_time))
            .limit(1)
        )
        current_result = await db.execute(current_query)
        current_snapshot = current_result.scalar()

        if not current_snapshot or not current_snapshot.price_usd:
            changes[address] = None
            continue

        # Get price from 24h ago
        past_query = (
            select(Snapshot)
            .where(
                and_(
                    Snapshot.token_address == address,
                    Snapshot.snapshot_time <= past_time,
                )
            )
            .order_by(desc(Snapshot.snapshot_time))
            .limit(1)
        )
        past_result = await db.execute(past_query)
        past_snapshot = past_result.scalar()

        if not past_snapshot or not past_snapshot.price_usd:
            changes[address] = None
            continue

        if past_snapshot.price_usd > 0:
            change = (
                (current_snapshot.price_usd - past_snapshot.price_usd)
                / past_snapshot.price_usd
                * 100
            )
            changes[address] = round(change, 2)
        else:
            changes[address] = None

    return changes
