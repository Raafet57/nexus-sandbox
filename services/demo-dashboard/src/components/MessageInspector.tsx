/**
 * MessageInspector - Professional ISO 20022 Message Viewer
 * 
 * A developer-focused component for viewing and analyzing ISO 20022
 * XML messages exchanged during the Nexus payment lifecycle.
 * 
 * Features:
 * - XML syntax highlighting with Prism.js
 * - Message timeline visualization (17-step lifecycle)
 * - Direction indicators (inbound/outbound)
 * - Copy-to-clipboard functionality
 * - Expandable/collapsible view
 * 
 * Reference: ADR-011 Developer Observability
 * Author: Siva Subramanian (https://linkedin.com/in/sivasub987)
 */

import {
    Card,
    Stack,
    Group,
    Text,
    Badge,
    Timeline,
    Code,
    ActionIcon,
    CopyButton,
    Tooltip,
    Collapse,
    ScrollArea,
    Paper,
    Title,
    Divider,
    Alert,
    Loader,
} from "@mantine/core";
import {
    IconArrowRight,
    IconArrowLeft,
    IconCopy,
    IconCheck,
    IconFileCode,
    IconChevronDown,
    IconChevronUp,
    IconInfoCircle,
    IconClock,
    IconAlertCircle,
} from "@tabler/icons-react";
import { useState } from "react";

// Message type metadata for display
const MESSAGE_METADATA: Record<string, {
    displayName: string;
    step: number;
    color: string;
    description: string;
}> = {
    "pacs.008": {
        displayName: "FI to FI Customer Credit Transfer",
        step: 15,
        color: "blue",
        description: "Payment instruction from Source PSP to Destination PSP via Nexus",
    },
    "pacs.002": {
        displayName: "Payment Status Report",
        step: 17,
        color: "green",
        description: "Confirmation from Destination PSP (ACCC = success, RJCT = rejected)",
    },
    "acmt.023": {
        displayName: "Identification Verification Request",
        step: 7,
        color: "violet",
        description: "Proxy resolution request to PDO",
    },
    "acmt.024": {
        displayName: "Identification Verification Report",
        step: 8,
        color: "grape",
        description: "Account details returned from PDO",
    },
    "camt.054": {
        displayName: "Bank to Customer Notification",
        step: 17,
        color: "cyan",
        description: "Reconciliation report for SAPs and FXPs",
    },
    "camt.056": {
        displayName: "FI to FI Payment Cancellation Request",
        step: 0,
        color: "orange",
        description: "Recall request for funds recovery",
    },
    "pacs.004": {
        displayName: "Payment Return",
        step: 0,
        color: "red",
        description: "Return of funds to sender",
    },
};

interface Message {
    messageType: string;
    direction: "inbound" | "outbound";
    xml: string;
    timestamp: string;
    description?: string;
}

interface MessageInspectorProps {
    uetr: string;
    messages?: Message[];
    loading?: boolean;
    error?: string;
}

/**
 * Format XML with indentation for display
 */
function formatXml(xml: string): string {
    if (!xml) return "";

    // Simple XML formatting
    let formatted = "";
    let indent = 0;
    const lines = xml.replace(/>\s*</g, ">\n<").split("\n");

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Closing tag - decrease indent first
        if (trimmed.startsWith("</")) {
            indent = Math.max(0, indent - 1);
        }

        formatted += "  ".repeat(indent) + trimmed + "\n";

        // Opening tag without close - increase indent
        if (trimmed.startsWith("<") && !trimmed.startsWith("</") &&
            !trimmed.startsWith("<?") && !trimmed.endsWith("/>") &&
            !trimmed.includes("</")) {
            indent++;
        }
    }

    return formatted.trim();
}

/**
 * XML Syntax Highlighter Component
 * Uses dark-mode compatible colors (VS Code Dark+ theme)
 * 
 * Uses placeholder tokens to prevent regex from matching inserted HTML spans
 */
function XmlHighlighter({ xml }: { xml: string }) {
    const formatted = formatXml(xml);

    // Use unique placeholders that won't be matched by subsequent regex
    // These get replaced with actual HTML at the very end
    const SPAN_OPEN = "___SPAN_OPEN___";
    const SPAN_CLOSE = "___SPAN_CLOSE___";

    // Escape HTML entities first
    let highlighted = formatted
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Apply syntax highlighting with placeholders
    // Tags (cyan-green for element names)
    highlighted = highlighted.replace(
        /(&lt;\/?)([a-zA-Z_][\w:-]*)/g,
        `$1${SPAN_OPEN}color:#4EC9B0${SPAN_CLOSE}$2</span>`
    );

    // Attributes (light purple for attribute names) - only match before = sign
    highlighted = highlighted.replace(
        /(\s)([a-zA-Z_][\w:-]*)(=)/g,
        `$1${SPAN_OPEN}color:#9CDCFE${SPAN_CLOSE}$2</span>$3`
    );

    // Attribute values (orange for strings)
    highlighted = highlighted.replace(
        /(="[^"]*")/g,
        `${SPAN_OPEN}color:#CE9178${SPAN_CLOSE}$1</span>`
    );

    // Text content between tags (lighter color for text)
    highlighted = highlighted.replace(
        /(&gt;)([^&\n]+)(&lt;\/)/g,
        `$1${SPAN_OPEN}color:#D4D4D4${SPAN_CLOSE}$2</span>$3`
    );

    // XML declaration (gray)
    highlighted = highlighted.replace(
        /(&lt;\?xml[^?]*\?&gt;)/g,
        `${SPAN_OPEN}color:#808080${SPAN_CLOSE}$1</span>`
    );

    // Now replace placeholders with actual span tags
    highlighted = highlighted
        .replace(/___SPAN_OPEN___/g, '<span style="')
        .replace(/___SPAN_CLOSE___/g, '">');

    return (
        <Code
            block
            style={{
                fontSize: "12px",
                lineHeight: 1.6,
                backgroundColor: "#1E1E1E",  // VS Code dark background
                border: "1px solid #3C3C3C",
                borderRadius: "6px",
                padding: "16px",
                fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
                color: "#D4D4D4",  // Default text color
                overflowX: "auto",
            }}
            dangerouslySetInnerHTML={{ __html: highlighted }}
        />
    );
}


