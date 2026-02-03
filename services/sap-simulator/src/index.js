/**
 * SAP Simulator - Settlement Access Provider
 * 
 * Reference: https://docs.nexusglobalpayments.org/settlement-access-provision/role-of-the-settlement-access-provider-sap
 * 
 * SAPs provide correspondent banking services:
 * - Hold FXP nostro/vostro accounts
 * - Process settlement instructions
 * - Send camt.054 notifications
 */

import express from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import pino from 'pino';

const config = {
    port: parseInt(process.env.PORT || '3000'),
    sapId: process.env.SAP_ID || 'sap-dbs',
    sapName: process.env.SAP_NAME || 'DBS SAP Singapore',
    sapBic: process.env.SAP_BIC || 'DBSSSGSG',
    sapCountry: process.env.SAP_COUNTRY || 'SG',
    sapCurrency: process.env.SAP_CURRENCY || 'SGD',
    nexusGatewayUrl: process.env.NEXUS_GATEWAY_URL || 'http://localhost:8000',
};

const logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    transport: { target: 'pino-pretty', options: { colorize: true } }
});

const app = express();
app.use(cors());
app.use(express.json());

// In-memory FXP account balances (for simulation)
const fxpAccounts = new Map();

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        sapId: config.sapId,
        sapName: config.sapName,
        sapBic: config.sapBic,
        country: config.sapCountry,
    });
});

/**
 * Get FXP account details
 * Reference: https://docs.nexusglobalpayments.org/settlement-access-provision/payment-process-for-the-source-sap
 */
app.get('/accounts/:fxpId', (req, res) => {
    const { fxpId } = req.params;

    const account = fxpAccounts.get(fxpId) || {
        fxpId,
        accountNumber: `SAP${config.sapId.toUpperCase()}${fxpId.toUpperCase().slice(0, 6)}`,
        currency: config.sapCurrency,
        balance: 1000000, // Default balance for simulation
    };

    res.json(account);
});

/**
 * Process credit to FXP account
 */
app.post('/accounts/:fxpId/credit', (req, res) => {
    const { fxpId } = req.params;
    const { amount, uetr, reference } = req.body;

    logger.info({ fxpId, amount, uetr }, 'Processing credit');

    // Get or create account
    let account = fxpAccounts.get(fxpId);
    if (!account) {
        account = {
            fxpId,
            accountNumber: `SAP${config.sapId.toUpperCase()}${fxpId.toUpperCase().slice(0, 6)}`,
            currency: config.sapCurrency,
            balance: 1000000,
        };
        fxpAccounts.set(fxpId, account);
    }

    account.balance += parseFloat(amount);

    res.json({
        success: true,
        uetr,
        newBalance: account.balance,
        reference,
    });
});

/**
 * Process debit from FXP account
 */
app.post('/accounts/:fxpId/debit', (req, res) => {
    const { fxpId } = req.params;
    const { amount, uetr, reference } = req.body;

    logger.info({ fxpId, amount, uetr }, 'Processing debit');

    let account = fxpAccounts.get(fxpId);
    if (!account) {
        return res.status(404).json({ error: 'Account not found' });
    }

    if (account.balance < amount) {
        return res.status(400).json({ error: 'Insufficient funds' });
    }

    account.balance -= parseFloat(amount);

    res.json({
        success: true,
        uetr,
        newBalance: account.balance,
        reference,
    });
});

/**
 * Get intermediary agent details
 * Reference: https://docs.nexusglobalpayments.org/payment-setup/step-13-16-set-up-and-send-the-payment-instruction
 */
app.get('/intermediary-agent', (req, res) => {
    res.json({
        bic: config.sapBic,
        name: config.sapName,
        country: config.sapCountry,
        currency: config.sapCurrency,
    });
});

app.listen(config.port, () => {
    logger.info({
        port: config.port,
        sapId: config.sapId,
        sapBic: config.sapBic,
    }, 'SAP Simulator started');
});
