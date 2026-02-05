import { createTheme } from "@mantine/core";

// Nexus brand purple (Mantine requires exactly 10 shades)
const nexusPurple: [string, string, string, string, string, string, string, string, string, string] = [
    "#f5f0ff",
    "#e5dbff",
    "#c9b3ff",
    "#ab87ff",
    "#9945ff", // Primary
    "#8b3df7",
    "#7c2fef",
    "#6c21d9",
    "#5c1ac3",
    "#4b12ad",
];

export const theme = createTheme({
    primaryColor: "nexusPurple",
    colors: {
        nexusPurple,
    },
    fontFamily: "Inter, system-ui, -apple-system, sans-serif",
    headings: {
        fontFamily: "Inter, system-ui, -apple-system, sans-serif",
    },
    defaultRadius: "md",
    cursorType: "pointer",
    components: {
        Button: {
            defaultProps: {
                size: "sm",
            },
        },
        Card: {
            defaultProps: {
                withBorder: true,
                shadow: "sm",
            },
        },
        Table: {
            defaultProps: {
                striped: true,
                highlightOnHover: true,
                withTableBorder: true,
            },
        },
    },
});
