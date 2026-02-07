# Changelog

All notable changes to the Nexus Global Payments Sandbox will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

#### Deep Parity Remediation (Feb 7, 2026 - Session 3)
- **Rate Limiting Middleware**: In-memory sliding window rate limiter with per-endpoint limits (e.g., 30/min for pacs.008, 60/min for quotes), X-RateLimit-* headers, and configurable `NEXUS_RATE_LIMIT_*` env vars
- **Settlement Positions**: `GET /v1/liquidity/positions` endpoint for FXP net positions across currency pairs, sourced from actual payment data with fallback examples
- **camt.103 XML Extraction**: `camt103.py` now parses reservation details (amount, currency, accountId, reservationType) from XML using lxml
- **pacs.004 Sandbox Mode**: Upgraded from 501 stub to functional return processing with reason code validation, return recording, and status cache updates
- **camt.056 Sandbox Mode**: Upgraded from 501 stub to functional recall processing with duplicate detection, state tracking, and recall ID generation
- **NEXUS_RELEASE_1_STRICT**: New env var to toggle between sandbox mode (default) and strict Release 1 behavior (501 for pacs.004/camt.056)

### Fixed

#### Parity Audit Remediation (Feb 7, 2026 - Session 2)
- **pacs.002 Namespace**: Aligned callback XML namespace from `001.10` to `001.15` to match pacs.008.py builders
- **Callback Timeout**: Made configurable via `NEXUS_CALLBACK_TIMEOUT_SECONDS` env var (default 10s)
- **Callback Parameters**: `schedule_pacs002_delivery` now forwards `currency` and `amount` parameters
- **pacs.004 XML Extraction**: Replaced placeholder `EXTRACTED_FROM_XML` with proper lxml-based OrgnlUETR parsing
- **camt.056 XML Extraction**: Replaced placeholder with lxml-based OrgnlUETR extraction for recall requests
- **camt.029 XML Extraction**: Replaced placeholder with lxml-based CxlStsId/recall reference extraction
- **Quote Expiry Guard**: Added defense-in-depth pre-submission expiry check in InteractiveDemo `handleConfirmPayment`

### Added
- **TROUBLESHOOTING.md**: Comprehensive troubleshooting guide for Docker, API, frontend, database, and health checks
- **Audit Trail Events**: pacs.004 and recall handlers now store audit trail events for all processed messages

#### ISO 20022 Compliance
- **ACSC Status Code**: Added `ACSC` (Accepted Settlement Completed) to TransactionStatus enum - now correctly returned in pacs.002 responses
- **XML Namespace Version**: Fixed pacs.008 XML namespace from `pacs.008.001.08` to `pacs.008.001.13` (8 occurrences in pacs008.py)

#### BIC Code Consistency
- Mass find/replace across 25+ files to align with seed data:
  - `DBSGSGSG` → `DBSSSGSG` (DBS Bank Singapore)
  - `BKKBTHBK` → `KASITHBK` (Kasikorn Bank Thailand)
  - `MAYBMYKL` → `MABORKKL` (Maybank Malaysia)
  - `NEXUSFXP1` → `FXP-ABC` (ABC Currency Exchange)
  - `SGIPSOPS` → `FAST` (Singapore IPS)
  - `THIPSOPS` → `PromptPay` (Thailand IPS)

#### Frontend
- **maxAmount Corrections**: Updated mockData.ts to match seed data values:
  - SGD: 200,000 | THB: 5,000,000 | MYR: 10,000,000 | IDR: 1,000,000,000 | PHP: 10,000,000
- **Quote Expiry Blocking**: InteractiveDemo now prevents selection of expired quotes with user notification
- **XML Preview**: Added live pacs.008 XML preview before submission (Step 3)

#### Infrastructure
- **Docker Compose Lite**: Added missing frontend/backend network definitions
- **Migration Order**: Renamed migrations for correct execution order:
  - `002_seed_data.sql` → `003_seed_data.sql`
  - `003_fxp_sap_tables.sql` → `004_fxp_sap_tables.sql`

