"""
pacs.002 Callback Delivery Module

Handles asynchronous delivery of ISO 20022 pacs.002 status reports
to the callback endpoints registered by Source IPS during pacs.008 submission.
"""

import httpx
import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

# pacs.002 XML Template
PACS002_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.10">
  <FIToFIPmtStsRpt>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{creation_datetime}</CreDtTm>
    </GrpHdr>
    <TxInfAndSts>
      <OrgnlEndToEndId>{uetr}</OrgnlEndToEndId>
      <TxSts>{status}</TxSts>
      <StsRsnInf>
        <Rsn>
          <Cd>{reason_code}</Cd>
        </Rsn>
        <AddtlInf>{additional_info}</AddtlInf>
      </StsRsnInf>
      <OrgnlTxRef>
        <IntrBkSttlmAmt Ccy="{currency}">{amount}</IntrBkSttlmAmt>
      </OrgnlTxRef>
    </TxInfAndSts>
  </FIToFIPmtStsRpt>
</Document>'''


def generate_pacs002_xml(
    uetr: str,
    status: str,  # ACCC (accepted) or RJCT (rejected)
    reason_code: Optional[str] = None,
    additional_info: Optional[str] = None,
    currency: str = "USD",
    amount: str = "0.00"
) -> str:
    """Generate ISO 20022 pacs.002 Payment Status Report XML."""
    
    msg_id = f"PSR{uuid4().hex[:12].upper()}"
    creation_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    return PACS002_TEMPLATE.format(
        msg_id=msg_id,
        creation_datetime=creation_datetime,
        uetr=uetr,
        status=status,
        reason_code=reason_code or ("" if status == "ACCC" else "NARR"),
        additional_info=additional_info or "",
        currency=currency,
        amount=amount
    )


async def deliver_pacs002_callback(
    callback_url: str,
    uetr: str,
    status: str,
    reason_code: Optional[str] = None,
    additional_info: Optional[str] = None,
    currency: str = "USD",
    amount: str = "0.00",
    max_retries: int = 3
) -> bool:
    """
    Deliver pacs.002 status report to the registered callback endpoint.
    
    Args:
        callback_url: The pacs002Endpoint registered during pacs.008 submission
        uetr: Universal End-to-End Transaction Reference
        status: ACCC (accepted) or RJCT (rejected)
        reason_code: ISO 20022 ExternalStatusReason1Code (e.g., BE23, AM04)
        additional_info: Human-readable description
        max_retries: Number of retry attempts
        
    Returns:
        True if delivery successful, False otherwise
    """
    
    if not callback_url:
        logger.warning(f"No callback URL for UETR {uetr}, skipping pacs.002 delivery")
        return False
    
    pacs002_xml = generate_pacs002_xml(
        uetr=uetr,
        status=status,
        reason_code=reason_code,
        additional_info=additional_info,
        currency=currency,
        amount=amount
    )
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    callback_url,
                    content=pacs002_xml,
                    headers={
                        "Content-Type": "application/xml",
                        "X-UETR": uetr,
                        "X-Message-Type": "pacs.002",
                        "X-Transaction-Status": status,
                    }
                )
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"pacs.002 delivered for {uetr}: {status} -> {callback_url}")
                    return True
                else:
                    logger.warning(f"pacs.002 delivery failed for {uetr}: HTTP {response.status_code}")
                    
        except Exception as e:
            logger.error(f"pacs.002 delivery error for {uetr} (attempt {attempt + 1}): {e}")
            
        # Wait before retry
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return False


async def schedule_pacs002_delivery(
    callback_url: str,
    uetr: str,
    status: str,
    reason_code: Optional[str] = None,
    additional_info: Optional[str] = None,
    delay_seconds: float = 0.5
):
    """
    Schedule pacs.002 delivery as background task with optional delay.
    Simulates realistic async processing time.
    """
    await asyncio.sleep(delay_seconds)
    await deliver_pacs002_callback(
        callback_url=callback_url,
        uetr=uetr,
        status=status,
        reason_code=reason_code,
        additional_info=additional_info
    )


# Error code descriptions for frontend display
ERROR_CODE_DESCRIPTIONS = {
    "ACCC": "Accepted Settlement Completed",
    "AB04": "Quote expired - exchange rate guarantee lapsed",
    "AM02": "Amount exceeds IPS transaction limit",
    "AM04": "Insufficient funds in debtor account",
    "AC04": "Closed account - recipient account has been closed",
    "BE23": "Account/Proxy invalid - not registered in PDO",
    "RR04": "Regulatory block - AML/CFT screening failed",
    "RC11": "Invalid SAP - settlement access provider not registered",
    "DUPL": "Duplicate payment - UETR already exists",
    "AGNT": "Agent incorrect - PSP not onboarded to Nexus",
    "FF05": "Invalid currency for corridor",
    "NARR": "Narrative - see additional information",
}


def get_error_description(code: str) -> str:
    """Get human-readable description for ISO 20022 status reason code."""
    return ERROR_CODE_DESCRIPTIONS.get(code, f"Unknown error code: {code}")
