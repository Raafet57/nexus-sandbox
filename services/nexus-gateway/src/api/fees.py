"""
Fees and Amounts API endpoints.

Reference: https://docs.nexusglobalpayments.org/apis/fees-and-amounts

This endpoint helps PSPs calculate the final amounts for a payment,
including all fees that will be deducted.
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db


router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class FeeBreakdown(BaseModel):
    """
    Detailed fee breakdown for a payment.
    
    Reference: https://docs.nexusglobalpayments.org/apis/fees-and-amounts
    """
    source_psp_fee: str | None = Field(alias="sourcePspFee", default=None)
    destination_psp_fee: str | None = Field(alias="destinationPspFee", default=None)
    fx_spread: str | None = Field(alias="fxSpread", default=None)
    total_fees: str = Field(alias="totalFees")
    
    class Config:
        populate_by_name = True


class AmountCalculation(BaseModel):
    """Amount calculation including fees."""
    sender_amount: str = Field(alias="senderAmount")
    interbank_settlement_amount: str = Field(alias="interbankSettlementAmount")
    creditor_amount: str = Field(alias="creditorAmount")
    fees: FeeBreakdown
    
    class Config:
        populate_by_name = True


class FeesAndAmountsResponse(BaseModel):
    """Response from GET /fees-and-amounts."""
    source_currency: str = Field(alias="sourceCurrency")
    destination_currency: str = Field(alias="destinationCurrency")
    exchange_rate: str = Field(alias="exchangeRate")
    calculation: AmountCalculation
    
    class Config:
        populate_by_name = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/fees-and-amounts",
    response_model=FeesAndAmountsResponse,
    summary="Calculate Fees and Amounts",
    description="""
    Calculate fees and final amounts for a payment.
    
    Reference: https://docs.nexusglobalpayments.org/apis/fees-and-amounts
    
    This endpoint provides a complete breakdown of:
    - Sender's total payment
    - Interbank settlement amount
    - Final creditor (recipient) amount
    - All applicable fees
    
    ## Fee Types
    
    1. **Source PSP Fee**: Fee charged by the sending bank
    2. **Destination PSP Fee**: Fee charged by the receiving bank (deducted from creditor amount)
    3. **FX Spread**: Implicit cost in the exchange rate
    
    ## Amount Type
    
    - **SOURCE**: Sender specifies how much they want to send
    - **DESTINATION**: Sender specifies how much recipient should receive
    """,
)
async def calculate_fees_and_amounts(
    quote_id: str = Query(
        ...,
        alias="quoteId",
        description="Quote ID from /quotes endpoint",
    ),
    source_psp_bic: str | None = Query(
        None,
        alias="sourcePspBic",
        description="BIC of the source PSP (to lookup fees)",
    ),
    destination_psp_bic: str | None = Query(
        None,
        alias="destinationPspBic",
        description="BIC of the destination PSP (to lookup fees)",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Calculate fees and amounts for a payment."""
    
    # Get quote details
    quote_query = text("""
        SELECT 
            q.quote_id,
            q.source_currency,
            q.destination_currency,
            q.final_rate,
            q.source_interbank_amount,
            q.destination_interbank_amount,
            q.expires_at,
            q.status,
            f.base_spread_bps
        FROM quotes q
        JOIN fxps f ON q.fxp_id = f.fxp_id
        WHERE q.quote_id = :quote_id::uuid
    """)
    
    result = await db.execute(quote_query, {"quote_id": quote_id})
    quote = result.fetchone()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status != "ACTIVE":
        raise HTTPException(status_code=410, detail="Quote is no longer active")
    
    # Get PSP fees
    source_fee_percent = Decimal("0")
    dest_fee_percent = Decimal("0")
    
    if source_psp_bic:
        psp_query = text("""
            SELECT fee_percent FROM psps WHERE bic = :bic
        """)
        result = await db.execute(psp_query, {"bic": source_psp_bic.upper()})
        psp = result.fetchone()
        if psp:
            source_fee_percent = Decimal(str(psp.fee_percent))
    
    if destination_psp_bic:
        psp_query = text("""
            SELECT fee_percent FROM psps WHERE bic = :bic
        """)
        result = await db.execute(psp_query, {"bic": destination_psp_bic.upper()})
        psp = result.fetchone()
        if psp:
            dest_fee_percent = Decimal(str(psp.fee_percent))
    
    # Calculate amounts
    interbank_source = Decimal(str(quote.source_interbank_amount))
    interbank_dest = Decimal(str(quote.destination_interbank_amount))
    
    # Source PSP fee (added to sender's payment)
    source_psp_fee = (interbank_source * source_fee_percent).quantize(Decimal("0.01"))
    sender_amount = interbank_source + source_psp_fee
    
    # Destination PSP fee (deducted from creditor amount)
    dest_psp_fee = (interbank_dest * dest_fee_percent).quantize(Decimal("0.01"))
    creditor_amount = interbank_dest - dest_psp_fee
    
    # FX spread (informational only - already baked into rate)
    # Reference: https://docs.nexusglobalpayments.org/fx-provision/rates-from-third-party-fx-providers
    spread_bps = quote.base_spread_bps
    fx_spread = (interbank_source * Decimal(spread_bps) / Decimal(10000)).quantize(Decimal("0.01"))
    
    # Total fees (visible to sender)
    total_fees = source_psp_fee + fx_spread
    
    return {
        "sourceCurrency": quote.source_currency,
        "destinationCurrency": quote.destination_currency,
        "exchangeRate": str(quote.final_rate),
        "calculation": {
            "senderAmount": str(sender_amount),
            "interbankSettlementAmount": str(interbank_source),
            "creditorAmount": str(creditor_amount),
            "fees": {
                "sourcePspFee": str(source_psp_fee) if source_psp_fee > 0 else None,
                "destinationPspFee": str(dest_psp_fee) if dest_psp_fee > 0 else None,
                "fxSpread": str(fx_spread) if fx_spread > 0 else None,
                "totalFees": str(total_fees),
            }
        }
    }
