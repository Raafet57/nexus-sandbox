# ADR-003: ISO 20022 Message Handling

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Define how ISO 20022 messages are parsed, validated, transformed, and stored

## Context

Nexus uses ISO 20022 as the standard messaging format for cross-border payments. The following messages are used as documented in the [Messaging & Translation](https://docs.nexusglobalpayments.org/messaging-and-translation/key-points) section:

| Message | Name | Purpose | Direction |
|---------|------|---------|-----------|
| `pacs.008` | FI to FI Customer Credit Transfer | Payment instruction | PSP → IPS → Nexus → IPS → PSP |
| `pacs.002` | Payment Status Report | Accept/reject response | PSP → IPS → Nexus → IPS → PSP |
| `pacs.004` | Payment Return | Return funds (future) | Not yet supported |
| `acmt.023` | Identification Verification Request | Proxy resolution request | PSP → IPS → Nexus → IPS → PDO |
| `acmt.024` | Identification Verification Report | Proxy resolution response | PDO → IPS → Nexus → IPS → PSP |
| `camt.054` | Bank to Customer Debit Credit Notification | FXP notification | Nexus → FXP/SAP |

**Reference**: 
- [MESSAGE: pacs.008](https://docs.nexusglobalpayments.org/messaging-and-translation/message-pacs.008-fi-to-fi-customer-credit-transfer)
- [MESSAGE: pacs.002](https://docs.nexusglobalpayments.org/messaging-and-translation/message-pacs.002-payment-status-report)
- [MESSAGE: acmt.023](https://docs.nexusglobalpayments.org/messaging-and-translation/message-acmt.023-identification-verification-request)
- [MESSAGE: acmt.024](https://docs.nexusglobalpayments.org/messaging-and-translation/message-acmt.024-identification-verification-report)

### ISO 20022 Version

Nexus uses the **2019 edition** of ISO 20022, adhering to the [CPMI Harmonised ISO 20022 Data Requirements](https://docs.nexusglobalpayments.org/messaging-and-translation/adherence-to-cpmi-harmonised-iso-20022-data-requirements).

## Decision

### Message Processing Pipeline

```
┌─────────────────┐
│  Raw XML Input  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  XSD Validation │  ← Validate against ISO 20022 schemas
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse to Model │  ← lxml + pydantic-xml
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Business Logic  │  ← Nexus-specific validations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Store Event    │  ← PostgreSQL event store
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Transform     │  ← Country-specific adaptations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Output │  ← Render to XML
└─────────────────┘
```

### XSD Schema Storage

Store official ISO 20022 XSD schemas in `/specs/iso20022/`:

```
specs/iso20022/
├── pacs.008.001.08.xsd
├── pacs.002.001.10.xsd
├── acmt.023.001.02.xsd
├── acmt.024.001.02.xsd
├── camt.054.001.08.xsd
└── head.001.001.02.xsd    # Business Application Header
```

### Python Data Models

Use `pydantic-xml` for type-safe XML parsing:

```python
from pydantic_xml import BaseXmlModel, element, attr
from decimal import Decimal
from datetime import datetime
from uuid import UUID

class PaymentIdentification(BaseXmlModel, tag="PmtId"):
    instruction_id: str = element(tag="InstrId")
    end_to_end_id: str = element(tag="EndToEndId")
    uetr: UUID = element(tag="UETR")

class CreditTransferTransactionInfo(BaseXmlModel, tag="CdtTrfTxInf"):
    payment_id: PaymentIdentification = element(tag="PmtId")
    interbank_settlement_amount: Decimal = element(tag="IntrBkSttlmAmt")
    exchange_rate: Decimal | None = element(tag="XchgRate", default=None)
    # ... additional fields per pacs.008 spec
```

### Storage Strategy

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| Raw XML | `TEXT` column | Audit trail, debugging |
| Parsed data | `JSONB` column | Indexed queries |
| Key identifiers | Separate columns | Foreign keys, lookups |

```sql
CREATE TABLE payment_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_type VARCHAR(20) NOT NULL,  -- 'pacs.008', 'pacs.002', etc.
    uetr UUID NOT NULL,
    direction VARCHAR(10) NOT NULL,      -- 'INBOUND', 'OUTBOUND'
    raw_xml TEXT NOT NULL,
    parsed_data JSONB NOT NULL,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    
    -- Indexes
    CONSTRAINT fk_payment FOREIGN KEY (uetr) REFERENCES payments(uetr)
);

CREATE INDEX idx_messages_uetr ON payment_messages(uetr);
CREATE INDEX idx_messages_type ON payment_messages(message_type);
CREATE INDEX idx_messages_received ON payment_messages(received_at);
```

### Message Transformation

Nexus performs transformations as documented in [Translation To/From Domestic Message Formats](https://docs.nexusglobalpayments.org/messaging-and-translation/translation-to-from-domestic-message-formats):

```python
class MessageTransformer:
    """Transform messages between Nexus standard and IPS-specific formats."""
    
    def transform_for_destination(
        self,
        message: Pacs008,
        destination_ips: str
    ) -> Pacs008:
        """Apply destination IPS-specific transformations."""
        
        # Example: Some IPS require different date formats
        if destination_ips == "THBAHTBK":  # Thailand
            # Thailand-specific transformations
            pass
        
        # Example: Purpose code requirements
        # Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/purpose-codes
        if message.purpose_code is None:
            message.purpose_code = self._derive_purpose_code(message)
        
        return message
```

### Validation Rules

**Reference**: [Validations, Duplicates & Fraud](https://docs.nexusglobalpayments.org/payment-processing/validations-duplicates-and-fraud)

```python
class MessageValidator:
    """Validate ISO 20022 messages per Nexus requirements."""
    
    def validate_pacs008(self, message: Pacs008) -> ValidationResult:
        errors = []
        
        # 1. Single transaction only (Nexus requirement)
        # Reference: https://docs.nexusglobalpayments.org/payment-setup/scope-of-nexus-payments
        if message.number_of_transactions != 1:
            errors.append("Nexus only accepts single transactions")
        
        # 2. UETR must be present
        if not message.payment_id.uetr:
            errors.append("UETR is required")
        
        # 3. Amount limits
        # Reference: https://docs.nexusglobalpayments.org/fx-provision/maximum-value-of-a-nexus-payment
        max_amount = self.get_max_amount(message.source_currency)
        if message.interbank_settlement_amount > max_amount:
            errors.append(f"Amount exceeds limit of {max_amount}")
        
        # 4. Required fields per destination country
        # Reference: https://docs.nexusglobalpayments.org/apis/countries response
        required_fields = self.get_required_fields(message.destination_country)
        for field in required_fields:
            if not getattr(message, field, None):
                errors.append(f"Field {field} is required for {message.destination_country}")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

## Alternatives Considered

### JSON-based Message Format Internally

**Approach**: Convert all XML to JSON immediately, work with JSON internally

**Pros:**
- Easier to work with in Python/Node.js
- Better tooling support

**Cons:**
- Loss of XML fidelity
- Cannot regenerate exact original message
- ISO 20022 is XML-native

**Decision**: Rejected; maintain XML fidelity, use JSONB for queries only.

### Protocol Buffers for Internal Communication

**Approach**: Use protobuf between services, XML only at boundaries

**Pros:**
- Type safety
- Performance

**Cons:**
- Additional serialization layer
- Complexity
- Debugging harder

**Decision**: Rejected; JSONB provides good balance.

### Third-party ISO 20022 Libraries

**Libraries Considered:**
- `iso20022` (Python): Basic parsing
- Prowide ISO 20022 (Java): Comprehensive but Java-only
- `iso20022-rs` (Rust): Performance but FFI complexity

**Decision**: Use pydantic-xml for Python with custom models. This provides:
- Full control over parsing logic
- Type safety via Pydantic
- Easy customization for Nexus-specific extensions

## Consequences

### Positive

- Full XML message fidelity preserved
- Type-safe parsing with validation
- Efficient queries via JSONB indexes
- Clear audit trail with raw XML storage

### Negative

- Custom parsing logic to maintain
- XSD schema updates require model updates
- Dual storage (raw + parsed) increases storage

### Message Element References

Key pacs.008 elements as documented in [Specific Message Elements](https://docs.nexusglobalpayments.org/messaging-and-translation/specific-message-elements):

| Element | XPath | Description |
|---------|-------|-------------|
| UETR | `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/PmtId/UETR` | Unique End-to-end Transaction Reference |
| Interbank Amount | `/.../CdtTrfTxInf/IntrBkSttlmAmt` | Amount transferred between banks |
| Exchange Rate | `/.../CdtTrfTxInf/XchgRate` | FX rate applied |
| Quote ID | `/.../CdtTrfTxInf/XchgRateInf/CtrctId` | Reference to accepted quote |
| Debtor | `/.../CdtTrfTxInf/Dbtr` | Sender details (FATF R16) |
| Creditor | `/.../CdtTrfTxInf/Cdtr` | Recipient details |
| Intermediary Agent 1 | `/.../CdtTrfTxInf/IntrmyAgt1` | Source SAP BIC |
| Intermediary Agent 2 | `/.../CdtTrfTxInf/IntrmyAgt2` | Destination SAP BIC |

## Related Decisions

- [ADR-001](ADR-001-technology-stack.md): Python lxml for XML processing
- [ADR-004](ADR-004-event-sourcing-strategy.md): Message events in event store
