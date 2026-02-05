# Nexus Assumptions: Economics and Fees (A23)

This document outlines the assumptions regarding fee transparency and the calculation of ultimate payment amounts.

## A23: Fee Formulas & Transparency
- **A23.1: Source PSP Fee**: Assumed as a combination of a fixed charge (e.g., 1.00 unit) and a percentage (e.g., 10bps) of the requested amount.
- **A23.2: Mandated Destination Fee**: The Gateway assumes it is the "Authority" on Destination PSP fees. D-PSPs are prohibited from recalculating or increasing their fee upon receipt of the message.
- **A23.3: Scheme Cost Recovery**: The Nexus Scheme Organisation (NSO) fee is assumed to be invoiced periodically to the Source IPS rather than deducted per-transaction in the sandbox.
- **A23.4: PTD Compliance**: All "Pre-Transaction Disclosure" calculations must be presented to the user BEFORE they authorize the payment instruction (`pacs.008`).

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A23.1 (S-PSP Fee) | Fixed + % | fee_formulas.py:238 | ✅ Verified |
| A23.4 (PTD) | Pre-auth disclosure | fee_formulas.py:271 | ✅ Verified |
