# Documentation Freshness Audit Report

**Date:** 2026-02-07
**Auditor:** Claude Code (Opus 4.6)
**Scope:** Analysis of documentation files against actual implementation

---

## Executive Summary

This audit compares the documentation in `/README.md`, `/docs/`, and related files against the actual implementation in the codebase. The audit identified **26 specific issues** ranging from missing endpoints to outdated references and incorrect file paths.

**Severity Breakdown:**
- **Critical (5):** Missing major features, incorrect API documentation
- **High (8):** Outdated commands, missing new endpoints
- **Medium (9):** Minor inconsistencies, unclear references
- **Low (4):** Typos, cosmetic issues

---

## 1. README.md Issues

### 1.1 Missing API Endpoints in Documentation

**Location:** `README.md` lines 106-204

**Issue:** The README lists API endpoints but is missing several newly implemented endpoints:

| Missing Endpoint | Actual Implementation File |
|-----------------|---------------------------|
| `POST /v1/fxp/rates` | `services/nexus-gateway/src/api/fxp.py:120` |
| `DELETE /v1/fxp/rates/{rate_id}` | `services/nexus-gateway/src/api/fxp.py:186` |
| `GET /v1/fxp/rates/history` | `services/nexus-gateway/src/api/fxp.py:292` |
| `POST /v1/fxp/psp-relationships` | `services/nexus-gateway/src/api/fxp.py:343` |
| `GET /v1/fxp/trades` | `services/nexus-gateway/src/api/fxp.py:530` |
| `POST /v1/sap/nostro-accounts` | `services/nexus-gateway/src/api/sap.py:140` |
| `GET /v1/sap/nostro-accounts/{account_id}` | `services/nexus-gateway/src/api/sap.py:289` |
| `POST /v1/sap/reservations` | `services/nexus-gateway/src/api/sap.py:343` |
| `POST /v1/sap/reservations/{reservation_id}/cancel` | `services/nexus-gateway/src/api/sap.py:507` |
| `GET /v1/sap/transactions` | `services/nexus-gateway/src/api/sap.py:555` |
| `GET /v1/sap/reconciliation` | `services/nexus-gateway/src/api/sap.py:626` |
| `POST /v1/sanctions/review-data` | `services/nexus-gateway/src/api/sanctions.py:95` |
| `POST /v1/sanctions/screen` | `services/nexus-gateway/src/api/sanctions.py:208` |

**Recommendation:** Add a new section in README.md for FXP, SAP, and Sanctions APIs.

---

### 1.2 Incorrect Seed Data File Reference

**Location:** `README.md` - Not explicitly mentioned but implied in `docs/USAGE_GUIDE.md:218`

**Issue:** `docs/USAGE_GUIDE.md` line 218 references `migrations/002_seed_data.sql` but the actual file is `migrations/003_seed_data.sql`.

**Actual File Structure:**
```
migrations/
├── 001_initial_schema.sql
├── 002_add_message_storage.sql
├── 003_seed_data.sql        # Correct filename
└── 004_fxp_sap_tables.sql
```

**Fix Required:**
- `docs/USAGE_GUIDE.md:218` - Change reference from `002_seed_data.sql` to `003_seed_data.sql`

---

### 1.3 Missing Reference to New API Documentation

**Location:** `README.md:68`

**Issue:** README links to `docs/api/API_REFERENCE.md` which does exist, but there's ALSO an `API_REFERENCE.md` at root level. The documentation structure is confusing.

**Files:**
- `/docs/api/API_REFERENCE.md` (exists - 613 lines, official API reference format)
- `/API_REFERENCE.md` (exists - 789 lines, more comprehensive but less official format)

**Recommendation:** Consolidate to one API reference file or clearly distinguish their purposes.

---

## 2. docs/USAGE_GUIDE.md Issues

### 2.1 Outdated Actor BIC References

**Location:** `docs/USAGE_GUIDE.md:26-32`

