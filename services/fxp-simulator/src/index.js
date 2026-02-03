/**
 * FXP Simulator - Foreign Exchange Provider
 * 
 * Reference: https://docs.nexusglobalpayments.org/fx-provision/role-of-the-fx-provider
 * 
 * NotebookLM Confirmed (2026-02-03):
 * - FXPs call POST /rates, POST /tiers, POST /relationships
 * - FXPs implement webhook to receive camt.054 notifications
 * - Settlement via SAPs with prefunding requirements
 * - Tiered pricing and PSP-specific rate improvements
 * - KYB via Wolfsberg CBDDQ
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
    port: parseInt(process.env.PORT || '3000'),
    fxpId: process.env.FXP_ID || 'fxp-abc',
    fxpName: process.env.FXP_NAME || 'ABC Currency Exchange',
    fxpBic: process.env.FXP_BIC || 'ABCEXSGS',

    // FX Spread Configuration
    baseSpreadBps: parseInt(process.env.FXP_BASE_SPREAD_BPS || '50'),

    // SAP Accounts (per NotebookLM: FXPs hold accounts at SAPs)
    sapAccounts: JSON.parse(process.env.SAP_ACCOUNTS || JSON.stringify({
        SG: { sapBic: 'DBSSSGSG', accountId: 'FXP-ABC-SG-001', balance: 1000000 },
        TH: { sapBic: 'BKKBTHBK', accountId: 'FXP-ABC-TH-001', balance: 25000000 },
        PH: { sapBic: 'ABORPHMM', accountId: 'FXP-ABC-PH-001', balance: 50000000 },
        MY: { sapBic: 'MABORMMM', accountId: 'FXP-ABC-MY-001', balance: 5000000 },
        ID: { sapBic: 'BNIDIDE1', accountId: 'FXP-ABC-ID-001', balance: 15000000000 },
    })),

    nexusGatewayUrl: process.env.NEXUS_GATEWAY_URL || 'http://localhost:8000',
    rateRefreshIntervalMs: parseInt(process.env.RATE_REFRESH_INTERVAL_MS || '60000'),
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
// In-Memory State (Production: would use database)
// =============================================================================

// Base rates with spreads applied (NotebookLM: FXP posts "base rates")
const baseRates = {
    'SGD-THB': { rate: 25.85, spreadBps: 50 },
    'SGD-MYR': { rate: 3.50, spreadBps: 45 },
    'SGD-PHP': { rate: 42.50, spreadBps: 55 },
    'SGD-IDR': { rate: 11500.00, spreadBps: 60 },
    'SGD-INR': { rate: 62.50, spreadBps: 50 },
    'THB-SGD': { rate: 0.0387, spreadBps: 50 },
    'THB-MYR': { rate: 0.135, spreadBps: 45 },
    'THB-PHP': { rate: 1.64, spreadBps: 50 },
    'MYR-SGD': { rate: 0.286, spreadBps: 45 },
    'MYR-THB': { rate: 7.39, spreadBps: 45 },
    'PHP-SGD': { rate: 0.0235, spreadBps: 55 },
    'PHP-THB': { rate: 0.61, spreadBps: 50 },
    'IDR-SGD': { rate: 0.000087, spreadBps: 60 },
};

/**
 * Tiered Improvements (NotebookLM: POST /tiers)
 * FXPs define volume thresholds for automatic rate improvements
 */
const tierImprovements = {
    'SGD-THB': [
        { minAmount: 10000, improvementBps: 5 },
        { minAmount: 50000, improvementBps: 10 },
        { minAmount: 100000, improvementBps: 15 },
    ],
    'SGD-PHP': [
        { minAmount: 10000, improvementBps: 5 },
        { minAmount: 50000, improvementBps: 10 },
    ],
    // Default tiers for other pairs
    '_default': [
        { minAmount: 25000, improvementBps: 5 },
        { minAmount: 100000, improvementBps: 10 },
    ],
};

/**
 * PSP-Specific Improvements (NotebookLM: POST /relationships)
 * Preferential pricing for partner PSPs
 */
const pspRelationships = {
    'DBSSSGSG': { approved: true, improvementBps: 3, kyb: 'CBDDQ-2024-001' },
    'UOVSSGSG': { approved: true, improvementBps: 2, kyb: 'CBDDQ-2024-002' },
    'OCBCSGSB': { approved: true, improvementBps: 2, kyb: 'CBDDQ-2024-003' },
    // Not yet approved
    'SCBLSGSG': { approved: false, improvementBps: 0, kyb: null },
};

/**
 * Payment tracking for reconciliation
 * (NotebookLM: FXPs rely on camt.054 to track positions)
 */
const paymentLedger = [];

