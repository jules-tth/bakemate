/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'soft-pastel-background': '#F9F7F5',
        'soft-pastel-accent': '#FFB6C1',
      }
    },
  },
  plugins: [],
}
