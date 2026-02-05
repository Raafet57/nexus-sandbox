// Mock Data for GitHub Pages Static Demo
// This file provides static data when the app runs without a backend

export const MOCK_ENABLED = import.meta.env.VITE_MOCK_DATA === "true" || import.meta.env.VITE_GITHUB_PAGES === "true";

// ============================================================================
// CURRENCY-AWARE FX RATES
// ============================================================================

const FX_RATES: Record<string, number> = {
    // SGD base rates
    "SGD_THB": 25.85,
    "SGD_IDR": 11423.50,
    "SGD_MYR": 3.45,
    "SGD_PHP": 42.15,
    "SGD_INR": 62.50,
    // THB base rates
    "THB_SGD": 0.0387,
    "THB_IDR": 441.80,
    "THB_MYR": 0.1334,
    // MYR base rates  
    "MYR_SGD": 0.290,
    "MYR_THB": 7.49,
    "MYR_IDR": 3310.00,
    // IDR base rates
    "IDR_SGD": 0.0000875,
    "IDR_THB": 0.00226,
    "IDR_MYR": 0.000302,
    // PHP base rates
    "PHP_SGD": 0.0237,
    // INR base rates
    "INR_SGD": 0.016,
};

// Country to currency mapping
const COUNTRY_CURRENCY: Record<string, string> = {
    "SG": "SGD",
    "TH": "THB",
    "MY": "MYR",
    "ID": "IDR",
    "PH": "PHP",
    "IN": "INR",
};

// ============================================================================
// MOCK PAYMENT STORE (Session-based state for GitHub Pages)
// ============================================================================

interface MockPayment {
    uetr: string;
    quoteId: string;
    sourcePspBic: string;
    destinationPspBic: string;
    debtorName: string;
    debtorAccount: string;
    creditorName: string;
    creditorAccount: string;
    sourceCurrency: string;
    destinationCurrency: string;
    sourceAmount: number;
    destinationAmount: number;
    exchangeRate: string;
    status: string;
    statusReasonCode?: string;
    createdAt: string;
    initiated_at: string; // Alias for createdAt for type compatibility
    completedAt?: string;
    messages: MockMessage[];
    events: MockEvent[];
}

interface MockMessage {
    messageType: string;
    direction: "inbound" | "outbound";
    xml: string;
    timestamp: string;
    description?: string;
}

interface MockEvent {
    eventId: string;
    uetr: string; // Required for PaymentEvent compatibility
    eventType: string;
    event_type?: string; // Alias for backend sync compatibility
    timestamp: string;
    actor: string;
    data: Record<string, unknown>; // Required for PaymentEvent compatibility
    details: Record<string, unknown>;
}

class MockPaymentStore {
    private payments: Map<string, MockPayment> = new Map();

    createPayment(params: {
        uetr: string;
        quoteId: string;
        exchangeRate: number;
        sourceAmount: number;
        sourceCurrency: string;
        destinationAmount: number;
        destinationCurrency: string;
        debtorName: string;
        debtorAccount: string;
        debtorAgentBic: string;
        creditorName: string;
        creditorAccount: string;
        creditorAgentBic: string;
        scenarioCode?: string;
    }): MockPayment {
        const now = new Date().toISOString();

        // Determine status based on scenario
        let status = "ACCC";
        let statusReasonCode: string | undefined;

        if (params.scenarioCode && params.scenarioCode !== "happy") {
            status = "RJCT";
            statusReasonCode = params.scenarioCode.toUpperCase();
        }

        // Generate pacs.008 XML
        const pacs008Xml = this.generatePacs008Xml(params, now);
        const pacs002Xml = this.generatePacs002Xml(params, status, statusReasonCode, now);

        const payment: MockPayment = {
            uetr: params.uetr,
            quoteId: params.quoteId,
            sourcePspBic: params.debtorAgentBic,
            destinationPspBic: params.creditorAgentBic,
            debtorName: params.debtorName,
            debtorAccount: params.debtorAccount,
            creditorName: params.creditorName,
            creditorAccount: params.creditorAccount,
            sourceCurrency: params.sourceCurrency,
            destinationCurrency: params.destinationCurrency,
            sourceAmount: params.sourceAmount,
            destinationAmount: params.destinationAmount,
            exchangeRate: params.exchangeRate.toString(),
            status,
            statusReasonCode,
            createdAt: now,
            initiated_at: now, // Alias for type compatibility
            completedAt: status === "ACCC" ? now : undefined,
            messages: [
                {
                    messageType: "pacs.008.001.13",
                    direction: "outbound",
                    xml: pacs008Xml,
                    timestamp: now,
                    description: "FI to FI Customer Credit Transfer"
                },
                {
                    messageType: "pacs.002.001.12",
                    direction: "inbound",
                    xml: pacs002Xml,
                    timestamp: now,
                    description: "Payment Status Report"
                }
            ],
            events: [
                { eventId: `evt-${Date.now()}-1`, uetr: params.uetr, eventType: "PAYMENT_INITIATED", event_type: "PAYMENT_INITIATED", timestamp: now, actor: params.debtorAgentBic, data: {}, details: {} },
                { eventId: `evt-${Date.now()}-2`, uetr: params.uetr, eventType: "QUOTE_VALIDATED", event_type: "QUOTE_VALIDATED", timestamp: now, actor: "NEXUSGWS", data: { quoteId: params.quoteId }, details: { quoteId: params.quoteId } },
                { eventId: `evt-${Date.now()}-3`, uetr: params.uetr, eventType: status === "ACCC" ? "SETTLEMENT_COMPLETE" : "PAYMENT_REJECTED", event_type: status === "ACCC" ? "SETTLEMENT_COMPLETE" : "PAYMENT_REJECTED", timestamp: now, actor: "NEXUSGWS", data: { status, statusReasonCode }, details: { status, statusReasonCode } },
            ]
        };

        this.payments.set(params.uetr, payment);
        return payment;
    }

