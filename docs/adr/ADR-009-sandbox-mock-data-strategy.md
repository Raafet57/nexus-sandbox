# ADR-009: Sandbox Mock Data Strategy

**Status**: Accepted  
**Date**: 2026-02-03  
**Decision Makers**: Development Team  
**Technical Story**: Define strategy for mock data in sandbox to enable demo flows without database persistence

## Context

The sandbox demo dashboard needs to function for demonstrations and testing without requiring:
- Pre-populated database records
- Manual quote creation steps
- Actor registration before every demo

### Problem Statement

API endpoints that query databases fail with 404/500 errors when expected records don't exist, blocking demo flows even though business logic is correct.

## Decision

### Fallback Mock Data Pattern

When database queries return empty results, sandbox endpoints **return realistic mock data** instead of failing:

```python
# Pattern used across sandbox endpoints
if not db_result:
    # Return mock data for sandbox demo
    return mock_response_for_sandbox()

# Production path - use real data
return format_db_result(db_result)
```

### Endpoints Using This Pattern

| Endpoint | Mock Data Returned |
|----------|-------------------|
| `GET /quotes/{id}/intermediary-agents` | Singapore FAST SAP + Thailand PromptPay SAP |
| `GET /quotes` | Example quotes for selected corridor |
| `POST /v1/addressing/resolve` | Mock beneficiary (Rajesh Kumar, SBININBB) |
| `GET /countries` | Full country list from seed data |

### Mock Data Values (Consistent Across Demo)

```json
{
  "sap_source": {
    "sapBicfi": "FASTSGS0",
    "sapName": "Singapore FAST SAP",
    "accountId": "SG12345678901234",
    "currency": "SGD"
  },
  "sap_destination": {
    "sapBicfi": "PPAYTH2B",
    "sapName": "Thailand PromptPay SAP",
    "accountId": "TH98765432109876",
    "currency": "THB"
  },
  "fxp": {
    "fxpId": "FXP_EXAMPLE_001",
    "fxpName": "Example FX Provider Pte Ltd"
  },
  "beneficiary": {
    "name": "Rajesh Kumar",
    "accountNumber": "IN12345678901234",
    "agentBic": "SBININBB"
  }
}
```

### When to Use Real vs Mock Data

| Scenario | Data Source |
|----------|-------------|
| Demo walkthrough | Mock data |
| Integration testing | Seeded database |
| E2E testing | Full persistence |
| Actor testing their implementation | Mix (their actor real, others mocked) |

## Consequences

### Positive
- Demo flows work immediately without setup
- Consistent visual demonstration
- Lower barrier for evaluation
- Actors can test integration without full stack

### Negative
- Mock data doesn't reflect real state
- Could mask database issues during development
- Need clear logging to distinguish mock vs real

### Logging Mock Data Usage

```python
import logging
logger = logging.getLogger(__name__)

if not db_result:
    logger.info(f"[SANDBOX] Returning mock data for {endpoint}")
    return mock_response()
```

## Related Decisions

- [ADR-002](ADR-002-pluggable-actor-architecture.md): Actor container architecture
- [ADR-007](ADR-007-testing-strategy.md): Testing pyramid (mock vs real data)
