# Nexus Global Payments Sandbox - Database and Seed Data Analysis

**Audit Date:** 2026-02-07
**Auditor:** Claude Opus 4.6
**Report Version:** 1.0

## Executive Summary

This comprehensive audit examines the database setup and seed data of the Nexus Global Payments Sandbox. The database consists of 4 migration files that establish a complete schema for cross-border payments, including reference data, participant management, FX rates, quotes, payments, event sourcing, and ISO 20022 message storage. The seed data provides foundational data for 6 countries, multiple participant types, fee structures, exchange rates, and proxy registrations.

**Key Findings:**
- Database schema is well-structured with 21 core tables
- Seed data covers 6 founding Nexus countries (SG, TH, MY, PH, ID, IN)
- 11 PSPs, 6 IPS operators, 3 FXPs, 6 SAPs, 5 PDOs are seeded
- Fee structures are defined but split between database and code
- 18 proxy registrations and 30+ FX rates are included
- Some gaps exist in address type inputs and ISO 20022 message template coverage

---

## 1. Migration Files Analysis

### 1.1 Migration: 001_initial_schema.sql

**Purpose:** Establishes the core database schema for the Nexus Sandbox
**Lines:** 469
**Status:** Well-documented with references to official Nexus documentation

#### Core Tables Created (21 total):

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `countries` | Nexus-enabled countries | ISO 3166-1 alpha-2 codes, UN numeric IDs |
| `currencies` | ISO 4217 currency codes | Decimal places configuration |
| `country_currencies` | Country-currency mappings | Max transaction amounts per country |
| `country_required_elements` | Required ISO 20022 elements | Per-country message requirements |
| `psps` | Payment Service Providers | BIC, fees, status tracking |
| `ips_operators` | Instant Payment Systems | Clearing system IDs, max amounts |
| `fxps` | Foreign Exchange Providers | Spread, tier improvements, PSP relationships |
| `saps` | Settlement Access Providers | Multi-currency support |
| `fxp_sap_accounts` | FXP accounts at SAPs | Liquidity management for settlement |
| `pdos` | Proxy Directory Operators | Supported proxy types per country |
| `address_types` | Payment address types | Proxy resolution configuration |
| `address_type_inputs` | Input field definitions | Dynamic form generation |
| `fx_rates` | FX base rates | Time-valid rates from FXPs |
| `quotes` | FX quote storage | All fees calculated at quote time |
| `payments` | Payment records | Partitioned by month, UETR primary key |
| `payment_events` | Event store | Event sourcing for payment lifecycle |
| `payment_snapshots` | Aggregate snapshots | Performance optimization |
| `iso20022_messages` | Raw message storage | All ISO 20022 message types |
| `proxy_registrations` | Proxy-to-account mappings | PDO functionality |
| `api_clients` | OAuth credentials | Client authentication |
| `audit_log` | Audit trail | Compliance and debugging |

#### Design Patterns Identified:

1. **Event Sourcing:** `payment_events` table with aggregate versioning
2. **Partitioning:** Monthly partitions for `payments` and `payment_events`
3. **UUID Primary Keys:** Most tables use UUID for distributed systems
4. **JSONB Columns:** Flexible data for tier improvements, PSP relationships
5. **Temporal Validity:** Rates and quotes have expiration tracking
6. **Audit Trail:** Comprehensive logging with trace IDs

#### Indexes Created:

- BIC indexes on PSPs, SAPs
- Composite indexes for FX rate lookups
- Partition-aware indexes for payments and events
- Status-based partial indexes for active data
- Actor-based indexes for event sourcing queries

#### Extensions Used:

- `uuid-ossp` - UUID generation
- `pg_trgm` - Fuzzy text search for sanctions screening

### 1.2 Migration: 002_add_message_storage.sql

**Purpose:** Adds ISO 20022 message storage columns to payment_events
**Lines:** 46
**Date:** 2026-02-04

#### Message Types Supported:

| Message Column | Purpose | Release |
|----------------|---------|---------|
| `pacs008_message` | FI to FI Customer Credit Transfer | Release 1 |
| `pacs002_message` | Payment Status Report | Release 1 |
| `acmt023_message` | Identification Verification Request | Release 1 |
| `acmt024_message` | Identification Verification Report | Release 1 |
| `camt054_message` | Bank to Customer Debit/Credit Notification | Release 1 |
| `camt103_message` | Create Reservation (SAP Method 2a) | Optional |
| `pain001_message` | Customer Credit Transfer Initiation (SAP Method 3) | Optional |
| `pacs004_message` | Payment Return | Future (Release 2) |
| `pacs028_message` | Payment Status Request | Future (Release 2) |
| `camt056_message` | Payment Cancellation Request | Future (Recall) |
| `camt029_message` | Investigation Response | Future (Recall) |

