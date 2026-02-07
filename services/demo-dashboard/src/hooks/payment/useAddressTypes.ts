/**
 * useAddressTypes Hook
 * 
 * Fetches and manages dynamic address input fields based on destination country.
 * Extracted from Payment.tsx to improve maintainability and testability.
 */

import { useState, useCallback, useEffect } from "react";
import { notifications } from "@mantine/notifications";
import { getAddressTypes } from "../../services/api";
import type { AddressTypeWithInputs } from "../../types";

interface UseAddressTypesParams {
    destCountry: string | null;
}

export function useAddressTypes({ destCountry }: UseAddressTypesParams) {
    const [addressTypes, setAddressTypes] = useState<(AddressTypeWithInputs & { value: string; label: string })[]>([]);
    const [selectedProxyType, setSelectedProxyType] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Fetch address types when destination country changes
    const fetchAddressTypes = useCallback(async () => {
        if (!destCountry) return;

        setLoading(true);
        try {
            const data = await getAddressTypes(destCountry);
            setAddressTypes(data.addressTypes.map((t) => ({
                ...t,
                value: t.addressTypeId,
                label: t.addressTypeName,
            } as AddressTypeWithInputs & { value: string; label: string })));
        } catch {
            notifications.show({
                title: "Address Types Error",
                message: "Could not fetch address types. Check backend connection.",
                color: "orange",
            });
        } finally {
            setLoading(false);
        }
    }, [destCountry]);

    // Automatically fetch when country changes
    useEffect(() => {
        if (destCountry) {
            fetchAddressTypes();
            setSelectedProxyType(null); // Reset selection
        }
    }, [destCountry, fetchAddressTypes]);

    // Get the inputs for the currently selected proxy type
    const selectedTypeInputs = addressTypes.find(t => t.addressTypeId === selectedProxyType)?.inputs || [];

    return {
        addressTypes,
        selectedProxyType,
        setSelectedProxyType,
        selectedTypeInputs,
        loading,
        fetchAddressTypes,
    };
}
