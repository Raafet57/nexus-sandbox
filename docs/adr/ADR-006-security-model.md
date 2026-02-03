# ADR-006: Security Model

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Define security architecture for the Nexus sandbox including authentication, authorization, and transport security

## Context

The Nexus scheme operates in a highly regulated financial environment. Security requirements are derived from:

1. **Nexus Scheme Rules**: Participant onboarding and authentication
2. **FATF Recommendation 16**: Originator and beneficiary information requirements
3. **ISO 27001**: Information security management
4. **PCI DSS**: Where applicable to card-linked participants

While this is a sandbox environment, we implement security measures that:
- Demonstrate production-equivalent patterns
- Protect test data from unauthorized access
- Enable security testing scenarios

### Reference Documentation

- [Obligations & Compliance](https://docs.nexusglobalpayments.org/addressing-and-proxy-resolution/obligations-on-the-proxy-directory-operator)
- [Sanctions Screening](https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening)
- [Validations, Duplicates & Fraud](https://docs.nexusglobalpayments.org/payment-processing/validations-duplicates-and-fraud)

## Decision

### Transport Security: mTLS

All inter-service communication uses **mutual TLS (mTLS)**:

```
┌──────────┐                    ┌──────────────┐
│   PSP    │──── mTLS ────────▶ │     IPS      │
└──────────┘                    └──────────────┘
                                       │
                                   mTLS │
                                       ▼
                                ┌──────────────┐
                                │    Nexus     │
                                │   Gateway    │
                                └──────────────┘
```

**Implementation:**

```yaml
# docker-compose.yml
services:
  nexus-gateway:
    volumes:
      - ./certs/nexus-gateway.crt:/etc/ssl/certs/server.crt:ro
      - ./certs/nexus-gateway.key:/etc/ssl/private/server.key:ro
      - ./certs/ca.crt:/etc/ssl/certs/ca.crt:ro
    environment:
      - TLS_ENABLED=true
      - TLS_VERIFY_CLIENT=true

  psp-sg:
    volumes:
      - ./certs/psp-sg.crt:/etc/ssl/certs/client.crt:ro
      - ./certs/psp-sg.key:/etc/ssl/private/client.key:ro
      - ./certs/ca.crt:/etc/ssl/certs/ca.crt:ro
```

**Certificate Generation Script:**

```bash
#!/bin/bash
# scripts/generate-certs.sh

# Create CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt \
    -subj "/CN=Nexus Sandbox CA/O=Nexus Global Payments"

# Generate service certificates
for SERVICE in nexus-gateway psp-sg psp-th psp-my ips-sg ips-th fxp-abc sap-dbs pdo-sg; do
    openssl genrsa -out ${SERVICE}.key 2048
    openssl req -new -key ${SERVICE}.key -out ${SERVICE}.csr \
        -subj "/CN=${SERVICE}/O=Nexus Global Payments"
    openssl x509 -req -days 365 -in ${SERVICE}.csr \
        -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out ${SERVICE}.crt
done
```

### API Authentication: OAuth 2.0 + JWT

PSPs and FXPs authenticate to Nexus using OAuth 2.0 Client Credentials flow:

**Reference**: Standard practice for B2B API authentication

```python
# Authentication flow
@router.post("/oauth/token")
async def get_access_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(None),
) -> TokenResponse:
    """
    OAuth 2.0 Token Endpoint
    
    Grant types:
    - client_credentials: For PSP/FXP API access
    
    Scopes:
    - quotes:read: Access GET /quotes
    - payments:submit: Submit payments (via ISO 20022)
    - rates:write: FXP rate submission
    - proxy:resolve: Proxy resolution
    """
    # Validate credentials against registered participants
    participant = await validate_credentials(client_id, client_secret)
    
    # Generate JWT with appropriate claims
    token = create_jwt(
        sub=participant.id,
        scope=scope.split() if scope else [],
        participant_type=participant.type,  # PSP, FXP, SAP
        country=participant.country,
        bic=participant.bic,
    )
    
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=3600,
        scope=scope,
    )
```

**JWT Claims:**

```json
{
  "sub": "psp-dbsssgsg",
  "iss": "nexus-sandbox",
  "aud": "nexus-gateway",
  "exp": 1738540800,
  "iat": 1738537200,
  "scope": ["quotes:read", "payments:submit"],
  "participant_type": "PSP",
  "country": "SG",
  "bic": "DBSSSGSG"
}
```

### Authorization: Role-Based Access Control (RBAC)

**Reference**: Derived from [Nexus actor roles](https://docs.nexusglobalpayments.org/introduction/terminology)

| Role | Allowed Actions |
|------|-----------------|
| `SOURCE_PSP` | GET /quotes, GET /countries, Submit pacs.008 |
| `DESTINATION_PSP` | Receive pacs.008, Send pacs.002 |
| `FXP` | POST /rates, DELETE /rates, Receive camt.054 |
| `SAP` | Manage FXP accounts, Process payments |
| `IPSO` | Forward messages, Report status |
| `NEXUS_ADMIN` | Full access (sandbox only) |

```python
from enum import Enum
from fastapi import Depends, HTTPException, Security

class ParticipantRole(str, Enum):
    SOURCE_PSP = "SOURCE_PSP"
    DESTINATION_PSP = "DESTINATION_PSP"
    FXP = "FXP"
    SAP = "SAP"
    IPSO = "IPSO"
    NEXUS_ADMIN = "NEXUS_ADMIN"

ENDPOINT_PERMISSIONS = {
    "GET /quotes": [ParticipantRole.SOURCE_PSP, ParticipantRole.NEXUS_ADMIN],
    "POST /rates": [ParticipantRole.FXP, ParticipantRole.NEXUS_ADMIN],
    "DELETE /rates/{id}": [ParticipantRole.FXP, ParticipantRole.NEXUS_ADMIN],
}

def require_role(*allowed_roles: ParticipantRole):
    """Dependency to enforce role-based authorization."""
    async def check_role(
        claims: JWTClaims = Depends(get_jwt_claims)
    ) -> JWTClaims:
        user_role = ParticipantRole(claims.participant_type)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role {user_role} not authorized for this endpoint"
            )
        return claims
    return check_role
```

### Data Protection

#### FATF R16 Compliance

**Reference**: [Steps 10-11: Sanctions Screening](https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening)

All payments must include originator and beneficiary information:

```python
class DebtorInfo(BaseModel):
    """Originator information per FATF R16."""
    name: str = Field(..., min_length=1, max_length=140)
    address: PostalAddress | None
    account_id: str
    
class CreditorInfo(BaseModel):
    """Beneficiary information per FATF R16."""
    name: str = Field(..., min_length=1, max_length=140)
    address: PostalAddress | None
    account_id: str
```

#### Data Encryption

| Data Type | At Rest | In Transit |
|-----------|---------|------------|
| API credentials | AES-256 encrypted | TLS 1.3 |
| Payment messages (XML) | Plain text (sandbox) | mTLS |
| PII (names, addresses) | Encrypted column | mTLS |
| Audit logs | Plain text | Internal network |

### Sanctions Screening (Simulated)

**Reference**: [Sanctions Screening](https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening)

The sandbox includes a simulated sanctions screening check:

```python
class SanctionsScreener:
    """Simulated sanctions screening for demo purposes."""
    
    # Demo sanctions list (configurable)
    DEMO_SANCTIONS_LIST = [
        "Kim Jong Un",
        "Vladimir Putin",
        "SANCTIONED ENTITY LTD",
    ]
    
    async def screen_payment(
        self,
        debtor: DebtorInfo,
        creditor: CreditorInfo,
    ) -> ScreeningResult:
        """
        Screen debtor and creditor against sanctions lists.
        
        Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening
        
        Note: This is a DEMO implementation. Production systems must use
        real-time sanctions databases (OFAC, EU, UN).
        """
        hits = []
        
        for name in [debtor.name, creditor.name]:
            for sanctioned in self.DEMO_SANCTIONS_LIST:
                if self._fuzzy_match(name, sanctioned):
                    hits.append(SanctionsHit(
                        matched_name=name,
                        list_entry=sanctioned,
                        confidence=0.95,
                    ))
        
        return ScreeningResult(
            passed=len(hits) == 0,
            hits=hits,
            screened_at=datetime.utcnow(),
        )
```

### Rate Limiting

Protect against abuse with rate limiting:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_client_id)

@router.get("/quotes")
@limiter.limit("100/minute")
async def get_quotes(...):
    ...

@router.get("/fees-and-amounts")
@limiter.limit("200/minute")
async def get_fees_and_amounts(...):
    ...
```

### Audit Logging

All security-relevant events are logged:

```python
class SecurityAuditLog(BaseModel):
    """Security audit log entry."""
    timestamp: datetime
    event_type: str  # AUTH_SUCCESS, AUTH_FAILURE, ACCESS_DENIED, etc.
    actor: str       # Client ID or BIC
    resource: str    # Endpoint or resource accessed
    action: str      # GET, POST, DELETE
    outcome: str     # SUCCESS, FAILURE
    details: dict    # Additional context
    source_ip: str
    trace_id: str
```

## Alternatives Considered

### API Key Only Authentication

**Approach**: Simple API key in header

**Pros:**
- Simpler implementation

**Cons:**
- No token expiration
- Harder to revoke
- No granular scopes

**Decision**: Rejected; OAuth 2.0 provides better security controls.

### Skip mTLS in Sandbox

**Approach**: Plain HTTP for simplicity

**Pros:**
- Easier debugging
- Simpler setup

**Cons:**
- Doesn't demonstrate production patterns
- Security testing not possible

**Decision**: Rejected; mTLS with self-signed certificates.

## Consequences

### Positive

- Production-equivalent security patterns demonstrated
- Enables security testing scenarios
- Clear audit trail

### Negative

- Certificate management complexity
- Additional setup steps for integrators
- Overhead of token refresh

## Related Decisions

- [ADR-001](ADR-001-technology-stack.md): Python libraries for JWT/OAuth
- [ADR-002](ADR-002-pluggable-actor-architecture.md): Actor authentication
