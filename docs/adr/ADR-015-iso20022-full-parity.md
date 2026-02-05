# ADR-015: ISO 20022 Full Protocol Parity in Nexus Sandbox

## Status
Accepted

## Context
The Nexus Global Payments Sandbox aims to provide a high-fidelity simulation of the Nexus payment scheme for PSPs and SAPs. While the core happy-path payment flow (pacs.008 -> pacs.002 -> camt.054) was implemented, gaps existed in the support for:
1.  **Exception Handling**: Returns (pacs.004) and Cancellations (camt.056/camt.029).
2.  **Status Investigations**: Payment Status Requests (pacs.028).
3.  **SAP Integration**: Reservation messages (camt.103).
4.  **Corporate Initiation**: Customer Credit Transfers (pain.001).
5.  **Proxy Resolution**: Explicit builders for proxy resolution (acmt.023/acmt.024) were missing, distinct from the endpoint logic.

To serve as a comprehensive reference implementation, the sandbox must achieve 100% protocol parity with the ISO 20022 message set defined in the Nexus specifications, even for messages marked as "future" or "planning" in some documentation versions.

## Decision
We decided to implement explicit, XSD-compliant Python XML builders for all 11 core ISO 20022 message types identified in the Nexus specification.

### Scope of Messages
| Message | Name | Purpose | Implementation |
|---------|------|---------|----------------|
| `pacs.008.001.13` | FIToFICustomerCreditTransfer | Interbank Payment | Updated Frontend/Backend |
| `pacs.002.001.15` | FIToFIPaymentStatusReport | Payment Status/Ack | Updated Backend Builder |
| `camt.054.001.13` | BankToCustomerDebitCreditNotification | Settlement Notification | Updated Backend Builder |
| `acmt.023.001.04` | IdentificationVerificationRequest | Proxy Resolution Request | **New** Backend Builder |
| `acmt.024.001.04` | IdentificationVerificationReport | Proxy Resolution Report | **New** Backend Builder |
| `pain.001.001.12` | CustomerCreditTransferInitiation | Corporate Initiation | **New** Backend Builder |
| `camt.103.001.03` | CreateReservation | SAP Liquidity Reservation | **New** Backend Builder |
| `pacs.004.001.14` | PaymentReturn | Returns (Refunds) | **New** Backend Builder |
| `pacs.028.001.06` | FIToFIPaymentStatusRequest | Status Check / Enquiry | **New** Backend Builder |
| `camt.056.001.11` | FIToFIPaymentCancellationRequest | Recall/Cancellation | **New** Backend Builder |
| `camt.029.001.13` | ResolutionOfInvestigation | Recall Resolution | **New** Backend Builder |

### Technical Approach
1.  **Explicit Builders**: Instead of generic string templates, we implemented dedicated functions (e.g., `build_pacs004`, `build_camt056`) in `iso20022.py`.
2.  **XSD Compliance**: Each builder was constructed by inspecting the specific XSD schema to ensure correct element hierarchy, ordering, and mandatory field inclusion (e.g., `GrpHdr` vs `Assgnmt` headers).
3.  **Namespace Accuracy**: Specific ISO 20022 versions (e.g., `camt.056.001.11`) are enforced in the XML namespaces.
4.  **Forensic Logging**: Failed validations are logged with full XML payloads for auditability.

## Consequences
### Positive
-   **Completeness**: The sandbox can now simulate unhappy paths (returns, recalls) and complex flows (proxy resolution, SAP reservation) with high fidelity.
-   **Verification**: Developers can use the sandbox to validate their own parsers against valid Nexus XML output for all message types.
-   **Future-Proofing**: Support for `pacs.004` and others anticipates future Nexus roadmap activity.

### Negative
-   **Maintenance**: Any updates to the Nexus usage guidelines (e.g., upgrading to new ISO versions) will require updating 11 distinct builder functions.
-   **Complexity**: The `iso20022.py` file has grown significantly; future refactoring might be needed to split builders into separate modules if they grow further.

## References
-   Nexus Documentation: `docs.nexusglobalpayments.org_documentation.md`
-   Implementation Plan: `implementation_plan.md.resolved`
