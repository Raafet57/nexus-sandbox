# ADR-016: API Parity and Naming Standards

## Status
Accepted

## Context
The Nexus Global Payments Sandbox API must maintain strict parity with the official detailed technical specifications (`docs.nexusglobalpayments.org`) to ensure it serves as a valid reference implementation for PSPs and IPS operators.

During the audit, we identified three classes of divergence:
1.  **Parameter Naming**: The documentation uses `camelCase` for path and query parameters (e.g., `countryCode`, `quoteId`), while the Python/FastAPI implementation followed PEP-8 `snake_case` (e.g., `country_code`, `quote_id`). This resulted in generated OpenAPI specifications that did not match the official contracts.
2.  **Path Structure**: Certain endpoints diverged in URL structure (e.g., `/address-types` vs `/addressTypesAndInputs`).
3.  **Missing Endpoints**: Some fee calculation endpoints (e.g., creditor agent fee disclosure) were missing entirely.

## Decision

### 1. Enforce Documentation-First Parameter Naming
All API endpoints MUST use `alias` arguments in Pydantic models and FastAPI `Path`/`Query` parameters to expose `camelCase` names to the public API while maintaining `snake_case` internally for Python code.

**Implementation Standard:**
```python
# GOOD
country_code: str = Path(..., alias="countryCode")

# BAD
country_code: str = Path(...)
```

### 2. Strict Path Compliance with Aliases
We will implement URL paths exactly as specified in the documentation. Where the codebase has established an alternative "cleaner" path (e.g., kebab-case), we will maintain the "strict" path as a hidden alias or primary route to satisfy documentation parity without breaking existing internal developer tools.

*   **Primary**: `/v1/countries/{countryCode}/addressTypesAndInputs` (Matches Doc)
*   **Legacy/Internal**: `/v1/countries/{countryCode}/address-types` (if needed)

### 3. Single Source of Truth for Logic
Duplicate endpoints (e.g., `max-amounts` in both `countries.py` and `currencies.py`) are strictly forbidden. The logic must reside in the domain-appropriate module (`countries.py` for country-specific regulation) and other routers should act as aliases or be removed if redundant.

## Consequences
### Positive
*   **100% Spec Compliance**: Client SDKs generated from our OpenAPI spec will now match the official SDKs.
*   **Reduced Friction**: Developers reading the official docs can copy-paste URLs and payloads directly into this sandbox.

### Negative
*   **Verbosity**: Code decorators become more verbose with explicit aliasing.
*   **Breaking Changes**: Clients relying on `snake_case` query parameters in the sandbox (if any existed outside our own demo) would need to update to `camelCase`. Given this is a sandbox environment, strict parity takes precedence.

## Verification
Verification is performed via `curl` requests checking explicitly against the documented parameter names (e.g., `?currencyCode=SGD` instead of `?currency_code=SGD`).
