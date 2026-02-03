# Nexus Sandbox 🌐

> **A complete educational sandbox implementation of the Nexus Global Payments scheme**

[![Demo Dashboard](https://img.shields.io/badge/Demo-Dashboard-blue)](http://localhost:8080)
[![API Docs](https://img.shields.io/badge/API-Docs-green)](http://localhost:8000/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Created by **[Siva Subramanian](https://sivasub.com)** | [GitHub](https://github.com/siva-sub) | [LinkedIn](https://www.linkedin.com/in/sivasub987/)

---

## 🎯 What is This?

This is a **portfolio project** demonstrating expertise in:
- **Cross-border instant payments** architecture
- **ISO 20022** message handling (pacs.008, pacs.002, camt.056)
- **Microservices** orchestration with Docker
- **Event-driven architecture** with Kafka
- **Distributed tracing** with Jaeger/OpenTelemetry

Based on the official [Nexus Global Payments documentation](https://docs.nexusglobalpayments.org/).

> ⚠️ **Disclaimer**: This is an educational sandbox. Not affiliated with Nexus Global Payments Ltd. or any founding central banks.

---

## 🚀 Quick Start


```bash
# Start all services
docker compose up -d

# Check the Usage Guide for simulation steps
# ./docs/USAGE_GUIDE.md
```

### 📖 Documentation Links
- [**Usage Guide**](./docs/USAGE_GUIDE.md): Start here to simulate your first payment.
- [**Integration Guide**](./docs/INTEGRATION_GUIDE.md): Connect your own PSP/FXP/IPS to the sandbox.
- [**API Reference**](./docs/API_REFERENCE.md): Complete list of available endpoints.
- [**Walkthrough**](./docs/assumptions/12_hardcoding_review.md): Detailed implementation log of the latest release.

---

## 🖥️ Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Demo Dashboard** | http://localhost:8080 | Interactive UI with payment demos |
| **API Documentation** | http://localhost:8000/docs | FastAPI auto-generated docs |
| **Swagger UI** | http://localhost:8081 | Alternative API explorer |
| **Jaeger Tracing** | http://localhost:16686 | Distributed tracing UI |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEXUS SANDBOX                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │
│  │ Demo        │     │ Swagger UI  │     │ Jaeger      │                    │
│  │ Dashboard   │     │             │     │ Tracing     │                    │
│  │ :8080       │     │ :8081       │     │ :16686      │                    │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                    │
│         │                   │                   │                            │
│         └───────────────────┼───────────────────┘                            │
│                             │                                                │
│                    ┌────────▼────────┐                                       │
│                    │  Nexus Gateway  │                                       │
│                    │     :8000       │                                       │
│                    │  (FastAPI)      │                                       │
│                    └────────┬────────┘                                       │
│                             │                                                │
│         ┌───────────────────┼───────────────────┐                            │
│         │                   │                   │                            │
│  ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐                    │
│  │ Postgres    │     │ Redis       │     │ Kafka       │                    │
│  │ :5432       │     │ :6379       │     │ :9092       │                    │
│  └─────────────┘     └─────────────┘     └─────────────┘                    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                        SIMULATORS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │ PSP-SG      │  │ PSP-TH      │  │ PSP-MY      │  Payment Service         │
│  │ DBS Bank    │  │ Kasikorn    │  │ Maybank     │  Providers               │
│  │ :3001       │  │ :3002       │  │ :3003       │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │ IPS-SG      │  │ IPS-TH      │  │ FXP-ABC     │  Instant Payment         │
│  │ FAST        │  │ PromptPay   │  │ FX Provider │  Systems + FX            │
│  │ :3101       │  │ :3102       │  │ :3201       │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐                                           │
│  │ SAP-DBS     │  │ PDO-SG      │  Settlement +                             │
│  │ Settlement  │  │ PayNow Dir  │  Proxy Directory                          │
│  │ :3301       │  │ :3401       │                                           │
│  └─────────────┘  └─────────────┘                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Demo Dashboard Screens

### 1. Landing Page
- Overview of Nexus architecture
- Key statistics and capabilities
- Quick navigation to all features

### 2. Actors & Fees
- All 13 participant types explained
- Fee structure visualization
- Competitive FX model diagram

### 3. Send Payment
- **Dynamic Address Forms**: Automatically generated inputs based on country-specific types (e.g., ACCT, MBNO).
- **Real-time Quoting**: Fee transparency and FX rate aggregation.
- **17-Step Lifecycle**: Complete observability of Step 1 to Step 17 (Confirmation).
- **ISO 20022 Messages**: Visualization of acmt.023/024 and pacs.008/002 flows.

### 4. ISO Messages
- 10+ message types documented
- Message flow patterns
- Status reason codes

---

## 🔌 API Endpoints

### Reference Data
```bash
# Get supported currencies
GET /currencies

# Get financial institutions
GET /financial-institutions?country=SG

# Get address types
GET /address-types-inputs?destinationCountry=TH
```

### Quotes & FX
```bash
# Get quote
GET /quotes?sourcePspBic=DBSSSGSG&destinationPspBic=KASITHBK&sourceCurrency=SGD&destinationCurrency=THB&sourceAmount=1000

# Lock quote
POST /quotes/{quoteId}/lock
```

### Payments
```bash
# Submit payment
POST /pacs008?pacs002Endpoint=https://callback.example.com

# Get payment status
GET /payments/{uetr}
```

### Returns & Recalls
```bash
# Return payment
POST /pacs004

# Recall payment
POST /camt056
```

---

## 🧪 Running Tests

```bash
# Run all tests
cd services/nexus-gateway
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_quotes.py -v
```

---

## 📁 Project Structure

```
nexus-sandbox/
├── docker-compose.yml          # Service orchestration
├── start.sh                    # One-command launcher
├── services/
│   ├── demo-dashboard/         # Frontend UI
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── index.html
│   │   ├── api.js             # API integration
│   │   └── screens/           # Dashboard pages
│   ├── nexus-gateway/          # Core API (FastAPI)
│   ├── psp-simulator/          # PSP mockups
│   ├── ips-simulator/          # IPS mockups
│   ├── fxp-simulator/          # FX provider
│   ├── sap-simulator/          # Settlement provider
│   └── pdo-simulator/          # Proxy directory
├── migrations/                 # Database schema
├── specs/                      # ISO 20022 XSDs
└── docs/                       # Documentation
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **API** | Python 3.11, FastAPI, Pydantic |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **Messaging** | Apache Kafka |
| **Tracing** | Jaeger, OpenTelemetry |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS |
| **Container** | Docker, Docker Compose |

---

## 📖 References

- [NGP Official Documentation](https://docs.nexusglobalpayments.org/)
- [ISO 20022 Message Catalogue](https://www.iso20022.org/catalogue-messages)
- [BIS Innovation Hub - Nexus](https://www.bis.org/about/bisih/topics/suptech_regtech/nexus.htm)

---

## 📄 License

MIT License © 2026 [Siva Subramanian](https://sivasub.com)

---

## 🤝 Contact

**Siva Subramanian**
- 🌐 Website: [sivasub.com](https://sivasub.com)
- 💼 LinkedIn: [linkedin.com/in/sivasub987](https://www.linkedin.com/in/sivasub987/)
- 🐙 GitHub: [github.com/siva-sub](https://github.com/siva-sub)
- 📧 Email: [hello@sivasub.com](mailto:hello@sivasub.com)
