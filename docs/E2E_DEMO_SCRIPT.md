# Nexus Sandbox E2E Demo Script

This document provides step-by-step instructions for demonstrating the complete payment lifecycle in the Nexus Sandbox.

---

## Prerequisites

1. **Start the services**:
   ```bash
   cd /home/siva/Projects/Nexus\ Global\ Payments\ Sandbox
   docker-compose up -d
   ```

2. **Access the dashboard**: Open `http://localhost:8080`

3. **Verify API status**: Green "API: connected" badge in header

---

## Happy Flow Demo

### Step 1: View Registered Actors

1. Navigate to **Actors** page from sidebar
2. Observe 6 pre-seeded actors:
   - `DBSGSGSG` (PSP - DBS Singapore)
   - `BKKBTHBK` (PSP - Bangkok Bank)
   - `MAYBMYKL` (PSP - Maybank Malaysia)
   - `NEXUSFXP1` (FXP - Nexus FXP Alpha)
   - `SGIPSOPS` (IPS - Singapore FAST)
   - `THIPSOPS` (IPS - Thailand PromptPay)

**Expected**: All actors show status `ACTIVE`

---

### Step 2: Proxy Resolution (acmt.023 → acmt.024)

1. Navigate to **Send Payment** page
2. Fill in:
   - Source Country: **Singapore**
   - Destination Country: **Thailand**
   - Proxy Type: **Mobile Number**
   - Proxy Value: `+66812345678`
3. Click **Resolve Proxy**

**API Call**:
```bash
POST /v1/addressing/resolve
{
  "proxyType": "MBNO",
  "proxyValue": "+66812345678",
  "destinationCountry": "TH"
}
```

**Expected Response**:
```json
{
  "resolutionId": "...",
  "accountNumber": "0123456789",
  "agentBic": "BKKBTHBK",
  "beneficiaryName": "Somchai Thai",
  "status": "VALIDATED"
}
```

---

### Step 3: FX Quote (camt.030 equivalent)

1. Enter Amount: **1000 SGD**
2. Click **Get Quote**

**API Call**:
```bash
GET /v1/quotes?sourceCountry=SG&destCountry=TH&sourceCurrency=SGD&destCurrency=THB&amount=1000&amountType=SOURCE
```

**Expected Response**:
```json
{
  "quoteId": "quote-uuid",
  "rate": 25.50,
  "sourceAmount": 1000.00,
  "destAmount": 25500.00,
  "fxpName": "Nexus FXP Alpha",
  "validUntil": "2026-02-03T15:10:00.000Z",
  "fees": { "nexusFee": 0.50, "sourcePspFee": 1.00 }
}
```

---

### Step 4: Pre-Transaction Disclosure

1. Review the disclosure breakdown:
   - Exchange Rate
   - Fees (Nexus, PSP, FXP)
   - Total amount receiver gets
   - Estimated completion time
2. Click **Accept Quote**

---

### Step 5: Payment Execution (pacs.008)

1. Enter Sender details
2. Click **Confirm & Send**

**ISO Message Lifecycle**:
```
┌─────────────────────────────────────────────────────────────┐
│ 1. PSP (DBSGSGSG) → IPS-SG → NEXUS GATEWAY                 │
│    pacs.008 with InstgAgt=DBSGSGSG, InstdAgt=SGIPSOPS      │
├─────────────────────────────────────────────────────────────┤
│ 2. NEXUS GATEWAY transform_pacs008():                       │
│    - InstgAgt: DBSGSGSG → THIPSOPS (Dest IPS)              │
│    - InstdAgt: SGIPSOPS → BKKBTHBK (Dest PSP)              │
│    - PrvsInstgAgt1: SGIPSOPS (audit trail)                 │
│    - IntrBkSttlmAmt: 1000 SGD → 25500 THB                  │
├─────────────────────────────────────────────────────────────┤
│ 3. NEXUS GATEWAY → IPS-TH → PSP (BKKBTHBK)                 │
│    Transformed pacs.008 with Thai currency/agents           │
├─────────────────────────────────────────────────────────────┤
│ 4. IPS-TH → NEXUS → IPS-SG → PSP                           │
│    pacs.002 with Status=ACCC (Accepted Settlement Completed)│
└─────────────────────────────────────────────────────────────┘
```

---

### Step 6: Verify in ISO Explorer

1. Navigate to **Messages** page
2. Search by UETR
3. View the message sequence:
   - `acmt.023` → `acmt.024`
   - `pacs.008` (outbound)
   - `pacs.008` (transformed)
   - `pacs.002` (status)

---

## Unhappy Flow Demos

### Error 1: Invalid Proxy (BE23)

**Input**: Proxy value `+66999999999` (not in directory)

**Expected**:
```json
{
  "status": "INVALID",
  "reasonCode": "BE23",
  "reasonText": "Account/Proxy Invalid"
}
```

**UI**: Red error alert "Beneficiary not found"

---

### Error 2: Expired Quote (AB04)

**Scenario**: Wait 10+ minutes after quote, then try to submit

**Expected**:
```json
{
  "status": "REJECTED",
  "statusReasonCode": "AB04",
  "message": "Quote expired"
}
```

**UI**: Modal "Quote has expired. Request a new quote."

---

### Error 3: Rate Mismatch (AB04)

**Scenario**: Quote rate changed between request and execution

**Expected**:
```json
{
  "status": "REJECTED",
  "statusReasonCode": "AB04",
  "message": "Agreed rate does not match"
}
```

---

### Error 4: Invalid SAP (RC11)

**Scenario**: SAP BIC not found in registry

**Expected**:
```json
{
  "status": "REJECTED",
  "statusReasonCode": "RC11",
  "message": "Invalid Intermediary Agent"
}
```

---

## API Quick Reference

| Step | Endpoint | Method | ISO Message |
|------|----------|--------|-------------|
| Register Actor | `/v1/actors/register` | POST | - |
| Resolve Proxy | `/v1/addressing/resolve` | POST | acmt.023 |
| Get Quote | `/v1/quotes` | GET | camt.030 |
| Submit Payment | `/v1/iso20022/pacs008` | POST | pacs.008 |
| Get Status | `/v1/payments/{uetr}/events` | GET | pacs.002 |

---

## ISO 20022 Status Codes

| Code | Meaning | When |
|------|---------|------|
| `ACCC` | Accepted Settlement Completed | Payment successful |
| `AB04` | Aborted - Settlement Fatal Error | Quote expired / rate mismatch |
| `BE23` | Account/Proxy Invalid | Proxy not found |
| `RC11` | Invalid Intermediary Agent | Bad SAP BIC |
| `AM04` | Insufficient Funds | Settlement failure |

---

## Network Mesh View

Navigate to **Network Mesh** to see the real-time topology:

- **Green nodes**: Active actors
- **Blue edges**: Payment flows
- **Animated particles**: Messages in transit

---

**Questions?** Check the [Integration Guide](./INTEGRATION_GUIDE.md) or API docs at `/docs`.
