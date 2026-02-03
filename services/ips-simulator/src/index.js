/**
 * IPS Simulator - Instant Payment System Operator
 * 
 * Reference: https://docs.nexusglobalpayments.org/payment-processing/role-and-responsibilities-of-the-instant-payment-system-operator-ipso
 * 
 * NotebookLM Confirmed (2026-02-03):
 * - Step 15-16: Source IPS validates, reserves funds, forwards to Nexus
 * - Step 16: Destination IPS forwards to Destination SAP/PSP
 * - Timeout handling for HIGH priority payments (25s SLA)
 * - Reversal chain on RJCT status
 */

import express from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import pino from 'pino';

// =============================================================================
// Configuration
// =============================================================================

const config = {
    port: parseInt(process.env.PORT || '3002'),
    ipsId: process.env.IPS_ID || 'ips-sg',
    ipsName: process.env.IPS_NAME || 'Singapore FAST',
    ipsCountry: process.env.IPS_COUNTRY || 'SG',
    ipsCurrency: process.env.IPS_CURRENCY || 'SGD',
    clearingSystemId: process.env.IPS_CLEARING_SYSTEM_ID || 'SGFASG22',

    // IPS Limits (NotebookLM: IPS determines max amounts)
    maxAmount: parseFloat(process.env.IPS_MAX_AMOUNT || '200000'),

    // Timeouts (NotebookLM: HIGH priority timeout triggers cancellation)
    highPriorityTimeoutMs: parseInt(process.env.HIGH_PRIORITY_TIMEOUT_MS || '25000'),
    normalPriorityTimeoutMs: parseInt(process.env.NORMAL_PRIORITY_TIMEOUT_MS || '14400000'), // 4 hours

    nexusGatewayUrl: process.env.NEXUS_GATEWAY_URL || 'http://localhost:8000',
    responseDelayMs: parseInt(process.env.RESPONSE_DELAY_MS || '200'),
};

const logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    transport: { target: 'pino-pretty', options: { colorize: true } }
});

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.text({ type: 'application/xml' }));

// =============================================================================
// In-Memory State
// =============================================================================

// Registered PSPs in this IPS
const registeredPsps = {
    'DBSSSGSG': { name: 'DBS Bank', status: 'ACTIVE', balance: 10000000 },
    'UOVSSGSG': { name: 'UOB Bank', status: 'ACTIVE', balance: 8000000 },
    'OCBCSGSB': { name: 'OCBC Bank', status: 'ACTIVE', balance: 7500000 },
    'SCBLSGSG': { name: 'Standard Chartered', status: 'ACTIVE', balance: 5000000 },
};

// Payment processing ledger
const paymentLedger = [];

// Pending payments awaiting response (for timeout handling)
const pendingPayments = new Map();

// =============================================================================
// Health Endpoint
// =============================================================================

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        ipsId: config.ipsId,
        ipsName: config.ipsName,
        country: config.ipsCountry,
        currency: config.ipsCurrency,
        clearingSystemId: config.clearingSystemId,
        maxAmount: config.maxAmount,
        registeredPsps: Object.keys(registeredPsps).length,
        pendingPayments: pendingPayments.size,
        ledgerSize: paymentLedger.length,
        highPriorityTimeoutMs: config.highPriorityTimeoutMs,
    });
});

// =============================================================================
// PSP Management
// =============================================================================

app.get('/psps', (req, res) => {
    const psps = Object.entries(registeredPsps).map(([bic, data]) => ({
        bic,
        ...data,
    }));
    res.json({ ipsId: config.ipsId, pspCount: psps.length, psps });
});

app.post('/psps/:bic/register', (req, res) => {
    const { bic } = req.params;
    const { name, initialBalance } = req.body;

    registeredPsps[bic] = {
        name: name || `PSP ${bic}`,
        status: 'ACTIVE',
        balance: parseFloat(initialBalance) || 0,
    };

    logger.info({ bic }, 'PSP registered with IPS');
    res.json({ success: true, bic, message: 'PSP registered with IPS' });
});

