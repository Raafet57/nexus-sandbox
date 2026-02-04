from datetime import datetime, timezone
import sys
def build_pacs002_acceptance(uetr: str, status_code: str, settlement_amount: float, settlement_currency: str) -> str:
    """Build pacs.002 Payment Status Report (Acceptance)."""
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'MSG{int(datetime.now(timezone.utc).timestamp() * 1000)}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.15">\n  <FIToFIPmtStsRpt>\n    <GrpHdr>\n      <MsgId>{msg_id}</MsgId>\n      <CreDtTm>{now}</CreDtTm>\n    </GrpHdr>\n    <TxInfAndSts>\n      <OrgnlInstrId>{uetr}</OrgnlInstrId>\n      <OrgnlEndToEndId>{uetr}</OrgnlEndToEndId>\n      <OrgnlTxId>{uetr}</OrgnlTxId>\n      <TxSts>{status_code}</TxSts>\n      <StsRsnInf>\n        <Rsn><Cd>AC01</Cd></Rsn>\n        <AddtlInf>Payment accepted and settled</AddtlInf>\n      </StsRsnInf>\n      <OrgnlTxRef>\n        <IntrBkSttlmAmt Ccy="{settlement_currency}">{settlement_amount}</IntrBkSttlmAmt>\n      </OrgnlTxRef>\n    </TxInfAndSts>\n  </FIToFIPmtStsRpt>\n</Document>'

def build_pacs002_rejection(uetr: str, status_code: str, reason_code: str, reason_description: str) -> str:
    """Build pacs.002 Payment Status Report (Rejection)."""
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'MSG{int(datetime.now(timezone.utc).timestamp() * 1000)}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.15">\n  <FIToFIPmtStsRpt>\n    <GrpHdr>\n      <MsgId>{msg_id}</MsgId>\n      <CreDtTm>{now}</CreDtTm>\n    </GrpHdr>\n    <TxInfAndSts>\n      <OrgnlInstrId>{uetr}</OrgnlInstrId>\n      <OrgnlEndToEndId>{uetr}</OrgnlEndToEndId>\n      <OrgnlTxId>{uetr}</OrgnlTxId>\n      <TxSts>{status_code}</TxSts>\n      <StsRsnInf>\n        <Rsn><Cd>{reason_code}</Cd></Rsn>\n        <AddtlInf>{reason_description}</AddtlInf>\n      </StsRsnInf>\n    </TxInfAndSts>\n  </FIToFIPmtStsRpt>\n</Document>'

def build_camt054(uetr: str, amount: float, currency: str, debtor_name: str, creditor_name: str, status: str='ACCC') -> str:
    """Build camt.054 Bank To Customer Debit Credit Notification."""
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'CAMT054-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.13">\n  <BkToCstmrDbtCdtNtfctn>\n    <GrpHdr>\n      <MsgId>{msg_id}</MsgId>\n      <CreDtTm>{now}</CreDtTm>\n    </GrpHdr>\n    <Ntfctn>\n      <Id>{uetr}</Id>\n      <CreDtTm>{now}</CreDtTm>\n      <Acct>\n        <Id>\n          <Othr>\n            <Id>SETTLEMENT-ACCOUNT</Id>\n          </Othr>\n        </Id>\n      </Acct>\n      <Ntry>\n        <Amt Ccy="{currency}">{amount}</Amt>\n        <CdtDbtInd>CRDT</CdtDbtInd>\n        <Sts>\n          <Cd>{status}</Cd>\n        </Sts>\n        <BkTxCd>\n          <Domn>\n            <Cd>PMNT</Cd>\n            <Fmly>\n              <Cd>ICDT</Cd>\n              <SubFmlyCd>SNDB</SubFmlyCd>\n            </Fmly>\n          </Domn>\n        </BkTxCd>\n        <NtryDtls>\n          <TxDtls>\n            <Refs>\n              <UETR>{uetr}</UETR>\n            </Refs>\n            <RltdPties>\n              <Dbtr><Nm>{debtor_name}</Nm></Dbtr>\n              <Cdtr><Nm>{creditor_name}</Nm></Cdtr>\n            </RltdPties>\n          </TxDtls>\n        </NtryDtls>\n      </Ntry>\n    </Ntfctn>\n  </BkToCstmrDbtCdtNtfctn>\n</Document>'