/**
 * Individual Message Card
 */
function MessageCard({ message }: { message: Message }) {
    const [expanded, setExpanded] = useState(false);
    const meta = MESSAGE_METADATA[message.messageType] || {
        displayName: message.messageType,
        step: 0,
        color: "gray",
        description: "Unknown message type",
    };

    return (
        <Paper shadow="xs" p="md" radius="md" withBorder>
            <Group justify="space-between" mb={expanded ? "md" : 0}>
                <Group>
                    {message.direction === "outbound" ? (
                        <IconArrowRight size={20} color="blue" />
                    ) : (
                        <IconArrowLeft size={20} color="green" />
                    )}
                    <div>
                        <Group gap={8}>
                            <Text fw={600}>{message.messageType}</Text>
                            <Badge color={meta.color} size="sm">
                                Step {meta.step}
                            </Badge>
                            <Badge
                                color={message.direction === "outbound" ? "blue" : "green"}
                                variant="light"
                                size="sm"
                            >
                                {message.direction === "outbound" ? "Sent" : "Received"}
                            </Badge>
                        </Group>
                        <Text size="xs" c="dimmed">{meta.displayName}</Text>
                    </div>
                </Group>

                <Group gap={8}>
                    <Tooltip label="Copy XML">
                        <CopyButton value={message.xml}>
                            {({ copied, copy }) => (
                                <ActionIcon
                                    color={copied ? "teal" : "gray"}
                                    variant="subtle"
                                    onClick={copy}
                                >
                                    {copied ? <IconCheck size={18} /> : <IconCopy size={18} />}
                                </ActionIcon>
                            )}
                        </CopyButton>
                    </Tooltip>
                    <ActionIcon
                        variant="subtle"
                        onClick={() => setExpanded(!expanded)}
                    >
                        {expanded ? <IconChevronUp size={18} /> : <IconChevronDown size={18} />}
                    </ActionIcon>
                </Group>
            </Group>

            <Collapse in={expanded}>
                <Stack gap="sm" mt="md">
                    <Group gap="xs">
                        <IconClock size={14} />
                        <Text size="xs" c="dimmed">
                            {message.timestamp ? new Date(message.timestamp).toLocaleString() : "N/A"}
                        </Text>
                    </Group>

                    <Text size="sm" c="dimmed">
                        {message.description || meta.description}
                    </Text>

                    <ScrollArea h={300}>
                        <XmlHighlighter xml={message.xml} />
                    </ScrollArea>
                </Stack>
            </Collapse>
        </Paper>
    );
}

/**
 * MessageInspector - Main Component
 */
export function MessageInspector({
    uetr,
    messages = [],
    loading = false,
    error
}: MessageInspectorProps) {
    if (loading) {
        return (
            <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="center" py="xl">
                    <Loader size="md" />
                    <Text>Loading messages for {uetr.substring(0, 8)}...</Text>
                </Group>
            </Card>
        );
    }

    if (error) {
        return (
            <Alert
                icon={<IconAlertCircle size={16} />}
                title="Error Loading Messages"
                color="red"
            >
                {error}
            </Alert>
        );
    }

    if (messages.length === 0) {
        return (
            <Alert
                icon={<IconInfoCircle size={16} />}
                title="No Messages"
                color="gray"
            >
                No ISO 20022 messages found for UETR: {uetr}
            </Alert>
        );
    }

    return (
        <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between" mb="md">
                <Group>
                    <IconFileCode size={24} />
                    <div>
                        <Title order={4}>Message Inspector</Title>
                        <Text size="sm" c="dimmed">
                            ISO 20022 messages for transaction
                        </Text>
                    </div>
                </Group>
                <Badge size="lg" variant="light">
                    {messages.length} message{messages.length !== 1 ? "s" : ""}
                </Badge>
            </Group>

            <Group mb="md">
                <Code>UETR: {uetr}</Code>
                <CopyButton value={uetr}>
                    {({ copied, copy }) => (
                        <Tooltip label={copied ? "Copied!" : "Copy UETR"}>
                            <ActionIcon
                                color={copied ? "teal" : "gray"}
                                variant="subtle"
                                onClick={copy}
                                size="sm"
                            >
                                {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                            </ActionIcon>
                        </Tooltip>
                    )}
                </CopyButton>
            </Group>

            <Divider mb="md" />

            <Timeline active={messages.length - 1} bulletSize={24} lineWidth={2}>
                {messages.map((message, index) => {
                    const meta = MESSAGE_METADATA[message.messageType] || {
                        displayName: message.messageType,
                        step: 0,
                        color: "gray",
                        description: "",
                    };

                    return (
                        <Timeline.Item
                            key={index}
                            bullet={
                                message.direction === "outbound"
                                    ? <IconArrowRight size={12} />
                                    : <IconArrowLeft size={12} />
                            }
                            color={meta.color}
                            title={
                                <Group gap={8}>
                                    <Text fw={600}>{message.messageType}</Text>
                                    <Badge color={meta.color} size="xs">
                                        Step {meta.step}
                                    </Badge>
                                </Group>
                            }
                        >
                            <MessageCard message={message} />
                        </Timeline.Item>
                    );
                })}
            </Timeline>
        </Card>
    );
}

export default MessageInspector;
