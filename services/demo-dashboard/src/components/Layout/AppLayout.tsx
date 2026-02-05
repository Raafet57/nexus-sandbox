import { useState, useEffect } from "react";
import {
    AppShell,
    Burger,
    Group,
    NavLink,
    Title,
    Text,
    Badge,
    useMantineColorScheme,
    ActionIcon,
    Box,
    Divider,
    ThemeIcon,
    Stack,
    Tooltip,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
    IconSend,
    IconArrowsExchange,
    IconCoin,
    IconMessage,
    IconSettings,
    IconMoon,
    IconSun,
    IconNetwork,
    IconUsers,
    IconBuilding,
    IconAddressBook,
    IconApi,
    IconExternalLink,
    IconReportAnalytics,
    IconPlayerPlay,
    IconWorld,
} from "@tabler/icons-react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { checkHealth } from "../../services/api";
import { MOCK_ENABLED } from "../../services/mockData";
import { DemoBanner } from "../DemoBanner";

interface NavItem {
    icon: typeof IconSend;
    label: string;
    path: string;
    description: string;
}

const navItems: NavItem[] = [
    {
        icon: IconSend,
        label: "Send Payment",
        path: "/payment",
        description: "PSP payment flow",
    },
    {
        icon: IconPlayerPlay,
        label: "Demo Scenarios",
        path: "/demo",
        description: "Unhappy flows testing",
    },
    {
        icon: IconBuilding,
        label: "PSP Dashboard",
        path: "/psp",
        description: "Source/Dest PSP view",
    },
    {
        icon: IconArrowsExchange,
        label: "FX Rates (FXP)",
        path: "/fxp",
        description: "FXP rate management",
    },
    {
        icon: IconCoin,
        label: "Liquidity (SAP)",
        path: "/sap",
        description: "SAP balance view",
    },
    {
        icon: IconNetwork,
        label: "IPS Dashboard",
        path: "/ips",
        description: "IPS operator view",
    },
    {
        icon: IconAddressBook,
        label: "PDO Dashboard",
        path: "/pdo",
        description: "Proxy directory view",
    },
    {
        icon: IconReportAnalytics,
        label: "Payments Explorer",
        path: "/explorer",
        description: "Transaction lifecycle & messages",
    },
    {
        icon: IconMessage,
        label: "Messages",
        path: "/messages",
        description: "ISO 20022 explorer",
    },
    {
        icon: IconNetwork,
        label: "Network Mesh",
        path: "/mesh",
        description: "System mesh view",
    },
    {
        icon: IconUsers,
        label: "Actors",
        path: "/actors",
        description: "Participant registry",
    },
    {
        icon: IconSettings,
        label: "Settings",
        path: "/settings",
        description: "Configuration",
    },
];

