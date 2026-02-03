# Nexus Assumptions: Developer Observability & API Access (A28-A30)

This document outlines assumptions regarding developer tooling, API documentation visibility, and observability features.

## A28: Per-Message-Type Callback Endpoints

- **A28.1: Query Parameter Callbacks**: When submitting ISO 20022 messages (pacs.008, acmt.023), the Source IPSO provides callback URLs as **query parameters**, not in the message body.

  ```http
  POST /iso20022/pacs008?pacs002Endpoint=http://source-ips/callback/pacs002&acmt024Endpoint=http://source-ips/callback/acmt024
  ```

- **A28.2: Callback Priority**: Callback registration is a **prerequisite** for payment submission. A payment cannot be initiated without defining where the response should be delivered.

- **A28.3: Gateway-Stored Callbacks**: The Nexus Gateway stores callback URLs and delivers responses asynchronously to the registered endpoints.

## A29: Developer Mode and Raw Message Access

- **A29.1: DevDebugPanel Component**: The frontend includes a collapsible "Developer Mode" panel showing:
  - UETR and Quote ID
  - Intermediary Agent chain
  - Gateway transformations (agent swapping, amount conversion)
  - Status reason codes

- **A29.2: Raw XML Visibility**: Developers can view raw pacs.008 and pacs.002 XML messages in the Payments Explorer to debug transformation issues.

- **A29.3: Message Inspector**: All actors (FXP, PSP, IPS, PDO, SAP, Mesh) have access to context-specific ISO 20022 message viewers showing sent/received messages.

## A30: OpenAPI/Swagger API Documentation

- **A30.1: Swagger UI at /docs**: FastAPI exposes interactive API documentation at `/docs` (Swagger UI) for developer exploration.

- **A30.2: ReDoc at /redoc**: Alternative documentation format available at `/redoc`.

- **A30.3: Dashboard Integration**: The demo dashboard includes a navigation link to API documentation for discoverability.

---

## Cross-Reference: Implementation Verification

| Assumption | Spec Requirement | Implementation File | Status |
|------------|------------------|---------------------|--------|
| A28.1 (Query Callbacks) | pacs002Endpoint param | `iso20022.py:parse_query_params` | 🔜 Planned |
| A28.3 (Gateway Delivery) | Async callback delivery | `iso20022.py:deliver_callback` | 🔜 Planned |
| A29.1 (DevDebugPanel) | Debug visibility | `DevDebugPanel.tsx` | ✅ Implemented |
| A29.2 (Raw XML) | Message inspection | `payments_explorer.py` | 🔜 Enhance |
| A30.1 (Swagger) | API docs | `main.py:docs_url="/docs"` | ✅ Implemented |
| A30.3 (Dashboard Link) | Navigation | `Navigation.tsx` | 🔜 Add link |

---

**Reference**: NotebookLM 2026-02-03 - Developer Observability and API Documentation
