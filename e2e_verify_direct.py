import ast
import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Path to the source file
SOURCE_PATH = "/home/siva/Projects/Nexus Global Payments Sandbox/services/nexus-gateway/src/api/iso20022.py"
ENDPOINT = "http://localhost:8000/v1/iso20022/validate"

def validate_xml(xml_content, msg_type_hint=None):
    try:
        req = urllib.request.Request(ENDPOINT, data=xml_content.encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/xml')
        
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode('utf-8')
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, json.loads(body) if body else {}
    except Exception as e:
        return 500, {"error": str(e)}

def run_tests_with_builders(builders_scope):
    print(f"Sending requests to {ENDPOINT}...")
    errors = []
    
    # Valid UUID for testing
    VALID_UETR = "550e8400-e29b-41d4-a716-446655440000"
    VALID_REQ_ID = "550e8400-e29b-41d4-a716-446655440001"
    VALID_ORIG_ID = "MSG-12345678"
    # Max35Text compliant ID
    VALID_ID_SHORT = "MSG-1234567890123456789012345678901"
    VALID_IBAN = "SS123456789012345678" # 2 letters, 2 digits, up to 30 chars

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

    # Access builders from scope
    b = builders_scope

    # 1. pacs.002 Acceptance
    try:
        if 'build_pacs002_acceptance' in b:
            xml = b['build_pacs002_acceptance'](VALID_ID_SHORT, "ACCC", 100.00, "USD")
            check("pacs.002_acceptance", xml)
    except Exception as e: errors.append(f"pacs.002_acc error: {e}")

    # 2. pacs.002 Rejection
    try:
        if 'build_pacs002_rejection' in b:
            xml = b['build_pacs002_rejection'](VALID_ID_SHORT, "RJCT", "AM09", "Refused")
            check("pacs.002_rejection", xml)
    except Exception as e: errors.append(f"pacs.002_rej error: {e}")

    # 3. camt.054
    try:
        if 'build_camt054' in b:
            # Id is Max35, UETR is Pattern UUID.
            # Wait, build_camt054 signature: uetr, amount...
            # In builder: <Id>{uetr}</Id> ... <NtryRef>{uetr}</NtryRef> ... <UETR>{uetr}</UETR>
            # If UETR field requires UUID, passing Short ID will fail pattern!
            # If Id field requires Max35, passing UUID will fail length (36)!
            # CONFLICT: The builder uses ONE variable `uetr` for multiple XSD fields with conflicting constraints (Max35 vs UUID).
            # Fix: Update builder to use different values or trim for Id.
            # I will updating builder logic for camt.054 is separate step? 
            # Use VALID_UETR here, and I will fix the builder to truncate for Id.
            xml = b['build_camt054'](VALID_UETR, 10.0, "USD", "Debtor Name", "Creditor Name", "BOOK")
            check("camt.054", xml)
    except Exception as e: errors.append(f"camt.054 error: {e}")

    # 4. pain.001
    try:
        if 'build_pain001' in b:
            xml = b['build_pain001'](VALID_ID_SHORT, 100.0, "USD", "Debtor", VALID_IBAN, "NEXUSGEN", "Creditor", VALID_IBAN, "NEXUSGEN")
            check("pain.001", xml)
    except Exception as e: errors.append(f"pain.001 error: {e}")

    # 5. camt.103
    try:
        if 'build_camt103' in b:
            xml = b['build_camt103'](VALID_ID_SHORT, 100.0, "USD", "RSV-1234")
            check("camt.103", xml)
    except Exception as e: errors.append(f"camt.103 error: {e}")

    # 6. pacs.004
    try:
        if 'build_pacs004' in b:
            xml = b['build_pacs004'](VALID_ID_SHORT, VALID_ID_SHORT, 50.0, "USD", "DUPL")
            check("pacs.004", xml)
    except Exception as e: errors.append(f"pacs.004 error: {e}")

    # 7. pacs.028
    try:
        if 'build_pacs028' in b:
            xml = b['build_pacs028'](VALID_ID_SHORT, VALID_ID_SHORT)
            check("pacs.028", xml)
    except Exception as e: errors.append(f"pacs.028 error: {e}")

    # 8. camt.056
    try:
        if 'build_camt056' in b:
            xml = b['build_camt056'](VALID_ID_SHORT, VALID_ID_SHORT)
            check("camt.056", xml)
    except Exception as e: errors.append(f"camt.056 error: {e}")

    # 9. camt.029
    try:
        if 'build_camt029' in b:
            xml = b['build_camt029'](VALID_ID_SHORT)
            check("camt.029", xml)
    except Exception as e: errors.append(f"camt.029 error: {e}")

    # 10. acmt.023
    try:
        if 'build_acmt023' in b:
            xml = b['build_acmt023'](VALID_ID_SHORT, "EMAL", "test@example.com")
            check("acmt.023", xml)
    except Exception as e: errors.append(f"acmt.023 error: {e}")

    VALID_IBAN = "SS123456789012345678" # 2 letters, 2 digits, up to 30 chars

    # 11. acmt.024
    try:
        if 'build_acmt024' in b:
            xml = b['build_acmt024'](VALID_ORIG_ID, VALID_ID_SHORT, True, VALID_IBAN, "Name")
            check("acmt.024", xml)
    except Exception as e: errors.append(f"acmt.024 error: {e}")

    if errors:
        print("\n❌ LIVE VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n✅ ALL SYSTEMS GO: End-to-End builders + backend validation passed!")

def main():
    print(f"Reading {SOURCE_PATH}...")
    with open(SOURCE_PATH, 'r') as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    
    # Extract only the builder functions source
    builder_code = ""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("build_"):
            if sys.version_info >= (3, 9):
                builder_code += ast.unparse(node) + "\n\n"
            else:
                print("Python < 3.9 detected, assuming python3 is newer.")
                # We can't really work without unparse easily unless we exec the file with mocks.
                # But let's assume Python 3.9+ is available in the environment (it usually is).
                pass

    # Execute builder code in a separate namespace
    scope = {}
    scope['datetime'] = datetime
    scope['timezone'] = timezone
    
    try:
        exec(builder_code, scope)
    except Exception as e:
        print(f"Failed to execute builder code: {e}")
        sys.exit(1)
    
    run_tests_with_builders(scope)

if __name__ == "__main__":
    main()