#### Documentation
- Fixed broken links in docs/README.md (removed DOCKER_SETUP.md references, added OBSERVABILITY.md and KUBERNETES_DEPLOYMENT.md)
- Fixed SCHEMA.md → POSTGRESQL_SCHEMA.md link

#### API
- **Step 12 Sender Confirmation**: New endpoint `/fees/sender-confirmation` validates quote exists/not expired and records audit event
- **Real camt.054**: Reconciliation endpoint queries actual payment data from database

#### GitHub Pages Demo
- **Mock Data Parity**: Fixed all BIC codes to match seed data (FXP-ABC, FAST, PromptPay, DuitNow, etc.)
- **Quote Expiry Validation**: Mock `confirmSenderApproval()` now validates quote expiry like real backend
- **FXP ID Corrections**: `generateMockQuotes()` now uses FXP-ABC and FXP-XYZ matching seed data
- **IPS Operators**: Fixed clearing_system_id values (FAST, PromptPay, DuitNow, BI-FAST, InstaPay)
- **New Mock APIs**:
  - `validateQuoteForConfirmation()` - validates quote exists/not expired
  - `recordSenderConfirmation()` - Step 12 confirmation with validation
  - QR Code APIs (`mockParseQRCode`, `mockGenerateQRCode`, `mockValidateQRCode`)
  - UPI APIs (`mockParseUPI`, `mockUpiToEMVCo`, `mockEmvcoToUPI`)
  - Demo Data Management (`getMockDemoDataStats`, `purgeMockDemoData`)
  - ISO 20022 Templates (`mockIsoTemplates`)
- **Mock Payment Store**: Now generates pacs.008 and pacs.002 XML with correct namespace (001.13)

#### CI/CD
- Added comprehensive GitHub Actions CI workflow (`ci.yml`) with:
  - Backend Python tests with PostgreSQL
  - Frontend TypeScript build and lint checks
  - Docker Compose validation
  - Migration validation
  - Code quality checks

## [1.0.0] - 2026-02-03

### Added

#### Core Payment Flow
- Complete 17-step payment lifecycle implementation
- FX quote aggregation with tier-based improvements
- Quote locking and expiry management
- Proxy resolution via PDO (mobile, email, QR)
- pacs.008 submission with XSD validation
- pacs.002 status reporting with callback delivery

#### ISO 20022 Messaging
- pacs.008 (FI to FI Customer Credit Transfer)
- pacs.002 (Payment Status Report)
- acmt.023/024 (Proxy Resolution)
- camt.054 (Reconciliation Report)
- camt.056 (Payment Recall)
- pacs.004 (Payment Return)

#### Actor Simulators
- PSP Simulator (Source/Destination banks)
- FXP Simulator (FX rate providers)
- SAP Simulator (Settlement Access Providers)
- IPS Simulator (FAST, PromptPay, DuitNow)
- PDO Simulator (Proxy Directory)

#### Demo Dashboard
- Send Payment wizard with real-time quoting
- Actor-specific dashboards (PSP, FXP, SAP, IPS, PDO)
- Payments Explorer with lifecycle timeline
- ISO 20022 Message Inspector (XML viewer)
- Network mesh visualization

#### Developer Experience
- OpenAPI documentation with comprehensive tag descriptions
- Swagger UI at `/docs`, ReDoc at `/redoc`
- Jaeger distributed tracing integration
- DevDebugPanel with actor-specific context

#### Documentation
- 11 Architecture Decision Records (ADRs)
- 12 Assumptions documents
- API Reference (613 lines)
- Integration Guide
- E2E Demo Script

### Reference
- Based on [Nexus Global Payments Documentation](https://docs.nexusglobalpayments.org/)
- ISO 20022 Message Catalogue

---

Created by [Siva Subramanian](https://linkedin.com/in/sivasub987)
