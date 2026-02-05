import {
    Card,
    Stack,
    Title,
    Group,
    Text,
    Timeline,
    Badge,
    Accordion,
    Code,
    Collapse,
} from "@mantine/core";
import {
    IconCheck,
    IconCircleDot,
    IconCircle,
    IconAlertCircle,
    IconClipboardList,
} from "@tabler/icons-react";
import type { LifecycleStep } from "../../types";

export interface LifecycleTrackerProps {
    steps: LifecycleStep[];
    devMode: boolean;
}

const PHASE_NAMES: Record<number, string> = {
    1: "Payment Setup",
    2: "Quoting",
    3: "Addressing & Compliance",
    4: "Processing & Settlement",
    5: "Completion",
};

function getStepIcon(status: LifecycleStep["status"]) {
    switch (status) {
        case "completed":
            return <IconCheck size={12} />;
        case "active":
            return <IconCircleDot size={12} />;
        case "error":
            return <IconAlertCircle size={12} />;
        default:
            return <IconCircle size={12} />;
    }
}

function getStepColor(status: LifecycleStep["status"]) {
    switch (status) {
        case "completed":
            return "green";
        case "active":
            return "blue";
        case "error":
            return "red";
        default:
            return "gray";
    }
}

export function LifecycleTracker({ steps, devMode }: LifecycleTrackerProps) {
    const stepsByPhase = Object.entries(PHASE_NAMES).map(([phase, name]) => ({
        phase: Number(phase),
        name,
        steps: steps.filter((s) => s.phase === Number(phase)),
    }));

    const completedSteps = steps.filter((s) => s.status === "completed").length;
    const totalSteps = steps.length;
    const progressPercentage = Math.round((completedSteps / totalSteps) * 100);

    return (
        <Card withBorder radius="md" p="xl">
            <Stack gap="md">
                <Group justify="space-between">
                    <Title order={5}>
                        <Group gap="xs">
                            <IconClipboardList size={20} color="var(--mantine-color-violet-filled)" />
                            Lifecycle Trace
                        </Group>
                    </Title>
                    <Badge color="violet" variant="light">
                        {completedSteps}/{totalSteps} ({progressPercentage}%)
                    </Badge>
                </Group>

                <Accordion variant="contained" radius="md" defaultValue="phase-1">
                    {stepsByPhase.map(({ phase, name, steps: phaseSteps }) => {
                        const phaseCompleted = phaseSteps.every((s) => s.status === "completed");
                        const phaseActive = phaseSteps.some((s) => s.status === "active");
                        const phaseError = phaseSteps.some((s) => s.status === "error");

                        return (
                            <Accordion.Item key={phase} value={`phase-${phase}`}>
                                <Accordion.Control>
                                    <Group gap="xs">
                                        <Badge 
                                            size="sm" 
                                            color={phaseError ? "red" : phaseCompleted ? "green" : phaseActive ? "blue" : "gray"}
                                            variant="filled"
                                        >
                                            {phase}
                                        </Badge>
                                        <Text size="sm" fw={500}>{name}</Text>
                                        <Text size="xs" c="dimmed">
                                            ({phaseSteps.filter(s => s.status === "completed").length}/{phaseSteps.length})
                                        </Text>
                                    </Group>
                                </Accordion.Control>
                                <Accordion.Panel>
                                    <Timeline active={-1} bulletSize={20} lineWidth={2}>
                                        {phaseSteps.map((step) => (
                                            <Timeline.Item
                                                key={step.id}
                                                bullet={getStepIcon(step.status)}
                                                color={getStepColor(step.status)}
                                                title={
                                                    <Group gap="xs">
                                                        <Text size="sm" fw={step.status === "active" ? 600 : 400}>
                                                            {step.name}
                                                        </Text>
                                                        {step.timestamp && (
                                                            <Text size="xs" c="dimmed">{step.timestamp}</Text>
                                                        )}
                                                    </Group>
                                                }
                                            >
                                                <Collapse in={devMode}>
                                                    <Stack gap={4} mt="xs">
                                                        <Group gap="xs">
                                                            <Text size="xs" c="dimmed">API:</Text>
                                                            <Code>{step.apiCall}</Code>
                                                        </Group>
                                                        {step.isoMessage !== "-" && (
                                                            <Group gap="xs">
                                                                <Text size="xs" c="dimmed">ISO:</Text>
                                                                <Badge size="xs" color="grape" variant="light">
                                                                    {step.isoMessage}
                                                                </Badge>
                                                            </Group>
                                                        )}
                                                        {step.details && (
                                                            <Code block mt="xs">
                                                                {JSON.stringify(step.details, null, 2)}
                                                            </Code>
                                                        )}
                                                    </Stack>
                                                </Collapse>
                                            </Timeline.Item>
                                        ))}
                                    </Timeline>
                                </Accordion.Panel>
                            </Accordion.Item>
                        );
                    })}
                </Accordion>
            </Stack>
        </Card>
    );
}
