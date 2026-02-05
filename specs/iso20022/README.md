# ISO 20022 Message Schemas for Nexus

This directory contains ISO 20022 XSD schemas for message validation in Nexus.

## ✅ Complete Schema Set

All required Nexus schemas are now available:

| Schema | Version | Size | Description | Status |
|--------|---------|------|-------------|--------|
| `pacs.002.001.15.xsd` | 15 | 61KB | Payment Status Report | ✅ |
| `pacs.004.001.14.xsd` | 14 | 79KB | Payment Return (Future) | ✅ |
| `pacs.008.001.13.xsd` | 13 | 63KB | FI Customer Credit Transfer | ✅ |
| `acmt.023.001.04.xsd` | 04 | 22KB | Identification Verification Request | ✅ |
| `acmt.024.001.04.xsd` | 04 | 23KB | Identification Verification Response | ✅ |
| `camt.054.001.13.xsd` | 13 | 107KB | Debit/Credit Notification | ✅ |

**Total:** 6 schemas, 355KB

## Directory Structure

```
xsd/
├── pacs.002.001.15.xsd      # Payment Status Report
├── pacs.004.001.14.xsd      # Payment Return (not supported yet)
├── pacs.008.001.13.xsd      # Payment Instruction
├── acmt.023.001.04.xsd      # Proxy Resolution Request
├── acmt.024.001.04.xsd      # Proxy Resolution Response
├── camt.054.001.13.xsd      # Reconciliation Notification
├── pacs_2024_2025/          # Full pacs archive + MDR docs
├── acmt_2024/               # Full acmt archive
└── camt_2025/               # Full camt archive
```

## Schema Sources

| Business Area | Source |
|---------------|--------|
| Payments Clearing (pacs) | ISO 20022 Catalogue 2024/2025 |
| Account Management (acmt) | ISO 20022 Catalogue 2024 |
| Cash Management (camt) | ISO 20022 Catalogue 2025 |

## Nexus-Specific Requirements

### Mandatory Elements (per Nexus deviation from ISO)

| Element | XPath | Notes |
|---------|-------|-------|
| **UETR** | `CdtTrfTxInf/PmtId/UETR` | UUID v4 format |
| **Purpose Code** | `CdtTrfTxInf/Purp/Cd` | Country-specific |
| **IntermediaryAgent1** | `CdtTrfTxInf/IntrmyAgt1` | FXP Source SAP |
| **IntermediaryAgent2** | `CdtTrfTxInf/IntrmyAgt2` | FXP Dest SAP |
| **Exchange Rate** | `CdtTrfTxInf/XchgRate` | Must match quote |
| **Quote ID** | `CdtTrfTxInf/PmtId/InstrId` | Nexus Quote ID |

### Nexus vs CBPR+ Deviations

| Element | CBPR+ | Nexus |
|---------|-------|-------|
| StsRsnInf (on RJCT) | Optional | **MANDATORY** |
| OrgnlGrpInf | Mandatory | Optional |
| OrgnlEndToEndId | Mandatory | Optional |

## pacs.002 Status Codes

| Code | Meaning |
|------|---------|
| ACCC | Settlement Completed (Success) |
| RJCT | Rejected (requires reason code) |
| BLCK | Blocked (investigation) |
| ACWP | Accepted Without Posting |
| ACTC | Technical Validation Accepted |

## Reason Codes for RJCT

| Code | Meaning |
|------|---------|
| AB03 | Settlement Timeout |
| AB04 | Rate Mismatch |
| AC04 | Closed Account |
| AC06 | Blocked Account |
| AM04 | Insufficient Funds |
| RC11 | Invalid Intermediary Agent |
| DUPL | Duplicate Payment |
| FR01 | Fraud |

## Usage in Python

```python
from lxml import etree

# Load schema
schema_doc = etree.parse("specs/iso20022/xsd/pacs.008.001.13.xsd")
schema = etree.XMLSchema(schema_doc)

# Validate message
message = etree.parse("message.xml")
is_valid = schema.validate(message)
```

## References

- [ISO 20022 Message Catalogue](https://www.iso20022.org/catalogue-messages)
- [Nexus Message Guidelines](https://docs.nexusglobalpayments.org/messaging-and-translation/message-guidelines-excel)
- [CPMI Harmonisation](https://docs.nexusglobalpayments.org/messaging-and-translation/adherence-to-cpmi-harmonised-iso-20022-data-requirements)