app.post('/psps/:bic/status', (req, res) => {
    const { bic } = req.params;
    const { status } = req.body;

    if (!registeredPsps[bic]) {
        return res.status(404).json({ error: `PSP ${bic} not found` });
    }

    registeredPsps[bic].status = status;
    logger.info({ bic, status }, 'PSP status updated');
    res.json({ success: true, bic, status });
});

// =============================================================================
// Payment Processing - Inbound from Source PSP
// =============================================================================

/**
 * POST /payments/inbound - Receive payment from Source PSP
 * Step 15: pacs.008 arrives from Source PSP
 * 
 * IPS responsibilities:
 * 1. Validate message format
 * 2. Check PSP registration
 * 3. Verify amount within limits
 * 4. Reserve/debit PSP funds
 * 5. Forward to Nexus Gateway
 * 6. Start timeout timer for HIGH priority
 */
app.post('/payments/inbound', async (req, res) => {
    const payment = req.body;
    const uetr = payment.uetr || uuidv4();
    const priority = payment.instructionPriority || 'NORM';

    logger.info({ uetr, priority, amount: payment.amount }, 'Received inbound payment from PSP');

    // 1. Check PSP registration
    const pspBic = payment.sourcePspBic;
    if (!registeredPsps[pspBic]) {
        return res.status(400).json({
            uetr,
            transactionStatus: 'RJCT',
            statusReasonCode: 'AGNT',
            message: `PSP ${pspBic} not registered with ${config.ipsName}`,
        });
    }

    if (registeredPsps[pspBic].status !== 'ACTIVE') {
        return res.status(400).json({
            uetr,
            transactionStatus: 'RJCT',
            statusReasonCode: 'AB08',
            message: `PSP ${pspBic} is offline`,
        });
    }

    // 2. Check amount limits
    const amount = parseFloat(payment.amount);
    if (amount > config.maxAmount) {
        return res.status(400).json({
            uetr,
            transactionStatus: 'RJCT',
            statusReasonCode: 'AM02',
            message: `Amount ${amount} exceeds IPS limit of ${config.maxAmount}`,
        });
    }

    // 3. Check PSP balance (reserve funds)
    if (registeredPsps[pspBic].balance < amount) {
        return res.status(400).json({
            uetr,
            transactionStatus: 'RJCT',
            statusReasonCode: 'AM04',
            message: 'Insufficient funds at source PSP',
        });
    }

    // 4. Reserve funds (debit PSP)
    registeredPsps[pspBic].balance -= amount;

    // 5. Record payment
    const paymentRecord = {
        id: uuidv4(),
        uetr,
        direction: 'OUTBOUND',
        sourcePspBic: pspBic,
        amount,
        currency: payment.currency || config.ipsCurrency,
        priority,
        status: 'RESERVED',
        receivedAt: new Date().toISOString(),
    };
    paymentLedger.push(paymentRecord);

    // 6. Set up timeout for HIGH priority (NotebookLM confirmed)
    if (priority === 'HIGH') {
        const timeoutId = setTimeout(() => {
            handlePaymentTimeout(uetr);
        }, config.highPriorityTimeoutMs);

        pendingPayments.set(uetr, {
            paymentRecord,
            timeoutId,
            startTime: Date.now(),
        });

        logger.info({ uetr, timeoutMs: config.highPriorityTimeoutMs }, 'HIGH priority timeout set');
    }

    // 7. Forward to Nexus Gateway (async, non-blocking response)
    forwardToNexus(payment, paymentRecord);

    // 8. Return ACTC (Accepted Technical Validation)
    res.json({
        uetr,
        transactionStatus: 'ACTC',
        message: 'Payment accepted and forwarding to Nexus',
        reservedAmount: amount,
        reservedAt: paymentRecord.receivedAt,
    });
});

