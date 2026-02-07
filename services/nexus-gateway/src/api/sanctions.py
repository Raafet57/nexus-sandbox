"""
Sanctions Screening Service (Steps 10-11 of Nexus Payment Flow)

This module implements FATF Recommendation 16 compliant sanctions screening
for cross-border payments as required by the Nexus specification.

Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

from ..db import get_db
from ..models.models import Payment, PaymentEvent
import json

router = APIRouter(prefix="/v1/sanctions", tags=["Sanctions Screening"])


# =============================================================================
# Schemas
# =============================================================================

class ScreeningStatus(str, Enum):
    """Sanctions screening status per FATF R16."""
    PENDING = "PENDING"           # Waiting for required data
    DATA_COMPLETE = "DATA_COMPLETE"  # All required data collected
    SCREENING_PASSED = "SCREENING_PASSED"  # No sanctions hits
    SCREENING_FAILED = "SCREENING_FAILED"  # Sanctions hit detected
    MANUAL_REVIEW = "MANUAL_REVIEW"  # Requires manual review (false positive)


class RequiredDataElement(str, Enum):
    """Required data elements per FATF Recommendation 16."""
    RECIPIENT_NAME = "recipient_name"
    RECIPIENT_ACCOUNT = "recipient_account"
    RECIPIENT_ADDRESS = "recipient_address"
    RECIPIENT_DOB = "recipient_dob"
    RECIPIENT_NATIONAL_ID = "recipient_national_id"
    SENDER_NAME = "sender_name"
    SENDER_ACCOUNT = "sender_account"


class SanctionsDataReviewRequest(BaseModel):
    """Step 10: Review data available for sanctions screening."""
    uetr: str = Field(..., description="Payment UETR")
    recipient_name: Optional[str] = Field(None, description="Recipient full name from acmt.024")
    recipient_account: Optional[str] = Field(None, description="Recipient account/IBAN")
    recipient_address: Optional[str] = Field(None, description="Recipient postal address")
    recipient_dob: Optional[str] = Field(None, description="Recipient date of birth (if available)")
    recipient_national_id: Optional[str] = Field(None, description="National ID (if available)")
    sender_name: str = Field(..., description="Sender/debtor name")
    sender_account: str = Field(..., description="Sender/debtor account")


class SanctionsDataReviewResponse(BaseModel):
    """Step 10 Response: Data completeness assessment."""
    uetr: str
    status: ScreeningStatus
    missing_elements: List[RequiredDataElement]
    warning_message: Optional[str] = None
    can_proceed_to_screening: bool
    fatf_r16_compliant: bool


class SanctionsScreeningRequest(BaseModel):
    """Step 11: Perform sanctions screening."""
    uetr: str = Field(..., description="Payment UETR")
    screening_provider: Optional[str] = Field(None, description="Sanctions screening provider")
    # Optional override for manual review scenarios
    force_pass: bool = Field(False, description="Force pass (for false positive resolution)")


class SanctionsScreeningResponse(BaseModel):
    """Step 11 Response: Screening results."""
    uetr: str
    status: ScreeningStatus
    screening_timestamp: str
    hits_detected: int
    hit_details: Optional[List[dict]] = None
    reason_code: Optional[str] = None
    reason_text: Optional[str] = None
    requires_manual_review: bool
    next_step: str  # "PROCEED" or "BLOCK"


# =============================================================================
# Step 10: Review Data for Sanctions Screening
# =============================================================================

@router.post(
    "/review-data",
    response_model=SanctionsDataReviewResponse,
    summary="Step 10: Review sanctions screening data",
    description="""
    **Step 10 of Nexus Payment Flow**
    
    Reviews the data available for sanctions screening after proxy/account resolution (acmt.024).
    
    Per FATF Recommendation 16, the following information MUST be included for cross-border payments:
    
    **RECIPIENT (Creditor):**
    - Name (mandatory)
    - Account Number (mandatory)
    - At least ONE of: Address, Date/Place of Birth, or National ID
    
    **SENDER (Debtor):**
    - Name (mandatory)
    - Account Number (mandatory)
    
    If the recipient name is blank, the Source PSP MUST ask the Sender for the Recipient's full name.
    
    Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening
    """
)
async def review_sanctions_data(
    request: SanctionsDataReviewRequest,
    db: AsyncSession = Depends(get_db)
) -> SanctionsDataReviewResponse:
    """
    Review data completeness for sanctions screening compliance.
    
    This implements Step 10 of the Nexus payment flow:
    1. Check if recipient name is present
    2. Check if recipient account is present
    3. Check for at least one additional identifier (address, DOB, national ID)
    4. Return list of missing elements if incomplete
    """
    missing_elements = []
    warnings = []
    
    # Check mandatory recipient elements per FATF R16
    if not request.recipient_name or request.recipient_name.strip() == "":
        missing_elements.append(RequiredDataElement.RECIPIENT_NAME)
        warnings.append("Recipient name is mandatory per FATF Recommendation 16")
    
    if not request.recipient_account or request.recipient_account.strip() == "":
        missing_elements.append(RequiredDataElement.RECIPIENT_ACCOUNT)
        warnings.append("Recipient account number is mandatory")
    
    # Check for at least one additional identifier (FATF R16 requires one of these)
    has_additional_id = (
        request.recipient_address or 
        request.recipient_dob or 
        request.recipient_national_id
    )
    
    if not has_additional_id:
        missing_elements.append(RequiredDataElement.RECIPIENT_ADDRESS)
        warnings.append(
            "At least one additional identifier required: Address, Date of Birth, or National ID. "
            "Without this, sanctions screening may trigger false positives."
        )
    
    # Check sender elements (should already be known to Source PSP from KYC)
    if not request.sender_name or request.sender_name.strip() == "":
        missing_elements.append(RequiredDataElement.SENDER_NAME)
    
    if not request.sender_account or request.sender_account.strip() == "":
        missing_elements.append(RequiredDataElement.SENDER_ACCOUNT)
    
    # Determine status
    if len(missing_elements) == 0:
        status = ScreeningStatus.DATA_COMPLETE
        can_proceed = True
        fatf_compliant = True
    elif RequiredDataElement.RECIPIENT_NAME in missing_elements:
        # Cannot proceed without recipient name - this is blocking
        status = ScreeningStatus.PENDING
        can_proceed = False
        fatf_compliant = False
    else:
        # Missing optional elements - can proceed but with warning
        status = ScreeningStatus.DATA_COMPLETE
        can_proceed = True
        fatf_compliant = True
    
    # Store review event
    await _store_screening_event(
        db=db,
        uetr=request.uetr,
        event_type="SANCTIONS_DATA_REVIEW",
        status=status.value,
        details={
            "missing_elements": [e.value for e in missing_elements],
            "warnings": warnings
        }
    )
    
    return SanctionsDataReviewResponse(
        uetr=request.uetr,
        status=status,
        missing_elements=missing_elements,
        warning_message="; ".join(warnings) if warnings else None,
        can_proceed_to_screening=can_proceed,
        fatf_r16_compliant=fatf_compliant
    )


# =============================================================================
# Step 11: Perform Sanctions Screening
# =============================================================================

@router.post(
    "/screen",
    response_model=SanctionsScreeningResponse,
    summary="Step 11: Screen payment against sanctions lists",
    description="""
    **Step 11 of Nexus Payment Flow**
    
    Performs sanctions screening against applicable sanctions lists per jurisdiction.
    
    The Source PSP must screen:
    1. Sender name (already screened during KYC, but may be re-screened)
    2. Recipient name against sanctions lists
    3. Any additional identifiers to resolve false positives
    
    ## Screening Results
    
    | Status | Action |
    |--------|--------|
    | SCREENING_PASSED | Proceed with payment |
    | SCREENING_FAILED | Block payment (RJCT with RR04 reason) |
    | MANUAL_REVIEW | Hold for compliance team review |
    
    Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening
    """
)
async def perform_sanctions_screening(
    request: SanctionsScreeningRequest,
    db: AsyncSession = Depends(get_db)
) -> SanctionsScreeningResponse:
    """
    Perform sanctions screening on payment participants.
    
    In a production environment, this would integrate with:
    - Dow Jones Watchlist
    - Refinitiv World-Check
    - Compliance-wise
    - Or other sanctions screening providers
    
    For sandbox/demo purposes, this simulates the screening workflow.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Simulate screening (in production, call actual screening API)
    # For demo purposes, we'll use deterministic "random" based on UETR
    import hashlib
    hash_val = int(hashlib.md5(request.uetr.encode()).hexdigest(), 16)
    
    if request.force_pass:
        # Manual override for false positive resolution
        status = ScreeningStatus.SCREENING_PASSED
        hits = 0
        reason_code = None
        reason_text = "Manual override - false positive resolved"
        requires_review = False
    elif hash_val % 100 < 95:  # 95% pass rate for demo
        status = ScreeningStatus.SCREENING_PASSED
        hits = 0
        reason_code = None
        reason_text = None
        requires_review = False
    elif hash_val % 100 < 98:  # 3% false positive rate
        status = ScreeningStatus.MANUAL_REVIEW
        hits = 1
        reason_code = "RR04"
        reason_text = "Potential sanctions match - requires manual review"
        requires_review = True
    else:  # 2% true positive rate (for demo)
        status = ScreeningStatus.SCREENING_FAILED
        hits = 1
        reason_code = "RR04"
        reason_text = "Sanctions list match detected - payment blocked"
        requires_review = False
    
    hit_details = []
    if hits > 0:
        hit_details.append({
            "list_name": "OFAC SDN" if hash_val % 2 == 0 else "UN Consolidated List",
            "match_score": 0.95,
            "matched_name": "Sample Match (Demo)",
            "requires_review": requires_review
        })
    
    # Store screening event
    await _store_screening_event(
        db=db,
        uetr=request.uetr,
        event_type="SANCTIONS_SCREENING",
        status=status.value,
        details={
            "hits_detected": hits,
            "screening_provider": request.screening_provider or "SANDBOX_DEMO",
            "reason_code": reason_code
        }
    )
    
    return SanctionsScreeningResponse(
        uetr=request.uetr,
        status=status,
        screening_timestamp=timestamp,
        hits_detected=hits,
        hit_details=hit_details if hit_details else None,
        reason_code=reason_code,
        reason_text=reason_text,
        requires_manual_review=requires_review,
        next_step="PROCEED" if status == ScreeningStatus.SCREENING_PASSED else "BLOCK"
    )


