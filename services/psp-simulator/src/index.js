/**
 * PSP Simulator - Main Application
 * 
 * Simulates a Payment Service Provider (bank/payment app) in the Nexus network.
 * 
 * Reference: https://docs.nexusglobalpayments.org/payment-processing/key-points
 * 
 * A PSP can be:
 * - Source PSP: Initiates payments on behalf of senders
 * - Destination PSP: Receives payments for recipients
 */

import express from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { XMLParser, XMLBuilder } from 'fast-xml-parser';
import pino from 'pino';

// Configuration from environment
const config = {
    port: parseInt(process.env.PORT || '3000'),
    pspBic: process.env.PSP_BIC || 'DBSSSGSG',
    pspCountry: process.env.PSP_COUNTRY || 'SG',
    pspCurrency: process.env.PSP_CURRENCY || 'SGD',
    pspName: process.env.PSP_NAME || 'DBS Bank Singapore',
    pspMaxAmount: parseFloat(process.env.PSP_MAX_AMOUNT || '200000'),
    pspFeePercent: parseFloat(process.env.PSP_FEE_PERCENT || '0.5') / 100,
    nexusGatewayUrl: process.env.NEXUS_GATEWAY_URL || 'http://localhost:8000',
    ipsUrl: process.env.IPS_URL || 'http://localhost:3101',
    sanctionsRejectNames: (process.env.SANCTIONS_REJECT_NAMES || 'Kim Jong Un,Vladimir Putin').split(','),
    responseDelayMs: parseInt(process.env.RESPONSE_DELAY_MS || '500'),
};

// Logger
const logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    transport: {
        target: 'pino-pretty',
        options: { colorize: true }
    }
});

// XML parser/builder for ISO 20022 messages
const xmlParser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: '@_',
});

const xmlBuilder = new XMLBuilder({
    ignoreAttributes: false,
    attributeNamePrefix: '@_',
    format: true,
});

// Express app
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.text({ type: 'application/xml' }));

// Request logging
app.use((req, res, next) => {
    logger.info({ method: req.method, path: req.path }, 'Request received');
    next();
});

// =============================================================================
// Health Endpoints
// =============================================================================

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        pspBic: config.pspBic,
        pspName: config.pspName,
        country: config.pspCountry,
        capabilities: {
            sourcePayments: true,
            destinationPayments: true,
            proxyResolution: true,  // Can resolve mobile/email to accounts
            confirmationOfPayee: true,
        },
        supportedProxyTypes: ['MBNO', 'EMAL', 'ACCT'],
    });
});

/**
 * Get supported address types for a destination country.
 * Reference: NotebookLM - PSP should call GET /address-types for dynamic forms
 */
app.get('/demo/address-types/:country', async (req, res) => {
    const { country } = req.params;

    try {
        const response = await axios.get(
            `${config.nexusGatewayUrl}/v1/countries/${country}/address-types`
        );
        res.json(response.data);
    } catch (error) {
        // Return simulated data if gateway unavailable
        res.json({
            country,
            addressTypes: [
                {
                    code: 'MBNO',
                    label: 'Mobile Number',
                    regex: country === 'PH' ? '^\\+639[0-9]{9}$' : '^\\+[0-9]{8,15}$',
                },
                {
                    code: 'EMAL',
                    label: 'Email Address',
                    regex: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
                },
                {
                    code: 'ACCT',
                    label: 'Account Number',
                    regex: '^[A-Za-z0-9]{5,20}$',
                },
            ],
        });
    }
});

// =============================================================================
// Demo UI - Initiate Payment
// Reference: https://docs.nexusglobalpayments.org/payment-setup/key-points
// =============================================================================

/**
 * Demo endpoint to initiate a cross-border payment.
 * 
 * This simulates the PSP's internal process when a customer initiates a payment:
 * - Step 3-6: Get FX quotes
 * - Step 7-9: Resolve proxy (CoP - Confirmation of Payee)
 * - Step 10-11: Sanctions screening
 * - Step 12: Pre-transaction disclosure
 * - Step 13-16: Create and send pacs.008
 * 
 * Reference: NotebookLM confirmed PSP responsibilities (2026-02-03)
 */