    get(uetr: string): MockPayment | undefined {
        return this.payments.get(uetr);
    }

    getStatus(uetr: string): { uetr: string; status: string; statusReasonCode?: string; reasonDescription?: string; sourcePsp: string; destinationPsp: string; amount: number; currency: string; initiatedAt: string; completedAt?: string } | { status: "NOT_FOUND"; uetr: string } {
        const payment = this.payments.get(uetr);
        if (!payment) {
            return { status: "NOT_FOUND", uetr };
        }
        return {
            uetr: payment.uetr,
            status: payment.status,
            statusReasonCode: payment.statusReasonCode,
            reasonDescription: this.getReasonDescription(payment.statusReasonCode),
            sourcePsp: payment.sourcePspBic,
            destinationPsp: payment.destinationPspBic,
            amount: payment.sourceAmount,
            currency: payment.sourceCurrency,
            initiatedAt: payment.createdAt,
            completedAt: payment.completedAt,
        };
    }

    getMessages(uetr: string): { messages: MockMessage[] } {
        const payment = this.payments.get(uetr);
        return { messages: payment?.messages || [] };
    }

    getEvents(uetr: string): { uetr: string; events: MockEvent[] } {
        const payment = this.payments.get(uetr);
        return { uetr, events: payment?.events || [] };
    }

    list(): MockPayment[] {
        return Array.from(this.payments.values());
    }

    private getReasonDescription(code?: string): string | undefined {
        const descriptions: Record<string, string> = {
            "AB04": "Quote Expired - Exchange rate no longer valid",
            "TM01": "Timeout - Processing time limit exceeded",
            "DUPL": "Duplicate Payment - Transaction already exists",
            "AM04": "Insufficient Funds - Sender balance insufficient",
            "AM02": "Amount Limit Exceeded - Above max transfer limit",
            "BE23": "Invalid Proxy - Recipient identifier not found",
            "AC04": "Closed Account - Recipient account is closed",
            "RR04": "Regulatory Block - Transaction blocked by compliance",
        };
        return code ? descriptions[code] : undefined;
    }

