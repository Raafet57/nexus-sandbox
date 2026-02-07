# Troubleshooting Guide

Common issues and solutions for the Nexus Global Payments Sandbox.

---

## Docker Startup

### Containers fail to start

```bash
# Clean rebuild
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

Check all healthy:
```bash
docker compose ps
```

### Port conflicts

Default ports: `8080` (frontend), `8000` (backend), `5432` (PostgreSQL), `6379` (Redis).

```bash
# Check for conflicts
lsof -i :8080
lsof -i :8000
```

---

## API Errors

### 500 on `/v1/quotes` — "No FX rates found"

FX rates are seeded with relative dates and expire after 30 days. If rates seem expired:

```bash
# Re-run seed script
docker compose exec nexus-gateway python -m scripts.seed_data
```

### 404 on `/v1/addressing/resolve` — Proxy not found

The proxy resolution uses mock data. Ensure the proxy value matches known test numbers:
- Singapore: `+6591234567`
- Indonesia: `+6281234567890`
- Thailand: `+66812345678`

### 410 on `/v1/fees/sender-confirmation` — Quote expired

Quotes have a 10-minute expiry. If you see `410 Gone`, the quote expired between selection and confirmation. Re-fetch quotes from `/v1/quotes`.

---

## Frontend Issues

### "Address Type error" on dashboard

This usually indicates the backend cannot reach its database or FX rates are expired. Check:

```bash
docker compose logs nexus-gateway | tail -20
```

### Frontend not loading / blank screen

Check the frontend container:
```bash
docker compose logs demo-dashboard | tail -20
```

Ensure the `VITE_API_BASE_URL` environment variable is set correctly in `docker-compose.yml`.

### Quote expiry countdown shows "Expired"

Quotes expire 10 minutes after creation. Click "Search & Get Quotes" again to fetch fresh quotes.

---

## Database Issues

### Connection refused to PostgreSQL

```bash
# Check PostgreSQL is running
docker compose ps nexus-db

# View logs
docker compose logs nexus-db

# Manual connection test
docker compose exec nexus-db psql -U nexus -d nexus_sandbox -c "SELECT 1"
```

### Missing tables

Tables are created from `migrations/` on first startup. Force recreation:

```bash
docker compose down -v  # WARNING: destroys data
docker compose up -d
```

---

## Health Check Failures

All services expose health endpoints:

| Service | Endpoint |
|---------|----------|
| nexus-gateway | `GET /health` |
| demo-dashboard | `GET /` (serves SPA) |
| nexus-db | `pg_isready` |

```bash
# Quick health check
curl http://localhost:8000/health
curl http://localhost:8080/
```

---

## Performance

### Slow payment processing

The sandbox simulates realistic async processing with configurable delays. The callback timeout is configurable:

```bash
# In .env or docker-compose.yml
NEXUS_CALLBACK_TIMEOUT_SECONDS=10  # Default: 10 seconds
```

---

## Getting Help

1. Check the [API Reference](API_REFERENCE.md)
2. Review the [CHANGELOG](../CHANGELOG.md) for recent fixes
3. Open an issue on GitHub with container logs attached
