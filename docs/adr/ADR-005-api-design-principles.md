# ADR-005: API Design Principles

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Define REST API design principles that align with official Nexus API specifications

## Context

The Nexus API is documented at [APIs Overview](https://docs.nexusglobalpayments.org/apis/overview) with specific endpoint definitions. Our sandbox implementation must:

1. **Faithfully replicate** the official API structure
2. **Support testing** by third-party PSP/FXP developers
3. **Provide clear documentation** via OpenAPI specifications
4. **Enable demo scenarios** with additional endpoints where needed

### Official Nexus API Structure

From the [API documentation](https://docs.nexusglobalpayments.org/apis/overview), Nexus provides:

| Category | Endpoints |
|----------|-----------|
| **Discovery** | `/countries`, `/countries/{code}`, `/countries/{code}/address-types` |
| **Quotes** | `/quotes`, `/quotes/{id}`, `/quotes/{id}/intermediary-agents` |
| **Fees** | `/fees-and-amounts` |
| **Rates** | `/rates` (FXP submission) |
| **Financial Institutions** | `/countries/{code}/psps`, `/countries/{code}/fin-insts` |

## Decision

### Principle 1: Mirror Official API Structure

All endpoints documented at docs.nexusglobalpayments.org are implemented with **identical paths and response structures**.

```python
# Exact match to official API
@router.get("/countries")
async def retrieve_all_countries() -> CountriesResponse:
    """
    Retrieve All Countries in Nexus
    
    Reference: https://docs.nexusglobalpayments.org/apis/countries#get-countries
    """
    ...

@router.get("/countries/{country_code}")
async def retrieve_single_country(country_code: str) -> CountryResponse:
    """
    Retrieve a Single Country
    
    Reference: https://docs.nexusglobalpayments.org/apis/countries#get-countries-countrycode
    """
    ...
```

### Principle 2: Response Schema Fidelity

Response schemas match the official documentation exactly:

**Reference**: [Countries API Response](https://docs.nexusglobalpayments.org/apis/countries)

```python
class CurrencyInfo(BaseModel):
    """Currency information as documented."""
    currency_code: str = Field(alias="currencyCode")
    max_amount: str = Field(alias="maxAmount")

class RequiredMessageElements(BaseModel):
    """Required fields per message type."""
    pacs008: list[str] | None = None

class CountryInfo(BaseModel):
    """Country information matching official schema."""
    country_id: int = Field(alias="countryId")
    country_code: str = Field(alias="countryCode")
    name: str
    currencies: list[CurrencyInfo]
    required_message_elements: RequiredMessageElements = Field(
        alias="requiredMessageElements"
    )

class CountriesResponse(BaseModel):
    """Response from GET /countries."""
    countries: list[CountryInfo]
```

### Principle 3: Reference Documentation in Code

Every endpoint includes a reference to the official documentation:

```python
@router.get("/quotes")
async def get_quotes(
    source_country: str = Query(..., alias="sourceCountry"),
    destination_country: str = Query(..., alias="destCountry"),
    amount: Decimal = Query(...),
    amount_type: str = Query(..., alias="amountType", regex="^(SOURCE|DESTINATION)$"),
) -> QuotesResponse:
    """
    Retrieve FX Quotes
    
    Returns a list of quotes from available FX Providers for the specified
    payment parameters.
    
    Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-3-6-exchange-rates
    
    Args:
        source_country: ISO 3166-1 alpha-2 country code of the sender
        destination_country: ISO 3166-1 alpha-2 country code of the recipient
        amount: Payment amount
        amount_type: SOURCE (sender amount) or DESTINATION (recipient amount)
    
    Quote Validity:
        Quotes are valid for 10 minutes from generation, as specified in the
        Nexus Scheme Rulebook.
    """
    ...
```

### Principle 4: Sandbox-Specific Extensions

Additional endpoints for testing/demo are prefixed with `/sandbox/`:

```python
# Sandbox-only endpoints (not in official API)
@router.post("/sandbox/payments/initiate")
async def initiate_demo_payment(request: DemoPaymentRequest) -> PaymentResponse:
    """
    Initiate a demo payment (sandbox only)
    
    This endpoint simplifies payment initiation for testing purposes.
    In production, payments are initiated via ISO 20022 messages from PSPs.
    """
    ...

@router.post("/sandbox/simulate/fx-rate-change")
async def simulate_rate_change(request: RateChangeRequest) -> None:
    """
    Simulate FX rate change (sandbox only)
    
    Forces a rate update for testing quote refresh scenarios.
    """
    ...
```

### Principle 5: Error Response Standardization

Error responses follow a consistent structure:

**Reference**: Error handling aligns with [Rejects](https://docs.nexusglobalpayments.org/payment-processing/unsuccessful-payments-exceptions/rejects)

```python
class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str           # Machine-readable error code
    message: str        # Human-readable message
    field: str | None   # Field that caused the error (if applicable)
    reference: str | None  # Link to documentation

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
    trace_id: str       # Correlation ID for debugging

# Error codes mapped from Nexus reject reasons
ERROR_CODES = {
    "QUOTE_EXPIRED": "The selected FX quote has expired",
    "QUOTE_NOT_FOUND": "Quote ID not recognized",
    "AMOUNT_EXCEEDS_LIMIT": "Amount exceeds IPS or PSP limits",
    "CURRENCY_NOT_SUPPORTED": "Currency pair not available",
    "CORRIDOR_NOT_AVAILABLE": "Country pair not enabled",
    "PROXY_NOT_FOUND": "Proxy resolution failed",
    "DUPLICATE_UETR": "Payment with this UETR already exists",
    "INSUFFICIENT_DATA": "Missing required FATF R16 data",
}
```

### Principle 6: Versioning Strategy

API version is embedded in the base path:

```
/v1/countries
/v1/quotes
```

This matches the implicit versioning in the Nexus documentation structure.

### Principle 7: Query Parameter Naming

Use camelCase for query parameters to match official API:

| Official API | Our Implementation |
|--------------|-------------------|
| `sourceCountry` | `source_country: str = Query(alias="sourceCountry")` |
| `destCountry` | `dest_country: str = Query(alias="destCountry")` |
| `amountType` | `amount_type: str = Query(alias="amountType")` |

### API Endpoint Catalog

#### Discovery APIs

| Method | Path | Description | Reference |
|--------|------|-------------|-----------|
| GET | `/countries` | List all countries | [Countries API](https://docs.nexusglobalpayments.org/apis/countries#get-countries) |
| GET | `/countries/{code}` | Single country | [Countries API](https://docs.nexusglobalpayments.org/apis/countries#get-countries-countrycode) |
| GET | `/countries/{code}/currencies/{currency}/max-amounts` | Transaction limits | [Currencies API](https://docs.nexusglobalpayments.org/apis/currencies) |
| GET | `/countries/{code}/address-types` | Address types | [Address Types API](https://docs.nexusglobalpayments.org/apis/address-types-and-inputs) |
| GET | `/countries/{code}/address-types-and-inputs` | Full address inputs | [Address Types API](https://docs.nexusglobalpayments.org/apis/address-types-and-inputs) |
| GET | `/countries/{code}/psps` | PSPs in country | [Financial Institutions API](https://docs.nexusglobalpayments.org/apis/financial-institutions) |
| GET | `/countries/{code}/fin-insts/{role}` | Financial institutions | [Financial Institutions API](https://docs.nexusglobalpayments.org/apis/financial-institutions) |

#### Quote APIs

| Method | Path | Description | Reference |
|--------|------|-------------|-----------|
| GET | `/quotes` | Get FX quotes | [Exchange Rates](https://docs.nexusglobalpayments.org/payment-setup/steps-3-6-exchange-rates) |
| GET | `/quotes/{quoteId}` | Single quote | [Quotes](https://docs.nexusglobalpayments.org/fx-provision/quotes) |
| GET | `/quotes/{quoteId}/intermediary-agents` | SAP account details | [Step 13](https://docs.nexusglobalpayments.org/payment-setup/step-13-16-set-up-and-send-the-payment-instruction) |

#### Fee APIs

| Method | Path | Description | Reference |
|--------|------|-------------|-----------|
| GET | `/fees-and-amounts` | Calculate fees | [Fees and Amounts](https://docs.nexusglobalpayments.org/apis/fees-and-amounts) |

#### Rate Management (FXP)

| Method | Path | Description | Reference |
|--------|------|-------------|-----------|
| POST | `/rates` | Submit rates | [Rates API](https://docs.nexusglobalpayments.org/fx-provision/rates-from-third-party-fx-providers) |
| DELETE | `/rates/{rateId}` | Withdraw rate | [Rates API](https://docs.nexusglobalpayments.org/fx-provision/rates-from-third-party-fx-providers) |

#### Sandbox-Only APIs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sandbox/payments/initiate` | Demo payment initiation |
| GET | `/sandbox/payments/{uetr}` | Get payment status (for demo) |
| POST | `/sandbox/simulate/delay` | Add artificial delay |
| POST | `/sandbox/simulate/reject` | Force payment rejection |

## Alternatives Considered

### Custom API Structure

**Approach**: Design our own API structure optimized for developer experience

**Pros:**
- Could be more intuitive
- Modern REST patterns

**Cons:**
- Doesn't match official Nexus API
- Integrators would need to rewrite for production

**Decision**: Rejected; fidelity to official API is paramount.

### GraphQL API

**Approach**: Offer GraphQL in addition to REST

**Pros:**
- Flexible queries
- Reduced over-fetching

**Cons:**
- Nexus is REST-only
- Additional complexity

**Decision**: Rejected; REST-only to match production.

## Consequences

### Positive

- Integrators can test against sandbox and deploy to production with minimal changes
- Clear documentation trail to official specs
- OpenAPI spec can be validated against official API

### Negative

- Some modern API patterns sacrificed for compatibility
- Must track official API changes

## Related Decisions

- [ADR-002](ADR-002-pluggable-actor-architecture.md): Actor-specific API contracts
- [ADR-007](ADR-007-testing-strategy.md): API testing approach
