import {
    Title,
    Card,
    Stack,
    Group,
    Text,
    Badge,
    Switch,
    TextInput,
    Select,
    Button,
    Divider,
    Code,
} from "@mantine/core";
import { useState } from "react";
import {
    IconSettings,
    IconServer,
    IconPalette,
    IconBell,
} from "@tabler/icons-react";
import { notifications } from "@mantine/notifications";

export function SettingsPage() {
    const [apiUrl, setApiUrl] = useState("/api");
    const [mockMode, setMockMode] = useState(false);
    const [animationsEnabled, setAnimationsEnabled] = useState(true);
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);

    const handleSave = () => {
        notifications.show({
            title: "Settings Saved",
            message: "Your preferences have been updated",
            color: "green",
        });
    };

    return (
        <Stack gap="md">
            <Group justify="space-between">
                <Title order={2}>Settings</Title>
                <Badge color="gray" variant="light" leftSection={<IconSettings size={14} />}>
                    Configuration
                </Badge>
            </Group>

            {/* API Configuration */}
            <Card>
                <Group mb="md">
                    <IconServer size={20} />
                    <Title order={5}>API Configuration</Title>
                </Group>
                <Stack gap="md">
                    <TextInput
                        label="API Base URL"
                        description="Backend gateway URL for API requests"
                        value={apiUrl}
                        onChange={(e) => setApiUrl(e.target.value)}
                        placeholder="/api or http://localhost:8000"
                    />
                    <Switch
                        label="Mock Mode (GitHub Pages)"
                        description="Use simulated data instead of real API calls"
                        checked={mockMode}
                        onChange={(e) => setMockMode(e.currentTarget.checked)}
                    />
                    <Text size="xs" c="dimmed">
                        Current environment: <Code>{import.meta.env.MODE}</Code>
                    </Text>
                </Stack>
            </Card>

            {/* Display Settings */}
            <Card>
                <Group mb="md">
                    <IconPalette size={20} />
                    <Title order={5}>Display Preferences</Title>
                </Group>
                <Stack gap="md">
                    <Switch
                        label="Enable Animations"
                        description="Animate lifecycle steps and transitions"
                        checked={animationsEnabled}
                        onChange={(e) => setAnimationsEnabled(e.currentTarget.checked)}
                    />
                    <Select
                        label="Default Actor View"
                        description="Which dashboard to show on startup"
                        data={[
                            { value: "psp", label: "PSP (Payment)" },
                            { value: "fxp", label: "FXP (Rates)" },
                            { value: "sap", label: "SAP (Liquidity)" },
                        ]}
                        defaultValue="psp"
                    />
                </Stack>
            </Card>

            {/* Notifications */}
            <Card>
                <Group mb="md">
                    <IconBell size={20} />
                    <Title order={5}>Notifications</Title>
                </Group>
                <Stack gap="md">
                    <Switch
                        label="Enable Toast Notifications"
                        description="Show status updates during payment flow"
                        checked={notificationsEnabled}
                        onChange={(e) => setNotificationsEnabled(e.currentTarget.checked)}
                    />
                </Stack>
            </Card>

            <Divider />

            <Group justify="flex-end">
                <Button variant="subtle">Reset to Defaults</Button>
                <Button onClick={handleSave}>Save Settings</Button>
            </Group>

            {/* System Info */}
            <Card>
                <Title order={6} mb="sm">System Information</Title>
                <Stack gap="xs">
                    <Group justify="space-between">
                        <Text size="sm" c="dimmed">Dashboard Version</Text>
                        <Code>2.0.0</Code>
                    </Group>
                    <Group justify="space-between">
                        <Text size="sm" c="dimmed">Mantine</Text>
                        <Code>v7.x</Code>
                    </Group>
                    <Group justify="space-between">
                        <Text size="sm" c="dimmed">React</Text>
                        <Code>v18.x</Code>
                    </Group>
                    <Group justify="space-between">
                        <Text size="sm" c="dimmed">Build</Text>
                        <Code>Vite + TypeScript</Code>
                    </Group>
                </Stack>
            </Card>
        </Stack>
    );
}
