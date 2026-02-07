/**
 * PaymentsExplorer - Transaction Lifecycle & Message Viewer
 * 
 * A comprehensive developer tool for exploring payment transactions,
 * viewing the 17-step lifecycle, and inspecting raw ISO 20022 messages.
 * 
 * Features:
 * - UETR-based transaction lookup
 * - 17-step lifecycle visualization
 * - Real-time status tracking
 * - ISO 20022 message inspection
 * - Debug information panel
 * 
 * Reference: ADR-011 Developer Observability
 * Author: Siva Subramanian (https://linkedin.com/in/sivasub987)
 */

import {
    Container,
    Paper,
    Title,
    Text,
    TextInput,
    Button,
    Group,
    Stack,
    Card,
    Badge,
    Timeline,
    Table,
    Code,
    Alert,
    Loader,
    SimpleGrid,
    Tabs,
    ActionIcon,
    CopyButton,
    Tooltip,
} from "@mantine/core";
import {
    IconSearch,
    IconCheck,
    IconCopy,
    IconClock,
    IconAlertCircle,
    IconFileCode,
    IconTimeline,
    IconReceiptDollar,
    IconBuilding,
} from "@tabler/icons-react";
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { MessageInspector } from "../components/MessageInspector";
import { DevDebugPanel } from "../components/DevDebugPanel";
import { getPaymentStatus, getPaymentMessages } from "../services/api";

// 17-step lifecycle phases
const LIFECYCLE_STEPS = [
    { step: 1, phase: "Setup", description: "Sender selects country" },
    { step: 2, phase: "Setup", description: "Sender enters amount" },
    { step: 3, phase: "Quotes", description: "PSP requests FX quotes" },
    { step: 4, phase: "Quotes", description: "Nexus aggregates rates" },
    { step: 5, phase: "Quotes", description: "PSP selects best quote" },
    { step: 6, phase: "Quotes", description: "Display rate to Sender" },
    { step: 7, phase: "Addressing", description: "Sender enters recipient" },
    { step: 8, phase: "Addressing", description: "Proxy resolution (acmt.023)" },
    { step: 9, phase: "Addressing", description: "Confirmation of Payee" },
    { step: 10, phase: "Compliance", description: "Sanctions screening (Source)" },
    { step: 11, phase: "Compliance", description: "Sanctions screening (Dest)" },
    { step: 12, phase: "Approval", description: "Sender confirms payment" },
    { step: 13, phase: "Execution", description: "Get intermediary agents" },
    { step: 14, phase: "Execution", description: "Construct pacs.008" },
    { step: 15, phase: "Execution", description: "Submit to Source IPS" },
    { step: 16, phase: "Execution", description: "Forward via Nexus" },
    { step: 17, phase: "Confirmation", description: "Receive pacs.002" },
];

// Status code descriptions
const STATUS_CODES: Record<string, { description: string; color: string }> = {
    ACCC: { description: "Settlement Completed", color: "green" },
    ACSP: { description: "Settlement in Progress", color: "blue" },
    RJCT: { description: "Rejected", color: "red" },
    PDNG: { description: "Pending", color: "yellow" },
    AB03: { description: "Timeout - Aborted", color: "orange" },
    AB04: { description: "Quote Expired", color: "orange" },
    AM04: { description: "Insufficient Funds", color: "red" },
    BE23: { description: "Account Not Found", color: "red" },
    RC11: { description: "Invalid SAP", color: "red" },
};

interface PaymentDetails {
    uetr: string;
    status: string;
    statusReasonCode?: string;
    reasonDescription?: string;
    sourcePsp: string;
    destinationPsp: string;
    amount: number;
    currency: string;
    initiatedAt: string;
    completedAt?: string;
}

interface Message {
    messageType: string;
    direction: "inbound" | "outbound";
    xml: string;
    timestamp: string;
    description?: string;
}

