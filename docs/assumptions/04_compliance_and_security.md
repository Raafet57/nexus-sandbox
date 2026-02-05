# Nexus Assumptions: Compliance and Security (A11-A15)

This document covers assumptions related to sanctions screening, transaction priorities, and communication security.

## A11: Sanctions Screening
- **A11.1: PSP Responsibility**: Primary responsibility for screening the Debtor and Creditor lies with the Source and Destination PSPs, respectively.
- **A11.2: Threshold Monitoring**: Domestic IPS systems handle mandatory threshold monitoring and AML reporting for relevant authorities.

## A12: Transaction Priorities
- **A12.1: HIGH Priority (SLA)**: Assumes a 25-second settlement SLA. If not met, the transaction is rejected with `AB03`.
- **A12.2: NORM Priority**: Allows for "Accepted Without Posting" (ACWP) status if a manual compliance investigation is required.

## A13: Communication Security (mTLS)
- **A13.1: Zero Trust Mesh**: All actor-to-actor communication (IPS ↔ Gateway ↔ SAP) assumes Mutual TLS (mTLS) authentication.
- **A13.2: BAH Signatures**: The Business Application Header (BAH) of ISO messages is assumed to contain valid digital signatures for non-repudiation.

## A15: Data Privacy & Residency
- **A15.1: Minimum Disclosure**: The Gateway only forwards data elements strictly necessary for the Destination IPS to credit the Recipient's account.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A12.1 (AB03) | 25s SLA timeout | pacs002.py:110 | ✅ Verified |
| A13 (mTLS) | Zero-trust auth | config.py (JWT) | ✅ Verified |
