# Nexus Sandbox Usage Guide

> **Quick Start**: Get started with cross-border payments simulation in under 5 minutes.

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.x | `docker compose version` |
| Memory | 4GB+ | Available RAM |

---

## 🚀 Getting Started

### 1. Start the Sandbox

```bash
# Clone and start
git clone https://github.com/siva-sub/nexus-sandbox.git
cd nexus-sandbox
./start.sh
```

Or manually:
```bash
docker compose up -d
```

Wait for health checks (~30 seconds):
```bash
docker compose ps
# All services should show "healthy"
```

### 2. Access the Dashboard

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8080 | Main UI |
| **API Docs** | http://localhost:8080/api/docs | Swagger UI |
| **ReDoc** | http://localhost:8080/api/redoc | Alternative docs |
| **Jaeger** | http://localhost:16686 | Distributed tracing |

**Status Check**: Look for 🟢 "Gateway: connected" in the sidebar.

---

## 💸 Your First Payment

### Step 1: Select Destination

1. Open http://localhost:8080
2. Go to **Send Payment** (first item in sidebar)
3. Choose **Singapore → Thailand** corridor

### Step 2: Get FX Quote

1. Enter amount: **1,000 SGD**
2. Click **Get Quote**
3. Compare quotes from multiple FXPs
4. Select the best rate

### Step 3: Resolve Recipient

1. Select **Mobile Number** (MBNO)
2. Enter: `+66812345678`
3. Click **Resolve Proxy**
4. Verify beneficiary: "Somchai Thai"

### Step 4: Confirm & Send

1. Review Pre-Transaction Disclosure (PTD)
2. Click **Confirm & Send**
3. Watch the 17-step lifecycle complete

### Step 5: Explore Results

| Tab | What to See |
|-----|-------------|
| **Overview** | Transaction status, amount, participants |
| **Lifecycle** | 17-step timeline with step indicators |
| **Messages** | Raw pacs.008 and pacs.002 XML |
| **Debug** | API commands and gateway context |

---

## 🔴 Error Scenarios

Test edge cases with these trigger values:

| Scenario | Trigger Value | Error Code | Description |
|----------|---------------|------------|-------------|
| **Proxy Not Found** | `+66999999999` | `BE23` | Account/Proxy Invalid |
| **Quote Expired** | Wait 10+ minutes | `AB04` | Quote validity exceeded |
| **Amount Too High** | `> 50,000` | `VAL01` | Maximum limit exceeded |
| **Invalid SAP** | (Internal) | `RC11` | Invalid Intermediary Agent |

---

## 🔍 Exploring Further

### Actor Dashboards

Each actor type has a dedicated view:

| Dashboard | Route | Purpose |
|-----------|-------|---------|
| PSP Dashboard | `/psp` | Source/Destination banks |
| FXP Rates | `/fxp` | FX rate management |
| SAP Liquidity | `/sap` | Settlement accounts |
| IPS Dashboard | `/ips` | Payment system operators |
| PDO Dashboard | `/pdo` | Proxy directory |

### Developer Tools

| Tool | Route | Description |
|------|-------|-------------|
| Payments Explorer | `/explorer` | UETR lookup, lifecycle, XML |
| Messages | `/messages` | Browse all ISO 20022 messages |
| Network Mesh | `/mesh` | Actor interconnection map |

---

## 📚 Next Steps

- **[Dashboard Guide](./DASHBOARD_GUIDE.md)** - Detailed UI reference
- **[Integration Guide](./INTEGRATION_GUIDE.md)** - Connect your system
- **[E2E Demo Script](./E2E_DEMO_SCRIPT.md)** - Live demonstration
- **[API Reference](./api/API_REFERENCE.md)** - Endpoint documentation

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard not loading | Check `docker compose ps` - wait for healthy |
| "Gateway: disconnected" | Restart: `docker compose restart nexus-gateway` |
| Quote returning empty | Check FXP service: `docker compose logs fxp-simulator` |
| Proxy not resolving | Verify PDO service: `docker compose logs pdo-simulator` |

### Useful Commands

```bash
# View logs
docker compose logs -f nexus-gateway

# Restart specific service
docker compose restart demo-dashboard

# Full reset
docker compose down && docker compose up -d
```

---

Created by [Siva Subramanian](https://linkedin.com/in/sivasub987)
