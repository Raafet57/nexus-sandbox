"""
Fee Formulas API Endpoints

Reference: https://docs.nexusglobalpayments.org/fees-and-pricing/source-psp-fees

Critical for Nexus fee transparency requirements:
- Sender must see EXACT fees before authorizing
- Source PSP fees can be invoiced OR deducted
- Destination PSP fees MUST be deducted from principal
- FX spread built into rate (no separate charge)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import BaseModel
from ..db import get_db

router = APIRouter(prefix="/v1", tags=["Fees"])


class FeeFormulaResponse(BaseModel):
    """Fee formula definition."""
    feeType: str
    countryCode: str
    currencyCode: str
    fixedAmount: str
    percentageRate: str
    minimumFee: str
    maximumFee: str
    description: str


class PreTransactionDisclosure(BaseModel):
    """
    Pre-transaction fee disclosure per Nexus requirements.
    
    Reference: https://docs.nexusglobalpayments.org/fees-and-pricing/fx-spread-transparency
    
    This MUST be shown to sender before authorization.
    """
    # Quote reference
    quoteId: str
    exchangeRate: str
    quoteValidUntil: str
    
    # Sender sees these amounts
    amountToDebit: str
    amountToDebitCurrency: str
    amountToCredit: str
    amountToCreditCurrency: str
    
    # Fee breakdown (transparency)
    sourcePspFee: str
    sourcePspFeeCurrency: str
    sourcePspFeeType: str  # INVOICED or DEDUCTED
    
    destinationPspFee: str
    destinationPspFeeCurrency: str
    
    fxSpreadBps: str  # Basis points of spread
    
    # Nexus scheme fee (informational - invoiced to IPS)
    nexusSchemeFee: str
    nexusSchemeFeeCurrency: str
    
    # Display options
    effectiveExchangeRate: str  # Total debit / Total credit
    definedExchangeRate: str    # Rate applied to principal


@router.get(
    "/fee-formulas/nexus-scheme-fee/{country_code}/{currency_code}",
    response_model=FeeFormulaResponse,
    summary="Get Nexus Scheme Fee formula",
    description="""
    Returns the Nexus Scheme Fee formula for a country/currency.
    
    The Nexus Scheme Fee is:
    - Charged to the Source IPS (passed to Source PSP)
    - INVOICED (not deducted from payment)
    - Denominated in Source Currency
    
    Reference: https://docs.nexusglobalpayments.org/fees-and-pricing/nexus-scheme-fee
    """
)
async def get_nexus_scheme_fee(
    country_code: str,
    currency_code: str,
    db: AsyncSession = Depends(get_db)
) -> FeeFormulaResponse:
    """
    Get Nexus scheme fee formula.
    
    Note: For sandbox, using simplified flat fee model.
    Production would have tiered pricing.
    """
    # Sandbox: Simplified fee structure
    # Real implementation would query fee_formulas table
    
    return FeeFormulaResponse(
        feeType="NEXUS_SCHEME_FEE",
        countryCode=country_code.upper(),
        currencyCode=currency_code.upper(),
        fixedAmount="0.50",  # Example: 0.50 per transaction
        percentageRate="0.0005",  # 0.05% = 5 basis points
        minimumFee="0.50",
        maximumFee="10.00",
        description="Nexus Scheme Fee - invoiced to Source IPS monthly"
    )


@router.get(
    "/fee-formulas/creditor-agent-fee/{country_code}/{currency_code}",
    response_model=FeeFormulaResponse,
    summary="Get Creditor Agent Fee formula",
    description="""
    Returns the Destination PSP (Creditor Agent) fee formula.
    
    This fee:
    - MUST be deducted from the payment principal
    - Is denominated in Destination Currency
    - Set by scheme, not individual PSPs
    
    Reference: https://docs.nexusglobalpayments.org/fees-and-pricing/destination-psp-fees
    """
)
async def get_creditor_agent_fee(
    country_code: str,
    currency_code: str,
    db: AsyncSession = Depends(get_db)
) -> FeeFormulaResponse:
    """
    Get destination PSP fee formula.
    
    Important: Destination PSPs cannot charge additional invoiced fees.
    """
    # Fee structures vary by country - sandbox uses simplified model
    fee_structures = {
        "SG": {"fixed": "0.50", "percent": "0.001", "min": "0.50", "max": "5.00"},
        "TH": {"fixed": "10.00", "percent": "0.001", "min": "10.00", "max": "100.00"},  # In THB
        "MY": {"fixed": "1.00", "percent": "0.001", "min": "1.00", "max": "10.00"},
        "PH": {"fixed": "25.00", "percent": "0.001", "min": "25.00", "max": "250.00"},  # In PHP
        "ID": {"fixed": "5000", "percent": "0.001", "min": "5000", "max": "50000"},  # In IDR
        "IN": {"fixed": "25.00", "percent": "0.001", "min": "25.00", "max": "250.00"},  # In INR
    }
    
    structure = fee_structures.get(country_code.upper(), {
        "fixed": "1.00",
        "percent": "0.001",
        "min": "1.00",
        "max": "10.00"
    })
    
    return FeeFormulaResponse(
        feeType="CREDITOR_AGENT_FEE",
        countryCode=country_code.upper(),
        currencyCode=currency_code.upper(),
        fixedAmount=structure["fixed"],
        percentageRate=structure["percent"],
        minimumFee=structure["min"],
        maximumFee=structure["max"],
        description="Destination PSP Fee - deducted from payment principal"
    )


@router.get(
    "/pre-transaction-disclosure",
    response_model=PreTransactionDisclosure,
    summary="Get pre-transaction disclosure (CRITICAL)",
    description="""
    **CRITICAL FOR NEXUS COMPLIANCE**
    
    Returns the complete fee disclosure that MUST be shown to the
    sender BEFORE they authorize the payment.
    
    Nexus requires transparency:
    - Exact amount to be debited
    - Exact amount to be credited  
    - All fees itemized
    - Exchange rate shown
    
    Reference: https://docs.nexusglobalpayments.org/fees-and-pricing/fx-spread-transparency
    """
)
async def get_pre_transaction_disclosure(
    quote_id: str,
    source_psp_fee: Optional[Decimal] = None,
    source_psp_fee_type: str = "DEDUCTED",  # DEDUCTED or INVOICED
    db: AsyncSession = Depends(get_db)
) -> PreTransactionDisclosure:
    """
    Calculate and return the complete pre-transaction disclosure.
    
    The sender must see this information before authorizing.
    """
    # Get quote details
    # Column names must match the actual database schema in the container
    quote_query = text("""
        SELECT 
            q.quote_id,
            q.source_currency,
            q.destination_currency,
            q.final_rate as exchange_rate,
            q.base_rate,
            q.requested_amount,
            q.source_interbank_amount,
            q.destination_interbank_amount,
            q.creditor_account_amount,
            q.destination_psp_fee,
            q.tier_improvement_bps,
            q.psp_improvement_bps,
            q.capped_to_max_amount,
            q.expires_at as valid_until
        FROM quotes q
        WHERE q.quote_id = :quote_id
          AND q.expires_at > NOW()
    """)
    
    result = await db.execute(quote_query, {"quote_id": quote_id})
    quote = result.fetchone()
    
    if not quote:
        raise HTTPException(
            status_code=404,
            detail=f"Quote {quote_id} not found or expired"
        )
    
    # Calculate all components
    # Map from the row object - handle case where requested_amount might be Source or Destination
    # but for disclosure we want the interbank amounts as well.
    source_amount = Decimal(str(quote.source_interbank_amount))
    dest_amount = Decimal(str(quote.destination_interbank_amount))
    exchange_rate = Decimal(str(quote.exchange_rate))
    
    # 1. Source PSP fee (configurable by PSP)
    # Using 1.00 SGD + 10bps for sandbox demo
    # IMPORTANT: Must calculate on SOURCE amount (SGD), not requested_amount (could be IDR)
    # Will recalculate for DESTINATION type after we know the source_interbank_recalc
    src_psp_fee_base = source_psp_fee  # May be overridden

    
    # 2. Destination PSP fee (scheme-mandated)
    # Mandated formula: fixed + percentage, subject to min/max
    # Logic: max(min_fee, min(max_fee, fixed + percent * principal))
    dest_fee_structs = {
        "SGD": {"fixed": "0.50", "percent": "0.001", "min": "0.50", "max": "5.00"},
        "THB": {"fixed": "10.00", "percent": "0.001", "min": "10.00", "max": "100.00"},
        "MYR": {"fixed": "1.00", "percent": "0.001", "min": "1.00", "max": "10.00"},
        "PHP": {"fixed": "25.00", "percent": "0.002", "min": "25.00", "max": "250.00"},
        # IDR: Scaled realistically - Rp 500 + 0.1%, min Rp 500, max Rp 50,000  
        # (5000 IDR min was 500% of 1000 IDR transfer - way too high)
        "IDR": {"fixed": "500", "percent": "0.001", "min": "500", "max": "50000"},
        "INR": {"fixed": "25.00", "percent": "0.001", "min": "25.00", "max": "250.00"},
    }
    
    struct = dest_fee_structs.get(quote.destination_currency, {"fixed": "1.00", "percent": "0.001", "min": "1.00", "max": "10.00"})
    # dest_psp_fee is calculated inside each amount_type branch below    
    # 3. Nexus scheme fee (invoiced to IPS - 0.50 + 5bps, cap 10.00)
    calc_nexus_fee = Decimal("0.50") + source_amount * Decimal("0.0005")
    nexus_fee = max(Decimal("0.50"), min(Decimal("10.00"), calc_nexus_fee))
    
    # Get amount_type from quote to determine calculation direction
    # Need to query for amount_type
    type_query = text("""
        SELECT amount_type FROM quotes WHERE quote_id = :quote_id
    """)
    type_result = await db.execute(type_query, {"quote_id": quote_id})
    type_row = type_result.fetchone()
    amount_type = type_row.amount_type if type_row else "SOURCE"
    
    # Calculate final amounts based on fee type AND amount_type
    # Per Nexus spec from NotebookLM:
    # - SOURCE: User specifies send amount. Recipient gets (dest_interbank - dest_fee)
    # - DESTINATION: User specifies receive amount. That IS what recipient gets.
    #   We work backwards: dest_interbank = creditor_amount + dest_fee
    
    if amount_type == "DESTINATION":
        # DESTINATION type: dest_amount (destination_interbank from quote) is what user wants recipient to receive
        # For DESTINATION type, the creditor_amount IS the requested amount
        creditor_amount = dest_amount  # This is what recipient gets (1000 IDR)
        
        # Calculate destination fee on CREDITOR amount (what recipient gets), NOT interbank
        # Per Nexus: fee is calculated on the amount being credited
        calc_dest_fee_dest = Decimal(struct["fixed"]) + creditor_amount * Decimal(struct["percent"])
        dest_psp_fee = max(Decimal(struct["min"]), min(Decimal(struct["max"]), calc_dest_fee_dest))
        
        # Interbank = creditor + fee (fee is ADDED, not deducted)
        dest_interbank_recalc = creditor_amount + dest_psp_fee
        
        # Recalculate source amount based on corrected dest interbank
        source_interbank_recalc = dest_interbank_recalc / exchange_rate
        
        # Source PSP fee calculated on SOURCE interbank amount (SGD), not destination
        src_psp_fee = src_psp_fee_base or (Decimal("1.00") + source_interbank_recalc * Decimal("0.001"))
        
        # Source PSP fee added to source amount
        if source_psp_fee_type == "DEDUCTED":
            amount_to_debit = source_interbank_recalc + src_psp_fee
        else:
            amount_to_debit = source_interbank_recalc
        amount_to_credit = creditor_amount  # Exactly what user requested
    else:
        # SOURCE type: source_amount is what user sends
        # Calculate source PSP fee on source amount
        src_psp_fee = src_psp_fee_base or (Decimal("1.00") + source_amount * Decimal("0.001"))
        
        # Destination fee calculated on dest_interbank_amount
        calc_dest_fee_src = Decimal(struct["fixed"]) + dest_amount * Decimal(struct["percent"])
        dest_psp_fee = max(Decimal(struct["min"]), min(Decimal(struct["max"]), calc_dest_fee_src))
        
        # Recipient gets dest_interbank - dest_fee
        if source_psp_fee_type == "DEDUCTED":
            amount_to_debit = source_amount + src_psp_fee
        else:
            amount_to_debit = source_amount
        amount_to_credit = dest_amount - dest_psp_fee
    
    # Effective exchange rate (what sender actually gets)
    effective_rate = amount_to_credit / amount_to_debit if amount_to_debit > 0 else exchange_rate
    
    return PreTransactionDisclosure(
        quoteId=quote_id,
        exchangeRate=str(exchange_rate),
        quoteValidUntil=quote.valid_until.isoformat(),
        
        amountToDebit=str(amount_to_debit.quantize(Decimal("0.01"))),
        amountToDebitCurrency=quote.source_currency,
        amountToCredit=str(amount_to_credit.quantize(Decimal("0.01"))),
        amountToCreditCurrency=quote.destination_currency,
        
        sourcePspFee=str(src_psp_fee),
        sourcePspFeeCurrency=quote.source_currency,
        sourcePspFeeType=source_psp_fee_type,
        
        destinationPspFee=str(dest_psp_fee.quantize(Decimal("0.01"))),
        destinationPspFeeCurrency=quote.destination_currency,
        
        fxSpreadBps=str((quote.tier_improvement_bps or 0) + (quote.psp_improvement_bps or 0)),
        
        nexusSchemeFee=str(nexus_fee.quantize(Decimal("0.01"))),
        nexusSchemeFeeCurrency=quote.source_currency,
        
        effectiveExchangeRate=str(effective_rate.quantize(Decimal("0.000001"))),
        definedExchangeRate=str(exchange_rate)
    )
