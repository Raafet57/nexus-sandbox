// API Types for Nexus Gateway

export interface CurrencyInfo {
    currencyCode: string;
    maxAmount: string;
}

export interface RequiredMessageElements {
    pacs008?: string[];
}

export interface Country {
    countryId: number;
    countryCode: string;
    name: string;
    currencies: CurrencyInfo[];
    requiredMessageElements: RequiredMessageElements;
}

export interface AddressTypeInput {
    label: {
        code: string;
        title: { [key: string]: string };
    };
    attributes: {
        name: string;
        type: string;
        pattern?: string;
        placeholder?: string;
        required: boolean;
        hidden: boolean;
    };
    iso20022Path?: string;
}

export interface AddressType {
    addressTypeId: string;
    addressTypeName: string;
    countryCode: string;
    inputs: AddressTypeInput[];
}

export interface Quote {
    quoteId: string;
    fxpId: string;
    fxpName: string;
    sourceCurrency: string;
    destinationCurrency: string;
    exchangeRate: string;
    spreadBps: number;
    sourceInterbankAmount: string;
    destinationInterbankAmount: string;
    creditorAccountAmount?: string;
    destinationPspFee?: string;
    cappedToMaxAmount: boolean;
    expiresAt: string;
}

export interface FeeBreakdown {
    quoteId: string;
    exchangeRate: string;
    quoteValidUntil: string;
    amountToDebit: string;
    amountToDebitCurrency: string;
    amountToCredit: string;
    amountToCreditCurrency: string;
    sourcePspFee: string;
    sourcePspFeeCurrency: string;
    sourcePspFeeType: "INVOICED" | "DEDUCTED";
    destinationPspFee: string;
    destinationPspFeeCurrency: string;
    fxSpreadBps: string;
    nexusSchemeFee: string;
    nexusSchemeFeeCurrency: string;
    effectiveExchangeRate: string;
    definedExchangeRate: string;
}

export interface ProxyResolutionResult {
    status: string;
    resolutionId?: string;
    accountName?: string;
    beneficiaryName?: string;
    accountNumber?: string;
    accountType?: string;
    bankName?: string;
    agentBic?: string;
    displayName?: string;
    verified: boolean;
    timestamp?: string;
}

export interface PaymentStatus {
    transactionId: string;
    status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "REJECTED";
    reasonCode?: string;
    reasonDescription?: string;
    timestamp: string;
}

export interface LifecycleStep {
    id: number;
    phase: number;
    name: string;
    apiCall: string;
    isoMessage?: string;
    status: "pending" | "active" | "completed" | "error";
    timestamp?: string;
    details?: string;
}

export interface FXRate {
    rateId: string;
    sourceCurrency: string;
    destinationCurrency: string;
    rate: number;
    spreadBps: number;
    fxpName: string;
    validUntil: string;
    status: "ACTIVE" | "EXPIRED" | "WITHDRAWN";
}

export interface LiquidityBalance {
    fxpId: string;
    fxpName: string;
    currency: string;
    totalBalance: number;
    reservedAmount: number;
    availableBalance: number;
    status: "ACTIVE" | "LOW" | "CRITICAL";
}

export interface Reservation {
    reservationId: string;
    quoteId: string;
    amount: number;
    currency: string;
    expiresAt: string;
    status: "ACTIVE" | "RELEASED" | "CONSUMED";
}

export interface IntermediaryAgentAccount {
    agentRole: string;
    bic: string;          // BIC of the SAP (e.g., FASTSGS0)
    accountNumber: string; // FXP account at SAP
    name: string;         // SAP name
}

export interface IntermediaryAgentsResponse {
    quoteId: string;
    intermediaryAgent1: IntermediaryAgentAccount;
    intermediaryAgent2: IntermediaryAgentAccount;
}
