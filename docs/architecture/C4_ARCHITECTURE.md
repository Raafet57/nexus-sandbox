# C4 Architecture: Nexus Global Payments

> This document provides comprehensive C4 model architecture diagrams for the Nexus Global Payments (NGP) cross-border instant payment platform.

> [!NOTE]
> **Sandbox vs Production**: This document describes the **target production architecture** based on official Nexus specifications. The sandbox implementation uses a simplified stack:
> - **Backend**: Python 3.11+ / FastAPI (vs Go/Java in production)
> - **Protocol**: REST/JSON (vs gRPC in production)  
> - **Deployment**: Docker Compose (vs Kubernetes in production)
> - **Messaging**: Direct HTTP callbacks (vs Kafka in production)
>
> See [README.md](../../README.md) for the actual sandbox technology stack.

## Overview

The C4 model (Context, Container, Component, Code) provides a hierarchical approach to describing software architecture. This document covers the first three levels of abstraction for the Nexus system.

---

## Level 1: System Context Diagram

The System Context diagram shows Nexus and its relationship with users and external systems.

```mermaid
C4Context
    title System Context Diagram - Nexus Global Payments

    Person(sender, "Sender", "Person or business initiating cross-border payment")
    Person(recipient, "Recipient", "Person or business receiving cross-border payment")
    
    System(nexus, "Nexus Global Payments", "Multilateral payment scheme enabling instant cross-border payments between domestic IPS")
    
    System_Ext(sourceIPS, "Source IPS", "Domestic Instant Payment System in sender's country")
    System_Ext(destIPS, "Destination IPS", "Domestic Instant Payment System in recipient's country")
    System_Ext(sourcePSP, "Source PSP", "Payment Service Provider holding sender's account")
    System_Ext(destPSP, "Destination PSP", "Payment Service Provider holding recipient's account")
    System_Ext(fxp, "FX Providers", "Financial institutions providing currency exchange services")
    System_Ext(pdo, "Proxy Directories", "Services mapping proxies (mobile, email) to accounts")
    
    Rel(sender, sourcePSP, "Initiates payment via app/web")
    Rel(sourcePSP, sourceIPS, "Submits pacs.008")
    Rel(sourceIPS, nexus, "Forwards pacs.008", "ISO 20022")
    Rel(nexus, destIPS, "Forwards transformed pacs.008", "ISO 20022")
    Rel(destIPS, destPSP, "Credits recipient")
    Rel(destPSP, recipient, "Payment received notification")
    
    Rel(nexus, fxp, "Aggregates FX rates", "REST API")
    Rel(nexus, pdo, "Resolves proxies", "acmt.023/024")
```

### Actors and Responsibilities

