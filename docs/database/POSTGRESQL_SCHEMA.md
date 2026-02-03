# PostgreSQL Schema Design: Nexus Global Payments

> This document defines the PostgreSQL database schema for the Nexus Global Payments platform, following best practices for high-throughput transactional systems.

## Design Principles

1. **Normalize first (3NF)** - Eliminate data redundancy; denormalize only for measured performance gains
2. **BIGINT GENERATED ALWAYS AS IDENTITY** - Preferred for PKs; UUID only for distributed/opaque IDs
3. **TIMESTAMPTZ** - Always use timezone-aware timestamps
4. **TEXT over VARCHAR** - Use CHECK constraints for length limits
5. **NUMERIC for money** - Never use floating point for financial amounts
6. **Index foreign keys** - PostgreSQL does NOT auto-index FK columns

---

## Core Tables

### Countries & Currencies

```sql
-- Countries enabled for Nexus payments
CREATE TABLE countries (
    country_code CHAR(2) PRIMARY KEY,  -- ISO 3166-1 alpha-2
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Currencies supported by each country
CREATE TABLE currencies (
    currency_code CHAR(3) PRIMARY KEY,  -- ISO 4217
    name TEXT NOT NULL,
    decimal_places SMALLINT NOT NULL DEFAULT 2,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Country-Currency mapping with max amounts
CREATE TABLE country_currencies (
    country_code CHAR(2) NOT NULL REFERENCES countries(country_code),
    currency_code CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    max_amount NUMERIC(18, 2) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (country_code, currency_code)
);
CREATE INDEX idx_country_currencies_currency ON country_currencies(currency_code);
```

### Payment Service Providers (PSPs)

```sql
-- PSPs (banks, payment institutions)
CREATE TABLE psps (
    psp_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    bic CHAR(8) NOT NULL UNIQUE,  -- SWIFT/BIC code
    name TEXT NOT NULL,
    country_code CHAR(2) NOT NULL REFERENCES countries(country_code),
    is_direct_member BOOLEAN NOT NULL DEFAULT TRUE,
    sponsoring_psp_id BIGINT REFERENCES psps(psp_id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_psps_country ON psps(country_code);
CREATE INDEX idx_psps_sponsoring ON psps(sponsoring_psp_id) WHERE sponsoring_psp_id IS NOT NULL;
```

### FX Providers (FXPs)

```sql
-- FX Providers
CREATE TABLE fxps (
    fxp_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    name TEXT NOT NULL,
    legal_entity_identifier TEXT,  -- LEI code
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- FXP-PSP relationships (for PSP-specific rate improvements)
CREATE TABLE fxp_psp_relationships (
    fxp_id BIGINT NOT NULL REFERENCES fxps(fxp_id),
    psp_id BIGINT NOT NULL REFERENCES psps(psp_id),
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('ONBOARDED', 'PREFERRED')),
    rate_improvement_bps SMALLINT NOT NULL DEFAULT 0,  -- basis points
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (fxp_id, psp_id)
);
CREATE INDEX idx_fxp_psp_psp ON fxp_psp_relationships(psp_id);
```

### Settlement Access Providers (SAPs)

```sql
-- SAPs (provide accounts to FXPs in each country)
CREATE TABLE saps (
    sap_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    psp_id BIGINT NOT NULL REFERENCES psps(psp_id),  -- SAP must be a PSP
    country_code CHAR(2) NOT NULL REFERENCES countries(country_code),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (psp_id, country_code)
);

-- FXP accounts held at SAPs
CREATE TABLE fxp_accounts (
    fxp_account_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fxp_id BIGINT NOT NULL REFERENCES fxps(fxp_id),
    sap_id BIGINT NOT NULL REFERENCES saps(sap_id),
    account_number TEXT NOT NULL,
    currency_code CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    account_type TEXT NOT NULL CHECK (account_type IN ('OPERATING', 'LIQUIDITY')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (fxp_id, sap_id, currency_code, account_type)
);
CREATE INDEX idx_fxp_accounts_fxp ON fxp_accounts(fxp_id);
CREATE INDEX idx_fxp_accounts_sap ON fxp_accounts(sap_id);
```

---

## FX Rates & Quotes

### Real-Time Rates (Ephemeral - Cache-Backed)

```sql
-- Base FX rates from FXPs (for audit; live rates in Redis)
CREATE TABLE fx_rates_log (
    rate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fxp_id BIGINT NOT NULL REFERENCES fxps(fxp_id),
    source_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    destination_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    rate NUMERIC(18, 10) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE fx_rates_log_2025_01 PARTITION OF fx_rates_log
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE fx_rates_log_2025_02 PARTITION OF fx_rates_log
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- ... continue for each month

CREATE INDEX idx_fx_rates_log_fxp ON fx_rates_log(fxp_id, created_at);
CREATE INDEX idx_fx_rates_log_pair ON fx_rates_log(source_currency, destination_currency, created_at);
```

