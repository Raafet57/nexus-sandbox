# Parity Gaps Found

## Confirmed Gaps

### GAP-001: acmt.024 builder missing Pty > Nm (HIGH)
- **File:** `services/nexus-gateway/src/api/iso20022/builders.py`
- **Issue:** `build_acmt024` does not include `<Pty><Nm>` element (full party name needed for sanctions screening per Nexus docs)
- **Status:** UNFIXED

### GAP-002: No build_pacs008 / build_pacs002 builders (MEDIUM)
- **File:** `services/nexus-gateway/src/api/iso20022/builders.py`
- **Issue:** builders.py only has `build_acmt023`, `build_acmt024`, `build_camt029`, `build_pacs004`. Missing `build_pacs008` (credit transfer) and `build_pacs002` (status report) builders.
- **Status:** UNFIXED

### GAP-003: No build_camt054 builder (LOW)
- **File:** `services/nexus-gateway/src/api/iso20022/builders.py`
- **Issue:** No builder for camt.054 (bank-to-customer debit/credit notification)
- **Status:** UNFIXED

### GAP-004: datetime.utcnow() deprecated (LOW)
- **File:** `services/nexus-gateway/src/api/quotes.py`
- **Issue:** Uses `datetime.utcnow()` which is deprecated in Python 3.12+. Should use `datetime.now(timezone.utc)`.
- **Status:** UNFIXED

### GAP-005: destCountry query param alias (CHECK)
- **File:** `services/nexus-gateway/src/api/quotes.py`
- **Issue:** Uses `destCountry` alias for destination country query param. Need to verify against docs API spec for correct param name.
- **Status:** NEEDS VERIFICATION

### GAP-006: Quote response fields (CHECK)
- **File:** `services/nexus-gateway/src/api/quotes.py`
- **Issue:** Quote response JSON fields need verification against docs API spec for completeness.
- **Status:** NEEDS VERIFICATION