# =============================================================================
# Helper Functions
# =============================================================================

async def _store_screening_event(
    db: AsyncSession,
    uetr: str,
    event_type: str,
    status: str,
    details: dict
) -> None:
    """Store sanctions screening event for audit trail."""
    from sqlalchemy import text
    
    query = text("""
        INSERT INTO payment_events (
            payment_id, event_type, event_timestamp, actor, details
        )
        SELECT 
            p.payment_id, :event_type, NOW(), 'SANCTIONS_SYSTEM', :details
        FROM payments p
        WHERE p.uetr = :uetr
    """)
    
    await db.execute(query, {
        "uetr": uetr,
        "event_type": event_type,
        "details": json.dumps({
            "screening_status": status,
            **details
        })
    })
    await db.commit()


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get(
    "/screening-result/{uetr}",
    summary="Get sanctions screening result for a payment"
)
async def get_screening_result(
    uetr: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Retrieve sanctions screening history for a payment."""
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            event_type,
            event_timestamp,
            details
        FROM payment_events
        WHERE payment_id = (
            SELECT payment_id FROM payments WHERE uetr = :uetr
        )
        AND event_type IN ('SANCTIONS_DATA_REVIEW', 'SANCTIONS_SCREENING')
        ORDER BY event_timestamp DESC
    """)
    
    result = await db.execute(query, {"uetr": uetr})
    events = result.fetchall()
    
    return {
        "uetr": uetr,
        "screening_events": [
            {
                "event_type": e.event_type,
                "timestamp": e.event_timestamp.isoformat(),
                "details": e.details
            }
            for e in events
        ]
    }