export function AppLayout() {
    const [opened, { toggle }] = useDisclosure();
    const { colorScheme, toggleColorScheme } = useMantineColorScheme();
    const location = useLocation();
    const [apiStatus, setApiStatus] = useState<"connected" | "disconnected" | "checking">("checking");

    useEffect(() => {
        const checkApiStatus = async () => {
            try {
                await checkHealth();
                setApiStatus("connected");
            } catch {
                setApiStatus("disconnected");
            }
        };

        checkApiStatus();
        const interval = setInterval(checkApiStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const statusColor = apiStatus === "connected" ? "green" : apiStatus === "disconnected" ? "red" : "yellow";
    const statusText = apiStatus === "connected" ? "Connected" : apiStatus === "disconnected" ? "Disconnected" : "Checking";

    return (
        <AppShell
            header={{ height: 60 }}
            navbar={{
                width: 280,
                breakpoint: "sm",
                collapsed: { mobile: !opened },
            }}
            padding="lg"
            styles={{
                header: {
                    borderBottom: "1px solid var(--glass-border)",
                    backdropFilter: "blur(10px)",
                    background: colorScheme === "dark" 
                        ? "rgba(26, 27, 30, 0.85)" 
                        : "rgba(255, 255, 255, 0.85)",
                },
                navbar: {
                    borderRight: "1px solid var(--glass-border)",
                    background: colorScheme === "dark"
                        ? "rgba(26, 27, 30, 0.95)"
                        : "rgba(255, 255, 255, 0.95)",
                },
                main: {
                    background: colorScheme === "dark"
                        ? "linear-gradient(180deg, #1a1b1e 0%, #141517 100%)"
                        : "linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%)",
                },
            }}
        >
            <AppShell.Header>
                <Group h="100%" px="md" justify="space-between">
                    <Group gap="md">
                        <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
                        <Group gap="xs">
                            <ThemeIcon 
                                size="lg" 
                                radius="md" 
                                variant="gradient"
                                gradient={{ from: "nexusPurple.5", to: "nexusCyan.5", deg: 135 }}
                            >
                                <IconWorld size={20} />
                            </ThemeIcon>
                            <Title order={3} fw={700} style={{ letterSpacing: "-0.02em" }}>
                                NEXUS SANDBOX
                            </Title>
                        </Group>
                        <Badge 
                            variant="gradient" 
                            gradient={{ from: "nexusPurple.5", to: "nexusCyan.5", deg: 135 }}
                            size="sm"
                            tt="uppercase"
                        >
                            Demo
                        </Badge>
                    </Group>
                    <Group gap="sm">
                        <Tooltip label={`API: ${statusText}`}>
                            <Badge
                                color={MOCK_ENABLED ? "blue" : statusColor}
                                variant="dot"
                                size="lg"
                                styles={{
                                    root: {
                                        cursor: "default",
                                    },
                                }}
                            >
                                {MOCK_ENABLED ? "Demo Mode" : `API: ${statusText.toUpperCase()}`}
                            </Badge>
                        </Tooltip>
                        <ActionIcon
                            variant="subtle"
                            size="lg"
                            radius="md"
                            onClick={() => toggleColorScheme()}
                            title="Toggle color scheme"
                        >
                            {colorScheme === "dark" ? <IconSun size={20} /> : <IconMoon size={20} />}
                        </ActionIcon>
                    </Group>
                </Group>
            </AppShell.Header>

            <AppShell.Navbar p="sm">
                <AppShell.Section grow style={{ overflow: "auto" }}>
                    <Stack gap={4}>
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            return (
                                <NavLink
                                    key={item.path}
                                    component={Link}
                                    to={item.path}
                                    label={item.label}
                                    description={item.description}
                                    leftSection={
                                        <ThemeIcon 
                                            size="sm" 
                                            variant={isActive ? "gradient" : "subtle"}
                                            gradient={isActive ? { from: "nexusPurple.5", to: "nexusCyan.5", deg: 135 } : undefined}
                                            color={isActive ? undefined : "gray"}
                                        >
                                            <item.icon size={16} />
                                        </ThemeIcon>
                                    }
                                    active={isActive}
                                    onClick={() => toggle()}
                                    styles={{
                                        root: {
                                            borderRadius: "var(--mantine-radius-md)",
                                            marginBottom: 2,
                                        },
                                        label: {
                                            fontWeight: isActive ? 600 : 500,
                                        },
                                    }}
                                />
                            );
                        })}
                    </Stack>
                </AppShell.Section>

                <AppShell.Section>
                    <Divider my="sm" color="var(--glass-border)" />
                    <NavLink
                        component="a"
                        href="/api/docs"
                        target="_blank"
                        label="API Docs"
                        description="Swagger/OpenAPI"
                        leftSection={
                            <ThemeIcon size="sm" variant="subtle" color="gray">
                                <IconApi size={16} />
                            </ThemeIcon>
                        }
                        rightSection={<IconExternalLink size={14} opacity={0.5} />}
                        styles={{
                            root: {
                                borderRadius: "var(--mantine-radius-md)",
                            },
                        }}
                    />
                    <Box p="sm" mt="xs">
                        <Text size="xs" c="dimmed" fw={600} tt="uppercase" mb="xs" style={{ letterSpacing: "0.05em" }}>
                            System Status
                        </Text>
                        <Group gap="xs">
                            <span className={`status-dot ${apiStatus}`} />
                            <Text size="sm" fw={500}>
                                Gateway: {statusText}
                            </Text>
                        </Group>
                    </Box>
                </AppShell.Section>
            </AppShell.Navbar>

            <AppShell.Main>
                <DemoBanner />
                <Box className="fade-in">
                    <Outlet />
                </Box>
            </AppShell.Main>
        </AppShell>
    );
}
