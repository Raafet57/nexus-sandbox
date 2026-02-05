# Nexus Assumptions: Actor Integration & Plug-and-Play (A25-A27)

This document outlines assumptions regarding external participant connectivity and sandbox testing.

## A25: Self-Service Actor Registration
- **A25.1: Callback URL Registration**: Actors can self-register their `callback_url` for sandbox testing via `POST /v1/actors/register`.
- **A25.2: BIC as Unique Identifier**: The BIC (Bank Identifier Code) is used as the primary unique identifier for actors.
- **A25.3: Actor Types**: The sandbox supports the following actor types: `FXP`, `IPS`, `PSP`, `SAP`, `PDO`.

## A26: Connectivity Models (Direct vs. Indirect)
- **A26.1: Direct Participants (FXP, IPS)**: These actors connect directly to the Nexus Gateway via HTTPS APIs. They can receive real-time ISO 20022 message delivery to their registered `callback_url`.
- **A26.2: Indirect Participants (PSP, SAP, PDO)**: These actors do not connect directly to Nexus. They interact with their domestic IPS, which then forwards messages to Nexus. In sandbox, they should configure their domestic IPS callback.

## A27: Sandbox Registry Simplification
- **A27.1: In-Memory Registry**: The sandbox uses an in-memory registry for actor data. Production would use a persistent database table.
- **A27.2: Pre-Seeded Actors**: The sandbox is pre-seeded with 6 actors (DBS SG, Bangkok Bank TH, Maybank MY, FXP Alpha, SG IPS, TH IPS) for immediate testing.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A25.1 (Callback) | Self-Service Registration | `actors.py:143` | ✅ Implemented |
| A26.1 (Direct FXP) | HTTPS Connectivity | `actors.py:69-122` | ✅ Pre-seeded |
| A27.1 (In-Memory) | Sandbox Simplification | `actors.py:66-122` | ✅ Implemented |

---

**Reference**: NotebookLM 2026-02-03 - Actor Connectivity Models
