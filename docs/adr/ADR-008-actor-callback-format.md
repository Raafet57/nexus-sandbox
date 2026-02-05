# ADR-008: Actor Callback Format and Authentication

**Status**: Accepted  
**Date**: 2026-02-03  
**Decision Makers**: Development Team  
**Technical Story**: Define callback/webhook format and authentication for actor integrations

## Context

The Nexus sandbox requires actors (PSPs, FXPs, SAPs) to receive callbacks for:
- Payment status reports (pacs.002)
- Account resolution responses (acmt.024)
- Payment notifications (camt.054 equivalent)

### Questions Addressed

Based on NotebookLM research against official Nexus documentation:

1. What format should callbacks use - XML or JSON?
2. What authentication is required for callback endpoints?
3. What specific endpoints must actors expose?

## Decision

### 1. Callback Format: Hybrid (XML for ISO, JSON for Notifications)

**Reference**: NotebookLM 2026-02-03 research

**ISO 20022 Messages** → `application/xml`
- `pacs.002` (Payment Status Report)
- `acmt.024` (Identification Verification Report)
- All callbacks containing full ISO 20022 message content

**Notifications and Reference Data** → `application/json`
- FXP payment completion notifications
- Reference data queries
- Non-ISO structured data

### 2. Authentication: Transport-Level Security

| Actor Type | Connectivity Method |
|------------|-------------------|
| IPS Operators | VPN over Internet |
| FX Providers | HTTPS over Internet |
| PSPs and SAPs | Connect via domestic IPS (not directly to Nexus) |

- All data encrypted in transit and at rest
- Application-level authentication (OAuth 2.0, mTLS) not explicitly required by Nexus spec
- **Sandbox assumption**: API keys for actor identification (not security)

### 3. Required Callback Endpoints

#### Source IPS Must Provide (via Query Parameters)

| Parameter | Purpose | Receives |
|-----------|---------|----------|
| `acmt024Endpoint` | Proxy resolution result | `acmt.024` XML |
| `pacs002Endpoint` | Payment status | `pacs.002` XML |

Example:
```http
POST /iso20022/pacs008?pacs002Endpoint=http://source-ips/callback/pacs002
```

#### FXP Must Expose

| Endpoint | Purpose | Format |
|----------|---------|--------|
| Payment notification | Receives UETR, amounts, rates on completion | JSON |

#### PSP and SAP Endpoints

PSPs and SAPs receive callbacks via their domestic IPS, not directly from Nexus:
- Nexus → Source IPS → Source PSP
- Nexus → Dest IPS → Dest SAP → Dest PSP

### Implementation for Sandbox

```typescript
// Actor registration request
POST /api/v1/actors/register
{
  "actorType": "PSP",
  "actorId": "my-custom-psp", 
  "bic": "MYPSSGSG",
  "callbackEndpoints": {
    "pacs002": "http://my-psp:8080/webhook/pacs002",
    "acmt024": "http://my-psp:8080/webhook/acmt024"
  }
}
```

## Consequences

### Positive
- Follows Nexus specification for message formats
- Actors can test callback handling with real XML/JSON payloads
- Sandbox mirrors production callback flow

### Negative
- XML parsing required for ISO callbacks
- Actors must implement both XML and JSON handlers

### Assumptions Documented

1. **Callback URL delivery**: IPS provides callback URLs as query parameters
2. **Format selection**: XML for ISO 20022, JSON for notifications
3. **Security**: Transport-level (HTTPS/VPN), not app-level auth in sandbox

## Related Decisions

- [ADR-002](ADR-002-pluggable-actor-architecture.md): Actor container design
- [ADR-003](ADR-003-iso20022-message-handling.md): ISO 20022 XML processing

## Sources

- NotebookLM query 2026-02-03: "Callback format and authentication for actors"
- https://docs.nexusglobalpayments.org/apis/overview
- https://docs.nexusglobalpayments.org/onboarding/connectivity-models
