"""
API endpoints for searching tokens and discovering meta relationships.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import Token, Snapshot, MetaRelationship
from ..schemas import CoinResponse
from ..services.social_listening import (
    discover_meta_relationships,
    search_related_metas,
    get_all_known_relationships,
    MetaDiscovery,
)

router = APIRouter()


class MetaRelationshipResponse(BaseModel):
    """Response model for a meta relationship."""
    source_keyword: str
    related_keyword: str
    relationship_type: str
    confidence: float
    context: Optional[str] = None


class SearchResult(BaseModel):
    """Search result containing coins and related metas."""
    query: str
    coins: List[CoinResponse]
    related_metas: List[MetaRelationshipResponse]
    suggestions: List[str]


class TrendingMetaResponse(BaseModel):
    """Response model for trending metas."""
    keyword: str
    mention_count: int
    related_keywords: List[str]
    source: str


@router.get("/coins", response_model=SearchResult)
async def search_coins(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    graduated_only: bool = Query(False, description="Only graduated tokens"),
    db: AsyncSession = Depends(get_db),
) -> SearchResult:
    """
    Search for coins by name, symbol, or keyword.

    Also returns related metas that match the search term.
    For example, searching "claw" will return:
    - All coins with "claw" in name/symbol
    - Related metas like "clawd" -> "molt" relationship

    This helps users discover the full meta ecosystem around a term.
    """
    query_lower = q.lower()

    # Search tokens by name, symbol, or detected keywords
    base_query = select(Token).where(
        or_(
            func.lower(Token.name).contains(query_lower),
            func.lower(Token.symbol).contains(query_lower),
            func.lower(Token.detected_keywords).contains(query_lower),
            func.lower(Token.primary_category).contains(query_lower),
            func.lower(Token.sub_category).contains(query_lower),
        )
    )

    if graduated_only:
        base_query = base_query.where(Token.is_graduated == True)

    base_query = base_query.limit(limit)

    result = await db.execute(base_query)
    tokens = result.scalars().all()

    # Get latest snapshots for these tokens
    token_addresses = [t.token_address for t in tokens]
    snapshots = {}

    if token_addresses:
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

    # Build coin responses
    coins = []
    for token in tokens:
        snapshot = snapshots.get(token.token_address)
        coins.append(CoinResponse(
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
        ))

    # Sort by market cap
    coins.sort(key=lambda x: x.market_cap_usd or 0, reverse=True)

    # Find related metas
    all_relationships = get_all_known_relationships()
    related = search_related_metas(q, all_relationships)

    related_metas = [
        MetaRelationshipResponse(
            source_keyword=r.source_keyword,
            related_keyword=r.related_keyword,
            relationship_type=r.relationship_type,
            confidence=r.confidence,
            context=r.context,
        )
        for r in related[:10]  # Limit to top 10 relationships
    ]

    # Generate suggestions based on related metas and found coins
    suggestions = set()
    for rel in related:
        suggestions.add(rel.source_keyword)
        suggestions.add(rel.related_keyword)
    for coin in coins[:5]:
        if coin.primary_category:
            suggestions.add(coin.primary_category)
        if coin.sub_category:
            suggestions.add(coin.sub_category)

    # Remove the original query from suggestions
    suggestions.discard(query_lower)
    suggestions.discard(q)

    return SearchResult(
        query=q,
        coins=coins,
        related_metas=related_metas,
        suggestions=list(suggestions)[:10],
    )


@router.get("/metas", response_model=List[MetaRelationshipResponse])
async def get_meta_relationships(
    source: Optional[str] = Query(None, description="Filter by source keyword"),
    db: AsyncSession = Depends(get_db),
) -> List[MetaRelationshipResponse]:
    """
    Get all known meta relationships.

    Optionally filter by source keyword to see what metas
    spawned from a particular trend.
    """
    # First check database for stored relationships
    query = select(MetaRelationship)
    if source:
        query = query.where(
            func.lower(MetaRelationship.source_keyword).contains(source.lower())
        )

    result = await db.execute(query)
    db_relationships = result.scalars().all()

    # Also include known relationships from the service
    known = get_all_known_relationships()

    # Combine and deduplicate
    seen = set()
    all_rels = []

    for rel in db_relationships:
        key = (rel.source_keyword.lower(), rel.related_keyword.lower())
        if key not in seen:
            seen.add(key)
            all_rels.append(MetaRelationshipResponse(
                source_keyword=rel.source_keyword,
                related_keyword=rel.related_keyword,
                relationship_type=rel.relationship_type,
                confidence=rel.confidence_score,
                context=None,
            ))

    for rel in known:
        if source and source.lower() not in rel.source_keyword.lower():
            continue
        key = (rel.source_keyword.lower(), rel.related_keyword.lower())
        if key not in seen:
            seen.add(key)
            all_rels.append(MetaRelationshipResponse(
                source_keyword=rel.source_keyword,
                related_keyword=rel.related_keyword,
                relationship_type=rel.relationship_type,
                confidence=rel.confidence,
                context=rel.context,
            ))

    # Sort by confidence
    all_rels.sort(key=lambda x: x.confidence, reverse=True)

    return all_rels


@router.get("/trending", response_model=List[TrendingMetaResponse])
async def get_trending_metas(
    db: AsyncSession = Depends(get_db),
) -> List[TrendingMetaResponse]:
    """
    Get currently trending metas based on social listening.

    This endpoint triggers a fresh social listening scan to
    discover what's trending in the Solana meme coin space.
    """
    topics, discoveries = await discover_meta_relationships()

    return [
        TrendingMetaResponse(
            keyword=t.keyword,
            mention_count=t.mention_count,
            related_keywords=t.co_keywords[:5],
            source=t.source,
        )
        for t in topics[:20]
    ]


@router.post("/discover")
async def trigger_meta_discovery(
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger meta relationship discovery.

    Runs the social listening service to find new meta relationships
    and stores them in the database.
    """
    topics, discoveries = await discover_meta_relationships()

    # Store new relationships in the database
    stored = 0
    for disc in discoveries:
        # Check if relationship already exists
        existing = await db.execute(
            select(MetaRelationship).where(
                and_(
                    MetaRelationship.source_keyword == disc.source_keyword,
                    MetaRelationship.related_keyword == disc.related_keyword,
                )
            )
        )

        if not existing.scalar():
            new_rel = MetaRelationship(
                source_keyword=disc.source_keyword,
                related_keyword=disc.related_keyword,
                relationship_type=disc.relationship_type,
                confidence_score=disc.confidence,
                discovery_source="social_listening",
            )
            db.add(new_rel)
            stored += 1

    await db.commit()

    return {
        "status": "success",
        "topics_found": len(topics),
        "relationships_discovered": len(discoveries),
        "new_relationships_stored": stored,
    }
