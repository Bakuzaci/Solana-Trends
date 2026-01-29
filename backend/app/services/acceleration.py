"""
Acceleration score calculation service.

Calculates trend acceleration scores for categories based on
coin velocity, market cap velocity, and breakout factors.
"""
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CategoryMetrics:
    """Metrics for a category at a point in time."""
    category: str
    sub_category: Optional[str]
    timestamp: datetime
    coin_count: int
    total_market_cap: float
    avg_market_cap: float
    max_market_cap: float


@dataclass
class AccelerationResult:
    """Result of acceleration score calculation."""
    total_score: float  # 0-100
    coin_velocity_score: float  # 0-30
    mcap_velocity_score: float  # 0-40
    breakout_factor_score: float  # 0-30
    details: dict


def calculate_coin_velocity(
    current_count: int,
    previous_count: int,
    max_score: float = 30.0
) -> float:
    """
    Calculate coin velocity component of acceleration score.

    Measures how quickly new coins are appearing in a category.

    Args:
        current_count: Current number of coins in category
        previous_count: Previous number of coins in category
        max_score: Maximum possible score (default 30)

    Returns:
        Score from 0 to max_score
    """
    if previous_count == 0:
        if current_count > 0:
            # New category with coins - max velocity
            return max_score
        return 0.0

    # Calculate percentage increase
    growth_rate = (current_count - previous_count) / previous_count

    # Scale: 0% = 0 points, 100%+ = max points
    # Using a logarithmic scale to prevent extreme spikes
    if growth_rate <= 0:
        return 0.0

    # Log scale: 10% growth = ~10 points, 50% = ~20, 100%+ = 30
    import math
    score = min(max_score, max_score * math.log1p(growth_rate * 2) / math.log1p(2))

    return round(score, 2)


def calculate_mcap_velocity(
    current_mcap: float,
    previous_mcap: float,
    current_count: int,
    max_score: float = 40.0
) -> float:
    """
    Calculate market cap velocity component of acceleration score.

    Measures how quickly the total market cap of a category is growing.

    Args:
        current_mcap: Current total market cap
        previous_mcap: Previous total market cap
        current_count: Current coin count (for normalization)
        max_score: Maximum possible score (default 40)

    Returns:
        Score from 0 to max_score
    """
    if previous_mcap <= 0:
        if current_mcap > 0:
            return max_score
        return 0.0

    # Calculate percentage increase
    growth_rate = (current_mcap - previous_mcap) / previous_mcap

    if growth_rate <= 0:
        return 0.0

    import math

    # Apply diminishing returns for very high growth
    # 50% growth = ~20 points, 100% = ~30, 200%+ = ~40
    score = min(max_score, max_score * math.log1p(growth_rate) / math.log1p(3))

    # Bonus for sustained growth with many coins
    if current_count >= 10 and growth_rate > 0.5:
        score = min(max_score, score * 1.1)

    return round(score, 2)


def calculate_breakout_factor(
    current_metrics: CategoryMetrics,
    historical_metrics: List[CategoryMetrics],
    max_score: float = 30.0
) -> float:
    """
    Calculate breakout factor component of acceleration score.

    Detects if a category is experiencing unusual growth compared
    to its historical baseline.

    Args:
        current_metrics: Current category metrics
        historical_metrics: List of historical metrics for comparison
        max_score: Maximum possible score (default 30)

    Returns:
        Score from 0 to max_score
    """
    if not historical_metrics:
        # No history - moderate breakout factor for new categories
        if current_metrics.coin_count >= 5:
            return max_score * 0.5
        return 0.0

    # Calculate historical averages
    avg_historical_count = sum(m.coin_count for m in historical_metrics) / len(historical_metrics)
    avg_historical_mcap = sum(m.total_market_cap for m in historical_metrics) / len(historical_metrics)

    # Calculate standard deviations
    import math

    if len(historical_metrics) > 1:
        count_variance = sum((m.coin_count - avg_historical_count) ** 2 for m in historical_metrics) / len(historical_metrics)
        count_std = math.sqrt(count_variance) if count_variance > 0 else 1

        mcap_variance = sum((m.total_market_cap - avg_historical_mcap) ** 2 for m in historical_metrics) / len(historical_metrics)
        mcap_std = math.sqrt(mcap_variance) if mcap_variance > 0 else avg_historical_mcap * 0.1
    else:
        count_std = avg_historical_count * 0.2 if avg_historical_count > 0 else 1
        mcap_std = avg_historical_mcap * 0.2 if avg_historical_mcap > 0 else 1

    # Calculate z-scores (how many standard deviations from mean)
    count_z = (current_metrics.coin_count - avg_historical_count) / max(count_std, 1)
    mcap_z = (current_metrics.total_market_cap - avg_historical_mcap) / max(mcap_std, 1)

    # Combine z-scores (weighted average)
    combined_z = (count_z * 0.4 + mcap_z * 0.6)

    if combined_z <= 0:
        return 0.0

    # Score based on z-score: z=1 = 10pts, z=2 = 20pts, z=3+ = 30pts
    score = min(max_score, combined_z * 10)

    return round(score, 2)