    private generatePacs008Xml(params: { uetr: string; quoteId: string; exchangeRate: number; sourceAmount: number; sourceCurrency: string; destinationAmount: number; destinationCurrency: string; debtorName: string; debtorAccount: string; debtorAgentBic: string; creditorName: string; creditorAccount: string; creditorAgentBic: string }, timestamp: string): string {
        return `<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.13">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>NEXUS-${Date.now()}</MsgId>
      <CreDtTm>${timestamp}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <SttlmInf><SttlmMtd>CLRG</SttlmMtd></SttlmInf>
    </GrpHdr>
    <CdtTrfTxInf>
      <PmtId>
        <InstrId>INSTR-${Date.now()}</InstrId>
        <EndToEndId>E2E-${Date.now()}</EndToEndId>
        <UETR>${params.uetr}</UETR>
      </PmtId>
      <IntrBkSttlmAmt Ccy="${params.sourceCurrency}">${params.sourceAmount.toFixed(2)}</IntrBkSttlmAmt>
      <IntrBkSttlmDt>${timestamp.split('T')[0]}</IntrBkSttlmDt>
      <XchgRate>${params.exchangeRate}</XchgRate>
      <InstdAmt Ccy="${params.destinationCurrency}">${params.destinationAmount.toFixed(2)}</InstdAmt>
      <ChrgBr>SHAR</ChrgBr>
      <Dbtr><Nm>${params.debtorName}</Nm></Dbtr>
      <DbtrAcct><Id><Othr><Id>${params.debtorAccount}</Id></Othr></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BICFI>${params.debtorAgentBic}</BICFI></FinInstnId></DbtrAgt>
      <CdtrAgt><FinInstnId><BICFI>${params.creditorAgentBic}</BICFI></FinInstnId></CdtrAgt>
      <Cdtr><Nm>${params.creditorName}</Nm></Cdtr>
      <CdtrAcct><Id><Othr><Id>${params.creditorAccount}</Id></Othr></Id></CdtrAcct>
      <SplmtryData><Envlp><NxsQtId>${params.quoteId}</NxsQtId></Envlp></SplmtryData>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>`;
    }

    private generatePacs002Xml(params: { uetr: string; debtorAgentBic: string; creditorAgentBic: string }, status: string, reasonCode: string | undefined, timestamp: string): string {
        const statusInfo = status === "ACCC"
            ? `<TxSts>ACCC</TxSts>`
            : `<TxSts>RJCT</TxSts>
        <StsRsnInf><Rsn><Cd>${reasonCode || "NARR"}</Cd></Rsn></StsRsnInf>`;

        return `<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.002.001.12">
  <FIToFIPmtStsRpt>
    <GrpHdr>
      <MsgId>PACS002-${Date.now()}</MsgId>
      <CreDtTm>${timestamp}</CreDtTm>
    </GrpHdr>
    <TxInfAndSts>
      <OrgnlEndToEndId>E2E-${Date.now()}</OrgnlEndToEndId>
      <OrgnlUETR>${params.uetr}</OrgnlUETR>
      ${statusInfo}
      <InstgAgt><FinInstnId><BICFI>${params.debtorAgentBic}</BICFI></FinInstnId></InstgAgt>
      <InstdAgt><FinInstnId><BICFI>${params.creditorAgentBic}</BICFI></FinInstnId></InstdAgt>
    </TxInfAndSts>
  </FIToFIPmtStsRpt>
</Document>`;
    }
}

export const mockPaymentStore = new MockPaymentStore();

// ============================================================================
// DYNAMIC QUOTE GENERATION
// ============================================================================

export interface MockQuote {
    quoteId: string;
    fxpId: string;
    fxpName: string;
    sourceCurrency: string;
    destinationCurrency: string;
    exchangeRate: string;
    spreadBps: number;
    sourceInterbankAmount: string;
    destinationInterbankAmount: string;
    creditorAccountAmount: string;
    cappedToMaxAmount: boolean;
    expiresAt: string;
    fees: MockFeeBreakdown;
}

export interface MockFeeBreakdown {
    quoteId: string;
    marketRate: string;
    customerRate: string;
    appliedSpreadBps: string;
    recipientNetAmount: string;
    payoutGrossAmount: string;
    destinationPspFee: string;
    destinationCurrency: string;
    senderPrincipal: string;
    sourcePspFee: string;
    sourcePspFeeType: string;
    schemeFee: string;
    senderTotal: string;
    sourceCurrency: string;
    effectiveRate: string;
    totalCostPercent: string;
    quoteValidUntil: string;
}

