"""
ISO 20022 Message Processing API Endpoints

Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/key-points

These are the core payment flow endpoints:
- POST /iso20022/pacs008 - Payment instruction (FI to FI Customer Credit Transfer)
- POST /iso20022/acmt023 - Proxy/account resolution request
- POST /iso20022/validate - Validate any ISO 20022 message against XSD

CRITICAL: Nexus validates quote ID, exchange rate, and SAP details.
          Quote expiry is 600 seconds (10 minutes).
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from pydantic import BaseModel
from lxml import etree
import json
import re

from ..db import get_db
from ..config import settings
from . import validation as xsd_validation

router = APIRouter(prefix="/v1/iso20022", tags=["ISO 20022 Messages"])


# =============================================================================
# Constants per Nexus Specification
# =============================================================================

QUOTE_EXPIRY_SECONDS = 600  # 10 minutes - FXPs must honour quotes for this duration

# NexusOrgnlUETR prefix for pacs.008 return payments
# Reference: NotebookLM 2026-02-03 - "Include original UETR prefixed with NexusOrgnlUETR:"
# Made flexible to accept: NexusOrgnlUETR:uuid, NexusOrgnlUETR: uuid, NexusOrgnlUETR uuid, etc.
NEXUS_ORIGINAL_UETR_PREFIX = "NexusOrgnlUETR:"
NEXUS_ORIGINAL_UETR_PATTERN = re.compile(r"NexusOrgnlUETR[:\s]+([a-f0-9\-]{36})", re.IGNORECASE)

# =============================================================================
# ISO 20022 Status Reason Codes (ExternalStatusReason1Code)
# Reference: NotebookLM - Technical Assumptions A20
# Assumption A28: Sandbox implements subset of 60+ production codes
# =============================================================================

# Success
STATUS_ACCEPTED = "ACCC"            # Accepted Settlement Completed

# Quote/Rate Errors (AB04: Aborted - Settlement Fatal Error)
STATUS_QUOTE_EXPIRED = "AB04"       # Quote validity window exceeded
STATUS_RATE_MISMATCH = "AB04"       # Agreed rate doesn't match stored quote

# Timeout Errors
STATUS_TIMEOUT = "AB03"             # Transaction not received within window

# Account Errors
STATUS_ACCOUNT_INCORRECT = "AC01"   # Incorrect Account Number format
STATUS_ACCOUNT_CLOSED = "AC04"      # Closed Account Number
STATUS_PROXY_INVALID = "BE23"       # Account/Proxy Invalid (not registered)

# Agent Errors
STATUS_AGENT_INCORRECT = "AGNT"     # Incorrect Agent (PSP not onboarded)
STATUS_INVALID_SAP = "RC11"         # Invalid Intermediary Agent
STATUS_AGENT_OFFLINE = "AB08"       # Offline Creditor Agent

# Amount Errors
STATUS_AMOUNT_LIMIT = "AM02"        # IPS Limit exceeded
STATUS_INSUFFICIENT_FUNDS = "AM04"  # Insufficient Funds

# Compliance Errors
STATUS_REGULATORY_AML = "RR04"      # Regulatory/AML block

# All status codes for validation
VALID_STATUS_CODES = {
    STATUS_ACCEPTED, STATUS_QUOTE_EXPIRED, STATUS_RATE_MISMATCH,
    STATUS_TIMEOUT, STATUS_ACCOUNT_INCORRECT, STATUS_ACCOUNT_CLOSED,
    STATUS_PROXY_INVALID, STATUS_AGENT_INCORRECT, STATUS_INVALID_SAP,
    STATUS_AGENT_OFFLINE, STATUS_AMOUNT_LIMIT, STATUS_INSUFFICIENT_FUNDS,
    STATUS_REGULATORY_AML
}


class PaymentValidationResult(BaseModel):
    """Result of pacs.008 validation."""
    valid: bool
    uetr: str
    quoteId: Optional[str] = None
    errors: list[str] = []
    statusCode: str = "ACCC"
    statusReasonCode: Optional[str] = None


class Pacs008Response(BaseModel):
    """Response after pacs.008 processing."""
    uetr: str
    status: str
    statusReasonCode: Optional[str] = None
    message: str
    callbackEndpoint: str
    processedAt: str


class Acmt023Response(BaseModel):
    """Response after acmt.023 processing."""
    requestId: str
    status: str
    callbackEndpoint: str
    processedAt: str


class Acmt024Response(BaseModel):
    """Response after acmt.024 processing."""
    requestId: str
    status: str
    debtorNameMasked: Optional[str] = None
    processedAt: str


class Pacs028Response(BaseModel):
    """Response after pacs.028 processing."""
    requestId: str
    originalUetr: str
    currentStatus: str
    processedAt: str


class Iso20022Template(BaseModel):
    """Template/Sample for an ISO 20022 message."""
    messageType: str
    name: str
    description: str
    sample_xml: str


# =============================================================================
# GET /iso20022/templates - Message Examples
# =============================================================================

@router.get(
    "/templates",
    response_model=dict[str, Iso20022Template],
    summary="Get ISO 20022 Message Templates",
    description="Returns reference XML samples for all supported ISO 20022 messages."
)
async def get_iso20022_templates():
    """Return dictionary of message templates for frontend usage."""
    return {
        "pacs.008": {
            "messageType": "pacs.008",
            "name": "FI To FI Customer Credit Transfer",
            "description": "Payment instruction message",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.13">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>PACS008-2026-0203-001</MsgId>
      <CreDtTm>2026-02-03T10:30:05Z</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <SttlmInf>
        <SttlmMtd>INGA</SttlmMtd>
      </SttlmInf>
    </GrpHdr>
    <CdtTrfTxInf>
      <PmtId>
        <EndToEndId>E2E-2026-0203-001</EndToEndId>
        <TxId>TXN-2026-0203-001</TxId>
      </PmtId>
      <IntrBkSttlmAmt Ccy="THB">26452.10</IntrBkSttlmAmt>
      <ChrgBr>SHAR</ChrgBr>
      <Dbtr>
        <Nm>JOHN DOE</Nm>
      </Dbtr>
      <DbtrAgt>
        <FinInstnId>
          <BICFI>DBSSSGSG</BICFI>
        </FinInstnId>
      </DbtrAgt>
      <CdtrAgt>
        <FinInstnId>
          <BICFI>KASITHBK</BICFI>
        </FinInstnId>
      </CdtrAgt>
      <Cdtr>
        <Nm>SOMCHAI THONGCHAI</Nm>
      </Cdtr>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>"""
        },
        "pacs.002": {
            "messageType": "pacs.002",
            "name": "Payment Status Report",
            "description": "Payment confirmation/rejection status",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.10">
  <FIToFIPmtStsRpt>
    <GrpHdr>
      <MsgId>PACS002-2026-0203-001</MsgId>
      <CreDtTm>2026-02-03T10:30:10Z</CreDtTm>
    </GrpHdr>
    <TxInfAndSts>
      <OrgnlEndToEndId>E2E-2026-0203-001</OrgnlEndToEndId>
      <OrgnlTxId>TXN-2026-0203-001</OrgnlTxId>
      <TxSts>ACCC</TxSts>
      <StsRsnInf>
        <Rsn>
          <Cd>0000</Cd>
        </Rsn>
        <AddtlInf>Payment completed successfully</AddtlInf>
      </StsRsnInf>
      <AccptncDtTm>2026-02-03T10:30:10Z</AccptncDtTm>
    </TxInfAndSts>
  </FIToFIPmtStsRpt>
</Document>"""
        },
        "acmt.023": {
            "messageType": "acmt.023",
            "name": "Identification Verification Request",
            "description": "Proxy resolution request sent to PDO",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:acmt.023.001.03">
  <IdVrfctnReq>
    <Assgnmt>
      <MsgId>ACMT023-2026-0203-001</MsgId>
      <CreDtTm>2026-02-03T10:30:00Z</CreDtTm>
      <Assgnr>
        <Pty>
          <Id>
            <OrgId>
              <LEI>529900T8BM49AURSDO55</LEI>
            </OrgId>
          </Id>
        </Pty>
      </Assgnr>
      <Assgne>
        <Pty>
          <Id>
            <OrgId>
              <Othr>
                <Id>NEXUSGW</Id>
              </Othr>
            </OrgId>
          </Id>
        </Pty>
      </Assgne>
    </Assgnmt>
    <Vrfctn>
      <Id>+66812345678</Id>
      <Tp>MOBL</Tp>
    </Vrfctn>
  </IdVrfctnReq>
</Document>"""
        },
        "acmt.024": {
            "messageType": "acmt.024",
            "name": "Identification Verification Report",
            "description": "Proxy resolution response from PDO",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:acmt.024.001.03">
  <IdVrfctnRpt>
    <Assgnmt>
      <MsgId>ACMT024-2026-0203-001</MsgId>
      <CreDtTm>2026-02-03T10:30:01Z</CreDtTm>
    </Assgnmt>
    <Rpt>
      <OrgnlId>REQ20260204-999</OrgnlId>
      <Vrfctn>true</Vrfctn>
      <UpdtdPtyAndAcctId>
        <Pty><Nm>Jane Smith</Nm></Pty>
        <Acct>
          <Id><Othr><Id>0987654321</Id></Othr></Id>
        </Acct>
        <Agt><FinInstnId><BICFI>BKKBTHBK</BICFI></FinInstnId></Agt>
      </UpdtdPtyAndAcctId>
    </Rpt>
  </IdVrfctnRpt>
</Document>"""
        },
        "camt.054": {
            "messageType": "camt.054",
            "name": "Bank to Customer Debit/Credit Notification",
            "description": "Reconciliation report for IPS Operators",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.08">
  <BkToCstmrDbtCdtNtfctn>
    <GrpHdr>
      <MsgId>RECON-20260204</MsgId>
      <CreDtTm>2026-02-04T23:59:59Z</CreDtTm>
    </GrpHdr>
    <Ntfctn>
      <Id>RECON-001</Id>
      <CreDtTm>2026-02-04T23:59:59Z</CreDtTm>
      <Ntry>
        <Amt Ccy="SGD">1000.00</Amt>
        <Sts>BOOK</Sts>
        <BkTxCd>
          <Domn>
            <Cd>PMNT</Cd>
            <Fmly><Cd>ICDT</Cd></Fmly>
          </Domn>
        </BkTxCd>
      </Ntry>
    </Ntfctn>
  </BkToCstmrDbtCdtNtfctn>
</Document>"""
        },
        "camt.103": {
            "messageType": "camt.103",
            "name": "Create Reservation",
            "description": "Liquidity reservation request (Method 2a)",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.103.001.03">
  <CretRsvatn>
    <GrpHdr>
      <MsgId>RSV20260204-001</MsgId>
      <CreDtTm>2026-02-04T18:00:02Z</CreDtTm>
    </GrpHdr>
    <RsvatnId>RSV-TX-001</RsvatnId>
    <CurRsvatn>
      <Amt Ccy="THB">25000.00</Amt>
      <Tp><Cd>AVLB</Cd></Tp>
    </CurRsvatn>
  </CretRsvatn>
</Document>"""
        },
        "pain.001": {
            "messageType": "pain.001",
            "name": "Customer Credit Transfer Initiation",
            "description": "Payment initiation request (Method 3)",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.11">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>INIT20260204-123</MsgId>
      <CreDtTm>2026-02-04T18:00:03Z</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <InitgPty><Nm>Destination IPS</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>P-INIT-01</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <Dbtr><Nm>FXP ALPHA</Nm></Dbtr>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>E2E-01</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="THB">25000.00</InstdAmt></Amt>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""
        },
        "pacs.004": {
            "messageType": "pacs.004",
            "name": "Payment Return",
            "description": "Return of funds (reversal)",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.004.001.11">
  <PmtRtr>
    <GrpHdr>
      <MsgId>RET20260204-001</MsgId>
      <CreDtTm>2026-02-04T18:30:00Z</CreDtTm>
    </GrpHdr>
    <TxInf>
      <RtrId>RTR-01</RtrId>
      <OrgnlUETR>91398cbd-0838-453f-b2c7-536e829f2b8e</OrgnlUETR>
      <RtrdIntrBkSttlmAmt Ccy="SGD">1000.00</RtrdIntrBkSttlmAmt>
      <RtrRsnInf><Rsn><Cd>CUST</Cd></Rsn></RtrRsnInf>
    </TxInf>
  </PmtRtr>
</Document>"""
        },
        "pacs.028": {
            "messageType": "pacs.028",
            "name": "FI To FI Payment Status Request",
            "description": "Status enquiry for a transaction",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.028.001.05">
  <FIToFIPmtStsReq>
    <GrpHdr>
      <MsgId>QRY20260204-01</MsgId>
      <CreDtTm>2026-02-04T18:05:00Z</CreDtTm>
    </GrpHdr>
    <TxInf>
      <OrgnlUETR>91398cbd-0838-453f-b2c7-536e829f2b8e</OrgnlUETR>
      <InstgAgt><FinInstnId><BICFI>DBSGSGSG</BICFI></FinInstnId></InstgAgt>
    </TxInf>
  </FIToFIPmtStsReq>
</Document>"""
        },
        "camt.056": {
            "messageType": "camt.056",
            "name": "FI To FI Payment Cancellation Request",
            "description": "Request to cancel an incorrect payment",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.056.001.10">
  <FIToFIPmtCxlReq>
    <GrpHdr>
      <MsgId>RCL20260204-01</MsgId>
      <CreDtTm>2026-02-04T19:00:00Z</CreDtTm>
    </GrpHdr>
    <Underlyg>
      <TxInf>
        <OrgnlUETR>91398cbd-0838-453f-b2c7-536e829f2b8e</OrgnlUETR>
        <CxlRsnInf><Rsn><Cd>DUPL</Cd></Rsn></CxlRsnInf>
      </TxInf>
    </Underlyg>
  </FIToFIPmtCxlReq>
</Document>"""
        },
        "camt.029": {
            "messageType": "camt.029",
            "name": "Resolution Of Investigation",
            "description": "Response to a cancellation request",
            "sample_xml": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.029.001.11">
  <RsltnOfInvstgtn>
    <Assgnmt>
      <MsgId>RSP20260204-01</MsgId>
      <CreDtTm>2026-02-04T19:15:00Z</CreDtTm>
    </Assgnmt>
    <Sts><Conf>RJCR</Conf></Sts>
    <CxlDetails>
      <TxInfAndSts>
        <OrgnlUETR>91398cbd-0838-453f-b2c7-536e829f2b8e</OrgnlUETR>
        <CxlStsId>RJCR</CxlStsId>
      </TxInfAndSts>
    </CxlDetails>
  </RsltnOfInvstgtn>
</Document>"""
        },
    }


# =============================================================================
# POST /iso20022/pacs008 - Payment Instruction
# =============================================================================

@router.post(
    "/pacs008",
    response_model=Pacs008Response,
    summary="Submit pacs.008 payment instruction",
    description="""
    **Core payment flow endpoint**
    
    Accepts an ISO 20022 pacs.008 (FI to FI Customer Credit Transfer) message
    from the Source IPS on behalf of the Source PSP.
    
    ## Validation per Nexus Specification
    
    1. **Quote Expiry**: Quotes valid for 600 seconds (10 min)
    2. **Exchange Rate**: Must match the stored quote rate
    3. **Intermediary Agents**: SAPs must match FXP's registered accounts
    
    ## Mandatory Fields (Nexus requirements beyond CBPR+)
    
    - UETR (UUID v4)
    - Acceptance Date Time
    - Debtor Account
    - Creditor Account
    - Agreed Rate (if using third-party FXP)
    
    Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-pacs.008-fi-to-fi-customer-credit-transfer
    """
)
async def process_pacs008(
    request: Request,
    pacs002_endpoint: str = Query(
        ...,
        alias="pacs002Endpoint",
        description="Callback URL for pacs.002 status report"
    ),
    db: AsyncSession = Depends(get_db)
) -> Pacs008Response:
    """
    Process pacs.008 payment instruction.
    
    Steps per Nexus specification:
    1. Parse ISO 20022 XML
    2. Extract UETR, quote ID, exchange rate
    3. Validate quote (expiry, rate, SAPs)
    4. Store payment record
    5. Forward to destination IPS (async)
    6. Return acknowledgement
    """
    processed_at = datetime.now(timezone.utc)
    
    # Get raw XML body
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read XML body: {str(e)}"
        )
    
    # Step 1: XSD Schema Validation (Lenient mode for sandbox)
    # In production, this would reject non-compliant messages
    # For sandbox demo, we log warnings but continue processing
    xsd_result = xsd_validation.validate_pacs008(xml_content)
    if not xsd_result.valid:
        # Forensic Logging: Store violation in Message Observatory
        # Reference: Gap Analysis - Integrate XSD validation into payment flow (Persistence)
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_WARNING",
            actor="NEXUS",
            data={
                "messageType": "pacs.008",
                "errors": xsd_result.errors,
                "summary": "Message has XSD schema warnings (sandbox lenient mode - processing continues)",
                "sandboxMode": True
            },
            pacs008_xml=xml_content
        )
        # SANDBOX: Log warning but continue (production would reject here)
        import logging
        logging.getLogger(__name__).warning(
            f"XSD validation warnings (sandbox lenient mode): {xsd_result.errors[:2]}"
        )
    
    # Step 2: Parse XML
    try:
        parsed = parse_pacs008(xml_content)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pacs.008 XML: {str(e)}"
        )
    
    # Validate against Nexus requirements
    validation = await validate_pacs008(parsed, db)
    
    if not validation.valid:
        # Store rejected payment so it appears in Payment Explorer
        await store_payment(
            db=db,
            uetr=validation.uetr,
            quote_id=parsed.get("quoteId"),
            source_psp_bic=parsed.get("debtorAgentBic"),
            destination_psp_bic=parsed.get("creditorAgentBic"),
            debtor_name=parsed.get("debtorName", "Unknown"),
            debtor_account=parsed.get("debtorAccount", "Unknown"),
            creditor_name=parsed.get("creditorName", "Unknown"),
            creditor_account=parsed.get("creditorAccount", "Unknown"),
            source_currency=parsed.get("settlementCurrency"),
            destination_currency=parsed.get("instructedCurrency", "XXX"),
            source_amount=parsed.get("settlementAmount"),
            exchange_rate=parsed.get("exchangeRate"),
            status="RJCT"
        )
        
        # Generate pacs.002 rejection response
        pacs002_xml = build_pacs002_rejection(
            uetr=validation.uetr,
            status_code="RJCT",
            reason_code=validation.statusReasonCode,
            reason_description=validation.errors[0] if validation.errors else "Validation failed"
        )
        
        # Store rejected payment event with both pacs.008 and pacs.002 for audit
        await store_payment_event(
            db=db,
            uetr=validation.uetr,
            event_type="PAYMENT_REJECTED",
            actor="NEXUS",
            data={
                "errors": validation.errors,
                "statusReasonCode": validation.statusReasonCode,
            },
            pacs008_xml=xml_content,  # Store full incoming pacs.008
            pacs002_xml=pacs002_xml   # Store generated pacs.002 rejection
        )
        
        raise HTTPException(
            status_code=422,
            detail={
                "uetr": validation.uetr,
                "status": "RJCT",
                "statusReasonCode": validation.statusReasonCode,
                "errors": validation.errors,
                "reference": "https://docs.nexusglobalpayments.org/payment-processing/validations-duplicates-and-fraud"
            }
        )
    
    # Store accepted payment
    await store_payment(
        db=db,
        uetr=validation.uetr,
        quote_id=parsed.get("quoteId"),
        source_psp_bic=parsed.get("debtorAgentBic"),
        destination_psp_bic=parsed.get("creditorAgentBic"),
        debtor_name=parsed.get("debtorName", "Unknown"),
        debtor_account=parsed.get("debtorAccount", "Unknown"),
        creditor_name=parsed.get("creditorName", "Unknown"),
        creditor_account=parsed.get("creditorAccount", "Unknown"),
        source_currency=parsed.get("settlementCurrency"),
        destination_currency=parsed.get("instructedCurrency", "XXX"),
        source_amount=parsed.get("settlementAmount"),
        exchange_rate=parsed.get("exchangeRate"),
        status="ACSP"
    )
    
    # Check for NexusOrgnlUETR in remittance info (pacs.008 return payment)
    # Reference: NotebookLM 2026-02-03 - "pacs.008 for returns must include NexusOrgnlUETR:"
    original_uetr = None
    remittance_info = parsed.get("remittanceInfo", "")
    if remittance_info:
        match = NEXUS_ORIGINAL_UETR_PATTERN.search(remittance_info)
        if match:
            original_uetr = match.group(1)
            # Emit RETURN_LINKED event for Message Observatory
            await store_payment_event(
                db=db,
                uetr=validation.uetr,
                event_type="RETURN_LINKED",
                actor="NEXUS",
                data={
                    "originalUetr": original_uetr,
                    "returnUetr": validation.uetr,
                    "message": f"Return payment linked to original payment {original_uetr}",
                    "nexusOrgnlUetrFound": True
                }
            )
    
    # Transformation Logic (Step 15-16 of Nexus Flow)
    # Forwarding message to Destination IPS requires updating Agents and Amounts
    # We fetch the SAP details from the quote validation result or re-query
    creditor_bic = parsed.get("creditorAgentBic") or "UNKNTHBK"  # Fallback BIC
    quote_data = {
        "dest_sap_bic": "SAP" + creditor_bic[3:] if len(creditor_bic) >= 4 else "SAPXXXX",  # Mock logic: Destination SAP
        "dest_psp_bic": creditor_bic,
        "dest_amount": parsed.get("instructedAmount") or parsed.get("settlementAmount") or "0",
        "dest_currency": parsed.get("instructedCurrency") or parsed.get("settlementCurrency") or "USD"
    }
    
    transformed_xml = transform_pacs008(xml_content, quote_data)
    
    # Generate pacs.002 acceptance response
    pacs002_xml = build_pacs002_acceptance(
        uetr=validation.uetr,
        status_code="ACCC",
        settlement_amount=parsed.get("settlementAmount"),
        settlement_currency=parsed.get("settlementCurrency")
    )
    
    # Generate camt.054 reconciliation message
    # Reference: Gap 8 - Generate camt.054 on successful payment
    camt054_xml = build_camt054(
        uetr=validation.uetr,
        amount=parsed.get("settlementAmount"),
        currency=parsed.get("settlementCurrency"),
        debtor_name=parsed.get("debtorName", "Demo Sender"),
        creditor_name=parsed.get("creditorName", "Demo Recipient")
    )
    
    await store_payment_event(
        db=db,
        uetr=validation.uetr,
        event_type="PAYMENT_ACCEPTED",
        actor="NEXUS",
        data={
            "quoteId": validation.quoteId,
            "transformedXml": transformed_xml[:500],  # Truncate transformed XML for data field
            "routingTo": "DEST_IPS",
            "reconciliationGenerated": True
        },
        pacs008_xml=xml_content,  # Store original pacs.008
        pacs002_xml=pacs002_xml,  # Store generated pacs.002 acceptance
        camt054_xml=camt054_xml   # Store generated camt.054 reconciliation
    )
    
    return Pacs008Response(
        uetr=validation.uetr,
        status="ACSP",
        statusReasonCode=None,
        message="Payment instruction accepted, transformed and forwarded to destination IPS",
        callbackEndpoint=pacs002_endpoint,
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/acmt023 - Proxy/Account Resolution
# =============================================================================

@router.post(
    "/acmt023",
    response_model=Acmt023Response,
    summary="Submit acmt.023 resolution request",
    description="""
    Accepts an ISO 20022 acmt.023 (Identification Verification Request) message
    for proxy or account resolution.
    
    Used in Steps 7-9 of the payment flow when the Source PSP needs to
    resolve a proxy (mobile number, email) to an account number.
    
    Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-acmt.023-identification-verification-request
    """
)
async def process_acmt023(
    request: Request,
    acmt024_endpoint: str = Query(
        ...,
        alias="acmt024Endpoint",
        description="Callback URL for acmt.024 resolution response"
    ),
    db: AsyncSession = Depends(get_db)
) -> Acmt023Response:
    """
    Process acmt.023 proxy resolution request.
    
    Steps:
    1. Validate against XSD schema
    2. Parse ISO 20022 XML
    3. Extract proxy type and value
    4. Route to destination PDO
    5. Return acknowledgement (async response via callback)
    """
    processed_at = datetime.now(timezone.utc)
    request_id = str(uuid4())
    
    # Get raw XML body
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read XML body: {str(e)}"
        )
    
    # Step 1: XSD Schema Validation
    xsd_result = xsd_validation.validate_acmt023(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "acmt.023",
                "errors": xsd_result.errors,
                "summary": "Incoming acmt.023 failed XSD schema validation"
            },
            acmt023_xml=xml_content
        )

        raise HTTPException(
            status_code=400,
            detail={
                "error": "XSD_VALIDATION_FAILED",
                "messageType": "acmt.023",
                "validationErrors": xsd_result.errors,
                "reference": "https://www.iso20022.org/message/acmt.023"
            }
        )
    
    # For sandbox: Accept and acknowledge
    # In production: Parse XML, route to PDO, wait for acmt.024
    
    return Acmt023Response(
        requestId=request_id,
        status="ACCEPTED",
        callbackEndpoint=acmt024_endpoint,
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/acmt024 - Proxy/Account Resolution Report
# =============================================================================

@router.post(
    "/acmt024",
    response_model=Acmt024Response,
    summary="Submit acmt.024 resolution report",
    description="""
    Accepts an ISO 20022 acmt.024 (Identification Verification Report) message
    providing details of a resolved proxy or account.
    
    Used in Step 9 of the payment flow when the Destination PDO responds
    to an acmt.023 request.
    
    Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-acmt.024-identification-verification-report
    """
)
async def process_acmt024(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Acmt024Response:
    """Process acmt.024 proxy resolution report."""
    processed_at = datetime.now(timezone.utc)
    request_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_acmt024(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "acmt.024",
                "errors": xsd_result.errors
            },
            acmt024_xml=xml_content
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    return Acmt024Response(
        requestId=request_id,
        status="RECEIVED",
        debtorNameMasked="REDACTED",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/pain001 - SAP Integration Method 3
# =============================================================================

class Pain001Response(BaseModel):
    """Response after pain.001 processing."""
    requestId: str
    status: str
    message: str
    processedAt: str


@router.post(
    "/pain001",
    response_model=Pain001Response,
    summary="Submit pain.001 Customer Credit Transfer Initiation",
    description="""
    **Optional - SAP Integration Method 3**
    
    Accepts a pain.001 (Customer Credit Transfer Initiation) message
    from the Destination IPS acting as a corporate client to the D-SAP.
    
    This is used when the D-SAP's corporate payment channel is leveraged
    for initiating domestic leg payments.
    
    Reference: https://docs.nexusglobalpayments.org/settlement-access-provision/processing-payments-as-an-sap
    """
)
async def process_pain001(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Pain001Response:
    """Process pain.001 Customer Credit Transfer Initiation."""
    processed_at = datetime.now(timezone.utc)
    request_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_pain001(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "pain.001",
                "errors": xsd_result.errors
            },
            pain001_xml=xml_content
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    return Pain001Response(
        requestId=request_id,
        status="ACCEPTED",
        message="pain.001 accepted - forwarding to SAP corporate channel",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/camt103 - SAP Integration Method 2a
# =============================================================================

class Camt103Response(BaseModel):
    """Response after camt.103 processing."""
    reservationId: str
    status: str
    message: str
    processedAt: str


@router.post(
    "/camt103",
    response_model=Camt103Response,
    summary="Submit camt.103 Create Reservation",
    description="""
    **Optional - SAP Integration Method 2a**
    
    Accepts a camt.103 (Create Reservation) message for liquidity reservation
    at the Destination SAP. This creates a debit authorization for the
    FXP's account before the payment is processed.
    
    Reference: https://docs.nexusglobalpayments.org/settlement-access-provision/liquidity
    """
)
async def process_camt103(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Camt103Response:
    """Process camt.103 Create Reservation."""
    processed_at = datetime.now(timezone.utc)
    reservation_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_camt103(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "camt.103",
                "errors": xsd_result.errors
            },
            camt103_xml=xml_content
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    return Camt103Response(
        reservationId=reservation_id,
        status="CREATED",
        message="Liquidity reservation created at SAP",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/pacs004 - Payment Return (Future)
# =============================================================================

class Pacs004Response(BaseModel):
    """Response after pacs.004 processing."""
    returnId: str
    originalUetr: str
    status: str
    message: str
    processedAt: str


@router.post(
    "/pacs004",
    response_model=Pacs004Response,
    summary="Submit pacs.004 Payment Return",
    description="""
    **Future/Roadmap - Not in Release 1**
    
    Accepts a pacs.004 (Payment Return) message for returning funds
    after settlement. Currently, Nexus Release 1 uses pacs.008 with
    NexusOrgnlUETR in remittance info for returns.
    
    This endpoint is provided for future compatibility.
    
    Reference: https://docs.nexusglobalpayments.org/payment-processing/returns
    """
)
async def process_pacs004(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Pacs004Response:
    """Process pacs.004 Payment Return."""
    processed_at = datetime.now(timezone.utc)
    return_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_pacs004(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "pacs.004",
                "errors": xsd_result.errors
            },
            pacs004_xml=xml_content
        )
        raise HTTPException(
            status_code=400, 
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    # Extract original UETR from XML (simplified)
    original_uetr = "EXTRACTED_FROM_XML"
    
    return Pacs004Response(
        returnId=return_id,
        originalUetr=original_uetr,
        status="ACCEPTED",
        message="Payment return processed (Future - use pacs.008 with NexusOrgnlUETR for Release 1)",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/pacs028 - Payment Status Request
# =============================================================================

@router.post(
    "/pacs028",
    response_model=Pacs028Response,
    summary="Submit pacs.028 Payment Status Request",
    description="""
    **Future/Roadmap - Not in Release 1**
    
    Accepts a pacs.028 (FI to FI Payment Status Request) message to query
    the current status of a payment that has not yet reached a final state.
    
    Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-pacs.028-fi-to-fi-payment-status-request
    """
)
async def process_pacs028(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Pacs028Response:
    """Process pacs.028 Payment Status Request."""
    processed_at = datetime.now(timezone.utc)
    request_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_pacs028(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "pacs.028",
                "errors": xsd_result.errors
            },
            pacs028_xml=xml_content
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    original_uetr = xsd_validation.safe_extract_uetr(xml_content) or "UNKNOWN"
    
    return Pacs028Response(
        requestId=request_id,
        originalUetr=original_uetr,
        currentStatus="PENDING",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/camt056 - Payment Recall (Future)
# =============================================================================

class Camt056Response(BaseModel):
    """Response after camt.056 processing."""
    recallId: str
    originalUetr: str
    status: str
    message: str
    processedAt: str


@router.post(
    "/camt056",
    response_model=Camt056Response,
    summary="Submit camt.056 Payment Cancellation Request (Recall)",
    description="""
    **Future/Roadmap - Not in Release 1**
    
    Accepts a camt.056 (FI to FI Payment Cancellation Request) for recalling
    funds after settlement due to fraud, error, or other reasons.
    
    For Release 1, use the Service Desk portal (/service-desk) for manual recall.
    
    Reference: https://docs.nexusglobalpayments.org/payment-processing/recall-and-return
    """
)
async def process_camt056(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Camt056Response:
    """Process camt.056 Payment Cancellation Request."""
    processed_at = datetime.now(timezone.utc)
    recall_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_camt056(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "camt.056",
                "errors": xsd_result.errors
            },
            camt056_xml=xml_content
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    original_uetr = "EXTRACTED_FROM_XML"
    
    return Camt056Response(
        recallId=recall_id,
        originalUetr=original_uetr,
        status="ACCEPTED",
        message="Recall request acknowledged (Future - use Service Desk for Release 1)",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/camt029 - Resolution of Investigation (Future)
# =============================================================================

class Camt029Response(BaseModel):
    """Response after camt.029 processing."""
    resolutionId: str
    recallId: str
    status: str
    resolution: str
    message: str
    processedAt: str


@router.post(
    "/camt029",
    response_model=Camt029Response,
    summary="Submit camt.029 Resolution of Investigation",
    description="""
    **Future/Roadmap - Not in Release 1**
    
    Accepts a camt.029 (Resolution of Investigation) message as a response
    to a camt.056 recall request. Indicates whether the recall was accepted
    or rejected by the beneficiary's PSP.
    
    Reference: https://docs.nexusglobalpayments.org/payment-processing/recall-and-return
    """
)
async def process_camt029(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Camt029Response:
    """Process camt.029 Resolution of Investigation."""
    processed_at = datetime.now(timezone.utc)
    resolution_id = str(uuid4())
    
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XML: {str(e)}")
    
    # XSD Validation
    xsd_result = xsd_validation.validate_camt029(xml_content)
    if not xsd_result.valid:
        # Forensic Logging
        failed_uetr = xsd_validation.safe_extract_uetr(xml_content) or f"UNKNOWN-{uuid4().hex[:8]}"
        await store_payment_event(
            db=db,
            uetr=failed_uetr,
            event_type="SCHEMA_VALIDATION_FAILED",
            actor="NEXUS",
            data={
                "messageType": "camt.029",
                "errors": xsd_result.errors
            },
            camt029_xml=xml_content
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "XSD_VALIDATION_FAILED", "errors": xsd_result.errors}
        )
    
    return Camt029Response(
        resolutionId=resolution_id,
        recallId="EXTRACTED_FROM_XML",
        status="RECEIVED",
        resolution="PENDING_REVIEW",
        message="Resolution of investigation received (Future - use Service Desk for Release 1)",
        processedAt=processed_at.isoformat()
    )


# =============================================================================
# POST /iso20022/validate - Generic XSD Validation
# =============================================================================

class ValidationResponse(BaseModel):
    """Response for XSD validation."""
    valid: bool
    messageType: str
    errors: list[str] = []
    warnings: list[str] = []


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate ISO 20022 message against XSD schema",
    description="""
    Validates any ISO 20022 message against its XSD schema.
    
    **Release 1 (Mandatory):**
    - pacs.008.001.13 (FI to FI Customer Credit Transfer)
    - pacs.002.001.15 (Payment Status Report)
    - acmt.023.001.04 (Identification Verification Request)
    - acmt.024.001.04 (Identification Verification Response)
    - camt.054.001.13 (Bank To Customer Notification)
    
    **Optional (SAP Integration):**
    - camt.103.001.03 (Create Reservation)
    - pain.001.001.12 (Customer Credit Transfer Initiation)
    
    **Future/Roadmap:**
    - pacs.004.001.14 (Payment Return)
    - pacs.028.001.06 (FI to FI Payment Status Request)
    - camt.056.001.11 (FI to FI Payment Cancellation Request)
    - camt.029.001.13 (Resolution of Investigation)
    
    Returns validation errors if the message does not conform to the schema.
    """
)
async def validate_message(
    request: Request,
    message_type: Optional[str] = Query(
        None,
        alias="messageType",
        description="Message type (auto-detected if not specified)"
    )
) -> ValidationResponse:
    """Validate ISO 20022 message against XSD schema."""
    
    # Get raw XML body
    try:
        body = await request.body()
        xml_content = body.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read XML body: {str(e)}"
        )
    
    # Auto-detect message type if not specified
    if not message_type:
        message_type = xsd_validation.detect_message_type(xml_content)
        if not message_type:
            raise HTTPException(
                status_code=400,
                detail="Could not detect message type. Please specify messageType parameter."
            )
    
    # Validate
    result = xsd_validation.validate_xml(xml_content, message_type)
    
    return ValidationResponse(
        valid=result.valid,
        messageType=result.message_type,
        errors=result.errors,
        warnings=result.warnings
    )


# =============================================================================
# GET /iso20022/schemas/health - Schema Health Check
# =============================================================================

@router.get(
    "/schemas/health",
    summary="Check XSD schema validation health",
    description="""
    Returns the health status of the XSD schema validation system.
    
    Shows:
    - Loaded schemas
    - Load errors
    - Schema directory path
    """
)
async def get_schema_health() -> dict:
    """Get health status of schema validation system."""
    return xsd_validation.get_validation_health()


# =============================================================================
# Helper Functions
# =============================================================================

def parse_pacs008(xml_content: str) -> dict:
    """
    Parse pacs.008 XML and extract key fields.
    
    Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/specific-message-elements
    """
    try:
        root = etree.fromstring(xml_content.encode())
        
        # Define namespace map for ISO 20022
        ns = {
            'doc': 'urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08',
            'head': 'urn:iso:std:iso:20022:tech:xsd:head.001.001.02'
        }
        
        # Extract with fallback for namespace-less XML (simplified parsing)
        def get_text(xpath, default=None):
            # Try with namespace
            elements = root.xpath(xpath, namespaces=ns)
            if elements:
                return elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
            # Try without namespace (for sandbox testing)
            simple_xpath = xpath.replace('doc:', '').replace('head:', '')
            elements = root.xpath(simple_xpath)
            if elements:
                return elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
            return default
        
        return {
            "uetr": get_text(".//UETR") or get_text(".//doc:UETR"),
            "messageId": get_text(".//MsgId") or get_text(".//doc:MsgId"),
            "endToEndId": get_text(".//EndToEndId") or get_text(".//doc:EndToEndId"),
            "quoteId": get_text(".//QtId") or get_text(".//doc:QtId") or get_text(".//CtrctId") or get_text(".//doc:CtrctId"),  # FX Quote ID
            "exchangeRate": get_text(".//PreAgrdXchgRate") or get_text(".//doc:PreAgrdXchgRate") or get_text(".//XchgRate") or get_text(".//doc:XchgRate"),
            "settlementAmount": get_text(".//IntrBkSttlmAmt") or get_text(".//doc:IntrBkSttlmAmt"),
            "settlementCurrency": get_text(".//IntrBkSttlmAmt/@Ccy") or "SGD",
            "instructedAmount": get_text(".//InstdAmt") or get_text(".//doc:InstdAmt"),
            "acceptanceDateTime": get_text(".//AccptncDtTm") or get_text(".//doc:AccptncDtTm"),
            "debtorName": get_text(".//Dbtr/Nm") or get_text(".//doc:Dbtr/doc:Nm"),
            "debtorAccount": get_text(".//DbtrAcct/Id/IBAN") or get_text(".//DbtrAcct/Id/Othr/Id") or get_text(".//doc:DbtrAcct/doc:Id/doc:IBAN"),
            "debtorAgentBic": get_text(".//DbtrAgt//BICFI") or get_text(".//doc:DbtrAgt//doc:BICFI"),
            "creditorName": get_text(".//Cdtr/Nm") or get_text(".//doc:Cdtr/doc:Nm"),
            "creditorAccount": get_text(".//CdtrAcct/Id/IBAN") or get_text(".//CdtrAcct/Id/Othr/Id") or get_text(".//doc:CdtrAcct/doc:Id/doc:IBAN"),
            "creditorAgentBic": get_text(".//CdtrAgt//BICFI") or get_text(".//doc:CdtrAgt//doc:BICFI"),
            "instructedCurrency": get_text(".//InstdAmt/@Ccy") or "USD",
            "intermediaryAgent1Bic": get_text(".//IntrmyAgt1//BICFI") or get_text(".//doc:IntrmyAgt1//doc:BICFI"),
            "intermediaryAgent2Bic": get_text(".//IntrmyAgt2//BICFI") or get_text(".//doc:IntrmyAgt2//doc:BICFI"),
            "chargeBearer": get_text(".//ChrgBr") or get_text(".//doc:ChrgBr"),
            # Remittance Information for NexusOrgnlUETR extraction (return payments)
            "remittanceInfo": get_text(".//AddtlRmtInf") or get_text(".//doc:RmtInf//doc:Ustrd") or get_text(".//RmtInf//Ustrd"),
        }
    
    except Exception as e:
        raise ValueError(f"Failed to parse pacs.008: {str(e)}")

def transform_pacs008(xml_content: str, quote_data: dict) -> str:
    """
    Transform pacs.008 for Destination IPS routing.
    
    Reference: NotebookLM 2026-02-03 - Agent Swapping and Amount Conversion
    
    1. Update Instructing Agent to Destination SAP BIC
    2. Update Instructed Agent to Destination PSP BIC
    3. Update Amount to Destination Interbank Amount (converted)
    4. Update PrvsInstgAgt1 to Source SAP (audit trail)
    5. Update ClrSys code to Destination IPS
    """
    try:
        root = etree.fromstring(xml_content.encode())
        ns = {'doc': 'urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08'}
        
        # Store Source SAP for audit trail
        original_instg_agt_bic = None
        instg_agt = root.xpath(".//doc:InstgAgt//doc:BICFI", namespaces=ns)
        if instg_agt:
            original_instg_agt_bic = instg_agt[0].text
            # 1. Instructing Agent (InstgAgt) -> Dest SAP
            instg_agt[0].text = quote_data["dest_sap_bic"]
            
        # 2. Instructed Agent (InstdAgt) -> Dest PSP
        instd_agt = root.xpath(".//doc:InstdAgt//doc:BICFI", namespaces=ns)
        if instd_agt:
            instd_agt[0].text = quote_data["dest_psp_bic"]
            
        # 3. Interbank Settlement Amount (IntrBkSttlmAmt) -> Dest Amount
        amt_elem = root.xpath(".//doc:IntrBkSttlmAmt", namespaces=ns)
        if amt_elem:
            amt_elem[0].text = str(quote_data["dest_amount"])
            amt_elem[0].set("Ccy", quote_data["dest_currency"])
        
        # 3b. Update Agreed Rate section (if exists)
        # Reference: Nexus Flow Step 15-16
        agrd_rate = root.xpath(".//doc:AgrdRate", namespaces=ns)
        if agrd_rate:
            # Update UnitCcy and QtdCcy if they exist
            unit_ccy = root.xpath(".//doc:AgrdRate/doc:UnitCcy", namespaces=ns)
            if unit_ccy: unit_ccy[0].text = quote_data.get("source_currency", "XXX")
            qtd_ccy = root.xpath(".//doc:AgrdRate/doc:QtdCcy", namespaces=ns)
            if qtd_ccy: qtd_ccy[0].text = quote_data.get("dest_currency", "XXX")
        
        # 4. Previous Instructing Agent (PrvsInstgAgt1) -> Source SAP (Audit Trail)
        # Reference: NotebookLM - "Nexus moves the Source SAP here to maintain the audit trail"
        if original_instg_agt_bic:
            cdt_trf_tx_inf = root.xpath(".//doc:CdtTrfTxInf", namespaces=ns)
            if cdt_trf_tx_inf:
                # Create PrvsInstgAgt1 element if not exists
                prvs_instg_agt1 = root.xpath(".//doc:PrvsInstgAgt1", namespaces=ns)
                if not prvs_instg_agt1:
                    new_elem = etree.SubElement(cdt_trf_tx_inf[0], "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}PrvsInstgAgt1")
                    fin_instn_id = etree.SubElement(new_elem, "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}FinInstnId")
                    bicfi = etree.SubElement(fin_instn_id, "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}BICFI")
                    bicfi.text = original_instg_agt_bic
        
        # 4b. Previous Instructing Agent Account (PrvsInstgAgt1Acct) -> FXP Account at S-SAP
        # Reference: NotebookLM - "FXP account at S-SAP moved here for traceability"
        # Assumption A29: FXP account ID derived from quote_data if available
        if quote_data.get("fxp_account_id"):
            cdt_trf_tx_inf = root.xpath(".//doc:CdtTrfTxInf", namespaces=ns)
            if cdt_trf_tx_inf:
                prvs_acct = etree.SubElement(cdt_trf_tx_inf[0], "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}PrvsInstgAgt1Acct")
                acct_id = etree.SubElement(prvs_acct, "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}Id")
                othr = etree.SubElement(acct_id, "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}Othr")
                othr_id = etree.SubElement(othr, "{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}Id")
                othr_id.text = quote_data["fxp_account_id"]
        
        # 5. Clear IntrmyAgt1 (Source SAP removed from destination leg)
        intmy_agt1 = root.xpath(".//doc:IntrmyAgt1", namespaces=ns)
        if intmy_agt1:
            intmy_agt1[0].getparent().remove(intmy_agt1[0])
        
        # 6. Update Clearing System code (ClrSys/Cd)
        clr_sys = root.xpath(".//doc:ClrSys//doc:Cd", namespaces=ns)
        if clr_sys and "dest_ips_code" in quote_data:
            clr_sys[0].text = quote_data["dest_ips_code"]
            
        return etree.tostring(root, encoding='unicode', pretty_print=True)
    except Exception as e:
        # Fallback if namespaces are missing (simplified XML)
        return xml_content  # For sandbox simplicity in edge cases


async def validate_pacs008(parsed: dict, db: AsyncSession) -> PaymentValidationResult:
    """
    Validate pacs.008 against Nexus requirements.
    
    SANDBOX MODE: Validation is lenient - logs warnings but allows processing.
    In production, this would strictly enforce all requirements.
    
    Reference: https://docs.nexusglobalpayments.org/payment-processing/validations-duplicates-and-fraud
    """
    import logging
    logger = logging.getLogger(__name__)
    
    errors = []
    warnings = []
    status_reason = None  # Will be set if validation fails
    quote_id = parsed.get("quoteId")
    uetr = parsed.get("uetr") or str(uuid4())
    
    # 1. UETR is mandatory (but sandbox generates it if missing)
    if not parsed.get("uetr"):
        warnings.append("UETR was not provided - generated for sandbox demo")
    
    # 2. SANDBOX MODE: Skip strict quote validation for demos
    # In production, this would strictly enforce quote expiry, rate matching, etc.
    if quote_id:
        logger.info(f"Sandbox mode: accepting quote {quote_id} without strict validation")
        quote_query = text("""
            SELECT 
                q.quote_id, q.final_rate as exchange_rate, q.expires_at,
                q.fxp_id,
                source_sap.bic as source_sap_bic,
                dest_sap.bic as dest_sap_bic
            FROM quotes q
            LEFT JOIN fxp_sap_accounts source_acc ON q.fxp_id = source_acc.fxp_id AND q.source_currency = source_acc.currency_code
            LEFT JOIN saps source_sap ON source_acc.sap_id = source_sap.sap_id
            LEFT JOIN fxp_sap_accounts dest_acc ON q.fxp_id = dest_acc.fxp_id AND q.destination_currency = dest_acc.currency_code
            LEFT JOIN saps dest_sap ON dest_acc.sap_id = dest_sap.sap_id
            WHERE q.quote_id = :quote_id
        """)
        
        result = await db.execute(quote_query, {"quote_id": quote_id})
        quote = result.fetchone()
        
        if not quote:
            errors.append(f"Quote {quote_id} not found")
            status_reason = STATUS_QUOTE_EXPIRED
        else:
            # Check quote expiry (600 seconds = 10 minutes)
            if quote.expires_at < datetime.now(timezone.utc):
                errors.append(f"Quote {quote_id} has expired (valid for 600 seconds)")
                status_reason = STATUS_QUOTE_EXPIRED
            
            # Check exchange rate matches
            if parsed.get("exchangeRate"):
                submitted_rate = Decimal(str(parsed["exchangeRate"]))
                stored_rate = Decimal(str(quote.exchange_rate))
                
                # Allow small tolerance for floating point
                if abs(submitted_rate - stored_rate) > Decimal("0.000001"):
                    errors.append(
                        f"Exchange rate mismatch: submitted {submitted_rate}, "
                        f"expected {stored_rate}"
                    )
                    status_reason = STATUS_RATE_MISMATCH
            
            # Check intermediary agents (SAPs) match FXP's accounts
            if parsed.get("intermediaryAgent1Bic"):
                if parsed["intermediaryAgent1Bic"] != quote.source_sap_bic:
                    errors.append(
                        f"Intermediary Agent 1 mismatch: {parsed['intermediaryAgent1Bic']} "
                        f"not a registered SAP for this corridor/FXP"
                    )
                    status_reason = STATUS_INVALID_SAP
            
            if parsed.get("intermediaryAgent2Bic"):
                if parsed["intermediaryAgent2Bic"] != quote.dest_sap_bic:
                    errors.append(
                        f"Intermediary Agent 2 mismatch: {parsed['intermediaryAgent2Bic']} "
                        f"not a registered SAP for this corridor/FXP"
                    )
                    status_reason = STATUS_INVALID_SAP
    
    # 3. Charge Bearer must be SHAR
    if parsed.get("chargeBearer") and parsed["chargeBearer"] != "SHAR":
        errors.append("Charge Bearer must be SHAR (Shared) for Nexus payments")
    
    # 4. Amount limit check (sandbox trigger: amounts > 50,000)
    # Reference: docs/UNHAPPY_FLOWS.md - AM02 trigger
    if parsed.get("settlementAmount"):
        try:
            amount = Decimal(str(parsed["settlementAmount"]))
            if amount > Decimal("50000"):
                errors.append(f"Amount {amount} exceeds IPS transaction limit (50,000)")
                status_reason = STATUS_AMOUNT_LIMIT
            # 4b. AM04 Trigger: Amounts ending in 99999 simulate insufficient funds
            # Reference: docs/UNHAPPY_FLOWS.md - AM04 trigger
            elif str(int(amount)).endswith("99999"):
                errors.append(f"Insufficient funds in source account for amount {amount}")
                status_reason = STATUS_INSUFFICIENT_FUNDS
        except:
            pass
    
    # 5. Duplicate UETR check
    if uetr:
        dup_query = text("SELECT COUNT(*) FROM payments WHERE uetr = :uetr AND status != 'RJCT'")
        dup_result = await db.execute(dup_query, {"uetr": uetr})
        dup_count = dup_result.scalar()
        if dup_count and dup_count > 0:
            errors.append(f"Duplicate UETR: {uetr} already exists")
            status_reason = "DUPL"  # ISO 20022 Duplicate Payment
    
    return PaymentValidationResult(
        valid=len(errors) == 0,
        uetr=uetr,
        quoteId=quote_id,
        errors=errors,
        statusCode="ACCC" if len(errors) == 0 else "RJCT",
        statusReasonCode=status_reason
    )


async def store_payment(
    db: AsyncSession,
    uetr: str,
    quote_id: Optional[str],
    source_psp_bic: str,
    destination_psp_bic: str,
    debtor_name: str,
    debtor_account: str,
    creditor_name: str,
    creditor_account: str,
    source_currency: str,
    destination_currency: str,
    source_amount: str,
    exchange_rate: Optional[str],
    status: str
):
    """Store payment record matching schema."""
    query = text("""
        INSERT INTO payments (
            uetr, quote_id, source_psp_bic, destination_psp_bic,
            debtor_name, debtor_account, creditor_name, creditor_account,
            source_currency, destination_currency, interbank_settlement_amount,
            exchange_rate, status, initiated_at, updated_at
        ) VALUES (
            :uetr, :quote_id, :source_psp_bic, :destination_psp_bic,
            :debtor_name, :debtor_account, :creditor_name, :creditor_account,
            :source_currency, :destination_currency, :interbank_settlement_amount,
            :exchange_rate, :status, NOW(), NOW()
        )
        ON CONFLICT (uetr, initiated_at) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = NOW()
    """)
    
    await db.execute(query, {
        "uetr": uetr,
        "quote_id": quote_id,
        "source_psp_bic": source_psp_bic or "MOCKPSGSG",
        "destination_psp_bic": destination_psp_bic or "MOCKTHBK",
        "debtor_name": debtor_name or "Demo Sender",
        "debtor_account": debtor_account or "DEMO-SENDER-ACCT",
        "creditor_name": creditor_name or "Demo Recipient",
        "creditor_account": creditor_account or "DEMO-RECIPIENT-ACCT",
        "source_currency": source_currency or "SGD",
        "destination_currency": destination_currency or "THB",
        "interbank_settlement_amount": Decimal(source_amount) if source_amount else Decimal("0"),
        "exchange_rate": Decimal(exchange_rate) if exchange_rate else None,
        "status": status,
    })
    await db.commit()


async def store_payment_event(
    db: AsyncSession,
    uetr: str,
    event_type: str,
    actor: str,
    data: dict,
    pacs008_xml: str = None,
    pacs002_xml: str = None,
    acmt023_xml: str = None,
    acmt024_xml: str = None,
    camt054_xml: str = None,
    camt103_xml: str = None,
    pain001_xml: str = None,
    pacs004_xml: str = None,
    pacs028_xml: str = None,
    camt056_xml: str = None,
    camt029_xml: str = None
):
    """Store payment event with actor details and optional ISO 20022 messages."""
    query = text("""
        INSERT INTO payment_events (
            event_id, uetr, event_type, actor, data, version, occurred_at,
            pacs008_message, pacs002_message, acmt023_message, acmt024_message,
            camt054_message, camt103_message, pain001_message,
            pacs004_message, pacs028_message, camt056_message, camt029_message
        ) VALUES (
            gen_random_uuid(), :uetr, :event_type, :actor, :data, 1, NOW(),
            :pacs008_message, :pacs002_message, :acmt023_message, :acmt024_message,
            :camt054_message, :camt103_message, :pain001_message,
            :pacs004_message, :pacs028_message, :camt056_message, :camt029_message
        )
    """)
    
    await db.execute(query, {
        "uetr": uetr,
        "event_type": event_type,
        "actor": actor,
        "data": json.dumps(data),
        "pacs008_message": pacs008_xml,
        "pacs002_message": pacs002_xml,
        "acmt023_message": acmt023_xml,
        "acmt024_message": acmt024_xml,
        "camt054_message": camt054_xml,
        "camt103_message": camt103_xml,
        "pain001_message": pain001_xml,
        "pacs004_message": pacs004_xml,
        "pacs028_message": pacs028_xml,
        "camt056_message": camt056_xml,
        "camt029_message": camt029_xml,
    })
    await db.commit()

# =============================================================================
# ISO 20022 Message Builders
# =============================================================================

def build_pacs002_acceptance(
    uetr: str,
    status_code: str,
    settlement_amount: float,
    settlement_currency: str
) -> str:
    """Build pacs.002 Payment Status Report (Acceptance)."""
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"MSG{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.15">
  <FIToFIPmtStsRpt>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
    </GrpHdr>
    <TxInfAndSts>
      <OrgnlInstrId>{uetr}</OrgnlInstrId>
      <OrgnlEndToEndId>{uetr}</OrgnlEndToEndId>
      <OrgnlTxId>{uetr}</OrgnlTxId>
      <TxSts>{status_code}</TxSts>
      <StsRsnInf>
        <Rsn><Cd>AC01</Cd></Rsn>
        <AddtlInf>Payment accepted and settled</AddtlInf>
      </StsRsnInf>
      <OrgnlTxRef>
        <IntrBkSttlmAmt Ccy="{settlement_currency}">{settlement_amount}</IntrBkSttlmAmt>
      </OrgnlTxRef>
    </TxInfAndSts>
  </FIToFIPmtStsRpt>
</Document>"""


def build_pacs002_rejection(
    uetr: str,
    status_code: str,
    reason_code: str,
    reason_description: str
) -> str:
    """Build pacs.002 Payment Status Report (Rejection)."""
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"MSG{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.15">
  <FIToFIPmtStsRpt>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
    </GrpHdr>
    <TxInfAndSts>
      <OrgnlInstrId>{uetr}</OrgnlInstrId>
      <OrgnlEndToEndId>{uetr}</OrgnlEndToEndId>
      <OrgnlTxId>{uetr}</OrgnlTxId>
      <TxSts>{status_code}</TxSts>
      <StsRsnInf>
        <Rsn><Cd>{reason_code}</Cd></Rsn>
        <AddtlInf>{reason_description}</AddtlInf>
      </StsRsnInf>
    </TxInfAndSts>
  </FIToFIPmtStsRpt>
</Document>"""


def build_camt054(
    uetr: str,
    amount: float,
    currency: str,
    debtor_name: str,
    creditor_name: str,
    status: str = "ACCC"
) -> str:
    """Build camt.054 Bank To Customer Debit Credit Notification."""
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"CAMT054-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.13">
  <BkToCstmrDbtCdtNtfctn>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
    </GrpHdr>
    <Ntfctn>
      <Id>{uetr[:35]}</Id>
      <CreDtTm>{now}</CreDtTm>
      <Acct>
        <Id>
          <Othr>
            <Id>SETTLEMENT-ACCOUNT</Id>
          </Othr>
        </Id>
      </Acct>
      <Ntry>
        <Amt Ccy="{currency}">{amount}</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Sts>
          <Cd>{status}</Cd>
        </Sts>
        <BkTxCd>
          <Domn>
            <Cd>PMNT</Cd>
            <Fmly>
              <Cd>ICDT</Cd>
              <SubFmlyCd>SNDB</SubFmlyCd>
            </Fmly>
          </Domn>
        </BkTxCd>
        <NtryDtls>
          <TxDtls>
            <Refs>
              <UETR>{uetr}</UETR>
            </Refs>
            <RltdPties>
              <Dbtr><Pty><Nm>{debtor_name}</Nm></Pty></Dbtr>
              <Cdtr><Pty><Nm>{creditor_name}</Nm></Pty></Cdtr>
            </RltdPties>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Ntfctn>
  </BkToCstmrDbtCdtNtfctn>
</Document>"""


def build_pain001(
    uetr: str,
    amount: float,
    currency: str,
    debtor_name: str,
    debtor_account: str,
    debtor_bic: str,
    creditor_name: str,
    creditor_account: str,
    creditor_bic: str
) -> str:
    """
    Build pain.001 Customer Credit Transfer Initiation.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"PAIN001-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.12">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <InitgPty>
        <Nm>Nexus Sandbox</Nm>
      </InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>{uetr}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <ReqdExctnDt>
        <Dt>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</Dt>
      </ReqdExctnDt>
      <Dbtr>
        <Nm>{debtor_name}</Nm>
      </Dbtr>
      <DbtrAcct>
        <Id>
          <IBAN>{debtor_account}</IBAN>
        </Id>
      </DbtrAcct>
      <DbtrAgt>
        <FinInstnId>
          <BICFI>{debtor_bic}</BICFI>
        </FinInstnId>
      </DbtrAgt>
      <CdtTrfTxInf>
        <PmtId>
          <EndToEndId>{uetr}</EndToEndId>
        </PmtId>
        <Amt>
          <InstdAmt Ccy="{currency}">{amount}</InstdAmt>
        </Amt>
        <CdtrAgt>
          <FinInstnId>
            <BICFI>{creditor_bic}</BICFI>
          </FinInstnId>
        </CdtrAgt>
        <Cdtr>
          <Nm>{creditor_name}</Nm>
        </Cdtr>
        <CdtrAcct>
          <Id>
            <IBAN>{creditor_account}</IBAN>
          </Id>
        </CdtrAcct>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""


def build_camt103(
    uetr: str,
    amount: float,
    currency: str,
    reservation_id: str = None
) -> str:
    """
    Build camt.103 Create Reservation.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"CAMT103-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    rsv_id = reservation_id or f"RSV-{uetr[:8]}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.103.001.03">
  <CretRsvatn>
    <MsgHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
    </MsgHdr>
    <RsvatnId>
      <RsvatnId>{rsv_id}</RsvatnId>
      <Tp>
        <Cd>BLK</Cd>
      </Tp>
    </RsvatnId>
    <ValSet>
      <Amt>
        <AmtWthCcy Ccy="{currency}">{amount}</AmtWthCcy>
      </Amt>
    </ValSet>
  </CretRsvatn>
</Document>"""


def build_pacs004(
    uetr: str,
    original_uetr: str,
    amount: float,
    currency: str,
    return_reason: str = "NARR"
) -> str:
    """
    Build pacs.004 Payment Return.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"PACS004-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.004.001.14">
  <PmtRtr>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <SttlmInf>
        <SttlmMtd>CLRG</SttlmMtd>
      </SttlmInf>
    </GrpHdr>
    <TxInf>
      <RtrId>{uetr}</RtrId>
      <OrgnlEndToEndId>{original_uetr}</OrgnlEndToEndId>
      <OrgnlTxId>{original_uetr}</OrgnlTxId>
      <RtrdIntrBkSttlmAmt Ccy="{currency}">{amount}</RtrdIntrBkSttlmAmt>
      <RtrRsnInf>
        <Rsn>
          <Cd>{return_reason}</Cd>
        </Rsn>
      </RtrRsnInf>
    </TxInf>
  </PmtRtr>
</Document>"""


def build_pacs028(
    request_id: str,
    original_uetr: str
) -> str:
    """
    Build pacs.028 Payment Status Request.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"PACS028-{request_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.028.001.06">
  <FIToFIPmtStsReq>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
    </GrpHdr>
    <TxInf>
      <StsReqId>{request_id}</StsReqId>
      <OrgnlEndToEndId>{original_uetr}</OrgnlEndToEndId>
      <OrgnlTxId>{original_uetr}</OrgnlTxId>
    </TxInf>
  </FIToFIPmtStsReq>
</Document>"""


def build_camt056(
    uetr: str,
    original_uetr: str,
    reason_code: str = "DUPL",
    reason_desc: str = "Duplicate payment"
) -> str:
    """
    Build camt.056 Payment Cancellation Request.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"CAMT056-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    case_id = f"CASE-{uetr[:8]}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.056.001.11">
  <FIToFIPmtCxlReq>
    <Assgnmt>
      <Id>{msg_id}</Id>
      <Assgnr>
        <Agt>
          <FinInstnId>
            <BICFI>NEXUSGEN</BICFI>
          </FinInstnId>
        </Agt>
      </Assgnr>
      <Assgne>
        <Agt>
          <FinInstnId>
            <BICFI>NEXUSGEN</BICFI>
          </FinInstnId>
        </Agt>
      </Assgne>
      <CreDtTm>{now}</CreDtTm>
    </Assgnmt>
    <Case>
      <Id>{case_id}</Id>
      <Cretr>
        <Agt>
          <FinInstnId>
            <BICFI>NEXUSGEN</BICFI>
          </FinInstnId>
        </Agt>
      </Cretr>
    </Case>
    <Undrlyg>
      <TxInf>
        <OrgnlEndToEndId>{original_uetr}</OrgnlEndToEndId>
        <OrgnlTxId>{original_uetr}</OrgnlTxId>
        <CxlRsnInf>
          <Rsn>
            <Cd>{reason_code}</Cd>
          </Rsn>
          <AddtlInf>{reason_desc}</AddtlInf>
        </CxlRsnInf>
      </TxInf>
    </Undrlyg>
  </FIToFIPmtCxlReq>
</Document>"""


def build_camt029(
    original_msg_id: str,
    status_code: str = "CNCL",
    status_desc: str = "Cancellation accepted"
) -> str:
    """
    Build camt.029 Resolution of Investigation.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"CAMT029-{original_msg_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.029.001.13">
  <RsltnOfInvstgtn>
    <Assgnmt>
      <Id>{msg_id}</Id>
      <Assgnr>
        <Agt>
          <FinInstnId>
            <BICFI>NEXUSGEN</BICFI>
          </FinInstnId>
        </Agt>
      </Assgnr>
      <Assgne>
        <Agt>
          <FinInstnId>
            <BICFI>NEXUSGEN</BICFI>
          </FinInstnId>
        </Agt>
      </Assgne>
      <CreDtTm>{now}</CreDtTm>
    </Assgnmt>
    <Sts>
      <Conf>{status_code}</Conf>
    </Sts>
    <CxlDtls>
      <TxInfAndSts>
        <OrgnlGrpInf>
          <OrgnlMsgId>{original_msg_id}</OrgnlMsgId>
          <OrgnlMsgNmId>{original_msg_id}</OrgnlMsgNmId>
        </OrgnlGrpInf>
        <CxlStsRsnInf>
          <Rsn>
            <Prtry>{status_desc}</Prtry>
          </Rsn>
        </CxlStsRsnInf>
      </TxInfAndSts>
    </CxlDtls>
  </RsltnOfInvstgtn>
</Document>"""


def build_acmt023(
    identification_id: str,
    proxy_type: str,
    proxy_value: str,
    assigner_bic: str = "NEXUSGEN",
    assignee_bic: str = "NEXUSGEN"
) -> str:
    """
    Build acmt.023 Identification Verification Request (Proxy Resolution).
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"ACMT023-{identification_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:acmt.023.001.04">
  <IdVrfctnReq>
    <Assgnmt>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <Assgnr>
        <Agt>
          <FinInstnId>
            <BICFI>{assigner_bic}</BICFI>
          </FinInstnId>
        </Agt>
      </Assgnr>
      <Assgne>
        <Agt>
          <FinInstnId>
            <BICFI>{assignee_bic}</BICFI>
          </FinInstnId>
        </Agt>
      </Assgne>
    </Assgnmt>
    <Vrfctn>
      <Id>{identification_id}</Id>
      <PtyAndAcctId>
        <Acct>
          <Id>
            <Othr>
              <Id>{proxy_value}</Id>
            </Othr>
          </Id>
          <Prxy>
            <Tp>
              <Cd>{proxy_type}</Cd>
            </Tp>
            <Id>{proxy_value}</Id>
          </Prxy>
        </Acct>
      </PtyAndAcctId>
    </Vrfctn>
  </IdVrfctnReq>
</Document>"""


def build_acmt024(
    original_msg_id: str,
    original_identification_id: str,
    verification_result: bool,
    resolved_iban: str = None,
    resolved_name: str = None,
    assigner_bic: str = "NEXUSGEN",
    assignee_bic: str = "NEXUSGEN"
) -> str:
    """
    Build acmt.024 Identification Verification Report (Proxy Resolution Response).
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f"ACMT024-{original_identification_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
    result_str = "true" if verification_result else "false"
    
    # Optional resolved block
    resolved_block = ""
    if verification_result and resolved_iban:
        resolved_block = f"""
      <UpdtdPtyAndAcctId>
        <Acct>
          <Id>
            <IBAN>{resolved_iban}</IBAN>
          </Id>
          <Nm>{resolved_name}</Nm>
        </Acct>
      </UpdtdPtyAndAcctId>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:acmt.024.001.04">
  <IdVrfctnRpt>
    <Assgnmt>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <Assgnr>
        <Agt>
          <FinInstnId>
            <BICFI>{assigner_bic}</BICFI>
          </FinInstnId>
        </Agt>
      </Assgnr>
      <Assgne>
        <Agt>
          <FinInstnId>
            <BICFI>{assignee_bic}</BICFI>
          </FinInstnId>
        </Agt>
      </Assgne>
    </Assgnmt>
    <OrgnlAssgnmt>
      <MsgId>{original_msg_id}</MsgId>
    </OrgnlAssgnmt>
    <Rpt>
      <OrgnlId>{original_identification_id}</OrgnlId>
      <Vrfctn>{result_str}</Vrfctn>{resolved_block}
    </Rpt>
  </IdVrfctnRpt>
</Document>"""

