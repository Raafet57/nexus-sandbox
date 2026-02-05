"""
Pytest configuration and fixtures for Nexus Gateway tests.

This module provides shared fixtures for testing the Nexus Gateway API.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def mock_db_result():
    """Create a mock database result with fetchone/fetchall methods."""
    def _create(row_data: dict | None = None, rows: list | None = None):
        result = MagicMock()
        
        if row_data:
            row = MagicMock()
            for key, value in row_data.items():
                setattr(row, key, value)
            result.fetchone.return_value = row
        else:
            result.fetchone.return_value = None
            
        if rows:
            result.fetchall.return_value = rows
        else:
            result.fetchall.return_value = []
            
        return result
    return _create


@pytest.fixture
def mock_db_session(mock_db_result):
    """Create a mock database session for unit tests."""
    session = AsyncMock()
    # Default: return empty result
    session.execute.return_value = mock_db_result()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def override_get_db(mock_db_session):
    """Override the database dependency with mock."""
    async def _override():
        yield mock_db_session
    return _override


# =============================================================================
# Client Fixtures (No DB required)
# =============================================================================

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client that bypasses DB connection."""
    # Import app without triggering lifespan
    from src.main import app
    
    # Patch the database lifespan to avoid connection
    with patch('src.db.Database.connect', new_callable=AsyncMock):
        with patch('src.db.Database.disconnect', new_callable=AsyncMock):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as ac:
                yield ac


# =============================================================================
# Mock Data Fixtures
# =============================================================================

@pytest.fixture
def sample_pacs008() -> dict:
    """Sample pacs.008 payment instruction."""
    return {
        "uetr": "550e8400-e29b-41d4-a716-446655440000",
        "messageId": "MSG-2026-02-03-001",
        "creationDateTime": "2026-02-03T01:00:00Z",
        "settlementMethod": "CLRG",
        "instructingAgent": {"bic": "DBSSSGSG"},
        "instructedAgent": {"bic": "NEXUSNEX"},
        "debtorName": "John Tan",
        "debtorAccount": "1234567890",
        "creditorName": "Maria Santos",
        "creditorAccount": "0987654321",
        "instructedAmount": {"amount": "1000.00", "currency": "SGD"},
        "interbankSettlementAmount": {"amount": "980.00", "currency": "SGD"},
        "instructionPriority": "NORM",
    }


@pytest.fixture
def sample_pacs002_accc() -> dict:
    """Sample pacs.002 acceptance confirmation."""
    return {
        "uetr": "550e8400-e29b-41d4-a716-446655440000",
        "transactionStatus": "ACCC",
        "acceptanceDatetime": "2026-02-03T01:00:05Z",
    }


@pytest.fixture
def sample_pacs002_rjct() -> dict:
    """Sample pacs.002 rejection."""
    return {
        "uetr": "550e8400-e29b-41d4-a716-446655440000",
        "transactionStatus": "RJCT",
        "statusReasonCode": "AC04",
        "statusReasonText": "Closed Account Number",
        "acceptanceDatetime": "2026-02-03T01:00:05Z",
    }


@pytest.fixture
def sample_acmt023() -> dict:
    """Sample acmt.023 proxy lookup request."""
    return {
        "proxyType": "MOBI",
        "proxyValue": "+6591234567",
        "destinationCountry": "SG",
    }


@pytest.fixture
def sample_camt056() -> dict:
    """Sample camt.056 recall request."""
    return {
        "originalUetr": "550e8400-e29b-41d4-a716-446655440000",
        "cancellationReasonCode": "DUPL",
        "cancellationReasonText": "Duplicate payment",
        "requestedBy": "DBSSSGSG",
        "recallType": "FULL",
    }


@pytest.fixture
def sample_quote_response() -> dict:
    """Sample quote response."""
    return {
        "quotes": [
            {
                "quoteId": "quote-001",
                "fxpId": "FXP-001",
                "fxpName": "Test FXP",
                "exchangeRate": "26.50000000",
                "sourceInterbankAmount": "1000.00",
                "destinationInterbankAmount": "26500.00",
                "cappedToMaxAmount": False,
                "expiresAt": "2026-02-03T01:10:00Z",
            }
        ]
    }
