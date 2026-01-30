"""
SQLAlchemy database models for TrendRadar.Sol.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Token(Base):
    """
    Token model representing a Solana meme coin.

    Stores metadata about each token including categorization
    and breakout meta detection results.
    """
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_address: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Categorization fields
    primary_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sub_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Breakout meta detection
    is_breakout_meta: Mapped[bool] = mapped_column(Boolean, default=False)
    breakout_meta_cluster: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Graduation status (migrated from PumpFun bonding curve to Raydium LP)
    is_graduated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship to snapshots
    snapshots: Mapped[List["Snapshot"]] = relationship(
        "Snapshot",
        back_populates="token",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Token(symbol={self.symbol}, address={self.token_address[:8]}...)>"


class Snapshot(Base):
    """
    Snapshot model for storing point-in-time market data for tokens.

    Captures market cap, liquidity, and price at regular intervals.
    """
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_address: Mapped[str] = mapped_column(
        Text,
        ForeignKey("tokens.token_address"),
        nullable=False,
        index=True,
    )
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Market data
    market_cap_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    liquidity_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_change_24h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationship to token
    token: Mapped["Token"] = relationship("Token", back_populates="snapshots")

    def __repr__(self) -> str:
        return f"<Snapshot(token={self.token_address[:8]}..., time={self.snapshot_time})>"


class TrendAggregate(Base):
    """
    Aggregated trend data for categories over time windows.

    Stores computed statistics about token categories including
    acceleration scores and breakout meta detection.
    """
    __tablename__ = "trend_aggregates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    category: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_window: Mapped[str] = mapped_column(Text, nullable=False)

    # Aggregate statistics
    coin_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Top coin in category
    top_coin_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    top_coin_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Trend metrics
    acceleration_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_breakout_meta: Mapped[bool] = mapped_column(Boolean, default=False)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            "snapshot_time", "category", "sub_category", "time_window",
            name="uix_trend_aggregate"
        ),
    )

    def __repr__(self) -> str:
        return f"<TrendAggregate(category={self.category}, window={self.time_window})>"
