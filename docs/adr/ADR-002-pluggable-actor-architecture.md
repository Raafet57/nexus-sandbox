# ADR-002: Pluggable Actor Architecture

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Design an architecture that allows third parties to plug in their own actor implementations

## Context

The Nexus Global Payments ecosystem involves multiple actor types as defined in the [official documentation](https://docs.nexusglobalpayments.org/introduction/terminology):

| Actor | Full Name | Role |
|-------|-----------|------|
| **PSP** | Payment Service Provider | Banks and payment apps that serve senders/recipients |
| **IPS** | Instant Payment System | Domestic clearing infrastructure (FAST, PromptPay, DuitNow) |
| **IPSO** | Instant Payment System Operator | Operates the IPS |
| **FXP** | Foreign Exchange Provider | Provides currency conversion |
| **SAP** | Settlement Access Provider | Holds accounts for FXPs in IPS |
| **PDO** | Proxy Directory Operator | Resolves proxies (mobile, email) to accounts |

**Reference**: [Chapter 2.3 of the Nexus (2024) Report](https://www.nexusglobalpayments.org/wp-content/uploads/2025/03/Project-Nexus-Report-Phase-3.pdf)

### Requirements

1. Each actor must be independently deployable
2. Third parties must be able to replace our simulator with their own implementation
3. Actor behavior must be configurable without code changes
4. All actors must communicate via well-defined API contracts

## Decision

### Architecture Pattern: Microservices with API Contracts

Each actor is implemented as a **standalone Docker container** with:

1. **OpenAPI specification** defining the actor's API contract
2. **Environment variable configuration** for behavior customization
3. **Health check endpoints** for orchestration
4. **Webhook support** for asynchronous notifications

### Container Design

```yaml
# docker-compose.yml structure
services:
  # Core Gateway
  nexus-gateway:
    image: nexus-sandbox/gateway:latest
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - kafka

  # Actor Simulators (replaceable)
  psp-sg:
    image: nexus-sandbox/psp-simulator:latest
    environment:
      - PSP_BIC=DBSSSGSG
      - PSP_COUNTRY=SG
      - PSP_NAME=DBS Bank Singapore

  psp-th:
    image: nexus-sandbox/psp-simulator:latest
    environment:
      - PSP_BIC=KASITHBK
      - PSP_COUNTRY=TH
      - PSP_NAME=Kasikorn Bank Thailand
```

### Pluggable Implementation Pattern

Users can replace any actor with their own implementation:

```yaml
# docker-compose.override.yml (user customization)
services:
  psp-sg:
    # Replace with custom implementation
    image: my-company/my-psp-implementation:v1.0
    environment:
      - PSP_BIC=MYPSSGSG
      - NEXUS_GATEWAY_URL=http://nexus-gateway:8000
```

### Actor API Contracts

#### PSP Simulator Contract

**Reference**: [Payment Processing](https://docs.nexusglobalpayments.org/payment-processing/key-points)

```yaml
# Inbound (from Nexus/IPS)
POST /payments/receive          # Receive pacs.008 for crediting
POST /payments/{uetr}/status    # Receive pacs.002 status update

# Outbound (to IPS)
POST /payments/initiate         # Initiate new payment (demo UI)

# Callbacks
POST /webhooks/payment-completed   # Notification of completion
```

#### IPS Simulator Contract

**Reference**: [Role of the IPSO](https://docs.nexusglobalpayments.org/payment-processing/role-and-responsibilities-of-the-instant-payment-system-operator-ipso)

```yaml
# From PSP
POST /clearing/submit           # PSP submits pacs.008

# From Nexus Gateway  
POST /clearing/forward          # Nexus forwards pacs.008 to dest IPS

# To PSP
POST /clearing/deliver          # Deliver payment to destination PSP
```

#### FXP Simulator Contract

**Reference**: [Role of the FX Provider](https://docs.nexusglobalpayments.org/fx-provision/role-of-the-fx-provider)

```yaml
# To Nexus
POST /rates                     # Submit FX rates
DELETE /rates/{rateId}          # Withdraw rate

# From Nexus
POST /notifications/payment     # Receive camt.054 notifications
GET /account/balance            # Query account balance at SAP
```

#### SAP Simulator Contract

**Reference**: [Role of the Settlement Access Provider](https://docs.nexusglobalpayments.org/settlement-access-provision/role-of-the-settlement-access-provider-sap)

```yaml
# Account management
GET /accounts/{fxpId}           # Query FXP account
POST /accounts/{fxpId}/credit   # Credit FXP account
POST /accounts/{fxpId}/debit    # Debit FXP account

# Liquidity
GET /liquidity/alerts           # Check liquidity status
```

#### PDO Simulator Contract

**Reference**: [Role of the Proxy Directory Operator](https://docs.nexusglobalpayments.org/addressing-and-proxy-resolution/role-of-the-proxy-directory-operator-pdo)

```yaml
# Proxy resolution
POST /proxy/resolve             # Resolve proxy to account
  # Input: acmt.023 (Identification Verification Request)
  # Output: acmt.024 (Identification Verification Report)
```

### Configuration Schema

Each actor supports standardized environment variables:

```bash
# Identity
ACTOR_TYPE=PSP|IPS|FXP|SAP|PDO
ACTOR_ID=unique-identifier
ACTOR_NAME="Human Readable Name"

# Nexus connectivity
NEXUS_GATEWAY_URL=http://nexus-gateway:8000
NEXUS_API_KEY=xxx

# Actor-specific (PSP example)
PSP_BIC=DBSSSGSG
PSP_COUNTRY=SG
PSP_MAX_AMOUNT=200000
PSP_CURRENCY=SGD
PSP_FEE_PERCENT=0.5

# Behavior modifiers
RESPONSE_DELAY_MS=500
REJECT_PROBABILITY=0.01
SANCTIONS_CHECK_ENABLED=true
```

## Alternatives Considered

### Monolithic Simulator

**Approach**: Single application simulating all actors

**Pros:**
- Simpler deployment
- Easier debugging

**Cons:**
- Cannot replace individual actors
- Not representative of real distributed system
- Harder to test integration scenarios

**Decision**: Rejected; does not support pluggable architecture.

### gRPC Contracts

**Approach**: Use gRPC instead of REST for inter-actor communication

**Pros:**
- Strong typing
- Better performance
- Bi-directional streaming

**Cons:**
- Higher barrier for third-party integrators
- More complex debugging
- Nexus API is REST-based

**Decision**: Rejected; REST aligns with official Nexus API design.

### Service Mesh (Istio/Linkerd)

**Approach**: Use service mesh for inter-service communication

**Pros:**
- mTLS out of the box
- Advanced traffic management

**Cons:**
- Overkill for sandbox
- Complex setup
- Resource intensive

**Decision**: Rejected for sandbox; recommended for production deployment.

## Consequences

### Positive

- Third parties can test their implementations against the sandbox
- Each actor can be developed and tested independently
- Configuration-driven behavior enables diverse test scenarios
- Mirrors the distributed nature of real Nexus deployment

### Negative

- More complex local development setup
- Network latency between containers
- Debugging distributed issues is harder

### Risks

| Risk | Mitigation |
|------|------------|
| API contract drift | Generate clients from OpenAPI specs |
| Configuration errors | Validate env vars on startup |
| Network partitions | Health checks and retry logic |

## Implementation Requirements

1. **OpenAPI specs** in `/specs/` directory for each actor type
2. **Health endpoints** (`GET /health`) on all services
3. **Startup validation** of required environment variables
4. **Graceful shutdown** handling SIGTERM

## Related Decisions

- [ADR-001](ADR-001-technology-stack.md): Technology choices for each actor type
- [ADR-003](ADR-003-iso20022-message-handling.md): Message format between actors
