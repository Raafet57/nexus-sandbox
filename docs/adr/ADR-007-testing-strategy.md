# ADR-007: Testing Strategy

**Status**: Accepted  
**Date**: 2026-02-02  
**Decision Makers**: Development Team  
**Technical Story**: Define comprehensive testing strategy for spec-driven development

## Context

This implementation follows **spec-driven development**, meaning:

1. Tests are derived from the official Nexus documentation
2. Tests verify API contract compliance
3. Tests cover all documented payment flows
4. Tests validate ISO 20022 message conformance

### Reference Documentation

- [Payment Setup Steps 1-17](https://docs.nexusglobalpayments.org/payment-setup/key-points)
- [API Specifications](https://docs.nexusglobalpayments.org/apis/overview)
- [ISO 20022 Message Guidelines](https://docs.nexusglobalpayments.org/messaging-and-translation/message-guidelines-excel)
- [Validation Rules](https://docs.nexusglobalpayments.org/payment-processing/validations-duplicates-and-fraud)

## Decision

### Testing Pyramid

```
           ┌───────────────┐
           │   E2E Tests   │  ← Full payment flows
           │   (10-15%)    │
           └───────────────┘
          ┌─────────────────┐
          │ Integration     │  ← Cross-service
          │ Tests (30%)     │
          └─────────────────┘
        ┌───────────────────┐
        │   Unit Tests      │  ← Business logic
        │   (55-60%)        │
        └───────────────────┘
```

### Test Categories

#### 1. Unit Tests

**Scope**: Individual functions and classes  
**Framework**: pytest (Python), Jest (Node.js)  
**Coverage Target**: 80%

```python
# tests/unit/test_quote_service.py

class TestQuoteGeneration:
    """
    Test FX quote generation logic.
    
    Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-3-6-exchange-rates
    """
    
    def test_quote_applies_tier_improvement(self):
        """
        Verify tier-based rate improvements are applied.
        
        Reference: https://docs.nexusglobalpayments.org/fx-provision/rates-from-third-party-fx-providers/improving-rates-for-larger-transactions
        """
        # Arrange
        base_rate = Decimal("25.50")
        amount = Decimal("10000")  # Qualifies for tier improvement
        fxp_config = FxpConfig(
            tier_improvements=[
                TierImprovement(min_amount=5000, improvement_bps=5),
                TierImprovement(min_amount=10000, improvement_bps=10),
            ]
        )
        
        # Act
        improved_rate = apply_tier_improvement(base_rate, amount, fxp_config)
        
        # Assert
        # 10 bps improvement = 0.1% = rate * 1.001 for buy-side
        expected = Decimal("25.5255")  # 25.50 * 1.001
        assert improved_rate == expected
    
    def test_quote_caps_to_max_amount(self):
        """
        Verify amounts exceeding IPS limits are capped.
        
        Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-3-6-exchange-rates
        Quote: "Nexus will check that the Interbank Settlement Amount does not 
        exceed the MaxAmount values in either the Source or Destination IPS"
        """
        # Arrange
        request = QuoteRequest(
            source_country="SG",
            destination_country="TH",
            amount=Decimal("300000"),  # Exceeds SG max of 200000
            amount_type=AmountType.SOURCE,
        )
        
        # Act
        result = generate_quote(request)
        
        # Assert
        assert result.capped_to_max_amount == True
        assert result.interbank_settlement_amount <= Decimal("200000")
```

#### 2. Integration Tests

**Scope**: Cross-service interactions  
**Framework**: pytest with Docker Compose  
**Environment**: Full stack (gateway + database + cache)

```python
# tests/integration/test_quotes_api.py

class TestQuotesApiIntegration:
    """
    Integration tests for GET /quotes endpoint.
    
    Reference: https://docs.nexusglobalpayments.org/apis/quotes
    """
    
    @pytest.fixture
    async def authenticated_client(self):
        """Get OAuth token for PSP."""
        token = await get_test_token(
            client_id="test-psp-sg",
            scope="quotes:read"
        )
        return AsyncClient(
            base_url="http://localhost:8000/v1",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    async def test_get_quotes_returns_valid_structure(
        self, authenticated_client
    ):
        """
        Verify GET /quotes response matches documented schema.
        
        Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-3-6-exchange-rates#step-4-nexus-generates-quotes
        """
        # Act
        response = await authenticated_client.get(
            "/quotes",
            params={
                "sourceCountry": "SG",
                "destCountry": "TH",
                "amount": "1000",
                "amountType": "SOURCE",
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure per documentation
        assert "quotes" in data
        for quote in data["quotes"]:
            assert "quoteId" in quote
            assert "fxpId" in quote
            assert "exchangeRate" in quote
            assert "expiresAt" in quote
            
            # Quote validity per Nexus spec (10 minutes)
            expires_at = datetime.fromisoformat(quote["expiresAt"])
            assert expires_at > datetime.utcnow()
            assert (expires_at - datetime.utcnow()).seconds <= 600
    
    async def test_quote_requires_authentication(self, client):
        """Verify unauthenticated requests are rejected."""
        response = await client.get(
            "/quotes",
            params={
                "sourceCountry": "SG",
                "destCountry": "TH",
                "amount": "1000",
                "amountType": "SOURCE",
            }
        )
        
        assert response.status_code == 401
```

#### 3. End-to-End Tests

**Scope**: Complete payment flows across all actors  
**Framework**: pytest with Docker Compose (full stack)  
**Environment**: All services running

```python
# tests/e2e/test_full_payment_flow.py

class TestFullPaymentFlow:
    """
    End-to-end tests for complete Nexus payment flows.
    
    Reference: https://docs.nexusglobalpayments.org/payment-setup/key-points
    
    These tests verify the entire payment journey from
    sender input to recipient notification.
    """
    
    @pytest.mark.timeout(120)  # Payment SLA is 60 seconds
    async def test_successful_sg_to_th_payment(self):
        """
        Test successful payment from Singapore to Thailand.
        
        Steps verified (per documentation):
        1-2: Country/currency selection
        3-6: FX quote retrieval
        7-9: Proxy resolution (mobile number)
        10-11: Sanctions screening (pass)
        12: Sender approval
        13-16: Payment instruction submission
        17: Confirmation received
        
        Reference: Full flow at https://docs.nexusglobalpayments.org/payment-setup/key-points
        """
        # Step 1-2: Verify country availability
        countries = await self.gateway_client.get("/countries")
        assert any(c["countryCode"] == "TH" for c in countries["countries"])
        
        # Step 3-4: Get FX quotes
        quotes_response = await self.gateway_client.get(
            "/quotes",
            params={
                "sourceCountry": "SG",
                "destCountry": "TH",
                "amount": "1000",
                "amountType": "SOURCE",
            }
        )
        assert quotes_response.status_code == 200
        quote = quotes_response.json()["quotes"][0]
        quote_id = quote["quoteId"]
        
        # Step 5: Select preferred quote
        # (PSP internal decision - we just record the selection)
        
        # Step 7-9: Resolve proxy (mobile number)
        proxy_response = await self.pdo_client.post(
            "/v1/addressing/resolve",
            json={
                "proxyType": "MOBI",
                "proxyValue": "+66812345678",
                "destinationCountry": "TH",
            }
        )
        assert proxy_response.json()["resolved"] == True
        creditor_account = proxy_response.json()["creditorAccount"]
        
        # Step 10-11: Sanctions screening (passed internally)
        
        # Step 13: Get intermediary agents
        agents_response = await self.gateway_client.get(
            f"/quotes/{quote_id}/intermediary-agents"
        )
        assert agents_response.status_code == 200
        agents = agents_response.json()
        
        # Step 14-15: Build and submit pacs.008
        uetr = uuid4()
        pacs008 = build_pacs008(
            uetr=uetr,
            quote=quote,
            creditor_account=creditor_account,
            intermediary_agents=agents,
            debtor_name="John Smith",
            creditor_name="Somchai Jaidee",
        )
        
        # Submit via Source IPS
        submit_response = await self.ips_sg_client.post(
            "/clearing/submit",
            content=pacs008.to_xml(),
            headers={"Content-Type": "application/xml"},
        )
        assert submit_response.status_code == 202
        
        # Step 17: Wait for completion
        # Monitor for pacs.002 ACCC status
        completion = await self.wait_for_payment_completion(uetr, timeout=60)
        
        assert completion.status == "ACCC"
        assert completion.creditor_amount == Decimal("25870")  # At rate ~25.87
        
        # Verify event trail
        events = await self.get_payment_events(uetr)
        event_types = [e["event_type"] for e in events]
        
        assert "PAYMENT_INITIATED" in event_types
        assert "PAYMENT_FORWARDED" in event_types
        assert "PAYMENT_ACCEPTED" in event_types
        assert "PAYMENT_COMPLETED" in event_types
    
    async def test_rejected_payment_sanctions_hit(self):
        """
        Test payment rejection due to sanctions screening failure.
        
        Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening
        """
        # Use name that triggers DEMO sanctions list
        pacs008 = build_pacs008(
            debtor_name="Kim Jong Un",  # Sanctions match
            ...
        )
        
        # Submit payment
        submit_response = await self.ips_sg_client.post(
            "/clearing/submit",
            content=pacs008.to_xml(),
        )
        
        # Should receive rejection
        completion = await self.wait_for_payment_completion(
            pacs008.uetr, timeout=30
        )
        
        assert completion.status == "RJCT"
        assert "SANC" in completion.reason_code  # Sanctions rejection
```

#### 4. Contract Tests

**Scope**: API contract compliance between services  
**Framework**: schemathesis (OpenAPI testing)

```python
# tests/contract/test_api_contracts.py

import schemathesis

# Load OpenAPI spec
schema = schemathesis.from_path("./specs/nexus-gateway.yaml")

@schema.parametrize()
def test_api_contracts(case):
    """
    Verify all endpoints conform to OpenAPI specification.
    
    This ensures our implementation matches the documented API structure.
    """
    response = case.call()
    case.validate_response(response)
```

#### 5. ISO 20022 Conformance Tests

**Scope**: XML message validation against XSD schemas  
**Framework**: pytest with lxml

```python
# tests/conformance/test_iso20022_messages.py

class TestISO20022Conformance:
    """
    Validate generated messages against ISO 20022 XSD schemas.
    
    Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-guidelines-excel
    """
    
    @pytest.fixture
    def pacs008_schema(self):
        """Load pacs.008 XSD schema."""
        return etree.XMLSchema(
            etree.parse("specs/iso20022/pacs.008.001.08.xsd")
        )
    
    def test_generated_pacs008_validates(self, pacs008_schema):
        """Verify generated pacs.008 is schema-valid."""
        # Generate a pacs.008 message
        message = build_pacs008(
            uetr=uuid4(),
            debtor_name="John Smith",
            debtor_account="123456789",
            creditor_name="Somchai Jaidee",
            creditor_account="987654321",
            amount=Decimal("1000.00"),
            source_currency="SGD",
            dest_currency="THB",
            exchange_rate=Decimal("25.87"),
        )
        
        # Parse and validate
        doc = etree.fromstring(message.to_xml().encode())
        
        assert pacs008_schema.validate(doc), \
            f"Validation errors: {pacs008_schema.error_log}"
    
    def test_pacs008_contains_required_nexus_elements(self):
        """
        Verify Nexus-required elements are present.
        
        Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/specific-message-elements
        """
        message = build_pacs008(...)
        doc = etree.fromstring(message.to_xml().encode())
        
        # UETR is required
        uetr = doc.find(".//UETR", namespaces=ISO20022_NS)
        assert uetr is not None
        
        # Single transaction only
        nb_of_txs = doc.find(".//NbOfTxs", namespaces=ISO20022_NS)
        assert nb_of_txs.text == "1"
        
        # Intermediary agents for FXP routing
        intrmy_agt1 = doc.find(".//IntrmyAgt1", namespaces=ISO20022_NS)
        assert intrmy_agt1 is not None
```

### Test Data Management

Seed data for tests is defined in `/seed/`:

```json
// seed/countries.json - Match official API response
{
  "countries": [
    {
      "countryId": 702,
      "countryCode": "SG",
      "name": "Singapore",
      "currencies": [
        {
          "currencyCode": "SGD",
          "maxAmount": "200000"
        }
      ],
      "requiredMessageElements": {
        "pacs008": ["purposeCode"]
      }
    }
  ]
}
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: |
          cd services/nexus-gateway
          pip install -e ".[test]"
          pytest tests/unit -v --cov=src --cov-report=xml
      
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker compose up -d
      - name: Wait for healthy
        run: ./scripts/wait-for-healthy.sh
      - name: Run integration tests
        run: pytest tests/integration -v
      
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start full stack
        run: docker compose --profile full up -d
      - name: Run E2E tests
        run: pytest tests/e2e -v --timeout=300
```

## Alternatives Considered

### Manual Testing Only

**Pros**: Faster initially

**Cons**: Not scalable, regressions slip through

**Decision**: Rejected; comprehensive automated testing is essential.

### Postman Collections

**Pros**: Easy to share, visual

**Cons**: Limited programmability, harder to CI

**Decision**: Use for documentation supplements, not primary testing.

## Consequences

### Positive

- Confidence in spec compliance
- Regression detection
- Documentation via tests

### Negative

- Test maintenance overhead
- CI execution time

## Related Decisions

- [ADR-005](ADR-005-api-design-principles.md): API contracts under test
- [ADR-003](ADR-003-iso20022-message-handling.md): XML validation
