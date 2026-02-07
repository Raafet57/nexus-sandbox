/**
 * usePaymentLifecycle Hook
 * 
 * Manages the 17-step payment lifecycle tracking for Nexus payments.
 * Extracted from Payment.tsx to improve maintainability and testability.
 */

import { useState, useCallback } from "react";

// 17-Step Lifecycle Definition (from Nexus documentation)
export interface LifecycleStep {
    id: number;
    phase: number;
    name: string;
    apiCall: string;
    isoMessage: string;
    status: "pending" | "active" | "completed" | "error";
    timestamp?: string;
    details?: string;
}

// Initial step definitions
const LIFECYCLE_STEPS: Omit<LifecycleStep, "status" | "timestamp" | "details">[] = [
    { id: 1, phase: 1, name: "Select Country", apiCall: "GET /countries", isoMessage: "-" },
    { id: 2, phase: 1, name: "Define Amount", apiCall: "Validation", isoMessage: "-" },
    { id: 3, phase: 2, name: "Request Quotes", apiCall: "GET /quotes", isoMessage: "-" },
    { id: 4, phase: 2, name: "Rate Improvements", apiCall: "GET /rates", isoMessage: "-" },
    { id: 5, phase: 2, name: "Compare Offers", apiCall: "Calculation", isoMessage: "-" },
    { id: 6, phase: 2, name: "Lock Quote", apiCall: "Selection", isoMessage: "-" },
    { id: 7, phase: 3, name: "Enter Address", apiCall: "GET /address-types", isoMessage: "-" },
    { id: 8, phase: 3, name: "Resolve Proxy", apiCall: "POST /addressing/resolve", isoMessage: "acmt.023/024" },
    { id: 9, phase: 3, name: "Sanctions Check", apiCall: "Internal Check", isoMessage: "-" },
    { id: 10, phase: 3, name: "Pre-Transaction Disclosure", apiCall: "GET /fees-and-amounts", isoMessage: "-" },
    { id: 11, phase: 3, name: "Sender Approval", apiCall: "User Confirmation", isoMessage: "-" },
    { id: 12, phase: 4, name: "Debtor Authorization", apiCall: "Bank Auth", isoMessage: "-" },
    { id: 13, phase: 4, name: "Get Intermediaries", apiCall: "GET /intermediary-agents", isoMessage: "-" },
    { id: 14, phase: 4, name: "Construct pacs.008", apiCall: "Message Build", isoMessage: "pacs.008" },
    { id: 15, phase: 4, name: "Submit to IPS", apiCall: "POST /iso20022/pacs008", isoMessage: "pacs.008" },
    { id: 16, phase: 4, name: "Settlement Chain", apiCall: "Nexus → Dest IPS → SAP", isoMessage: "-" },
    { id: 17, phase: 5, name: "Accept & Notify", apiCall: "Response Processing", isoMessage: "pacs.002" },
];

export const PHASE_NAMES: Record<number, string> = {
    1: "Payment Setup",
    2: "Quoting",
    3: "Addressing & Compliance",
    4: "Processing & Settlement",
    5: "Completion",
};

export interface StepsByPhase {
    phase: number;
    name: string;
    steps: LifecycleStep[];
}

export function usePaymentLifecycle() {
    const [steps, setSteps] = useState<LifecycleStep[]>(
        LIFECYCLE_STEPS.map((s) => ({ ...s, status: "pending" as const }))
    );

    // Advance lifecycle to a specific step
    const advanceStep = useCallback((stepId: number, details?: string) => {
        setSteps((prev) =>
            prev.map((s) => ({
                ...s,
                status: s.id < stepId ? "completed" : s.id === stepId ? "active" : "pending",
                timestamp: s.id === stepId ? new Date().toLocaleTimeString() : s.timestamp,
                details: s.id === stepId ? details : s.details,
            }))
        );
    }, []);

    // Mark a specific step as completed
    const markStepComplete = useCallback((stepId: number, details?: string) => {
        setSteps((prev) =>
            prev.map((s) => ({
                ...s,
                status: s.id === stepId ? "completed" : s.status,
                timestamp: s.id === stepId ? new Date().toLocaleTimeString() : s.timestamp,
                details: s.id === stepId ? details : s.details,
            }))
        );
    }, []);

    // Mark a specific step as error
    const markStepError = useCallback((stepId: number, error: string) => {
        setSteps((prev) =>
            prev.map((s) => ({
                ...s,
                status: s.id === stepId ? "error" : s.status,
                timestamp: s.id === stepId ? new Date().toLocaleTimeString() : s.timestamp,
                details: s.id === stepId ? error : s.details,
            }))
        );
    }, []);

    // Reset all steps to pending
    const resetSteps = useCallback(() => {
        setSteps(LIFECYCLE_STEPS.map((s) => ({ ...s, status: "pending" as const })));
    }, []);

    // Group steps by phase for UI rendering
    const stepsByPhase: StepsByPhase[] = Object.entries(PHASE_NAMES).map(([phase, name]) => ({
        phase: Number(phase),
        name,
        steps: steps.filter((s) => s.phase === Number(phase)),
    }));

    return {
        steps,
        stepsByPhase,
        advanceStep,
        markStepComplete,
        markStepError,
        resetSteps,
        setSteps, // For direct manipulation if needed
    };
}
