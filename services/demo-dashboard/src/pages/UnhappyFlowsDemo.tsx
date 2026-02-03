/**
 * Unhappy Flows Demo Page
 *
 * Pre-configured scenarios to demonstrate error handling:
 * - BE23: Invalid Proxy
 * - AM04: Insufficient Funds
 * - AM02: Amount Limit Exceeded
 * - AB04: Quote Expired
 * - AC04: Closed Account
 * - RR04: Regulatory Block
 * - DUPL: Duplicate Payment
 *
 * Reference: docs/UNHAPPY_FLOWS.md
 */

import {
    Container,
    Title,
    Text,
    Card,
    Group,
    Stack,
    Badge,
    Button,
    Table,
    Alert,
    Code,
    Paper,
    ThemeIcon,
    SimpleGrid,
    Divider,
} from "@mantine/core";
import {
    IconAlertTriangle,
    IconCheck,
    IconX,
    IconPlayerPlay,
    IconClock,
    IconCurrencyDollar,
    IconUser,
    IconLock,
    IconCopy,
} from "@tabler/icons-react";
import { useNavigate } from "react-router-dom";
import { notifications } from "@mantine/notifications";

// ISO 20022 Error Code definitions
const ERROR_CODES = {
    BE23: {
        name: "Invalid Proxy",
        description: "Account/Proxy not registered in destination PDO",
        trigger: "+66999999999",
        icon: IconUser,
        color: "red",
    },
    AM04: {
        name: "Insufficient Funds",
        description: "Debtor account has insufficient balance",
        trigger: "99999 (amount)",
        icon: IconCurrencyDollar,
        color: "orange",
    },
    AM02: {
        name: "Amount Limit",
        description: "Transaction exceeds IPS limit (50,000)",
        trigger: "50001+ (amount)",
        icon: IconCurrencyDollar,
        color: "yellow",
    },
    AB04: {
        name: "Quote Expired",
        description: "FX quote validity window exceeded (10 min)",
        trigger: "Wait 10+ minutes",
        icon: IconClock,
        color: "blue",
    },
    AC04: {
        name: "Closed Account",
        description: "Recipient account has been closed",
        trigger: "+60999999999",
        icon: IconX,
        color: "red",
    },
    RR04: {
        name: "Regulatory Block",
        description: "AML/CFT screening failed",
        trigger: "+62999999999",
        icon: IconLock,
        color: "purple",
    },
    DUPL: {
        name: "Duplicate Payment",
        description: "UETR already exists in system",
        trigger: "Reuse UETR",
        icon: IconCopy,
        color: "gray",
    },
};

