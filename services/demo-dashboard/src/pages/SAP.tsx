import {
    Title,
    Card,
    Stack,
    Group,
    Text,
    Badge,
    Table,
    SimpleGrid,
    Progress,
    RingProgress,
    ThemeIcon,
    Anchor,
    Breadcrumbs,
    Alert,
} from "@mantine/core";
import {
    IconCoin,
    IconLock,
    IconCheck,
    IconAlertTriangle,
    IconInfoCircle,
} from "@tabler/icons-react";
import { useState, useEffect } from "react";
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

function CountdownBadge({ targetDate }: { targetDate: string }) {
    const seconds = useCountdown(targetDate);
    return (
        <Badge size="sm" variant="outline" color={seconds < 30 ? "red" : "blue"}>
            {seconds}s
        </Badge>
    );
}


// Demo liquidity data
const DEMO_BALANCES = [
    { fxpId: "FXP-001", fxpName: "GlobalFX", currency: "SGD", totalBalance: 500000, reservedAmount: 50000, availableBalance: 450000, status: "ACTIVE" as const },
    { fxpId: "FXP-002", fxpName: "RapidExchange", currency: "SGD", totalBalance: 450000, reservedAmount: 45000, availableBalance: 405000, status: "ACTIVE" as const },
    { fxpId: "FXP-003", fxpName: "SwiftFX", currency: "SGD", totalBalance: 100000, reservedAmount: 80000, availableBalance: 20000, status: "LOW" as const },
];

const DEMO_RESERVATIONS = [
    { reservationId: "RES-001", quoteId: "QT-2026-0203-001", amount: 10000, currency: "SGD", expiresAt: new Date(Date.now() + 600000).toISOString(), status: "ACTIVE" as const },
    { reservationId: "RES-002", quoteId: "QT-2026-0203-002", amount: 25000, currency: "SGD", expiresAt: new Date(Date.now() + 450000).toISOString(), status: "ACTIVE" as const },
    { reservationId: "RES-003", quoteId: "QT-2026-0203-003", amount: 15000, currency: "SGD", expiresAt: new Date(Date.now() + 300000).toISOString(), status: "ACTIVE" as const },
];


