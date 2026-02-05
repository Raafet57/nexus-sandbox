import { createTheme, virtualColor } from "@mantine/core";
import type { MantineColorsTuple } from "@mantine/core";

const nexusPurple: MantineColorsTuple = [
    "#f5f0ff",
    "#e5dbff",
    "#c9b3ff",
    "#ab87ff",
    "#9945ff",
    "#8b3df7",
    "#7c2fef",
    "#6c21d9",
    "#5c1ac3",
    "#4b12ad",
];

const nexusCyan: MantineColorsTuple = [
    "#e0fcff",
    "#b8f3fb",
    "#8eeaf9",
    "#63e0f7",
    "#3cd6f5",
    "#22bcdb",
    "#0d93ab",
    "#00697a",
    "#00404a",
    "#00181b",
];

const nexusGreen: MantineColorsTuple = [
    "#e6fff2",
    "#c3fce0",
    "#9ef7cc",
    "#78f2b7",
    "#52eda3",
    "#30d989",
    "#1cb871",
    "#0a9659",
    "#007541",
    "#005329",
];

const nexusOrange: MantineColorsTuple = [
    "#fff4e6",
    "#ffe8cc",
    "#ffd8a8",
    "#ffc078",
    "#ffa94d",
    "#ff922b",
    "#fd7e14",
    "#e8590c",
    "#d9480f",
    "#c92a00",
];

export const theme = createTheme({
    primaryColor: "nexusPurple",
    colors: {
        nexusPurple,
        nexusCyan,
        nexusGreen,
        nexusOrange,
        primary: virtualColor({
            name: "primary",
            dark: "nexusPurple",
            light: "nexusPurple",
        }),
    },
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    headings: {
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: "600",
        sizes: {
            h1: { fontSize: "2.25rem", lineHeight: "1.2" },
            h2: { fontSize: "1.75rem", lineHeight: "1.3" },
            h3: { fontSize: "1.375rem", lineHeight: "1.35" },
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
        xs: "0 1px 2px rgba(0, 0, 0, 0.05)",
        sm: "0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    },
    components: {
        Button: {
            defaultProps: {
                size: "sm",
            },
            styles: {
                root: {
                    fontWeight: 500,
                    transition: "all 0.2s ease",
                },
            },
        },
        Card: {
            defaultProps: {
                withBorder: true,
                shadow: "sm",
            },
            styles: {
                root: {
                    transition: "transform 0.2s ease, box-shadow 0.2s ease",
                },
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
                    letterSpacing: "0.025em",
                },
            },
        },
        NavLink: {
            styles: {
                root: {
                    borderRadius: "var(--mantine-radius-md)",
                    transition: "all 0.15s ease",
                },
            },
        },
        TextInput: {
            styles: {
                input: {
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                },
            },
        },
        Select: {
            styles: {
                input: {
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                },
            },
        },
        NumberInput: {
            styles: {
                input: {
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                },
            },
        },
    },
});
