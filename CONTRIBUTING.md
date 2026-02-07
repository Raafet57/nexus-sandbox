# Contributing to Nexus Sandbox

Thank you for your interest in contributing to the Nexus Global Payments Sandbox!

## 🚀 Getting Started

### Prerequisites

- **Docker Desktop** 4.0+ or Docker Engine 20.10+
- **Python** 3.11+ (for local backend development)
- **Node.js** 20+ (for local frontend development)
- **Git** for version control

### Quick Start with Docker (Recommended)

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/nexus-sandbox.git
   cd nexus-sandbox
   ```
3. **Start** the services:
   ```bash
   # Lite mode (faster, ~20 seconds)
   docker compose -f docker-compose.lite.yml up -d

   # Full stack (all simulators, ~2 minutes)
   docker compose up -d
   ```
4. **Access** the dashboard at http://localhost:8080

---

## 🖥️ Local Development Setup

### Backend Development (FastAPI)

**Without Docker:**

```bash
# 1. Install dependencies
cd services/nexus-gateway
pip install -e .

# 2. Set up environment variables
export DATABASE_URL="postgresql://nexus:nexus_sandbox_password@localhost:5432/nexus"
export REDIS_URL="redis://localhost:6379/0"

# 3. Run migrations (if needed)
# Assuming PostgreSQL is running locally

# 4. Start the server
uvicorn src.main:app --reload --port 8000
```

**With Docker (Hot Reload):**

```bash
# Build and run with volume mount for code changes
docker compose -f docker-compose.yml up --build nexus-gateway
```

### Frontend Development (React + Vite)

```bash
# 1. Install dependencies
cd services/demo-dashboard
npm install

# 2. Start development server
npm run dev

# 3. Access at http://localhost:5173
```

**API Proxy Configuration:**

The frontend uses Vite's proxy to forward API requests to the backend. See `vite.config.ts` for configuration.

### Running Tests

```bash
# Backend tests
cd services/nexus-gateway
pytest --cov=src --cov-report=html
pytest tests/test_quotes.py -v  # Specific test

# Frontend tests
cd services/demo-dashboard
npm run test
```

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Demo Dashboard                        │
│                    (React + Vite + Mantine)                   │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────┐
│                      Nexus Gateway (FastAPI)                  │
│                     • ISO 20022 Validation                   │
│                     • Quote Aggregation                     │
│                     • Payment Routing                      │
│                     • Event Sourcing                       │
└───┬────────────────┬───────────┬────────────────┬──────────┬──┘
    │                │           │                │          │
┌───▼────┐   ┌─────▼──────┐   ┌───▼────┐   ┌─────▼────┐   ┌───▼─────┐
│ PSP   │   │ IPS       │   │ FXP   │   │ SAP     │   │ PDO     │
│ Sim   │   │ Sim       │   │ Sim   │   │ Sim     │   │ Sim     │
└───────┘   └───────────┘   └────────┘   └─────────┘   └─────────┘
```

### Data Flow (17-Step Payment Lifecycle)

1. **Setup** (Steps 1-2): Country/currency selection
2. **Quotes** (Steps 3-6): FX rate aggregation and quote locking
3. **Addressing** (Steps 7-9): Proxy resolution via acmt.023/024
4. **Compliance** (Steps 10-11): Sanctions screening
5. **Approval** (Step 12): Sender confirmation
6. **Execution** (Steps 13-16): pacs.008 routing and settlement
7. **Confirmation** (Step 17): pacs.002 status report

**Reference**: [docs/architecture/C4_ARCHITECTURE.md](./docs/architecture/C4_ARCHITECTURE.md)

---

## 📋 Development Guidelines

### Code Style

- **Python**: Follow PEP 8, use type hints, add docstrings
- **TypeScript**: Use strict mode, follow ESLint rules
- **Commits**: Use [Conventional Commits](https://conventionalcommits.org/)

```
feat: add new endpoint for quote locking
fix: correct pacs.008 XML parsing
docs: update API reference
test: add unit tests for FXP rates
refactor: improve quote aggregation logic
chore: update dependencies
```

### Branch Naming

- `feature/short-description` - New features
- `fix/issue-number-description` - Bug fixes
- `docs/what-changed` - Documentation only
- `refactor/component-name` - Code refactoring

### Project Structure

```
nexus-sandbox/
├── services/
│   ├── nexus-gateway/      # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/          # API endpoints
│   │   │   ├── models/       # Database models
│   │   │   └── config.py     # Configuration
│   ├── demo-dashboard/      # React frontend
│   │   ├── src/
│   │   │   ├── pages/        # Page components
│   │   │   ├── services/     # API client
│   │   │   └── types/        # TypeScript types
│   └── *-simulator/          # Simulators (PSP, IPS, FXP, SAP, PDO)
├── docs/                    # Documentation
├── migrations/              # Database migrations
└── docker-compose.yml       # Service orchestration
```

---

## 🧪 Testing Guidelines

### Unit Tests

```bash
# Backend
cd services/nexus-gateway
pytest tests/unit/ -v
pytest --cov=src --cov-report=html

# Frontend
cd services/demo-dashboard
npm run test
```

### Integration Tests

```bash
# Start all services
docker compose up -d

# Run integration test suite
docker compose exec nexus-gateway pytest tests/integration/
```

### Manual Testing Checklist

- [ ] Complete SG → TH payment (happy flow)
- [ ] Test unhappy flow with trigger values
- [ ] Verify all ISO 20022 messages are valid
- [ ] Check health endpoints return 200
- [ ] Test simulator callback delivery

---

## 📝 Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the code style guidelines
3. **Write tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** and ensure they pass
6. **Commit** with conventional commit messages
7. **Push** to your fork
8. **Create Pull Request** with:
   - Clear title and description
   - Link to related issues
   - Screenshots for UI changes
   - List of files modified

### PR Review Criteria

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

---

## 🔍 Common Development Tasks

### Adding a New Endpoint

1. Define the route in `services/nexus-gateway/src/api/`
2. Add Pydantic schemas in `services/nexus-gateway/src/api/schemas.py`
3. Update `API_REFERENCE.md` with documentation
4. Add tests in `services/nexus-gateway/tests/`

### Adding a New Simulator

1. Create directory in `services/`
2. Implement `/health` endpoint
3. Implement business logic endpoints
4. Add to `docker-compose.yml`
5. Document in README

### Adding a New Country

1. Add country data to `migrations/003_seed_data.sql`
2. Define address types in `migrations/004_fxp_sap_tables.sql`
3. Add PSP, IPS, SAP, PDO entries
4. Add FX rates
5. Update frontend types if needed

---

## 📚 Resources

- [Official Nexus Documentation](https://docs.nexusglobalpayments.org/)
- [ISO 20022 Message Catalogue](https://www.iso20022.org/)
- [Project ADRs](./docs/adr/) - Architecture Decision Records
- [Message Examples](./docs/MESSAGE_EXAMPLES.md)
- [Integration Guide](./docs/INTEGRATION_GUIDE.md)

---

## 🆘 Getting Help

- **Issues**: Use [GitHub Issues](https://github.com/siva-sub/nexus-sandbox/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/siva-sub/nexus-sandbox/discussions)
- **Email**: hello@sivasub.com

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Created by [Siva Subramanian](https://linkedin.com/in/sivasub987)