export function generateMockQuotes(
    sourceCountry: string,
    destCountry: string,
    amount: number,
    amountType: "SOURCE" | "DESTINATION"
): MockQuote[] {
    const sourceCurrency = COUNTRY_CURRENCY[sourceCountry] || "SGD";
    const destCurrency = COUNTRY_CURRENCY[destCountry] || "IDR";

    const rateKey = `${sourceCurrency}_${destCurrency}`;
    const baseRate = FX_RATES[rateKey] || 1.0;

    // Generate 2-3 quotes from different FXPs with varying spreads
    const fxps = [
        { id: "NEXUSFXP1", name: "Nexus FXP Alpha", spreadBps: 50 },
        { id: "NEXUSFXP2", name: "Global FX Partners", spreadBps: 65 },
    ];

    return fxps.map((fxp, idx) => {
        const spreadRate = baseRate * (1 + fxp.spreadBps / 10000);

        let sourceAmount: number;
        let destAmount: number;

        if (amountType === "SOURCE") {
            sourceAmount = amount;
            destAmount = amount * spreadRate;
        } else {
            destAmount = amount;
            sourceAmount = amount / spreadRate;
        }

        // Calculate fees
        const sourcePspFee = sourceAmount * 0.005; // 0.5%
        const schemeFee = sourceAmount * 0.001; // 0.1%
        const destPspFee = destAmount * 0.0001; // Small destination fee
        const senderTotal = sourceAmount + sourcePspFee + schemeFee;
        const recipientNet = destAmount - destPspFee;
        const effectiveRate = recipientNet / senderTotal;
        const totalCostPercent = ((spreadRate - baseRate) / baseRate * 100) + 0.6; // spread + fees

        const quoteId = `quote-mock-${Date.now()}-${idx}`;
        const expiresAt = new Date(Date.now() + 600000).toISOString();

        return {
            quoteId,
            fxpId: fxp.id,
            fxpName: fxp.name,
            sourceCurrency,
            destinationCurrency: destCurrency,
            exchangeRate: spreadRate.toFixed(4),
            spreadBps: fxp.spreadBps,
            sourceInterbankAmount: sourceAmount.toFixed(2),
            destinationInterbankAmount: destAmount.toFixed(2),
            creditorAccountAmount: recipientNet.toFixed(2),
            cappedToMaxAmount: false,
            expiresAt,
            fees: {
                quoteId,
                marketRate: baseRate.toFixed(4),
                customerRate: spreadRate.toFixed(4),
                appliedSpreadBps: fxp.spreadBps.toString(),
                recipientNetAmount: recipientNet.toFixed(2),
                payoutGrossAmount: destAmount.toFixed(2),
                destinationPspFee: destPspFee.toFixed(2),
                destinationCurrency: destCurrency,
                senderPrincipal: sourceAmount.toFixed(2),
                sourcePspFee: sourcePspFee.toFixed(2),
                sourcePspFeeType: "DEDUCTED",
                schemeFee: schemeFee.toFixed(2),
                senderTotal: senderTotal.toFixed(2),
                sourceCurrency,
                effectiveRate: effectiveRate.toFixed(4),
                totalCostPercent: totalCostPercent.toFixed(2),
                quoteValidUntil: expiresAt
            }
        };
    });
}

export function getMockFeeBreakdown(quoteId: string): MockFeeBreakdown | null {
    // Check if this is a dynamically generated quote
    const cachedQuote = mockQuotesCache.get(quoteId);
    if (cachedQuote) return cachedQuote.fees;

    // Fallback to static quotes only if exact match exists
    // Do NOT fall back to mockQuotes[0] as it's hardcoded for THB
    const staticQuote = mockQuotes.find(q => q.quoteId === quoteId);
    return staticQuote?.fees || null;
}

// Cache for dynamically generated quotes (keyed by quoteId)
const mockQuotesCache = new Map<string, MockQuote>();

export function cacheMockQuote(quote: MockQuote): void {
    mockQuotesCache.set(quote.quoteId, quote);
}

// ============================================================================
// STATIC MOCK DATA (Fallback/Reference)
// ============================================================================

// Countries - matching production data
export const mockCountries = [
    {
        countryId: 1,
        countryCode: "SG",
        name: "Singapore",
        currencies: [
            { currencyCode: "SGD", maxAmount: "50000" }
        ],
        requiredMessageElements: { pacs008: [] }
    },
    {
        countryId: 2,
        countryCode: "TH",
        name: "Thailand",
        currencies: [
            { currencyCode: "THB", maxAmount: "1500000" }
        ],
        requiredMessageElements: { pacs008: [] }
    },
    {
        countryId: 3,
        countryCode: "MY",
        name: "Malaysia",
        currencies: [
            { currencyCode: "MYR", maxAmount: "200000" }
        ],
        requiredMessageElements: { pacs008: [] }
    },
    {
        countryId: 4,
        countryCode: "ID",
        name: "Indonesia",
        currencies: [
            { currencyCode: "IDR", maxAmount: "200000000" }
        ],
        requiredMessageElements: { pacs008: [] }
    },
    {
        countryId: 5,
        countryCode: "PH",
        name: "Philippines",
        currencies: [
            { currencyCode: "PHP", maxAmount: "5000000" }
        ],
        requiredMessageElements: { pacs008: [] }
    },
    {
        countryId: 6,
        countryCode: "IN",
        name: "India",
        currencies: [
            { currencyCode: "INR", maxAmount: "10000000" }
        ],
        requiredMessageElements: { pacs008: [] }
    }
];

