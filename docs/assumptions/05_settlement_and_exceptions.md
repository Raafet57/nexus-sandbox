# Nexus Assumptions: Settlement and Exceptions (A18-A19)

This document details the mechanics of settlement cycles, technical timeouts, and exception management flows.

## A18: Settlement Mechanics
- **A18.1: Reservation Phase**: Source IPS debits the S-PSP and credits the Source SAP account (reserved status) BEFORE sending the `pacs.008` to Nexus.
- **A18.2: Atomic Finality**: Settlement at the Destination IPS and Destination SAP must occur simultaneously to ensure no principal risk.
- **A18.3: Automatic Reversal**: If a `RJCT` status is received from the Destination country, the Source SAP/IPS must automatically reverse the original reservation within seconds.

## A19: Payment Returns and Recalls
- **A19.1: Formal Returns (pacs.004)**: Returns are assumed to be "new payments" in the reverse direction, triggered by the D-PSP when a credit is impossible (e.g., account closed).
- **A19.2: Recall Requests (camt.056)**: S-PSP may request a recall for fraud or duplicate errors. Final approval for fund return rests with the D-PSP and their customer.
- **A19.3: FX Risk Allocation**: On returns, the party at fault for the original error (S-PSP for sender error, D-PSP for system error) absorbs any depreciation/gain in value between the two legs.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A18.3 (Reversal) | Automatic reversal | returns.py | ✅ Verified |
| A19.1 (pacs.004) | Formal return | returns.py | ✅ Verified |
