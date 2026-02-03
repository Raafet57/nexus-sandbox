# Demo Dashboard User Guide

This guide explains each section of the Nexus Sandbox demo dashboard and how they relate to the [17-step payment lifecycle](https://docs.nexusglobalpayments.org/).

---

## Navigation Overview

The dashboard simulates all five actor types in the Nexus ecosystem:

| Actor | Role | Dashboard |
|-------|------|-----------|
| **PSP** | Payment Service Provider | Send Payment, PSP Dashboard |
| **FXP** | FX Provider | FX Rates |
| **SAP** | Settlement Access Provider | Liquidity |
| **IPS** | Instant Payment System | IPS Dashboard |
| **PDO** | Proxy Directory Operator | PDO Dashboard |

---

## 📤 Send Payment (`/payment`)

**Purpose**: Simulate the sender's PSP initiating a cross-border payment.

**Lifecycle Steps Covered**: 1–17 (complete flow)

**Features**:
- Select destination country and IPS
- Enter amount and see real-time FX quotes
- Choose best quote from multiple FXPs
- Enter recipient's proxy (mobile, email)
- Trigger proxy resolution via PDO
- Confirm and submit payment
- View pacs.002 confirmation

**Reference**: [Payment Setup](https://docs.nexusglobalpayments.org/payment-setup/)

---

## 🏦 PSP Dashboard (`/psp`)

**Purpose**: View operations from either Source or Destination PSP perspective.

**Actor Role**:
- **Source PSP**: Initiates payments, requests quotes, submits pacs.008
- **Destination PSP**: Receives payments, credits recipient, sends pacs.002

**Features**:
- View pending and completed transactions
- See callback delivery status
- Monitor pacs.002 responses
- Track payment timelines

**Reference**: [PSP Implementation](https://docs.nexusglobalpayments.org/participating-entities/psps/)

---

## 💱 FX Rates (FXP) (`/fxp`)

**Purpose**: Manage FX Provider rate configuration and quote responses.

**Lifecycle Steps**: 3–6 (Quoting Phase)

**Features**:
- Configure base rates for currency pairs
- Set spread in basis points (bps)
- View quote request history
- Monitor accepted vs. rejected quotes
- Simulate rate volatility

**Key Concept**: Tier-based improvements—rates get better with volume.

**Reference**: [FX Provision](https://docs.nexusglobalpayments.org/fx-provision/)

---

## 💰 Liquidity (SAP) (`/sap`)

**Purpose**: Settlement Access Provider liquidity monitoring.

**Actor Role**: SAPs provide prefunded accounts for cross-border settlement.

**Features**:
- View prefunded balances by currency
- Monitor settlement queue
- Track daily settlement volumes
- View position limits

**Key Fields**:
- `InstrAgnt` (Instructing Agent)
- `InstdAgnt` (Instructed Agent)
- `SttlmAcct` (Settlement Account)

**Reference**: [Settlement Mechanism](https://docs.nexusglobalpayments.org/settlement/)

---

## 🌐 IPS Dashboard (`/ips`)

**Purpose**: Instant Payment System operator view (FAST, PromptPay, DuitNow).

**Lifecycle Steps**: 15–17 (Execution & Confirmation)

**Features**:
- View incoming/outgoing messages
- Monitor message routing
- Track settlement confirmations
- View IPS-specific configurations

**Supported IPS**:
- 🇸🇬 FAST (Singapore)
- 🇹🇭 PromptPay (Thailand)
- 🇲🇾 DuitNow (Malaysia)
- 🇮🇳 UPI (India)
- 🇵🇭 InstaPay (Philippines)

**Reference**: [Participating IPS](https://docs.nexusglobalpayments.org/participating-entities/ips/)

---

## 📇 PDO Dashboard (`/pdo`)

**Purpose**: Proxy Directory Operator—resolve aliases to account details.

**Lifecycle Steps**: 7–9 (Addressing Phase)

**Features**:
- View proxy registrations
- Monitor resolution requests (acmt.023)
- See resolution responses (acmt.024)
- Manage proxy types

**Proxy Types**:
- 📱 Mobile number
- 📧 Email address
- 🆔 National ID
- 📲 QR code

**Reference**: [Proxy Resolution](https://docs.nexusglobalpayments.org/addressing/)

---

## 🔍 Payments Explorer (`/explorer`)

**Purpose**: Developer tool for transaction debugging and lifecycle visualization.

**Features**:
- Search by UETR (Unique End-to-End Transaction Reference)
- View 17-step lifecycle timeline
- Inspect raw ISO 20022 XML (pacs.008, pacs.002)
- See status codes with descriptions
- Access DevDebugPanel for API commands

**Tabs**:
1. **Overview**: Transaction summary, status, participants
2. **Lifecycle**: Visual timeline of 17 steps
3. **Messages**: Raw XML with syntax highlighting
4. **Debug**: Developer commands and gateway context

**Reference**: [ADR-011 Developer Observability](./adr/ADR-011-developer-observability.md)

---

## 📨 Messages (`/messages`)

**Purpose**: Browse and filter ISO 20022 messages across all transactions.

**Message Types**:
| Code | Name | Direction |
|------|------|-----------|
| `pacs.008` | FI to FI Customer Credit Transfer | Outbound |
| `pacs.002` | Payment Status Report | Inbound |
| `acmt.023` | Identification Verification Request | Outbound |
| `acmt.024` | Identification Verification Response | Inbound |
| `camt.054` | Bank to Customer Debit/Credit Notification | Inbound |
| `camt.056` | FI to FI Payment Cancellation Request | Outbound |
| `pacs.004` | Payment Return | Inbound |

**Reference**: [ISO 20022 Catalogue](https://www.iso20022.org/), [ADR-003](./adr/ADR-003-iso20022-message-handling.md)

---

## 🕸️ Network Mesh (`/mesh`)

**Purpose**: Visualize the interconnection between all actors in the Nexus network.

**Features**:
- Interactive network diagram
- See message flow between actors
- Visualize settlement paths
- Monitor connection health

---

## 👥 Actors (`/actors`)

**Purpose**: Registry of all participants in the sandbox.

**Actor Categories**:
- **PSPs**: Banks and payment providers
- **FXPs**: FX rate providers
- **SAPs**: Settlement providers
- **IPS**: National payment systems
- **PDOs**: Proxy directories

**Fields**:
- BIC (Bank Identifier Code)
- LEI (Legal Entity Identifier)
- Country
- Supported currencies

---

## ⚙️ Settings (`/settings`)

**Purpose**: Configure sandbox behavior and preferences.

**Options**:
- Quote validity timeout
- Payment SLA settings
- Mock data configuration
- Logging verbosity
- Theme (light/dark)

---

## 📚 API Docs (`/api/docs`)

**Purpose**: Interactive Swagger UI for the Nexus Gateway API.

**Opens in new tab** with full OpenAPI documentation including:
- All 18 endpoint groups
- Request/response schemas
- Try-it-out functionality
- Authentication headers

**Alternative**: ReDoc at `/api/redoc`

---

## System Status Indicator

The bottom of the navigation shows real-time API connectivity:

| Status | Meaning |
|--------|---------|
| 🟢 `connected` | Gateway API is healthy |
| 🔴 `disconnected` | Cannot reach `/health` endpoint |
| ⚪ `checking` | Testing connection |

---

## Quick Reference: 17-Step Lifecycle

| Phase | Steps | Dashboard |
|-------|-------|-----------|
| **Setup** | 1–2 | Send Payment |
| **Quotes** | 3–6 | Send Payment, FXP |
| **Addressing** | 7–9 | Send Payment, PDO |
| **Compliance** | 10–11 | (Background) |
| **Approval** | 12 | Send Payment |
| **Execution** | 13–16 | IPS, Messages |
| **Confirmation** | 17 | PSP, Explorer |

---

Created by [Siva Subramanian](https://linkedin.com/in/sivasub987)
