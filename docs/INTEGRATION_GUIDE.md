# Nexus Sandbox Integration Guide

This guide explains how external developers can plug their own components (FXP, IPS, PSP) into the Nexus Sandbox for testing and validation.

## 1. Sandbox Overview

The Nexus Sandbox provides a simulated multi-country payment environment with the following pre-configured corridors:

| Source Country | Destination Country | Currency Pair |
|----------------|---------------------|---------------|
| Singapore (SG) | Thailand (TH)       | SGD → THB     |
| Singapore (SG) | Malaysia (MY)       | SGD → MYR     |
| Thailand (TH)  | Singapore (SG)      | THB → SGD     |

### Pre-Seeded Actors

The sandbox includes 6 pre-registered actors for immediate testing:

| BIC          | Actor Type | Name                     | Country |
|--------------|------------|--------------------------|---------|
| `DBSGSGSG`   | PSP        | DBS Bank Singapore       | SG      |
| `BKKBTHBK`   | PSP        | Bangkok Bank             | TH      |
| `MAYBMYKL`   | PSP        | Maybank Malaysia         | MY      |
| `NEXUSFXP1`  | FXP        | Nexus FXP Alpha          | SG      |
| `SGIPSOPS`   | IPS        | Singapore FAST IPS       | SG      |
| `THIPSOPS`   | IPS        | Thailand PromptPay IPS   | TH      |

---

## 2. Registering Your Actor

### 2.1. Self-Service Registration API

Register your component using the following endpoint:

```bash
POST /v1/actors/register
Content-Type: application/json

{
  "bic": "YOURPSPXXX",
  "actorType": "PSP",  // FXP | IPS | PSP | SAP | PDO
  "name": "Your Organization Name",
  "countryCode": "SG",
  "callbackUrl": "https://your-server.com/nexus/callback"  // Optional
}
```

**Response:**
```json
{
  "actorId": "actor-a1b2c3d4",
  "bic": "YOURPSPXXX",
  "actorType": "PSP",
  "name": "Your Organization Name",
  "countryCode": "SG",
  "callbackUrl": "https://your-server.com/nexus/callback",
  "registeredAt": "2026-02-03T14:30:00.000Z",
  "status": "ACTIVE"
}
```

### 2.2. Viewing Registered Actors

```bash
GET /v1/actors
GET /v1/actors?actorType=FXP
GET /v1/actors?countryCode=SG
GET /v1/actors/YOURPSPXXX
```

### 2.3. Updating Callback URL

```bash
PATCH /v1/actors/YOURPSPXXX/callback
Content-Type: application/json

{
  "callbackUrl": "https://new-server.com/nexus/callback"
}
```

---

## 3. Connectivity Models

### Direct Participants (FXP, IPS)

| Actor Type | Connection | Protocol | Callback Support |
|------------|------------|----------|------------------|
| **FXP**    | Direct to Nexus Gateway | HTTPS REST API | ✅ Supported |
| **IPS**    | Direct to Nexus Gateway | ISO 20022 / VPN | ✅ Supported |

**FXP Integration Flow:**
1. Register your FXP via `/v1/actors/register`.
2. Submit rates via `POST /v1/rates`.
3. Receive "Trade Notification" webhooks when your rate is selected.

### Indirect Participants (PSP, SAP, PDO)

| Actor Type | Connection | Protocol | Callback Support |
|------------|------------|----------|------------------|
| **PSP**    | Via Domestic IPS | Domestic Standard | ❌ Via IPS |
| **SAP**    | Via Domestic IPS | Domestic Standard | ❌ Via IPS |
| **PDO**    | Via Domestic IPS | ISO 20022 API | ❌ Via IPS |

**PSP Integration Flow:**
1. Connect to your simulated domestic IPS endpoint (e.g., `ips-sg`).
2. Send `pacs.008` messages for payment initiation.
3. Receive `pacs.002` status responses from IPS.

---

## 4. ISO 20022 Message Examples

### 4.1. Proxy Resolution (`acmt.023` / `acmt.024`)

**Request (acmt.023):**
```bash
POST /v1/addressing/resolve
Content-Type: application/json

{
  "proxyType": "MBNO",
  "proxyValue": "+66812345678",
  "destinationCountry": "TH"
}
```

**Response (acmt.024 equivalent):**
```json
{
  "resolutionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "accountNumber": "0123456789",
  "accountType": "BBAN",
  "agentBic": "BKKBTHBK",
  "beneficiaryName": "Somchai Thai",
  "displayName": "Somchai T.",
  "status": "VALIDATED",
  "timestamp": "2026-02-03T14:45:00.000Z"
}
```

### 4.2. Payment Instruction (`pacs.008`)

Refer to `/v1/iso20022/pacs008` for submitting payment instructions. The gateway performs:

1. **Quote Validation**: Checks `AgreedRate` UUID against stored quotes.
2. **Agent Swapping**:
   - `InstgAgt`: Source PSP → Destination SAP
   - `InstdAgt`: Source SAP → Destination PSP
3. **Amount Conversion**: `IntrBkSttlmAmt` converted using agreed FX rate.

---

## 5. Testing Your Integration

### 5.1. End-to-End Flow

1. **Register Actor** → `POST /v1/actors/register`
2. **Request Quote** → `GET /v1/quotes?sourceCountry=SG&destCountry=TH&amount=1000&amountType=SOURCE`
3. **Resolve Proxy** → `POST /v1/addressing/resolve`
4. **Submit Payment** → `POST /v1/iso20022/pacs008`
5. **Check Status** → `GET /v1/payments/{uetr}/events`

### 5.2. Dashboard Verification

View your transaction lifecycle at:
- **Payment Dashboard**: `http://localhost:8080`
- **ISO Explorer**: `http://localhost:8080/messages`
- **Mesh Visualizer**: `http://localhost:8080/mesh`

---

## 6. Assumptions & Limitations

| Assumption | Description |
|------------|-------------|
| A25 | Self-service registration via `callbackUrl` |
| A26 | Direct connectivity for FXP/IPS only |
| A27 | In-memory registry for sandbox simplicity |

For the complete list, see `docs/assumptions/09_actor_integration.md`.

---

**Questions?** Check the API docs at `http://localhost:8080/api/docs` (Swagger UI) or `/api/redoc`.