def calculate_acceleration_score(
    current_metrics: CategoryMetrics,
    previous_metrics: Optional[CategoryMetrics] = None,
    historical_metrics: Optional[List[CategoryMetrics]] = None
) -> AccelerationResult:
    """
    Calculate the total acceleration score for a category.

    The acceleration score indicates how quickly a category/trend
    is growing and whether it might be a breakout meta.

    Components:
    - Coin Velocity (0-30): Rate of new coins appearing
    - Market Cap Velocity (0-40): Rate of market cap growth
    - Breakout Factor (0-30): Deviation from historical baseline

    Total score ranges from 0-100.

    Args:
        current_metrics: Current category metrics
        previous_metrics: Previous time period metrics (for velocity)
        historical_metrics: Historical metrics (for breakout detection)

    Returns:
        AccelerationResult with total and component scores
    """
    # Default previous metrics if not provided
    if previous_metrics is None:
        previous_metrics = CategoryMetrics(
            category=current_metrics.category,
            sub_category=current_metrics.sub_category,
            timestamp=current_metrics.timestamp - timedelta(hours=1),
            coin_count=0,
            total_market_cap=0.0,
            avg_market_cap=0.0,
            max_market_cap=0.0,
        )

    # Calculate component scores
    coin_velocity = calculate_coin_velocity(
        current_metrics.coin_count,
        previous_metrics.coin_count
    )

    mcap_velocity = calculate_mcap_velocity(
        current_metrics.total_market_cap,
        previous_metrics.total_market_cap,
        current_metrics.coin_count
    )

    breakout_factor = calculate_breakout_factor(
        current_metrics,
        historical_metrics or []
    )

    # Calculate total score
    total_score = coin_velocity + mcap_velocity + breakout_factor

    # Build details dictionary
    details = {
        "current_coin_count": current_metrics.coin_count,
        "previous_coin_count": previous_metrics.coin_count,
        "coin_count_change": current_metrics.coin_count - previous_metrics.coin_count,
        "current_total_mcap": current_metrics.total_market_cap,
        "previous_total_mcap": previous_metrics.total_market_cap,
        "mcap_change_pct": (
            ((current_metrics.total_market_cap - previous_metrics.total_market_cap) /
             previous_metrics.total_market_cap * 100)
            if previous_metrics.total_market_cap > 0 else 0
        ),
        "historical_periods": len(historical_metrics) if historical_metrics else 0,
    }

    return AccelerationResult(
        total_score=round(total_score, 2),
        coin_velocity_score=coin_velocity,
        mcap_velocity_score=mcap_velocity,
        breakout_factor_score=breakout_factor,
        details=details,
    )


def is_breakout_meta(acceleration_score: float, threshold: float = 70.0) -> bool:
    """
    Determine if a category qualifies as a breakout meta.

    Args:
        acceleration_score: Total acceleration score (0-100)
        threshold: Minimum score to be considered breakout (default 70)

    Returns:
        True if the category is a breakout meta
    """
    return acceleration_score >= threshold


def get_acceleration_tier(score: float) -> str:
    """
    Get a human-readable tier for an acceleration score.

    Args:
        score: Acceleration score (0-100)

    Returns:
        Tier name: "cold", "warming", "hot", "explosive"
    """
    if score >= 80:
        return "explosive"
    elif score >= 60:
        return "hot"
    elif score >= 40:
        return "warming"
    else:
        return "cold"
