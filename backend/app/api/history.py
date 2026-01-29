"""
API endpoints for historical trend data.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, asc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import TrendAggregate, Snapshot, Token

router = APIRouter()


PeriodType = Literal["24h", "7d", "14d"]


class HistoryDataPoint(BaseModel):
    """Single data point in historical trend data."""
    timestamp: datetime
    coin_count: int = 0
    total_market_cap: float = 0.0
    avg_market_cap: float = 0.0
    max_market_cap: float = 0.0
    acceleration_score: float = 0.0
    is_breakout_meta: bool = False


class TrendHistoryResponse(BaseModel):
    """Response model for trend history."""
    category: str
    sub_category: Optional[str] = None
    period: str
    data_points: List[HistoryDataPoint] = []
    summary: dict = {}


def get_period_delta(period: str) -> timedelta:
    """Convert period string to timedelta."""
    mapping = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "14d": timedelta(days=14),
    }
    return mapping.get(period, timedelta(hours=24))


@router.get("/{category}/{sub_category}", response_model=TrendHistoryResponse)
async def get_trend_history(
    category: str,
    sub_category: str,
    period: PeriodType = Query("24h", description="Historical period"),
    time_window: str = Query("24h", description="Time window for aggregates"),
    db: AsyncSession = Depends(get_db),
) -> TrendHistoryResponse:
    """
    Get historical trend data for charts.

    Returns time-series data for the specified category over the given period.
    """
    period_delta = get_period_delta(period)
    start_time = datetime.utcnow() - period_delta

    # Handle "all" sub-category meaning aggregate for the whole category
    if sub_category.lower() == "all":
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category.is_(None),
                    TrendAggregate.time_window == time_window,
                    TrendAggregate.snapshot_time >= start_time,
                )
            )
            .order_by(asc(TrendAggregate.snapshot_time))
        )
        actual_sub_category = None
    else:
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category == sub_category,
                    TrendAggregate.time_window == time_window,
                    TrendAggregate.snapshot_time >= start_time,
                )
            )
            .order_by(asc(TrendAggregate.snapshot_time))
        )
        actual_sub_category = sub_category

    result = await db.execute(query)
    aggregates = result.scalars().all()

    # Convert to data points
    data_points = []
    for agg in aggregates:
        data_points.append(
            HistoryDataPoint(
                timestamp=agg.snapshot_time,
                coin_count=agg.coin_count or 0,
                total_market_cap=agg.total_market_cap or 0.0,
                avg_market_cap=agg.avg_market_cap or 0.0,
                max_market_cap=agg.max_market_cap or 0.0,
                acceleration_score=agg.acceleration_score or 0.0,
                is_breakout_meta=agg.is_breakout_meta,
            )
        )

    # Calculate summary statistics
    summary = _calculate_summary(data_points)

    return TrendHistoryResponse(
        category=category,
        sub_category=actual_sub_category,
        period=period,
        data_points=data_points,
        summary=summary,
    )


@router.get("/{category}/{sub_category}/coins", response_model=List[dict])
async def get_trend_coins_history(
    category: str,
    sub_category: str,
    period: PeriodType = Query("24h", description="Historical period"),
    limit: int = Query(10, ge=1, le=50, description="Number of top coins"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get historical data for top coins in a trend.

    Returns time-series price/market cap data for individual coins.
    """
    period_delta = get_period_delta(period)
    start_time = datetime.utcnow() - period_delta

    # Get top tokens in the category by latest market cap
    if sub_category.lower() == "all":
        token_query = (
            select(Token)
            .where(Token.primary_category == category)
            .limit(limit * 2)  # Get more to filter by market cap
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
            .limit(limit * 2)
        )

    token_result = await db.execute(token_query)
    tokens = token_result.scalars().all()

    if not tokens:
        return []

    # Get snapshots for these tokens
    token_addresses = [t.token_address for t in tokens]
    snapshot_query = (
        select(Snapshot)
        .where(
            and_(
                Snapshot.token_address.in_(token_addresses),
                Snapshot.snapshot_time >= start_time,
            )
        )
        .order_by(Snapshot.token_address, asc(Snapshot.snapshot_time))
    )

    snapshot_result = await db.execute(snapshot_query)
    snapshots = snapshot_result.scalars().all()

    # Group snapshots by token
    token_data = {}
    for token in tokens:
        token_data[token.token_address] = {
            "token_address": token.token_address,
            "name": token.name,
            "symbol": token.symbol,
            "history": [],
            "latest_market_cap": 0,
        }

    for snapshot in snapshots:
        if snapshot.token_address in token_data:
            token_data[snapshot.token_address]["history"].append({
                "timestamp": snapshot.snapshot_time.isoformat(),
                "price_usd": snapshot.price_usd,
                "market_cap_usd": snapshot.market_cap_usd,
                "liquidity_usd": snapshot.liquidity_usd,
            })
            # Track latest market cap for sorting
            if snapshot.market_cap_usd:
                token_data[snapshot.token_address]["latest_market_cap"] = snapshot.market_cap_usd

    # Sort by latest market cap and take top N
    sorted_tokens = sorted(
        token_data.values(),
        key=lambda x: x["latest_market_cap"],
        reverse=True
    )[:limit]

    # Remove the helper field
    for token in sorted_tokens:
        del token["latest_market_cap"]

    return sorted_tokens


