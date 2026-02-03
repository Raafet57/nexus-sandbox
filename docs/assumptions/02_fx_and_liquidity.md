# Nexus Assumptions: FX and Liquidity (A6-A10, A17)

This document covers the business logic for Foreign Exchange (FX) provision, Settlement Access Provider (SAP) operations, and liquidity management.

## A6: FX Provision Model
- **A6.1: Competitive Multi-FXP**: The system assumes multiple providers (FXPs) can bid on the same corridor. The Gateway aggregates these quotes and returns them to the Source PSP based on best rate or preference.
- **A6.2: Quote Locking (600s)**: FX quotes are assumed to be "locked" for a period of 600 seconds (10 minutes). Instructions submitted after this TTL are rejected with status `AB04`.

## A7: FXP Obligations
- **A7.1: Zero-Fee Principal**: FXPs are prohibited from charging transaction fees. Revenue must be derived entirely from the agreed exchange rate spread.
- **A7.2: Liquidity Pre-Positioning**: FXPs are assumed to have pre-funded accounts at both Source and Destination SAPs to ensure instant settlement finality.

## A8: Settlement Access Providers (SAP)
- **A8.1: Intermediary Clearing**: SAPs provide the technical bridge for FXPs to settle funds in currencies where they lack direct central bank settlement access.
- **A8.2: Principal Integrity**: SAPs must settle the exact amount specified in the `pacs.008` message without deducting intermediary banking fees from the principal.

## A10: Liquidity Reservation
- **A10.1: Upfront Fund Hold**: The system assumes a "Reservation First" model where the Source IPS reserves funds on the Source PSP's account before forwarding the message to the Nexus Gateway.

## A17: FXP Advanced Pricing (Tiers)
- **A17.1: Volume Tiers**: FXPs may register tiered rate improvements for high-value transactions or large aggregated volumes.
- **A17.2: Preferential Relationships**: The system supports bilateral "preferred rate" agreements between specific PSPs and FXPs.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A6.2 (600s TTL) | 10 minute validity | config.py:35 | ✅ Verified |
| A17 (Tiers) | Volume discounts | quotes.py:240-243 | ✅ Verified |