| Actor | Type | Description |
|-------|------|-------------|
| **Sender** | Human/Business | Initiates cross-border payment via PSP app |
| **Recipient** | Human/Business | Receives funds in local currency |
| **Source PSP** | External System | Bank/payment institution holding sender's account |
| **Destination PSP** | External System | Bank/payment institution holding recipient's account |
| **Source IPS** | External System | Domestic instant payment system (sender's country) |
| **Destination IPS** | External System | Domestic instant payment system (recipient's country) |
| **FX Providers** | External System | Multi-currency liquidity providers |
| **Proxy Directories** | External System | Mobile/email to account mapping services |

---

## Level 2: Container Diagram

The Container diagram shows the high-level technology choices and how responsibilities are distributed.

```mermaid
C4Container
    title Container Diagram - Nexus Global Payments Platform

    Container_Boundary(nexus, "Nexus Platform") {
        Container(gateway, "Nexus Gateway", "Go/Java", "Central message hub connecting all IPS. Handles message transformation and routing")
        Container(fxService, "FX Quote Service", "Go", "Aggregates rates from FXPs, generates payment-specific quotes")
        Container(proxyService, "Proxy Resolution Service", "Go", "Routes proxy lookups to appropriate PDOs")
        Container(rateEngine, "Rate Engine", "Go", "Real-time rate calculation with tier-based improvements")
        Container(validationEngine, "Validation Engine", "Go", "UETR duplicate check, amount limits, compliance")
        Container(eventStore, "Event Store", "Apache Kafka", "Immutable event log for all payment events")
        Container(cache, "Rate Cache", "Redis Cluster", "Sub-ms latency for FX rates and quotes")
        Container(db, "Transaction Database", "PostgreSQL", "Payment transactions, reference data, audit trail")
        ContainerQueue(mq, "Message Queue", "Kafka", "Async payment processing and notifications")
    }
    
    System_Ext(sourceIPS, "Source IPS", "Domestic IPS")
    System_Ext(destIPS, "Destination IPS", "Domestic IPS")
    System_Ext(fxProviders, "FX Providers", "Currency exchange")
    System_Ext(pdo, "Proxy Directories", "Proxy resolution")
    
    Rel(sourceIPS, gateway, "pacs.008", "ISO 20022/HTTPS")
    Rel(gateway, destIPS, "pacs.008 (transformed)", "ISO 20022/HTTPS")
    Rel(gateway, fxService, "Quote requests", "gRPC")
    Rel(gateway, proxyService, "Proxy resolution", "gRPC")
    Rel(gateway, validationEngine, "Validation", "gRPC")
    Rel(fxService, rateEngine, "Rate calculations", "gRPC")
    Rel(rateEngine, cache, "Read/write rates", "Redis Protocol")
    Rel(fxService, fxProviders, "GET /rates", "REST/HTTPS")
    Rel(proxyService, pdo, "acmt.023/024", "ISO 20022/HTTPS")
    Rel(gateway, eventStore, "Publish events", "Kafka Protocol")
    Rel(gateway, db, "Store transactions", "PostgreSQL Protocol")
    Rel(eventStore, mq, "Stream events")
```

### Container Descriptions

| Container | Technology | Purpose |
|-----------|------------|---------|
| **Nexus Gateway** | Go/Java | Central message ingestion, transformation, and routing |
| **FX Quote Service** | Go | Aggregates real-time rates from FXPs, generates quotes |
| **Proxy Resolution Service** | Go | Handles acmt.023/024 proxy lookups |
| **Rate Engine** | Go | Applies tier-based and PSP-specific rate improvements |
| **Validation Engine** | Go | UETR checks, amount limits, compliance validation |
| **Event Store** | Apache Kafka | Immutable event log for audit and event sourcing |
| **Rate Cache** | Redis Cluster | Sub-millisecond rate retrieval for quote generation |
| **Transaction Database** | PostgreSQL 15+ | ACID-compliant transaction ledger |
| **Message Queue** | Apache Kafka | Async notifications to SAPs and FXPs |

---

## Level 3: Component Diagram - Nexus Gateway

```mermaid
C4Component
    title Component Diagram - Nexus Gateway

    Container_Boundary(gateway, "Nexus Gateway") {
        Component(ingress, "Message Ingress", "Go", "Receives ISO 20022 messages from Source IPS")
        Component(parser, "Message Parser", "Go", "Parses and validates ISO 20022 XML/JSON")
        Component(transformer, "Message Transformer", "Go", "Converts between IPS-specific formats")
        Component(router, "Payment Router", "Go", "Determines destination IPS and routing path")
        Component(quoteValidator, "Quote Validator", "Go", "Validates FX quote IDs and expiry")
        Component(uuidChecker, "UETR Dedup Service", "Go", "Checks for duplicate payment references")
        Component(amountValidator, "Amount Validator", "Go", "Validates transaction limits")
        Component(statusTracker, "Status Tracker", "Go", "Tracks pacs.002 confirmations")
        Component(egress, "Message Egress", "Go", "Sends transformed messages to Destination IPS")
        Component(eventPublisher, "Event Publisher", "Go", "Publishes payment events to Kafka")
    }
    
    Rel(ingress, parser, "Raw message")
    Rel(parser, router, "Parsed message")
    Rel(router, quoteValidator, "Quote ID")
    Rel(router, uuidChecker, "UETR")
    Rel(router, amountValidator, "Amount")
    Rel(router, transformer, "Validated message")
    Rel(transformer, egress, "Transformed message")
    Rel(egress, statusTracker, "Track outbound")
    Rel(statusTracker, eventPublisher, "Status events")
```

### Gateway Components

| Component | Responsibility |
|-----------|----------------|
| **Message Ingress** | TLS termination, receive ISO 20022 from Source IPS |
| **Message Parser** | XML/JSON parsing, schema validation |
| **Message Transformer** | XPath-based message transformation between IPS formats |
| **Payment Router** | Destination lookup, routing decisions |
| **Quote Validator** | Verify quote ID, check expiry, validate rate |
| **UETR Dedup Service** | Prevent duplicate payment processing |
| **Amount Validator** | Check against IPS max amounts |
| **Status Tracker** | Correlate pacs.002 responses |
| **Message Egress** | mTLS connection to Destination IPS |
| **Event Publisher** | Kafka event emission for audit trail |

---

## Level 3: Component Diagram - FX Quote Service

```mermaid
C4Component
    title Component Diagram - FX Quote Service

    Container_Boundary(fxService, "FX Quote Service") {
        Component(rateAggregator, "Rate Aggregator", "Go", "Collects rates from all FXPs")
        Component(tierCalculator, "Tier Calculator", "Go", "Applies tier-based rate improvements")
        Component(pspImprover, "PSP Rate Improver", "Go", "Applies PSP-specific improvements")
        Component(quoteGenerator, "Quote Generator", "Go", "Creates payment-specific quotes with expiry")
        Component(quoteStore, "Quote Store", "Go", "Persists quotes with 10-minute TTL")
        Component(intermediaryResolver, "Intermediary Resolver", "Go", "Resolves FXP account details (SAPs)")
        Component(rateNotifier, "Rate Notifier", "Go", "Notifies FXPs of market-leading rates")
    }
    
    Rel(rateAggregator, tierCalculator, "Base rates")
    Rel(tierCalculator, pspImprover, "Tiered rates")
    Rel(pspImprover, quoteGenerator, "Final rates")
    Rel(quoteGenerator, quoteStore, "Store quote")
    Rel(quoteStore, intermediaryResolver, "Quote lookup")
    Rel(rateAggregator, rateNotifier, "Market rates")
```

---

## Cross-Cutting Concerns

### Security Boundaries

```mermaid
flowchart TB
    subgraph "DMZ"
        LB[Load Balancer]
        WAF[Web Application Firewall]
    end
    
    subgraph "Application Zone"
        Gateway[Nexus Gateway]
        FXService[FX Service]
        ProxyService[Proxy Service]
    end
    
    subgraph "Data Zone"
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Kafka[(Kafka)]
    end
    
    WAF -->|mTLS| Gateway
    Gateway -->|gRPC/TLS| FXService
    Gateway -->|gRPC/TLS| ProxyService
    Gateway -->|TLS| DB
    FXService -->|TLS| Cache
    Gateway -->|TLS| Kafka
```

### Data Flow Patterns

| Pattern | Implementation |
|---------|----------------|
| **Synchronous Query** | REST API for quotes, amounts, countries |
| **Synchronous Command** | pacs.008 payment instruction processing |
| **Async Notification** | camt.054 to FXPs via Kafka → Webhook |
| **Event Sourcing** | All payment state changes as immutable events |

---

## Deployment Topology

```mermaid
flowchart TB
    subgraph "Region: Asia-Pacific"
        subgraph "K8s Cluster 1"
            GW1[Gateway Pods]
            FX1[FX Service Pods]
        end
        DB1[(Primary DB)]
        Redis1[(Redis)]
    end
    
    subgraph "Region: Europe"
        subgraph "K8s Cluster 2"
            GW2[Gateway Pods]
            FX2[FX Service Pods]
        end
        DB2[(Replica DB)]
        Redis2[(Redis)]
    end
    
    GLB[Global Load Balancer]
    GLB --> GW1
    GLB --> GW2
    DB1 -->|Streaming Replication| DB2
```

---

## Related Documents

- [Event Sourcing Patterns](EVENT_SOURCING.md)
- [Microservices Patterns](MICROSERVICES_PATTERNS.md)
- [PostgreSQL Schema](../database/POSTGRESQL_SCHEMA.md)
- [Kubernetes Deployment](../infrastructure/KUBERNETES_DEPLOYMENT.md)

---

*Generated using C4 Model best practices. Reference: [c4model.com](https://c4model.com)*
