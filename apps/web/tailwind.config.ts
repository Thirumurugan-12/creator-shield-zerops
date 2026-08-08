import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        secured: "hsl(var(--status-secured))",
        processing: "hsl(var(--status-processing))",
        review: "hsl(var(--status-review))",
        "high-risk": "hsl(var(--status-high-risk))",
        critical: "hsl(var(--status-critical))",
        "evidence-match": "hsl(var(--evidence-match))",
      },
      borderRadius: { lg: "0.75rem", md: "0.5rem", sm: "0.375rem" },
      boxShadow: { panel: "0 1px 2px hsl(0 0% 0% / 0.04), 0 8px 24px hsl(0 0% 0% / 0.04)" },
    },
  },
  plugins: [],
} satisfies Config;