// =============================================================================
// Health Endpoints
// =============================================================================

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        fxpId: config.fxpId,
        fxpName: config.fxpName,
        fxpBic: config.fxpBic,
        baseSpreadBps: config.baseSpreadBps,
        supportedPairs: Object.keys(baseRates).length,
        approvedPsps: Object.values(pspRelationships).filter(r => r.approved).length,
        sapAccounts: Object.keys(config.sapAccounts),
    });
});

// =============================================================================
// Rate Management APIs
// =============================================================================

/**
 * GET /rates - Get all current rates from this FXP
 */
app.get('/rates', (req, res) => {
    const rates = Object.entries(baseRates).map(([pair, data]) => {
        const [source, dest] = pair.split('-');
        return {
            sourceCurrency: source,
            destinationCurrency: dest,
            baseRate: data.rate.toString(),
            spreadBps: data.spreadBps,
            effectiveRate: calculateEffectiveRate(data.rate, data.spreadBps),
            tiers: tierImprovements[pair] || tierImprovements['_default'],
            updatedAt: new Date().toISOString(),
        };
    });

    res.json({
        fxpId: config.fxpId,
        fxpBic: config.fxpBic,
        rateCount: rates.length,
        rates,
    });
});

/**
 * POST /rates - Update a specific rate
 * NotebookLM: FXPs call POST /rates to submit "base rates"
 */
app.post('/rates', (req, res) => {
    const { sourceCurrency, destinationCurrency, rate, spreadBps } = req.body;
    const pair = `${sourceCurrency}-${destinationCurrency}`;

    if (!sourceCurrency || !destinationCurrency || !rate) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    baseRates[pair] = {
        rate: parseFloat(rate),
        spreadBps: spreadBps || config.baseSpreadBps,
    };

    logger.info({ pair, rate, spreadBps }, 'Rate updated');

    res.json({
        success: true,
        pair,
        newRate: baseRates[pair],
        message: 'Rate updated. Will be submitted to Nexus on next refresh cycle.',
    });
});

/**
 * DELETE /rates/:pair - Withdraw a rate from market
 * NotebookLM: FXPs can withdraw rates (e.g., during maintenance)
 */
app.delete('/rates/:pair', (req, res) => {
    const { pair } = req.params;

    if (!baseRates[pair]) {
        return res.status(404).json({ error: 'Rate not found' });
    }

    const oldRate = baseRates[pair];
    delete baseRates[pair];

    logger.info({ pair }, 'Rate withdrawn');

    res.json({
        success: true,
        pair,
        withdrawn: oldRate,
        message: 'Rate withdrawn. Existing quotes remain valid for 10 minutes.',
    });
});

// =============================================================================
// Tier Management APIs (NotebookLM: POST /tiers)
// =============================================================================

/**
 * GET /tiers - Get all tier configurations
 */
app.get('/tiers', (req, res) => {
    res.json({
        fxpId: config.fxpId,
        tiers: tierImprovements,
    });
});

/**
 * POST /tiers - Set tier improvements for a currency pair
 */
app.post('/tiers', (req, res) => {
    const { currencyPair, tiers } = req.body;

    if (!currencyPair || !tiers || !Array.isArray(tiers)) {
        return res.status(400).json({ error: 'Invalid request' });
    }

    tierImprovements[currencyPair] = tiers.map(t => ({
        minAmount: t.minAmount,
        improvementBps: t.improvementBps,
    }));

    logger.info({ currencyPair, tierCount: tiers.length }, 'Tiers updated');

    res.json({
        success: true,
        currencyPair,
        tiers: tierImprovements[currencyPair],
    });
});

// =============================================================================
// PSP Relationship Management (NotebookLM: POST /relationships)
// =============================================================================

/**
 * GET /relationships - Get all PSP relationships
 */
app.get('/relationships', (req, res) => {
    const relationships = Object.entries(pspRelationships).map(([pspBic, data]) => ({
        pspBic,
        approved: data.approved,
        improvementBps: data.improvementBps,
        kybReference: data.kyb,
    }));

    res.json({
        fxpId: config.fxpId,
        relationshipCount: relationships.length,
        approvedCount: relationships.filter(r => r.approved).length,
        relationships,
    });
});

/**
 * POST /relationships - Register or update PSP relationship
 * NotebookLM: After KYB, FXP informs Nexus PSP is "approved"
 */