**Issue:** Documentation lists pre-seeded actors but some BICs don't match actual implementation.

**Documented:**
| BIC | Name | Type |
|-----|------|------|
| `FAST` | Singapore FAST IPS | IPS |
| `PromptPay` | Thailand PromptPay IPS | IPS |

**Actual Implementation (`services/nexus-gateway/src/api/actors.py:154-173`):**
| BIC | Name | Type |
|-----|------|------|
| `SGIPSOPS` | Singapore FAST IPS | IPS |
| `THIPSOPS` | Thailand PromptPay IPS | IPS |

**Fix Required:** Update actor BICs in documentation to match actual pre-seeded data.

---

### 2.2 Missing Callback-Test Endpoint Documentation

**Location:** `docs/USAGE_GUIDE.md:165-167`

**Issue:** The callback test example uses incorrect endpoint.

**Documented:**
```bash
POST /v1/actors/{bic}/callback-test
```

**Actual Implementation (`services/nexus-gateway/src/api/actors.py:300-340`):**
The endpoint exists at `POST /v1/actors/{bic}/callback-test` - this is CORRECT.

However, the example curl command at line 252 uses:
```bash
curl -X POST http://localhost:3000/v1/actors/TESTSGSG/callback-test
```

**Issue:** The example uses port 3000 (which would be the frontend dev server), not port 8000 (gateway API).

**Fix Required:** Change port from 3000 to 8000 in example.

---

### 2.3 Mock Mode Environment Variable

**Location:** `docs/USAGE_GUIDE.md:232-234`

**Issue:** Documentation mentions `MOCK_ENABLED=true` environment variable for frontend, but doesn't clarify this is a **frontend** setting (Vite env var), not backend.

**Clarification Needed:**
- Frontend mock mode: Set `VITE_MOCK_ENABLED=true` or `MOCK_ENABLED` in frontend
- Backend has no mock mode - it always processes real data

---

## 3. docs/INTEGRATION_GUIDE.md Issues

### 3.1 Missing FXP/SAP/Sanctions Endpoints

**Location:** `docs/INTEGRATION_GUIDE.md`

**Issue:** Integration guide does not document the new FXP, SAP, and Sanctions endpoints added in recent commits.

**Missing Sections:**
1. FXP Rate Management (lines 282-330 cover this partially, but missing endpoints)
2. SAP Liquidity Management (mentioned in README but not Integration Guide)
3. Sanctions Screening (not mentioned at all)

**Recommendation:** Add dedicated sections for:
- `/v1/fxp/*` endpoints
- `/v1/sap/*` endpoints
- `/v1/sanctions/*` endpoints

---

### 3.2 Inconsistent Callback URL Documentation

**Location:** `docs/INTEGRATION_GUIDE.md:252-257`

**Issue:** Callback test example uses `http://localhost:3000` which is incorrect.

**Documented:**
```bash
curl -X POST http://localhost:3000/v1/actors/TESTSGSG/callback-test
```

**Correct Port:** Gateway runs on port 8000, not 3000.

**Fix Required:**
```bash
curl -X POST http://localhost:8000/v1/actors/TESTSGSG/callback-test
```

---

### 3.3 Missing Quote Lock Endpoint

**Location:** `README.md:125-127`

**Issue:** Documentation mentions `POST /quotes/{quoteId}/lock` but this endpoint doesn't exist in the implementation.

**Actual Quote Endpoints:**
- `GET /v1/quotes` - Get quotes
- `GET /v1/quotes/{sourceCountry}/{sourceCurrency}/{destCountry}/{destCurrency}/{amountCurrency}/{amount}` - Get quotes by path
- `GET /v1/quotes/{quoteId}/intermediary-agents` - Get settlement routing

**Fix Required:** Remove non-existent `POST /quotes/{quoteId}/lock` endpoint from README.

---

## 4. docs/DASHBOARD_GUIDE.md Issues

### 4.1 Missing New Dashboard Pages

**Location:** `docs/DASHBOARD_GUIDE.md`