// Pre-seeded PSPs
export const mockPSPs = [
    { psp_id: "psp-dbs-sg", bic: "DBSGSGSG", name: "DBS Bank Singapore", country_code: "SG", fee_percent: 0.5 },
    { psp_id: "psp-uob-sg", bic: "UOVBSGSG", name: "UOB Singapore", country_code: "SG", fee_percent: 0.45 },
    { psp_id: "psp-bkk-th", bic: "BKKBTHBK", name: "Bangkok Bank", country_code: "TH", fee_percent: 0.4 },
    { psp_id: "psp-kbank-th", bic: "KASITHBK", name: "Kasikornbank", country_code: "TH", fee_percent: 0.35 },
    { psp_id: "psp-mayb-my", bic: "MAYBMYKL", name: "Maybank Malaysia", country_code: "MY", fee_percent: 0.5 },
    { psp_id: "psp-mandiri-id", bic: "BMRIIDJA", name: "Bank Mandiri", country_code: "ID", fee_percent: 0.4 },
];

// Pre-seeded IPS
export const mockIPSOperators = [
    { ips_id: "ips-fast", name: "Singapore FAST", country_code: "SG", clearing_system_id: "SGIPSOPS", max_amount: 200000, currency_code: "SGD" },
    { ips_id: "ips-promptpay", name: "Thailand PromptPay", country_code: "TH", clearing_system_id: "THIPSOPS", max_amount: 2000000, currency_code: "THB" },
    { ips_id: "ips-duitnow", name: "Malaysia DuitNow", country_code: "MY", clearing_system_id: "MYIPSOPS", max_amount: 500000, currency_code: "MYR" },
    { ips_id: "ips-bi-fast", name: "Indonesia BI-FAST", country_code: "ID", clearing_system_id: "IDIPSOPS", max_amount: 250000000, currency_code: "IDR" },
];

// Pre-seeded PDOs
export const mockPDOs = [
    { pdo_id: "pdo-sg", name: "PayNow Directory (SG)", country_code: "SG", supported_proxy_types: ["MBNO", "NRIC", "UEN"] },
    { pdo_id: "pdo-th", name: "PromptPay Directory (TH)", country_code: "TH", supported_proxy_types: ["MBNO", "IDNO", "TXID"] },
    { pdo_id: "pdo-my", name: "DuitNow Directory (MY)", country_code: "MY", supported_proxy_types: ["MBNO", "NRIC", "PSPT"] },
    { pdo_id: "pdo-id", name: "QRIS Directory (ID)", country_code: "ID", supported_proxy_types: ["MBNO", "NIK", "QRIS"] },
];

// Sample FX Rates (static reference)
export const mockFXRates = [
    { rateId: "rate-1", sourceCurrency: "SGD", destinationCurrency: "THB", rate: 25.85, spreadBps: 50, fxpName: "Nexus FXP Alpha", validUntil: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" },
    { rateId: "rate-2", sourceCurrency: "SGD", destinationCurrency: "MYR", rate: 3.45, spreadBps: 45, fxpName: "Nexus FXP Alpha", validUntil: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" },
    { rateId: "rate-3", sourceCurrency: "SGD", destinationCurrency: "IDR", rate: 11423.50, spreadBps: 50, fxpName: "Nexus FXP Alpha", validUntil: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" },
] as any[];

// Sample Payments (static reference - for initial Explorer data)
export const mockPayments = [
    {
        uetr: "91398cbd-0838-453f-b2c7-536e829f2b8e",
        quoteId: "quote-demo-1",
        sourcePspBic: "DBSGSGSG",
        destinationPspBic: "BMRIIDJA",
        debtorName: "John Tan",
        debtorAccount: "12345678",
        creditorName: "Budi Santoso",
        creditorAccount: "87654321",
        sourceCurrency: "SGD",
        destinationCurrency: "IDR",
        sourceAmount: 8.75,
        exchangeRate: "11423.50",
        status: "ACCC",
        createdAt: "2026-02-04T10:30:00Z",
        initiated_at: "2026-02-04T10:30:00Z"
    }
];

// Sample Liquidity Balances
export const mockLiquidityBalances = [
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "SGD", totalBalance: 5000000, reservedAmount: 125000, availableBalance: 4875000, status: "ACTIVE" },
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "THB", totalBalance: 150000000, reservedAmount: 3500000, availableBalance: 146500000, status: "ACTIVE" },
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "MYR", totalBalance: 15000000, reservedAmount: 450000, availableBalance: 14550000, status: "ACTIVE" },
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "IDR", totalBalance: 50000000000, reservedAmount: 1000000000, availableBalance: 49000000000, status: "ACTIVE" },
];

