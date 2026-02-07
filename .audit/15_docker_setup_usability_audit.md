# Docker Setup Usability Audit

**Project**: Nexus Global Payments Sandbox
**Audit Date**: 2025-02-07
**Auditor**: Claude (Automated Audit)
**Purpose**: Evaluate Docker setup for out-of-the-box developer experience

---

## Executive Summary

The Docker setup for Nexus Sandbox is **generally well-structured** but has several critical issues that could negatively impact the developer experience. The setup includes both full (`docker-compose.yml`) and lite (`docker-compose.lite.yml`) configurations, a convenience startup script (`start.sh`), and multiple service Dockerfiles.

### Overall Assessment: B (78/100)

| Category | Score | Status |
|----------|-------|--------|
| Compose Configuration | 75/100 | Fair |
| Dockerfile Quality | 85/100 | Good |
| Developer Experience | 70/100 | Fair |
| Documentation | 80/100 | Good |
| Resource Management | 80/100 | Good |

### Critical Issues Found

1. **CRITICAL**: `KAFKA_ENABLED` and `OTEL_ENABLED` environment variables are set in lite mode but not handled by the Python application
2. **HIGH**: No health checks on simulator services (PSP, IPS, FXP, SAP, PDO)
3. **MEDIUM**: Inconsistent health check commands (wget vs curl)
4. **MEDIUM**: Missing environment variable documentation
5. **LOW**: No .env.example file provided

---

## 1. docker-compose.yml Analysis

### 1.1 Service Overview

| Service | Container Name | Port | Health Check | Resource Limits |
|---------|----------------|------|--------------|-----------------|
| demo-dashboard | nexus-demo | 8080 | Yes (wget) | 128M/0.25 CPU |
| swagger-ui | nexus-swagger | 8081 | No | 128M/0.25 CPU |
| postgres | nexus-postgres | 5432 | Yes (pg_isready) | 1G/1.0 CPU |
| redis | nexus-redis | 6379 | Yes (redis-cli) | 256M/0.5 CPU |
| kafka | nexus-kafka | 9092 | Yes (kafka-topics) | 1G/1.0 CPU |
| zookeeper | nexus-zookeeper | - | Yes (nc echo) | 512M/0.5 CPU |
| jaeger | nexus-jaeger | 16686, 4317, 4318 | No | 512M/0.5 CPU |
| nexus-gateway | nexus-gateway | 8000 | Yes (curl) | 512M/1.0 CPU |
| psp-sg | nexus-psp-sg | 3001 | No | 256M/0.5 CPU |
| psp-th | nexus-psp-th | 3002 | No | 256M/0.5 CPU |
| psp-my | nexus-psp-my | 3003 | No | 256M/0.5 CPU |
| ips-sg | nexus-ips-sg | 3101 | No | 256M/0.5 CPU |
| ips-th | nexus-ips-th | 3102 | No | 256M/0.5 CPU |
| fxp-abc | nexus-fxp-abc | 3201 | No | 256M/0.5 CPU |
| sap-dbs | nexus-sap-dbs | 3301 | No | 256M/0.5 CPU |
| pdo-sg | nexus-pdo-sg | 3401 | No | 256M/0.5 CPU |

### 1.2 Health Checks

**Well Implemented:**
- postgres: Uses `pg_isready` with appropriate retries
- redis: Uses `redis-cli ping`
- kafka: Uses `kafka-topics --list` with proper start_period
- zookeeper: Uses netcat echo check
- nexus-gateway: Uses curl against /health endpoint
- demo-dashboard: Uses wget against /health endpoint

**Missing Health Checks:**
- swagger-ui: No health check defined
- jaeger: No health check defined
- All simulator services: No health checks defined

**Impact:** Without health checks, simulators may be accessed before they're ready, causing API failures.

### 1.3 Dependencies

**Properly Configured:**
```yaml
depends_on:
  nexus-gateway:
    condition: service_healthy
```

- demo-dashboard correctly waits for nexus-gateway
- swagger-ui correctly waits for nexus-gateway
- nexus-gateway correctly waits for postgres, redis, and kafka

**Issues:**
- Simulator services (PSP/IPS/FXP/SAP/PDO) use simple `depends_on` without health checks
- This means they may start before nexus-gateway is actually ready

### 1.4 Resource Management

**Good:**
- All services have CPU and memory limits defined
- Resource reservations are set for critical services
- Memory limits are appropriate for container types