app.post('/demo/initiate-payment', async (req, res) => {
    try {
        const {
            debtorName,
            debtorAccount,
            creditorIdentifier,      // Could be mobile, email, or account
            creditorIdentifierType,  // MBNO, EMAL, etc.
            creditorCountry,
            amount,
            amountType = 'SOURCE',
            purposeCode = 'GDDS',
            remittanceInfo,
            senderIdHash,            // Anti-fraud: hash of sender's ID
        } = req.body;

        const uetr = uuidv4();
        logger.info({ uetr }, 'Initiating payment');

        // =================================================================
        // Step 7-9: Confirmation of Payee (CoP) - Proxy Resolution
        // Reference: NotebookLM - POST /iso20022/acmt023
        // =================================================================
        logger.info('Step 7-9: Confirmation of Payee (CoP)');

        let creditorName, creditorAccount;

        if (creditorIdentifierType === 'ACCT') {
            // Direct account number - no resolution needed
            creditorAccount = creditorIdentifier;
            creditorName = req.body.creditorName || 'Unknown Recipient';
        } else {
            // Proxy resolution required (mobile, email, etc.)
            try {
                const copResponse = await resolveProxy({
                    proxyType: creditorIdentifierType,
                    proxyValue: creditorIdentifier,
                    destinationCountry: creditorCountry,
                    senderIdHash,
                });

                creditorName = copResponse.displayName;
                creditorAccount = copResponse.accountNumber;

                logger.info({
                    proxyType: creditorIdentifierType,
                    displayName: creditorName,
                }, 'CoP successful - recipient verified');

            } catch (copError) {
                logger.warn({ error: copError.message }, 'CoP failed');
                return res.status(400).json({
                    error: 'COP_FAILED',
                    message: `Could not verify recipient: ${copError.message}`,
                    uetr,
                });
            }
        }

        // =================================================================
        // Step 3-6: Get FX Quotes
        // Reference: NotebookLM - GET /quotes (must call each time amount changes)
        // Quote expiry: 10 minutes (600 seconds)
        // =================================================================
        logger.info('Step 3-4: Getting FX quotes');
        const quotesResponse = await axios.get(`${config.nexusGatewayUrl}/v1/quotes`, {
            params: {
                sourceCountry: config.pspCountry,
                destCountry: creditorCountry,
                amount,
                amountType,
                sourcePspBic: config.pspBic,
            },
        });

        const quotes = quotesResponse.data.quotes;
        if (!quotes || quotes.length === 0) {
            throw new Error('No FX quotes available');
        }

        // Step 5: Select best quote (lowest rate for the customer)
        // NotebookLM: PSP selects preferred quote, generally doesn't show full list to sender
        const selectedQuote = quotes[0];
        const quoteExpiresAt = new Date(selectedQuote.validUntil || Date.now() + 600000);

        logger.info({
            quoteId: selectedQuote.quoteId,
            rate: selectedQuote.exchangeRate,
            expiresAt: quoteExpiresAt.toISOString(),
        }, 'Quote selected');

        // Check quote expiry (10 minute rule)
        if (new Date() > quoteExpiresAt) {
            return res.status(400).json({
                error: 'QUOTE_EXPIRED',
                message: 'Quote has expired. Please refresh quotes.',
                uetr,
            });
        }

        // Step 6: Get intermediary agents
        logger.info('Step 6: Getting intermediary agents');
        const agentsResponse = await axios.get(
            `${config.nexusGatewayUrl}/v1/quotes/${selectedQuote.quoteId}/intermediary-agents`
        );
        const agents = agentsResponse.data;

        // =================================================================
        // Step 10-11: Sanctions Screening
        // Reference: NotebookLM - PSP performs screening before sending
        // =================================================================
        logger.info('Step 10-11: Sanctions screening');
        const sanctionsHit = performSanctionsCheck(debtorName, creditorName);
        if (sanctionsHit) {
            logger.warn({ sanctionsHit }, 'Sanctions hit - rejecting payment');
            return res.status(400).json({
                error: 'SANCTIONS_HIT',
                message: `Sanctions screening failed: ${sanctionsHit}`,
                uetr,
            });
        }

        // =================================================================
        // Step 12: Pre-Transaction Disclosure
        // Reference: NotebookLM - PSP MUST display before sender confirms:
        // 1) Amount Debited, 2) Amount Credited, 3) Fees, 4) Effective Rate
        // =================================================================
        logger.info('Step 12: Getting pre-transaction disclosure');
        const disclosureResponse = await axios.get(
            `${config.nexusGatewayUrl}/v1/fees/pre-transaction-disclosure`, {
            params: {
                quoteId: selectedQuote.quoteId,
                sourcePspFee: config.pspFeePercent * parseFloat(amount),
                sourcePspFeeType: 'INVOICED',
            }
        }
        );
        const disclosure = disclosureResponse.data;

        logger.info({
            amountDebited: disclosure.amountDebited,
            amountCredited: disclosure.amountCredited,
            effectiveRate: disclosure.effectiveExchangeRate,
        }, 'Pre-transaction disclosure ready');

        // =================================================================
        // Step 13-14: Build pacs.008 Message
        // =================================================================
        logger.info('Step 13-14: Building pacs.008');
        const pacs008 = buildPacs008({
            uetr,
            debtorName,
            debtorAccount,
            creditorName,
            creditorAccount,
            amount: selectedQuote.sourceInterbankAmount,
            currency: config.pspCurrency,
            exchangeRate: selectedQuote.exchangeRate,
            quoteId: selectedQuote.quoteId,
            purposeCode,
            remittanceInfo,
            sourcePspBic: config.pspBic,
            intermediaryAgent1: agents.intermediaryAgent1,
            intermediaryAgent2: agents.intermediaryAgent2,
        });

        // Step 15: Send to IPS
        logger.info('Step 15: Sending to IPS');
        // In production: await axios.post(`${config.ipsUrl}/payments`, pacs008);

        res.status(202).json({
            message: 'Payment initiated',
            uetr,
            quoteId: selectedQuote.quoteId,
            // Pre-transaction disclosure (MANDATORY per Nexus)
            preTransactionDisclosure: {
                amountDebited: disclosure.amountDebited,
                amountCredited: disclosure.amountCredited,
                sourcePspFee: disclosure.sourcePspFee,
                effectiveExchangeRate: disclosure.effectiveExchangeRate,
                nexusSchemeFee: disclosure.nexusSchemeFee,
            },
            recipientVerified: {
                displayName: creditorName,
                masked: true,
            },
            exchangeRate: selectedQuote.exchangeRate,
            quoteExpiresAt: quoteExpiresAt.toISOString(),
            status: 'INITIATED',
        });

    } catch (error) {
        logger.error({ error: error.message }, 'Payment initiation failed');
        res.status(500).json({
            error: 'INITIATION_FAILED',
            message: error.message,
        });
    }
});

