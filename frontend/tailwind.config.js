/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#001B4D",       // Primary Deep Navy
          blue: "#005BBB",       // Primary Corporate Blue
          dark: "#1E293B",       // Slate Dark Neutral
          muted: "#64748B",      // Slate Muted Text
          surface: "#F1F5F9",    // Background Surface Light
          white: "#FFFFFF",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