### Rate Tiers

```sql
-- Tier-based rate improvements
CREATE TABLE rate_tiers (
    tier_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fxp_id BIGINT NOT NULL REFERENCES fxps(fxp_id),
    source_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    destination_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    min_amount NUMERIC(18, 2) NOT NULL,
    max_amount NUMERIC(18, 2),
    improvement_bps SMALLINT NOT NULL,  -- basis points improvement
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tier_amount_range CHECK (max_amount IS NULL OR max_amount > min_amount)
);
CREATE INDEX idx_rate_tiers_fxp_pair ON rate_tiers(fxp_id, source_currency, destination_currency);
```

### Quotes

```sql
-- Payment-specific FX quotes (10-minute TTL)
CREATE TABLE quotes (
    quote_id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    fxp_id BIGINT NOT NULL REFERENCES fxps(fxp_id),
    psp_id BIGINT NOT NULL REFERENCES psps(psp_id),
    source_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    destination_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    base_rate NUMERIC(18, 10) NOT NULL,
    tier_improvement_bps SMALLINT NOT NULL DEFAULT 0,
    psp_improvement_bps SMALLINT NOT NULL DEFAULT 0,
    final_rate NUMERIC(18, 10) NOT NULL,
    source_amount NUMERIC(18, 2),
    destination_amount NUMERIC(18, 2),
    amount_type TEXT NOT NULL CHECK (amount_type IN ('SOURCE', 'DESTINATION')),
    source_sap_account_id BIGINT REFERENCES fxp_accounts(fxp_account_id),
    destination_sap_account_id BIGINT REFERENCES fxp_accounts(fxp_account_id),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT quote_amount_check CHECK (source_amount IS NOT NULL OR destination_amount IS NOT NULL)
);
CREATE INDEX idx_quotes_psp ON quotes(psp_id);
CREATE INDEX idx_quotes_expires ON quotes(expires_at);
CREATE INDEX idx_quotes_fxp ON quotes(fxp_id);
```

---

## Payments

### Transaction Ledger

```sql
-- Payment transactions (immutable append-only)
CREATE TABLE payments (
    payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uetr UUID NOT NULL UNIQUE,  -- Unique End-to-End Transaction Reference
    quote_id UUID REFERENCES quotes(quote_id),
    
    -- Sender details
    source_psp_id BIGINT NOT NULL REFERENCES psps(psp_id),
    source_country_code CHAR(2) NOT NULL REFERENCES countries(country_code),
    debtor_name TEXT NOT NULL,
    debtor_account TEXT NOT NULL,
    
    -- Recipient details
    destination_psp_id BIGINT NOT NULL REFERENCES psps(psp_id),
    destination_country_code CHAR(2) NOT NULL REFERENCES countries(country_code),
    creditor_name TEXT NOT NULL,
    creditor_account TEXT NOT NULL,
    
    -- Amounts
    debtor_amount NUMERIC(18, 2) NOT NULL,
    debtor_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    source_interbank_amount NUMERIC(18, 2) NOT NULL,
    destination_interbank_amount NUMERIC(18, 2) NOT NULL,
    creditor_amount NUMERIC(18, 2) NOT NULL,
    creditor_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    exchange_rate NUMERIC(18, 10) NOT NULL,
    
    -- Fees
    source_psp_fee NUMERIC(18, 2) NOT NULL DEFAULT 0,
    destination_psp_fee NUMERIC(18, 2) NOT NULL DEFAULT 0,
    
    -- FX Provider
    fxp_id BIGINT REFERENCES fxps(fxp_id),
    source_sap_id BIGINT REFERENCES saps(sap_id),
    destination_sap_id BIGINT REFERENCES saps(sap_id),
    
    -- Status
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'SUBMITTED', 'ACCEPTED', 'REJECTED', 'BLOCKED', 'COMPLETED', 'RETURNED'
    )),
    priority TEXT NOT NULL DEFAULT 'NORM' CHECK (priority IN ('NORM', 'HIGH')),
    
    -- Purpose
    purpose_code CHAR(4),
    remittance_info TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    submitted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Raw message storage (for audit)
    pacs008_message JSONB,
    pacs002_message JSONB
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for high-volume table
CREATE TABLE payments_2025_01 PARTITION OF payments
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE payments_2025_02 PARTITION OF payments
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Indexes
CREATE INDEX idx_payments_source_psp ON payments(source_psp_id, created_at);
CREATE INDEX idx_payments_dest_psp ON payments(destination_psp_id, created_at);
CREATE INDEX idx_payments_status ON payments(status) WHERE status NOT IN ('COMPLETED', 'REJECTED');
CREATE INDEX idx_payments_created ON payments(created_at);
```

### Payment Events (Event Sourcing)

