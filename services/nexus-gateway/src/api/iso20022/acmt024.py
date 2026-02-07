"""
acmt.024 - Identification Verification Report

This module handles the proxy resolution reports provided by a Destination PDO
responding to an acmt.023 request.

Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-acmt.024-identification-verification-report
"""
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from uuid import uuid4
import logging

from ...db import get_db
from .. import validation as xsd_validation
from ..schemas import Acmt024Response
from .utils import store_payment_event

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/acmt024",
    response_model=Acmt024Response,
    summary="Submit acmt.024 resolution report",
    description="""
    Accepts an ISO 20022 acmt.024 (Identification Verification Report) message
    providing details of a resolved proxy or account.
    
    Used in Step 9 of the payment flow when the Destination PDO responds
    to an acmt.023 request.
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
    
    # Parse ISO 20022 fields per documentation
    # XPath: /Document/IdVrfctnRpt/Rpt/Vrfctn for true/false
    # XPath: /Document/IdVrfctnRpt/Rpt/UpdtdPtyAndAcctId/Pty/Nm for party name
    # XPath: /Document/IdVrfctnRpt/Rpt/UpdtdPtyAndAcctId/Acct/Nm for display name
    # XPath: /Document/IdVrfctnRpt/Rpt/Rsn/Cd for error code
    try:
        from lxml import etree
        root = etree.fromstring(xml_content.encode())
        ns = {"doc": "urn:iso:std:iso:20022:tech:xsd:acmt.024.001.04"}
        
        def get_text(xpath, default=None):
            elements = root.xpath(xpath, namespaces=ns)
            if elements:
                return elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
            # Try without namespace  
            simple_xpath = xpath.replace('doc:', '')
            elements = root.xpath(simple_xpath)
            if elements:
                return elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
            return default
        
        parsed_fields = {
            "messageId": get_text(".//doc:MsgId") or get_text(".//MsgId"),
            "originalId": get_text(".//doc:OrgnlId") or get_text(".//OrgnlId"),
            "verificationResult": get_text(".//doc:Vrfctn") or get_text(".//Vrfctn"),
            "reasonCode": get_text(".//doc:Rsn/doc:Cd") or get_text(".//Rsn/Cd"),
            # Party and account details
            "partyName": get_text(".//doc:UpdtdPtyAndAcctId/doc:Pty/doc:Nm") or get_text(".//UpdtdPtyAndAcctId/Pty/Nm"),
            "accountName": get_text(".//doc:UpdtdPtyAndAcctId/doc:Acct/doc:Nm") or get_text(".//UpdtdPtyAndAcctId/Acct/Nm"),
            "accountId": get_text(".//doc:UpdtdPtyAndAcctId/doc:Acct/doc:Id/doc:Othr/doc:Id") or get_text(".//UpdtdPtyAndAcctId/Acct/Id/Othr/Id"),
            "iban": get_text(".//doc:UpdtdPtyAndAcctId/doc:Acct/doc:Id/doc:IBAN") or get_text(".//UpdtdPtyAndAcctId/Acct/Id/IBAN"),
            "agentBic": get_text(".//doc:UpdtdPtyAndAcctId/doc:Agt/doc:FinInstnId/doc:BICFI") or get_text(".//UpdtdPtyAndAcctId/Agt/FinInstnId/BICFI"),
        }
        
        logger.info(f"Parsed acmt.024: {parsed_fields}")
        
        # Determine status based on verification result
        verification_passed = parsed_fields.get("verificationResult", "").lower() == "true"
        display_name = parsed_fields.get("accountName") or parsed_fields.get("partyName") or "REDACTED"
        
    except Exception as e:
        logger.warning(f"Failed to parse acmt.024 fields: {e}")
        parsed_fields = {}
        verification_passed = False
        display_name = "REDACTED"
    
    return Acmt024Response(
        requestId=request_id,
        status="VERIFIED" if verification_passed else "FAILED",
        debtorNameMasked=display_name,
        processedAt=processed_at.isoformat()
    )
