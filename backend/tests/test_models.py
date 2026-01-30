"""Tests for database models."""
import pytest
from datetime import datetime, timezone
from app.models import Token, Snapshot, TrendAggregate


class TestTokenModel:
    """Test the Token model."""

    async def test_create_token(self, test_db_session):
        """Test creating a token."""
        token = Token(
            token_address="test_address_123",
            name="Test Token",
            symbol="TEST",
            created_at=datetime.utcnow(),
            primary_category="Technology",
            sub_category="AI & Bots",
        )
        test_db_session.add(token)
        await test_db_session.commit()
        await test_db_session.refresh(token)

        assert token.id is not None
        assert token.token_address == "test_address_123"
        assert token.name == "Test Token"
        assert token.symbol == "TEST"
        assert token.primary_category == "Technology"

    async def test_token_unique_address(self, test_db_session):
        """Test that token addresses must be unique."""
        token1 = Token(
            token_address="unique_address",
            name="Token 1",
            symbol="TK1",
            created_at=datetime.utcnow(),
            primary_category="Technology",
            sub_category="AI & Bots",
        )
        test_db_session.add(token1)
        await test_db_session.commit()

        # Try to create another token with the same address
        token2 = Token(
            token_address="unique_address",
            name="Token 2",
            symbol="TK2",
            created_at=datetime.utcnow(),
            primary_category="Finance",
            sub_category="DeFi",
        )
        test_db_session.add(token2)

        with pytest.raises(Exception):
            await test_db_session.commit()


class TestSnapshotModel:
    """Test the Snapshot model."""

    async def test_create_snapshot(self, test_db_session):
        """Test creating a snapshot."""
        # First create a token since snapshot has a foreign key
        token = Token(
            token_address="test_snapshot_addr",
            name="Test Token",
            symbol="TST",
            created_at=datetime.utcnow(),
        )
        test_db_session.add(token)
        await test_db_session.commit()

        snapshot = Snapshot(
            token_address="test_snapshot_addr",
            market_cap_usd=1000000.0,
            liquidity_usd=50000.0,
            price_usd=1.5,
        )
        test_db_session.add(snapshot)
        await test_db_session.commit()
        await test_db_session.refresh(snapshot)

        assert snapshot.id is not None
        assert snapshot.token_address == "test_snapshot_addr"
        assert snapshot.snapshot_time is not None


class TestTrendAggregateModel:
    """Test the TrendAggregate model."""

    async def test_create_trend_aggregate(self, test_db_session):
        """Test creating a trend aggregate."""
        trend = TrendAggregate(
            snapshot_time=datetime.utcnow(),
            category="Animals",
            sub_category="Dogs",
            time_window="24h",
            coin_count=25,
            total_market_cap=5000000.0,
            avg_market_cap=200000.0,
            acceleration_score=75.5,
        )
        test_db_session.add(trend)
        await test_db_session.commit()
        await test_db_session.refresh(trend)

        assert trend.id is not None
        assert trend.category == "Animals"
        assert trend.sub_category == "Dogs"
        assert trend.coin_count == 25
        assert trend.acceleration_score == 75.5
