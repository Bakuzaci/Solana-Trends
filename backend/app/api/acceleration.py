"""
API endpoints for acceleration data.
"""
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from ..database import get_db
from ..models import TrendAggregate, Token
from ..schemas import CategoryTrend
from ..services.acceleration import get_acceleration_tier

router = APIRouter()


@router.get("/top", response_model=List[CategoryTrend])
async def get_top_accelerating_trends(
    limit: int = Query(10, ge=1, le=50, description="Number of top trends to return"),
    time_window: str = Query("24h", description="Time window for acceleration calculation"),
    db: AsyncSession = Depends(get_db),
) -> List[CategoryTrend]:
    """
    Get top fastest accelerating trends RIGHT NOW.

    Returns the top N trends sorted by acceleration score, representing
    categories that are experiencing the most rapid growth.
    """
    # Get the most recent snapshot time
    latest_snapshot_query = select(func.max(TrendAggregate.snapshot_time))
    result = await db.execute(latest_snapshot_query)
    latest_time = result.scalar()

    if not latest_time:
        return []

    # Query trend aggregates for the latest snapshot, sorted by acceleration
    query = (
        select(TrendAggregate)
        .where(
            and_(
                TrendAggregate.snapshot_time == latest_time,
                TrendAggregate.time_window == time_window,
                TrendAggregate.acceleration_score.isnot(None),
                TrendAggregate.acceleration_score > 0,
            )
        )
        .order_by(desc(TrendAggregate.acceleration_score))
        .limit(limit)
    )

    result = await db.execute(query)
    trends = result.scalars().all()

    # Calculate change percentages
    response = []
    for trend in trends:
        change_1h = await _calculate_mcap_change(
            db, trend.category, trend.sub_category, time_window, hours=1
        )
        change_24h = await _calculate_mcap_change(
            db, trend.category, trend.sub_category, time_window, hours=24
        )

        response.append(
            CategoryTrend(
                category=trend.category,
                sub_category=trend.sub_category,
                coin_count=trend.coin_count or 0,
                total_market_cap=trend.total_market_cap or 0.0,
                acceleration_score=trend.acceleration_score or 0.0,
                is_breakout_meta=trend.is_breakout_meta,
                change_1h=change_1h,
                change_24h=change_24h,
            )
        )

    return response


@router.get("/breakout-metas", response_model=List[CategoryTrend])
async def get_breakout_metas(
    limit: int = Query(10, ge=1, le=50, description="Number of breakout metas to return"),
    time_window: str = Query("24h", description="Time window"),
    db: AsyncSession = Depends(get_db),
) -> List[CategoryTrend]:
    """
    Get current breakout metas.

    Returns trends that have been flagged as breakout metas based on
    their acceleration score exceeding the threshold.
    """
    # Get the most recent snapshot time
    latest_snapshot_query = select(func.max(TrendAggregate.snapshot_time))
    result = await db.execute(latest_snapshot_query)
    latest_time = result.scalar()

    if not latest_time:
        return []

    # Query only breakout metas
    query = (
        select(TrendAggregate)
        .where(
            and_(
                TrendAggregate.snapshot_time == latest_time,
                TrendAggregate.time_window == time_window,
                TrendAggregate.is_breakout_meta == True,
            )
        )
        .order_by(desc(TrendAggregate.acceleration_score))
        .limit(limit)
    )

    result = await db.execute(query)
    trends = result.scalars().all()

    response = []
    for trend in trends:
        change_1h = await _calculate_mcap_change(
            db, trend.category, trend.sub_category, time_window, hours=1
        )
        change_24h = await _calculate_mcap_change(
            db, trend.category, trend.sub_category, time_window, hours=24
        )

        response.append(
            CategoryTrend(
                category=trend.category,
                sub_category=trend.sub_category,
                coin_count=trend.coin_count or 0,
                total_market_cap=trend.total_market_cap or 0.0,
                acceleration_score=trend.acceleration_score or 0.0,
                is_breakout_meta=True,
                change_1h=change_1h,
                change_24h=change_24h,
            )
        )

    return response


@router.get("/tier/{category}/{sub_category}")
async def get_acceleration_tier_for_trend(
    category: str,
    sub_category: str,
    time_window: str = Query("24h", description="Time window"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get the acceleration tier for a specific trend.

    Returns the acceleration score and tier (cold, warming, hot, explosive)
    for the specified category.
    """
    # Get the most recent snapshot time
    latest_snapshot_query = select(func.max(TrendAggregate.snapshot_time))
    result = await db.execute(latest_snapshot_query)
    latest_time = result.scalar()

    if not latest_time:
        return {"error": "No trend data available"}

    # Handle "all" sub-category
    if sub_category.lower() == "all":
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.snapshot_time == latest_time,
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category.is_(None),
                    TrendAggregate.time_window == time_window,
                )
            )
            .limit(1)
        )
    else:
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.snapshot_time == latest_time,
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category == sub_category,
                    TrendAggregate.time_window == time_window,
                )
            )
            .limit(1)
        )

    result = await db.execute(query)
    trend = result.scalar()

    if not trend:
        return {"error": "Trend not found"}

    score = trend.acceleration_score or 0.0
    tier = get_acceleration_tier(score)

    return {
        "category": category,
        "sub_category": sub_category if sub_category.lower() != "all" else None,
        "acceleration_score": score,
        "tier": tier,
        "is_breakout_meta": trend.is_breakout_meta,
        "coin_count": trend.coin_count,
        "total_market_cap": trend.total_market_cap,
    }


async def _calculate_mcap_change(
    db: AsyncSession,
    category: str,
    sub_category: str | None,
    time_window: str,
    hours: int,
) -> float | None:
    """
    Calculate percentage change in market cap over the specified hours.
    """
    now = datetime.utcnow()
    past_time = now - timedelta(hours=hours)

    # Build query for past trend
    if sub_category:
        past_query = (
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
        past_query = (
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

    past_result = await db.execute(past_query)
    past_trend = past_result.scalar()

    if not past_trend or not past_trend.total_market_cap:
        return None

    # Get current trend
    if sub_category:
        current_query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category == sub_category,
                    TrendAggregate.time_window == time_window,
                )
            )
            .order_by(desc(TrendAggregate.snapshot_time))
            .limit(1)
        )
    else:
        current_query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category.is_(None),
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

    if past_trend.total_market_cap > 0:
        change = (
            (current_trend.total_market_cap - past_trend.total_market_cap)
            / past_trend.total_market_cap
            * 100
        )
        return round(change, 2)

    return None