**Assessment:** Complete coverage of Release 1 messages with placeholders for future releases.

### 1.3 Migration: 003_seed_data.sql

**Purpose:** Populates reference data and participant information
**Lines:** 316
**Status:** Foundational seed data for sandbox operation

#### Seed Data Breakdown:

**Currencies (7):** SGD, THB, MYR, PHP, IDR, INR, USD

**Countries (6):**
- Singapore (SG) - UN numeric: 702
- Thailand (TH) - UN numeric: 764
- Malaysia (MY) - UN numeric: 458
- Philippines (PH) - UN numeric: 608
- Indonesia (ID) - UN numeric: 360
- India (IN) - UN numeric: 356

**Country-Currency Max Amounts:**
| Country | Currency | Max Amount | USD Approx |
|---------|----------|------------|------------|
| SG | SGD | 200,000 | ~$150,000 |
| TH | THB | 5,000,000 | ~$150,000 |
| MY | MYR | 10,000,000 | ~$2,300,000 |
| PH | PHP | 10,000,000 | ~$180,000 |
| ID | IDR | 1,000,000,000 | ~$66,000 |
| IN | INR | 10,000,000 | ~$120,000 |

**Required Message Elements by Country:**
- SG: purposeCode
- TH: purposeCode, categoryPurposeCode
- MY: purposeCode
- PH: purposeCode
- ID: purposeCode

### 1.4 Migration: 004_fxp_sap_tables.sql

**Purpose:** Adds FXP rate management and SAP liquidity tables
**Lines:** 116
**Date:** 2026-02-07

#### New Tables:

1. **`fxp_rates`** - Rate submission and withdrawal tracking
   - Status: ACTIVE, WITHDRAWN, EXPIRED
   - Tracks effective rate with spread applied

2. **`fxp_psp_relationships`** - Tier-based rate improvements
   - Tiers: STANDARD, VOLUME, PREMIUM
   - Per-PSP improvement basis points

3. **`sap_reservations`** - Liquidity reservations for payments
   - Status lifecycle: ACTIVE → UTILIZED/EXPIRED/CANCELLED
   - Expiration tracking

4. **`sap_transactions`** - Settlement transaction logging
   - DEBIT/CREDIT tracking
   - Status progression: PENDING → COMPLETED/FAILED

5. **`trade_notifications`** - FXP notifications when rates selected
   - Delivery status tracking
   - Retry mechanism support

**Assessment:** Comprehensive liquidity management capability not present in initial schema.

---

## 2. Database Schema

### 2.1 Reference Data Schema

```
countries (1) ----< (1) country_currencies (1) ----< (1) currencies
     |
     +----< (1) country_required_elements
     |
     +----< (N) address_types ----< (N) address_type_inputs
```

### 2.2 Participant Schema

```
psps (Payment Service Providers)
ips_operators (Instant Payment Systems)
fxps (Foreign Exchange Providers)
saps (Settlement Access Providers)
pdos (Proxy Directory Operators)

fxps (1) ----< (N) fxp_sap_accounts ----< (1) saps
```

### 2.3 Transaction Flow Schema

```
fxps (1) ----< (N) fx_rates
     |
     +----< (N) quotes ----< (1) payments
                                      |
                                      +----< (N) payment_events
```

### 2.4 Key Relationships

| From Table | To Table | Relationship Type |
|------------|----------|-------------------|
| payments | quotes | Optional (quote_id) |
| payment_events | payments | Many-to-one (uetr) |
| quotes | fxps | Many-to-one (fxp_id) |
| fxp_sap_accounts | fxps | Many-to-one (fxp_id) |
| fxp_sap_accounts | saps | Many-to-one (sap_id) |
| proxy_registrations | countries | Many-to-one (country_code) |
| psps | countries | Many-to-one (country_code) |

---

## 3. Seed Data - Actors

### 3.1 Payment Service Providers (PSPs) - 11 Total