app.post('/relationships', (req, res) => {
    const { pspBic, improvementBps, kybReference, approved } = req.body;

    if (!pspBic) {
        return res.status(400).json({ error: 'PSP BIC required' });
    }

    pspRelationships[pspBic] = {
        approved: approved !== undefined ? approved : true,
        improvementBps: improvementBps || 0,
        kyb: kybReference || null,
    };

    logger.info({ pspBic, approved: pspRelationships[pspBic].approved }, 'PSP relationship updated');

    res.json({
        success: true,
        pspBic,
        relationship: pspRelationships[pspBic],
        message: approved ? 'PSP approved for FX services' : 'PSP relationship registered pending KYB',
    });
});

/**
 * POST /relationships/:pspBic/approve - Approve PSP after KYB
 */
app.post('/relationships/:pspBic/approve', (req, res) => {
    const { pspBic } = req.params;
    const { kybReference, improvementBps } = req.body;

    if (!pspRelationships[pspBic]) {
        pspRelationships[pspBic] = { approved: false, improvementBps: 0, kyb: null };
    }

    pspRelationships[pspBic].approved = true;
    pspRelationships[pspBic].kyb = kybReference || `CBDDQ-${Date.now()}`;
    if (improvementBps !== undefined) {
        pspRelationships[pspBic].improvementBps = improvementBps;
    }

    logger.info({ pspBic, kybReference: pspRelationships[pspBic].kyb }, 'PSP approved after KYB');

    res.json({
        success: true,
        pspBic,
        approved: true,
        kybReference: pspRelationships[pspBic].kyb,
        message: 'PSP approved. Quotes will now be visible to this PSP.',
    });
});

// =============================================================================
// SAP Account and Liquidity Management
// =============================================================================

/**
 * GET /liquidity - Get current liquidity positions at SAPs
 * NotebookLM: FXPs must prefund accounts at Destination SAPs
 */
app.get('/liquidity', (req, res) => {
    const positions = Object.entries(config.sapAccounts).map(([country, account]) => ({
        country,
        sapBic: account.sapBic,
        accountId: account.accountId,
        balance: account.balance,
        currency: getCurrencyForCountry(country),
    }));

    res.json({
        fxpId: config.fxpId,
        positionCount: positions.length,
        positions,
        lastUpdated: new Date().toISOString(),
    });
});

/**
 * POST /liquidity/:country/prefund - Simulate prefunding an account
 */
app.post('/liquidity/:country/prefund', (req, res) => {
    const { country } = req.params;
    const { amount } = req.body;

    if (!config.sapAccounts[country]) {
        return res.status(404).json({ error: `No SAP account for ${country}` });
    }

    config.sapAccounts[country].balance += parseFloat(amount);

    logger.info({ country, amount, newBalance: config.sapAccounts[country].balance }, 'Account prefunded');

    res.json({
        success: true,
        country,
        currency: getCurrencyForCountry(country),
        amount,
        newBalance: config.sapAccounts[country].balance,
    });
});

// =============================================================================
// Webhook: camt.054 Payment Notifications
// NotebookLM: FXP must implement webhook to receive notifications
// =============================================================================

/**
 * POST /notifications/camt054 - Receive payment notification
 * Called by Nexus immediately after pacs.002 ACCC
 */
app.post('/notifications/camt054', (req, res) => {
    const notification = req.body;

    logger.info({
        uetr: notification.uetr,
        amount: notification.amount,
        currency: notification.currency,
        direction: notification.direction,
    }, 'Received camt.054 notification');

    // Update internal ledger
    paymentLedger.push({
        id: uuidv4(),
        uetr: notification.uetr,
        amount: notification.amount,
        currency: notification.currency,
        direction: notification.direction,
        exchangeRate: notification.exchangeRate,
        timestamp: new Date().toISOString(),
        reconciled: false,
    });

    // Update SAP account balance (simulation)
    const country = getCountryForCurrency(notification.currency);
    if (country && config.sapAccounts[country]) {
        if (notification.direction === 'CREDIT') {
            config.sapAccounts[country].balance += parseFloat(notification.amount);
        } else if (notification.direction === 'DEBIT') {
            config.sapAccounts[country].balance -= parseFloat(notification.amount);
        }

        logger.debug({
            country,
            direction: notification.direction,
            newBalance: config.sapAccounts[country].balance,
        }, 'SAP balance updated');
    }

    res.status(200).json({
        acknowledged: true,
        uetr: notification.uetr,
        ledgerEntryId: paymentLedger[paymentLedger.length - 1].id,
    });
});

/**
 * GET /ledger - View payment ledger
 */
app.get('/ledger', (req, res) => {
    const limit = parseInt(req.query.limit) || 50;

    res.json({
        fxpId: config.fxpId,
        entryCount: paymentLedger.length,
        entries: paymentLedger.slice(-limit).reverse(),
    });
});

// =============================================================================
// Quote Calculation (for internal use / testing)
// =============================================================================

/**
 * POST /calculate-quote - Calculate a specific quote
 * Shows how tier and relationship improvements are applied
 */