async function forwardToNexus(payment, paymentRecord) {
    try {
        const response = await axios.post(
            `${config.nexusGatewayUrl}/v1/iso20022/pacs008`,
            payment,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000,
            }
        );

        paymentRecord.status = 'FORWARDED';
        paymentRecord.forwardedAt = new Date().toISOString();
        paymentRecord.nexusResponse = response.data;

        logger.info({ uetr: paymentRecord.uetr }, 'Payment forwarded to Nexus');

    } catch (error) {
        logger.error({ uetr: paymentRecord.uetr, error: error.message }, 'Failed to forward to Nexus');

        paymentRecord.status = 'FORWARD_FAILED';
        paymentRecord.error = error.message;

        // Rollback reservation
        if (registeredPsps[paymentRecord.sourcePspBic]) {
            registeredPsps[paymentRecord.sourcePspBic].balance += paymentRecord.amount;
            paymentRecord.status = 'REVERSED';
        }
    }
}

// =============================================================================
// Payment Processing - Outbound from Nexus to Destination PSP
// =============================================================================

/**
 * POST /payments/outbound - Receive payment from Nexus for local delivery
 * Step 16: Nexus sends transformed pacs.008 to Destination IPS
 */
app.post('/payments/outbound', async (req, res) => {
    const payment = req.body;
    const uetr = payment.uetr;

    logger.info({ uetr, destPsp: payment.destinationPspBic }, 'Received payment from Nexus for local delivery');

    // Simulate processing delay
    await new Promise(r => setTimeout(r, config.responseDelayMs));

    // 1. Check destination PSP
    const destPspBic = payment.destinationPspBic;
    if (!registeredPsps[destPspBic]) {
        return res.status(400).json({
            uetr,
            transactionStatus: 'RJCT',
            statusReasonCode: 'AGNT',
            message: `Destination PSP ${destPspBic} not registered`,
        });
    }

    if (registeredPsps[destPspBic].status !== 'ACTIVE') {
        return res.status(400).json({
            uetr,
            transactionStatus: 'RJCT',
            statusReasonCode: 'AB08',
            message: 'Destination PSP offline',
        });
    }

    // 2. Record payment
    const paymentRecord = {
        id: uuidv4(),
        uetr,
        direction: 'INBOUND',
        destinationPspBic: destPspBic,
        amount: parseFloat(payment.amount),
        currency: payment.currency || config.ipsCurrency,
        status: 'DELIVERING',
        receivedAt: new Date().toISOString(),
    };
    paymentLedger.push(paymentRecord);

    // 3. Credit destination PSP (simulation of PSP receiving funds)
    registeredPsps[destPspBic].balance += parseFloat(payment.amount);

    // 4. Mark as completed
    paymentRecord.status = 'COMPLETED';
    paymentRecord.completedAt = new Date().toISOString();

    logger.info({ uetr, destPsp: destPspBic, amount: payment.amount }, 'Payment delivered to destination PSP');

    res.json({
        uetr,
        transactionStatus: 'ACCC',
        acceptanceDatetime: paymentRecord.completedAt,
        message: 'Payment credited to destination PSP',
    });
});

// =============================================================================
// Status Updates and Reversal Chain
// =============================================================================

/**
 * POST /payments/:uetr/status - Receive status update from Nexus
 * Handles pacs.002 responses and triggers reversal if RJCT
 */
app.post('/payments/:uetr/status', (req, res) => {
    const { uetr } = req.params;
    const { transactionStatus, statusReasonCode, statusReasonText } = req.body;

    logger.info({ uetr, transactionStatus, statusReasonCode }, 'Received status update from Nexus');

    // Clear pending timeout if exists
    if (pendingPayments.has(uetr)) {
        const pending = pendingPayments.get(uetr);
        clearTimeout(pending.timeoutId);
        pendingPayments.delete(uetr);
        logger.debug({ uetr }, 'Cleared pending timeout');
    }

    // Find and update payment record
    const payment = paymentLedger.find(p => p.uetr === uetr);
    if (payment) {
        payment.status = transactionStatus;
        payment.statusReasonCode = statusReasonCode;
        payment.statusReasonText = statusReasonText;
        payment.statusUpdatedAt = new Date().toISOString();

        // If rejected, trigger reversal chain
        if (transactionStatus === 'RJCT' && payment.direction === 'OUTBOUND') {
            handleReversal(payment, statusReasonCode);
        }
    }

    res.json({ acknowledged: true, uetr, status: transactionStatus });
});

// =============================================================================
// Timeout Handling (NotebookLM: HIGH priority cancellation)
// =============================================================================