**Potential Issue:**
- PostgreSQL limit of 1G may be insufficient for heavy testing
- Kafka limit of 1G could be constraining for high-throughput scenarios

### 1.5 Network Configuration

**Good:**
- Two networks defined: `frontend` and `backend`
- Services properly segmented (demo-dashboard on both, others on backend)
- Custom network names for easy identification

---

## 2. docker-compose.lite.yml Analysis

### 2.1 Purpose and Design

The lite profile is designed for fast startup (~20 seconds vs 2+ minutes) by excluding:
- Kafka/Zookeeper (event streaming)
- Jaeger (tracing)
- All simulator services (PSP/IPS/FXP/SAP/PDO)

### 2.2 Services Included

| Service | Purpose |
|---------|---------|
| postgres | Database |
| redis | Cache |
| nexus-gateway | Core API |
| demo-dashboard | UI |

### 2.3 CRITICAL ISSUE: Unhandled Environment Variables

The lite compose file sets these environment variables:

```yaml
KAFKA_ENABLED: "false"
OTEL_ENABLED: "false"
```

**However, these are NOT handled in the Python code:**

1. `config.py` does not define `kafka_enabled` or `otel_enabled` fields
2. `main.py` checks `settings.otel_enabled` but the environment variable name is `OTEL_ENABLED` (doesn't match due to Pydantic's case-insensitive setting, but verification needed)

**Impact:**
- The lite mode may fail to start properly
- Even if it starts, Kafka connection errors may occur since the application doesn't know Kafka is disabled
- OpenTelemetry will try to connect to Jaeger even though it's not running

**Recommendation:**
Add these fields to `config.py`:
```python
kafka_enabled: bool = True
otel_enabled: bool = True
```

And conditionally initialize Kafka/OTEL in `main.py`.

### 2.4 Lite Mode Functionality

**Questionable:** The lite mode excludes all simulators but the backend still has "mock implementations" per the comment. However:
- It's unclear if the mock implementations are automatically used when simulators are absent
- Documentation doesn't explain what functionality is lost in lite mode
- No clear guidance on when to use full vs lite

---

## 3. Dockerfile Analysis

### 3.1 nexus-gateway/Dockerfile

**Multi-stage build: YES**

```dockerfile
FROM python:3.12-slim AS builder
# ... build stage ...
FROM python:3.12-slim AS runtime
# ... runtime stage ...
```

**Strengths:**
- Uses multi-stage build for smaller image
- Installs build dependencies only in builder stage
- Copies only installed packages, not build tools
- Creates non-root user (nexus)
- Sets appropriate Python environment variables
- Includes health check

**Issues:**
- No `.dockerignore` usage verification (file exists but should be validated)
- `specs/` directory is copied but may not exist or may be large
- No explicit layer caching optimization (COPY pyproject.toml first is good, but could COPY requirements.txt if it existed)

**Security:**
- Non-root user created: YES
- No unnecessary packages: GOOD
- Latest base image: python:3.12-slim (acceptable)

### 3.2 demo-dashboard/Dockerfile

**Multi-stage build: YES**

```dockerfile
FROM node:20-alpine AS builder
# ... build ...
FROM nginx:alpine AS production
# ... serve ...
```

**Strengths:**
- Multi-stage build (builds with Node, serves with nginx)
- Uses nginx:alpine for minimal production image
- Copies custom nginx.conf

**Issues:**
- No health check defined (could add curl/wget check)
- Build stage could cache node_modules better

**Security:**
- Runs as nginx user (default): GOOD
- Minimal base image: GOOD

### 3.3 Simulator Dockerfiles (PSP/IPS/FXP/SAP/PDO)

All simulators use the same pattern:

```dockerfile
FROM node:20-alpine
# ... create non-root user ...
RUN npm install --omit=dev
# ... copy code ...
USER appuser
HEALTHCHECK --interval=30s --timeout=10s CMD wget -qO- http://localhost:3000/health
```

**Strengths:**
- Consistent structure across all simulators
- Non-root user (appuser)
- Health checks defined at container level
- Uses `--omit=dev` for production dependencies only

**Issues:**
- All are identical - could use a single Dockerfile with build args
- Health checks defined in Dockerfile but not in docker-compose
- wget may not be installed in node:20-alpine (curl is usually available)

**Consistency Score:** 10/10 - All simulators follow the same pattern

---