def build_pain001(uetr: str, amount: float, currency: str, debtor_name: str, debtor_account: str, debtor_bic: str, creditor_name: str, creditor_account: str, creditor_bic: str) -> str:
    """
    Build pain.001 Customer Credit Transfer Initiation.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'PAIN001-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    return f"""<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.12">\n  <CstmrCdtTrfInitn>\n    <GrpHdr>\n      <MsgId>{{msg_id}}</MsgId>\n      <CreDtTm>{{now}}</CreDtTm>\n      <NbOfTxs>1</NbOfTxs>\n      <InitgPty>\n        <Nm>Nexus Sandbox</Nm>\n      </InitgPty>\n    </GrpHdr>\n    <PmtInf>\n      <PmtInfId>{{uetr}}</PmtInfId>\n      <PmtMtd>TRF</PmtMtd>\n      <ReqdExctnDt>{{datetime.now(timezone.utc).strftime('%Y-%m-%d')}}</ReqdExctnDt>\n      <Dbtr>\n        <Nm>{{debtor_name}}</Nm>\n      </Dbtr>\n      <DbtrAcct>\n        <Id>\n          <IBAN>{{debtor_account}}</IBAN>\n        </Id>\n      </DbtrAcct>\n      <DbtrAgt>\n        <FinInstnId>\n          <BICFI>{{debtor_bic}}</BICFI>\n        </FinInstnId>\n      </DbtrAgt>\n      <CdtTrfTxInf>\n        <PmtId>\n          <EndToEndId>{{uetr}}</EndToEndId>\n        </PmtId>\n        <Amt>\n          <InstdAmt Ccy="{{currency}}">{{amount}}</InstdAmt>\n        </Amt>\n        <CdtrAgt>\n          <FinInstnId>\n            <BICFI>{{creditor_bic}}</BICFI>\n          </FinInstnId>\n        </CdtrAgt>\n        <Cdtr>\n          <Nm>{{creditor_name}}</Nm>\n        </Cdtr>\n        <CdtrAcct>\n          <Id>\n            <IBAN>{{creditor_account}}</IBAN>\n          </Id>\n        </CdtrAcct>\n      </CdtTrfTxInf>\n    </PmtInf>\n  </CstmrCdtTrfInitn>\n</Document>"""

def build_camt103(uetr: str, amount: float, currency: str, reservation_id: str=None) -> str:
    """
    Build camt.103 Create Reservation.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'CAMT103-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    rsv_id = reservation_id or f'RSV-{uetr[:8]}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.103.001.03">\n  <CretRsvatn>\n    <MsgHdr>\n      <MsgId>{{msg_id}}</MsgId>\n      <CreDtTm>{{now}}</CreDtTm>\n    </MsgHdr>\n    <RsvatnId>\n      <RsvatnId>{{rsv_id}}</RsvatnId>\n    </RsvatnId>\n    <ValSet>\n      <Amt>\n        <AmtWthCcy Ccy="{{currency}}">{{amount}}</AmtWthCcy>\n      </Amt>\n    </ValSet>\n  </CretRsvatn>\n</Document>'

def build_pacs004(uetr: str, original_uetr: str, amount: float, currency: str, return_reason: str='NARR') -> str:
    """
    Build pacs.004 Payment Return.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'PACS004-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.004.001.14">\n  <PmtRtr>\n    <GrpHdr>\n      <MsgId>{{msg_id}}</MsgId>\n      <CreDtTm>{{now}}</CreDtTm>\n      <NbOfTxs>1</NbOfTxs>\n      <InitgPty>\n        <Nm>Nexus Sandbox</Nm>\n      </InitgPty>\n    </GrpHdr>\n    <TxInf>\n      <RtrId>{{uetr}}</RtrId>\n      <OrgnlEndToEndId>{{original_uetr}}</OrgnlEndToEndId>\n      <OrgnlTxId>{{original_uetr}}</OrgnlTxId>\n      <RtrdIntrBkSttlmAmt Ccy="{{currency}}">{{amount}}</RtrdIntrBkSttlmAmt>\n      <RtrRsnInf>\n        <Rsn>\n          <Cd>{{return_reason}}</Cd>\n        </Rsn>\n      </RtrRsnInf>\n    </TxInf>\n  </PmtRtr>\n</Document>'

