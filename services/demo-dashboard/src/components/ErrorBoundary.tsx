/**
 * ErrorBoundary Component - Prevents blank screen crashes
 * Catches JavaScript errors in child components and displays fallback UI
 */

import React from "react";
import {
    Alert,
    Button,
    Stack,
    Title,
    Text,
    Code,
    Group,
} from "@mantine/core";
import { IconAlertTriangle, IconRefresh, IconHome } from "@tabler/icons-react";

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
    errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("ErrorBoundary caught an error:", error, errorInfo);
        this.setState({ errorInfo });
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
    };

    handleGoHome = () => {
        window.location.hash = "#/payment";
        this.setState({ hasError: false, error: null, errorInfo: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <Stack align="center" justify="center" p="xl" mih={400}>
                    <IconAlertTriangle size={48} color="var(--mantine-color-orange-6)" />
                    <Title order={3}>Something went wrong</Title>
                    <Text c="dimmed" ta="center" maw={500}>
                        An unexpected error occurred. This might be due to expired data or a temporary issue.
                    </Text>

                    <Alert color="red" variant="light" w="100%" maw={600} mt="md">
                        <Text size="sm" fw={500} mb="xs">Error Details:</Text>
                        <Code block style={{ whiteSpace: "pre-wrap", fontSize: "0.75rem" }}>
                            {this.state.error?.message || "Unknown error"}
                        </Code>
                    </Alert>

                    <Group mt="lg">
                        <Button
                            variant="light"
                            leftSection={<IconRefresh size={16} />}
                            onClick={this.handleRetry}
                        >
                            Try Again
                        </Button>
                        <Button
                            variant="filled"
                            leftSection={<IconHome size={16} />}
                            onClick={this.handleGoHome}
                        >
                            Go to Home
                        </Button>
                    </Group>
                </Stack>
            );
        }

        return this.props.children;
    }
}
