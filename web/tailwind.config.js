/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0f172a",
        accent: "#22d3ee",
        muted: "#64748b",
      },
    },
  },
  plugins: [],
};
