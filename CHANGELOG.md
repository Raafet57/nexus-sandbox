# Changelog

All notable changes to the Nexus Global Payments Sandbox will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

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
