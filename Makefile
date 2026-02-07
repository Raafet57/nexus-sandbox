# Nexus Global Payments Sandbox - Developer Makefile
# ================================================
# Quick commands for local development and testing

.PHONY: help dev dev-lite test lint build clean down logs db-shell db-migrate audit

# Default target
help:
	@echo "Nexus Global Payments Sandbox - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev         - Start full stack (all simulators)"
	@echo "  make dev-lite    - Start lite stack (faster, ~20s)"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - Show logs from all services"
	@echo "  make rebuild     - Rebuild and start all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run backend tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make test-all    - Run all tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run linters on backend and frontend"
	@echo "  make format      - Format code with black and prettier"
	@echo ""
	@echo "Database:"
	@echo "  make db-shell    - Open PostgreSQL shell"
	@echo "  make db-migrate  - Run database migrations"
	@echo "  make db-seed     - Seed database with demo data"
	@echo "  make db-reset    - Reset database (WARNING: deletes data)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Stop and remove all containers, volumes, images"
	@echo "  make audit       - Run comprehensive audit (requires Python)"

# =============================================================================
# Development Commands
# =============================================================================

dev:
	docker compose -f docker-compose.yml up --build

dev-lite:
	docker compose -f docker-compose.lite.yml up --build

down:
	docker compose -f docker-compose.yml down
	docker compose -f docker-compose.lite.yml down

logs:
	docker compose -f docker-compose.yml logs -f --tail=100

rebuild: clean dev

# =============================================================================
# Testing Commands
# =============================================================================

test:
	cd services/nexus-gateway && python -m pytest tests/ -v

test-frontend:
	cd services/demo-dashboard && npm test

test-all: test test-frontend

# =============================================================================
# Code Quality Commands
# =============================================================================

lint:
	@echo "Running backend linter..."
	cd services/nexus-gateway && python -m flake8 src/ --max-line-length=120 || true
	@echo "Running frontend linter..."
	cd services/demo-dashboard && npm run lint || true

format:
	@echo "Formatting Python code..."
	cd services/nexus-gateway && python -m black src/ --line-length=120
	@echo "Formatting TypeScript code..."
	cd services/demo-dashboard && npx prettier --write 'src/**/*.{ts,tsx}'

# =============================================================================
# Database Commands
# =============================================================================

db-shell:
	docker compose exec postgres psql -U nexus -d nexus

db-migrate:
	docker compose exec nexus-gateway python -m alembic upgrade head

db-seed:
	docker compose exec postgres psql -U nexus -d nexus -f /docker-entrypoint-initdb.d/003_seed_data.sql

db-reset: down
	docker volume rm nexus-sandbox_postgres_data || true
	docker compose -f docker-compose.yml up -d postgres
	sleep 5
	make db-migrate
	make db-seed

# =============================================================================
# Utility Commands
# =============================================================================

clean:
	docker compose -f docker-compose.yml down -v --remove-orphans
	docker compose -f docker-compose.lite.yml down -v --remove-orphans
	docker system prune -f

audit:
	@echo "Running comprehensive audit..."
	@echo "This requires the audit agents to be set up."
	@python -c "import sys; print('Audit not configured in this environment')"

# =============================================================================
# CI/CD Support
# =============================================================================

ci: lint test-all

# =============================================================================
# Documentation
# =============================================================================

docs:
	@echo "Opening API documentation..."
	@echo "API docs available at: http://localhost:8000/docs"
	@echo "Dashboard available at: http://localhost:8080"
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000/docs 2>/dev/null || true; \
	fi

# =============================================================================
# Simulator Management
# =============================================================================

simulator-status:
	@echo "Checking simulator health..."
	@curl -s http://localhost:3001/health && echo " PSP-SG: OK" || echo " PSP-SG: DOWN"
	@curl -s http://localhost:3002/health && echo " IPS-SG: OK" || echo " IPS-SG: DOWN"
	@curl -s http://localhost:3003/health && echo " FXP: OK" || echo " FXP: DOWN"
	@curl -s http://localhost:3004/health && echo " SAP-SG: OK" || echo " SAP-SG: DOWN"
	@curl -s http://localhost:3401/health && echo " PDO-SG: OK" || echo " PDO-SG: DOWN"

# =============================================================================
# Quick Demo Commands
# =============================================================================

demo-payment:
	@echo "Sending demo payment..."
	@curl -X POST http://localhost:8000/v1/iso20022/pacs008?pacs002Endpoint=http://example.com/callback \
		-H "Content-Type: application/xml" \
		-d '<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.13">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>DEMO-001</MsgId>
      <CreDtTm>2025-01-01T00:00:00Z</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
    </GrpHdr>
    <CdtTrfTxInf>
      <PmtId>
        <EndToEndId>E2E-DEMO-001</EndToEndId>
      </PmtId>
      <IntrBkSttlmAmt Ccy="SGD">100.00</IntrBkSttlmAmt>
      <Dbtr>
        <Nm>Demo Sender</Nm>
      </Dbtr>
      <DbtrAcct>
        <Id>
          <Othr><Id>SG123456789</Id></Othr>
        </Id>
      </DbtrAcct>
      <Cdtr>
        <Nm>Demo Recipient</Nm>
      </Cdtr>
      <CdtrAcct>
        <Id>
          <Othr><Id>TH987654321</Id></Othr>
        </Id>
      </CdtrAcct>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>' || echo "Services not running. Start with 'make dev-lite'"

# =============================================================================
# Installation
# =============================================================================

install:
	@echo "Installing dependencies..."
	cd services/nexus-gateway && pip install -e .
	cd services/demo-dashboard && npm install

install-dev:
	@echo "Installing development dependencies..."
	cd services/nexus-gateway && pip install -e ".[dev]"
	cd services/demo-dashboard && npm install

# =============================================================================
# Docker Build
# =============================================================================

build:
	docker compose -f docker-compose.yml build

build-no-cache:
	docker compose -f docker-compose.yml build --no-cache

# =============================================================================
# Info
# =============================================================================

info:
	@echo "Nexus Global Payments Sandbox"
	@echo "================================"
	@echo "Services:"
	@echo "  - Nexus Gateway (API):  http://localhost:8000"
	@echo "  - Demo Dashboard:       http://localhost:8080"
	@echo "  - API Docs (Swagger):   http://localhost:8000/docs"
	@echo "  - Jaeger Tracing:      http://localhost:16686"
	@echo ""
	@echo "Simulators:"
	@echo "  - PSP-SG:  http://localhost:3001"
	@echo "  - IPS-SG:  http://localhost:3002"
	@echo "  - FXP:     http://localhost:3003"
	@echo "  - SAP-SG:  http://localhost:3004"
	@echo "  - PDO-SG:  http://localhost:3401"
	@echo ""
	@echo "Database:"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis:      localhost:6379"
