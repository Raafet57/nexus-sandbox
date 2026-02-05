# Nexus Global Payments Sandbox

## Overview

This is an educational sandbox implementation of the Nexus Global Payments scheme - a cross-border instant payments platform. The project demonstrates expertise in:

- **Cross-border instant payments** architecture with a complete 17-step payment lifecycle
- **ISO 20022** message handling (pacs.008, pacs.002, camt.056, acmt.023/024, and 6 other message types)
- **Microservices** orchestration with Docker
- **Event-driven architecture** with Kafka
- **Distributed tracing** with Jaeger/OpenTelemetry

The sandbox simulates five actor types: PSP (Payment Service Provider), FXP (Foreign Exchange Provider), SAP (Settlement Access Provider), IPS (Instant Payment System), and PDO (Proxy Directory Operator).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend (Nexus Gateway)
- **Language**: Python 3.12 with FastAPI
- **Purpose**: Core payment orchestration, ISO 20022 message validation, FX quote aggregation
- **API Documentation**: Auto-generated OpenAPI at `/docs` (Swagger) and `/redoc`
- **Key Design Patterns**:
  - Event sourcing with CQRS for payment state management
  - Pluggable actor architecture - each actor type runs as an independent container
  - XSD validation for all ISO 20022 XML messages using lxml

### Frontend (Demo Dashboard)
- **Framework**: React with TypeScript
- **Purpose**: Interactive demo UI for sending payments, viewing actor dashboards, and inspecting ISO 20022 messages
- **Key Pages**: Send Payment wizard, PSP/FXP/SAP/IPS/PDO dashboards, Payments Explorer, Network Mesh visualization

### Database
- **PostgreSQL 16**: Primary data store for payments, quotes, actors, and event logs
- **Schema Design**: Event-sourced with `payment_events` table storing full message XML for forensic audit
- **Key Tables**: `payments`, `quotes`, `psps`, `countries`, `payment_events`

### Caching and Messaging
- **Redis 7**: Quote caching and session management
- **Apache Kafka 3.6+**: Async message delivery for actor callbacks

### Containerization
- **Docker Compose**: Full orchestration of all services
- **Lite Profile**: `docker-compose.lite.yml` for quick startup (~20 seconds)
- **Full Profile**: Includes Kafka and all actor simulators

### ISO 20022 Message Types Supported
The system handles 11 message types with XSD validation:
1. pacs.008 (Payment Instruction)
2. pacs.002 (Payment Status Report)
3. pacs.004 (Payment Return)
4. pacs.028 (Payment Status Request)
5. acmt.023 (Proxy Resolution Request)
6. acmt.024 (Proxy Resolution Report)
7. camt.054 (Reconciliation Report)
8. camt.056 (Recall Request)
9. camt.029 (Recall Response)
10. camt.103 (Create Reservation)
11. pain.001 (Payment Initiation)

### Key Architectural Decisions
- **Protocol Parity**: API parameters use camelCase to match official Nexus documentation exactly
- **Quote Snapshot Architecture**: All fees calculated once at quote creation to prevent calculation drift
- **Sandbox Mock Data**: When database queries return empty, realistic mock data is returned for demo purposes
- **Hybrid Callback Format**: ISO 20022 messages use XML, notifications use JSON

## External Dependencies

### Required Services (via Docker)
- **PostgreSQL 16**: Payment and event storage
- **Redis 7**: Quote caching
- **Apache Kafka 3.6+**: Async messaging (full profile only)
- **Jaeger**: Distributed tracing at port 16686

### Third-Party Integrations (Simulated)
- **Domestic IPS Systems**: FAST (Singapore), PromptPay (Thailand), DuitNow (Malaysia) - all simulated
- **FX Providers**: Mock FXP simulators with tiered rate improvements
- **Proxy Directory**: Mock PDO for mobile/email/QR proxy resolution

### Development Tools
- **Playwright**: E2E testing and screenshot capture
- **pytest**: Backend unit and integration tests

### Pre-Seeded Test Actors
| BIC | Type | Name |
|-----|------|------|
| DBSGSGSG | PSP | DBS Singapore |
| BKKBTHBK | PSP | Bangkok Bank |
| MAYBMYKL | PSP | Maybank Malaysia |
| NEXUSFXP1 | FXP | Nexus FXP Alpha |
| SGIPSOPS | IPS | Singapore FAST |
| THIPSOPS | IPS | Thailand PromptPay |