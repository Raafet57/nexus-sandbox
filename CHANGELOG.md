# Changelog

All notable changes to the Nexus Global Payments Sandbox will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
