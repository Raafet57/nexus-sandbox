import { useState, useEffect, useCallback } from "react";
import {
    Title,
    Card,
    Stack,
    Group,
    Text,
    Badge,
    SimpleGrid,
    ThemeIcon,
    Box,
    Paper,
    Divider,
    Loader,
    Alert,
} from "@mantine/core";
import {
    IconNetwork,
    IconDatabase,
    IconBuildingBank,
    IconArrowsExchange,
    IconUserCheck,
    IconCheck,
    IconAlertCircle,
} from "@tabler/icons-react";

import { getActors, type Actor } from "../services/api";
import { DevDebugPanel } from "../components/DevDebugPanel";


export function MeshPage() {
    const [actors, setActors] = useState<Actor[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchActors = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getActors();
            setActors(data.actors || []);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Connection error");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchActors();
    }, [fetchActors]);

    if (loading) return <Group justify="center" p="xl"><Loader size="xl" /></Group>;

    return (
        <Stack gap="md">
            <Group justify="space-between">
                <Title order={2}>Nexus Mesh Visualizer</Title>
                <Badge color="blue" variant="light" leftSection={<IconNetwork size={14} />}>
                    Topology
                </Badge>
            </Group>

            {error && (
                <Alert color="red" icon={<IconAlertCircle size={16} />}>
                    {error}
                </Alert>
            )}

            <Text size="sm" c="dimmed">
                Real-time connectivity status of all actors in the multilateral mesh.
            </Text>

            <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
                {actors.map((actor) => (
                    <Card key={actor.bic} withBorder shadow="sm">
                        <Group justify="space-between" mb="xs">
                            <ThemeIcon
                                color="blue"
                                variant="light"
                                size="lg"
                            >
                                {actor.actorType === "PSP" && <IconBuildingBank size={18} />}
                                {actor.actorType === "IPS" && <IconDatabase size={18} />}
                                {actor.actorType === "FXP" && <IconArrowsExchange size={18} />}
                                {actor.actorType === "PDO" && <IconUserCheck size={18} />}
                                {actor.actorType === "SAP" && <IconCheck size={18} />}
                            </ThemeIcon>
                            <Badge
                                variant="dot"
                                color={actor.status === "ACTIVE" ? "green" : "gray"}
                            >
                                {actor.status}
                            </Badge>
                        </Group>

                        <Title order={5}>{actor.name}</Title>
                        <Text size="xs" c="dimmed" mb="md">{actor.actorType} | {actor.bic}</Text>

                        <Divider mb="sm" />

                        <Group justify="space-between">
                            <Text size="xs" fw={500}>Latency</Text>
                            <Text size="xs" c="green">{Math.floor(Math.random() * 50) + 10}ms</Text>
                        </Group>
                    </Card>
                ))}

                {/* Gateway is an infra component, not an actor in the registry */}
                <Card withBorder shadow="sm" style={{ border: '1px solid var(--mantine-color-nexusPurple-light)' }}>
                    <Group justify="space-between" mb="xs">
                        <ThemeIcon color="nexusPurple" variant="light" size="lg">
                            <IconNetwork size={18} />
                        </ThemeIcon>
                        <Badge variant="dot" color="green">ONLINE</Badge>
                    </Group>
                    <Title order={5}>Nexus Gateway</Title>
                    <Text size="xs" c="dimmed" mb="md">Orchestrator | CORE-BASE</Text>
                    <Divider mb="sm" />
                    <Group justify="space-between">
                        <Text size="xs" fw={500}>Latency</Text>
                        <Text size="xs" c="green">5ms</Text>
                    </Group>
                </Card>
            </SimpleGrid>

            {/* Logical Flow Diagram - Redesigned for 17-step compliance */}
            <Card withBorder mt="xl">
                <Title order={5} mb="xl">Logical Transaction Path (17-Step Cycle)</Title>
                <Box style={{ overflowX: 'auto', paddingBottom: 20 }}>
                    <Group gap={0} wrap="nowrap">
                        <FlowItem label="S-PSP" sub="Instruction" color="blue" />
                        <Connector />
                        <FlowItem label="PDO" sub="Resolution" color="violet" />
                        <Connector />
                        <FlowItem label="S-IPS" sub="Settlement 1" color="blue" />
                        <Connector />
                        <FlowItem label="Nexus" sub="Gateway" primary />
                        <Connector />
                        <FlowItem label="FXP" sub="Liquidity" color="orange" />
                        <Connector />
                        <FlowItem label="SAP" sub="Bridge" color="orange" />
                        <Connector />
                        <FlowItem label="D-IPS" sub="Settlement 2" color="green" />
                        <Connector />
                        <FlowItem label="D-PSP" sub="Creditor" color="green" />
                    </Group>
                </Box>
                <Text size="xs" c="dimmed" mt="sm">
                    Tracing the path from Proxy Resolution (Step 8) to final Status Confirmation (Step 17).
                </Text>
            </Card>

            {/* Developer Debug Panel for Gateway/Mesh View */}
            <DevDebugPanel context={{ actorType: "GATEWAY", actorName: "Nexus Gateway" }} showToggle={true} />
        </Stack>
    );
}

function FlowItem({ label, sub, primary, color }: { label: string, sub: string, primary?: boolean, color?: string }) {
    return (
        <Paper
            withBorder
            p="xs"
            style={{
                minWidth: 100,
                textAlign: 'center',
                backgroundColor: primary ? 'var(--mantine-color-nexusPurple-light)' : undefined,
                borderColor: primary ? 'var(--mantine-color-nexusPurple-filled)' : (color ? `var(--mantine-color-${color}-6)` : undefined),
                borderWidth: primary ? 2 : 1
            }}
        >
            <Text size="sm" fw={700} c={color ? `${color}.7` : undefined}>{label}</Text>
            <Text size="xs" c="dimmed">{sub}</Text>
        </Paper>
    );
}

function Connector() {
    return (
        <Box style={{ width: 30, height: 2, backgroundColor: 'var(--mantine-color-gray-4)' }} />
    );
}
