import { createTheme } from "@mantine/core";
import type { MantineColorsTuple } from "@mantine/core";

const slate: MantineColorsTuple = [
    "#f8fafc",
    "#f1f5f9",
    "#e2e8f0",
    "#cbd5e1",
    "#94a3b8",
    "#64748b",
    "#475569",
    "#334155",
    "#1e293b",
    "#0f172a",
];

const emerald: MantineColorsTuple = [
    "#ecfdf5",
    "#d1fae5",
    "#a7f3d0",
    "#6ee7b7",
    "#34d399",
    "#10b981",
    "#059669",
    "#047857",
    "#065f46",
    "#064e3b",
];

const amber: MantineColorsTuple = [
    "#fffbeb",
    "#fef3c7",
    "#fde68a",
    "#fcd34d",
    "#fbbf24",
    "#f59e0b",
    "#d97706",
    "#b45309",
    "#92400e",
    "#78350f",
];

const sky: MantineColorsTuple = [
    "#f0f9ff",
    "#e0f2fe",
    "#bae6fd",
    "#7dd3fc",
    "#38bdf8",
    "#0ea5e9",
    "#0284c7",
    "#0369a1",
    "#075985",
    "#0c4a6e",
];

const rose: MantineColorsTuple = [
    "#fff1f2",
    "#ffe4e6",
    "#fecdd3",
    "#fda4af",
    "#fb7185",
    "#f43f5e",
    "#e11d48",
    "#be123c",
    "#9f1239",
    "#881337",
];

export const theme = createTheme({
    primaryColor: "sky",
    colors: {
        slate,
        emerald,
        amber,
        sky,
        rose,
    },
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    headings: {
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: "600",
        sizes: {
            h1: { fontSize: "2rem", lineHeight: "1.2" },
            h2: { fontSize: "1.5rem", lineHeight: "1.3" },
            h3: { fontSize: "1.25rem", lineHeight: "1.35" },
            h4: { fontSize: "1.125rem", lineHeight: "1.4" },
            h5: { fontSize: "1rem", lineHeight: "1.45" },
        },
    },
    defaultRadius: "md",
    cursorType: "pointer",
    spacing: {
        xs: "0.5rem",
        sm: "0.75rem",
        md: "1rem",
        lg: "1.5rem",
        xl: "2rem",
    },
    shadows: {
        xs: "0 1px 2px rgba(0, 0, 0, 0.04)",
        sm: "0 1px 3px rgba(0, 0, 0, 0.08)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.08)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.08)",
        xl: "0 20px 25px -5px rgba(0, 0, 0, 0.08)",
    },
    components: {
        Button: {
            defaultProps: {
                size: "sm",
            },
            styles: {
                root: {
                    fontWeight: 500,
                },
            },
        },
        Card: {
            defaultProps: {
                withBorder: true,
                shadow: "xs",
            },
        },
        Table: {
            defaultProps: {
                striped: true,
                highlightOnHover: true,
                withTableBorder: true,
            },
        },
        Badge: {
            styles: {
                root: {
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.02em",
                },
            },
        },
        NavLink: {
            styles: {
                root: {
                    borderRadius: "var(--mantine-radius-md)",
                },
            },
        },
    },
});
