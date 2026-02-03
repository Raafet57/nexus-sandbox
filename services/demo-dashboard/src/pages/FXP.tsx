import { useState } from "react";
import {
    Title,
    Card,
    Stack,
    Group,
    Select,
    NumberInput,
    Button,
    Text,
    Badge,
    Table,
    Tabs,
    SimpleGrid,
    ActionIcon,
    Tooltip,
    Anchor,
    Breadcrumbs,
    Alert,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
    IconArrowsExchange,
    IconPlus,
    IconRefresh,
    IconTrash,
    IconClock,
    IconInfoCircle,
} from "@tabler/icons-react";
import { useEffect } from "react";
import { DevDebugPanel } from "../components/DevDebugPanel";

function useCountdown(targetDate: string) {
    const [timeLeft, setTimeLeft] = useState<number>(0);

    useEffect(() => {
        const update = () => {
            const diff = Math.max(0, Math.floor((new Date(targetDate).getTime() - Date.now()) / 1000));
            setTimeLeft(diff);
        };
        update();
        const timer = setInterval(update, 1000);
        return () => clearInterval(timer);
    }, [targetDate]);

    return timeLeft;
}

function CountdownText({ targetDate }: { targetDate: string }) {
    const seconds = useCountdown(targetDate);
    return <Text size="sm">{seconds}s</Text>;
}


// Demo FX rates data
const DEMO_RATES = [
    { rateId: "R-001", sourceCurrency: "SGD", destinationCurrency: "THB", rate: 26.4521, spreadBps: 25, fxpName: "GlobalFX", validUntil: new Date(Date.now() + 60000).toISOString(), status: "ACTIVE" as const },
    { rateId: "R-002", sourceCurrency: "SGD", destinationCurrency: "MYR", rate: 3.4123, spreadBps: 30, fxpName: "GlobalFX", validUntil: new Date(Date.now() + 45000).toISOString(), status: "ACTIVE" as const },
    { rateId: "R-003", sourceCurrency: "SGD", destinationCurrency: "PHP", rate: 42.1234, spreadBps: 35, fxpName: "GlobalFX", validUntil: new Date(Date.now() + 30000).toISOString(), status: "ACTIVE" as const },
];

const CORRIDORS = [
    { value: "SGD-THB", label: "SGD → THB" },
    { value: "SGD-MYR", label: "SGD → MYR" },
    { value: "SGD-PHP", label: "SGD → PHP" },
    { value: "SGD-IDR", label: "SGD → IDR" },
];