function handlePaymentTimeout(uetr) {
    logger.warn({ uetr }, 'HIGH priority payment timeout - triggering cancellation');

    const pending = pendingPayments.get(uetr);
    if (!pending) return;

    const { paymentRecord } = pending;

    // Mark as timed out
    paymentRecord.status = 'TIMEOUT';
    paymentRecord.timedOutAt = new Date().toISOString();

    // Trigger reversal (refund to source PSP)
    handleReversal(paymentRecord, 'AB03');

    // Notify Nexus (send pacs.002 RJCT with AB03)
    axios.post(`${config.nexusGatewayUrl}/v1/iso20022/pacs002`, {
        uetr,
        transactionStatus: 'RJCT',
        statusReasonCode: 'AB03',
        statusReasonText: 'Aborted Settlement Timeout',
        acceptanceDatetime: new Date().toISOString(),
    }).catch(err => {
        logger.error({ uetr, error: err.message }, 'Failed to notify Nexus of timeout');
    });

    pendingPayments.delete(uetr);
}

function handleReversal(payment, reasonCode) {
    logger.info({ uetr: payment.uetr, reasonCode }, 'Processing reversal - refunding source PSP');

    // Credit back to source PSP
    if (payment.sourcePspBic && registeredPsps[payment.sourcePspBic]) {
        const psp = registeredPsps[payment.sourcePspBic];
        const previousBalance = psp.balance;
        psp.balance += payment.amount;

        payment.reversedAt = new Date().toISOString();
        payment.reversalReasonCode = reasonCode;
        payment.status = 'REVERSED';

        logger.info({
            uetr: payment.uetr,
            psp: payment.sourcePspBic,
            amount: payment.amount,
            previousBalance,
            newBalance: psp.balance,
        }, 'Funds reversed to source PSP');
    }
}

// =============================================================================
// Legacy Endpoints (for backward compatibility)
// =============================================================================

app.post('/messages/forward', async (req, res) => {
    const { uetr, destinationPspBic, pacs008 } = req.body;
    logger.info({ uetr, destinationPspBic }, 'Legacy forward endpoint called');
    await new Promise(r => setTimeout(r, config.responseDelayMs));
    res.status(202).json({ uetr, status: 'FORWARDED', clearingSystemId: config.clearingSystemId });
});

app.post('/messages/status', async (req, res) => {
    const { uetr, status, originatorPspBic } = req.body;
    logger.info({ uetr, status, originatorPspBic }, 'Legacy status endpoint called');
    res.status(200).json({ uetr, status: 'STATUS_FORWARDED' });
});

app.post('/validate/amount', async (req, res) => {
    const { amount, currency } = req.body;
    if (currency !== config.ipsCurrency) {
        return res.status(400).json({ valid: false, error: `Currency ${currency} not supported` });
    }
    const isValid = amount <= config.maxAmount;
    res.json({ valid: isValid, maxAmount: config.maxAmount, currency: config.ipsCurrency });
});

// =============================================================================
// Ledger and Reporting
// =============================================================================

app.get('/ledger', (req, res) => {
    const limit = parseInt(req.query.limit) || 50;
    res.json({
        ipsId: config.ipsId,
        ipsName: config.ipsName,
        entryCount: paymentLedger.length,
        entries: paymentLedger.slice(-limit).reverse(),
    });
});

app.get('/ledger/:uetr', (req, res) => {
    const payment = paymentLedger.find(p => p.uetr === req.params.uetr);
    if (!payment) {
        return res.status(404).json({ error: 'Payment not found in ledger' });
    }
    res.json(payment);
});

// =============================================================================
// Start Server
// =============================================================================

app.listen(config.port, () => {
    logger.info({
        port: config.port,
        ipsId: config.ipsId,
        ipsName: config.ipsName,
        country: config.ipsCountry,
        currency: config.ipsCurrency,
        clearingSystemId: config.clearingSystemId,
        maxAmount: config.maxAmount,
        registeredPsps: Object.keys(registeredPsps).length,
        highPriorityTimeoutMs: config.highPriorityTimeoutMs,
    }, 'IPS Simulator started');
});
