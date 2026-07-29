/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B0D12",
        surface: "#12151C",
        raised: "#1A1E27",
        edge: "#262B37",
        edgeSoft: "#1F232D",
        primary: "#E7EAF2",
        muted: "#8891A5",
        faint: "#5B6377",
        brand: {
          DEFAULT: "#4FE3C1",
          dim: "#2C8C79",
          glow: "rgba(79, 227, 193, 0.18)",
        },
        bug: {
          DEFAULT: "#FB7280",
          dim: "#7A3A40",
          glow: "rgba(251, 114, 128, 0.14)",
        },
        fix: {
          DEFAULT: "#3ED598",
          dim: "#215B41",
          glow: "rgba(62, 213, 152, 0.14)",
        },
        warn: {
          DEFAULT: "#F2B84B",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.03) inset, 0 20px 60px -30px rgba(0,0,0,0.6)",
        glowBrand: "0 0 0 1px rgba(79,227,193,0.25), 0 0 40px -8px rgba(79,227,193,0.35)",
      },
      keyframes: {
        blink: {
          "0%, 49%": { opacity: 1 },
          "50%, 100%": { opacity: 0 },
        },
        typeIn: {
          from: { width: "0%" },
          to: { width: "100%" },
        },
        fadeUp: {
          from: { opacity: 0, transform: "translateY(8px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: 0.4 },
          "50%": { opacity: 1 },
        },
      },
      animation: {
        blink: "blink 1s step-end infinite",
        fadeUp: "fadeUp 0.5s ease-out both",
        pulseDot: "pulseDot 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
