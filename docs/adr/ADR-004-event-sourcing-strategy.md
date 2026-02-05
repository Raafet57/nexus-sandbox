# ADR-004: Event Sourcing Strategy

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Define how payment state is captured, stored, and replayed using event sourcing

## Context

The Nexus payment flow involves multiple state transitions across distributed actors, as documented in [Payment Processing](https://docs.nexusglobalpayments.org/payment-processing/key-points). Each payment passes through clearly defined stages:

```
Quote Request → Quote Selected → Payment Initiated → Payment Forwarded → 
Payment Accepted/Rejected → Sender Notified → Completed
```

**Reference**: [Payment Setup Steps](https://docs.nexusglobalpayments.org/payment-setup/key-points) and [Step 17: Accept the confirmation](https://docs.nexusglobalpayments.org/payment-setup/step-17-accept-the-confirmation-and-notify-sender)

### Requirements

1. **Audit Trail**: Complete history of all state changes for compliance
2. **Temporal Queries**: "What was the state at time T?"
3. **Replay Capability**: Rebuild current state from events
4. **Debugging**: Trace exactly what happened in a payment flow
5. **Notifications**: Trigger downstream actions (camt.054 to FXPs)

## Decision

### Event Sourcing with CQRS

Implement **Event Sourcing** with **Command Query Responsibility Segregation (CQRS)**:

- **Write Side**: Append-only event log
- **Read Side**: Materialized projections for queries

### Aggregate: Payment

The **Payment** is the primary aggregate, identified by **UETR** (Unique End-to-end Transaction Reference).

**Reference**: [UETR in pacs.008](https://docs.nexusglobalpayments.org/messaging-and-translation/specific-message-elements)

```python
@dataclass
class PaymentAggregate:
    """Payment aggregate root - all state changes via events."""
    
    uetr: UUID
    version: int = 0
    status: PaymentStatus = PaymentStatus.PENDING
    events: list[PaymentEvent] = field(default_factory=list)
    
    def apply_event(self, event: PaymentEvent) -> None:
        """Apply event to update aggregate state."""
        match event.event_type:
            case PaymentEventType.INITIATED:
                self.status = PaymentStatus.INITIATED
            case PaymentEventType.FORWARDED:
                self.status = PaymentStatus.FORWARDED
            case PaymentEventType.ACCEPTED:
                self.status = PaymentStatus.COMPLETED
            case PaymentEventType.REJECTED:
                self.status = PaymentStatus.REJECTED
        
        self.version += 1
        self.events.append(event)
```

### Event Schema

```python
class PaymentEventType(str, Enum):
    # Quote phase
    QUOTE_REQUESTED = "QUOTE_REQUESTED"
    QUOTE_GENERATED = "QUOTE_GENERATED"
    QUOTE_SELECTED = "QUOTE_SELECTED"
    
    # Proxy resolution phase
    PROXY_RESOLUTION_REQUESTED = "PROXY_RESOLUTION_REQUESTED"
    PROXY_RESOLVED = "PROXY_RESOLVED"
    PROXY_RESOLUTION_FAILED = "PROXY_RESOLUTION_FAILED"
    
    # Payment phase
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_VALIDATED = "PAYMENT_VALIDATED"
    PAYMENT_VALIDATION_FAILED = "PAYMENT_VALIDATION_FAILED"
    PAYMENT_FORWARDED = "PAYMENT_FORWARDED"
    PAYMENT_ACCEPTED = "PAYMENT_ACCEPTED"
    PAYMENT_REJECTED = "PAYMENT_REJECTED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    
    # Notification phase
    FXP_NOTIFIED = "FXP_NOTIFIED"
    SENDER_NOTIFIED = "SENDER_NOTIFIED"


class PaymentEvent(BaseModel):
    """Immutable payment event."""
    
    event_id: UUID = Field(default_factory=uuid4)
    event_type: PaymentEventType
    uetr: UUID                      # Aggregate ID
    version: int                    # Optimistic concurrency
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    actor: str                      # BIC or 'NEXUS'
    correlation_id: UUID | None     # For tracing
    data: dict                      # Event-specific payload
    
    class Config:
        frozen = True  # Immutable
```

### Event Store Schema

```sql
-- Event store table
CREATE TABLE payment_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    uetr UUID NOT NULL,
    version INT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor VARCHAR(20) NOT NULL,
    correlation_id UUID,
    data JSONB NOT NULL,
    
    -- Ensure ordering within aggregate
    CONSTRAINT unique_aggregate_version UNIQUE (uetr, version)
);

-- Indexes for common queries
CREATE INDEX idx_events_uetr ON payment_events(uetr);
CREATE INDEX idx_events_type ON payment_events(event_type);
CREATE INDEX idx_events_occurred ON payment_events(occurred_at);
CREATE INDEX idx_events_actor ON payment_events(actor);

-- Partition by month for performance
CREATE TABLE payment_events_2026_02 PARTITION OF payment_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### Event Mapping to Nexus Flow

| Nexus Step | Event Type | Data |
|------------|------------|------|
| Step 3: Quote request | `QUOTE_REQUESTED` | `{amount, sourceCurrency, destCurrency}` |
| Step 4: Quotes generated | `QUOTE_GENERATED` | `{quotes: [...], validUntil}` |
| Step 5: Quote selected | `QUOTE_SELECTED` | `{quoteId, fxpId, rate}` |
| Step 8: Proxy resolution | `PROXY_RESOLVED` | `{proxyType, creditorName, creditorAccount}` |
| Step 13-14: pacs.008 created | `PAYMENT_INITIATED` | `{pacs008Xml, messageId}` |
| Step 15: Sent to IPS | `PAYMENT_FORWARDED` | `{destinationIps, forwardedAt}` |
| Step 17: ACCC received | `PAYMENT_ACCEPTED` | `{pacs002Xml, acceptedAt}` |
| Step 17: RJCT received | `PAYMENT_REJECTED` | `{pacs002Xml, reasonCode}` |
| Notification | `FXP_NOTIFIED` | `{camt054Xml, fxpId}` |

**Reference**: [Steps 1-17 Payment Flow](https://docs.nexusglobalpayments.org/payment-setup/key-points)

### Projections (Read Models)

#### Payment Status Projection

```sql
-- Materialized view for payment status queries
CREATE TABLE payment_status_projection (
    uetr UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    source_psp VARCHAR(20),
    destination_psp VARCHAR(20),
    source_currency VARCHAR(3),
    destination_currency VARCHAR(3),
    source_amount DECIMAL(18, 2),
    destination_amount DECIMAL(18, 2),
    exchange_rate DECIMAL(18, 6),
    quote_id UUID,
    fxp_id VARCHAR(20),
    initiated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    total_duration_seconds INT,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INT NOT NULL DEFAULT 1
);

CREATE INDEX idx_status_status ON payment_status_projection(status);
CREATE INDEX idx_status_source_psp ON payment_status_projection(source_psp);
CREATE INDEX idx_status_dest_psp ON payment_status_projection(destination_psp);
```

#### Timeline Projection

```sql
-- Denormalized timeline for API response
CREATE TABLE payment_timeline_projection (
    uetr UUID NOT NULL,
    sequence INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    actor VARCHAR(20) NOT NULL,
    details JSONB,
    
    PRIMARY KEY (uetr, sequence)
);
```

### Snapshotting Strategy

Create snapshots every 50 events to optimize aggregate loading:

```sql
CREATE TABLE payment_snapshots (
    uetr UUID PRIMARY KEY,
    version INT NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```python
class PaymentRepository:
    """Repository for loading/saving payment aggregates."""
    
    SNAPSHOT_FREQUENCY = 50
    
    async def load(self, uetr: UUID) -> PaymentAggregate:
        # Try to load from snapshot first
        snapshot = await self.load_snapshot(uetr)
        
        if snapshot:
            aggregate = PaymentAggregate.from_snapshot(snapshot)
            # Load events after snapshot
            events = await self.load_events_after(uetr, snapshot.version)
        else:
            aggregate = PaymentAggregate(uetr=uetr)
            events = await self.load_all_events(uetr)
        
        for event in events:
            aggregate.apply_event(event)
        
        return aggregate
```

## Alternatives Considered

### State-based Storage

**Approach**: Store current state only, update in place

**Pros:**
- Simpler queries
- Less storage

**Cons:**
- No audit trail
- Cannot answer temporal queries
- Lost information on state transitions

**Decision**: Rejected; audit trail is essential for payment compliance.

### Full Event Sourcing (No CQRS)

**Approach**: Rebuild state from events on every query

**Pros:**
- Single source of truth

**Cons:**
- Performance issues for complex queries
- Cannot efficiently join across aggregates

**Decision**: Use CQRS with projections for read performance.

### External Event Store (EventStoreDB)

**Approach**: Use specialized event store database

**Pros:**
- Purpose-built for event sourcing
- Subscription support

**Cons:**
- Additional infrastructure
- Operational complexity
- Overkill for sandbox

**Decision**: PostgreSQL with custom event tables is sufficient for sandbox.

## Consequences

### Positive

- Complete audit trail for every payment
- Temporal queries: "What was the status at time T?"
- Debugging: Replay exact sequence of events
- Easy to add new projections without schema changes

### Negative

- Storage overhead from event history
- Eventual consistency between events and projections
- Complexity of maintaining projections

### Compliance Alignment

Event sourcing directly supports Nexus compliance requirements:

| Requirement | How Events Help |
|-------------|-----------------|
| **Audit trail** | Every state change recorded |
| **Traceability** | UETR links all events |
| **Non-repudiation** | Immutable event log |
| **Debugging** | Replay to find issues |

**Reference**: [Validations, Duplicates & Fraud](https://docs.nexusglobalpayments.org/payment-processing/validations-duplicates-and-fraud)

## Related Decisions

- [ADR-001](ADR-001-technology-stack.md): PostgreSQL for event store
- [ADR-003](ADR-003-iso20022-message-handling.md): Raw XML stored in event data
