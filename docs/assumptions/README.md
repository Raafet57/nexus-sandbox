# Nexus Sandbox: Assumptions Index

This directory contains granular assumption documents covering all technical and business logic decisions (A1-A24) made during the Nexus Sandbox implementation. Each file includes a **Cross-Reference Table** linking assumptions to their implementation in the codebase.

## Document Overview

| File | Assumptions | Topics |
|------|-------------|--------|
| [01_scope_and_infrastructure.md](01_scope_and_infrastructure.md) | A1, A5 | Sandbox scope, timing, UTC mandate |
| [02_fx_and_liquidity.md](02_fx_and_liquidity.md) | A6-A10, A17 | FX provision, 600s TTL, SAP roles |
| [03_messaging_and_idempotency.md](03_messaging_and_idempotency.md) | A2, A16, A21 | ISO 20022, XSD, UETR |
| [04_compliance_and_security.md](04_compliance_and_security.md) | A11-A15 | Sanctions, mTLS, priorities |
| [05_settlement_and_exceptions.md](05_settlement_and_exceptions.md) | A18-A19 | Reversals, returns, recalls |
| [06_economics_and_fees.md](06_economics_and_fees.md) | A23 | Fee formulas, PTD compliance |
| [07_status_and_reason_codes.md](07_status_and_reason_codes.md) | A20 | ISO reason codes (60+) |
| [08_complex_edge_cases.md](08_complex_edge_cases.md) | A22, A24 | Sponsored entities, finality |

## Verification Status

All assumptions have been:
1. **Recovered** from previous session artifacts
2. **Verified** against the Nexus Technical Blueprint (via NotebookLM)
3. **Cross-referenced** with implementation files in `services/nexus-gateway/src/`

---

*Last updated: 2026-02-03*