```sql
-- Immutable event log for payment state changes
CREATE TABLE payment_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id BIGINT NOT NULL,  -- No FK for performance; UETR is authority
    uetr UUID NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'PAYMENT_INITIATED', 'QUOTE_SELECTED', 'PAYMENT_SUBMITTED',
        'PAYMENT_FORWARDED', 'PAYMENT_ACCEPTED', 'PAYMENT_REJECTED',
        'PAYMENT_BLOCKED', 'PAYMENT_COMPLETED', 'PAYMENT_RETURNED',
        'INVESTIGATION_REQUESTED', 'INVESTIGATION_RESOLVED'
    )),
    event_data JSONB NOT NULL,
    actor TEXT NOT NULL,  -- 'SENDER', 'SOURCE_PSP', 'NEXUS', 'DEST_PSP', etc.
    correlation_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

CREATE TABLE payment_events_2025_01 PARTITION OF payment_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE INDEX idx_payment_events_uetr ON payment_events(uetr);
CREATE INDEX idx_payment_events_payment ON payment_events(payment_id);
CREATE INDEX idx_payment_events_type ON payment_events(event_type, created_at);
```

---

## Proxy Resolution

### Address Types

```sql
-- Address types supported by each country
CREATE TABLE address_types (
    address_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_code CHAR(2) NOT NULL REFERENCES countries(country_code),
    type_code TEXT NOT NULL,  -- 'MOBI', 'IBAN', 'ACCT', 'EMAIL', etc.
    display_name TEXT NOT NULL,
    requires_proxy_resolution BOOLEAN NOT NULL DEFAULT FALSE,
    proxy_directory_url TEXT,
    clearing_system_id TEXT,
    iso20022_path TEXT NOT NULL,  -- XPath in pacs.008
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (country_code, type_code)
);
CREATE INDEX idx_address_types_country ON address_types(country_code);

-- Address input fields for UI generation
CREATE TABLE address_inputs (
    input_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    address_type_id BIGINT NOT NULL REFERENCES address_types(address_type_id),
    field_name TEXT NOT NULL,
    display_label TEXT NOT NULL,
    input_type TEXT NOT NULL CHECK (input_type IN ('TEXT', 'SELECT', 'TEL', 'EMAIL')),
    validation_pattern TEXT,
    max_length INTEGER,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    display_order SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (address_type_id, field_name)
);
CREATE INDEX idx_address_inputs_type ON address_inputs(address_type_id);
```

---

## Compliance & Audit

### Sanctions Screening Log

```sql
-- Sanctions screening results (for compliance audit)
CREATE TABLE screening_results (
    screening_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    uetr UUID NOT NULL,
    screening_type TEXT NOT NULL CHECK (screening_type IN ('SENDER', 'RECIPIENT', 'PAYMENT')),
    screened_by TEXT NOT NULL,  -- PSP BIC or 'NEXUS'
    result TEXT NOT NULL CHECK (result IN ('CLEAR', 'MATCH', 'POTENTIAL_MATCH', 'ERROR')),
    list_matched TEXT,
    match_score NUMERIC(5, 2),
    decision TEXT CHECK (decision IN ('APPROVED', 'BLOCKED', 'PENDING_REVIEW')),
    decided_by TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_screening_payment ON screening_results(payment_id);
CREATE INDEX idx_screening_uetr ON screening_results(uetr);
CREATE INDEX idx_screening_result ON screening_results(result) WHERE result != 'CLEAR';
```

---

## Indexing Strategy Summary

| Table | Index Type | Columns | Purpose |
|-------|-----------|---------|---------|
| `payments` | B-tree | `uetr` (UNIQUE) | Payment lookup |
| `payments` | B-tree | `source_psp_id, created_at` | PSP payment history |
| `payments` | Partial | `status` WHERE NOT COMPLETED | Active payments |
| `quotes` | B-tree | `expires_at` | Quote expiry cleanup |
| `fx_rates_log` | B-tree | `created_at` (partition key) | Time-series queries |
| `payment_events` | B-tree | `uetr` | Event sourcing replay |

---

## Performance Considerations

### Partitioning Strategy

- **payments**: Monthly range partitions by `created_at`
- **payment_events**: Monthly range partitions by `created_at`
- **fx_rates_log**: Monthly range partitions by `created_at`

### Retention Policy

```sql
-- Drop old partitions after 7 years (regulatory requirement)
DROP TABLE IF EXISTS payments_2018_01;
DROP TABLE IF EXISTS payment_events_2018_01;
DROP TABLE IF EXISTS fx_rates_log_2018_01;
```

### Connection Pooling

Recommend **PgBouncer** in transaction mode for connection pooling with the Gateway service.

---

## Related Documents

- [C4 Architecture](../architecture/C4_ARCHITECTURE.md)
- [Event Sourcing Patterns](../architecture/EVENT_SOURCING.md)
- [Security Model](../security/SECURITY_MODEL.md)

---

*Schema designed following PostgreSQL best practices. Reference: [PostgreSQL Skill Guidelines]()*
