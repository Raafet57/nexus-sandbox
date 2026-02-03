# ADR-011: Developer Observability and API Documentation

**Status**: Accepted  
**Date**: 2026-02-03  
**Decision Makers**: Development Team  
**Technical Story**: Define how developers view message history and access API documentation

## Context

Developers testing the Nexus sandbox need:
1. Visibility into the 17-step payment lifecycle
2. Access to raw ISO 20022 XML messages sent/received
3. Browsable API documentation
4. Debug information for troubleshooting test scenarios

### Questions Addressed

Based on NotebookLM research against official Nexus documentation:

1. Does Nexus recommend exposing OpenAPI/Swagger endpoints?
2. What debug information should be visible in developer dashboards?
3. How should developers view message history?

## Decision

### 1. API Documentation: OpenAPI/Swagger Standard

**Reference**: NotebookLM 2026-02-03 research

FastAPI automatically provides:
- `/docs` - Swagger UI (interactive testing)
- `/redoc` - ReDoc (reference documentation)
- `/openapi.json` - Raw OpenAPI 3.0 spec

**Dashboard Integration**: Add navigation link to `/docs` for developer access.

### 2. Payments Explorer UI

Implement a "Message Inspector" component showing:

#### Required Debug Fields (per NotebookLM)

| Field | Purpose | Source |
|-------|---------|--------|
| UETR | Primary correlation key | pacs.008 `<UETR>` |
| Quote ID | Link to FX rate | POST /quotes response |
| Timestamps (UTC) | SLA verification | `<AccptncDtTm>` |
| Status Codes | Error diagnosis | pacs.002 `<TxSts>`, `<StsRsnInf>` |
| Full XML | Debug transformations | Raw pacs.008, pacs.002 |
| Intermediary Agents | SAP routing verification | `<IntrmyAgt1>`, `<IntrmyAgt2>` |

#### API Endpoints

```yaml
/v1/payments:
  get:
    summary: List recent payments
    parameters:
      - status: ACCC | RJCT | PDNG
      - limit: 20

/v1/payments/{uetr}/events:
  get:
    summary: Get all lifecycle events
    response:
      - event_id, event_type, occurred_at
      - pacs008_message (raw XML)
      - pacs002_message (raw XML)
      - data (JSON metadata)

/v1/payments/{uetr}/status:
  get:
    summary: Get current status with reason codes
    response:
      - uetr, status, reason_code
      - source_psp, destination_psp
      - amounts, fx_rate
```

### 3. Frontend Integration

```typescript
// DevDebugPanel shows:
// 1. Transaction Tracking (UETR, Quote ID, Intermediary Agents)
// 2. Gateway Transformations (Agent swapping, Amount conversion)
// 3. Actor Response Codes (ACCC, AB03, AB04, AM04)
// 4. Raw XML viewer (collapsible, syntax highlighted)
```

### 4. camt.054 Reconciliation Reports

For batch verification, expose:

```yaml
/v1/reconciliation/reports:
  get:
    parameters:
      - date_from, date_to
      - status: ACCC | RJCT
    response:
      - Periodic camt.054 equivalent
      - All transactions with final status
```

## Implementation

### Existing Components ✅

1. **DevDebugPanel** (`/components/DevDebugPanel.tsx`) - Already implemented
2. **Payments Explorer API** (`payments_explorer.py`) - Basic implementation
3. **Swagger UI** (`/docs`) - Automatic via FastAPI

### Enhancements Needed

1. Add `/payments/{uetr}/messages` endpoint for raw XML
2. Add "API Docs" link to dashboard navigation
3. Enhance DevDebugPanel with XML syntax highlighting

## Consequences

### Positive
- Developers can trace full payment lifecycle
- Raw XML inspection enables debugging of transformations
- Self-service API exploration via Swagger UI
- Matches production Service Desk functionality

### Negative
- Additional API endpoints to maintain
- XML storage increases database size
- Security consideration: sanitize sensitive data in logs

## Related Decisions

- [ADR-008](ADR-008-actor-callback-format.md): Callback format (XML/JSON)
- [ADR-010](ADR-010-payment-lifecycle-persistence.md): Event persistence

## Sources

- NotebookLM query 2026-02-03: "Developer observability and API documentation"
- https://docs.nexusglobalpayments.org/apis/overview