export function PaymentsExplorer() {
    const [searchParams] = useSearchParams();
    const [uetrInput, setUetrInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [payment, setPayment] = useState<PaymentDetails | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [error, setError] = useState<string | null>(null);

    // Handle URL query param for direct linking from demo
    useEffect(() => {
        const uetrFromUrl = searchParams.get("uetr");
        if (uetrFromUrl && uetrFromUrl !== uetrInput) {
            setUetrInput(uetrFromUrl);
            // Auto-search when UETR is provided via URL
            searchPaymentByUetr(uetrFromUrl);
        }
    }, [searchParams]);

    const searchPaymentByUetr = async (uetr: string) => {
        setLoading(true);
        setError(null);
        setPayment(null);
        setMessages([]);

        try {
            // Fetch payment status using mock-enabled API
            const statusData = await getPaymentStatus(uetr);

            if (statusData.status === "NOT_FOUND") {
                setError(`Payment not found: ${uetr}`);
                setLoading(false);
                return;
            }

            setPayment(statusData as PaymentDetails);

            // Fetch messages using mock-enabled API
            const msgData = await getPaymentMessages(uetr);
            setMessages((msgData.messages || []) as Message[]);
        } catch (err) {
            setError(`Failed to fetch payment: ${err}`);
        } finally {
            setLoading(false);
        }
    };

    const searchPayment = async () => {
        if (!uetrInput.trim()) {
            setError("Please enter a UETR");
            return;
        }
        await searchPaymentByUetr(uetrInput);
    };

    const getStatusInfo = (code: string) =>
        STATUS_CODES[code] || { description: "Unknown Status", color: "gray" };

    return (
        <Container size="xl" py="md">
            <Stack gap="lg">
                {/* Header */}
                <div>
                    <Title order={1}>Payments Explorer</Title>
                    <Text c="dimmed">
                        Developer tool for tracing the 17-step payment lifecycle and inspecting ISO 20022 messages
                    </Text>
                </div>

                {/* Search */}
                <Paper shadow="xs" p="md" radius="md" withBorder>
                    <Group>
                        <TextInput
                            placeholder="Enter UETR (e.g., f47ac10b-58cc-4372-a567-0e02b2c3d479)"
                            value={uetrInput}
                            onChange={(e) => setUetrInput(e.target.value)}
                            style={{ flex: 1 }}
                            leftSection={<IconSearch size={16} />}
                            onKeyDown={(e) => e.key === "Enter" && searchPayment()}
                        />
                        <Button
                            onClick={searchPayment}
                            loading={loading}
                            leftSection={<IconSearch size={16} />}
                        >
                            Search
                        </Button>
                    </Group>
                </Paper>

                {/* Error */}
                {error && (
                    <Alert
                        icon={<IconAlertCircle size={16} />}
                        title="Error"
                        color="red"
                        withCloseButton
                        onClose={() => setError(null)}
                    >
                        {error}
                    </Alert>
                )}

                {/* Loading */}
                {loading && (
                    <Group justify="center" py="xl">
                        <Loader size="lg" />
                        <Text>Searching for transaction...</Text>
                    </Group>
                )}

                {/* Results */}
                {payment && (
                    <Tabs defaultValue="overview" variant="pills">
                        <Tabs.List mb="md">
                            <Tabs.Tab value="overview" leftSection={<IconReceiptDollar size={16} />}>
                                Overview
                            </Tabs.Tab>
                            <Tabs.Tab value="lifecycle" leftSection={<IconTimeline size={16} />}>
                                Lifecycle
                            </Tabs.Tab>
                            <Tabs.Tab value="messages" leftSection={<IconFileCode size={16} />}>
                                Messages ({messages.length})
                            </Tabs.Tab>
                            <Tabs.Tab value="debug" leftSection={<IconBuilding size={16} />}>
                                Debug Panel
                            </Tabs.Tab>
                        </Tabs.List>

                        {/* Overview Tab */}
                        <Tabs.Panel value="overview">
                            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
                                <Card shadow="xs" padding="lg" radius="md" withBorder>
                                    <Title order={4} mb="md">Transaction Details</Title>
                                    <Table>
                                        <Table.Tbody>
                                            <Table.Tr>
                                                <Table.Td fw={500}>UETR</Table.Td>
                                                <Table.Td>
                                                    <Group gap="xs">
                                                        <Code>{payment.uetr}</Code>
                                                        <CopyButton value={payment.uetr}>
                                                            {({ copied, copy }) => (
                                                                <Tooltip label={copied ? "Copied!" : "Copy"}>
                                                                    <ActionIcon
                                                                        size="sm"
                                                                        variant="subtle"
                                                                        onClick={copy}
                                                                    >
                                                                        {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                                                                    </ActionIcon>
                                                                </Tooltip>
                                                            )}
                                                        </CopyButton>
                                                    </Group>
                                                </Table.Td>
                                            </Table.Tr>
                                            <Table.Tr>
                                                <Table.Td fw={500}>Status</Table.Td>
                                                <Table.Td>
                                                    <Badge
                                                        color={getStatusInfo(payment.status).color}
                                                        size="lg"
                                                    >
                                                        {payment.status}
                                                    </Badge>
                                                </Table.Td>
                                            </Table.Tr>
                                            {payment.statusReasonCode && (
                                                <Table.Tr>
                                                    <Table.Td fw={500}>Reason Code</Table.Td>
                                                    <Table.Td>
                                                        <Badge color="gray" variant="light">
                                                            {payment.statusReasonCode}
                                                        </Badge>
                                                        {payment.reasonDescription && (
                                                            <Text size="xs" c="dimmed" mt={4}>
                                                                {payment.reasonDescription}
                                                            </Text>
                                                        )}
                                                    </Table.Td>
                                                </Table.Tr>
                                            )}
                                            <Table.Tr>
                                                <Table.Td fw={500}>Amount</Table.Td>
                                                <Table.Td>
                                                    <Text fw={600}>
                                                        {payment.currency} {payment.amount?.toLocaleString()}
                                                    </Text>
                                                </Table.Td>
                                            </Table.Tr>
                                        </Table.Tbody>
                                    </Table>
                                </Card>

                                <Card shadow="xs" padding="lg" radius="md" withBorder>
                                    <Title order={4} mb="md">Participants</Title>
                                    <Table>
                                        <Table.Tbody>
                                            <Table.Tr>
                                                <Table.Td fw={500}>Source PSP</Table.Td>
                                                <Table.Td>
                                                    <Code>{payment.sourcePsp || "N/A"}</Code>
                                                </Table.Td>
                                            </Table.Tr>
                                            <Table.Tr>
                                                <Table.Td fw={500}>Destination PSP</Table.Td>
                                                <Table.Td>
                                                    <Code>{payment.destinationPsp || "N/A"}</Code>
                                                </Table.Td>
                                            </Table.Tr>
                                            <Table.Tr>
                                                <Table.Td fw={500}>Initiated</Table.Td>
                                                <Table.Td>
                                                    <Group gap="xs">
                                                        <IconClock size={14} />
                                                        <Text size="sm">
                                                            {payment.initiatedAt
                                                                ? new Date(payment.initiatedAt).toLocaleString()
                                                                : "N/A"}
                                                        </Text>
                                                    </Group>
                                                </Table.Td>
                                            </Table.Tr>
                                            {payment.completedAt && (
                                                <Table.Tr>
                                                    <Table.Td fw={500}>Completed</Table.Td>
                                                    <Table.Td>
                                                        <Group gap="xs">
                                                            <IconCheck size={14} color="green" />
                                                            <Text size="sm">
                                                                {new Date(payment.completedAt).toLocaleString()}
                                                            </Text>
                                                        </Group>
                                                    </Table.Td>
                                                </Table.Tr>
                                            )}
                                        </Table.Tbody>
                                    </Table>
                                </Card>
                            </SimpleGrid>
                        </Tabs.Panel>

                        {/* Lifecycle Tab */}
                        <Tabs.Panel value="lifecycle">
                            <Card shadow="xs" padding="lg" radius="md" withBorder>
                                <Title order={4} mb="md">17-Step Payment Lifecycle</Title>
                                <Timeline active={payment.status === "ACCC" ? 17 : -1} bulletSize={28}>
                                    {LIFECYCLE_STEPS.map((step) => {
                                        const phaseColors: Record<string, string> = {
                                            Setup: "blue",
                                            Quotes: "violet",
                                            Addressing: "grape",
                                            Compliance: "orange",
                                            Approval: "cyan",
                                            Execution: "teal",
                                            Confirmation: "green",
                                        };

                                        return (
                                            <Timeline.Item
                                                key={step.step}
                                                color={phaseColors[step.phase]}
                                                title={
                                                    <Group gap="xs">
                                                        <Badge size="sm" variant="light">
                                                            Step {step.step}
                                                        </Badge>
                                                        <Text size="sm" fw={500}>
                                                            {step.description}
                                                        </Text>
                                                    </Group>
                                                }
                                            >
                                                <Badge
                                                    color={phaseColors[step.phase]}
                                                    variant="outline"
                                                    size="xs"
                                                >
                                                    {step.phase}
                                                </Badge>
                                            </Timeline.Item>
                                        );
                                    })}
                                </Timeline>
                            </Card>
                        </Tabs.Panel>

                        {/* Messages Tab */}
                        <Tabs.Panel value="messages">
                            <MessageInspector
                                uetr={payment.uetr}
                                messages={messages}
                                loading={false}
                            />
                        </Tabs.Panel>

                        {/* Debug Tab */}
                        <Tabs.Panel value="debug">
                            <DevDebugPanel
                                context={{
                                    actorType: "GATEWAY",
                                    actorName: "Nexus Gateway"
                                }}
                                showToggle={false}
                                defaultOpen={true}
                            />
                        </Tabs.Panel>
                    </Tabs>
                )}

                {/* Empty State */}
                {!payment && !loading && !error && (
                    <Paper shadow="xs" p="xl" radius="md" withBorder>
                        <Stack align="center" gap="md">
                            <IconSearch size={48} color="gray" />
                            <Title order={3}>Search for a Payment</Title>
                            <Text c="dimmed" ta="center" maw={400}>
                                Enter a UETR to view the complete payment lifecycle,
                                ISO 20022 messages, and debug information.
                            </Text>
                            <Code>Example: f47ac10b-58cc-4372-a567-0e02b2c3d479</Code>
                        </Stack>
                    </Paper>
                )}
            </Stack>
        </Container>
    );
}

export default PaymentsExplorer;