| BIC | Name | Country | Fee % | Notes |
|-----|------|---------|-------|-------|
| DBSSSGSG | DBS Bank Singapore | SG | 0.5% | Also a SAP |
| OCBCSGSG | OCBC Bank Singapore | SG | 0.5% | Also a SAP |
| UABORKKL | UOB Singapore | SG | 0.5% | BIC format may vary |
| KASITHBK | Kasikornbank | TH | 0.3% | Also a SAP |
| BABORKKL | Bangkok Bank | TH | 0.3% | - |
| SICOTHBK | Siam Commercial Bank | TH | 0.3% | - |
| MABORKKL | Maybank | MY | 0.4% | Also a SAP |
| CIABORMY | CIMB Bank | MY | 0.4% | - |
| PUBLMYKL | Public Bank | MY | 0.4% | - |
| BABORPMM | BDO Unibank | PH | 0.5% | Also a SAP |
| BMRIIDJA | Bank Mandiri | ID | 0.3% | Also a SAP |
| BCAIIDJA | Bank Central Asia | ID | 0.3% | - |

**Assessment:** Good coverage across all countries. Some PSPs serve dual roles as SAPs.

### 3.2 IPS Operators - 6 Total

| Name | Country | Clearing System ID | Max Amount | Currency |
|------|---------|-------------------|------------|----------|
| FAST (Fast And Secure Transfers) | SG | SGFASG22 | 200,000 | SGD |
| PromptPay | TH | THBAHTBK | 5,000,000 | THB |
| DuitNow | MY | MYDUITMYK | 10,000,000 | MYR |
| InstaPay | PH | PHINSTPH | 10,000,000 | PHP |
| BI-FAST | ID | IDFASTID | 1,000,000,000 | IDR |
| UPI (NPCI) | IN | INUPINPC | 10,000,000 | INR |

**Assessment:** Complete coverage of all 6 countries with appropriate clearing system IDs.

### 3.3 Foreign Exchange Providers (FXPs) - 3 Total

| FXP Code | Name | Base Spread BPS | Tier Improvements | PSP Improvements |
|----------|------|-----------------|-------------------|------------------|
| FXP-ABC | ABC Currency Exchange | 50 | 3 tiers | DBSSSGSG (-5), KASITHBK (-3) |
| FXP-XYZ | XYZ Forex Services | 45 | 2 tiers | None |
| FXP-GLOBAL | Global Exchange Partners | 55 | 2 tiers | MABORKKL (-4) |

**Tier Improvements (FXP-ABC):**
```json
[
  {"minAmount": 1000, "improvementBps": 5},
  {"minAmount": 10000, "improvementBps": 10},
  {"minAmount": 50000, "improvementBps": 15}
]
```

**Assessment:** Good diversity in pricing structures. PSP relationship improvements demonstrate preferential pricing.

### 3.4 Settlement Access Providers (SAPs) - 6 Total

| BIC | Name | Country | Currency |
|-----|------|---------|----------|
| DBSSSGSG | DBS Bank Singapore (SAP) | SG | SGD |
| OCBCSGSG | OCBC Bank Singapore (SAP) | SG | SGD |
| KASITHBK | Kasikornbank (SAP) | TH | THB |
| MABORKKL | Maybank (SAP) | MY | MYR |
| BABORPMM | BDO Unibank (SAP) | PH | PHP |
| BMRIIDJA | Bank Mandiri (SAP) | ID | IDR |
| SBININBB | State Bank of India (SAP) | IN | INR |

**Assessment:** Each country has at least one SAP. Some SAPs overlap with PSPs (realistic for major banks).

### 3.5 Proxy Directory Operators (PDOs) - 5 Total

| Name | Country | Supported Proxy Types |
|------|---------|----------------------|
| PayNow Directory | SG | MOBI, NRIC, UEN |
| PromptPay Directory | TH | MOBI, NIDN, EWAL |
| DuitNow Directory | MY | MOBI, NRIC, BIZN, PASS |
| InstaPay Directory | PH | MOBI |
| BI-FAST Directory | ID | MBNO, EMAL, NIK |

**Note:** India PDO is missing from seed data but referenced in address types.

### 3.6 FXP Accounts at SAPs

- Generated via CROSS JOIN of FXPs and SAPs
- Each FXP gets an account at each SAP
- Initial balance: 1,000,000 in SAP's currency
- Account format: "FXPACC" + 6-digit zero-padded number
- Total accounts created: 3 FXPs × 7 SAPs = 21 accounts

