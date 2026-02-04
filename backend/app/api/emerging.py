"""
API endpoints for emerging/uncategorized metas.

Surfaces tokens that don't match known categories but cluster together,
indicating potential new trends.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import Token, Snapshot
from ..schemas import CoinResponse, CategoryTrend
from ..services.breakout_detector import (
    BreakoutDetector,
    TokenInfo,
    detect_breakout_metas,
)


router = APIRouter()


@router.get("/clusters", response_model=List[dict])
async def get_emerging_clusters(
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    min_cluster_size: int = Query(3, ge=2, le=10, description="Minimum tokens per cluster"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get emerging meta clusters from uncategorized tokens.
    
    Uses DBSCAN clustering on token names to detect emerging trends
    that don't match existing categories.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get uncategorized tokens from the last N hours
    query = (
        select(Token)
        .where(
            and_(
                Token.first_seen_at >= cutoff_time,
                or_(
                    Token.primary_category.is_(None),
                    Token.primary_category == "Miscellaneous",
                )
            )
        )
    )
    
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    if len(tokens) < min_cluster_size:
        return []
    
    # Convert to TokenInfo for clustering
    token_infos = [
        TokenInfo(
            address=t.token_address,
            name=t.name,
            symbol=t.symbol,
        )
        for t in tokens
    ]
    
    # Run breakout detection
    clusters = detect_breakout_metas(
        token_infos,
        min_cluster_size=min_cluster_size,
        eps=0.6,
    )
    
    if not clusters:
        return []
    
    # Get market data for clustered tokens
    all_addresses = []
    for cluster in clusters:
        all_addresses.extend(cluster.tokens)
    
    # Get latest snapshots
    snapshot_subq = (
        select(
            Snapshot.token_address,
            func.max(Snapshot.snapshot_time).label("max_time")
        )
        .where(Snapshot.token_address.in_(all_addresses))
        .group_by(Snapshot.token_address)
        .subquery()
    )
    
    snapshot_query = (
        select(Snapshot)
        .join(
            snapshot_subq,
            and_(
                Snapshot.token_address == snapshot_subq.c.token_address,
                Snapshot.snapshot_time == snapshot_subq.c.max_time,
            )
        )
    )
    
    snapshot_result = await db.execute(snapshot_query)
    snapshots = {s.token_address: s for s in snapshot_result.scalars().all()}
    
    # Build response
    response = []
    for cluster in clusters:
        # Calculate cluster stats
        cluster_mcap = 0
        cluster_volume = 0
        cluster_tokens = []
        
        for addr in cluster.tokens:
            snapshot = snapshots.get(addr)
            token = next((t for t in tokens if t.token_address == addr), None)
            
            if snapshot:
                cluster_mcap += snapshot.market_cap_usd or 0
                cluster_volume += snapshot.volume_24h or 0
            
            if token:
                cluster_tokens.append({
                    "token_address": token.token_address,
                    "name": token.name,
                    "symbol": token.symbol,
                    "market_cap_usd": snapshot.market_cap_usd if snapshot else None,
                    "volume_24h": snapshot.volume_24h if snapshot else None,
                    "price_change_24h": snapshot.price_change_24h if snapshot else None,
                })
        
        response.append({
            "cluster_id": cluster.cluster_id,
            "cluster_name": cluster.cluster_name,
            "common_keywords": cluster.common_keywords,
            "confidence_score": cluster.confidence_score,
            "token_count": cluster.size,
            "total_market_cap": cluster_mcap,
            "total_volume_24h": cluster_volume,
            "tokens": cluster_tokens,
        })
    
    # Sort by total volume (most active clusters first)
    response.sort(key=lambda x: x["total_volume_24h"], reverse=True)
    
    return response


@router.get("/uncategorized", response_model=List[CoinResponse])
async def get_uncategorized_tokens(
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    limit: int = Query(50, ge=1, le=200, description="Maximum tokens"),
    min_volume: float = Query(0, ge=0, description="Minimum 24h volume"),
    db: AsyncSession = Depends(get_db),
) -> List[CoinResponse]:
    """
    Get uncategorized tokens sorted by volume.
    
    These are tokens that don't match known category keywords,
    potentially representing new emerging metas.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get uncategorized tokens
    query = (
        select(Token)
        .where(
            and_(
                Token.first_seen_at >= cutoff_time,
                or_(
                    Token.primary_category.is_(None),
                    Token.primary_category == "Miscellaneous",
                )
            )
        )
        .limit(limit * 2)  # Fetch extra for filtering
    )
    
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    if not tokens:
        return []
    
    # Get latest snapshots
    token_addresses = [t.token_address for t in tokens]
    
    snapshot_subq = (
        select(
            Snapshot.token_address,
            func.max(Snapshot.snapshot_time).label("max_time")
        )
        .where(Snapshot.token_address.in_(token_addresses))
        .group_by(Snapshot.token_address)
        .subquery()
    )
    
    snapshot_query = (
        select(Snapshot)
        .join(
            snapshot_subq,
            and_(
                Snapshot.token_address == snapshot_subq.c.token_address,
                Snapshot.snapshot_time == snapshot_subq.c.max_time,
            )
        )
    )
    
    snapshot_result = await db.execute(snapshot_query)
    snapshots = {s.token_address: s for s in snapshot_result.scalars().all()}
    
    # Build response
    response = []
    for token in tokens:
        snapshot = snapshots.get(token.token_address)
        
        # Apply volume filter
        volume = snapshot.volume_24h if snapshot else 0
        if volume < min_volume:
            continue
        
        coin = CoinResponse(
            id=token.id,
            token_address=token.token_address,
            name=token.name,
            symbol=token.symbol,
            created_at=token.created_at,
            first_seen_at=token.first_seen_at,
            primary_category=token.primary_category or "Emerging",
            sub_category=token.sub_category or "Uncategorized",
            detected_keywords=token.detected_keywords,
            is_breakout_meta=token.is_breakout_meta,
            breakout_meta_cluster=token.breakout_meta_cluster,
            market_cap_usd=snapshot.market_cap_usd if snapshot else None,
            liquidity_usd=snapshot.liquidity_usd if snapshot else None,
            price_usd=snapshot.price_usd if snapshot else None,
            price_change_24h=snapshot.price_change_24h if snapshot else None,
            volume_24h=snapshot.volume_24h if snapshot else None,
        )
        response.append(coin)
    
    # Sort by volume descending
    response.sort(key=lambda x: x.volume_24h or 0, reverse=True)
    
    return response[:limit]