app.post('/calculate-quote', (req, res) => {
    const { sourceCurrency, destinationCurrency, amount, pspBic } = req.body;
    const pair = `${sourceCurrency}-${destinationCurrency}`;

    if (!baseRates[pair]) {
        return res.status(404).json({ error: `No rate available for ${pair}` });
    }

    const base = baseRates[pair];
    let totalImprovementBps = 0;
    const improvements = [];

    // 1. Check tier improvements
    const tiers = tierImprovements[pair] || tierImprovements['_default'];
    for (const tier of tiers) {
        if (parseFloat(amount) >= tier.minAmount) {
            totalImprovementBps = tier.improvementBps; // Use highest qualifying tier
            improvements.push({ type: 'TIER', bps: tier.improvementBps, reason: `Amount >= ${tier.minAmount}` });
        }
    }

    // 2. Check PSP relationship improvements (added to tier)
    if (pspBic && pspRelationships[pspBic]?.approved) {
        const pspImprovement = pspRelationships[pspBic].improvementBps;
        totalImprovementBps += pspImprovement;
        improvements.push({ type: 'RELATIONSHIP', bps: pspImprovement, reason: `PSP ${pspBic} relationship` });
    }

    // 3. Calculate final rate
    const effectiveSpreadBps = Math.max(0, base.spreadBps - totalImprovementBps);
    const finalRate = calculateEffectiveRate(base.rate, effectiveSpreadBps);

    res.json({
        fxpId: config.fxpId,
        pair,
        amount,
        baseRate: base.rate,
        baseSpreadBps: base.spreadBps,
        improvements,
        totalImprovementBps,
        effectiveSpreadBps,
        finalRate,
        destinationAmount: (parseFloat(amount) * finalRate).toFixed(2),
        quoteValidFor: '600 seconds',
    });
});

// =============================================================================
// Helper Functions
// =============================================================================

function calculateEffectiveRate(baseRate, spreadBps) {
    // Spread reduces the rate customer gets
    return baseRate * (1 - spreadBps / 10000);
}

function getCurrencyForCountry(country) {
    const map = { SG: 'SGD', TH: 'THB', MY: 'MYR', PH: 'PHP', ID: 'IDR', IN: 'INR' };
    return map[country] || country;
}

function getCountryForCurrency(currency) {
    const map = { SGD: 'SG', THB: 'TH', MYR: 'MY', PHP: 'PH', IDR: 'ID', INR: 'IN' };
    return map[currency] || null;
}

// =============================================================================
// Background: Rate Submission to Nexus
// =============================================================================

async function submitRatesToNexus() {
    try {
        for (const [pair, data] of Object.entries(baseRates)) {
            const [source, dest] = pair.split('-');

            await axios.post(`${config.nexusGatewayUrl}/v1/rates`, {
                fxpId: config.fxpId,
                fxpBic: config.fxpBic,
                sourceCurrency: source,
                destinationCurrency: dest,
                baseRate: data.rate,
                spreadBps: data.spreadBps,
                validSeconds: config.rateRefreshIntervalMs / 1000 * 2,
            }, {
                headers: { 'Content-Type': 'application/json' }
            });

            logger.debug({ pair, rate: data.rate }, 'Rate submitted');
        }

        logger.info({ pairCount: Object.keys(baseRates).length }, 'All rates submitted to Nexus');
    } catch (error) {
        logger.error({ error: error.message }, 'Failed to submit rates');
    }
}

async function submitTiersToNexus() {
    try {
        for (const [pair, tiers] of Object.entries(tierImprovements)) {
            if (pair === '_default') continue;

            await axios.post(`${config.nexusGatewayUrl}/v1/tiers`, {
                fxpId: config.fxpId,
                currencyPair: pair,
                tiers,
            }, {
                headers: { 'Content-Type': 'application/json' }
            });
        }

        logger.info('Tier configurations submitted to Nexus');
    } catch (error) {
        logger.debug({ error: error.message }, 'Failed to submit tiers (gateway may be starting)');
    }
}

// =============================================================================
// Start Server
// =============================================================================

app.listen(config.port, () => {
    logger.info({
        port: config.port,
        fxpId: config.fxpId,
        fxpName: config.fxpName,
        fxpBic: config.fxpBic,
        pairCount: Object.keys(baseRates).length,
        sapCountries: Object.keys(config.sapAccounts),
    }, 'FXP Simulator started');

    // Start rate refresh loop (wait for gateway to start)
    setTimeout(() => {
        submitRatesToNexus();
        submitTiersToNexus();
        setInterval(submitRatesToNexus, config.rateRefreshIntervalMs);
    }, 10000);
});