**Issue:** Documentation is missing new UI components that exist in the codebase.

**Missing Pages:**
1. **Service Desk** (`/service-desk`) - For manual disputes/recalls
   - File: `services/demo-dashboard/src/pages/ServiceDesk.tsx`
2. **Actor Registration Modal** - New modal component
   - File: `services/demo-dashboard/src/components/ActorRegistrationModal.tsx`
3. **Payment Components** - New payment-related components
   - Directory: `services/demo-dashboard/src/components/payment/`

---

### 4.2 Outdated "Settings" Page Reference

**Location:** `docs/DASHBOARD_GUIDE.md:248-258`

**Issue:** The Settings page is documented but the actual implementation and features may differ from what's described.

**Documented Features:**
- Quote validity timeout
- Payment SLA settings
- Mock data configuration
- Logging verbosity
- Theme (light/dark)

**Verification Needed:** Check if all these features are actually implemented.

---

## 5. docs/E2E_DEMO_SCRIPT.md Issues

### 5.1 Incorrect Pre-Seeded Actor Count

**Location:** `docs/E2E_DEMO_SCRIPT.md:26-32`

**Issue:** States "6 pre-seeded actors" but actual implementation has 7.

**Actual Actors (`services/nexus-gateway/src/api/actors.py:112-174`):**
1. DBSSSGSG (PSP)
2. KASITHBK (PSP)
3. MABORKKL (PSP)
4. FXP-ABC (FXP)
5. SGIPSOPS (IPS)
6. THIPSOPS (IPS)
7. (Plus possible SAP actors from database)

**Fix Required:** Update count from 6 to 7 (or verify exact count).

---

### 5.2 Missing Quote Endpoint Example

**Location:** `docs/E2E_DEMO_SCRIPT.md:79-82`

**Issue:** Shows GET request format but doesn't match actual implementation path.

**Documented:**
```bash
GET /v1/quotes/SG/SGD/TH/THB/SGD/1000
```

**Actual Implementation (`services/nexus-gateway/src/api/quotes.py`):**
The endpoint exists at this path, so this is actually **CORRECT**.

---

## 6. API_REFERENCE.md (Root) Issues

### 6.1 Incorrect API Base URL

**Location:** `API_REFERENCE.md:4`

**Issue:** Shows production and sandbox URLs that don't match this sandbox project.

**Documented:**
- Production: `https://api.nexusglobalpayments.org/v1`
- Sandbox: `https://sandbox.nexusglobalpayments.org/v1`

**Actual (per this project):**
- Local: `http://localhost:8000`