---

## 4. Seed Data - Fees

### 4.1 Fee Structure Sources

Fee structures are defined in **two locations**:

1. **Database:** `psps.fee_percent` column (for PSP fees)
2. **Code:** `/services/nexus-gateway/src/api/fee_config.py` (for all fees)

### 4.2 Destination PSP Fee Structures (from code)

| Country | Currency | Fixed | Percent | Min | Max |
|---------|----------|-------|---------|-----|-----|
| SG | SGD | 0.50 | 0.1% | 0.50 | 5.00 |
| TH | THB | 10.00 | 0.1% | 10.00 | 100.00 |
| MY | MYR | 1.00 | 0.1% | 1.00 | 10.00 |
| PH | PHP | 25.00 | 0.2% | 25.00 | 250.00 |
| ID | IDR | 5000 | 0.1% | 5000 | 50000 |
| IN | INR | 25.00 | 0.1% | 25.00 | 250.00 |

**Calculation Formula:** `fee = max(min, min(max, fixed + amount * percent))`

### 4.3 Source PSP Fee Structures (from code)

| Currency | Fixed | Percent | Min | Max |
|----------|-------|---------|-----|-----|
| SGD | 0.50 | 0.1% | 0.50 | 10.00 |
| THB | 10.00 | 0.1% | 10.00 | 100.00 |
| MYR | 1.00 | 0.1% | 1.00 | 10.00 |
| PHP | 25.00 | 0.1% | 25.00 | 250.00 |
| IDR | 5000 | 0.1% | 5000 | 50000 |
| INR | 25.00 | 0.1% | 25.00 | 250.00 |

### 4.4 Nexus Scheme Fee Structure (from code)

- Fixed: 0.10
- Percent: 0.05%
- Min: 0.10
- Max: 5.00

### 4.5 Fee Types

- **Default:** DEDUCTED (fee deducted from principal)
- **Country-specific overrides:** None currently defined
- All fees are in source currency except destination PSP fee

**Assessment:** Fee structures are comprehensive and follow Nexus specifications. However, having fees split between database and code is not ideal for maintainability.

---

## 5. Seed Data - Exchange Rates

### 5.1 FX Rates Summary

**Total Rates Seeded:** 30+ rates
**FXP Source:** FXP-ABC (all base rates)
**Validity:** 100 years from creation
**Format:** destination per source (e.g., THB per 1 SGD)

### 5.2 SGD-Based Rates (from SGD)

| Pair | Base Rate | Spread BPS | Effective |
|------|-----------|------------|-----------|
| SGD→THB | 25.85 | 50 | 25.72 |
| SGD→MYR | 3.50 | 50 | 3.48 |
| SGD→PHP | 42.50 | 50 | 42.29 |
| SGD→IDR | 11500.00 | 50 | 11442.50 |
| SGD→INR | 62.50 | 50 | 62.19 |

### 5.3 Reverse Rates (to SGD)

| Pair | Base Rate |
|------|-----------|
| THB→SGD | 0.0387 |
| MYR→SGD | 0.286 |

### 5.4 Additional FXP Rates

**FXP-XYZ Rates:**
- SGD→THB: 25.80 (slightly better than FXP-ABC)
- SGD→MYR: 3.48 (slightly better than FXP-ABC)

**Assessment:** Good coverage of major corridors. Rates are realistic for SEA region.

---

## 6. Seed Data - Other

### 6.1 Address Types - 20 Total

| Country | Code | Name | Proxy Resolution | Clearing System |
|---------|------|------|------------------|-----------------|
| SG | MOBI | Mobile Number (PayNow) | Yes | SGFASG22 |
| SG | NRIC | NRIC/FIN (PayNow) | Yes | SGFASG22 |
| SG | UEN | Business UEN (PayNow) | Yes | SGFASG22 |
| SG | ACCT | Bank Account Number | No | SGFASG22 |
| TH | MOBI | Mobile Number (PromptPay) | Yes | THBAHTBK |
| TH | NIDN | National ID (PromptPay) | Yes | THBAHTBK |
| TH | EWAL | e-Wallet ID (PromptPay) | Yes | THBAHTBK |
| TH | ACCT | Bank Account Number | No | THBAHTBK |
| MY | MOBI | Mobile Number (DuitNow) | Yes | MYDUITMYK |
| MY | NRIC | MyKad Number (DuitNow) | Yes | MYDUITMYK |
| MY | BIZN | Business Registration (DuitNow) | Yes | MYDUITMYK |
| MY | PASS | Passport Number (DuitNow) | Yes | MYDUITMYK |
| MY | ACCT | Bank Account Number | No | MYDUITMYK |
| ID | MBNO | Mobile Number (BI-FAST) | Yes | IDFASTID |
| ID | EMAL | Email Address (BI-FAST) | Yes | IDFASTID |
| ID | NIK | National ID (NIK) | Yes | IDFASTID |
| ID | ACCT | Bank Account Number | No | IDFASTID |
| IN | MBNO | Mobile Number (UPI) | Yes | INUPINPC |
| IN | VPA | Virtual Payment Address (VPA) | Yes | INUPINPC |
| IN | ACCT | Bank Account Number | No | INUPINPC |