@router.get("/trending-names", response_model=List[dict])
async def get_trending_token_names(
    hours: int = Query(6, ge=1, le=48, description="Look back hours"),
    limit: int = Query(20, ge=1, le=50, description="Maximum keywords"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get trending words/phrases from recent token names.
    
    Analyzes token names to find commonly appearing words,
    useful for spotting emerging trends before they form clusters.
    """
    from collections import Counter
    import re
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get recent tokens
    query = (
        select(Token)
        .where(Token.first_seen_at >= cutoff_time)
    )
    
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    if not tokens:
        return []
    
    # Extract words from token names
    stop_words = {
        "the", "a", "an", "of", "in", "to", "for", "on", "with", "by",
        "coin", "token", "sol", "solana", "inu", "elon", "moon",
        "pump", "fun", "meme", "crypto", "chain", "finance", "fi",
    }
    
    word_counts = Counter()
    word_tokens = {}  # Track which tokens contain each word
    
    for token in tokens:
        # Extract words from name
        words = re.findall(r'[a-zA-Z]+', token.name.lower())
        
        for word in words:
            if len(word) >= 3 and word not in stop_words:
                word_counts[word] += 1
                if word not in word_tokens:
                    word_tokens[word] = []
                word_tokens[word].append({
                    "name": token.name,
                    "symbol": token.symbol,
                    "address": token.token_address,
                })
    
    # Get most common words (appearing in 2+ tokens)
    trending = [
        {
            "word": word,
            "count": count,
            "tokens": word_tokens[word][:5],  # First 5 tokens
        }
        for word, count in word_counts.most_common(limit * 2)
        if count >= 2
    ][:limit]
    
    return trending
