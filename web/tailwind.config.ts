import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        muted: "#64748b",
        line: "#e2e8f0",
        brand: "#2563eb",
        hot: "#dc2626",
        warm: "#d97706",
        ok: "#16a34a",
      },
    },
  },
  plugins: [],
};

export default config;