def build_pacs028(request_id: str, original_uetr: str) -> str:
    """
    Build pacs.028 Payment Status Request.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'PACS028-{request_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.028.001.06">\n  <FIToFIPmtStsReq>\n    <GrpHdr>\n      <MsgId>{{msg_id}}</MsgId>\n      <CreDtTm>{{now}}</CreDtTm>\n    </GrpHdr>\n    <TxInf>\n      <StsReqId>{{request_id}}</StsReqId>\n      <OrgnlEndToEndId>{{original_uetr}}</OrgnlEndToEndId>\n      <OrgnlTxId>{{original_uetr}}</OrgnlTxId>\n    </TxInf>\n  </FIToFIPmtStsReq>\n</Document>'

def build_camt056(uetr: str, original_uetr: str, reason_code: str='DUPL', reason_desc: str='Duplicate payment') -> str:
    """
    Build camt.056 Payment Cancellation Request.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'CAMT056-{uetr[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    case_id = f'CASE-{uetr[:8]}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.056.001.11">\n  <FIToFIPmtCxlReq>\n    <Assgnmt>\n      <Id>{{msg_id}}</Id>\n      <Assgnr>\n        <Agt>\n          <FinInstnId>\n            <BICFI>NEXUSGENERIC</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgnr>\n      <Assgne>\n        <Agt>\n          <FinInstnId>\n            <BICFI>NEXUSGENERIC</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgne>\n      <CreDtTm>{{now}}</CreDtTm>\n    </Assgnmt>\n    <Case>\n      <Id>{{case_id}}</Id>\n      <Cretr>\n        <Agt>\n          <FinInstnId>\n            <BICFI>NEXUSGENERIC</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Cretr>\n    </Case>\n    <Undrlyg>\n      <TxInf>\n        <OrgnlEndToEndId>{{original_uetr}}</OrgnlEndToEndId>\n        <OrgnlTxId>{{original_uetr}}</OrgnlTxId>\n        <CxlRsnInf>\n          <Rsn>\n            <Cd>{{reason_code}}</Cd>\n          </Rsn>\n          <AddtlInf>{{reason_desc}}</AddtlInf>\n        </CxlRsnInf>\n      </TxInf>\n    </Undrlyg>\n  </FIToFIPmtCxlReq>\n</Document>'

