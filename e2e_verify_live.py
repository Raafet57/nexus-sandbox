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

def extract_builders_and_test():
    print(f"Reading {SOURCE_PATH}...")
    with open(SOURCE_PATH, 'r') as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    
    # Extract only the builder functions
    builder_code = ""
    imports = "from datetime import datetime, timezone\nimport sys\n"
    
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("build_"):
            if sys.version_info >= (3, 9):
                builder_code += ast.unparse(node) + "\n\n"
            else:
                print("Python < 3.9 detected, skipping source extraction test.")
                return

    full_script = imports + builder_code + f"""
import urllib.request
import urllib.error
import json

ENDPOINT = "{ENDPOINT}"

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
        return e.code, json.loads(body) if body else {{}}
    except Exception as e:
        return 500, {{"error": str(e)}}

def run_tests():
    print(f"Sending requests to {{ENDPOINT}}...")
    errors = []
    
    # helper to check
    def check(name, xml):
        print(f"  Validating {{name}}...")
        status, resp = validate_xml(xml)
        if status != 200:
            errors.append(f"{{name}} failed HTTP {{status}}: {{resp}}")
            return
        if not resp.get("valid"):
            errors.append(f"{{name}} XSD invalid: {{resp.get('errors')}}")
        else:
            print(f"    ✅ {{name}} OK")

    # Valid UUID for testing
    VALID_UETR = "550e8400-e29b-41d4-a716-446655440000"
    VALID_REQ_ID = "550e8400-e29b-41d4-a716-446655440001"
    VALID_ORIG_ID = "MSG-12345678"

    # 1. pacs.002 Acceptance
    try:
        if 'build_pacs002_acceptance' in globals():
            xml = build_pacs002_acceptance(VALID_UETR, "ACCC", 100.00, "USD")
            check("pacs.002_acceptance", xml)
    except Exception as e: errors.append(f"pacs.002_acc error: {e}")

    # 2. pacs.002 Rejection
    try:
        if 'build_pacs002_rejection' in globals():
            xml = build_pacs002_rejection(VALID_UETR, "RJCT", "AM09", "Refused")
            check("pacs.002_rejection", xml)
    except Exception as e: errors.append(f"pacs.002_rej error: {e}")

    # 3. camt.054
    try:
        if 'build_camt054' in globals():
            xml = build_camt054(VALID_UETR, 10.0, "USD", "Debtor Name", "Creditor Name", "BOOK")
            check("camt.054", xml)
    except Exception as e: errors.append(f"camt.054 error: {e}")

    # 4. pain.001
    try:
        if 'build_pain001' in globals():
            xml = build_pain001(VALID_UETR, 100.0, "USD", "Debtor", "D_ACC", "NEXUSGENERIC", "Creditor", "C_ACC", "NEXUSGENERIC")
            check("pain.001", xml)
    except Exception as e: errors.append(f"pain.001 error: {e}")

    # 5. camt.103
    try:
        if 'build_camt103' in globals():
            xml = build_camt103("RSV-123", 100.0, "USD", VALID_UETR)
            check("camt.103", xml)
    except Exception as e: errors.append(f"camt.103 error: {e}")

    # 6. pacs.004
    try:
        if 'build_pacs004' in globals():
            xml = build_pacs004(VALID_UETR, "550e8400-e29b-41d4-a716-446655449999", 50.0, "USD", "DUPL")
            check("pacs.004", xml)
    except Exception as e: errors.append(f"pacs.004 error: {e}")

    # 7. pacs.028
    try:
        if 'build_pacs028' in globals():
            xml = build_pacs028(VALID_REQ_ID, VALID_UETR)
            check("pacs.028", xml)
    except Exception as e: errors.append(f"pacs.028 error: {e}")

    # 8. camt.056
    try:
        if 'build_camt056' in globals():
            xml = build_camt056(VALID_UETR, "550e8400-e29b-41d4-a716-446655449999")
            check("camt.056", xml)
    except Exception as e: errors.append(f"camt.056 error: {e}")

    # 9. camt.029
    try:
        if 'build_camt029' in globals():
            xml = build_camt029(VALID_ORIG_ID)
            check("camt.029", xml)
    except Exception as e: errors.append(f"camt.029 error: {e}")

    # 10. acmt.023
    try:
        if 'build_acmt023' in globals():
            xml = build_acmt023(VALID_REQ_ID, "EMAL", "test@example.com")
            check("acmt.023", xml)
    except Exception as e: errors.append(f"acmt.023 error: {e}")

    # 11. acmt.024
    try:
        if 'build_acmt024' in globals():
            xml = build_acmt024(VALID_ORIG_ID, VALID_REQ_ID, True, "IBAN123", "Name")
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
"""
    
    with open("live_e2e_runner.py", "w") as f:
        f.write(full_script)
    print("Generated live_e2e_runner.py")

if __name__ == "__main__":
    extract_builders_and_test()
