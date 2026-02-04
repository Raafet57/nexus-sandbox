// Mock Data for GitHub Pages Static Demo
// This file provides static data when the app runs without a backend

export const MOCK_ENABLED = import.meta.env.VITE_MOCK_DATA === "true" || import.meta.env.VITE_GITHUB_PAGES === "true";

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
    { psp_id: "psp-mayb-my", bic: "MAYBMYKL", name: "Maybank Malaysia", country_code: "MY", fee_percent: 0.5 }
];

// Pre-seeded IPS
export const mockIPSOperators = [
    { ips_id: "ips-fast", name: "Singapore FAST", country_code: "SG", clearing_system_id: "SGIPSOPS", max_amount: 200000, currency_code: "SGD" },
    { ips_id: "ips-promptpay", name: "Thailand PromptPay", country_code: "TH", clearing_system_id: "THIPSOPS", max_amount: 2000000, currency_code: "THB" },
    { ips_id: "ips-duitnow", name: "Malaysia DuitNow", country_code: "MY", clearing_system_id: "MYIPSOPS", max_amount: 500000, currency_code: "MYR" }
];

// Pre-seeded PDOs
export const mockPDOs = [
    { pdo_id: "pdo-sg", name: "PayNow Directory (SG)", country_code: "SG", supported_proxy_types: ["MBNO", "NRIC", "UEN"] },
    { pdo_id: "pdo-th", name: "PromptPay Directory (TH)", country_code: "TH", supported_proxy_types: ["MBNO", "IDNO", "TXID"] },
    { pdo_id: "pdo-my", name: "DuitNow Directory (MY)", country_code: "MY", supported_proxy_types: ["MBNO", "NRIC", "PSPT"] }
];

// Sample FX Rates
export const mockFXRates = [
    { rateId: "rate-1", sourceCurrency: "SGD", destinationCurrency: "THB", rate: 25.85, spreadBps: 50, fxpName: "Nexus FXP Alpha", validUntil: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" },
    { rateId: "rate-2", sourceCurrency: "SGD", destinationCurrency: "MYR", rate: 3.45, spreadBps: 45, fxpName: "Nexus FXP Alpha", validUntil: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" },
    { rateId: "rate-3", sourceCurrency: "THB", destinationCurrency: "SGD", rate: 0.0387, spreadBps: 50, fxpName: "Nexus FXP Alpha", validUntil: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" }
] as any[];

// Sample Payments (for explorer)
export const mockPayments = [
    {
        uetr: "91398cbd-0838-453f-b2c7-536e829f2b8e",
        quoteId: "quote-demo-1",
        sourcePspBic: "DBSGSGSG",
        destinationPspBic: "BKKBTHBK",
        debtorName: "John Tan",
        debtorAccount: "12345678",
        creditorName: "Somchai Thai",
        creditorAccount: "87654321",
        sourceCurrency: "SGD",
        destinationCurrency: "THB",
        sourceAmount: 1000,
        exchangeRate: "25.85",
        status: "ACCC",
        createdAt: "2026-02-04T10:30:00Z",
        initiated_at: "2026-02-04T10:30:00Z"
    }
];

// Sample Liquidity Balances
export const mockLiquidityBalances = [
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "SGD", totalBalance: 5000000, reservedAmount: 125000, availableBalance: 4875000, status: "ACTIVE" },
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "THB", totalBalance: 150000000, reservedAmount: 3500000, availableBalance: 146500000, status: "ACTIVE" },
    { fxpId: "NEXUSFXP1", fxpName: "Nexus FXP Alpha", currency: "MYR", totalBalance: 15000000, reservedAmount: 450000, availableBalance: 14550000, status: "ACTIVE" }
];

// Sample Quotes - includes SGD→THB, SGD→MYR, SGD→IDR for demo corridors
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
    {
        quoteId: "quote-demo-2",
        fxpId: "NEXUSFXP1",
        fxpName: "Nexus FXP Alpha",
        sourceCurrency: "SGD",
        destinationCurrency: "IDR",
        exchangeRate: "11423.50",
        spreadBps: 45,
        sourceInterbankAmount: "8.75",
        destinationInterbankAmount: "100000.00",
        creditorAccountAmount: "100000.00",
        cappedToMaxAmount: false,
        expiresAt: new Date(Date.now() + 600000).toISOString(),
        fees: {
            quoteId: "quote-demo-2",
            marketRate: "11420.00",
            customerRate: "11423.50",
            appliedSpreadBps: "45",
            recipientNetAmount: "100000.00",
            payoutGrossAmount: "100010.00",
            destinationPspFee: "10.00",
            destinationCurrency: "IDR",
            senderPrincipal: "8.75",
            sourcePspFee: "0.05",
            sourcePspFeeType: "DEDUCTED",
            schemeFee: "0.01",
            senderTotal: "8.81",
            sourceCurrency: "SGD",
            effectiveRate: "11350.74",
            totalCostPercent: "0.45",
            quoteValidUntil: new Date(Date.now() + 600000).toISOString()
        }
    },
    {
        quoteId: "quote-demo-3",
        fxpId: "NEXUSFXP1",
        fxpName: "Nexus FXP Alpha",
        sourceCurrency: "SGD",
        destinationCurrency: "MYR",
        exchangeRate: "3.45",
        spreadBps: 40,
        sourceInterbankAmount: "1000.00",
        destinationInterbankAmount: "3450.00",
        creditorAccountAmount: "3450.00",
        cappedToMaxAmount: false,
        expiresAt: new Date(Date.now() + 600000).toISOString(),
        fees: {
            quoteId: "quote-demo-3",
            marketRate: "3.44",
            customerRate: "3.45",
            appliedSpreadBps: "40",
            recipientNetAmount: "3450.00",
            payoutGrossAmount: "3451.00",
            destinationPspFee: "1.00",
            destinationCurrency: "MYR",
            senderPrincipal: "1000.00",
            sourcePspFee: "0.50",
            sourcePspFeeType: "DEDUCTED",
            schemeFee: "0.10",
            senderTotal: "1000.60",
            sourceCurrency: "SGD",
            effectiveRate: "3.44",
            totalCostPercent: "0.35",
            quoteValidUntil: new Date(Date.now() + 600000).toISOString()
        }
    }
];

// Mock Actors for Mesh page
export const mockActors = [
    { bic: "DBSGSGSG", name: "DBS Bank Singapore", actorType: "PSP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "UOVBSGSG", name: "UOB Singapore", actorType: "PSP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "BKKBTHBK", name: "Bangkok Bank", actorType: "PSP" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "MAYBMYKL", name: "Maybank Malaysia", actorType: "PSP" as const, countryCode: "MY", status: "ACTIVE" },
    { bic: "SGIPSOPS", name: "Singapore FAST", actorType: "IPS" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "THIPSOPS", name: "Thailand PromptPay", actorType: "IPS" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "MYIPSOPS", name: "Malaysia DuitNow", actorType: "IPS" as const, countryCode: "MY", status: "ACTIVE" },
    { bic: "NEXUSFXP1", name: "Nexus FXP Alpha", actorType: "FXP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "NEXUSSAP1", name: "Nexus SAP Singapore", actorType: "SAP" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "NEXUSSAP2", name: "Nexus SAP Thailand", actorType: "SAP" as const, countryCode: "TH", status: "ACTIVE" },
    { bic: "PDOSGOPS", name: "PayNow Directory", actorType: "PDO" as const, countryCode: "SG", status: "ACTIVE" },
    { bic: "PDOTHOPS", name: "PromptPay Directory", actorType: "PDO" as const, countryCode: "TH", status: "ACTIVE" },
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
