"""
Unit tests for Health endpoints.

These tests verify the basic health and root endpoints work.
Since the app requires DB at startup, we test in a simplified way.
"""

import pytest


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Test /health endpoint returns OK."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        """Test root endpoint returns API info."""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nexus Global Payments Gateway"
        assert "version" in data
        assert data["status"] == "sandbox"