def build_camt029(original_msg_id: str, status_code: str='CNCL', status_desc: str='Cancellation accepted') -> str:
    """
    Build camt.029 Resolution of Investigation.
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'CAMT029-{original_msg_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.029.001.13">\n  <RsltnOfInvstgtn>\n    <Assgnmt>\n      <Id>{{msg_id}}</Id>\n      <Assgnr>\n        <Agt>\n          <FinInstnId>\n            <BICFI>NEXUSGENERIC</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgnr>\n      <Assgne>\n        <Agt>\n          <FinInstnId>\n            <BICFI>NEXUSGENERIC</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgne>\n      <CreDtTm>{{now}}</CreDtTm>\n    </Assgnmt>\n    <Sts>\n      <Conf>\n        <Cd>{{status_code}}</Cd>\n      </Conf>\n    </Sts>\n    <CxlDtls>\n      <TxInfAndSts>\n        <OrgnlGrpInf>\n          <OrgnlMsgId>{{original_msg_id}}</OrgnlMsgId>\n        </OrgnlGrpInf>\n        <CxlStsRsnInf>\n          <Rsn>\n            <Prtry>{{status_desc}}</Prtry>\n          </Rsn>\n        </CxlStsRsnInf>\n      </TxInfAndSts>\n    </CxlDtls>\n  </RsltnOfInvstgtn>\n</Document>'

def build_acmt023(identification_id: str, proxy_type: str, proxy_value: str, assigner_bic: str='NEXUSGENERIC', assignee_bic: str='NEXUSGENERIC') -> str:
    """
    Build acmt.023 Identification Verification Request (Proxy Resolution).
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'ACMT023-{identification_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:acmt.023.001.04">\n  <IdVrfctnReq>\n    <Assgnmt>\n      <MsgId>{{msg_id}}</MsgId>\n      <CreDtTm>{{now}}</CreDtTm>\n      <Assgnr>\n        <Agt>\n          <FinInstnId>\n            <BICFI>{{assigner_bic}}</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgnr>\n      <Assgne>\n        <Agt>\n          <FinInstnId>\n            <BICFI>{{assignee_bic}}</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgne>\n    </Assgnmt>\n    <Vrfctn>\n      <Id>{{identification_id}}</Id>\n      <PtyAndAcctId>\n        <Acct>\n          <Id>\n            <Othr>\n              <Id>{{proxy_value}}</Id>\n            </Othr>\n          </Id>\n          <Prxy>\n            <Tp>\n              <Cd>{{proxy_type}}</Cd>\n            </Tp>\n            <Id>{{proxy_value}}</Id>\n          </Prxy>\n        </Acct>\n      </PtyAndAcctId>\n    </Vrfctn>\n  </IdVrfctnReq>\n</Document>'

def build_acmt024(original_msg_id: str, original_identification_id: str, verification_result: bool, resolved_iban: str=None, resolved_name: str=None, assigner_bic: str='NEXUSGENERIC', assignee_bic: str='NEXUSGENERIC') -> str:
    """
    Build acmt.024 Identification Verification Report (Proxy Resolution Response).
    """
    now = datetime.now(timezone.utc).isoformat()
    msg_id = f'ACMT024-{original_identification_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}'
    result_str = 'true' if verification_result else 'false'
    resolved_block = ''
    if verification_result and resolved_iban:
        resolved_block = f'\n      <UpdtdPtyAndAcctId>\n        <Acct>\n          <Id>\n            <IBAN>{{resolved_iban}}</IBAN>\n          </Id>\n          <Nm>{{resolved_name}}</Nm>\n        </Acct>\n      </UpdtdPtyAndAcctId>'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:acmt.024.001.04">\n  <IdVrfctnRpt>\n    <Assgnmt>\n      <MsgId>{{msg_id}}</MsgId>\n      <CreDtTm>{{now}}</CreDtTm>\n      <Assgnr>\n        <Agt>\n          <FinInstnId>\n            <BICFI>{{assigner_bic}}</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgnr>\n      <Assgne>\n        <Agt>\n          <FinInstnId>\n            <BICFI>{{assignee_bic}}</BICFI>\n          </FinInstnId>\n        </Agt>\n      </Assgne>\n    </Assgnmt>\n    <OrgnlAssgnmt>\n      <MsgId>{{original_msg_id}}</MsgId>\n    </OrgnlAssgnmt>\n    <Rpt>\n      <OrgnlId>{{original_identification_id}}</OrgnlId>\n      <Vrfctn>{{result_str}}</Vrfctn>{{resolved_block}}\n    </Rpt>\n  </IdVrfctnRpt>\n</Document>'


import urllib.request
import urllib.error
import json

ENDPOINT = "http://localhost:8000/v1/iso20022/validate"

