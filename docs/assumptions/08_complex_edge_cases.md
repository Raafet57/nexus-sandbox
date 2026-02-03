# Nexus Assumptions: Complex Edge Cases (A22, A24)

This document covers structural variants and scheme-level responsibilities.

## A22: Complex Participation Scenarios
- **A22.1: Sponsored Entities**: Small PSPs or Fintechs connecting via a direct Clearing Member (Sponsoring PSP). The Gateway assumes the Sponsor BIC is used for clearing, while the Sponsored ID appears in the Credit Transfer info.
- **A22.2: Same-Entity Scenarios**: Cases where the PSP, IPS, and SAP are the same legal entity (e.g., a central bank-owned IPS). Intra-country logic is assumed to be transparent to the Nexus Gateway.
- **A22.3: Amount Capping**: When a quote request (`GET /quotes`) exceeds the destination country's limit, the Gateway returns a capped amount flag rather than returning zero quotes.

## A24: Actor Responsibility Matrix
- **A24.1: Finality Irrevocability**: Once settlement occurs at the Destination IPS, the payment is final. Recovery of funds MUST use the Return (pacs.004) flow.
- **A24.2: Scheme Liability**: The NSO provides the rules and technical platform but bears zero financial liability for settlement failures caused by FXP insolvency.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A22.3 (Capping) | Max amount flag | quotes.py:266-276 | ✅ Verified |
| A24.1 (Finality) | pacs.004 returns | returns.py | ✅ Verified |
