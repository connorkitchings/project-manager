import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "var(--color-base)",
        ink: "var(--color-ink)",
        pine: "var(--color-pine)",
        sand: "var(--color-sand)",
        accent: "var(--color-accent)",
        attention: "var(--color-attention)",
        danger: "var(--color-danger)",
        calm: "var(--color-calm)",
      },
      boxShadow: {
        panel: "0 16px 50px rgba(18, 41, 34, 0.08)",
      },
      fontFamily: {
        display: ["\"Space Grotesk\"", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