export function UnhappyFlowsDemo() {
    const navigate = useNavigate();

    const runDemo = (code: string) => {
        const errorDef = ERROR_CODES[code as keyof typeof ERROR_CODES];

        // Store trigger value in session for Payment page to consume
        sessionStorage.setItem("demoTrigger", JSON.stringify({
            code,
            trigger: errorDef.trigger,
            startedAt: new Date().toISOString(),
        }));

        notifications.show({
            title: `${code} Demo Started`,
            message: `Navigate to Payment page and use trigger: ${errorDef.trigger}`,
            color: errorDef.color,
            icon: <errorDef.icon size={16} />,
        });

        // Navigate to payment with pre-filled demo
        navigate(`/payment?demo=${code}`);
    };

    return (
        <Container size="xl" py="md">
            <Stack gap="lg">
                {/* Header */}
                <Group justify="space-between" align="flex-start">
                    <div>
                        <Title order={2}>Unhappy Flows Demo</Title>
                        <Text c="dimmed" size="sm">
                            Test ISO 20022 error scenarios with pre-configured trigger values
                        </Text>
                    </div>
                    <Badge size="lg" variant="light" color="red">
                        Sandbox Testing
                    </Badge>
                </Group>

                {/* Quick Reference */}
                <Alert
                    icon={<IconAlertTriangle size={16} />}
                    title="Trigger Values Reference"
                    color="yellow"
                >
                    <Text size="sm">
                        Use these values in the Send Payment flow to trigger specific error scenarios.
                        All errors return ISO 20022 pacs.002 with RJCT status and reason code.
                    </Text>
                </Alert>

                {/* Error Scenarios Grid */}
                <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="md">
                    {Object.entries(ERROR_CODES).map(([code, def]) => (
                        <Card key={code} withBorder padding="md" radius="md">
                            <Group justify="space-between" mb="xs">
                                <Group gap="xs">
                                    <ThemeIcon size="lg" radius="md" color={def.color}>
                                        <def.icon size={18} />
                                    </ThemeIcon>
                                    <div>
                                        <Text fw={700}>{code}</Text>
                                        <Text size="xs" c="dimmed">{def.name}</Text>
                                    </div>
                                </Group>
                            </Group>

                            <Text size="sm" c="dimmed" mb="md">
                                {def.description}
                            </Text>

                            <Paper p="xs" bg="dark.7" radius="sm" mb="md">
                                <Group gap="xs">
                                    <Text size="xs" c="dimmed">Trigger:</Text>
                                    <Code>{def.trigger}</Code>
                                </Group>
                            </Paper>

                            <Button
                                fullWidth
                                variant="light"
                                color={def.color}
                                leftSection={<IconPlayerPlay size={16} />}
                                onClick={() => runDemo(code)}
                            >
                                Run Demo
                            </Button>
                        </Card>
                    ))}
                </SimpleGrid>

                <Divider my="md" />

                {/* Trigger Values Table */}
                <Card withBorder>
                    <Title order={4} mb="md">Complete Trigger Values Reference</Title>
                    <Table striped highlightOnHover>
                        <Table.Thead>
                            <Table.Tr>
                                <Table.Th>Error Code</Table.Th>
                                <Table.Th>Name</Table.Th>
                                <Table.Th>Trigger Value</Table.Th>
                                <Table.Th>Where to Apply</Table.Th>
                            </Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                            <Table.Tr>
                                <Table.Td><Badge color="red">BE23</Badge></Table.Td>
                                <Table.Td>Proxy Invalid</Table.Td>
                                <Table.Td><Code>+66999999999</Code></Table.Td>
                                <Table.Td>Phone number field</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td><Badge color="red">AC04</Badge></Table.Td>
                                <Table.Td>Closed Account</Table.Td>
                                <Table.Td><Code>+60999999999</Code></Table.Td>
                                <Table.Td>Phone number field</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td><Badge color="purple">RR04</Badge></Table.Td>
                                <Table.Td>Regulatory Block</Table.Td>
                                <Table.Td><Code>+62999999999</Code></Table.Td>
                                <Table.Td>Phone number field</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td><Badge color="yellow">AM02</Badge></Table.Td>
                                <Table.Td>Amount Limit</Table.Td>
                                <Table.Td><Code>50001</Code> or higher</Table.Td>
                                <Table.Td>Amount field</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td><Badge color="orange">AM04</Badge></Table.Td>
                                <Table.Td>Insufficient Funds</Table.Td>
                                <Table.Td><Code>99999</Code> or <Code>199999</Code></Table.Td>
                                <Table.Td>Amount field</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td><Badge color="blue">AB04</Badge></Table.Td>
                                <Table.Td>Quote Expired</Table.Td>
                                <Table.Td>Wait 10+ minutes after quote</Table.Td>
                                <Table.Td>Time-based</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td><Badge color="gray">DUPL</Badge></Table.Td>
                                <Table.Td>Duplicate Payment</Table.Td>
                                <Table.Td>Submit same UETR twice</Table.Td>
                                <Table.Td>UETR field (advanced)</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Card>

                {/* Success Path */}
                <Card withBorder>
                    <Group justify="space-between" mb="md">
                        <div>
                            <Title order={4}>Happy Flow (Success Path)</Title>
                            <Text size="sm" c="dimmed">Normal payment flow with ACCC status</Text>
                        </div>
                        <Button
                            variant="light"
                            color="green"
                            leftSection={<IconCheck size={16} />}
                            onClick={() => navigate("/payment")}
                        >
                            Run Happy Flow
                        </Button>
                    </Group>
                    <Text size="sm">
                        Use any valid proxy (e.g., <Code>+65123456789</Code>) and amount under 50,000.
                        The payment will complete with pacs.002 status <Code>ACCC</Code> (Accepted).
                    </Text>
                </Card>
            </Stack>
        </Container>
    );
}
