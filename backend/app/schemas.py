"""
Pydantic schemas for API request/response models.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# =============================================================================
# Token Schemas
# =============================================================================

class TokenBase(BaseModel):
    """Base token schema with common fields."""
    token_address: str = Field(..., description="Solana token address")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")


class TokenCreate(TokenBase):
    """Schema for creating a new token."""
    created_at: datetime = Field(..., description="Token creation timestamp")
    primary_category: Optional[str] = None
    sub_category: Optional[str] = None
    detected_keywords: Optional[str] = None


class TokenResponse(TokenBase):
    """Schema for token API responses."""
    id: int
    created_at: datetime
    first_seen_at: datetime
    primary_category: Optional[str] = None
    sub_category: Optional[str] = None
    detected_keywords: Optional[str] = None
    is_breakout_meta: bool = False
    breakout_meta_cluster: Optional[str] = None

    class Config:
        from_attributes = True


class CoinResponse(TokenResponse):
    """Extended token response with latest market data."""
    market_cap_usd: Optional[float] = None
    liquidity_usd: Optional[float] = None
    price_usd: Optional[float] = None
    price_change_24h: Optional[float] = None

    class Config:
        from_attributes = True


# =============================================================================
# Snapshot Schemas
# =============================================================================

class SnapshotBase(BaseModel):
    """Base snapshot schema."""
    token_address: str
    market_cap_usd: Optional[float] = None
    liquidity_usd: Optional[float] = None
    price_usd: Optional[float] = None


class SnapshotCreate(SnapshotBase):
    """Schema for creating a new snapshot."""
    snapshot_time: Optional[datetime] = None


class SnapshotResponse(SnapshotBase):
    """Schema for snapshot API responses."""
    id: int
    snapshot_time: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Trend Schemas
# =============================================================================

class TrendAggregateBase(BaseModel):
    """Base trend aggregate schema."""
    category: str = Field(..., description="Primary category name")
    sub_category: Optional[str] = Field(None, description="Sub-category name")
    time_window: str = Field(..., description="Time window (1h, 6h, 24h, 7d)")


class TrendAggregateCreate(TrendAggregateBase):
    """Schema for creating trend aggregates."""
    snapshot_time: datetime
    coin_count: Optional[int] = None
    total_market_cap: Optional[float] = None
    avg_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    top_coin_address: Optional[str] = None
    top_coin_name: Optional[str] = None
    acceleration_score: Optional[float] = None
    is_breakout_meta: bool = False


class TrendResponse(TrendAggregateBase):
    """Schema for trend API responses."""
    id: int
    snapshot_time: datetime
    coin_count: Optional[int] = None
    total_market_cap: Optional[float] = None
    avg_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    top_coin_address: Optional[str] = None
    top_coin_name: Optional[str] = None
    acceleration_score: Optional[float] = None
    is_breakout_meta: bool = False

    class Config:
        from_attributes = True


class TrendSummary(BaseModel):
    """Summary of trends for a category."""
    category: str
    sub_category: Optional[str] = None
    coin_count: int = 0
    total_market_cap: float = 0.0
    acceleration_score: float = 0.0
    is_breakout_meta: bool = False
    top_coins: List[CoinResponse] = []
    trend_direction: str = "stable"  # "up", "down", "stable"

    class Config:
        from_attributes = True


# =============================================================================
# Dashboard Schemas
# =============================================================================

class DashboardStats(BaseModel):
    """Overall dashboard statistics."""
    total_tokens: int = 0
    total_categories: int = 0
    breakout_metas_count: int = 0
    last_update: Optional[datetime] = None


class CategoryTrend(BaseModel):
    """Trend data for a single category."""
    category: str
    sub_category: Optional[str] = None
    coin_count: int = 0
    total_market_cap: float = 0.0
    acceleration_score: float = 0.0
    is_breakout_meta: bool = False
    change_1h: Optional[float] = None
    change_24h: Optional[float] = None


class DashboardResponse(BaseModel):
    """Complete dashboard data response."""
    stats: DashboardStats
    top_trends: List[CategoryTrend] = []
    breakout_metas: List[CategoryTrend] = []
    recent_tokens: List[CoinResponse] = []


# =============================================================================
# API Response Wrappers
# =============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: List = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    message: str
    data: Optional[dict] = None
