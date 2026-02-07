"""
Recall and Investigation Handlers

Handles ISO 20022 camt.056 (Payment Cancellation Request) and
camt.029 (Resolution of Investigation) messages.

Currently future/roadmap items for Release 1 - use Service Desk for recall.

Reference: https://docs.nexusglobalpayments.org/payment-processing/recall-and-return
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from uuid import uuid4
from lxml import etree
import logging

from ...db import get_db
from .. import validation as xsd_validation
from ..schemas import Camt056Response, Camt029Response
from .utils import store_payment_event

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# XML Extraction Helpers
# =============================================================================

def _extract_original_uetr_from_camt056(xml_content: str) -> str:
    """Extract OrgnlUETR from camt.056 XML document.
    
    Searches for OrgnlUETR in the Undrlyg/TxInf section.
    """
    try:
        root = etree.fromstring(xml_content.encode())
        ns = {'doc': 'urn:iso:std:iso:20022:tech:xsd:camt.056.001.11'}
        
        # Try namespaced paths
        for xpath in [
            './/doc:OrgnlUETR',
            './/doc:Undrlyg/doc:TxInf/doc:OrgnlUETR',
            './/doc:OrgnlGrpInf/doc:OrgnlMsgId',
        ]:
            elements = root.xpath(xpath, namespaces=ns)
            if elements and elements[0].text:
                return elements[0].text
        
        # Fallback without namespace
        for xpath in ['.//OrgnlUETR', './/Undrlyg/TxInf/OrgnlUETR']:
            elements = root.xpath(xpath)
            if elements and elements[0].text:
                return elements[0].text
        
        return f"UNKNOWN-{uuid4().hex[:8]}"
    except Exception:
        return f"UNKNOWN-{uuid4().hex[:8]}"


def _extract_recall_id_from_camt029(xml_content: str) -> str:
    """Extract the recall reference from camt.029 XML document.
    
    Searches for CxlStsId (Cancellation Status Identification) or
    the original message reference.
    """
    try:
        root = etree.fromstring(xml_content.encode())
        ns = {'doc': 'urn:iso:std:iso:20022:tech:xsd:camt.029.001.13'}
        
        # Try namespaced paths for recall reference
        for xpath in [
            './/doc:CxlStsId',
            './/doc:RslvdCase/doc:Id',
            './/doc:Assgnmt/doc:Id',
            './/doc:OrgnlGrpInf/doc:OrgnlMsgId',
        ]:
            elements = root.xpath(xpath, namespaces=ns)
            if elements and elements[0].text:
                return elements[0].text
        
        # Fallback without namespace
        for xpath in ['.//CxlStsId', './/RslvdCase/Id', './/Assgnmt/Id']:
            elements = root.xpath(xpath)
            if elements and elements[0].text:
                return elements[0].text
        
        return f"UNKNOWN-{uuid4().hex[:8]}"
    except Exception:
        return f"UNKNOWN-{uuid4().hex[:8]}"


# =============================================================================
# Endpoints
# =============================================================================

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
    
    # Extract original UETR from parsed XML
    original_uetr = _extract_original_uetr_from_camt056(xml_content)
    logger.info(f"camt.056 recall request received for original UETR: {original_uetr}")
    
    # Store recall event for audit trail
    await store_payment_event(
        db=db,
        uetr=original_uetr,
        event_type="RECALL_REQUEST_RECEIVED",
        actor="NEXUS",
        data={
            "recallId": recall_id,
            "messageType": "camt.056",
            "note": "Future - use Service Desk for Release 1"
        },
        camt056_xml=xml_content
    )
    
    return Camt056Response(
        recallId=recall_id,
        originalUetr=original_uetr,
        status="ACCEPTED",
        message="Recall request acknowledged (Future - use Service Desk for Release 1)",
        processedAt=processed_at.isoformat()
    )


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
    
    # Extract recall reference from parsed XML
    recall_ref = _extract_recall_id_from_camt029(xml_content)
    logger.info(f"camt.029 resolution received for recall: {recall_ref}")
    
    # Store resolution event for audit trail
    await store_payment_event(
        db=db,
        uetr=recall_ref,
        event_type="RECALL_RESOLUTION_RECEIVED",
        actor="NEXUS",
        data={
            "resolutionId": resolution_id,
            "messageType": "camt.029",
            "note": "Future - use Service Desk for Release 1"
        },
        camt029_xml=xml_content
    )
    
    return Camt029Response(
        resolutionId=resolution_id,
        recallId=recall_ref,
        status="RECEIVED",
        resolution="PENDING_REVIEW",
        message="Resolution of investigation received (Future - use Service Desk for Release 1)",
        processedAt=processed_at.isoformat()
    )
