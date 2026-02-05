# Nexus Assumptions: Status Reason Codes (A20)

This document identifies the ISO 20022 Status Reason Codes implemented to handle diverse rejection and investigation scenarios.

## A20: ISO Reason Code Mappings
The system assumes implementation of 60+ specific status codes across the following categories:

### A20.1: Account Issues
- `AC01`: Incorrect Account Number
- `AC04`: Closed Account Number
- `AC06`: Blocked Account
- `BE23`: Proxy Not Found (PDO Error)

### A20.2: Agent/Network Issues
- `AGNT`: Incorrect Agent BIC
- `AB03`: Settlement Timeout (HIGH Priority SLA expired)
- `AB04`: Rate mismatch or Quote expired
- `RC11`: Invalid Intermediary Agent (SAP mismatch)

### A20.3: Compliance & Regulatory
- `FR01`: Fraud Related
- `RR04`: Regulatory Reason (Sanctions/AML hit)

### A20.4: Amount & Liquidity
- `AM02`: Amount Exceeds IPS Limit
- `AM04`: Insufficient Funds (FXP liquidity failure at SAP)
- `AM09`: Wrong Amount (Principal mismatch)

### A20.5: Technical & Data Quality
- `FF01`: XSD Validation Failure
- `CH21`: Mandatory Element Missing
- `DUPL`: Duplicate Merchant Reference or UETR

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A20.2 (AB03) | Settlement Timeout | pacs002.py:110 | ✅ Verified |
| A20.2 (AB04) | Quote Expired | pacs002.py | ✅ Verified |