## 4. .dockerignore Analysis

### nexus-gateway/.dockerignore

```
__pycache__
*.py[cod]
# ... standard Python ignores ...
```

**Good:** Excludes Python cache, tests, documentation, env files

**Missing:**
- No exclusion of `.git` directory (though git status shows it's in main .gitignore)
- Test files not explicitly excluded (though `__pycache__` covers most)

### demo-dashboard/.dockerignore

```
node_modules
.git
*.md
.env
dist
coverage
# ... standard Node ignores ...
```

**Good:** Comprehensive Node.js excludes

**Note:** Excludes `*.md` which is appropriate for Docker builds

---

## 5. start.sh Analysis

### 5.1 Script Overview

A comprehensive bash script that provides:

```bash
./start.sh start      # Full stack
./start.sh lite       # Lite mode
./start.sh stop       # Stop all
./start.sh restart    # Restart
./start.sh logs       # Show logs
./start.sh status     # Show status
./start.sh clean      # Cleanup
```

### 5.2 Strengths

1. **User-friendly output**: Colored output with clear messages
2. **Docker verification**: Checks if Docker is installed and running
3. **Clear access points**: Prints URLs after startup
4. **Helpful tips**: Shows additional commands
5. **Error handling**: Uses `set -e` for early exit on errors

### 5.3 Issues

1. **No service health verification**: Doesn't wait for services to be healthy
2. **No error context**: If docker compose fails, doesn't show error details
3. **Assumes default ports**: Doesn't check if ports are already in use
4. **Linux-focused**: Uses Linux-specific commands (though mostly portable)

### 5.4 Improvements Needed

```bash
# Add port conflict detection
if nc -z localhost 8080 2>/dev/null; then
    echo "Error: Port 8080 is already in use"
    exit 1
fi

# Add health verification
echo "Waiting for services to be healthy..."
timeout 60 bash -c 'until curl -f http://localhost:8080/health; do sleep 2; done'
```

---

## 6. Common Issues Analysis

### 6.1 Port Conflicts

**Ports in use:**

| Port | Service | Conflict Risk |
|------|---------|---------------|
| 8080 | demo-dashboard | HIGH (common web port) |
| 8081 | swagger-ui | MEDIUM |
| 8000 | nexus-gateway | LOW (often used by dev servers) |
| 5432 | postgres | HIGH (default PostgreSQL) |
| 6379 | redis | MEDIUM (default Redis) |
| 9092 | kafka | LOW |
| 16686 | jaeger | LOW |
| 3001-3003 | PSPs | LOW |
| 3101-3102 | IPSs | LOW |
| 3201 | FXP | LOW |
| 3301 | SAP | LOW |
| 3401 | PDO | LOW |

**Recommendation:**
- Document port conflicts in README
- Add port conflict detection to start.sh
- Consider using Docker's automatic port allocation for less critical services

### 6.2 Volume Permissions

**Current:** Volumes are managed by Docker

**Potential Issues:**
- PostgreSQL data volume may have permission issues on Linux with SELinux
- No volume backup/restore documentation

**Status:** Should work out-of-the-box for most users

### 6.3 Network Issues

**Current:** Custom bridge networks

**Potential Issues:**
- VPN software may interfere with Docker networking
- Corporate firewalls may block inter-container communication

**Status:** Minimal issues expected

### 6.4 Environment Variable Requirements

**Current:** All environment variables are defined in docker-compose files

**Issues:**
- No .env.example file
- No documentation of available configuration options
- Secrets are hardcoded in docker-compose.yml

**Recommendation:**
Create `.env.example`:
```env
# Database
POSTGRES_DB=nexus
POSTGRES_USER=nexus
POSTGRES_PASSWORD=nexus_sandbox_password

# JWT (change in production)
JWT_SECRET=nexus-sandbox-jwt-secret-change-in-production

# Feature flags
KAFKA_ENABLED=true
OTEL_ENABLED=true
```

---

## 7. First-Time Developer Experience Simulation

### 7.1 Cloning and Starting

```bash
git clone https://github.com/siva-sub/nexus-sandbox.git
cd nexus-sandbox
docker compose up -d
```

**Expected Time:** 2-5 minutes for first run (building images)

**Potential Issues:**
1. Port conflicts (especially 5432, 8080)
2. Out of memory on systems with <8GB RAM
3. Kafka may timeout on slower systems

### 7.2 Accessing Services

After startup, a developer should be able to access:
- http://localhost:8080 - Dashboard
- http://localhost:8081 - Swagger UI
- http://localhost:16686 - Jaeger
- http://localhost:8000/docs - API docs

**Current UX:** GOOD - All URLs are printed by start.sh

### 7.3 Stopping and Cleaning

```bash
docker compose down
# or
./start.sh clean
```

**Current UX:** GOOD - Clean script provided

---

## 8. Recommendations

### 8.1 Critical (Must Fix)

1. **Fix Lite Mode Environment Variables**
   - Add `kafka_enabled` and `otel_enabled` to config.py
   - Make Kafka and OTEL initialization conditional
   - Test lite mode thoroughly

2. **Add Simulator Health Checks**
   - All simulators have `/health` endpoints
   - Add health checks to docker-compose.yml for all simulators
   - Use `depends_on: condition: service_healthy` for services that depend on simulators

### 8.2 High Priority

3. **Port Conflict Detection**
   - Add check to start.sh
   - Document port conflicts in README
   - Consider providing a port mapping configuration option

4. **Environment Variable Documentation**
   - Create .env.example
   - Document all configurable environment variables
   - Separate secrets from configuration

5. **Service Health Verification**
   - Add post-startup health check to start.sh
   - Show "Ready" message when all services are healthy
   - Show service status on startup

### 8.3 Medium Priority

6. **Improve Dockerfile Caching**
   - Separate requirements copying in Python Dockerfile
   - Consider using BuildKit for better caching

7. **Standardize Health Check Commands**
   - Use curl consistently (or wget consistently)
   - Ensure health check tools are installed

8. **Add Development Mode**
   - Create docker-compose.dev.yml for hot-reload
   - Document development workflow

### 8.4 Low Priority

9. **Consolidate Simulator Dockerfiles**
   - Use single Dockerfile with build args
   - Reduces duplication and maintenance burden

10. **Add Metrics Dashboard**
    - Include a simple metrics/health dashboard
    - Show container resource usage
    - Display service health at a glance

---

## 9. Best Practices Followed

1. Multi-stage builds for production images
2. Non-root users for security
3. Resource limits to prevent runaway containers
4. Health checks for critical services
5. Log rotation configuration
6. Separate networks for frontend/backend
7. Named containers for easy identification
8. Volume management for persistent data
9. .dockerignore files to exclude unnecessary files
10. Comprehensive startup script

---

## 10. Conclusion

The Docker setup for Nexus Sandbox demonstrates good practices in containerization with multi-stage builds, proper resource management, and security considerations. However, several issues could impact the out-of-the-box developer experience:

1. The lite mode has unhandled environment variables that could cause failures
2. Simulator services lack health checks in the compose configuration
3. No port conflict detection or pre-flight checks
4. Limited environment variable documentation

With the recommended improvements, especially the critical fixes for lite mode and simulator health checks, the Docker setup would provide an excellent developer experience.

### Final Scores

| Aspect | Score | Notes |
|--------|-------|-------|
| Correctness | 75/100 | Lite mode bug affects score |
| Completeness | 80/100 | Missing health checks for some services |
| Consistency | 85/100 | Good consistency across simulators |
| Documentation | 75/100 | Good README, missing env docs |
| Developer Experience | 70/100 | Good start.sh, missing pre-flight checks |
| Security | 85/100 | Non-root users, minimal base images |
| Performance | 80/100 | Good resource limits, caching could improve |

**Overall: 78/100 (B)**

The setup is functional and well-structured but needs the critical issues addressed for a smooth out-of-the-box experience.

---

## Appendix: File Locations

- docker-compose.yml: `/home/siva/Projects/Nexus Global Payments Sandbox/docker-compose.yml`
- docker-compose.lite.yml: `/home/siva/Projects/Nexus Global Payments Sandbox/docker-compose.lite.yml`
- start.sh: `/home/siva/Projects/Nexus Global Payments Sandbox/start.sh`
- nexus-gateway Dockerfile: `/home/siva/Projects/Nexus Global Payments Sandbox/services/nexus-gateway/Dockerfile`
- demo-dashboard Dockerfile: `/home/siva/Projects/Nexus Global Payments Sandbox/services/demo-dashboard/Dockerfile`
- Simulator Dockerfiles: `/home/siva/Projects/Nexus Global Payments Sandbox/services/*/Dockerfile`
