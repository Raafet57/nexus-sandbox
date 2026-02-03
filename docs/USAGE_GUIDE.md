# Nexus Global Payments Sandbox: Usage Guide 🚀

Welcome to the Nexus Sandbox! this guide will help you simulate your first cross-border payment and explore the underlying ISO 20022 infrastructure.

## Getting Started

### 1. Boot the Sandbox
Ensure you have Docker and Docker Compose installed.
```bash
docker compose up
```

### 2. Access the Dashboard
The demo dashboard is available at:
- **URL**: [http://localhost:5173](http://localhost:5173)
- **API Status**: Look for the "CONNECTED" badge in the header.

---

## Your First Payment (Happy Flow)

Follow these steps to simulate a successful payment:

1.  **Select Destination**: Choose **Singapore** or **Thailand**.
2.  **Define Amount**: Enter an amount (e.g., 1000). The sandbox will validate against simulated FXP liquidity limits.
3.  **Select FX Quote**: Choose one of the multi-provider quotes (powered by simulated FXP aggregation).
4.  **Enter Recipient**:
    - Select **Mobile Number** (MBNO).
    - Use a test value like `+6591234567`.
    - Click **Search** to trigger the `acmt.023` resolution flow.
5.  **Confirm Identity**: Verify the beneficiary name returned by the simulated PDO.
6.  **Confirm & Send**: Click send to trigger the `pacs.008` instruction.

### What to watch in the Lifecycle Trace:
- **Step 6**: Preview the Pre-Transaction Disclosure (PTD).
- **Step 8**: See the `acmt.023` resolution details.
- **Step 13**: Observe the identified **Settlement Path** (Source and Destination SAP accounts).

---

## Advanced Scenarios (Unhappy Flows)

Test how your system should handle errors by using these trigger values:

| Scenario | Trigger Value | Error Code | Description |
| :--- | :--- | :--- | :--- |
| **Proxy Not Found** | `+XX9999999999` | `BE23` | Simulated PDO returns "Account Proxy Invalid". |
| **Sanctions Hit** | `SANCTION_HIT` | `RJCT` | (Simulated internal check) Triggers a payment rejection. |
| **Limit Exceeded** | `> 50,000` | `VAL01` | Triggers a maximum transaction amount violation. |

---

## Exploring the Infrastructure

- **Nexus Mesh View**: Visit the **Registry & Mesh** tab to see the distribution of actors (PSP, IPS, FXP, SAP) across the network.
- **API Docs**: Access the interactive Swagger documentation at [http://localhost:8000/docs](http://localhost:8000/docs).
- **ISO 20022 Logs**: Check the `nexus-gateway` container logs to see the raw JSON interpretations of acmt and pacs messages.

---

## Developer Integration

For detailed instructions on connecting your own system to the Sandbox, see the [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md).
