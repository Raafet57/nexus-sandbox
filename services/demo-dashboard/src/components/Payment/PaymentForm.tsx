import {
    Card,
    Stack,
    Title,
    Group,
    Text,
    Select,
    SegmentedControl,
    NumberInput,
    TextInput,
    Button,
    Badge,
} from "@mantine/core";
import {
    IconCreditCard,
    IconUser,
    IconQrcode,
} from "@tabler/icons-react";
import type { Country, AddressTypeWithInputs, AddressTypeInputDetails } from "../../types";

export interface PaymentFormProps {
    countries: Country[];
    proxyTypes: AddressTypeWithInputs[];
    sourceCountry: string | null;
    selectedCountry: string | null;
    amount: number | string;
    amountType: "SOURCE" | "DESTINATION";
    selectedProxyType: string | null;
    recipientData: Record<string, string>;
    recipientErrors: Record<string, string | null>;
    loading: { qrScan: boolean; resolve: boolean };
    qrInput: string;
    onSourceCountryChange: (value: string | null) => void;
    onDestCountryChange: (value: string | null) => void;
    onAmountChange: (value: number | string) => void;
    onAmountTypeChange: (value: "SOURCE" | "DESTINATION") => void;
    onProxyTypeChange: (value: string | null) => void;
    onRecipientDataChange: (data: Record<string, string>) => void;
    onQrInputChange: (value: string) => void;
    onQrScan: () => void;
    onResolve: () => void;
}

export function PaymentForm({
    countries,
    proxyTypes,
    sourceCountry,
    selectedCountry,
    amount,
    amountType,
    selectedProxyType,
    recipientData,
    recipientErrors,
    loading,
    qrInput,
    onSourceCountryChange,
    onDestCountryChange,
    onAmountChange,
    onAmountTypeChange,
    onProxyTypeChange,
    onRecipientDataChange,
    onQrInputChange,
    onQrScan,
    onResolve,
}: PaymentFormProps) {
    const selectedCountryData = countries.find((c) => c.countryCode === selectedCountry);
    const sourceCountryData = countries.find((c) => c.countryCode === sourceCountry);

    const handleRecipientFieldChange = (fieldName: string, value: string) => {
        onRecipientDataChange({ ...recipientData, [fieldName]: value });
    };

    return (
        <Stack gap="md">
            <Card withBorder radius="md" p="xl" bg="var(--mantine-color-dark-7)">
                <Stack gap="md">
                    <Title order={5}>
                        <Group gap="xs">
                            <IconCreditCard size={20} color="var(--mantine-color-blue-filled)" />
                            Sender Information
                        </Group>
                    </Title>
                    <Select
                        label="Source Country"
                        placeholder="Select sending country"
                        data={countries.filter(c => c.countryCode && c.name).map((c) => ({ 
                            value: c.countryCode, 
                            label: c.name 
                        }))}
                        value={sourceCountry}
                        onChange={onSourceCountryChange}
                        searchable
                        allowDeselect={false}
                    />
                    <Stack gap="xs">
                        <Text size="sm" fw={500}>Amount Specification</Text>
                        <SegmentedControl
                            value={amountType}
                            onChange={(val) => onAmountTypeChange(val as "SOURCE" | "DESTINATION")}
                            data={[
                                { value: "SOURCE", label: "I want to send" },
                                { value: "DESTINATION", label: "Recipient gets" },
                            ]}
                            size="sm"
                        />
                    </Stack>
                    <NumberInput
                        label={amountType === "SOURCE"
                            ? `Amount to Send (${sourceCountryData?.currencies?.[0]?.currencyCode || "SGD"})`
                            : `Amount to Receive (${selectedCountryData?.currencies?.[0]?.currencyCode || "Destination Currency"})`}
                        value={Number(amount)}
                        onChange={onAmountChange}
                        min={1}
                        thousandSeparator=","
                        description={amountType === "SOURCE"
                            ? "System will calculate how much recipient receives"
                            : "System will calculate how much to debit from your account"}
                    />
                </Stack>
            </Card>

            <Card withBorder radius="md" p="xl">
                <Stack gap="md">
                    <Group justify="space-between">
                        <Title order={5}>
                            <Group gap="xs">
                                <IconUser size={20} color="var(--mantine-color-green-filled)" />
                                Recipient Information
                            </Group>
                        </Title>
                        <Badge color="grape" variant="light" leftSection={<IconQrcode size={12} />}>
                            EMVCo QR
                        </Badge>
                    </Group>

                    <TextInput
                        placeholder="Paste EMVCo QR data (SGQR, PromptPay, DuitNow)"
                        value={qrInput}
                        onChange={(e) => onQrInputChange(e.currentTarget.value)}
                        rightSection={
                            <Button
                                size="compact-xs"
                                variant="subtle"
                                onClick={onQrScan}
                                loading={loading.qrScan}
                            >
                                <IconQrcode size={14} />
                            </Button>
                        }
                    />

                    <Select
                        label="Destination Country"
                        placeholder="Select country"
                        data={countries.filter(c => c.countryCode && c.name).map((c) => ({ 
                            value: c.countryCode, 
                            label: c.name 
                        }))}
                        value={selectedCountry}
                        onChange={onDestCountryChange}
                        searchable
                    />

                    <Select
                        label="Target Proxy Type"
                        placeholder="Select method"
                        data={proxyTypes
                            .filter(t => (t.value || t.addressTypeId) && (t.label || t.addressTypeName))
                            .map(t => ({ 
                                value: t.value || t.addressTypeId, 
                                label: t.label || t.addressTypeName 
                            }))}
                        value={selectedProxyType}
                        onChange={onProxyTypeChange}
                        disabled={!selectedCountry}
                    />

                    {proxyTypes.find(t => t.value === selectedProxyType)?.inputs?.map((input: AddressTypeInputDetails) => (
                        <TextInput
                            key={input.fieldName}
                            label={input.displayLabel}
                            placeholder={`Enter ${input.displayLabel}`}
                            value={recipientData[input.fieldName] || ""}
                            onChange={(e) => handleRecipientFieldChange(input.fieldName, e.currentTarget.value)}
                            error={recipientErrors[input.fieldName]}
                            required={input.attributes?.required}
                        />
                    ))}

                    {selectedProxyType && (
                        <Button
                            onClick={onResolve}
                            loading={loading.resolve}
                            disabled={!selectedCountry || !selectedProxyType}
                        >
                            Resolve Recipient
                        </Button>
                    )}
                </Stack>
            </Card>
        </Stack>
    );
}
