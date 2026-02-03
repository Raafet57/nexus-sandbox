"""
Bank to Customer Debit/Credit Notification (camt.054) for Reconciliation

Reference: NotebookLM query 2026-02-03

Purpose: Allows IPS Operators to reconcile transactions with Nexus
Version: camt.054.001.11
Frequency: Daily (configurable) or on-demand via API
Content: All transactions with final status (ACCC, BLCK, RJCT) in period
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from ..db import get_db

router = APIRouter(prefix="/v1/reconciliation", tags=["Reconciliation"])


# =============================================================================
# Pydantic Models for camt.054 Response
# =============================================================================

class TransactionEntry(BaseModel):
    """Individual transaction entry in camt.054."""
    messageId: str
    instructionId: str
    uetr: str
    clearingSystemRef: str
    nexusFxQuoteId: Optional[str] = None
    transactionStatus: str  # ACCC, BLCK, RJCT
    statusReasonCode: Optional[str] = None
    debtorName: str
    debtorAgent: str  # BIC
    creditorName: str
    creditorAgent: str  # BIC
    amount: str
    currency: str
    transactionDateTime: str


class TransactionSummary(BaseModel):
    """Summary of transactions in the report."""
    totalCount: int
    totalAmount: str
    currency: str
    netDebitCredit: str  # DBIT or CRDT
    successCount: int
    rejectedCount: int
    blockedCount: int


class Camt054Response(BaseModel):
    """camt.054 Bank to Customer Debit/Credit Notification."""
    messageId: str
    creationDateTime: str
    periodStart: str
    periodEnd: str
    ipsOperatorId: str
    summary: TransactionSummary
    entries: list[TransactionEntry]


# =============================================================================
# GET /reconciliation/camt054 - Generate Reconciliation Report
# =============================================================================

@router.get(
    "/camt054",
    response_model=Camt054Response,
    summary="Generate camt.054 reconciliation report",
    description="""
    **IPS Reconciliation Report**
    
    Generates a camt.054.001.11 Bank to Customer Debit/Credit Notification
    for an IPS Operator to reconcile their transactions with Nexus.
    
    ## Report Contents (NotebookLM confirmed)
    
    - **Summary**: Total count, total amount, net debit/credit
    - **Entries**: All transactions with final status in period
    - **IDs**: Message ID, Instruction ID, UETR, Clearing System Ref, FX Quote ID
    - **Parties**: Debtor/Creditor names and agents (BIC)
    
    ## Filters
    
    - **period_start/period_end**: Custom date range (ISO 8601)
    - **status**: Filter by status (ACCC, BLCK, RJCT, or ALL)
    - Default: Last 24 hours, ALL statuses
    
    ## Frequency Options
    
    - **Daily**: Auto-generated at IPS-configured time
    - **On-demand**: Call this API for custom period
    
    Reference: https://docs.nexusglobalpayments.org/settlement-access-provision/reconciliation
    """
)
async def generate_camt054(
    ips_operator_id: str = Query(..., alias="ipsOperatorId", description="IPS Operator ID"),
    period_start: Optional[str] = Query(None, alias="periodStart", description="Period start (ISO 8601)"),
    period_end: Optional[str] = Query(None, alias="periodEnd", description="Period end (ISO 8601)"),
    status: str = Query("ALL", description="Filter by status: ACCC, BLCK, RJCT, or ALL"),
    db: AsyncSession = Depends(get_db)
) -> Camt054Response:
    """Generate camt.054 reconciliation report."""
    now = datetime.now(timezone.utc)
    
    # Default period: last 24 hours
    if not period_end:
        end_dt = now
    else:
        end_dt = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
    
    if not period_start:
        start_dt = end_dt - timedelta(hours=24)
    else:
        start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
    
    # For sandbox: generate example data
    # Production would query payments table with status filter
    example_entries = [
        TransactionEntry(
            messageId="MSG202602030001",
            instructionId="INS202602030001",
            uetr="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            clearingSystemRef="NEXUS202602030001",
            nexusFxQuoteId="QUOTE-SGD-THB-001",
            transactionStatus="ACCC",
            statusReasonCode=None,
            debtorName="John Sender",
            debtorAgent="DBSSSGSG",
            creditorName="Somchai Recipient",
            creditorAgent="KASITHBK",
            amount="1000.00",
            currency="SGD",
            transactionDateTime=(now - timedelta(hours=2)).isoformat()
        ),
        TransactionEntry(
            messageId="MSG202602030002",
            instructionId="INS202602030002",
            uetr="a47bc20c-58cc-4372-b567-1f02b2c3d480",
            clearingSystemRef="NEXUS202602030002",
            nexusFxQuoteId="QUOTE-SGD-MYR-001",
            transactionStatus="ACCC",
            statusReasonCode=None,
            debtorName="Jane Sender",
            debtorAgent="OCBCSGSG",
            creditorName="Ahmad Recipient",
            creditorAgent="MABORBB",
            amount="500.00",
            currency="SGD",
            transactionDateTime=(now - timedelta(hours=5)).isoformat()
        ),
        TransactionEntry(
            messageId="MSG202602030003",
            instructionId="INS202602030003",
            uetr="b48cd30d-68dd-5483-c678-2g13c3d4e581",
            clearingSystemRef="NEXUS202602030003",
            nexusFxQuoteId="QUOTE-SGD-PHP-001",
            transactionStatus="RJCT",
            statusReasonCode="AC04",  # Closed Account
            debtorName="Mike Sender",
            debtorAgent="UOVSSGSG",
            creditorName="Maria Recipient",
            creditorAgent="BDOEPHM1",
            amount="200.00",
            currency="SGD",
            transactionDateTime=(now - timedelta(hours=8)).isoformat()
        ),
    ]
    
    # Filter by status if specified
    if status != "ALL":
        example_entries = [e for e in example_entries if e.transactionStatus == status]
    
    # Calculate summary
    success_count = sum(1 for e in example_entries if e.transactionStatus == "ACCC")
    rejected_count = sum(1 for e in example_entries if e.transactionStatus == "RJCT")
    blocked_count = sum(1 for e in example_entries if e.transactionStatus == "BLCK")
    
    total_amount = sum(float(e.amount) for e in example_entries)
    
    return Camt054Response(
        messageId=f"CAMT054-{ips_operator_id}-{now.strftime('%Y%m%d%H%M%S')}",
        creationDateTime=now.isoformat(),
        periodStart=start_dt.isoformat(),
        periodEnd=end_dt.isoformat(),
        ipsOperatorId=ips_operator_id,
        summary=TransactionSummary(
            totalCount=len(example_entries),
            totalAmount=f"{total_amount:.2f}",
            currency="SGD",
            netDebitCredit="DBIT" if total_amount > 0 else "CRDT",
            successCount=success_count,
            rejectedCount=rejected_count,
            blockedCount=blocked_count
        ),
        entries=example_entries
    )


# =============================================================================
# GET /reconciliation/summary - Quick Summary
# =============================================================================

@router.get(
    "/summary",
    summary="Get reconciliation summary",
    description="""
    Quick summary of transaction statuses without full entries.
    Useful for dashboards and monitoring.
    """
)
async def get_reconciliation_summary(
    ips_operator_id: str = Query(..., alias="ipsOperatorId"),
    period_hours: int = Query(24, alias="periodHours", ge=1, le=168),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get quick reconciliation summary."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(hours=period_hours)
    
    # For sandbox: return example summary
    return {
        "ipsOperatorId": ips_operator_id,
        "periodStart": period_start.isoformat(),
        "periodEnd": now.isoformat(),
        "periodHours": period_hours,
        "counts": {
            "total": 127,
            "successful": 118,
            "rejected": 7,
            "blocked": 2
        },
        "amounts": {
            "totalProcessed": "1250000.00",
            "successful": "1180000.00",
            "rejected": "65000.00",
            "blocked": "5000.00",
            "currency": "SGD"
        },
        "successRate": "92.9%"
    }
