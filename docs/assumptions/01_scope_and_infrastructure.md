# Nexus Assumptions: Scope and Infrastructure (A1, A5)

This document outlines assumptions regarding the sandbox scope, environment simplifications, and timing standards.

## A1: Sandbox Scope & Simplifications
- **A1.1: Single Gateway Instance**: The implementation assumes a single instance of the Nexus Gateway handled via Docker. High availability (HA) and automatic failover clustering are considered outside the educational scope.
- **A1.2: Simulation Depth**: Domestic IPS clearing and settlement are simulated within specific containers (`ips-sg`, `ips-th`, etc.) rather than connecting to live national payment infrastructure.
- **A1.3: Synchronous REST Handling**: While production Nexus uses asynchronous patterns for ISO 20022 message delivery, this sandbox uses synchronous FastAPI endpoints for REST-based discovery to simplify real-time UI updates.

## A5: Timing and Timezones
- **A5.1: UTC Zulu Mandate**: All system timestamps (including message creation times, expiry, and acceptance) MUST strictly follow ISO 8601 UTC Zulu format (e.g., `YYYY-MM-DDTHH:MM:SS.sssZ`).
- **A5.2: Millisecond Precision**: The system assumes 3 decimal places for millisecond precision to ensure compatibility across disparate domestic IPS systems during the clearing cycle.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A5.1 (UTC) | Strict UTC Zulu | quotes.py:227 | ✅ Verified |
| A1.3 (Sync) | Synchronous API | main.py | ✅ Verified |