export function FXPPage() {
    const [rates, setRates] = useState(DEMO_RATES);
    const [newRate, setNewRate] = useState({ corridor: "SGD-THB", rate: 0, spread: 25 });

    const handleSubmitRate = () => {
        const [source, dest] = newRate.corridor.split("-");
        setRates([
            ...rates,
            {
                rateId: `R-${Date.now()}`,
                sourceCurrency: source,
                destinationCurrency: dest,
                rate: newRate.rate,
                spreadBps: newRate.spread,
                fxpName: "Demo FXP",
                validUntil: new Date(Date.now() + 60000).toISOString(),
                status: "ACTIVE",
            },
        ]);
        notifications.show({ title: "Rate Submitted", message: `${newRate.corridor} @ ${newRate.rate}`, color: "green" });
    };

    const handleWithdraw = (rateId: string) => {
        setRates(rates.filter((r) => r.rateId !== rateId));
        notifications.show({ title: "Rate Withdrawn", message: `Removed ${rateId}`, color: "yellow" });
    };

    return (
        <Stack gap="md">
            <Breadcrumbs mb="xs">
                <Anchor href="/actors" size="xs">Actor Registry</Anchor>
                <Text size="xs" c="dimmed">FX Rate Management</Text>
            </Breadcrumbs>
            <Group justify="space-between">
                <Title order={2}>FX Provider (FXP) Dashboard</Title>
                <Group>
                    <Anchor href="/sap" size="sm">View Liquidity (SAP)</Anchor>
                    <Badge color="blue" variant="light" leftSection={<IconArrowsExchange size={14} />}>
                        FXP View
                    </Badge>
                </Group>
            </Group>

            {/* FXP Role Explanation Banner */}
            <Alert icon={<IconInfoCircle size={18} />} title="What is a Foreign Exchange Provider (FXP)?" color="blue" variant="light">
                <Text size="sm">
                    FXPs provide competitive FX rates for cross-border payments in Nexus. They submit rates to Nexus,
                    which are then offered to PSPs when requesting quotes. FXPs can offer tiered pricing based on
                    transaction amounts and PSP relationships.
                </Text>
                <Anchor href="https://docs.nexusglobalpayments.org/fx-provision/role-of-the-fx-provider" size="xs" mt="xs">
                    Learn more in Nexus Documentation →
                </Anchor>
            </Alert>

            <Tabs defaultValue="active">
                <Tabs.List>
                    <Tabs.Tab value="active">Active Rates</Tabs.Tab>
                    <Tabs.Tab value="submit">Submit Rate</Tabs.Tab>
                    <Tabs.Tab value="tiers">Tier Management</Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="active" pt="md">
                    <Card>
                        <Table>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>Corridor</Table.Th>
                                    <Table.Th>Rate</Table.Th>
                                    <Table.Th>Spread (bps)</Table.Th>
                                    <Table.Th>Expires</Table.Th>
                                    <Table.Th>Status</Table.Th>
                                    <Table.Th>Actions</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                {rates.map((rate) => (
                                    <Table.Tr key={rate.rateId}>
                                        <Table.Td>
                                            <Text fw={500}>{rate.sourceCurrency} → {rate.destinationCurrency}</Text>
                                        </Table.Td>
                                        <Table.Td>{rate.rate.toFixed(4)}</Table.Td>
                                        <Table.Td>{rate.spreadBps}</Table.Td>
                                        <Table.Td>
                                            <Group gap="xs">
                                                <IconClock size={14} />
                                                <CountdownText targetDate={rate.validUntil} />
                                            </Group>
                                        </Table.Td>

                                        <Table.Td>
                                            <Badge color="green" size="sm">{rate.status}</Badge>
                                        </Table.Td>
                                        <Table.Td>
                                            <Group gap="xs">
                                                <Tooltip label="Refresh">
                                                    <ActionIcon variant="subtle" color="blue">
                                                        <IconRefresh size={16} />
                                                    </ActionIcon>
                                                </Tooltip>
                                                <Tooltip label="Withdraw">
                                                    <ActionIcon variant="subtle" color="red" onClick={() => handleWithdraw(rate.rateId)}>
                                                        <IconTrash size={16} />
                                                    </ActionIcon>
                                                </Tooltip>
                                            </Group>
                                        </Table.Td>
                                    </Table.Tr>
                                ))}
                            </Table.Tbody>
                        </Table>
                    </Card>
                </Tabs.Panel>

                <Tabs.Panel value="submit" pt="md">
                    <SimpleGrid cols={{ base: 1, md: 2 }}>
                        <Card>
                            <Stack gap="md">
                                <Title order={5}>Submit New Rate</Title>
                                <Select
                                    label="Currency Corridor"
                                    data={CORRIDORS}
                                    value={newRate.corridor}
                                    onChange={(v) => setNewRate({ ...newRate, corridor: v || "SGD-THB" })}
                                />
                                <NumberInput
                                    label="Exchange Rate"
                                    value={newRate.rate}
                                    onChange={(v) => setNewRate({ ...newRate, rate: Number(v) })}
                                    decimalScale={4}
                                    min={0}
                                />
                                <NumberInput
                                    label="Spread (basis points)"
                                    value={newRate.spread}
                                    onChange={(v) => setNewRate({ ...newRate, spread: Number(v) })}
                                    min={0}
                                    max={100}
                                />
                                <Button leftSection={<IconPlus size={16} />} onClick={handleSubmitRate}>
                                    Submit Rate
                                </Button>
                            </Stack>
                        </Card>

                        <Card>
                            <Title order={5} mb="md">Rate Preview</Title>
                            <Stack gap="xs">
                                <Group justify="space-between">
                                    <Text c="dimmed">Corridor</Text>
                                    <Text fw={500}>{newRate.corridor}</Text>
                                </Group>
                                <Group justify="space-between">
                                    <Text c="dimmed">Rate</Text>
                                    <Text fw={500}>{newRate.rate.toFixed(4)}</Text>
                                </Group>
                                <Group justify="space-between">
                                    <Text c="dimmed">Spread</Text>
                                    <Text fw={500}>{newRate.spread} bps</Text>
                                </Group>
                                <Group justify="space-between">
                                    <Text c="dimmed">Valid for</Text>
                                    <Text fw={500}>600 seconds</Text>
                                </Group>

                            </Stack>
                        </Card>
                    </SimpleGrid>
                </Tabs.Panel>

                <Tabs.Panel value="tiers" pt="md">
                    <Card>
                        <Title order={5} mb="md">PSP Relationship Tiers</Title>
                        <Text c="dimmed" size="sm">
                            Configure rate improvements for specific PSP relationships (premium pricing tiers).
                        </Text>
                        <Table mt="md">
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>PSP</Table.Th>
                                    <Table.Th>Tier</Table.Th>
                                    <Table.Th>Improvement (bps)</Table.Th>
                                    <Table.Th>Actions</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                <Table.Tr>
                                    <Table.Td>Demo Bank SG</Table.Td>
                                    <Table.Td><Badge>PREMIUM</Badge></Table.Td>
                                    <Table.Td>-5 bps</Table.Td>
                                    <Table.Td>
                                        <Button size="xs" variant="subtle">Edit</Button>
                                    </Table.Td>
                                </Table.Tr>
                                <Table.Tr>
                                    <Table.Td>Partner Bank TH</Table.Td>
                                    <Table.Td><Badge color="gray">STANDARD</Badge></Table.Td>
                                    <Table.Td>0 bps</Table.Td>
                                    <Table.Td>
                                        <Button size="xs" variant="subtle">Edit</Button>
                                    </Table.Td>
                                </Table.Tr>
                            </Table.Tbody>
                        </Table>
                    </Card>
                </Tabs.Panel>
            </Tabs>

            {/* Developer Debug Panel for FXP Actor */}
            <DevDebugPanel context={{ actorType: "FXP", actorName: "FX Provider" }} showToggle={true} />
        </Stack>
    );
}
