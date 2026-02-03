# Nexus Sandbox Documentation Index

Comprehensive documentation for the Nexus Global Payments Sandbox.

## Quick Start

| Document | Description |
|----------|-------------|
| [README](../README.md) | Project overview and setup |
| [Usage Guide](./USAGE_GUIDE.md) | Basic usage instructions |
| [Dashboard Guide](./DASHBOARD_GUIDE.md) | **NEW** - Navigation and UI reference |
| [Integration Guide](./INTEGRATION_GUIDE.md) | External system integration |
| [E2E Demo Script](./E2E_DEMO_SCRIPT.md) | Live demonstration walkthrough |

---

## Architecture

| Document | Description |
|----------|-------------|
| [C4 Architecture](./architecture/C4_ARCHITECTURE.md) | Context, container, component diagrams |
| [Event Sourcing](./architecture/EVENT_SOURCING.md) | Payment event persistence strategy |

---

## API Reference

| Document | Description |
|----------|-------------|
| [API Reference](./api/API_REFERENCE.md) | Complete endpoint documentation |
| [Swagger UI](http://localhost:8080/api/docs) | Interactive API explorer |
| [ReDoc](http://localhost:8080/api/redoc) | Alternative API documentation |

---

## Architecture Decision Records (ADRs)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](./adr/ADR-001-technology-stack.md) | Technology Stack | Accepted |
| [ADR-002](./adr/ADR-002-pluggable-actor-architecture.md) | Pluggable Actor Architecture | Accepted |
| [ADR-003](./adr/ADR-003-iso20022-message-handling.md) | ISO 20022 Message Handling | Accepted |
| [ADR-004](./adr/ADR-004-event-sourcing-strategy.md) | Event Sourcing Strategy | Accepted |
| [ADR-005](./adr/ADR-005-api-design-principles.md) | API Design Principles | Accepted |
| [ADR-006](./adr/ADR-006-security-model.md) | Security Model | Accepted |
| [ADR-007](./adr/ADR-007-testing-strategy.md) | Testing Strategy | Accepted |
| [ADR-008](./adr/ADR-008-actor-callback-format.md) | Actor Callback Format | Accepted |
| [ADR-009](./adr/ADR-009-sandbox-mock-data-strategy.md) | Sandbox Mock Data Strategy | Accepted |
| [ADR-010](./adr/ADR-010-payment-lifecycle-persistence.md) | Payment Lifecycle Persistence | Accepted |
| [ADR-011](./adr/ADR-011-developer-observability.md) | Developer Observability | Accepted |

---

## Assumptions Registry

Design assumptions documented during implementation:

| File | Topics |
|------|--------|
| [01 Scope & Infrastructure](./assumptions/01_scope_and_infrastructure.md) | A01–A05 |
| [02 FX & Liquidity](./assumptions/02_fx_and_liquidity.md) | A06–A10 |
| [03 Messaging & Idempotency](./assumptions/03_messaging_and_idempotency.md) | A11–A14 |
| [04 Compliance & Security](./assumptions/04_compliance_and_security.md) | A15–A18 |
| [05 API Design](./assumptions/05_api_design.md) | A19–A21 |
| [06 Testing](./assumptions/06_testing.md) | A22–A23 |
| [07 Callback System](./assumptions/07_callback_system.md) | A24 |
| [08 Mock Data](./assumptions/08_mock_data.md) | A25 |
| [09 Event Sourcing Implementation](./assumptions/09_event_sourcing_implementation.md) | A26 |
| [10 Lifecycle Persistence](./assumptions/10_lifecycle_persistence.md) | A27 |
| [11 Developer Observability](./assumptions/11_developer_observability.md) | A28–A30 |

---

## Infrastructure

| Document | Description |
|----------|-------------|
| [Docker Setup](./infrastructure/DOCKER_SETUP.md) | Container configuration |
| [Schema Documentation](./database/SCHEMA.md) | Database schema reference |
| [Security Model](./security/SECURITY_MODEL.md) | Authentication and authorization |

---

## External References

- [Nexus Official Documentation](https://docs.nexusglobalpayments.org/)
- [ISO 20022 Message Catalogue](https://www.iso20022.org/)
- [BIS Nexus Blueprint](https://www.bis.org/publ/othp54.htm)

---

Created by [Siva Subramanian](https://linkedin.com/in/sivasub987)