// =============================================================================
// Receive Payment (as Destination PSP)
// Reference: https://docs.nexusglobalpayments.org/payment-processing/key-points
// =============================================================================

/**
 * Receive a pacs.008 payment instruction.
 * 
 * This endpoint is called by the IPS when a cross-border payment
 * arrives for a customer at this PSP.
 */
app.post('/payments/receive', async (req, res) => {
    try {
        const pacs008Xml = req.body;
        const parsed = xmlParser.parse(pacs008Xml);

        // Extract key fields
        const uetr = extractUetr(parsed);
        const creditorName = extractCreditorName(parsed);
        const amount = extractAmount(parsed);

        logger.info({ uetr, creditorName, amount }, 'Payment received');

        // Simulate processing delay
        await delay(config.responseDelayMs);

        // Simulate acceptance (could add rejection logic here)
        const pacs002 = buildPacs002(uetr, 'ACCC', null);

        logger.info({ uetr }, 'Payment accepted');

        res.status(200).json({
            uetr,
            status: 'ACCC',
            message: 'Payment accepted',
        });

    } catch (error) {
        logger.error({ error: error.message }, 'Payment processing failed');
        res.status(500).json({
            error: 'PROCESSING_FAILED',
            message: error.message,
        });
    }
});

/**
 * Receive a pacs.002 status report.
 * 
 * This endpoint is called when the destination PSP responds
 * to a payment we initiated.
 */
