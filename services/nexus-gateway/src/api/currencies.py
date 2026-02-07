"""
Currencies API Endpoints

Reference: https://docs.nexusglobalpayments.org/apis/currencies

Provides currency reference data for Nexus payments including
decimal places, associated countries, and currency metadata.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from ..db import get_db

router = APIRouter(prefix="/v1", tags=["Reference Data"])


from .schemas import CurrencyResponse, CurrenciesListResponse


@router.get(
    "/currencies",
    response_model=CurrenciesListResponse,
    summary="List all currencies",
    description="""
    Returns all currencies available on the Nexus network.
    
    Reference: https://docs.nexusglobalpayments.org/apis/currencies
    """
)
async def list_currencies(
    db: AsyncSession = Depends(get_db)
) -> CurrenciesListResponse:
    """
    Get all currencies with their associated countries.
    
    Used by Source PSP to display available currencies for payments.
    """
    query = text("""
        SELECT 
            c.currency_code,
            c.name,
            c.decimal_places,
            COALESCE(
                array_agg(DISTINCT cc.country_code) FILTER (WHERE cc.country_code IS NOT NULL),
                ARRAY[]::text[]
            ) as countries
        FROM currencies c
        LEFT JOIN country_currencies cc ON c.currency_code = cc.currency_code
        GROUP BY c.currency_code, c.name, c.decimal_places
        ORDER BY c.currency_code
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    currencies = []
    for row in rows:
        currencies.append(CurrencyResponse(
            code=row.currency_code,
            name=row.name,
            fractional_digits=row.decimal_places,
            is_active=True
        ))
    
    return CurrenciesListResponse(currencies=currencies)


@router.get(
    "/currencies/{currency_code}",
    response_model=CurrencyResponse,
    summary="Get currency details",
    description="""
    Returns details for a specific currency.
    
    Reference: https://docs.nexusglobalpayments.org/apis/currencies
    """
)
async def get_currency(
    currency_code: str,
    db: AsyncSession = Depends(get_db)
) -> CurrencyResponse:
    """
    Get details for a single currency by its 3-letter code.
    """
    query = text("""
        SELECT 
            c.currency_code,
            c.name,
            c.decimal_places
        FROM currencies c
        WHERE c.currency_code = :currency_code
    """)
    
    result = await db.execute(query, {"currency_code": currency_code.upper()})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Currency {currency_code} not found"
        )
    
    return CurrencyResponse(
        code=row.currency_code,
        name=row.name,
        fractional_digits=row.decimal_places,
        is_active=True
    )