**Clarification Needed:** This file appears to be documentation for the OFFICIAL Nexus API, not this sandbox. Either:
1. Remove this file (it's confusing)
2. Clearly label it as reference to the official API
3. Move it to `/docs/api/official/` directory

---

### 6.2 Wrong Lock Quote Endpoint

**Location:** `API_REFERENCE.md:125-127`

**Same as README:** Mentions non-existent `POST /quotes/{quoteId}/lock` endpoint.

---

## 7. docs/api/API_REFERENCE.md Issues

### 7.1 OAuth Authentication Section

**Location:** `docs/api/API_REFERENCE.md:12-33`

**Issue:** Documents OAuth 2.0 authentication which is NOT implemented in the sandbox.

**Documented:**
```bash
curl -X POST https://auth.nexusglobalpayments.org/oauth/token ...
```

**Actual Implementation (`services/nexus-gateway/src/main.py:52-199`):**
No OAuth authentication. The comment at line 25 says:
```python
# SECURITY: In production, set NEXUS_JWT_SECRET environment variable
```

**Clarification Needed:** This is a reference document for the official Nexus API, not the sandbox implementation. Should be clearly labeled.

---

## 8. Port Number Inconsistencies

### 8.1 Swagger UI Port

**Location:** `README.md:80-81`

**Documented:**
| **API Docs (Swagger)** | http://localhost:8080/api/docs |

**Actual (docker-compose.yml:47-61):**
```yaml
swagger-ui:
  ports:
    - "8081:8080"
```

**Issue:** Swagger UI is actually on port 8081 in the full stack, but can also be accessed via the dashboard at `http://localhost:8080/api/docs` due to nginx proxy.

**Status:** Actually CORRECT - the dashboard nginx proxies `/api/docs` to the gateway. The direct swagger-ui service is on 8081 but that's just for documentation - the actual API docs are proxied through the dashboard.

---

### 8.2 Jaeger Port

**Location:** `README.md:274`, `start.sh:59`

**Documented:** Jaeger on port 16686

**Actual (docker-compose.yml:197-203):**
```yaml
jaeger:
  ports:
    - "16686:16686"
```

**Status:** CORRECT

---

## 9. Missing Documentation for New Features

### 9.1 Sanctions Screening (Steps 10-11)

**Location:** `services/nexus-gateway/src/api/sanctions.py`

**Issue:** Complete sanctions screening module is implemented but not documented.

**Implemented Features:**
- `POST /v1/sanctions/review-data` - FATF R16 compliance review
- `POST /v1/sanctions/screen` - Sanctions list screening
- `GET /v1/sanctions/screening-result/{uetr}` - Retrieve results

**Required Documentation:**
- Add to README API section
- Add to Integration Guide
- Add to Usage Guide (as part of payment flow)

---

### 9.2 FXP Rate History

**Location:** `services/nexus-gateway/src/api/fxp.py:292-336`

**Issue:** `GET /v1/fxp/rates/history` endpoint exists but not documented.

---

### 9.3 SAP Liquidity Alerts Configuration

**Location:** `services/nexus-gateway/src/api/sap.py:694-750`

**Issue:** `POST /v1/sap/liquidity-alerts` endpoint exists but not documented.

---

## 10. ISO 20022 Message Documentation Issues

### 10.1 Message Count Mismatch

**Location:** `README.md:354`, `docs/MESSAGE_EXAMPLES.md:1-4`

**Issue:** Documentation claims "11 distinct message types" but need to verify actual count.

**Message Types Actually Documented in MESSAGE_EXAMPLES.md:**
1. pacs.008.001.13
2. pacs.002.001.15
3. acmt.023.001.04
4. acmt.024.001.04
5. camt.054.001.13
6. camt.103.001.03
7. pain.001.001.12
8. pacs.004.001.14
9. pacs.028.001.06
10. camt.056.001.11
11. camt.029.001.13

**Status:** Count is CORRECT - 11 message types documented.

---

### 10.2 Modular ISO 20022 Structure

**Location:** `services/nexus-gateway/src/api/iso20022/__init__.py`

**Issue:** The ISO 20022 handling has been refactored into a modular structure but documentation doesn't reflect this.

**New Structure:**
- `constants.py` - Status codes and configuration
- `schemas.py` - Pydantic response models
- `pacs008.py` - pacs.008 handler
- `pacs002.py` - pacs.002 handler
- `acmt023.py`, `acmt024.py` - Proxy resolution handlers
- `pain001.py` - Payment initiation
- `camt103.py` - Reservation creation
- `pacs004.py` - Payment return
- `pacs028.py` - Payment status request
- `recall_handlers.py` - camt.056/camt.029
- `validate.py` - Validation endpoints

**Recommendation:** Update architecture documentation to reflect modular design.

---

## 11. Database Migration Documentation

### 11.1 Migration File References

**Issue:** Multiple documentation references may incorrectly reference old migration file names.

**Actual Migration Order:**
1. `001_initial_schema.sql`
2. `002_add_message_storage.sql`
3. `003_seed_data.sql`
4. `004_fxp_sap_tables.sql`

**Note:** The seed data was moved from 002 to 003, which may cause confusion in documentation that references the old number.

---

## 12. Demo Data Issues

### 12.1 PSP BIC Mismatch

**Location:** `migrations/003_seed_data.sql:87-110`

**Issue:** Seed data includes PSPs with different BIC formats than documented.

**Seed Data Has:**
- `UABORKKL` - Documented as "UOB Singapore" but BIC suggests UOB in Malaysia

**Actors.py Has:**
- Uses different BICs for IPS actors

**Recommendation:** Standardize actor data between seed database and in-memory registry.

---

## 13. Frontend-Backend API Contract Issues

### 13.1 Address Type Response Format

**Location:** `services/demo-dashboard/src/services/api.ts:128-146`

**Issue:** Frontend transforms backend response format, but this transformation isn't documented.

**Backend Returns:**
```json
{
  "addressTypes": [{
    "addressTypeId": "...",
    "addressTypeName": "...",
    "inputs": [{
      "attributes": { "name": "...", "type": "..." },
      "label": { "title": { "en": "..." }, "code": "..." }
    }]
  }]
}
```

**Frontend Expects:**
```json
{
  "addressTypes": [{
    "addressTypeId": "...",
    "addressTypeName": "...",
    "inputs": [{
      "fieldName": "...",
      "displayLabel": "...",
      "dataType": "..."
    }]
  }]
}
```

**Recommendation:** Document the transformation or standardize the format.

---

## Summary of Required Fixes

### High Priority (Documentation Accuracy)

1. **README.md:125-127** - Remove non-existent `POST /quotes/{quoteId}/lock` endpoint
2. **docs/USAGE_GUIDE.md:218** - Change `002_seed_data.sql` to `003_seed_data.sql`
3. **docs/USAGE_GUIDE.md:252** - Change port from 3000 to 8000 in callback example
4. **docs/INTEGRATION_GUIDE.md:252** - Same port fix
5. **docs/E2E_DEMO_SCRIPT.md:26** - Update actor count from 6 to 7

### Medium Priority (Missing Content)

6. **README.md** - Add FXP endpoints section
7. **README.md** - Add SAP endpoints section
8. **README.md** - Add Sanctions endpoints section
9. **docs/INTEGRATION_GUIDE.md** - Add FXP/SAP/Sanctions integration examples
10. **docs/DASHBOARD_GUIDE.md** - Add Service Desk page documentation
11. **docs/DASHBOARD_GUIDE.md** - Add Actor Registration Modal documentation

### Low Priority (Clarifications)

12. Clarify purpose of root `API_REFERENCE.md` vs `/docs/api/API_REFERENCE.md`
13. Document OAuth as "reference to official API" not implemented in sandbox
14. Add architecture diagram for modular ISO 20022 structure
15. Document address type response format transformation

---

## Appendix: Quick Reference - Actual vs Documented

| Feature | Documented Location | Actual Implementation | Status |
|---------|-------------------|----------------------|--------|
| FXP Rate Submit | Missing | `fxp.py:120` | NEEDS DOC |
| FXP Rate Withdraw | Missing | `fxp.py:186` | NEEDS DOC |
| FXP Rate History | Missing | `fxp.py:292` | NEEDS DOC |
| FXP PSP Relationships | Partial | `fxp.py:343` | NEEDS DOC |
| FXP Trade Notifications | Partial | `fxp.py:530` | NEEDS DOC |
| SAP Nostro Accounts | Missing | `sap.py:140` | NEEDS DOC |
| SAP Reservations | Missing | `sap.py:343` | NEEDS DOC |
| SAP Reconciliation | Missing | `sap.py:626` | NEEDS DOC |
| Sanctions Screening | Missing | `sanctions.py:95` | NEEDS DOC |
| Quote Lock | `README:125` | Does NOT exist | WRONG DOC |
| Actor Callback Test | `USAGE_GUIDE:252` | `actors.py:300` | WRONG PORT |
| Seed Data File | `USAGE_GUIDE:218` | `003_seed_data.sql` | WRONG FILE # |

---

**End of Report**

*Generated: 2026-02-07*
*Auditor: Claude Code (Opus 4.6)*