app.post('/payments/:uetr/status', async (req, res) => {
    const { uetr } = req.params;
    const { status, reasonCode } = req.body;

    logger.info({ uetr, status, reasonCode }, 'Status update received');

    // In a real implementation, update internal payment state
    // and notify the customer

    res.status(200).json({
        uetr,
        status,
        acknowledged: true,
    });
});

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Simulated proxy database for CoP testing.
 * In production, this would call POST /iso20022/acmt023
 */
const simulatedProxyDb = {
    // Philippines mobile numbers
    '+639171234567': { displayName: 'Juan D***', accountNumber: '1234567890', country: 'PH' },
    '+639181234567': { displayName: 'Maria S***', accountNumber: '0987654321', country: 'PH' },
    // Thailand mobile numbers
    '+66812345678': { displayName: 'Somchai T***', accountNumber: 'TH12345678', country: 'TH' },
    // Singapore mobile numbers
    '+6591234567': { displayName: 'Ah Kow L***', accountNumber: 'SG98765432', country: 'SG' },
    // Malaysia mobile numbers
    '+60123456789': { displayName: 'Ahmad B***', accountNumber: 'MY11223344', country: 'MY' },
    // Indonesia mobile numbers
    '+6281234567890': { displayName: 'Budi P***', accountNumber: 'ID55667788', country: 'ID' },
};

/**
 * Resolve proxy identifier to account details via CoP.
 * Reference: NotebookLM - POST /iso20022/acmt023
 * 
 * @param {Object} params
 * @param {string} params.proxyType - MBNO, EMAL, etc.
 * @param {string} params.proxyValue - The actual mobile/email
 * @param {string} params.destinationCountry - Target country
 * @param {string} params.senderIdHash - Anti-fraud hash of sender ID
 * @returns {Promise<{displayName: string, accountNumber: string}>}
 */
async function resolveProxy({ proxyType, proxyValue, destinationCountry, senderIdHash }) {
    logger.info({ proxyType, proxyValue, destinationCountry }, 'Resolving proxy via CoP');

    // In production: Call POST /iso20022/acmt023
    // For sandbox: Use simulated database

    // Simulate network delay
    await delay(config.responseDelayMs);

    // Look up in simulated database
    const record = simulatedProxyDb[proxyValue];

    if (!record) {
        throw new Error(`Proxy not found: ${proxyValue}`);
    }

    if (record.country !== destinationCountry) {
        throw new Error(`Proxy ${proxyValue} is registered in ${record.country}, not ${destinationCountry}`);
    }

    // Anti-fraud rate limiting (in production, Nexus Gateway tracks this)
    if (senderIdHash) {
        logger.debug({ senderIdHash }, 'Anti-fraud: sender ID hash provided');
    }

    return {
        displayName: record.displayName,
        accountNumber: record.accountNumber,
    };
}

/**
 * Perform simulated sanctions screening.
 * Reference: https://docs.nexusglobalpayments.org/payment-setup/steps-10-11-sanctions-screening
 */
function performSanctionsCheck(debtorName, creditorName) {
    for (const sanctioned of config.sanctionsRejectNames) {
        if (debtorName.toLowerCase().includes(sanctioned.toLowerCase())) {
            return `Debtor name matches: ${sanctioned}`;
        }
        if (creditorName.toLowerCase().includes(sanctioned.toLowerCase())) {
            return `Creditor name matches: ${sanctioned}`;
        }
    }
    return null;
}