// Static quotes (fallback)
export const mockQuotes = [
    {
        quoteId: "quote-demo-1",
        fxpId: "NEXUSFXP1",
        fxpName: "Nexus FXP Alpha",
        sourceCurrency: "SGD",
        destinationCurrency: "THB",
        exchangeRate: "25.85",
        spreadBps: 50,
        sourceInterbankAmount: "1000.00",
        destinationInterbankAmount: "25850.00",
        creditorAccountAmount: "25850.00",
        cappedToMaxAmount: false,
        expiresAt: new Date(Date.now() + 600000).toISOString(),
        fees: {
            quoteId: "quote-demo-1",
            marketRate: "25.80",
            customerRate: "25.85",
            appliedSpreadBps: "50",
            recipientNetAmount: "25850.00",
            payoutGrossAmount: "25851.50",
            destinationPspFee: "1.50",
            destinationCurrency: "THB",
            senderPrincipal: "1000.00",
            sourcePspFee: "0.50",
            sourcePspFeeType: "DEDUCTED",
            schemeFee: "0.10",
            senderTotal: "1000.60",
            sourceCurrency: "SGD",
            effectiveRate: "25.83",
            totalCostPercent: "0.4",
            quoteValidUntil: new Date(Date.now() + 600000).toISOString()
        }
    },
];

// Mock Actors for Mesh page
export const mockActors = [
    { bic: "DBSGSGSG", name: "DBS Bank Singapore", actorType: "PSP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "UOVBSGSG", name: "UOB Singapore", actorType: "PSP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "BKKBTHBK", name: "Bangkok Bank", actorType: "PSP" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "BMRIIDJA", name: "Bank Mandiri", actorType: "PSP" as const, countryCode: "ID", status: "ACTIVE" },
    { bic: "MAYBMYKL", name: "Maybank Malaysia", actorType: "PSP" as const, countryCode: "MY", status: "ACTIVE" },
    { bic: "SGIPSOPS", name: "Singapore FAST", actorType: "IPS" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "THIPSOPS", name: "Thailand PromptPay", actorType: "IPS" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "MYIPSOPS", name: "Malaysia DuitNow", actorType: "IPS" as const, countryCode: "MY", status: "ACTIVE" },
    { bic: "IDIPSOPS", name: "Indonesia BI-FAST", actorType: "IPS" as const, countryCode: "ID", status: "ACTIVE" },
    { bic: "NEXUSFXP1", name: "Nexus FXP Alpha", actorType: "FXP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "NEXUSSAP1", name: "Nexus SAP Singapore", actorType: "SAP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "NEXUSSAP2", name: "Nexus SAP Thailand", actorType: "SAP" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "PDOSGOPS", name: "PayNow Directory", actorType: "PDO" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "PDOTHOPS", name: "PromptPay Directory", actorType: "PDO" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "PDOIDOPS", name: "QRIS Directory", actorType: "PDO" as const, countryCode: "ID", status: "ACTIVE" },
];

// Demo mode indicator
export const DEMO_BANNER_MESSAGE = `
🎮 **GitHub Pages Demo Mode**

This is a static demo of the Nexus Sandbox dashboard. 
For the full interactive experience with real API calls:

\`\`\`bash
git clone https://github.com/siva-sub/nexus-sandbox.git
docker compose -f docker-compose.lite.yml up -d
\`\`\`

Then visit http://localhost:8080
`;
