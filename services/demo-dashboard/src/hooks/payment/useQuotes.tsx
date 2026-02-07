/**
 * useQuotes Hook
 * 
 * Manages FX quote fetching, selection, and expiration handling.
 * Extracted from Payment.tsx to improve maintainability and testability.
 */

import { useState, useCallback, useEffect } from "react";
import { notifications } from "@mantine/notifications";
import { IconAlertCircle } from "@tabler/icons-react";
import { getQuotes, getPreTransactionDisclosure, getIntermediaryAgents } from "../../services/api";
import type { Quote, FeeBreakdown, IntermediaryAgentsResponse, Country } from "../../types";

interface UseQuotesParams {
    sourceCountry: string | null;
    destCountry: string | null;
    countries: Country[];
    amount: number | string;
    amountType: "SOURCE" | "DESTINATION";
    sourceFeeType?: "INVOICED" | "DEDUCTED";
    onStepAdvance?: (stepId: number, details?: string) => void;
}

export function useQuotes({
    sourceCountry,
    destCountry,
    countries,
    amount,
    amountType,
    sourceFeeType = "INVOICED",
    onStepAdvance,
}: UseQuotesParams) {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
    const [feeBreakdown, setFeeBreakdown] = useState<FeeBreakdown | null>(null);
    const [intermediaries, setIntermediaries] = useState<IntermediaryAgentsResponse | null>(null);
    const [loading] = useState(false);
    const [now, setNow] = useState(Date.now());

    // Ticker for quote expiration
    useEffect(() => {
        const timer = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(timer);
    }, []);

    // Fetch quotes when parameters change
    const fetchQuotes = useCallback(async () => {
        if (!sourceCountry || !destCountry || !amount) return;

        try {
            const sCountry = countries.find(c => c.countryCode === sourceCountry);
            const dCountry = countries.find(c => c.countryCode === destCountry);

            if (!sCountry || !dCountry) return;

            const sourceCcy = sCountry.currencies[0].currencyCode;
            const destCcy = dCountry.currencies[0].currencyCode;

            const data = await getQuotes(
                sourceCountry,
                sourceCcy,
                destCountry,
                destCcy,
                Number(amount),
                amountType
            );
            setQuotes(data.quotes);
        } catch {
            notifications.show({
                title: "Quotes Unavailable",
                message: "Could not fetch FX quotes. Ensure FX are seeded in database.",
                color: "orange",
            });
        }
    }, [sourceCountry, destCountry, countries, amount, amountType]);

    // Handle quote selection with fee breakdown and intermediary fetching
    const selectQuote = useCallback(async (quote: Quote) => {
        setSelectedQuote(quote);
        onStepAdvance?.(6);

        // Fetch fee breakdown (Pre-Transaction Disclosure)
        try {
            const fees = await getPreTransactionDisclosure(quote.quoteId, sourceFeeType);
            setFeeBreakdown(fees);
            onStepAdvance?.(10);
        } catch {
            notifications.show({
                title: "Fee Calculation Error",
                message: "Could not calculate fee breakdown.",
                color: "orange",
            });
        }

        // Fetch intermediary agents
        try {
            const agents = await getIntermediaryAgents(quote.quoteId);
            setIntermediaries(agents);
            onStepAdvance?.(13);
        } catch {
            notifications.show({
                title: "Intermediary Error",
                message: "Could not fetch settlement routing.",
                color: "orange",
            });
        }
    }, [onStepAdvance, sourceFeeType]);

    // Quote expiration detection
    useEffect(() => {
        if (selectedQuote) {
            const expiresAt = new Date(selectedQuote.expiresAt).getTime();
            const isExpired = now >= expiresAt;

            if (isExpired) {
                // Clear the expired quote
                setSelectedQuote(null);
                setFeeBreakdown(null);
                setIntermediaries(null);

                // Show notification
                notifications.show({
                    title: "Quote Expired",
                    message: "Your selected quote has expired. Please select a new quote to continue.",
                    color: "orange",
                    icon: <IconAlertCircle size={ 16} />,
                    autoClose: 5000,
                });

    // Refresh quotes
    fetchQuotes();
    onStepAdvance?.(5);
}
        }
    }, [selectedQuote, now, fetchQuotes, onStepAdvance]);

// Clear selection when dependencies change
const clearSelection = useCallback(() => {
    setSelectedQuote(null);
    setFeeBreakdown(null);
    setIntermediaries(null);
}, []);

return {
    quotes,
    selectedQuote,
    feeBreakdown,
    intermediaries,
    loading,
    now,
    fetchQuotes,
    selectQuote,
    clearSelection,
    setQuotes,
};
}
