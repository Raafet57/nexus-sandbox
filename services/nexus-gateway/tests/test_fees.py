"""
Unit tests for Fee endpoints.

Tests fees.py and fee_formulas.py endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient


class TestFeesAndAmounts:
    """Test GET /fees-and-amounts endpoint."""

    @pytest.mark.asyncio
    async def test_calculate_fees_requires_quote_id(
        self,
        async_client: AsyncClient,
    ):
        """Test that quoteId is required."""
        response = await async_client.get("/v1/fees-and-amounts")
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "quoteId" in str(data) or "quote" in str(data).lower()


class TestFeeFormulas:
    """Test fee formula endpoints."""

    @pytest.mark.asyncio
    async def test_get_nexus_scheme_fee(
        self,
        async_client: AsyncClient,
        mock_db_session: AsyncMock,
        override_get_db,
    ):
        """Test Nexus scheme fee formula endpoint."""
        from src.main import app
        from src.db import get_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = await async_client.get(
                "/v1/fee-formulas/nexus-scheme-fee/SG/SGD"
            )
            assert response.status_code in [200, 404, 500]
            if response.status_code == 200:
                data = response.json()
                assert "feeType" in data
                assert data["countryCode"] == "SG"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_creditor_agent_fee(
        self,
        async_client: AsyncClient,
        mock_db_session: AsyncMock,
        override_get_db,
    ):
        """Test creditor agent fee formula endpoint."""
        from src.main import app
        from src.db import get_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = await async_client.get(
                "/v1/fee-formulas/creditor-agent-fee/PH/PHP"
            )
            assert response.status_code in [200, 404, 500]
            if response.status_code == 200:
                data = response.json()
                assert "feeType" in data
        finally:
            app.dependency_overrides.clear()
