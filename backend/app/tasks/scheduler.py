"""
Background task scheduler using APScheduler.

Handles periodic fetching of token data, categorization,
snapshot storage, and trend aggregation.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import func, and_
from sqlalchemy.future import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..config import settings
from ..database import async_session_maker
from ..models import Token, Snapshot, TrendAggregate
from ..services.data_collector import (
    fetch_new_tokens,
    fetch_token_prices,
    fetch_graduated_tokens,
    TokenData,
)
from ..services.categorizer import categorize_token
from ..services.acceleration import (
    calculate_acceleration_score,
    is_breakout_meta,
    CategoryMetrics,
)
from ..services.breakout_detector import (
    BreakoutDetector,
    TokenInfo,
    detect_breakout_metas,
)


# Time windows for trend aggregation
TIME_WINDOWS = ["12h", "24h", "7d"]


async def snapshot_job():
    """
    Main snapshot job that runs periodically.

    1. Fetches new tokens from the data source
    2. Categorizes new tokens
    3. Stores/updates token records
    4. Creates price snapshots for all tokens
    """
    print(f"[{datetime.utcnow()}] Starting snapshot job...")

    async with async_session_maker() as session:
        try:
            # Fetch new tokens from PumpFun
            print("Fetching new tokens...")
            new_tokens = await fetch_new_tokens(limit=100)
            print(f"Fetched {len(new_tokens)} new tokens")

            # Also fetch graduated tokens (these have real liquidity and DEX pairs)
            print("Fetching graduated tokens...")
            graduated_tokens = await fetch_graduated_tokens(limit=50)
            print(f"Fetched {len(graduated_tokens)} graduated tokens")

            # Combine tokens, avoiding duplicates
            seen_addresses = set()
            all_tokens = []
            for t in new_tokens + graduated_tokens:
                if t.token_address not in seen_addresses:
                    seen_addresses.add(t.token_address)
                    all_tokens.append(t)
            print(f"Processing {len(all_tokens)} unique tokens")

            # Process and store tokens
            tokens_created = 0
            tokens_updated = 0

            for token_data in all_tokens:
                # Check if token already exists
                existing = await session.execute(
                    select(Token).where(Token.token_address == token_data.token_address)
                )
                existing_token = existing.scalar()

                if existing_token:
                    tokens_updated += 1
                else:
                    # Categorize new token
                    primary_cat, sub_cat, keywords = categorize_token(
                        token_data.name,
                        token_data.symbol
                    )

                    # Create new token record
                    # is_graduated will be set later based on liquidity
                    new_token = Token(
                        token_address=token_data.token_address,
                        name=token_data.name,
                        symbol=token_data.symbol,
                        created_at=token_data.created_at,
                        first_seen_at=datetime.utcnow(),
                        primary_category=primary_cat,
                        sub_category=sub_cat,
                        detected_keywords=",".join(keywords) if keywords else None,
                        is_graduated=False,  # Will be updated based on liquidity
                    )
                    session.add(new_token)
                    tokens_created += 1

            await session.commit()
            print(f"Tokens - Created: {tokens_created}, Updated: {tokens_updated}")

            # Create initial snapshots using data from the token endpoints
            # This preserves liquidity/market cap from PumpFun endpoints
            now = datetime.utcnow()
            snapshots_created = 0

            # Build a map of token data from the fetched tokens
            token_data_map = {t.token_address: t for t in all_tokens}

            # Fetch additional price data (pairs endpoint for price changes)
            new_token_addresses = [t.token_address for t in all_tokens]
            prices = {}
            if new_token_addresses:
                print(f"Fetching additional price data for {len(new_token_addresses)} tokens...")
                prices = await fetch_token_prices(new_token_addresses)

            graduated_updated = 0
            for token_data in all_tokens:
                address = token_data.token_address
                price_update = prices.get(address, {})

                # Prefer data from token endpoint, fall back to price endpoint
                # Token endpoints have better data for new/graduated tokens
                market_cap = token_data.market_cap_usd or price_update.get("market_cap_usd") or 0
                liquidity = token_data.liquidity_usd or price_update.get("liquidity_usd") or 0
                price = token_data.price_usd or price_update.get("price_usd") or 0

                # Price change and volume only come from pairs endpoint
                price_change_24h = price_update.get("price_change_24h")
                volume_24h = price_update.get("volume_24h")

                snapshot = Snapshot(
                    token_address=address,
                    snapshot_time=now,
                    market_cap_usd=market_cap,
                    liquidity_usd=liquidity,
                    price_usd=price,
                    price_change_24h=price_change_24h,
                    volume_24h=volume_24h,
                )
                session.add(snapshot)
                snapshots_created += 1

                # Update graduation status based on liquidity
                # A token is graduated if it has real DEX liquidity (migrated from bonding curve)
                is_graduated = liquidity > 0
                update_query = (
                    Token.__table__.update()
                    .where(Token.token_address == address)
                    .values(is_graduated=is_graduated)
                )
                await session.execute(update_query)
                if is_graduated:
                    graduated_updated += 1

            await session.commit()
            print(f"Created {snapshots_created} price snapshots, marked {graduated_updated} as graduated")

            # Fetch updated prices for existing tokens
            await _update_existing_token_prices(session)

            # Run breakout detection on recent tokens
            await _detect_breakouts(session)

            print(f"[{datetime.utcnow()}] Snapshot job completed successfully")

        except Exception as e:
            print(f"Error in snapshot job: {e}")
            await session.rollback()
            raise


async def _update_existing_token_prices(session):
    """
    Update prices for existing tokens that weren't in the new fetch.
    """
    # Get tokens that haven't been updated recently
    cutoff_time = datetime.utcnow() - timedelta(minutes=settings.snapshot_interval_minutes)

    # Find tokens without recent snapshots
    subquery = (
        select(Snapshot.token_address)
        .where(Snapshot.snapshot_time > cutoff_time)
        .distinct()
        .subquery()
    )

    query = (
        select(Token.token_address)
        .where(Token.token_address.notin_(select(subquery)))
        .limit(50)  # Batch to avoid rate limits
    )

    result = await session.execute(query)
    token_addresses = [row[0] for row in result.fetchall()]

    if not token_addresses:
        return

    print(f"Updating prices for {len(token_addresses)} existing tokens...")

    # Fetch prices
    prices = await fetch_token_prices(token_addresses)

    # Create snapshots and update graduation status based on liquidity
    now = datetime.utcnow()
    graduated_count = 0
    for address, price_data in prices.items():
        liquidity = price_data.get("liquidity_usd") or 0

        snapshot = Snapshot(
            token_address=address,
            snapshot_time=now,
            market_cap_usd=price_data.get("market_cap_usd"),
            liquidity_usd=liquidity,
            price_usd=price_data.get("price_usd"),
            price_change_24h=price_data.get("price_change_24h"),
            volume_24h=price_data.get("volume_24h"),
        )
        session.add(snapshot)

        # Update graduation status based on liquidity
        is_graduated = liquidity > 0
        update_query = (
            Token.__table__.update()
            .where(Token.token_address == address)
            .values(is_graduated=is_graduated)
        )
        await session.execute(update_query)
        if is_graduated:
            graduated_count += 1

    await session.commit()
    print(f"Created {len(prices)} price snapshots, {graduated_count} graduated")


async def _detect_breakouts(session):
    """
    Run breakout detection on recent tokens.
    """
    # Get tokens from the last 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)

    query = (
        select(Token)
        .where(Token.first_seen_at >= cutoff_time)
    )

    result = await session.execute(query)
    recent_tokens = result.scalars().all()

    if len(recent_tokens) < 10:
        return

    # Convert to TokenInfo for breakout detector
    token_infos = [
        TokenInfo(
            address=t.token_address,
            name=t.name,
            symbol=t.symbol
        )
        for t in recent_tokens
    ]

    # Run detection
    clusters = detect_breakout_metas(token_infos, min_cluster_size=3, eps=0.6)

    if not clusters:
        return

    print(f"Detected {len(clusters)} potential breakout metas")

    # Update tokens with breakout info
    for cluster in clusters:
        for token_address in cluster.tokens:
            await session.execute(
                select(Token)
                .where(Token.token_address == token_address)
            )
            # Using update for efficiency
            update_query = (
                Token.__table__.update()
                .where(Token.token_address == token_address)
                .values(
                    is_breakout_meta=True,
                    breakout_meta_cluster=cluster.cluster_name
                )
            )
            await session.execute(update_query)

    await session.commit()


async def aggregate_job():
    """
    Aggregation job that calculates trend statistics.

    1. Groups tokens by category
    2. Calculates aggregate statistics
    3. Computes acceleration scores
    4. Stores trend aggregates
    """
    print(f"[{datetime.utcnow()}] Starting aggregation job...")

    async with async_session_maker() as session:
        try:
            now = datetime.utcnow()

            for time_window in TIME_WINDOWS:
                print(f"Processing time window: {time_window}")
                await _aggregate_for_time_window(session, now, time_window)

            print(f"[{datetime.utcnow()}] Aggregation job completed successfully")

        except Exception as e:
            print(f"Error in aggregation job: {e}")
            await session.rollback()
            raise


async def _aggregate_for_time_window(session, snapshot_time: datetime, time_window: str):
    """
    Calculate and store trend aggregates for a specific time window.
    """
    # Parse time window to get the lookback period
    window_hours = {"12h": 12, "24h": 24, "7d": 168}
    hours = window_hours.get(time_window, 24)
    window_start = snapshot_time - timedelta(hours=hours)

    # Get all unique category combinations
    category_query = (
        select(Token.primary_category, Token.sub_category)
        .where(Token.primary_category.isnot(None))
        .distinct()
    )
    result = await session.execute(category_query)
    categories = result.fetchall()

    for primary_cat, sub_cat in categories:
        if not primary_cat:
            continue

        # Get tokens in this category
        token_query = (
            select(Token)
            .where(
                and_(
                    Token.primary_category == primary_cat,
                    Token.sub_category == sub_cat if sub_cat else Token.sub_category.is_(None),
                )
            )
        )
        token_result = await session.execute(token_query)
        tokens = token_result.scalars().all()

        if not tokens:
            continue

        token_addresses = [t.token_address for t in tokens]

        # Get latest snapshots for these tokens
        snapshot_subq = (
            select(
                Snapshot.token_address,
                func.max(Snapshot.snapshot_time).label("max_time")
            )
            .where(
                and_(
                    Snapshot.token_address.in_(token_addresses),
                    Snapshot.snapshot_time >= window_start,
                )
            )
            .group_by(Snapshot.token_address)
            .subquery()
        )

        latest_snapshots_query = (
            select(Snapshot)
            .join(
                snapshot_subq,
                and_(
                    Snapshot.token_address == snapshot_subq.c.token_address,
                    Snapshot.snapshot_time == snapshot_subq.c.max_time,
                )
            )
        )

        snapshot_result = await session.execute(latest_snapshots_query)
        snapshots = snapshot_result.scalars().all()

        # Calculate aggregate statistics
        coin_count = len(tokens)
        market_caps = [s.market_cap_usd for s in snapshots if s.market_cap_usd]
        total_market_cap = sum(market_caps) if market_caps else 0
        avg_market_cap = total_market_cap / len(market_caps) if market_caps else 0
        max_market_cap = max(market_caps) if market_caps else 0

        # Find top coin
        top_coin = None
        top_coin_name = None
        if snapshots:
            top_snapshot = max(snapshots, key=lambda s: s.market_cap_usd or 0)
            top_coin = top_snapshot.token_address
            for t in tokens:
                if t.token_address == top_coin:
                    top_coin_name = t.name
                    break

        # Calculate acceleration score
        current_metrics = CategoryMetrics(
            category=primary_cat,
            sub_category=sub_cat,
            timestamp=snapshot_time,
            coin_count=coin_count,
            total_market_cap=total_market_cap,
            avg_market_cap=avg_market_cap,
            max_market_cap=max_market_cap,
        )

        # Get previous metrics for velocity calculation
        previous_metrics = await _get_previous_metrics(
            session, primary_cat, sub_cat, time_window, hours=1
        )

        # Get historical metrics for breakout detection
        historical_metrics = await _get_historical_metrics(
            session, primary_cat, sub_cat, time_window, periods=6
        )

        acceleration_result = calculate_acceleration_score(
            current_metrics,
            previous_metrics,
            historical_metrics
        )

        is_breakout = is_breakout_meta(acceleration_result.total_score)

        # Store the aggregate
        aggregate = TrendAggregate(
            snapshot_time=snapshot_time,
            category=primary_cat,
            sub_category=sub_cat,
            time_window=time_window,
            coin_count=coin_count,
            total_market_cap=total_market_cap,
            avg_market_cap=avg_market_cap,
            max_market_cap=max_market_cap,
            top_coin_address=top_coin,
            top_coin_name=top_coin_name,
            acceleration_score=acceleration_result.total_score,
            is_breakout_meta=is_breakout,
        )

        session.add(aggregate)

    await session.commit()


async def _get_previous_metrics(
    session,
    category: str,
    sub_category: Optional[str],
    time_window: str,
    hours: int = 1
) -> Optional[CategoryMetrics]:
    """
    Get metrics from a previous time period for velocity calculation.
    """
    past_time = datetime.utcnow() - timedelta(hours=hours)

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
            .order_by(TrendAggregate.snapshot_time.desc())
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
            .order_by(TrendAggregate.snapshot_time.desc())
            .limit(1)
        )

    result = await session.execute(query)
    previous = result.scalar()

    if not previous:
        return None

    return CategoryMetrics(
        category=previous.category,
        sub_category=previous.sub_category,
        timestamp=previous.snapshot_time,
        coin_count=previous.coin_count or 0,
        total_market_cap=previous.total_market_cap or 0,
        avg_market_cap=previous.avg_market_cap or 0,
        max_market_cap=previous.max_market_cap or 0,
    )


async def _get_historical_metrics(
    session,
    category: str,
    sub_category: Optional[str],
    time_window: str,
    periods: int = 6
) -> List[CategoryMetrics]:
    """
    Get historical metrics for breakout detection.
    """
    if sub_category:
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category == sub_category,
                    TrendAggregate.time_window == time_window,
                )
            )
            .order_by(TrendAggregate.snapshot_time.desc())
            .limit(periods)
        )
    else:
        query = (
            select(TrendAggregate)
            .where(
                and_(
                    TrendAggregate.category == category,
                    TrendAggregate.sub_category.is_(None),
                    TrendAggregate.time_window == time_window,
                )
            )
            .order_by(TrendAggregate.snapshot_time.desc())
            .limit(periods)
        )

    result = await session.execute(query)
    historical = result.scalars().all()

    return [
        CategoryMetrics(
            category=h.category,
            sub_category=h.sub_category,
            timestamp=h.snapshot_time,
            coin_count=h.coin_count or 0,
            total_market_cap=h.total_market_cap or 0,
            avg_market_cap=h.avg_market_cap or 0,
            max_market_cap=h.max_market_cap or 0,
        )
        for h in historical
    ]


async def start_scheduler() -> AsyncIOScheduler:
    """
    Start the background scheduler.

    Returns:
        The running AsyncIOScheduler instance
    """
    scheduler = AsyncIOScheduler()

    # Add snapshot job
    scheduler.add_job(
        snapshot_job,
        trigger=IntervalTrigger(minutes=settings.snapshot_interval_minutes),
        id="snapshot_job",
        name="Fetch tokens and create snapshots",
        replace_existing=True,
    )

    # Add aggregation job (runs slightly after snapshot job)
    scheduler.add_job(
        aggregate_job,
        trigger=IntervalTrigger(minutes=settings.snapshot_interval_minutes),
        id="aggregate_job",
        name="Calculate trend aggregates",
        replace_existing=True,
    )

    # Start the scheduler
    scheduler.start()

    # Schedule initial jobs to run after a short delay (non-blocking)
    # This allows the app to start responding to health checks quickly
    print("Scheduling initial data collection...")
    scheduler.add_job(
        snapshot_job,
        trigger="date",  # Run once immediately
        id="initial_snapshot_job",
        name="Initial snapshot fetch",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        aggregate_job,
        trigger="date",  # Run once immediately
        id="initial_aggregate_job",
        name="Initial aggregation",
        replace_existing=True,
        misfire_grace_time=300,
    )

    return scheduler


async def stop_scheduler(scheduler: AsyncIOScheduler):
    """
    Stop the background scheduler gracefully.

    Args:
        scheduler: The running scheduler instance
    """
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        print("Scheduler shutdown complete")
