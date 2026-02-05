# Nexus Assumptions: Messaging and Idempotency (A2, A16, A21)

This document details the ISO 20022 messaging standards, validation rules, and duplicate prevention logic.

## A2: ISO 20022 Standards
- **A2.1: Schema Versions**: The sandbox assumes adherence to ISO 20022:2019/2024 message versions (e.g., `pacs.008.001.13`).
- **A2.2: Encoding**: All XML interaction is assumed to be `UTF-8` encoded without Byte Order Marks (BOM).
- **A2.3: UETR Role**: The Unique End-to-End Transaction Reference (UETR) is the primary key for tracking payment state across the multilateral mesh.

## A16: XSD Validation Layers
- **A16.1: Strict Structural Checks**: Every incoming ISO message must pass technical validation against the official Nexus XSD files before business logic is applied.
- **A16.2: External Code Sets**: Codes used in status reports (pacs.002) and returns (pacs.004) must belong to the ISO 20022 External Code Set maintained by SWIFT.

## A21: Message Idempotency
- **A21.1: 7-Day Window**: The Gateway assumes a 7-day uniqueness window for UETRs. Duplicate UETRs within this period return the latest status of the existing transaction.
- **A21.2: End-to-End Key**: Idempotency is enforced at the Gateway level to prevent double-debiting during retries.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A2.1 (ISO 20022) | pacs.008.001.13 | iso20022.py | ✅ Verified |
| A21 (UETR) | 7-day uniqueness | iso20022.py:476 | ✅ Verified |