def validate_xml(xml_content, msg_type_hint=None):
    try:
        req = urllib.request.Request(ENDPOINT, data=xml_content.encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/xml')
        if msg_type_hint:
            # Query param for message type if needed, but endpoint auto-detects
            pass
            
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode('utf-8')
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, json.loads(body) if body else {}
    except Exception as e:
        return 500, {"error": str(e)}

def run_tests():
    print(f"Sending requests to {ENDPOINT}...")
    errors = []
    
    # helper to check
    def check(name, xml):
        print(f"  Validating {name}...")
        status, resp = validate_xml(xml)
        if status != 200:
            errors.append(f"{name} failed HTTP {status}: {resp}")
            return
        if not resp.get("valid"):
            errors.append(f"{name} XSD invalid: {resp.get('errors')}")
        else:
            print(f"    ✅ {name} OK")

    # 1. pacs.002 Acceptance
    try:
        if 'build_pacs002_acceptance' in globals():
            xml = build_pacs002_acceptance("uetr-1", "ACCC", 100.00, "USD")
            check("pacs.002_acceptance", xml)
    except Exception as e: errors.append(f"pacs.002_acc error: {e}")

    # 2. pacs.002 Rejection
    try:
        if 'build_pacs002_rejection' in globals():
            xml = build_pacs002_rejection("uetr-1", "RJCT", "AM09", "Refused")
            check("pacs.002_rejection", xml)
    except Exception as e: errors.append(f"pacs.002_rej error: {e}")

    # 3. camt.054
    try:
        if 'build_camt054' in globals():
            xml = build_camt054("uetr-1", 10.0, "USD", "Debtor Name", "Creditor Name", "BOOK")
            check("camt.054", xml)
    except Exception as e: errors.append(f"camt.054 error: {e}")

    # 4. pain.001
    try:
        if 'build_pain001' in globals():
            xml = build_pain001("uetr-1", 100.0, "USD", "Debtor", "D_ACC", "D_BIC", "Creditor", "C_ACC", "C_BIC")
            check("pain.001", xml)
    except Exception as e: errors.append(f"pain.001 error: {e}")

    # 5. camt.103
    try:
        if 'build_camt103' in globals():
            xml = build_camt103("res-1", 100.0, "USD", "uetr-1")
            check("camt.103", xml)
    except Exception as e: errors.append(f"camt.103 error: {e}")

    # 6. pacs.004
    try:
        if 'build_pacs004' in globals():
            xml = build_pacs004("uetr-orig", 50.0, "USD", "DUPL")
            check("pacs.004", xml)
    except Exception as e: errors.append(f"pacs.004 error: {e}")

    # 7. pacs.028
    try:
        if 'build_pacs028' in globals():
            xml = build_pacs028("uetr-1", "req-1")
            check("pacs.028", xml)
    except Exception as e: errors.append(f"pacs.028 error: {e}")

    # 8. camt.056
    try:
        if 'build_camt056' in globals():
            xml = build_camt056("uetr-new", "uetr-orig")
            check("camt.056", xml)
    except Exception as e: errors.append(f"camt.056 error: {e}")

    # 9. camt.029
    try:
        if 'build_camt029' in globals():
            xml = build_camt029("msg-orig")
            check("camt.029", xml)
    except Exception as e: errors.append(f"camt.029 error: {e}")

    # 10. acmt.023
    try:
        if 'build_acmt023' in globals():
            xml = build_acmt023("id-1", "EMAL", "test@example.com")
            check("acmt.023", xml)
    except Exception as e: errors.append(f"acmt.023 error: {e}")

    # 11. acmt.024
    try:
        if 'build_acmt024' in globals():
            xml = build_acmt024("msg-1", "id-1", True, "IBAN123", "Name")
            check("acmt.024", xml)
    except Exception as e: errors.append(f"acmt.024 error: {e}")

    if errors:
        print("❌ LIVE VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✅ ALL SYSTEMS GO: End-to-End builders + backend validation passed!")

run_tests()
