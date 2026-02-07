"""
acmt.023 - Identification Verification Request

This module handles proxy-to-account resolution requests where a Source PSP 
needs to resolve a proxy (e.g., mobile number, email) to a bank account ID.

Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-acmt.023-identification-verification-request
"""
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from uuid import uuid4
import logging

from ...db import get_db
from .. import validation as xsd_validation
from ..schemas import Acmt023Response
from .utils import store_payment_event

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/acmt023",
    response_model=Acmt023Response,
    summary="Submit acmt.023 resolution request",
    description="""
    Accepts an ISO 20022 acmt.023 (Identification Verification Request) message
    for proxy or account resolution.
    
    Used in Steps 7-9 of the payment flow when the Source PSP needs to
    resolve a proxy (mobile number, email) to an account number.
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
    
    # Step 2: Parse ISO 20022 fields per documentation
    # XPath: /Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Prxy/Tp/Cd for proxy type
    # XPath: /Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Prxy/Id for proxy value
    # XPath: /Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Id/IBAN for IBAN
    # XPath: /Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Id/Othr/Id for account number
    try:
        from lxml import etree
        root = etree.fromstring(xml_content.encode())
        ns = {"doc": "urn:iso:std:iso:20022:tech:xsd:acmt.023.001.03"}
        
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
            "creationDateTime": get_text(".//doc:CreDtTm") or get_text(".//CreDtTm"),
            # Proxy resolution fields (per documentation paths)
            "proxyType": get_text(".//doc:Prxy/doc:Tp/doc:Cd") or get_text(".//Prxy/Tp/Cd"),
            "proxyValue": get_text(".//doc:Prxy/doc:Id") or get_text(".//Prxy/Id"),
            # Account resolution fields  
            "iban": get_text(".//doc:Acct/doc:Id/doc:IBAN") or get_text(".//Acct/Id/IBAN"),
            "accountId": get_text(".//doc:Acct/doc:Id/doc:Othr/doc:Id") or get_text(".//Acct/Id/Othr/Id"),
            # Destination info
            "destinationPspBic": get_text(".//doc:Agt/doc:FinInstnId/doc:BICFI") or get_text(".//Agt/FinInstnId/BICFI"),
        }
        
        logger.info(f"Parsed acmt.023: {parsed_fields}")
        
    except Exception as e:
        logger.warning(f"Failed to parse acmt.023 fields: {e}")
        parsed_fields = {}
    
    # For sandbox: Accept and acknowledge
    # In production: Parse XML, route to PDO, wait for acmt.024
    
    return Acmt023Response(
        requestId=request_id,
        status="ACCEPTED",
        callbackEndpoint=acmt024_endpoint,
        processedAt=processed_at.isoformat()
    )
