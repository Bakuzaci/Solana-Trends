"""Tests for API endpoints."""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns status."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "app" in data
        assert "version" in data
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "moralis_configured" in data


class TestTrendsAPI:
    """Test trends API endpoints."""

    async def test_get_trends_empty(self, client: AsyncClient):
        """Test getting trends when database is empty."""
        response = await client.get("/api/trends")  # No trailing slash
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_trends_with_params(self, client: AsyncClient):
        """Test getting trends with query parameters."""
        response = await client.get("/api/trends?min_coin_count=5&time_window=24h")  # No trailing slash
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAccelerationAPI:
    """Test acceleration API endpoints."""
    
    async def test_get_top_acceleration(self, client: AsyncClient):
        """Test getting top accelerating trends."""
        response = await client.get("/api/acceleration/top")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_top_acceleration_with_limit(self, client: AsyncClient):
        """Test getting top accelerating trends with limit."""
        response = await client.get("/api/acceleration/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestHistoryAPI:
    """Test history API endpoints."""
    
    async def test_get_history_nonexistent(self, client: AsyncClient):
        """Test getting history for non-existent category."""
        response = await client.get("/api/history/NonExistent/test")
        # Should return empty list or 404
        assert response.status_code in [200, 404]