@router.get("/compare", response_model=dict)
async def compare_trends(
    categories: str = Query(..., description="Comma-separated category:sub_category pairs"),
    period: PeriodType = Query("24h", description="Historical period"),
    time_window: str = Query("24h", description="Time window for aggregates"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Compare multiple trends over time.

    Accepts comma-separated category pairs like "Animals:Dogs,Meme Culture:Classic Memes"
    and returns historical data for comparison charts.
    """
    period_delta = get_period_delta(period)
    start_time = datetime.utcnow() - period_delta

    # Parse category pairs
    category_pairs = []
    for pair in categories.split(","):
        parts = pair.strip().split(":")
        if len(parts) == 2:
            category_pairs.append((parts[0].strip(), parts[1].strip()))
        elif len(parts) == 1:
            category_pairs.append((parts[0].strip(), None))

    if not category_pairs:
        return {"error": "No valid category pairs provided"}

    # Get data for each category
    comparison_data = {}
    for category, sub_category in category_pairs:
        key = f"{category}:{sub_category}" if sub_category else category

        if sub_category and sub_category.lower() != "all":
            query = (
                select(TrendAggregate)
                .where(
                    and_(
                        TrendAggregate.category == category,
                        TrendAggregate.sub_category == sub_category,
                        TrendAggregate.time_window == time_window,
                        TrendAggregate.snapshot_time >= start_time,
                    )
                )
                .order_by(asc(TrendAggregate.snapshot_time))
            )
        else:
            query = (
                select(TrendAggregate)
                .where(
                    and_(
                        TrendAggregate.category == category,
                        TrendAggregate.sub_category.is_(None),
                        TrendAggregate.time_window == time_window,
                        TrendAggregate.snapshot_time >= start_time,
                    )
                )
                .order_by(asc(TrendAggregate.snapshot_time))
            )

        result = await db.execute(query)
        aggregates = result.scalars().all()

        comparison_data[key] = {
            "category": category,
            "sub_category": sub_category,
            "data_points": [
                {
                    "timestamp": agg.snapshot_time.isoformat(),
                    "coin_count": agg.coin_count or 0,
                    "total_market_cap": agg.total_market_cap or 0.0,
                    "acceleration_score": agg.acceleration_score or 0.0,
                }
                for agg in aggregates
            ],
        }

    return {
        "period": period,
        "trends": comparison_data,
    }


def _calculate_summary(data_points: List[HistoryDataPoint]) -> dict:
    """
    Calculate summary statistics for a series of data points.
    """
    if not data_points:
        return {
            "min_market_cap": 0,
            "max_market_cap": 0,
            "avg_market_cap": 0,
            "market_cap_change_pct": 0,
            "coin_count_change": 0,
            "peak_acceleration": 0,
            "breakout_periods": 0,
        }

    market_caps = [dp.total_market_cap for dp in data_points if dp.total_market_cap > 0]
    accelerations = [dp.acceleration_score for dp in data_points]
    breakout_count = sum(1 for dp in data_points if dp.is_breakout_meta)

    first_point = data_points[0]
    last_point = data_points[-1]

    market_cap_change = 0
    if first_point.total_market_cap > 0:
        market_cap_change = (
            (last_point.total_market_cap - first_point.total_market_cap)
            / first_point.total_market_cap
            * 100
        )

    return {
        "min_market_cap": min(market_caps) if market_caps else 0,
        "max_market_cap": max(market_caps) if market_caps else 0,
        "avg_market_cap": sum(market_caps) / len(market_caps) if market_caps else 0,
        "market_cap_change_pct": round(market_cap_change, 2),
        "coin_count_change": last_point.coin_count - first_point.coin_count,
        "peak_acceleration": max(accelerations) if accelerations else 0,
        "breakout_periods": breakout_count,
        "data_points_count": len(data_points),
    }
