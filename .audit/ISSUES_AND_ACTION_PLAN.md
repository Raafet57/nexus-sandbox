# 🎯 Nexus Sandbox - Issues Tracker & Action Plan

**Generated:** 2026-02-07  
**Source:** Comprehensive Parity Audit

---

## 🔴 Critical Issues (P0 - Fix Immediately)

### Issue C1: Source PSP Fee Double Calculation
- **File:** `services/nexus-gateway/src/api/quotes.py`
- **Lines:** 326-327, 410
- **Severity:** 🔴 Critical
- **Impact:** Incorrect fee totals displayed to users

**Problem Description:**
The source PSP fee appears to be calculated in multiple places, potentially leading to double-counting in certain code paths.

**Code Evidence:**
```python
# In quotes.py around line 326-327
source_fee_amount = calculate_source_fee(...)
# ... later in the same function or in fees.py:410
source_fee_amount = calculate_source_fee(...)  # Double calculation?
```

**Recommended Fix:**
```python
# Consolidate fee calculation in a single function
# Use the existing invariant assertions in fees.py to verify
```

**Verification Steps:**
1. Add debug logging to trace fee calculation
2. Run fee calculation tests
3. Verify FeeCard displays correct totals

---

### Issue C2: Hardcoded JWT Secret
- **File:** `services/nexus-gateway/src/config.py`
- **Line:** 18
- **Severity:** 🔴 Critical (Security)
- **Impact:** Authentication bypass vulnerability

**Problem Description:**
JWT secret is hardcoded in the configuration file.

**Current Code:**
```python
JWT_SECRET: str = "demo-secret-key-change-in-production"  # Line 18
```

**Recommended Fix:**
```python
JWT_SECRET: str = Field(default_factory=lambda: os.urandom(32).hex())
# OR require environment variable
JWT_SECRET: str = Field(..., env="JWT_SECRET")  # Required in production
```

---

### Issue C3: Hardcoded Callback Shared Secret
- **File:** `services/nexus-gateway/src/api/callbacks.py`
- **Line:** 24
- **Severity:** 🔴 Critical (Security)
- **Impact:** Callback spoofing vulnerability

**Problem Description:**
All callbacks use the same hardcoded shared secret.

**Current Code:**
```python
DEFAULT_SHARED_SECRET: str = "nexus-sandbox-shared-secret-2024"
```

**Recommended Fix:**
```python
# Generate per-actor secret during registration
# Store in database alongside actor record
# Use actor-specific secret for HMAC signing
```

---

## 🟡 Medium Issues (P1 - Fix Soon)

### Issue M1: In-Memory Actor Registry
- **File:** `services/nexus-gateway/src/api/actors.py`
- **Severity:** 🟡 Medium
- **Impact:** Actor data lost on service restart

**Problem Description:**
Actor registry uses an in-memory dictionary that doesn't persist across restarts.

**Current Implementation:**
```python
_actor_registry: dict[str, dict] = {}
```

**Recommended Fix:**
```python
# Create actors table in PostgreSQL
# Migrate registry to use database
# Add caching layer with Redis for performance
```

---

### Issue M2: No Webhook Persistence
- **File:** `services/nexus-gateway/src/api/callbacks.py`
- **Severity:** 🟡 Medium
- **Impact:** Failed callbacks are lost

**Problem Description:**
Callbacks are fire-and-forget with no persistence for failed deliveries.

**Current Implementation:**
```python
# Direct HTTP call, no queue
response = await client.post(callback_url, ...)
```

**Recommended Fix:**
```python
# Implement callback queue table
# Store failed callbacks for retry
# Implement dead letter queue (DLQ) after max retries
```

---

### Issue M3: Missing Simulator Health Checks
- **Files:** All simulator services
- **Severity:** 🟡 Medium
- **Impact:** Docker compose health checks fail for simulators

**Problem Description:**
Simulator services don't expose `/health` endpoints.

**Recommended Fix:**
```javascript
// Add to each simulator's index.js
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'psp-sg' });
});
```

---

### Issue M4: Docker Compose Indentation
- **File:** `docker-compose.yml`
- **Line:** 532-534
- **Severity:** 🟡 Medium
- **Impact:** YAML formatting issue

**Problem Description:**
Incorrect indentation in volumes/networks section.

---

## 🟢 Low Issues (P2 - Nice to Have)

### Issue L1: No Makefile
- **Severity:** 🟢 Low
- **Impact:** Developer experience

**Recommended Addition:**
```makefile
.PHONY: dev test lint build clean

dev:
	docker-compose -f docker-compose.lite.yml up

test:
	cd services/nexus-gateway && pytest -v

lint:
	cd services/nexus-gateway && flake8 src
	cd services/demo-dashboard && npm run lint

build:
	docker-compose build

clean:
	docker-compose down -v
```

---

### Issue L2: License Mismatch
- **Files:** `LICENSE`, `package.json`
- **Severity:** 🟢 Low
- **Impact:** Legal clarity

**Problem:** LICENSE file is MIT but package.json says ISC.

**Fix:** Align both to MIT.

---

### Issue L3: No Pre-commit Hooks
- **Severity:** 🟢 Low
- **Impact:** Code quality

**Recommended Addition:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
```

---

## 📋 Implementation Priority Matrix

| Issue | Effort | Impact | Priority | Owner |
|-------|--------|--------|----------|-------|
| C1 - Fee Double Calc | Low | High | P0 | Backend |
| C2 - JWT Secret | Low | High | P0 | Security |
| C3 - Callback Secret | Medium | High | P0 | Security |
| M1 - Actor Registry | High | Medium | P1 | Backend |
| M2 - Webhook Persistence | Medium | Medium | P1 | Backend |
| M3 - Health Checks | Low | Medium | P1 | DevOps |
| M4 - Docker Indent | Low | Low | P1 | DevOps |
| L1 - Makefile | Low | Low | P2 | DevEx |
| L2 - License | Low | Low | P2 | Legal |
| L3 - Pre-commit | Low | Low | P2 | DevEx |

---

## 🗓️ Suggested Timeline

### Week 1: Critical Fixes
- [ ] Fix C1: Fee double calculation
- [ ] Fix C2: JWT secret hardcoding
- [ ] Fix C3: Callback secret hardcoding
- [ ] Run full test suite
- [ ] Verify fixes with integration tests

### Week 2: Medium Priority
- [ ] Fix M3: Simulator health checks
- [ ] Fix M4: Docker compose indentation
- [ ] Address M1: Begin actor registry migration (if time permits)

### Week 3-4: Persistence Layer
- [ ] Complete M1: Actor registry database migration
- [ ] Address M2: Webhook persistence implementation

### Month 2: Polish
- [ ] Address L1-L3: Developer experience improvements
- [ ] Add comprehensive integration tests
- [ ] Performance optimization

---

## ✅ Verification Checklist

### After Critical Fixes
- [ ] Fee calculation produces correct totals
- [ ] JWT secret loaded from environment
- [ ] Callback secret unique per actor
- [ ] All tests pass
- [ ] Integration tests pass

### After Medium Fixes
- [ ] Actor data persists across restarts
- [ ] Failed callbacks are retried
- [ ] All services report healthy in Docker
- [ ] Docker compose starts without errors

### Before Production
- [ ] Security audit completed
- [ ] Load testing passed
- [ ] Documentation updated
- [ ] Runbook created
- [ ] Monitoring configured

---

**End of Issues Tracker & Action Plan**
