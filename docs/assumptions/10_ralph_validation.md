# Nexus Assumptions: Ralph Wiggum Validation Additions (A28-A30)

This document extends the assumptions repository with discoveries from the Ralph Wiggum validation loop.

## A28: Status Code Coverage
- **A28.1: Sandbox Subset**: The sandbox implements 13 of the 60+ production ISO 20022 status codes.
- **A28.2: Completeness for Demo**: All codes needed for demonstrating happy flows (ACCC) and common error scenarios (AB04, BE23, AC01, AC04, AM04, AB03, RC11) are implemented.

## A29: FXP Account Traceability
- **A29.1: PrvsInstgAgt1Acct**: When available in `quote_data`, the FXP's settlement account at the Source SAP is recorded in the transformed `pacs.008` for audit trail purposes.
- **A29.2: Optional Element**: If `fxp_account_id` is not provided in the quote, this element is omitted (graceful degradation).

## A30: Validation Completeness
- **A30.1: Edge Case Coverage**: The sandbox documents but does not exhaustively implement all edge cases. For example:
  - Sponsored entity scenarios (A22) are documented but not simulated.
  - Same-entity scenarios (PSP=IPS=SAP) are acknowledged but simplified.
- **A30.2: Documentation First**: All edge cases are documented in `E2E_DEMO_SCRIPT.md` even if not code-implemented.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A28.1 | 60+ codes (subset) | `iso20022.py:39-76` | ✅ 13 implemented |
| A29.1 | PrvsInstgAgt1Acct | `iso20022.py:543-554` | ✅ Implemented |
| A30.1 | Edge case docs | `E2E_DEMO_SCRIPT.md` | ✅ Documented |

---

**Reference**: NotebookLM 2026-02-03 - Ralph Wiggum Validation Loop
