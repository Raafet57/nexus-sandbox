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
from pydantic import BaseModel
from ..db import get_db

router = APIRouter(prefix="/v1", tags=["Reference Data"])


class CurrencyResponse(BaseModel):
    """Currency details response."""
    currencyCode: str
    currencyName: str
    decimalPlaces: int
    countries: list[str]
    isActive: bool


class CurrenciesListResponse(BaseModel):
    """List of currencies."""
    currencies: list[CurrencyResponse]


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
            c.currency_name,
            c.decimal_places,
            c.is_active,
            COALESCE(
                array_agg(DISTINCT cc.country_code) FILTER (WHERE cc.country_code IS NOT NULL),
                ARRAY[]::text[]
            ) as countries
        FROM currencies c
        LEFT JOIN country_currencies cc ON c.currency_code = cc.currency_code
        GROUP BY c.currency_code, c.currency_name, c.decimal_places, c.is_active
        ORDER BY c.currency_code
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    currencies = []
    for row in rows:
        currencies.append(CurrencyResponse(
            currencyCode=row.currency_code,
            currencyName=row.currency_name,
            decimalPlaces=row.decimal_places,
            countries=list(row.countries) if row.countries else [],
            isActive=row.is_active
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
            c.currency_name,
            c.decimal_places,
            c.is_active,
            COALESCE(
                array_agg(DISTINCT cc.country_code) FILTER (WHERE cc.country_code IS NOT NULL),
                ARRAY[]::text[]
            ) as countries
        FROM currencies c
        LEFT JOIN country_currencies cc ON c.currency_code = cc.currency_code
        WHERE c.currency_code = :currency_code
        GROUP BY c.currency_code, c.currency_name, c.decimal_places, c.is_active
    """)
    
    result = await db.execute(query, {"currency_code": currency_code.upper()})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Currency {currency_code} not found"
        )
    
    return CurrencyResponse(
        currencyCode=row.currency_code,
        currencyName=row.currency_name,
        decimalPlaces=row.decimal_places,
        countries=list(row.countries) if row.countries else [],
        isActive=row.is_active
    )


@router.get(
    "/countries/{country_code}/currencies/{currency_code}/max-amounts",
    summary="Get maximum payment amount",
    description="""
    Returns the maximum payment amount permitted for a specific 
    country and currency combination.
    
    Reference: https://docs.nexusglobalpayments.org/fx-provision/maximum-value-of-a-nexus-payment
    
    The maximum is the LESSER of:
    - Country-specific maximum (from IPS limits)
    - Currency-specific maximum (from IPS limits)
    - Nexus scheme maximum
    """
)
async def get_max_amounts(
    country_code: str,
    currency_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the maximum amount for a country/currency pair.
    
    This is critical for the Source PSP to validate amounts
    BEFORE attempting a payment.
    """
    query = text("""
        SELECT 
            cc.country_code,
            cc.currency_code,
            cc.max_amount_source,
            cc.max_amount_destination,
            co.country_name,
            cu.currency_name
        FROM country_currencies cc
        JOIN countries co ON cc.country_code = co.country_code
        JOIN currencies cu ON cc.currency_code = cu.currency_code
        WHERE cc.country_code = :country_code 
          AND cc.currency_code = :currency_code
    """)
    
    result = await db.execute(query, {
        "country_code": country_code.upper(),
        "currency_code": currency_code.upper()
    })
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No configuration found for {country_code}/{currency_code}"
        )
    
    return {
        "countryCode": row.country_code,
        "countryName": row.country_name,
        "currencyCode": row.currency_code,
        "currencyName": row.currency_name,
        "maxAmountAsSource": str(row.max_amount_source),
        "maxAmountAsDestination": str(row.max_amount_destination),
        "reference": "https://docs.nexusglobalpayments.org/fx-provision/maximum-value-of-a-nexus-payment"
    }
