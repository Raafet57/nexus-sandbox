import {
    Card,
    Stack,
    Title,
    Group,
    Text,
    Table,
    Badge,
    Button,
    Box,
    Progress,
} from "@mantine/core";
import { IconCoin, IconCheck } from "@tabler/icons-react";
import type { Quote, FeeBreakdown } from "../../types";

export interface QuoteSelectorProps {
    quotes: Quote[];
    selectedQuote: Quote | null;
    feeBreakdown: FeeBreakdown | null;
    now: number;
    onQuoteSelect: (quote: Quote) => void;
}

function formatCurrency(amount: number, currency: string): string {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
    }).format(amount);
}

function getQuoteTimeRemaining(expiresAt: string, now: number): { 
    remaining: number; 
    percentage: number; 
    isExpired: boolean 
} {
    const expiresAtMs = new Date(expiresAt).getTime();
    const remaining = Math.max(0, Math.floor((expiresAtMs - now) / 1000));
    const totalDuration = 60;
    const percentage = Math.max(0, Math.min(100, (remaining / totalDuration) * 100));
    const isExpired = remaining <= 0;
    return { remaining, percentage, isExpired };
}

export function QuoteSelector({
    quotes,
    selectedQuote,
    feeBreakdown,
    now,
    onQuoteSelect,
}: QuoteSelectorProps) {
    if (quotes.length === 0) {
        return (
            <Card withBorder radius="md" p="xl">
                <Stack align="center" gap="md">
                    <IconCoin size={48} color="var(--mantine-color-dimmed)" />
                    <Title order={4} c="dimmed">Quoting</Title>
                    <Text c="dimmed" ta="center">
                        Select a destination country to retrieve live multi-provider quotes via Nexus FXP Aggregation.
                    </Text>
                </Stack>
            </Card>
        );
    }

    return (
        <Card withBorder radius="md" p="xl">
            <Stack gap="md">
                <Group justify="space-between">
                    <Title order={5}>
                        <Group gap="xs">
                            <IconCoin size={20} color="var(--mantine-color-yellow-filled)" />
                            FX Quotes
                        </Group>
                    </Title>
                    <Badge color="blue" variant="light">
                        {quotes.length} Provider{quotes.length > 1 ? "s" : ""}
                    </Badge>
                </Group>

                <Table highlightOnHover>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>Provider</Table.Th>
                            <Table.Th>Rate</Table.Th>
                            <Table.Th>You Send</Table.Th>
                            <Table.Th>They Receive</Table.Th>
                            <Table.Th>Expires</Table.Th>
                            <Table.Th></Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {quotes.map((quote) => {
                            const { remaining, percentage, isExpired } = getQuoteTimeRemaining(quote.expiresAt, now);
                            const isSelected = selectedQuote?.quoteId === quote.quoteId;

                            return (
                                <Table.Tr 
                                    key={quote.quoteId}
                                    style={{ 
                                        opacity: isExpired ? 0.5 : 1,
                                        backgroundColor: isSelected ? "var(--mantine-color-blue-light)" : undefined
                                    }}
                                >
                                    <Table.Td>
                                        <Text fw={500}>{quote.fxpName || quote.fxpCode}</Text>
                                        <Text size="xs" c="dimmed">{quote.fxpCode}</Text>
                                    </Table.Td>
                                    <Table.Td>
                                        <Text ff="monospace">{quote.exchangeRate.toFixed(4)}</Text>
                                        <Text size="xs" c="dimmed">+{quote.spreadBps || 0}bps</Text>
                                    </Table.Td>
                                    <Table.Td>
                                        <Text fw={500}>{formatCurrency(quote.sourceAmount, quote.sourceCurrency)}</Text>
                                    </Table.Td>
                                    <Table.Td>
                                        <Text fw={500} c="green">{formatCurrency(quote.destinationAmount, quote.destinationCurrency)}</Text>
                                    </Table.Td>
                                    <Table.Td>
                                        <Box w={80}>
                                            <Progress 
                                                value={percentage} 
                                                color={isExpired ? "red" : percentage < 30 ? "orange" : "green"}
                                                size="sm"
                                            />
                                            <Text size="xs" c={isExpired ? "red" : "dimmed"} ta="center">
                                                {isExpired ? "Expired" : `${remaining}s`}
                                            </Text>
                                        </Box>
                                    </Table.Td>
                                    <Table.Td>
                                        <Button
                                            size="xs"
                                            variant={isSelected ? "filled" : "light"}
                                            color={isSelected ? "green" : "blue"}
                                            onClick={() => onQuoteSelect(quote)}
                                            disabled={isExpired}
                                            leftSection={isSelected ? <IconCheck size={14} /> : undefined}
                                        >
                                            {isSelected ? "Selected" : "Select"}
                                        </Button>
                                    </Table.Td>
                                </Table.Tr>
                            );
                        })}
                    </Table.Tbody>
                </Table>

                {feeBreakdown && selectedQuote && (
                    <Card withBorder radius="sm" p="md" bg="var(--mantine-color-dark-6)">
                        <Stack gap="xs">
                            <Text size="sm" fw={500}>Pre-Transaction Disclosure</Text>
                            <Group justify="space-between">
                                <Text size="sm" c="dimmed">Send Amount:</Text>
                                <Text size="sm">{formatCurrency(feeBreakdown.sendAmount, feeBreakdown.sendCurrency)}</Text>
                            </Group>
                            <Group justify="space-between">
                                <Text size="sm" c="dimmed">FX Rate:</Text>
                                <Text size="sm">{feeBreakdown.exchangeRate.toFixed(4)}</Text>
                            </Group>
                            <Group justify="space-between">
                                <Text size="sm" c="dimmed">Total Fees:</Text>
                                <Text size="sm" c="orange">{formatCurrency(feeBreakdown.totalFees, feeBreakdown.sendCurrency)}</Text>
                            </Group>
                            <Group justify="space-between">
                                <Text size="sm" fw={500}>Recipient Gets:</Text>
                                <Text size="sm" fw={500} c="green">
                                    {formatCurrency(feeBreakdown.receiveAmount, feeBreakdown.receiveCurrency)}
                                </Text>
                            </Group>
                        </Stack>
                    </Card>
                )}
            </Stack>
        </Card>
    );
}