/**
 * Build a pacs.008 message.
 * Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-pacs.008-fi-to-fi-customer-credit-transfer
 */
function buildPacs008(params) {
    const msgId = `${config.pspBic}-${Date.now()}`;
    const now = new Date().toISOString();

    // Simplified pacs.008 structure
    // In production, this would include all required elements
    const message = {
        Document: {
            '@_xmlns': 'urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08',
            FIToFICstmrCdtTrf: {
                GrpHdr: {
                    MsgId: msgId,
                    CreDtTm: now,
                    NbOfTxs: '1',
                    SttlmInf: {
                        SttlmMtd: 'CLRG',
                    },
                },
                CdtTrfTxInf: {
                    PmtId: {
                        InstrId: msgId,
                        EndToEndId: params.uetr,
                        UETR: params.uetr,
                    },
                    IntrBkSttlmAmt: {
                        '@_Ccy': params.currency,
                        '#text': params.amount,
                    },
                    XchgRate: params.exchangeRate,
                    XchgRateInf: {
                        CtrctId: params.quoteId,
                    },
                    InstgAgt: {
                        FinInstnId: {
                            BICFI: params.sourcePspBic,
                        },
                    },
                    IntrmyAgt1: {
                        FinInstnId: {
                            BICFI: params.intermediaryAgent1.bic,
                        },
                    },
                    IntrmyAgt2: {
                        FinInstnId: {
                            BICFI: params.intermediaryAgent2.bic,
                        },
                    },
                    Dbtr: {
                        Nm: params.debtorName,
                    },
                    DbtrAcct: {
                        Id: {
                            Othr: {
                                Id: params.debtorAccount,
                            },
                        },
                    },
                    Cdtr: {
                        Nm: params.creditorName,
                    },
                    CdtrAcct: {
                        Id: {
                            Othr: {
                                Id: params.creditorAccount,
                            },
                        },
                    },
                    Purp: {
                        Cd: params.purposeCode,
                    },
                    RmtInf: {
                        Ustrd: params.remittanceInfo || '',
                    },
                },
            },
        },
    };

    return xmlBuilder.build(message);
}

/**
 * Build a pacs.002 status report.
 * Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/message-pacs.002-payment-status-report
 */
function buildPacs002(uetr, status, reasonCode) {
    const msgId = `${config.pspBic}-${Date.now()}-STATUS`;
    const now = new Date().toISOString();

    const message = {
        Document: {
            '@_xmlns': 'urn:iso:std:iso:20022:tech:xsd:pacs.002.001.10',
            FIToFIPmtStsRpt: {
                GrpHdr: {
                    MsgId: msgId,
                    CreDtTm: now,
                },
                TxInfAndSts: {
                    OrgnlEndToEndId: uetr,
                    TxSts: status,
                    StsRsnInf: reasonCode ? { Rsn: { Cd: reasonCode } } : undefined,
                },
            },
        },
    };

    return xmlBuilder.build(message);
}

function extractUetr(parsed) {
    return parsed?.Document?.FIToFICstmrCdtTrf?.CdtTrfTxInf?.PmtId?.UETR || 'unknown';
}

function extractCreditorName(parsed) {
    return parsed?.Document?.FIToFICstmrCdtTrf?.CdtTrfTxInf?.Cdtr?.Nm || 'Unknown';
}

function extractAmount(parsed) {
    return parsed?.Document?.FIToFICstmrCdtTrf?.CdtTrfTxInf?.IntrBkSttlmAmt?.['#text'] || '0';
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// =============================================================================
// Start Server
// =============================================================================

app.listen(config.port, () => {
    logger.info({
        port: config.port,
        pspBic: config.pspBic,
        pspName: config.pspName,
        country: config.pspCountry,
    }, 'PSP Simulator started');
});