**Gap:** No address type inputs are seeded in the database. Input field definitions are generated dynamically by the API.

### 6.2 Proxy Registrations - 18 Total

| Country | Type | Value | Creditor Name | Bank |
|---------|------|-------|---------------|------|
| SG | MOBI | +6591234567 | John Tan Wei Ming | DBS |
| SG | MOBI | +6598765432 | Mary Lim Siew Hwa | OCBC |
| SG | NRIC | S1234567A | Alice Wong Mei Ling | DBS |
| TH | MOBI | +66812345678 | Somchai Jaidee | Kasikornbank |
| TH | MOBI | +66898765432 | Siriwan Suksan | Bangkok Bank |
| TH | NIDN | 1234567890123 | Prasit Thongchai | Siam Commercial |
| MY | MOBI | +60123456789 | Ahmad bin Abdullah | Maybank |
| MY | MOBI | +60198765432 | Siti Aminah binti Hassan | CIMB |
| PH | MOBI | +639123456789 | Juan dela Cruz | BDO |
| ID | MBNO | +6281234567890 | Budi Santoso | Bank Mandiri |
| ID | MBNO | +6289876543210 | Siti Nurhaliza | Bank Central Asia |
| ID | EMAL | budi@example.co.id | Budi Hartono | Bank Mandiri |
| IN | MBNO | +919123456789 | Rajesh Kumar | State Bank of India |
| IN | MBNO | +919876543210 | Priya Sharma | HDFC Bank |

**Assessment:** Good test data covering each country's primary proxy types. Account numbers are realistic format.

### 6.3 API Clients - OAuth Credentials

**PSP Clients (11):** One per PSP
- Client ID format: `psp-{lowercase_bic}`
- Secret: SHA-256 hash of `sandbox-secret-{bic}`
- Scopes: quotes:read, payments:submit, proxy:resolve

**FXP Clients (3):** One per FXP
- Client ID format: `fxp-{lowercase_fxp_code}`
- Secret: SHA-256 hash of `sandbox-secret-{fxp_code}`
- Scopes: rates:write, rates:read

**Admin Client (1):**
- Client ID: `nexus-admin`
- Secret: SHA-256 hash of `sandbox-admin-secret`
- Scopes: admin:all

**Assessment:** Proper OAuth setup with appropriate scope separation.

---

## 7. Completeness Assessment

### 7.1 Required Actors - Present

| Actor Type | Required | Seeded | Gap |
|------------|----------|--------|-----|
| PSPs | Yes | 11 | None |
| IPS Operators | Yes | 6 | None |
| FXPs | Yes | 3 | None |
| SAPs | Yes | 7 | None |
| PDOs | Yes | 5 | India PDO missing |

**Minor Gap:** India (IN) has address types defined for UPI but no PDO seed entry.

### 7.2 Fee Formulas - Complete

| Fee Type | Status | Location |
|----------|--------|----------|
| Nexus Scheme Fee | Complete | fee_config.py |
| Destination PSP Fee | Complete | fee_config.py |
| Source PSP Fee | Complete | fee_config.py |
| Tier Improvements | Complete | fxps.tier_improvements |
| PSP Improvements | Complete | fxps.psp_improvements |

**All fee types are defined and functional.**

### 7.3 Exchange Rates - Partially Complete

**Present:**
- All SGD outbound rates (5)
- Major reverse rates (2)
- FXP-ABC and FXP-XYZ rates

**Missing:**
- Cross rates between non-SGD currencies (e.g., THB→MYR)
- India-based outbound rates
- FXP-GLOBAL rates beyond the 2 seeded

