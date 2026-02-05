# ADR-001: Technology Stack Selection

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Select appropriate technologies for building a spec-compliant Nexus Global Payments sandbox

## Context

We are building a comprehensive sandbox implementation of the Nexus Global Payments system as documented at [docs.nexusglobalpayments.org](https://docs.nexusglobalpayments.org/). The implementation must:

1. Faithfully replicate the API endpoints and message flows specified in the official documentation
2. Support pluggable actor components (PSP, IPS, FXP, SAP, PDO)
3. Handle ISO 20022 XML messages (pacs.008, pacs.002, acmt.023, acmt.024, camt.054)
4. Be containerized for portability and easy deployment
5. Support comprehensive testing and demonstration scenarios

### Reference Documentation

- [Nexus Overview](https://docs.nexusglobalpayments.org/) - System architecture and actors
- [API Specifications](https://docs.nexusglobalpayments.org/apis/overview) - REST API endpoints
- [ISO 20022 Messages](https://docs.nexusglobalpayments.org/messaging-and-translation/key-points) - Message specifications

## Decision

### Core Components

| Component | Technology | Version |
|-----------|------------|---------|
| **Nexus Gateway** | Python + FastAPI | Python 3.12, FastAPI 0.110+ |
| **Actor Simulators** | Node.js + Express | Node 20 LTS, Express 4.x |
| **ISO 20022 Parsing** | Python lxml + pydantic-xml | lxml 5.x |
| **Database** | PostgreSQL | 16.x |
| **Cache** | Redis | 7.x |
| **Message Broker** | Apache Kafka | 3.6+ |
| **Distributed Tracing** | Jaeger | 1.50+ |
| **Containerization** | Docker + Docker Compose | Docker 24+, Compose 2.x |

### Rationale

#### Python + FastAPI for Nexus Gateway

**Chosen because:**
- **Automatic OpenAPI generation**: FastAPI generates OpenAPI 3.1 specs matching the Nexus API documentation style
- **Async-first**: Native async/await for handling concurrent payment flows
- **Type safety**: Pydantic models enforce schema validation matching ISO 20022 constraints
- **Rapid development**: Faster iteration for sandbox development
- **XML handling**: Excellent lxml library for ISO 20022 XML processing

**Reference**: The Nexus API uses RESTful patterns with JSON responses as shown in [Countries API](https://docs.nexusglobalpayments.org/apis/countries):
```
GET /countries HTTP/1.1
Host: localhost:3000
Accept: */*
```

#### Node.js + Express for Actor Simulators

**Chosen because:**
- **Widely understood**: Easy for third parties to modify and extend
- **Quick prototyping**: Rapid development of mock behaviors
- **JSON native**: Natural fit for API responses
- **Web UI support**: Easy to add demo interfaces

**Reference**: Actors (PSP, IPS, FXP, SAP, PDO) are defined in the [Terminology section](https://docs.nexusglobalpayments.org/introduction/terminology).

#### PostgreSQL 16

**Chosen because:**
- **Event sourcing support**: JSONB for flexible event storage, table partitioning for time-series data
- **Transactional integrity**: ACID compliance for payment state management
- **ISO 20022 storage**: Can store raw XML in TEXT columns with JSONB for indexed queries
- **Production parity**: Matches enterprise payment system patterns

**Reference**: Payment state tracking aligns with the [Payment Processing](https://docs.nexusglobalpayments.org/payment-processing/key-points) documentation.

#### Redis 7

**Chosen because:**
- **FX rate caching**: Low-latency access to current rates
- **Quote storage**: Ephemeral quote data with TTL (10-minute validity per Nexus spec)
- **Session management**: API authentication tokens

**Reference**: Quote validity period from [Steps 3-6: Exchange Rates](https://docs.nexusglobalpayments.org/payment-setup/steps-3-6-exchange-rates).

#### Apache Kafka

**Chosen because:**
- **Event sourcing backbone**: Immutable event log for all payment state changes
- **Async notifications**: camt.054 notifications to FXPs
- **Audit trail**: Complete history of all messages
- **Scalability path**: Supports future multi-instance deployment

**Reference**: Event notifications align with [MESSAGE: camt.054 Bank to Customer Debit Credit Notification](https://docs.nexusglobalpayments.org/settlement-access-provision/message-camt.054-bank-to-customer-debit-credit-notification).

## Alternatives Considered

### Go for Core Gateway

**Pros:**
- Excellent performance
- Strong typing
- Good concurrency model

**Cons:**
- Slower development velocity
- Less flexible XML handling
- Smaller ecosystem for banking-specific libraries

**Decision**: Rejected for sandbox; may reconsider for production implementation.

### Java + Spring Boot

**Pros:**
- Industry standard for banking
- Mature ISO 20022 libraries (Prowide)
- Enterprise support

**Cons:**
- Heavyweight for sandbox
- Slower startup times
- More complex deployment

**Decision**: Rejected due to development overhead.

### MongoDB for Event Store

**Pros:**
- Native JSON/BSON support
- Flexible schema

**Cons:**
- Weaker transactional guarantees
- Less suitable for financial data
- Harder to enforce referential integrity

**Decision**: Rejected; PostgreSQL provides better consistency guarantees.

## Consequences

### Positive

- Fast development iteration
- Easy for community contributors
- Comprehensive API documentation generated automatically
- Strong testing support (pytest, Jest)

### Negative

- Python may have performance limitations under extreme load
- Dual-language stack requires familiarity with both Python and Node.js
- Not directly suitable for production deployment without additional hardening

### Risks

| Risk | Mitigation |
|------|------------|
| Performance bottlenecks | Profile early, optimize critical paths |
| XML parsing errors | Validate against XSD schemas |
| Type mismatches | Use Pydantic models with strict validation |

## Compliance

This decision aligns with:
- Nexus API specification structure
- ISO 20022 message handling requirements
- Docker-first deployment model

## Related Decisions

- [ADR-002](ADR-002-pluggable-actor-architecture.md): Actor containerization
- [ADR-003](ADR-003-iso20022-message-handling.md): XML processing patterns
