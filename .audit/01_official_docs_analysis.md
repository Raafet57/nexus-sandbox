# Nexus Global Payments Sandbox - Official Documentation Analysis

## Executive Summary

This report provides a comprehensive analysis of the Nexus Global Payments Sandbox documentation, extracted from the official documentation file. The Nexus system is a cross-border payment network that enables real-time international payments through a standardized API and ISO 20022 message format.

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Data Models and Schemas](#data-models-and-schemas)
3. [ISO 20022 Message Formats](#iso-20022-message-formats)
4. [Payment Flow Specifications](#payment-flow-specifications)
5. [Fee Calculation Rules](#fee-calculation-rules)
6. [Actor Registration Requirements](#actor-registration-requirements)
7. [Callback URL Specifications](#callback-url-specifications)
8. [Error Handling Specifications](#error-handling-specifications)
9. [Quote Request/Response Formats](#quote-requestresponse-formats)
10. [Address Validation Requirements](#address-validation-requirements)
11. [Currency, Country, and Financial Institution Constraints](#currency-country-and-financial-institution-constraints)
12. [UI/UX Requirements](#uiux-requirements)

---

## 1. API Endpoints

### Core API Endpoints

#### Countries API
```
GET /countries
Returns all countries available on the Nexus network, along with key reference data for sending payments to those countries, such as maximum transaction amounts and requirements for category purpose codes.

Response:
{
  "countries": [
    {
      "countryId": 344,
      "countryCode": "HK",
      "name": "Hong Kong",
      "currencies": [
        {
          "currencyCode": "HKD",
          "maxAmount": "10000"
        },
        {
          "currencyCode": "CNY",
          "maxAmount": "20000"
        }
      ],
      "requiredMessageElements": {
        "pacs008": [
          "purposeCode"
        ]
      }
    }
  ]
}
```

```
GET /countries/{countryCode}
Returns a specified country based on the 2-letter countryCode provided.

Path Parameters:
- countryCode: The ISO 3166 alpha-2 country code (e.g., "ID")
```

#### Quotes API
```
GET /quotes/{sourceCountry}/{sourceCurrency}/{destinationCountry}/{destinationCurrency}/{amountCurrency}/{amount}
Retrieves a list of quotes for currency exchange based on the specified country/currency pair and the amount.

Path Parameters:
- sourceCountry: 2-letter country code for the Source Country (e.g., "SG")
- sourceCurrency: 3-letter currency code for the Source Currency (e.g., "SGD")
- destinationCountry: 2-letter country code for the Destination Country (e.g., "TH")
- destinationCurrency: 3-letter currency code for the Destination Currency (e.g., "THB")
- amountCurrency: Source Currency if Sender defined amount to send, Destination Currency if defined amount to receive
- amount: The amount to be exchanged (adjusted for any Source PSP Deducted Fee)

Query Parameters:
- finInstTypeId: Type ID of the financial institution
- finInstId: ID of the financial institution
```

```
GET /quotes/{quoteId}/intermediary-agents
Retrieve intermediary agents (Settlement Access Providers) associated with a specified quote.

Path Parameters:
- quoteId: ID of the quote (UUID format, e.g., "9fa1e78d-b3d0-4d68-8032-d39d414a7366")
```

#### Address Types API
```
GET /countries/{countryCode}/address-types-and-inputs
Returns all address types AND their associated inputs for a specified country.

GET /countries/{countryCode}/address-types
Returns high-level address types (only) for a specified country.

GET /address-types/{addressTypeId}/inputs
Returns the detailed input fields for a specified Address Type.

Path Parameters:
- countryCode: The ISO 3166 alpha-2 country code
- addressTypeId: The ID of the address type (e.g., "IDACCT")
```

#### Maximum Amounts API
```
GET /countries/{countryCode}/currencies/{currencyCode}/max-amounts
Returns maximum payment amount for a specified country and currency combination.

Response:
[
  {
    "clearingSystemId": "SGDFAST",
    "maxAmount": "200000"
  }
]
```

#### Fees and Amounts API
```
GET /fees-and-amounts/{sourceCountry}/{sourceCurrency}/{destinationCountry}/{destinationCurrency}/{amountCurrency}/{amount}/{exchangeRate}
Get Fees and Interbank Settlement Amounts

Response:
{
  "debtorAgent": {
    "interbankSettlementAmount": {
      "amount": 100,
      "currency": "SGD"
    },
    "nexusSchemeFee": {
      "amount": 0.5,
      "currency": "SGD"
    }
  },
  "creditorAgent": {
    "interbankSettlementAmount": {
      "amount": 350,
      "currency": "MYR"
    },
    "chargesAmount": {
      "amount": 2.24,
      "currency": "MYR"
    },
    "creditorAccountAmount": 347.76
  }
}
```

#### Fee Formulas API
```
GET /fee-formulas/nexus-scheme-fee/{countryCode}/{currencyCode}
Returns the Nexus Scheme Fee Formula for a specified Source Country, denominated in the Source Currency.

Response:
{
  "countryCode": "SG",
  "currency": "SGD",
  "nominalFeeAmount": "0.50",
  "percentageFeeAsRatio": 0.001
}
```

```
GET /fee-formulas/creditor-agent-fee/{countryCode}/{currencyCode}
Returns the Creditor Agent (Destination PSP) Fee Formula for a specified Destination Country, denominated in the Destination Currency.

Response:
{
  "countryCode": "MY",
  "nominalFee": {
    "amount": "2.22",
    "currency": "MYR"
  },
  "percentageFee": 0.1
}
```

---

## 2. Data Models and Schemas

### Quote Request Model
```json
{
  "quoteRequestId": "d302cc08-323b-4ac6-897e-579a9abe0c88",
  "sourceCountry": "SG",
  "sourceCurrency": "SGD",
  "destinationCountry": "TH",
  "destinationCurrency": "THB",
  "amountCurrency": "SGD",
  "amount": 1000,
  "quotes": [
    {
      "quoteId": "855cd802-8c7b-4fd2-8ce7-a456c1e12509",
      "issuedDateTime": "2024-10-22T12:00:00Z",
      "fxpfinInstIdType": "BICFI",
      "fxpfinInstId": "FXSGAAAA",
      "exchangeRate": 25,
      "debtorAgent": {
        "interbankSettlementAmount": {
          "currency": "SGD",
          "amount": 1000,
          "cappedToMaxAmount": false
        },
        "nexusSchemeFee": {
          "amount": 1.5,
          "currency": "SGD"
        }
      },
      "intermediaryAgent1": {
        "finInstId": {
          "name": "DBS Bank Ltd",
          "BICFI": "DBSSSGSG",
          "LEI": "ATUEL7OJR5057F2PV266",
          "clearingSystemMemberId": {
            "clearingSystemId": null,
            "memberId": null
          },
          "other": {
            "id": null
          }
        }
      },
      "intermediaryAgent1Account": {
        "id": "2345678901"
      },
      "creditorAgent": {
        "interbankSettlementAmount": {
          "amount": 25000,
          "currency": "THB",
          "cappedToMaxAmount": false
        },
        "chargesInformation": {
          "amount": {
            "amount": 100,
            "currency": "THB"
          }
        },
        "creditorAccountAmount": 24900
      }
    }
  ]
}
```

### Intermediary Agents Model
```json
{
  "intermediaryAgent1": {
    "name": "DBS Bank Ltd",
    "countryCode": "SG",
    "currencyCode": "SGD",
    "finInstId": {
      "BICFI": [
        "DBSSSGSG"
      ],
      "LEI": "ATUEL7OJR5057F2PV266",
      "otherId": null
    },
    "account": {
      "otherId": "2345678901"
    }
  },
  "intermediaryAgent2": {
    "name": "Kasikornbank Public Company Limited",
    "countryCode": "TH",
    "currencyCode": "THB",
    "finInstId": {
      "BICFI": [
        "KASITHBK"
      ],
      "LEI": null,
      "otherId": null
    },
    "account": {
      "otherId": "8881234569"
    }
  }
}
```

### Country Model
```json
{
  "id": 360,
  "countryCode": "ID",
  "name": "Indonesia",
  "currencies": [
    {
      "currencyCode": "IDR",
      "maxAmount": "15000000"
    }
  ],
  "requiredMessageElements": {
    "pacs008": [
      "categoryPurposeCode"
    ]
  }
}
```

### Address Type Model
```json
{
  "addressTypeId": "PHACCT",
  "countries": [
    "PH"
  ],
  "addressTypeCode": "ACCT",
  "clearingSystemId": "PHPINST",
  "displayOrder": 3,
  "inputs": [
    {
      "addressInputId": "PHINPT1",
      "label": {
        "addressTypeCode": "ACCT",
        "title": {
          "en": "Account number, 10-18 digits",
          "de": "Kontonummer, 10-18 Ziffern"
        }
      },
      "attributes": {
        "name": "accountOrProxyId",
        "type": "number",
        "pattern": "^\\d{10,18}$",
        "placeholder": "1234567890",
        "required": true
      },
      "iso20022XPath": {
        "acmt023": "/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Id/Othr/Id",
        "pacs008": "/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/CrtrAcct/Id/Othr/Id"
      }
    }
  ]
}
```

---

## 3. ISO 20022 Message Formats

### Supported Message Types
- **pacs.008** - FI to FI Customer Credit Transfer (payment instruction)
- **pacs.002** - Financial Institution Credit Transfer Status Report
- **acmt.023** - Identification Verification Request (proxy/account resolution)
- **acmt.024** - Identification Verification Response (proxy/account resolution)
- **camt.054** - Report of Intra-position Financial Transfer Messages (reconciliation)

### pacs.008 Payment Instruction Requirements

**Mandatory Elements:**
- Single transaction only (Nexus supports single payments only)
- Unique End-to-End Reference (UETR)
- Intermediary Agents (Source and Destination SAP accounts)
- FX Quote ID (when using third-party FX Provider)
- Instruction Priority (NORM for P2P, HIGH for P2M)

**XPath Structure:**
- Debtor Agent: `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/DbtrAgt/FinInstnId/BICFI`
- Creditor Agent: `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/CdtrAgt/FinInstnId/BICFI`
- Debtor Account: `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/DbtrAcct/Id/IBAN` or `/Othr/Id`
- Creditor Account: `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/CrtrAcct/Id/IBAN` or `/Othr/Id`
- Intermediary Agent 1: Source SAP account
- Intermediary Agent 2: Destination SAP account
- Amount: `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/InstdAmt`
- Exchange Rate: In `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/RmtInf/Strd/CdtrRefInf/Ref`
- Quote ID: In Agreed Rate section
- Instruction Priority: `/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/PmtTpInf/InstrPrty/`
- Purpose Code: Required for some countries (e.g., HK, SG, MY)
- Category Purpose Code: Required for others (e.g., ID, PH, TH)

### acmt.023 Identification Verification Request

**Purpose:** Proxy and account resolution to obtain recipient account details

**Key Elements:**
- Party and Account Identification
- Financial Institution Identification
- Address Information
- Proxy/Account Type Codes

**Supported Proxy Types:**
- Email (EMAL)
- Mobile Number (MBNO)
- National ID Number (NID)
- Other proxy types as defined by each IPS

**XPath References:**
- Account/Proxy ID: `/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Prxy/Id`
- Account/Proxy Type: `/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Prxy/Tp/Cd`
- Account ID (other): `/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Id/Othr/Id`
- BIC: `/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Agt/FinInstnId/BICFI`
- IBAN: `/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Id/IBAN`

---

## 4. Payment Flow Specifications

### High-Level Process Flow

#### Source Country (Sending) Flow - 23 Steps
1. **Sender** initiates and authorizes Nexus cross-border payment with full transparency
2. **Source PSP** debits Sender's account or reserves funds
3. **Source PSP** sends payment instruction to Source IPS
4. **Source IPS** ensures settlement (reserves pre-funded balance or settles)
5. **Source IPS** sends payment instruction to Source SAP for validation
6. **Source SAP** reviews payment instruction, applies sanctions screening if required
7. **Source SAP** accepts payment or rejects with status message
8. **Source IPS** sends Nexus `pacs.008` to Nexus
9. **Nexus** validates and transforms payment instruction:
   - Changes instructing/instructed agents to Destination SAP/Destination PSP
   - Validates quote, updates currency, applies conversion
10. **Nexus** forwards payment instruction to Destination IPS
11. **Destination Nexus Gateway** sends processing result via `pacs.002` to Source Nexus Gateway
12. **Source Nexus Gateway** forwards `pacs.002` to Source IPS
13. **Source Gateway** informs FXP that payment has been processed using their quote
14. **Source IPS** finalizes payment between Source PSP and Source SAP
15. **Source IPS** sends confirmation to Source PSP
16. **Source PSP** finalizes debit on Sender's account
17. **Source PSP** informs Sender that payment is complete

#### Destination Country (Receiving) Flow - Multiple Scenarios

**Normal Priority (NORM) - 20 Steps:**
1. **Destination Nexus Gateway** sends `pacs.008` to Destination IPS
2. **Destination IPS** sends payment instruction to Destination SAP
3. **Destination SAP** verifies FXP has sufficient funds, applies compliance checks
4. **Destination SAP** reserves amount on FXP's account or rejects
5. **Destination SAP** submits payment instruction to Destination IPS
6. **Destination IPS** ensures settlement (reserves pre-funded balance)
7. **Destination IPS** forwards payment message to Destination PSP
8. **Destination PSP** applies sanctions screening, validates Recipient's account
9. **Destination PSP** sends `pacs.002` confirmation to Destination IPS
10. **Destination IPS** sends `pacs.002` to Nexus Gateway
11. **Nexus Gateway** confirms receipt with `pacs.002`
12. **Destination IPS** finalizes settlement
13. **Destination IPS** confirms settlement to Destination SAP and Destination PSP
14. **Destination SAP** finalizes debit on FXP account
15. **Destination PSP** credits Recipient's account

**High Priority (HIGH) - 25 Steps:**
- Includes timeout mechanism by Nexus Gateway
- Settlement is subject to confirmation of Nexus `pacs.002`
- More detailed reconciliation and error handling

---

## 5. Fee Calculation Rules

### Fee Components
1. **Nexus Scheme Fee** - Paid by Source IPS to Nexus Scheme
2. **Source PSP Fee** - Optional fee charged by Source PSP
3. **Destination PSP Fee** - Charged by Destination PSP (recorded in ChargesInformation/Amount)

### Fee Calculation Process
1. **Source PSP Deducted Fee:**
   - If Sender defined amount to send: Subtract fee before submitting quote request
   - Final amount debited from Sender = Interbank Settlement Amount + Source PSP Fee
   - Formula: `DebtorAccountAmount = InterbankSettlementAmount + SourcePSPFee`

2. **Destination PSP Fee:**
   - Calculated by Nexus and provided in quote response
   - Amount credited to Recipient = Interbank Settlement Amount - Destination PSP Fee
   - Formula: `CreditorAccountAmount = InterbankSettlementAmount - DestinationPSPFee`

3. **Fee Tiers:**
   - FXPs define tier-based improvements in basis points
   - Base rate applies for transactions below lowest tier
   - Tier amounts configurable per FXP

4. **Maximum Amount Constraints:**
   - Nexus applies caps from Source and Destination IPSs
   - Response includes `cappedToMaxAmount` flag if exceeded
   - Interbank Settlement Amount shows maximum that can be sent

### Fee Formulas API
- **Nexus Scheme Fee:** Formula denominated in Source Currency
- **Creditor Agent Fee:** Formula denominated in Destination Currency
- Both include nominal amount + percentage fee components

---

## 6. Actor Registration Requirements

### Financial Institutions (PSPs)
- Must be licensed payment service providers
- API credentials separate for payments vs FX/Treasury departments
- Support ISO 20022 messages for Nexus communications
- Maximum transaction limits configurable per country/currency

### Settlement Access Providers (SAPs)
- Must be registered as SAPs with Nexus
- Provide settlement services to FXPs
- Must support multiple currencies and corridors
- Cannot be limited to specific currency pairs or corridors
- Must comply with Nexus message format requirements

### Foreign Exchange Providers (FXPs)
- Willing to quote FX rates for specific currency pairs
- Rates shown to Source PSPs with business relationship
- Upload rates via POST /rates/ API
- Can withdraw rates using DELETE /rates/ API
- Define tier-based rate improvements

### IPSs (Instant Payment Systems)
- Must ensure settlement certainty
- Support real-time payment processing
- Must not introduce delays
- Support message translation between Nexus and domestic formats
- Monitor response times for SLA compliance

### Requirements per Actor Type
1. **Technical Requirements:**
   - ISO 20022 message support
   - API integration capabilities
   - Real-time processing
   - Compliance screening

2. **Operational Requirements:**
   - SLA adherence
   - Liquidity management
   - Dispute resolution processes
   - Regulatory compliance

3. **Security Requirements:**
   - Sanctions screening
   - AML/CFT compliance
   - Data protection
   - Secure message transmission

---

## 7. Callback URL Specifications

### Callback Flow
1. **Nexus Gateway** sends HTTP callbacks for status updates
2. **Destination PSP** must implement callback endpoints
3. **Status codes** communicated via callback:
   - ACCC (Accepted)
   - RJCT (Rejected)
   - BLCK (Blocked)
   - PEND (Pending)

### Callback Requirements
- Must support HTTP/HTTPS
- Must respond within SLA timeframes
- Must acknowledge receipt of callbacks
- Must handle retry mechanisms for failed callbacks
- Must provide transaction correlation information

---

## 8. Error Handling Specifications

### ISO 20022 Status Codes
Common status codes in `pacs.002` messages:
- **ACCC**: Accepted
- **RJCT**: Rejected
- **BLCK**: Blocked
- **PEND**: Pending

### Error Conditions
1. **Exchange Rate Validation Error**
   - Code: AB04 (Aborted Settlement Fatal Error)
   - Triggered when rate in pacs.008 differs from quote

2. **Maximum Amount Exceeded**
   - Flag: `cappedToMaxAmount: true`
   - Nexus applies smaller cap of Source/Destination IPS limits

3. **Sanctions Screening**
   - Triggers reject with appropriate reason code
   - Must be applied by both Source and Destination PSPs

4. **Account Validation Failure**
   - acmt.023 rejection with specific reason codes
   - Validates recipient account details before payment

5. **Timeout Errors**
   - High priority payments rejected after timeout
   - Applies to Destination side processing

### Error Recovery
- Investigations and disputes via Nexus Service Desk
- Manual intervention for complex cases
- Automated message resend capabilities
- Transaction rollback mechanisms

---

## 9. Quote Request/Response Formats

### Quote Request Process
1. **Source PSP** calls `GET /quotes` API with:
   - Source/destination country and currency
   - Amount (adjusted for Source PSP fee if applicable)
   - Optional financial institution filters

2. **Nexus** generates quotes based on:
   - Available FXPs with approved PSP relationships
   - Base rates from POST /rates/ API
   - Tier-based improvements
   - PSP-specific preferential rates

3. **Quote Response** includes:
   - Quote ID (UUID)
   - Exchange rate
   - Interbank Settlement Amounts
   - Fees breakdown
   - Intermediary Agent details
   - Currency amounts
   - Cap flags (if applicable)

### Quote Validation Rules
1. **Quote Expiry:** Quotes expire after 10 minutes (600 seconds)
2. **Rate Matching:** Exchange rate in pacs.008 must match quote exactly
3. **Amount Validation:** Amounts cannot exceed maximum transaction limits
4. **FSP Relationship:** Quotes only shown from FXP with approved PSP relationship

### Intermediary Agents Retrieval
- Called via `GET /quotes/{quoteId}/intermediary-agents`
- Returns SAP account details for both Source and Destination
- Required for pacs.008 message construction

---

## 10. Address Validation Requirements

### Supported Address Types
1. **Account Number (ACCT)**
   - Direct account-based payments
   - Requires account number and BIC
   - Used where IBAN not available

2. **Email Proxy (EMAL)**
   - Payments to email addresses
   - Resolved via proxy directory
   - Requires email and BIC

3. **Mobile Number Proxy (MBNO)**
   - Payments to mobile numbers
   - Resolved via proxy directory
   - Requires mobile number and BIC

4. **National ID Proxy (NID)**
   - Payments using national ID numbers
   - Country-specific implementation
   - Requires ID and BIC

### Address Validation Flow
1. **Sender** provides recipient details via API form
2. **Source PSP** displays appropriate input fields based on address type
3. **Source PSP** sends acmt.023 message to Nexus for resolution
4. **Nexus** forwards to Destination PSP for account verification
5. **Destination PSP** returns validated account details
6. **Response** includes display name and account information

### Input Field Requirements
Each address type has defined:
- Input validation patterns
- Required fields
- ISO 20022 XPath mappings
- Localization labels (English, German, etc.)

---

## 11. Currency, Country, and Financial Institution Constraints

### Supported Countries (as of documentation)
- **Hong Kong (HK)**: HKD, CNY (max: 10,000-20,000)
- **Indonesia (ID)**: IDR (max: 15,000,000)
- **Malaysia (MY)**: MYR (max: 10,000,000)
- **Philippines (PH)**: PHP (max: 50,000)
- **Singapore (SG)**: SGD (max: 200,000)
- **Thailand (TH)**: THB (max: 2,000,000)

### Currency Requirements
- 3-letter ISO currency codes
- Maximum amounts per currency/country combination
- Interbank settlement in both source and destination currencies
- Currency conversion with applied exchange rates

### Financial Institution Constraints
1. **BIC Requirements:**
   - 6-8 character BIC codes
   - Validation pattern: `^[A-Z]{6}[0-9A-Z]{2}([0-9A-Z]{3})?$`
   - Required for all payment instructions

2. **LEI Requirements:**
   - Legal Entity Identifier for corporate entities
   - Optional for some institutions
   - Required for SAP registration

3. **Clearing System IDs:**
   - System-specific identifiers (e.g., SGDFAST, PHPINST)
   - Required for maximum amount validation
   - Varies by IPS implementation

### Maximum Amount Constraints
- Defined per IPS, not by Nexus
- Applied automatically during quote generation
- Response includes cap information if limits exceeded
- Cannot be overridden by PSPs

---

## 12. UI/UX Requirements

### Sender Interface Requirements
1. **Form Elements:**
   - Currency selection dropdown
   - Amount input with validation
   - Address type selection
   - Recipient detail input fields
   - Purpose code/category code selection
   - Message/reference text field

2. **Display Requirements:**
   - Full transparency on recipient amount
   - Real-time exchange rate display
   - Fee breakdown
   - Estimated delivery time
   - Regulatory warnings (if applicable)

3. **Input Validation:**
   - Pattern matching for account numbers
   - Email/phone number validation
   - Maximum amount enforcement
   - Real-time format checking

### Address Input Generation
Based on country and address type:
```javascript
// Example address input field structure
{
  "addressInputId": "PHINPT1",
  "label": {
    "en": "Account number, 10-18 digits",
    "de": "Kontonummer, 10-18 Ziffern"
  },
  "attributes": {
    "name": "accountOrProxyId",
    "type": "number",
    "pattern": "^\\d{10,18}$",
    "placeholder": "1234567890",
    "required": true
  },
  "iso20022XPath": {
    "acmt023": "/Document/IdVrfctnReq/Vrfctn/PtyAndAcctId/Acct/Id/Othr/Id",
    "pacs008": "/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/CrtrAcct/Id/Othr/Id"
  }
}
```

### Payment Status Display
- Real-time status updates
- Visual indicators for payment state
- Transaction reference numbers
- Error messages with explanations
- Support for investigation initiation

### Accessibility Requirements
- Multi-language support (English, German, etc.)
- Screen reader compatibility
- Keyboard navigation
- Clear error messages
- Responsive design for mobile devices

---

## Summary of Key Specifications

### Technical Requirements
- **Message Format:** ISO 20022 XML messages only
- **API Style:** RESTful APIs with JSON responses
- **Security:** TLS/SSL encryption required
- **Authentication:** API key-based authentication
- **Message Validation:** Strict XPath-based validation

### Operational Requirements
- **Processing Time:** Real-time (near-instant) for most payments
- **SLAs:** Defined response time requirements for all participants
- **Settlement:** Final and irrevocable once confirmed
- **Reconciliation:** Daily camt.054 reports provided
- **Disputes:** Manual process via Service Desk for now

### Compliance Requirements
- **Sanctions Screening:** Mandatory for all PSPs
- **AML/CFT:** Compliance with local regulations
- **Data Protection:** GDPR and local privacy laws
- **Audit Trail:** Complete transaction history maintained
- **Reporting:** Regular regulatory reporting required

This comprehensive analysis provides the foundation for all other audits of the Nexus Global Payments Sandbox implementation.