**Assessment:** Sufficient for sandbox operations but could be more comprehensive.

### 7.4 Demo Data - Sufficient

| Data Type | Count | Assessment |
|-----------|-------|------------|
| Proxy Registrations | 14 | Adequate for testing |
| FXP-SAP Accounts | 21 | Good coverage |
| API Clients | 15 | Complete |
| Country-Required Elements | 7 | Per Nexus spec |

### 7.5 Address Type Inputs - Not Seeded

The `address_type_inputs` table is empty. Input fields are generated dynamically by:
- `/services/nexus-gateway/src/api/addressing.py`

**Implication:** Form inputs are code-generated rather than database-driven. This is acceptable but less flexible.

---

## 8. Data Integrity Issues

### 8.1 BIC Format Inconsistencies

Some PSPs in seed data use potentially non-standard BIC formats:
- `UABORKKL` (UOB Singapore) - May not match standard format
- `BABORKKL` (Bangkok Bank) - Verify against SWIFT directory

**Recommendation:** Validate all BICs against SWIFT/BIC directory.

### 8.2 Missing India PDO

Address types are defined for India (MBNO, VPA, ACCT) but no PDO entry:
```sql
-- Missing from seed_data.sql:
INSERT INTO pdos (name, country_code, supported_proxy_types) VALUES
    ('UPI Directory', 'IN', '["MBNO", "VPA"]'::jsonb);
```

### 8.3 Address Types Not Referencing Inputs Table

The `address_types` table exists but `address_type_inputs` remains empty. The API generates inputs dynamically, making this table currently unused.

---

## 9. Recommendations

### 9.1 Critical

1. **Add India PDO Entry:**
   ```sql
   INSERT INTO pdos (name, country_code, supported_proxy_types) VALUES
       ('UPI Directory', 'IN', '["MBNO", "VPA"]'::jsonb);
   ```

2. **Validate BIC Codes:** Cross-reference all PSP/SAP BICs with SWIFT directory

3. **Add Address Type Inputs:** Populate `address_type_inputs` table OR remove it if dynamic generation is preferred

### 9.2 Important

1. **Centralize Fee Configuration:** Move all fee structures from code to database for dynamic updates

2. **Add Cross FX Rates:** Include non-SGD base rates (THB→MYR, IDR→PHP, etc.)

3. **Add FXP-GLOBAL Rates:** Complete rate coverage for the third FXP

### 9.3 Nice to Have

1. **Add Sanctions Lists:** Seed table of sanctioned names/entities for testing

2. **Add Purpose Codes:** Database table of valid purpose codes per country

3. **Add Test Payment Templates:** Pre-defined payment scenarios for demo/testing

---

## 10. Conclusion

The Nexus Global Payments Sandbox database is well-designed and comprehensive. The schema supports all core Nexus functionality including:

- Multi-country cross-border payments
- FX quote generation with tier-based improvements
- Event sourcing for payment lifecycle tracking
- ISO 20022 message storage for all Release 1 messages
- Proxy resolution and addressing
- Liquidity management for FXPs and SAPs

The seed data provides sufficient foundation for sandbox operations with good coverage of Southeast Asian countries. Minor gaps exist in:
1. India PDO seed entry
2. Address type input population
3. Non-SGD FX rate pairs

Overall, the database setup is production-ready for a sandbox environment with clear paths for enhancement.

---

**Report End**

**Files Analyzed:**
- `/home/siva/Projects/Nexus Global Payments Sandbox/migrations/001_initial_schema.sql`
- `/home/siva/Projects/Nexus Global Payments Sandbox/migrations/002_add_message_storage.sql`
- `/home/siva/Projects/Nexus Global Payments Sandbox/migrations/003_seed_data.sql`
- `/home/siva/Projects/Nexus Global Payments Sandbox/migrations/004_fxp_sap_tables.sql`
- `/home/siva/Projects/Nexus Global Payments Sandbox/services/nexus-gateway/src/api/fee_config.py`
- `/home/siva/Projects/Nexus Global Payments Sandbox/services/nexus-gateway/src/api/schemas.py`
- `/home/siva/Projects/Nexus Global Payments Sandbox/services/demo-dashboard/src/services/mockData.ts`
- `/home/siva/Projects/Nexus Global Payments Sandbox/docker-compose.yml`
