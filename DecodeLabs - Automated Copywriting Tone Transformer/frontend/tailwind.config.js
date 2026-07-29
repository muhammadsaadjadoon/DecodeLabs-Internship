/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#07111F",
        midnight: "#050A14",
        panel: "#0E1A2E",
        panelSoft: "#13233B",
        panelLine: "#24354F",
        paper: "#F7FAFF",
        paperLine: "#D9E4F2",
        ink: "#0A1630",
        lex: {
          cyan: "#20D9F2",
          blue: "#087BFF",
          teal: "#0FE6D2",
          navy: "#081943",
          glow: "#36E7FF",
        },
        amber: {
          DEFAULT: "#20D9F2",
          soft: "#0D3348",
        },
        mint: {
          DEFAULT: "#0FE6D2",
          soft: "#0D3E42",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        serif: ["'Source Serif 4'", "serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        premium: "0 24px 70px -35px rgba(32,217,242,.55), inset 0 1px 0 rgba(255,255,255,.08)",
        paper: "0 30px 80px -48px rgba(15, 25, 45, .95), 0 1px 0 rgba(255,255,255,.85)",
        glow: "0 0 0 1px rgba(32,217,242,.24), 0 24px 70px -35px rgba(32,217,242,.85)",
      },
      backgroundImage: {
        "lex-panel": "linear-gradient(145deg, rgba(19,35,59,.92), rgba(8,17,32,.96))",
        "lex-button": "linear-gradient(135deg, #20D9F2 0%, #087BFF 58%, #0FE6D2 100%)",
      },
    },
  },
  plugins: [],
};