export function SAPPage() {
    const totalBalance = DEMO_BALANCES.reduce((sum, b) => sum + b.totalBalance, 0);
    const totalReserved = DEMO_BALANCES.reduce((sum, b) => sum + b.reservedAmount, 0);
    const totalAvailable = totalBalance - totalReserved;
    const reservedPercent = (totalReserved / totalBalance) * 100;

    return (
        <Stack gap="md">
            <Breadcrumbs mb="xs">
                <Anchor href="/actors" size="xs">Actor Registry</Anchor>
                <Text size="xs" c="dimmed">Liquidity Management</Text>
            </Breadcrumbs>
            <Group justify="space-between">
                <Title order={2}>Settlement Access Provider (SAP) Dashboard</Title>
                <Group>
                    <Anchor href="/fxp" size="sm">View FX Rates (FXP)</Anchor>
                    <Badge color="green" variant="light" leftSection={<IconCoin size={14} />}>
                        SAP View
                    </Badge>
                </Group>
            </Group>

            {/* SAP Role Explanation */}
            <Alert icon={<IconInfoCircle size={18} />} title="What is a Settlement Access Provider (SAP)?" color="green" variant="light">
                <Text size="sm">
                    SAPs are banks that hold <strong>settlement accounts</strong> (nostro accounts) on behalf of FXPs.
                    They manage liquidity reservations for quoted payments and facilitate final settlement through
                    the domestic IPS. SAPs ensure FXPs have sufficient funds before payments are executed.
                </Text>
                <Anchor href="https://docs.nexusglobalpayments.org/settlement-access-provision/role-of-the-settlement-access-provider-sap" size="xs" mt="xs">
                    Learn more in Nexus Documentation →
                </Anchor>
            </Alert>

            <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
                <Card>
                    <Group justify="space-between" mb="xs">
                        <Text c="dimmed" size="sm">Total Balance</Text>
                        <ThemeIcon variant="light" color="blue">
                            <IconCoin size={16} />
                        </ThemeIcon>
                    </Group>
                    <Title order={3}>SGD {totalBalance.toLocaleString()}</Title>
                </Card>

                <Card>
                    <Group justify="space-between" mb="xs">
                        <Text c="dimmed" size="sm">Reserved</Text>
                        <ThemeIcon variant="light" color="yellow">
                            <IconLock size={16} />
                        </ThemeIcon>
                    </Group>
                    <Title order={3}>SGD {totalReserved.toLocaleString()}</Title>
                    <Text size="xs" c="dimmed">{DEMO_RESERVATIONS.length} active quotes</Text>
                </Card>

                <Card>
                    <Group justify="space-between" mb="xs">
                        <Text c="dimmed" size="sm">Available</Text>
                        <ThemeIcon variant="light" color="green">
                            <IconCheck size={16} />
                        </ThemeIcon>
                    </Group>
                    <Title order={3}>SGD {totalAvailable.toLocaleString()}</Title>
                </Card>
            </SimpleGrid>

            {/* Utilization Ring */}
            <Card>
                <Group>
                    <RingProgress
                        size={100}
                        thickness={10}
                        sections={[
                            { value: reservedPercent, color: "yellow" },
                            { value: 100 - reservedPercent, color: "green" },
                        ]}
                        label={
                            <Text ta="center" size="xs" fw={700}>
                                {reservedPercent.toFixed(0)}%
                            </Text>
                        }
                    />
                    <Stack gap={0}>
                        <Text size="sm" fw={500}>Liquidity Utilization</Text>
                        <Text size="xs" c="dimmed">
                            {reservedPercent.toFixed(1)}% reserved across all FXPs
                        </Text>
                    </Stack>
                </Group>
            </Card>

            {/* FXP Balances */}
            <Card>
                <Title order={5} mb="md">FXP Balances</Title>
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>FXP Name</Table.Th>
                            <Table.Th>Currency</Table.Th>
                            <Table.Th>Total</Table.Th>
                            <Table.Th>Reserved</Table.Th>
                            <Table.Th>Available</Table.Th>
                            <Table.Th>Utilization</Table.Th>
                            <Table.Th>Status</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {DEMO_BALANCES.map((balance) => {
                            const util = (balance.reservedAmount / balance.totalBalance) * 100;
                            return (
                                <Table.Tr key={balance.fxpId}>
                                    <Table.Td fw={500}>{balance.fxpName}</Table.Td>
                                    <Table.Td>{balance.currency}</Table.Td>
                                    <Table.Td>{balance.totalBalance.toLocaleString()}</Table.Td>
                                    <Table.Td>{balance.reservedAmount.toLocaleString()}</Table.Td>
                                    <Table.Td>{balance.availableBalance.toLocaleString()}</Table.Td>
                                    <Table.Td style={{ width: 150 }}>
                                        <Progress
                                            value={util}
                                            color={util > 80 ? "red" : util > 50 ? "yellow" : "green"}
                                            size="sm"
                                        />
                                    </Table.Td>
                                    <Table.Td>
                                        <Badge
                                            color={balance.status === "ACTIVE" ? "green" : balance.status === "LOW" ? "yellow" : "red"}
                                            leftSection={balance.status === "LOW" ? <IconAlertTriangle size={12} /> : null}
                                        >
                                            {balance.status}
                                        </Badge>
                                    </Table.Td>
                                </Table.Tr>
                            );
                        })}
                    </Table.Tbody>
                </Table>
            </Card>

            {/* Active Reservations */}
            <Card>
                <Title order={5} mb="md">Active Reservations</Title>
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th>Quote ID</Table.Th>
                            <Table.Th>Amount</Table.Th>
                            <Table.Th>Currency</Table.Th>
                            <Table.Th>Expires In</Table.Th>
                            <Table.Th>Status</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {DEMO_RESERVATIONS.map((res) => (
                            <Table.Tr key={res.reservationId}>
                                <Table.Td>
                                    <Text size="sm" ff="monospace">{res.quoteId}</Text>
                                </Table.Td>
                                <Table.Td>{res.amount.toLocaleString()}</Table.Td>
                                <Table.Td>{res.currency}</Table.Td>
                                <Table.Td>
                                    <CountdownBadge targetDate={res.expiresAt} />
                                </Table.Td>

                                <Table.Td>
                                    <Badge color="green" size="sm">{res.status}</Badge>
                                </Table.Td>
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>
            </Card>

            {/* Developer Debug Panel for SAP Actor */}
            <DevDebugPanel context={{ actorType: "SAP", actorName: "Settlement Access Provider" }} showToggle={true} />
        </Stack>
    );
}
